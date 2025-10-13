#!/bin/bash

# This file goes through all geotiff (*.tif) files in a given folder
# and extracts the extents/bounding box of these files and collects them 
# in a *.geojson file 
# call: create_footprints.sh path/to/geotiffs path/to/footprints.geojson
# prerequ.: gdal
# # # #



# Set the source directory containing the TIFF files
src_dir=$1

# Set the destination directory for the shapefiles
dst_file=$2

# Create the destination directory if it doesn't exist
mkdir -p "$dst_dir"

# Loop through each TIFF file in the source directory
for tif_file in "$src_dir"/*.tif; do

  # Get the base name of the TIFF file (without the extension)
  base_name=$(basename "$tif_file" .tif)
  
  # Run gdal_footprint to create the output
  gdal_footprint "$tif_file" "$dst_file"
  
  echo "Created footprint for $tif_file at $dst_file"

done
