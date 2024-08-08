#!/bin/bash

# This file selects 10.000 random geotiff patches from the CHILE set and adds 
# them as background class to the training set. 
# This strategy is based on the assumption that >99% of the area of CHILE is not 
# of class "miningsite"
# call: select_10000_random_patches.sh
# # # # # #


# Define source and destination directories
SOURCE_DIR="./CHILE/patches"
TRAIN_DIR="./mines_train/patches_temp"
MASK_DIR="./mines_train/masks/patches_temp"

# create destination and mask folder in the training set
mkdir $TRAIN_DIR
mkdir $MASK_DIR

# Find and process 10,000 GeoTIFF files
find "$SOURCE_DIR" -type f -name "*.tif" | shuf -n 10000 | while read -r file; do
  
  # Copy the file to the destination directory
  cp "$file" "$TRAIN_DIR"
  
  # Get the filename without the directory
  filename=$(basename "$file")
  
  # Create the output mask file path
  mask_file="$MASK_DIR/$filename"
  
  # Create a grayscale mask with all pixels set to zero
  gdal_calc.py -A "$file" --outfile="$mask_file" --calc="0" --type=Byte

done
