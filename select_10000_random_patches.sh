#!/bin/bash

# Define source and destination directories
SOURCE_DIR="./CHILE/patches"
DEST_DIR="./mines_train/patches_temp"
MASK_DIR="./mines_train/masks/patches_temp"

mkdir $DEST_DIR
mkdir $MASK_DIR

# Find and process 10,000 GeoTIFF files
find "$SOURCE_DIR" -type f -name "*.tif" | shuf -n 10000 | while read -r file; do
  
  # Copy the file to the destination directory
  cp "$file" "$DEST_DIR"
  
  # Get the filename without the directory
  filename=$(basename "$file")
  
  # Create the output mask file path
  mask_file="$MASK_DIR/$filename"
  
  # Create a grayscale mask with all pixels set to zero
  gdal_calc.py -A "$file" --outfile="$mask_file" --calc="0" --type=Byte

done
