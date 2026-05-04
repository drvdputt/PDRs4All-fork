import asdf
from astropy.io import fits
from astropy import units as u
import json


def make_offset_file_nirspec():
    pass


def make_offset_file_mirifu(
    level3_asn_file, offset_short=(0, 0), offset_medium=(0, 0), offset_long=(0, 0)
):
    """We only have the disk coordinates to go by. So for now, it's a
    global offset for short / medium / long

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

    write_offsets_file(level3_asn_file.replace(".json", "_offsets.asdf"), filename, raoffset, decoffset)


def write_offsets_file(fn_asdf, filename, raoffset, decoffset):
    tree = {
        "units": str(u.arcsec),
        "filename": filename,
        "raoffset": raoffset,
        "decoffset": decoffset,
    }

    with asdf.AsdfFile(tree) as af:
        af.write_to(fn_asdf)
