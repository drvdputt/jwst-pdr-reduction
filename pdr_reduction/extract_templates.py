"""Script to do the extraction, given the template file and a list of
cubes.

"""
import argparse
from astropy.table import Table
from astropy import units as u
from regions import Regions
from specutils import Spectrum1D
from pahfitcube.cube_aperture import cube_sky_aperture_extraction
from myastro import spectral_segments, regionhacks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "region_file",
        help="File containing DS9 regions representing template apertures.",
    )
    ap.add_argument(
        "cube_files", nargs="+", help="Data cubes to extract from and merge."
    )
    ap.add_argument(
        "--apply_offsets",
        action="store_true",
        help="""Apply additive offsets to make the spectral stitching
        smoother. Resulting continuum might be unrealistic.""",
    )
    ap.add_argument(
        "--reference_segment",
        type=int,
        help="""Index of the cube to use as a reference for spectral stitching"""
    )
    ap.add_argument(
        "--template_names",
        nargs="+",
        help="""Optional list of names to give to the template spectra.
        Number of arguments must equal the number of apertures in the given
        region file. E.g. "HII", "Atomic", "DF3", "DF2", "DF1" for the Orion
        templates.""",
    )
    args = ap.parse_args()

    # load the cubes
    cubes = spectral_segments.sort(
        [Spectrum1D.read(cf, format="JWST s3d") for cf in args.cube_files]
    )

    # set up template apertures and names
    regions = Regions.read(args.region_file)
    apertures = [regionhacks.skyregion_to_aperture_auto(r) for r in regions]

    # determine template names
    if args.template_names is None:
        template_names = [f"T{i}" for i in range(1, len(apertures) + 1)]
    else:
        template_names = args.template_names

    t = extract_templates_table(cubes, apertures, template_names, args.apply_offsets)
    fname = "templates.ecsv"
    print(f"Writing extracted spectra to {fname}")
    t.write(fname, overwrite=True)


# define this local utility function
def extract_and_merge(cubes, aperture, apply_offsets):
    """Steps that need to happen for every aperture.

    1. extract from every given cube
    2. apply stitching corrections
    3. return a single merged spectrum"""
    specs = [cube_sky_aperture_extraction(s, aperture) for s in cubes]

    if apply_offsets:
        shifts = spectral_segments.overlap_shifts(specs)
        # choose a segment in the middle as the reference for the stitching
        offsets = spectral_segments.shifts_to_offsets(shifts, len(specs) // 2)
        specs_to_merge = [s + o for s, o in zip(specs, offsets)]
    else:
        specs_to_merge = specs

    return spectral_segments.merge_1d(specs_to_merge)


def extract_templates_table(cubes, apertures, template_names, apply_offsets=False):
    templates = {
        k: extract_and_merge(cubes, a, apply_offsets)
        for k, a in zip(template_names, apertures)
    }

    # Construct astropy table and save as ECSV
    columns = {
        "wavelength": templates[template_names[0]].spectral_axis.to(u.micron),
    }
    for k, v in templates.items():
        columns[f"flux_{k}"] = v.flux
        columns[f"unc_{k}"] = v.uncertainty.array * v.flux.unit

    t = Table(columns)
    return t


if __name__ == "__main__":
    main()
