#!/bin/bash

# Set the directory containing the files
input_dir="./outputs/unet/"
output_dir="./outputs/unet_merged/"

# create output folder
mkdir $output_dir

# Initialize an associative array to track unique base filenames
declare -A base_filenames

# Count the total number of files
total_files=$(find "${input_dir}" -type f -name '_Chile_*_mask.tif' | wc -l)
processed_files=0

echo "Extracting unique base filenames..."

# Loop over all the files with the specific pattern in the input directory
for file in "${input_dir}"_Chile_*_mask.tif; do
  # Extract the base filename by removing the patch indices and suffix
  base=$(basename "$file" | sed 's/_[0-9]\+_[0-9]\+_mask\.tif$//')
  
  # Store the base filename in the associative array
  base_filenames["$base"]=1
  
  # Update progress
  processed_files=$((processed_files + 1))
  echo -ne "Progress: $((processed_files * 100 / total_files))%\r"
done

echo -ne "Extracting unique base filenames completed!\n"

# Count the number of unique base filenames
total_bases=${#base_filenames[@]}
processed_bases=0

echo "Merging tiles..."

# Loop through each unique base filename and merge the tiles
for base in "${!base_filenames[@]}"; do
  # Construct the output filename
  output="${output_dir}${base}_combined_mask.tif"
  
  # Use gdal_merge.py to merge the tiles
  # gdal_merge.py -o $output ${input_dir}${base}_*.tif

  # create cloud-optimized tif files
  gdal_merge.py -o $output ${input_dir}${base}_*.tif -co TILED=YES -co COMPRESS=LZW -co COPY_SRC_OVERVIEWS=YES

  # create and append to raster-footprint geojson
  gdal_footprint "$output" "merged_raster_footprints.geojson"
  
  # Update progress
  processed_bases=$((processed_bases + 1))
  echo -ne "Progress: $((processed_bases * 100 / total_bases))%\r"
done

echo -ne "Merging tiles completed!\n"

# Create a VRT file from the merged output files
echo "Creating VRT file..."
gdalbuildvrt output.vrt ./$output_dir/*.tif
