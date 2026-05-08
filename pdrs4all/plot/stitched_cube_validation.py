"""Plot to check quality of cube stitching

Input: stitched cube and original individual cubes; must be the
"aligned" cubes, e.g. ch1wcs or ch4wcs produced by
postprocess_mirifu.bash

Plots: Merged spectrum and segments for a few random pixels

"""

from argparse import ArgumentParser
from .templates_overview import nice_ticks
from matplotlib import pyplot as plt
from typing import Iterable
from specutils import Spectrum


def plot_cube_spaxel(ax, cube, x, y, **kwargs):
    return ax.plot(cube.spectral_axis.value, cube.flux.value[:, y, x], **kwargs)


def plot_same_spaxel(
    ax,
    x: int,
    y: int,
    cube_stitched: Spectrum,
    cubes_other: Iterable[Spectrum],
    color_stitched=None,
    color_other=None,
):
    line_stitched = plot_cube_spaxel(
        ax, cube_stitched, x, y, color=color_stitched, label=str((x, y))
    )

    if color_other is None:
        color_other = line_stitched[0].get_color()
        alpha = 0.3
    else:
        alpha = 1

    for cube in cubes_other:
        plot_cube_spaxel(ax, cube, x, y, color=color_other, alpha=alpha)


if __name__ == "__main__":
    ap = ArgumentParser()
    ap.add_argument("stitched_cube")
    ap.add_argument(
        "--segments",
        nargs="+",
        help="Cubes from which the stitched cube was built. Must be same shape.",
    )

    # TODO: option here to choose pixels

    args = ap.parse_args()

    cube_stitched = Spectrum.read(args.stitched_cube, format="JWST s3d")
    list_cube_segments = [Spectrum.read(f) for f in args.segments]

    y_mid = cube_stitched.shape[1] // 2
    x_max = cube_stitched.shape[2]
    list_pix = [(y_mid, x) for x in (x_max // 4, x_max // 2, x_max // 4 * 3)]

    fig, ax = plt.subplots()
    for y, x in list_pix:
        plot_same_spaxel(ax, x, y, cube_stitched, list_cube_segments)

    nice_ticks(ax)

    ax.legend()

    plt.show()
