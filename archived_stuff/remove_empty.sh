#!/bin/bash
ROI_IMAGES_PATCHES=$1_patches
ROI_MASKS_PATCHES=$2_patches


# now get rid of completely black or small tiles and masks
for image in "$ROI_IMAGES_PATCHES"/*.png; do

    fname=$(basename "$image")

    # Use gdalinfo to get pixel value statistics for each band
    stats_r=$(gdalinfo -stats "$image" | grep -A 2 "Band 1" | tail -n 2)
    stats_g=$(gdalinfo -stats "$image" | grep -A 2 "Band 2" | tail -n 2)
    stats_b=$(gdalinfo -stats "$image" | grep -A 2 "Band 3" | tail -n 2)

    # Extract minimum and maximum pixel values for each band
    mean_val_r=$(echo "$stats_r" | grep -oP "Mean=.{3}" | cut -d= -f2)
    mean_val_g=$(echo "$stats_g" | grep -oP "Mean=.{3}" | cut -d= -f2)
    mean_val_b=$(echo "$stats_b" | grep -oP "Mean=.{3}" | cut -d= -f2)

    size_info=$(gdalinfo "$image" | grep "Size is")	
	
    # Extract width value
    width=$(echo "$size_info" | awk '{print $3}' | awk -F ',' '{print $1}')

	# Extract height value
	height=$(echo "$size_info" | awk '{print $4}')
	
	echo "$fname": 
	echo "     " width: "$width", height: "$height", green: "$mean_val_g", red: "$mean_val_r", blue: "$mean_val_b"

    if [[ ( "$mean_val_r" == "0.0" && "$mean_val_g" == "0.0" && "$mean_val_b" == "0.0" ) || ( $width -ne 256 || $height -ne 256 ) ]]; then
        echo "      Image is completely black or smaller than 256x256 -> DELETE"
        rm -f "$ROI_IMAGES_PATCHES/$fname"
        rm -f "$ROI_MASKS_PATCHES/$fname"
    else
        echo ""
    fi
	echo ""

done
