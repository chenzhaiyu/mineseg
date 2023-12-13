# run this script inside the ... folder

mkdir -p patches_img_testset
mkdir -p patches_img_trainset
mkdir -p patches_mask_testset
mkdir -p patches_mask_trainset

# Define the lines to search for
lines=(
  "-69.496631_-22.928807_-69.153308_-22.678149"
  "-69.594134_-23.503055_-69.440326_-23.358149"
  "-69.964923_-22.687018_-69.791888_-22.424492"
  "-69.496631_-22.928807_-69.153308_-22.678149"
  "-69.964923_-22.687018_-69.791888_-22.424492"
  "-69.496631_-22.928807_-69.153308_-22.678149"
  "-69.964923_-22.687018_-69.791888_-22.424492"
  "-69.350289_-20.130951_-69.177941_-19.983245"
  "-69.350289_-20.130951_-69.177941_-19.983245"
  "-69.350289_-20.130951_-69.177941_-19.983245"
  "-68.88689_-23.510611_-68.742694_-23.34428"
  "-68.88689_-23.510611_-68.742694_-23.34428"
  "-68.837837_-22.385967_-68.822946_-22.373626"
  "-68.892984_-22.090307_-68.604592_-21.858526"
  "-68.896417_-21.076386_-68.520822_-20.866085"
  "-68.896417_-21.076386_-68.520822_-20.866085"
)

# Move files containing the specified lines to folder_B
for line in "${lines[@]}"; do
  grep -l "$line" * | xargs -I {} mv {} patches_img_testset/
done

# Move files containing the specified lines to folder_B
for line in "${lines[@]}"; do
  grep -l "$line" * | xargs -I {} mv {} patches_img_testset/
done


echo "images ans masks are moved to test set"