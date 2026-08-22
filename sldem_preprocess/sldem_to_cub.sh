#!/bin/bash
# $1 lbl file
# $2 name for cub file
# $3 working directory

# Initialize Conda for this script session
eval "$(conda shell.bash hook)"

conda activate isis

cd $3

pds2isis from=$1 to=$2

echo "Cub produced ${2}"

conda deactivate