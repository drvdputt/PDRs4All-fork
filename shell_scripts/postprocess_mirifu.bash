set -x
# Where the postprocessing scripts are stored. Needs to be set by user.
ROOT=~/Repositories/pdrs4all

set -e
# point the script to where the pipeline output is
RUNDIR="$1"

JWSTVERSION="$(python -c 'import jwst; print(jwst.__version__)')"
PMAPVERSION="$(python -c 'import crds; print(crds.get_context_name("jwst"))')"

NEWDIR=vX.X_auto_"$PMAPVERSION"_"$JWSTVERSION"
echo mkdir -p "$NEWDIR"
mkdir -p "$NEWDIR"

for d in log crf templates cubes/default
do mkdir -p "$NEWDIR"/"$d"
done

# log files
cp "$RUNDIR"/log/* "$NEWDIR"/log

# crf files (for nirspec, nscleaned output is in separate directory
cp "$RUNDIR"/science/stage3/*crf.fits "$NEWDIR"/crf

# for mirifu, the cubes build in stage 3 without problems, so we can just copy them here
cp "$RUNDIR"/science/stage3/*s3d.fits "$NEWDIR"/cubes/default

# we are now done copying stuff. We will process the crf files further.
cd "$NEWDIR"/crf

# First, create association files for each detector and band setting, based on a file pattern
# (works only for orion data). If you use this for other data, then you will have to figure out
# the appropriate files to build each segment.

# LONG = 02111 - 0211h

create_association 12LONG_crf jw01288002001_0211[13579bdfh]*_mirifushort_*_crf.fits
create_association 34LONG_crf jw01288002001_0211[13579bdfh]*_mirifulong_*_crf.fits
# MEDIUM = 0210j - 0210z
create_association 12MEDIUM_crf jw01288002001_0210[jlnprtvxz]*_mirifushort_*_crf.fits
create_association 34MEDIUM_crf jw01288002001_0210[jlnprtvxz]*_mirifulong_*_crf.fits
# SHORT = 02101 - 0210h
create_association 12SHORT_crf jw01288002001_0210[13579bdfh]*_mirifushort_*_crf.fits
create_association 34SHORT_crf jw01288002001_0210[13579bdfh]*_mirifulong_*_crf.fits

# make offset files for cube_build with WCS correction included.
for ASN in *crf_asn.json; do
    python3 -m pdrs4all.postprocess.smart_wcscorr $ASN
done

mkdir -p ../cubes/default_offset ../cubes/ch1wcs ../cubes/ch1wcs_offset ../cubes/ch4wcs ../ch4wcs_offset
PAOPT="--cube_pa=250.42338204969806"
CH1OPT="${PAOPT} --scalexy 0.13 --ra_center 83.83535169747073 --dec_center -5.419729392828107  --nspax_x 213 --nspax_y 41"
CH4OPT="${PAOPT} --cube_pa=250.42338204969806 --scalexy 0.35 --ra_center 83.83535169747073 --dec_center -5.419729392828107 --nspax_x 91 --nspax_y 29"
for ASN in *crf_asn.json; do
    OFFSET_FILE="${ASN%.json}_offsets.asdf" 
    strun cube_build $ASN --output_dir ../cubes/default_offset --cube_pa=250.42338204969806 --offset_file $OFFSET_FILE
    strun cube_build $ASN --output_dir ../cubes/ch1wcs $CH1OPT
    strun cube_build $ASN --output_dir ../cubes/ch1wcs_offset $CH1OPT $OFFSET_FILE
    strun cube_build $ASN --output_dir ../cubes/ch4wcs $CH4OPT
    strun cube_build $ASN --output_dir ../cubes/ch4wcs_offset $CH4OPT $OFFSET_FILE
done

# Simple WCS correction for default cubes: this does not change the data, only the WCS prameters -> after correcting, no longer aligned.
# python3 -m pdrs4all.postprocess.mrs_simple_wcscorr
# cubes/default/*s3d.fits --output_dir cubes/default_wcscorr python3 -m
# pdrs4all.postprocess.mrs_simple_wcscorr cubes/ch1wcs/*s3d.fits --output_dir
# cubes/ch1wcs_wcscorr python3 -m pdrs4all.postprocess.mrs_simple_wcscorr cubes/ch4wcs/*s3d.fits
# --output_dir cubes/ch4wcs_wcscorr ideally we want to apply the WCS correction BEFORE building
# the cubes, or by creating the "shifts" json file (see cube_build step documentation)

cd ..

# templates extracted from different versions of the cubes
extract_templates "$ROOT"/regions/aper_T_DF_extraction.reg cubes/default/*s3d.fits --template_names "HII" "Atomic" "DF3" "DF2" "DF1" -o templates/default_nostitch.ecsv
extract_templates "$ROOT"/regions/aper_T_DF_extraction.reg cubes/default/*s3d.fits --template_names "HII" "Atomic" "DF3" "DF2" "DF1" --apply_offsets --reference_segment 0 -o templates/default_addstitch.ecsv

extract_templates "$ROOT"/regions/aper_T_DF_extraction.reg cubes/default_offset/*s3d.fits --template_names "HII" "Atomic" "DF3" "DF2" "DF1" -o templates/default_offset_nostitch.ecsv
extract_templates "$ROOT"/regions/aper_T_DF_extraction.reg cubes/default_offset/*s3d.fits --template_names "HII" "Atomic" "DF3" "DF2" "DF1" --apply_offsets --reference_segment 0 -o templates/default_offset_addstitch.ecsv

# naive ch4 stitch for now. Possible improvements: use better ch4 cubes (built using offsets to
# correct WCS), and using additive or multiplicative flux corrections
python3 -m pdrs4all.postprocess.naive_cube_merge cubes/ch4wcs_offset/*s3d.fits -o cubes/ch4wcs_offset_stitched_s3d.fits
