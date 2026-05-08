from sys import argv

from astropy.io import fits
from astropy import units as u
from astropy.wcs import WCS
from specutils import Spectrum

from ismwestern.general import spectrumutils
from ismwestern import io

fn = argv[1]
h = fits.open(fn)
w = WCS(h[1].header)
s = spectrumutils.spectrum_from_arrays(
    flux=h[1].data * u.MJy / u.sr * 83, spectral_axis=h["WAVE"].data * u.um, wcs=w.celestial
)
s.write(fn.replace('.fits', 's3d.fits'), format='jwst')
