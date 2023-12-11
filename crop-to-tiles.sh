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


