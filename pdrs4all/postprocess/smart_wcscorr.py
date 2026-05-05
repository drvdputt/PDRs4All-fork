import asdf
from astropy.io import fits
from astropy import units as u
import json
import argparse

def make_offset_file_nirspec():
    pass


def make_offset_file_mirifu(
    level3_asn_file,
    offset_short=(0, 0.14),
    offset_medium=(0, 0.14),
    offset_long=(0, 0.14),
):
    """We only have the disk coordinates to go by. So for now, it's a
    global offset for short / medium / long

    I have supplied default values (in arcsec) based on the following
    observation.

    Offsets from the wcscorr using proplyd are not consistent (depend on
    WCS chosen). Which ones to pick then? Ch1wcs ones are very
    consistent between A,B,C. Makes sense as they're oversampled to
    resolves PSF peak better maybe.

    default: [(<Angle 3.54861437e-06 deg>, <Angle 4.0649258e-05 deg>),
    (<Angle 6.54209285e-06 deg>, <Angle 2.40642612e-05 deg>),
    (<Angle -1.16205216e-05 deg>, <Angle 5.74031503e-05 deg>)]

    ch1wcs: [(<Angle 3.54874749e-06 deg>, <Angle 4.06493016e-05 deg>),
    (<Angle 3.46451318e-06 deg>, <Angle 4.06588569e-05 deg>),
    (<Angle 3.50556408e-06 deg>, <Angle 4.06929241e-05 deg>)]

    ==> 3.5e-6 deg = 0.01 arcsec (effectively zero)
        4.065e-5 deg = 0.14 arcsec approx 1 pixel

    ch4wcs: [(<Angle -1.45809456e-05 deg>, <Angle 2.55355894e-05 deg>),
    (<Angle -1.45315868e-05 deg>, <Angle 2.54494603e-05 deg>),
    (<Angle -1.45292235e-05 deg>, <Angle 2.54867052e-05 deg>)]

    Question: Do these change between data reduction versions? Maybe WCS
    calibration can improve still.

    Guideline: When releasing a new data reduction, run python -m
    pdrs4all.postprocess.mrs_simple_wcscorr; it will print angle offset
    values for RA/Dec like those shown above.

    Parameters
    ----------

    level3_asn_file: path
        Level 3 association file containing all input files that will be
        used to build the cubes. Will typically be the CRF files created
        by the stage3 pipeline, which are then used to build the custom
        cubes.

    offset_*: pair (degrees, degrees)
        offsets for each observation, representing offset to apply to RA
        and Dec. We currently have no way to correct individual mosaic
        tiles or dither positions, so these offsets are applied
        globally.

    """
    # pseudocode
    with open(level3_asn_file, "r") as f:
        asn_tree = json.load(f)
    filename = [m["expname"] for m in asn_tree["products"][0]["members"]]
    raoffset = []
    decoffset = []

    radict = {
        "SHORT": offset_short[0],
        "MEDIUM": offset_medium[0],
        "LONG": offset_long[0],
    }
    decdict = {
        "SHORT": offset_short[1],
        "MEDIUM": offset_medium[1],
        "LONG": offset_long[1],
    }

    for f in filename:
        band = fits.open(f)[0].header["band"]  # find short/medium/long
        raoffset.append(radict[band])
        decoffset.append(decdict[band])

    write_offsets_file(
        level3_asn_file.replace(".json", "_offsets.asdf"), filename, raoffset, decoffset
    )


def write_offsets_file(fn_asdf, filename, raoffset, decoffset):
    tree = {
        "units": str(u.arcsec),
        "filename": filename,
        "raoffset": raoffset,
        "decoffset": decoffset,
    }

    with asdf.AsdfFile(tree) as af:
        af.write_to(fn_asdf)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Create offsets file for MIRI IFU ASN file; uses hardcoded shifts")
    ap.add_argument('asn')
    args = ap.parse_args()
    make_offset_file_mirifu(args.asn)
