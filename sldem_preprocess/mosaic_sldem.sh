#!/bin/bash
# $1 working directory

# Initialize Conda for this script session
eval "$(conda shell.bash hook)"

conda activate isis

cd $1

automos fromlist=sldem.lis mosaic=SLDEM_km.cub matchbandbin=false
echo 'cubs mosaiced'

fx f1=SLDEM_km.cub to=SLDEM_m_rad.cub equation="f1*1000"
echo 'mosaic units converted'

demprep from=SLDEM_m_rad.cub to=SLDEM.demprep.cub
echo 'dem prepared for use'

conda deactivate