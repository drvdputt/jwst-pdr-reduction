from jwst.pipeline import (
    Detector1Pipeline,
    Spec2Pipeline,
    Spec3Pipeline,
    Image2Pipeline,
    Image3Pipeline,
)


def default_dict(output_dir):
    return dict(output_dir=output_dir, save_results=True)


def pipeline_class_and_options_dict(stage, instrument, output_dir):
    """Choose pipeline and return options.

    This is done in a function to avoid some duplication

    Parameters
    ----------

    stage: int
        1, 2, or 3

    instrument: str
        instrument/mode string. Allowed values are NRS_IFU, MIR_MRS,
        NIR_IMAGE, MIR_IMAGE

    output_dir: str
        Output directory to set in the options dictionary.
    """
    options = default_dict(output_dir)

    if stage == 1:
        class_name = Detector1Pipeline

    # shorthand
    skiptrue = {"skip": True}
    skipfalse = {"skip": False}

    if instrument == "NRS_IFU":
        if stage == 2:
            class_name = Spec2Pipeline
        if stage == 3:
            class_name = Spec3Pipeline
            options["steps"] = {
                "outlier_detection": skipfalse,
                "cube_build": {
                    "grating": "all",
                    "filter": "all",
                    "output_type": "band",
                    "coord_system": "ifualign",
                    "weighting": "drizzle",
                },
            }

    if instrument == "MIR_MRS":
        if stage == 1:
            options.update(
                {
                    "steps": {
                        # "refpix": skiptrue,
                        # "reset": skiptrue,
                        # "rscd": skiptrue,
                    }
                }
            )
        if stage == 2:
            class_name = Spec2Pipeline
            options["steps"] = {
                # background subtraction active in stage 2 and 3. But
                # will only actually run if bg files are given. So this
                # way, we can choose on the command line which
                # background subtraction to do (by using the '-b' option
                # in either stage 2 or 3, but not both).
                "bkg_subtract": skipfalse,
                "residual_fringe": skipfalse,
            }
        if stage == 3:
            class_name = Spec3Pipeline
            options["steps"] = {
                "master_background": skipfalse,
                "outlier_detection": skipfalse,
                "mrs_imatch": skiptrue,
                "extract_1d": skiptrue,
                "cube_build": {"output_type": "band", "coord_system": "ifualign"},
            }

    if instrument == "NRC_IMAGE":
        if stage == 1:
            options.update(
                {
                    "steps": {
                        "ramp_fit": {"suppress_one_group": False},
                    }
                }
            )
        if stage == 2:
            class_name = Image2Pipeline
            # no additional options
        if stage == 3:
            class_name = Image3Pipeline
            options["steps"] = {"tweakreg": skiptrue}

    if instrument == "MIR_IMAGE":
        if stage == 1:
            options.update(
                {
                    "steps": {
                        "refpix": skiptrue,
                        "reset": skiptrue,
                        "rscd": skiptrue,
                        # "jump": {
                        #     "three_group_rejection_threshold": 1.0,
                        #     "save_results": True,
                        # },
                        # "ramp_fit": {"save_opt": True, "save_results": True},
                    }
                }
            )
        if stage == 2:
            class_name = Image2Pipeline
            options["steps"] = {"resample": skiptrue}
        if stage == 3:
            class_name = Image3Pipeline
            options["steps"] = {
                "assign_mtwcs": skiptrue,
                "skymatch": skiptrue,
                "source_catalog": skiptrue,
            }

    return class_name, options
