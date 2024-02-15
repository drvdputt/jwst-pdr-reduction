"""Open a cal file, and set the DO_NOT_USE bit to 1 for certain other DQ flags.

Mainly required for NIRSpec, but can maybe clean some of the other data too.

"""
from jwst import datamodels
from argparse import ArgumentParser
import numpy as np

ap = ArgumentParser()
ap.add_argument("input_cal")
ap.add_argument("--output_cal", default=None)
args = ap.parse_args()
# IF there are spikes other artifacts in s3d files - try to clean up the cal files.

# This is something I have added and is not standard. I have found that
# working with NIRSpec IFU data some some of the reference files do not
# have the DQ flags set to DO_NOT_USE, but other DQ flags indicate the
# data is not useable. By try and error I found these flags useful to
# set to DO_NOT_USE so the spec3 pipeline (cube_build_does not used them
# ) The NIRSPec team is currently updating reference files and flagging
# DQ values in the reference files appropriately. So eventully this will
# not be needed. You could turn off some of these flagging and compare
# the *_cal.fits to the *_cal_mod.fits and double check that the
# flagging does flag data you do not want

DO_NOT_USE = datamodels.dqflags.pixel["DO_NOT_USE"]
NO_SAT_CHECK = datamodels.dqflags.pixel["NO_SAT_CHECK"]
UNRELIABLE_FLAT = datamodels.dqflags.pixel["UNRELIABLE_FLAT"]
OTHER_BAD_PIXEL = datamodels.dqflags.pixel["OTHER_BAD_PIXEL"]
MSA_FAILED_OPEN = datamodels.dqflags.pixel["MSA_FAILED_OPEN"]
# this one may or may not be one you want to set. Currently the code
# to set these pixels to DO_NOT_USE is commented out (see below)

filename = args.input_cal
print("File", filename)
new_file = args.output_cal
print("new file", new_file)
input_cal = datamodels.IFUImageModel(filename)

flag_names = ["NO_SAT_CHECK", "UNRELIABLE_FLAT", "OTHER_BAD_PIXEL"]
apply_DNU_flags = [NO_SAT_CHECK, UNRELIABLE_FLAT, OTHER_BAD_PIXEL]
for flag_name, flag in zip(flag_names, apply_DNU_flags):
    dq_current = input_cal.dq
    bad = np.where(np.bitwise_and(dq_current, flag).astype(bool))[0]
    nbad = len(bad)

    dqtest = dq_current[bad]
    test = np.where(np.bitwise_and(dqtest, DO_NOT_USE).astype(bool))[0]
    ntest = len(test)

    n = nbad - ntest

    if n > 0:
        print(f"Number of pixels with {flag_name} but no DO_NOT_USE: ", n)
        input_cal.dq[bad] = np.bitwise_or(input_cal.dq[bad], DO_NOT_USE)
        input_cal.data[bad] = np.nan


# This one may not be need. You should check. Now expand the
# unrelaible_flat flag to be 1 pixel more along the edge of the slices
expand_flat = True
if expand_flat:
    dq_expand = input_cal.dq
    uflat = np.where(np.bitwise_and(dq_expand, UNRELIABLE_FLAT).astype(bool))
    nflat = len(uflat[0])
    # loop over the pixels with UNRELIABLE FLAT set. Check y+1, y-1 (not
    # sure which edge of the slice we on) and then these pixels to
    # UNRELIABLE_FLAT
    print("Looping over ", nflat)

    for i in range(nflat):
        ix = uflat[1][i]
        iy = uflat[0][i]
        input_cal.dq[iy + 1, ix] = np.bitwise_or(input_cal.dq[iy + 1, ix], DO_NOT_USE)
        input_cal.dq[iy + 1, ix] = np.bitwise_or(
            input_cal.dq[iy + 1, ix], UNRELIABLE_FLAT
        )

        input_cal.dq[iy - 1, ix] = np.bitwise_or(input_cal.dq[iy - 1, ix], DO_NOT_USE)
        input_cal.dq[iy - 1, ix] = np.bitwise_or(
            input_cal.dq[iy - 1, ix], UNRELIABLE_FLAT
        )

        input_cal.dq[iy - 2, ix] = np.bitwise_or(input_cal.dq[iy - 2, ix], DO_NOT_USE)
        input_cal.dq[iy - 2, ix] = np.bitwise_or(
            input_cal.dq[iy - 2, ix], UNRELIABLE_FLAT
        )

        input_cal.dq[iy + 2, ix] = np.bitwise_or(input_cal.dq[iy + 2, ix], DO_NOT_USE)
        input_cal.dq[iy + 2, ix] = np.bitwise_or(
            input_cal.dq[iy + 2, ix], UNRELIABLE_FLAT
        )


print("Saving to ", args.output_cal)
input_cal.save(args.output_cal)
