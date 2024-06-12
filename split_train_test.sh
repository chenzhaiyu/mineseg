# run this script inside the source code folder

path=./

mkdir -p $path/patches_img_testset
mkdir -p $path/patches_img_trainset
mkdir -p $path/patches_mask_testset
mkdir -p $path/patches_mask_trainset

# Define the regions of interest that are defined as test set
lines=(
    "roi_\[-70.187396, -27.599106, -70.361804, -27.395674\]_0_0"
    "roi_\[-70.319232, -34.122725, -70.536212, -34.05221\]_0_0"
    "roi_\[-68.742694, -23.510611, -68.88689, -23.34428\]_0_0"
    "roi_\[-71.042956, -30.309592, -71.155566, -30.16722\]_0_0"
    "roi_\[-70.838336, -32.601905, -70.908374, -32.553302\]_0_0"
    "roi_\[-71.347827, -30.034153, -71.376666, -30.004426\]_0_0"
    "roi_\[-68.604592, -22.090307, -68.892984, -21.858526\]_1_1"
    "roi_\[-69.2, -26.866472, -69.307117, -26.729182\]_0_0"
    "roi_\[-68.520822, -21.076386, -68.896417, -20.866085\]_1_0"
    "roi_\[-69.232959, -27.588152, -69.344195, -27.511445\]_0_0"
    "roi_\[-69.802875, -25.889626, -69.978656, -25.741278\]_0_0"
    "roi_\[-70.565051, -25.688075, -70.611743, -25.641038\]_0_0"
    "roi_\[-69.926471, -29.837791, -70.039081, -29.697126\]_0_0"
    "roi_\[-71.593646, -52.900706, -71.756381, -52.809075\]_0_0"
    "roi_\[-70.194263, -33.248571, -70.394763, -33.053111\]_0_0"
    "roi_\[-71.200885, -29.766291, -71.268176, -29.684003\]_0_0"
    "roi_\[-68.604592, -22.090307, -68.892984, -21.858526\]_0_1"
    "roi_\[-70.747699, -28.34984, -70.865802, -28.237382\]_0_0"
)

echo copying patches to trainset
rsync -r $path/rois/patches/ $path/patches_img_trainset/

echo copying masks to trainset
rsync -r $path/rois/masks/patches/ $path/patches_mask_trainset/

echo moving patches to testset
# move files containing the specified lines to patches img test folder
for line in "${lines[@]}"; do
  find $path/patches_img_trainset -name "*$line*" -exec mv {} $path/patches_img_testset/ \;
done

echo train-patches:
ls -l $path/patches_img_trainset | wc -l

echo moving masks to testset
# copy files containing the specified lines to patches mask test folder
for line in "${lines[@]}"; do
  find $path/patches_mask_trainset -name "*$line*" -exec mv {} $path/patches_mask_testset/ \;
done

echo test-patches:
ls -l $path/patches_img_testset | wc -l

echo "images and masks are moved to test set"
