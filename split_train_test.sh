# run this script inside the source code folder

root=data_s2

mkdir -p ./$root/patches_img_testset
mkdir -p ./$root/patches_img_trainset
mkdir -p ./$root/patches_mask_testset
mkdir -p ./$root/patches_mask_trainset

# Define the regions of interest that are defined as test set
lines=(
  "T19JCJ_20210411T144721_TCI-71.022357_-28.844199_-70.953693_-28.752737"
  "T19JCJ_20210413T143729_TCI-70.843829_-28.651555_-70.780658_-28.604544"
  "T19JCJ_20210413T143729_TCI-70.865802_-28.34984_-70.747699_-28.237382"
  "T19JCJ_20210413T143729_TCI-71.022357_-28.844199_-70.953693_-28.752737"
  "T19JDN_20210413T143729_TCI-69.599628_-25.143551_-69.471912_-25.051522"
  "T19JDN_20210413T143729_TCI-69.6216_-24.456657_-69.552936_-24.390386"
  "T19KCQ_20220501T144719_TCI-69.964923_-22.687018_-69.791888_-22.424492"
  "T19KDR_20220501T144719_TCI-69.496631_-22.928807_-69.153308_-22.678149"
  "T19KDR_20220501T144719_TCI-69.964923_-22.687018_-69.791888_-22.424492"
  "T19KDR_20220503T143731_TCI-69.496631_-22.928807_-69.153308_-22.678149"
  "T19KDR_20220503T143731_TCI-69.964923_-22.687018_-69.791888_-22.424492"
  "T19KDT_20220501T144719_TCI-69.350289_-20.130951_-69.177941_-19.983245"
  "T19KDT_20220503T143731_TCI-69.350289_-20.130951_-69.177941_-19.983245"
  "T19KDU_20220501T144719_TCI-69.350289_-20.130951_-69.177941_-19.983245"
  "T19KEP_20220503T143731_TCI-68.88689_-23.510611_-68.742694_-23.34428"
  "T19KEQ_20220503T143731_TCI-68.88689_-23.510611_-68.742694_-23.34428"
  "T19KER_20220503T143731_TCI-68.837837_-22.385967_-68.822946_-22.373626"
)

echo copying patches to trainset
cp ./$root/patches/* ./$root/patches_img_trainset/

echo copying masks to trainset
cp ./$root/masks/* ./$root/patches_mask_trainset/

echo moving patches to testset
# copy files containing the specified lines to patches img test folder
for line in "${lines[@]}"; do
  find ./$root/patches_img_trainset -name *$line* -exec mv {} ./$root/patches_img_testset/ \;
done

echo train-patches: 
ls -l ./$root/patches_img_trainset | wc -l

echo test-patches: 
ls -l ./$root/patches_img_testset | wc -l

echo moving masks to testset
# copy files containing the specified lines to patches mask test folder
for line in "${lines[@]}"; do
  find ./$root/patches_mask_trainset -name *$line* -exec mv {} ./$root/patches_mask_testset/ \;
done

echo "images and masks are moved to test set"




