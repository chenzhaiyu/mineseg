# Set output paths of the 256x256 segmentation patches

ROI_IMAGES=$1
ROI_MASKS=$2

ROI_IMAGES_PATCHES=$1_patches
ROI_MASKS_PATCHES=$2_patches

mkdir -p "$ROI_IMAGES_PATCHES"
mkdir -p "$ROI_MASKS_PATCHES"


# Use find to locate all *.jp2 files recursively under the specified path
find "$ROI_IMAGES" -type f -name "*_TCI.jp2" | while IFS= read -r f
do
  echo "Processing file $f"
  /usr/bin/gdal_retile.py -v -ps 256 256 -overlap 128 -of PNG -targetDir "$ROI_IMAGES_PATCHES" "$f"
done


# Use find to locate all *.jp2 files recursively under the specified path
find "$ROI_MASKS" -type f -name "*_TCI.jp2" | while IFS= read -r f
do
  echo "Processing file $f"
  /usr/bin/gdal_retile.py -v -ps 256 256 -overlap 128 -of PNG -targetDir "$ROI_MASKS_PATCHES" "$f"
done



# now get rid of completely black or small tiles and masks
for image in "$ROI_IMAGES"/*.png; do

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

    # Extract width and height from the size information
    width=$(echo "$size_info" | awk '{print $3}')
    height=$(echo "$size_info" | awk '{print $5}')

    # Check if all pixel values in all bands are zero
    if { [ "$mean_val_r" == "0.0" ] && [ "$mean_val_g" == "0.0" ] && [ "$mean_val_b" == "0.0" ] || $width != 256 || $height!=256 ; } then
        echo "Image $image is completely black or smaller then 256x256."
        rm $ROI_IMAGES/fname
        rm $ROI_MASKS/fname
    else
        echo "Image $image is not completely black."
    fi

done
