# this script downloads all sentinel 2 granules of almost whole Chile

$outfolder=chile_files
mkdir ./$outfolder

# north chile
python s2downloader.py --bbox -76.154831 -25.269693 -65.827683 -17.186103 --dates "2022-05-01" "2022-05-03" --folder "./$outfolder"

# mid chile
python s2downloader.py --bbox -75.000219 -38.937122 -67.763672 -24.447150 --dates "2021-04-10" "2021-04-13" --folder "./$outfolder"

# mid-south chile
python s2downloader.py --bbox -76.289063 -51.890054 -70.919534 -38.243365 --dates "2022-02-21" "2022-02-22" --folder "./$outfolder"
python s2downloader.py --bbox -76.289063 -51.890054 -70.919534 -38.243365 --dates "2022-01-20" "2022-01-20" --folder "./$outfolder"

# south chile
python s2downloader.py --bbox -69.505005 -56.102683 -65.093994 -53.265213 --dates "2021-02-10" "2021-02-10" --folder "./$outfolder"
python s2downloader.py --bbox -69.505005 -56.102683 -65.093994 -53.265213 --dates "2022-02-21" "2022-02-21" --folder "./$outfolder"
python s2downloader.py --bbox -69.505005 -56.102683 -65.093994 -53.265213 --dates "2022-08-06" "2022-08-06" --folder "./$outfolder"
