# checks for completely black images and deletes them
# this is useful after the cutting into tiles and masks

# get the path as parameter from command line
SEARCHPATH=$1
PATCHDIR=patches
MASKSDIR=masks

# now get rid of completely black tiles and masks
for image in "$SEARCHPATH"/$PATCHDIR/*.png; do

    FILENAME=$(basename "$image")
	
    # Use gdalinfo to get pixel value statistics for each band
    stats_r=$(gdalinfo -stats "$image" | grep -A 2 "Band 1" | tail -n 2)
    stats_g=$(gdalinfo -stats "$image" | grep -A 2 "Band 2" | tail -n 2)
    stats_b=$(gdalinfo -stats "$image" | grep -A 2 "Band 3" | tail -n 2)

    # Extract minimum and maximum pixel values for each band
    mean_val_r=$(echo "$stats_r" | grep -oP "Mean=.{3}" | cut -d= -f2)
    mean_val_g=$(echo "$stats_g" | grep -oP "Mean=.{3}" | cut -d= -f2)
    mean_val_b=$(echo "$stats_b" | grep -oP "Mean=.{3}" | cut -d= -f2)

	# Check if all pixel values in all bands are zero
    if [ "$mean_val_r" == "0.0" ] && [ "$mean_val_g" == "0.0" ] && [ "$mean_val_b" == "0.0" ]; then
        echo "Image $image is completely black."
        echo "       delete " $SEARCHPATH/$PATCHDIR/$FILENAME
		rm $SEARCHPATH/$PATCHDIR/$FILENAME
        echo "       delete " $SEARCHPATH/$MASKSDIR/$FILENAME
		rm $SEARCHPATH/$MASKSDIR/$FILENAME
		
    else
        echo "Image $image is not completely black."
    fi
done
