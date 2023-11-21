#!/usr/bin/env bash

# -- multiprocessing options --
# _____________________________

# J is the number of processes for stage 1 and 2. The recommended limit, is to make sure you
# have about 10 GB of RAM per process. For the science cluster at ST, with 512 GB RAM, I use
# J=48.
J=48

# JJ is the number of processes for stage 3, where cube_build is a big memory bottleneck. The
# required memory depends heavily on the final shape of the cube. For Orion, there is lots of
# empty space in the cubes with the default coordinate grids, and about 50 GB of RAM was needed
# per process. But with ~200GB RAM, the 3 NIRSpec cubes can be built simultaneously, which saves
# some time for this slow step.
JJ=3

# Use these if there's too much multithreading. On machines with high core counts, numpy etc can
# sometimes launch a large number of threads. This doesn't give much speedup if multiprocessing
# is used already.
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

# -- environment --
# _________________

# Set CRDS context here. If N is not a number, no context will be set, resulting in the latest
# pmap.
export CRDS_PATH=/home/dvandeputte/storage/crds_cache
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
IN_SCI=$(realpath science)
IN_SCII=$(realpath science_imprint)
IN_BKG=$(realpath background)
IN_BKGI=$(realpath background_imprint)

# Modify the output directory here. Default has the pmap number in it (if set).
OUT_PFX=${N}pmap
# subdirectories for output are made here
for d in science science_imprint background background_imprint
do mkdir -p $OUT_PFX/$d
done
OUT_SCI=$(realpath $OUT_PFX/science)
OUT_SCII=$(realpath $OUT_PFX/science_imprint)
OUT_BKG=$(realpath $OUT_PFX/background)
OUT_BKGI=$(realpath $OUT_PFX/background_imprint)

# -- run the pipeline --
# ______________________

# the commands below assume that the pdr_reduction python package is installed

# background imprint (need up to stage 1)
pipeline -j $J -s 1 -o $OUT_BKGI $IN_BKGI
# background (need up to stage 2)
pipeline -j $J -s 12 -o $OUT_BKG $IN_BKG
# background stage 3 if interested
# pipeline -j $JJ -s 3 -o $OUT_BKG $IN_BKG

# science imprint
pipeline -j $J -s 1 -o $OUT_SCII $IN_SCII
# science
python $SCRIPT -j $J -s 1 -o $OUT_SCI $IN_SCI

# -- reduction without NSClean --
# _______________________________

# science stage 2 needs imprints with -i
# python $SCRIPT -j $J -s 2 -i $OUT_SCII -o $OUT_SCI $IN_SCI
# science stage 3 needs background (if doing master background subtraction). For image-to-image
# background subtraction, use the -b option in stage 2 instead.
# python $SCRIPT -j $JJ -s 3 --mosaic -b $OUT_BKG -o $OUT_SCI $IN_SCI

# -- reduction with NSClean --
# ____________________________

# Apply NSClean (1/f noise correction) to the stage 1 data, and run stage 2 and 3 again. Similar
# subdirectories need to be made.
OUT_PFX_NSC=${OUT_PFX}_nsclean
for d in science science_imprint background background_imprint
do mkdir -p $OUT_PFX_NSC/$d/stage1
done
OUT_SCI_NSC=$(realpath $OUT_PFX_NSC/science)
OUT_SCII_NSC=$(realpath $OUT_PFX_NSC/science_imprint)
OUT_BKG_NSC=$(realpath $OUT_PFX_NSC/background)
OUT_BKGI_NSC=$(realpath $OUT_PFX_NSC/background_imprint)

# Use GNU parallel for performance
parallel -j $J nsclean_run {} $OUT_BKG_NSC/stage1/{/} ::: $OUT_BKG/stage1/*rate.fits
parallel -j $J nsclean_run {} $OUT_BKGI_NSC/stage1/{/} ::: $OUT_BKGI/stage1/*rate.fits
parallel -j $J nsclean_run {} $OUT_SCII_NSC/stage1/{/} ::: $OUT_SCII/stage1/*rate.fits
parallel -j $J nsclean_run {} $OUT_SCI_NSC/stage1/{/} ::: $OUT_SCI/stage1/*rate.fits

# the rest of the steps with the cleaned data
pipeline -j $J -s 2 -i $OUT_BKGI_NSC -o $OUT_BKG_NSC $IN_BKG
pipeline -j $J -s 2 -i $OUT_SCII_NSC -o $OUT_SCI_NSC $IN_SCI
pipeline -j $JJ -s 3 --mosaic -b $OUT_BKG -o $OUT_SCI_NSC $IN_SCI
