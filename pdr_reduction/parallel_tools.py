# this has problems returning the JWST datamodels (i.e. the output of
# the steps), because they're not pickleable. But the import below
# works! It's a third-party package that uses dill for pickling
from multiprocess.pool import Pool
from functools import partial


def run_stage_many(max_cores, obsfiles, stage_class, stage_options_dict=None):
    """
    Run the same stage on many files.

    The call() function will be used.

    Parameters
    ----------

    obsfiles: list of str
        Fits files used as input (strings)

    stage_options_dict: dict
        Dictionary of options passed to the call() function for the
        stage. After unpacking using **, it should look like this
        example from the documentation.

        result = Detector1Pipeline.call('jw00017001001_01101_00001_nrca1_uncal.fits',
                                        steps={'jump': {'threshold': 12.0, 'save_results':True}})

    """
    kwargs = {} if stage_options_dict is None else stage_options_dict
    # define wrapper to call with kwargs already filled in. The only
    # other argument is the first positional one, which
    # run_function_many will fill in.
    f = partial(stage_class.call, **kwargs)
    run_function_many(f, obsfiles, max_cores)


def run_function_many(func, args, max_cores):
    """Run a function that takes a single argument in parallel.

    CAUTION: do not use with jwst pipeline or step objects, since I
    found that there are some problems if the same instance is reused.
    E.g., some of the output files get the wrong name or are
    overwritten. The workaround is run_stage_many().

    """
    if max_cores > 1:
        print("running in parallel on ", args)
        p = Pool(max_cores)
        _ = p.map(func, args)
        p.close()
        p.join()
    else:
        print("running normal for loop over", args)
        for x in args:
            func(x)
