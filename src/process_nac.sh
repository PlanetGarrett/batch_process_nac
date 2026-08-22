#!/bin/bash
# $1 edr_name
# $2 boolean if nac has crosstrack_summing = 2
# s3 boolean if want to do photometric correction (heavy load)
# $4 boolean if using lronacpho instead of photomet
# $5 center longitude
# $6 center latitude
# $7 patch size
# $8 if want tif
# $9 working directory
# $10 if user dem
# $11 dem path
edr_file="${1}.IMG"
raw_cub_file="${1//E}.raw.cub"
cal_file="${1//E}.cal.cub"
echo_file="${1//E}.echo.cub"
trim_file="${1//E}.tr.cub"
pho_file="${1//E}.pho.cub"
pvl_file="${1//E}.pvl"
cub_file="${1//E}.cub"
tif_file="${1//E}.tif"

# Initialize Conda for this script session
eval "$(conda shell.bash hook)"

conda activate isis

cd $9

lronac2isis from=$edr_file to=$raw_cub_file
echo "raw cub was produced ${raw_cub_file}"

# Spice
if [[ ${10} == "true" ]]; then
    echo "Using user DEM for spiceinit: ${11}"
    spiceinit from=$raw_cub_file spksmithed=true web=true shape=user model=${11}
else
    spiceinit from=$raw_cub_file spksmithed=true web=true
fi
echo "raw cub was spiced"

# Calibrate
lronaccal from=$raw_cub_file to=$cal_file
echo "spiced was calibrated"

# Echo correction
lronacecho from=$cal_file to=$echo_file
echo "cal was echoed"

# Set trim values
trim_1=46
trim_2=26
if [[ $2 == "true" ]]; then
    trim_1=23
    trim_2=13
fi

# Trim dark borders produced by echo
if [[ "$1" == *"L"* ]]; then
    echo "Left camera trim"
    trim from=$echo_file to=$trim_file left=$trim_1 right=$trim_2
else
    echo "Right camera trim"
    trim from=$echo_file to=$trim_file left=$trim_2 right=$trim_1
fi
echo "echo was trimmed"

# Photometric correction
if [[ $3 == "true" ]]; then
    if [[ $4 == "true" ]]; then
        lronacpho from=$trim_file to=$pho_file phopar=../config/nacpho.pvl
    else
        photomet from=$trim_file to=$pho_file frompvl=../config/basicpho.pvl
    fi
    echo "trim was photometrically calibrated"
fi

maptemplate map=$pvl_file projection=equirectangular clon=$5 clat=$6 targopt=user targetname=Moon londom=180

cam2map from=$trim_file to=$cub_file map=$pvl_file warpalgorithm=forwardpatch patchsize=$7
echo 'NAC projected into cub'

if [[ $8 == "true" ]]; then
    gdal_translate -of GTiff -ot Float32 -co COMPRESS=DEFLATE -co PREDICTOR=3 -a_nodata 0 -scale $cub_file $tif_file
    echo 'geotiff produced'
fi

echo 'ISIS processing complete'

conda deactivate