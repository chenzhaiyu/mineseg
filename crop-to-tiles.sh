TARGDIR=$2
FILES=$1

mkdir -p "$TARGDIR"

# Use find to locate all *.jp2 files recursively under the specified path
find "$FILES" -type f -name "*.jp2" | while IFS= read -r f
do
  echo "Processing file $f"
  /usr/bin/gdal_retile.py -v -ps 256 256 -overlap 128 -of PNG -targetDir "$TARGDIR" "$f"
done
