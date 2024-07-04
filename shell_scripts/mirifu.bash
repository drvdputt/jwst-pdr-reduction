#!/usr/bin/env bash

# -- multiprocessing options --
# _____________________________

# J is the number of processes for stage 1 and 2. The recommended limit, is to make sure you
# have about 10 GB of RAM per process. For the science cluster at ST, with 512 GB RAM, I use
# J=48.
J=1

# JJ is the number of processes for stage 3, where cube_build is a big memory bottleneck. The
# required memory depends heavily on the final shape of the cube.
JJ=1

# Use these if there's too much multithreading. On machines with high core counts, numpy etc can
# sometimes launch a large number of threads. This can actually slow things down if
# multiprocessing is used already.
T=8
export MKL_NUM_THREADS=$T
export NUMEXPR_NUM_THREADS=$T
export OMP_NUM_THREADS=$T
export OPENBLAS_NUM_THREADS=$T

# -- environment --
# _________________

# Set CRDS context here. If N is not a number, no context will be set, resulting in the latest
# pmap.
export CRDS_PATH=$HOME/crds_cache
export CRDS_SERVER_URL=https://jwst-crds.stsci.edu
# N=1147
N=latest
if [[ $N =~ ^[0-9]{4}$ ]]
then export CRDS_CONTEXT=jwst_$N.pmap
fi

# If you use conda, activate enable its use here and activate the right environment
# eval "$(conda shell.bash hook)"
# conda activate jwstpip
python -c "import sys; print(sys.executable)"

# -- set up directories --
# ________________________

# Specify input directories as recommended in the readme. The script needs absolute paths for
# everything. This is a quirk of the association generator.
HERE=$(pwd)
IN_SCI=$HERE/science
IN_BKG=$HERE/background

# Modify the output directory here. Default has the pmap number in it (if set).
OUT_PFX=${N}pmap
# subdirectories for output are made here
OUT_SCI=$HERE/$OUT_PFX/science
OUT_BKG=$HERE/$OUT_PFX/background

# -- run the pipeline --
# ______________________

# the commands below assume that the pdr_reduction python package is installed

# background (need up to stage 2)
pipeline -j $J -s 12 -o $OUT_BKG $IN_BKG &> log_bkg_12.txt
# background stage 3 if interested
pipeline -j $JJ -s 3 -o $OUT_BKG $IN_BKG &> log_bkg_3.txt

# science
pipeline -j $J -s 1 --custom_options performance.json -o $OUT_SCI $IN_SCI &> log_sci_1.txt
# stage 2 with optional residual fringe correction
pipeline -j $J -s 2 --residual_fringe -b $OUT_BKG -o $OUT_SCI $IN_SCI &> log_sci_2.txt
pipeline -j $JJ -s 3 --mosaic -o $OUT_SCI $IN_SCI &> log_sci_3.txt
