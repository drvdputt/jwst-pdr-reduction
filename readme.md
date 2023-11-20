# JWST PDR tools

This repository is a collection of data reduction tools for JWST data of PDRs.
Most of this was developed in the context of the "PDRs4All" Early Release
Science program (ERS-1288), which observed the Orion Bar with imaging and
spectroscopy mosaics. A GTO program also recently completed, using a similar
strategy for the PDRs in the Horsehead and NGC7023. Additions and improvements
to the tools in the context of these other PDRs, will also be added.

I also aim to include some things to automate the creation of some derived data
products (resolution-matched data cubes, aperture extraction of spectra, merging
spectral orders).

This toolset is made public, as it can serve as a good starting point for the
reduction of other similar observing programs.

## Pipeline workflow

The PDR programs (ERS-1288 and GTO-1192) all consist of NIRCam imaging, MIRI
imaging, NIRSpec IFU spectroscopy, and MIRI IFU spectroscopy. The steps for the
reduction of each of these are briefly explained below, and a few shell scripts that
implement these workflows are provided.

### Manual steps

Before running these tools on your data, the `_uncal` files have to be sorted according  to
1. object
2. instrument
3. exposure type: science, background, and (for nirspec only) science imprint,
   background imprint.

The provided shell scripts can then be copied, and the paths set in them can be
slightly modified to point to the directories containing the `_uncal` files. By
default, the provided scripts assume that they are placed at the same level as
the science, background, etc directories.

- object 1
  + nirspec
    - `nirspec_script.bash`
    - `science`
    - `science_imprint`
    - `background`
    - `background_imprint`
  + mirifu
    - `mirifu_script.bash`
    - `science`
    - `background`
- object 2
  ...

Side note on the historical reason for this: To work around some issues with the
default association files, we coded a simplified association generator. The
files need to be sorted for this generator to work, as it uses glob within a
directory.

### NIRSpec IFU

1. Stage 1 pipeline for `science, science_imprint, background,
   background_imprint`
2. 1/f noise reduction with NSclean (Rauscher, 2023arXiv230603250R), and custom
   masks.
3. Stage 2 for `science, background`, with imprints used.
4. Modify DQ array of `_cal` files, to make sure certain bad pixels are set to
   `DO_NOT_USE` (TODO: decide which flags)
5. Stage 3 with optional master background subtraction. The cube mosaic is
   built. Outlier reduction parameters should be tweaked to recommended values
   for NIRSpec.
6. TODO: alternate Stage 3, with WCS that better matches the mosaic footprint.

TODO: provide region files for aperture extraction, and provide a stitched
extracted spectrum in an extra script.

### MIRI IFU

1. Stage 1 pipeline for `science, background`
2. Stage 2 pipeline with optional image-to-image background subtraction
3. Stage 3 pipeline with master background subtraction, if the stage 2
   background was not performed.

### Imaging

This can be added later. Some alignment based on stellar catalogs will be
required. For NIRCam, a 1/f noise reduction would also be useful.

### Shell scripts

See `shell_scripts/`. It is recommended to copy one of these to your working
directory, and then modify the calls the `pipeline` script and extra cleaning
tools as needed.

Then run `bash script.bash` in the working directory where `science/` etc are
located.

## Installation

1. Clone this repository
2. Install the python package in your environment by running `pip install -e .`
   in the root directory of this repository. Alternatively, use `poetry
   install`, and then `poetry shell` to create and activate a new environment.
3. Install a manual dependency: NSClean, see [Paper on
   arxiv](https://arxiv.org/abs/2306.03250), and [download
   page](https://webb.nasa.gov/content/forScientists/publications.html).
   Download and `nsclean_1.9.tar.gz`, then `cd` into `nsclean_1.9/` and run `pip
   install .` in your environment.
