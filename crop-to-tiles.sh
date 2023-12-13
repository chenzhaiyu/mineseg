# Set output paths of the 256x256 segmentation patches
PATCHDIR=$1/_patches/patches
MASKSDIR=$1/_patches/masks

mkdir -p "$PATCHDIR"
mkdir -p "$MASKSDIR"


# Use find to locate all *.jp2 files recursively under the specified path
find "$1"/images -type f -name "*.jp2" | while IFS= read -r f
do
  echo "Processing file $f"
  /usr/bin/gdal_retile.py -v -ps 256 256 -overlap 128 -of PNG -targetDir "$PATCHDIR" "$f"
done


# Use find to locate all *.jp2 files recursively under the specified path
find "$1"/masks -type f -name "*.jp2" | while IFS= read -r f
do
  echo "Processing file $f"
  /usr/bin/gdal_retile.py -v -ps 256 256 -overlap 128 -of PNG -targetDir "$MASKSDIR" "$f"
done


# now get rid of completely black or small tiles and masks
for image in "$input_folder"/*.png; do

    # Use gdalinfo to get pixel value statistics for each band
    stats_r=$(gdalinfo -stats "$image" | grep -A 2 "Band 1" | tail -n 2)
    stats_g=$(gdalinfo -stats "$image" | grep -A 2 "Band 2" | tail -n 2)
    stats_b=$(gdalinfo -stats "$image" | grep -A 2 "Band 3" | tail -n 2)

    # Extract minimum and maximum pixel values for each band
    mean_val_r=$(echo "$stats_r" | grep -oP "Mean=.{3}" | cut -d= -f2)
    mean_val_g=$(echo "$stats_g" | grep -oP "Mean=.{3}" | cut -d= -f2)
    mean_val_b=$(echo "$stats_b" | grep -oP "Mean=.{3}" | cut -d= -f2)

    size_info=$(gdalinfo "$image" | grep "Size is")

    # Extract width and height from the size information
    width=$(echo "$size_info" | awk '{print $3}')
    height=$(echo "$size_info" | awk '{print $5}')

	# Check if all pixel values in all bands are zero
    if { [ "$mean_val_r" == "0.0" ] && [ "$mean_val_g" == "0.0" ] && [ "$mean_val_b" == "0.0" ] || $width != 256 || $height!=256 ; } then
        echo "Image $image is completely black or smaller then 256x256."
    else
        echo "Image $image is not completely black."
    fi

done