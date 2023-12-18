# this file downloads sentinel-2 granules of which our dataset has annotations for

outfolder=./granules
mkdir -p $outfolder

# north chile
python s2downloader.py --bbox -69.350289 -20.130951 -69.177941 -19.983245 --dates "2022-05-01" "2022-05-03" --folder "$outfolder" -e True
python s2downloader.py --bbox -68.896417 -21.076386 -68.520822 -20.866085 --dates "2022-05-01" "2022-05-03" --folder "$outfolder" -e True
python s2downloader.py --bbox -68.892984 -22.090307 -68.604592 -21.858526 --dates "2022-05-01" "2022-05-03" --folder "$outfolder" -e True
python s2downloader.py --bbox -68.837837 -22.385967 -68.822946 -22.373626 --dates "2022-05-01" "2022-05-03" --folder "$outfolder" -e True
python s2downloader.py --bbox -70.229968 -22.409258 -70.155810 -22.354655 --dates "2022-05-01" "2022-05-03" --folder "$outfolder" -e True
python s2downloader.py --bbox -69.964923 -22.687018 -69.791888 -22.424492 --dates "2022-05-01" "2022-05-03" --folder "$outfolder" -e True
python s2downloader.py --bbox -69.496631 -22.928807 -69.153308 -22.678149 --dates "2022-05-01" "2022-05-03" --folder "$outfolder" -e True
python s2downloader.py --bbox -70.286273 -22.801004 -70.133838 -22.626187 --dates "2022-05-01" "2022-05-03" --folder "$outfolder" -e True
python s2downloader.py --bbox -70.317859 -23.369495 -70.212115 -23.252204 --dates "2022-05-01" "2022-05-03" --folder "$outfolder" -e True
python s2downloader.py --bbox -70.129718 -23.477865 -69.988269 -23.370756 --dates "2022-05-01" "2022-05-03" --folder "$outfolder" -e True
python s2downloader.py --bbox -69.594134 -23.503055 -69.440326 -23.358149 --dates "2022-05-01" "2022-05-03" --folder "$outfolder" -e True
python s2downloader.py --bbox -68.886890 -23.510611 -68.742694 -23.344280 --dates "2022-05-01" "2022-05-03" --folder "$outfolder" -e True

# mid chile
python s2downloader.py --bbox -69.621600 -24.456657 -69.552936 -24.390386 --dates "2021-04-10" "2021-04-13" --folder "$outfolder" -e True
python s2downloader.py --bbox -70.435962 -25.026637 -70.354938 -24.919576 --dates "2021-04-10" "2021-04-13" --folder "$outfolder" -e True
python s2downloader.py --bbox -69.599628 -25.143551 -69.471912 -25.051522 --dates "2021-04-10" "2021-04-13" --folder "$outfolder" -e True
python s2downloader.py --bbox -70.611743 -25.688075 -70.565051 -25.641038 --dates "2021-04-10" "2021-04-13" --folder "$outfolder" -e True
python s2downloader.py --bbox -69.978656 -25.889626 -69.802875 -25.741278 --dates "2021-04-10" "2021-04-13" --folder "$outfolder" -e True
python s2downloader.py --bbox -69.682025 -26.318782 -69.507617 -26.186997 --dates "2021-04-10" "2021-04-13" --folder "$outfolder" -e True
python s2downloader.py --bbox -70.390643 -26.626106 -70.254687 -26.470088 --dates "2021-04-10" "2021-04-13" --folder "$outfolder" -e True
python s2downloader.py --bbox -69.462298 -26.535224 -69.355182 -26.457794 --dates "2021-04-10" "2021-04-13" --folder "$outfolder" -e True
python s2downloader.py --bbox -69.307117 -26.866472 -69.200000 -26.729182 --dates "2021-04-10" "2021-04-13" --folder "$outfolder" -e True
python s2downloader.py --bbox -70.418109 -27.202861 -70.291766 -27.048859 --dates "2021-04-10" "2021-04-13" --folder "$outfolder" -e True
python s2downloader.py --bbox -70.361804 -27.599106 -70.187396 -27.395674 --dates "2021-04-10" "2021-04-13" --folder "$outfolder" -e True
python s2downloader.py --bbox -69.344195 -27.588152 -69.232959 -27.511445 --dates "2021-04-10" "2021-04-13" --folder "$outfolder" -e True
python s2downloader.py --bbox -69.679278 -28.227702 -69.496631 -28.095734 --dates "2021-04-10" "2021-04-13" --folder "$outfolder" -e True
python s2downloader.py --bbox -70.865802 -28.349840 -70.747699 -28.237382 --dates "2021-04-10" "2021-04-13" --folder "$outfolder" -e True
python s2downloader.py --bbox -70.843829 -28.651555 -70.780658 -28.604544 --dates "2021-04-10" "2021-04-13" --folder "$outfolder" -e True
python s2downloader.py --bbox -71.022357 -28.844199 -70.953693 -28.752737 --dates "2021-04-10" "2021-04-13" --folder "$outfolder" -e True
python s2downloader.py --bbox -71.268176 -29.766291 -71.200885 -29.684003 --dates "2021-04-10" "2021-04-13" --folder "$outfolder" -e True
python s2downloader.py --bbox -70.039081 -29.837791 -69.926471 -29.697126 --dates "2021-04-10" "2021-04-13" --folder "$outfolder" -e True
python s2downloader.py --bbox -71.376666 -30.034153 -71.347827 -30.004426 --dates "2021-04-10" "2021-04-13" --folder "$outfolder" -e True
python s2downloader.py --bbox -71.155566 -30.309592 -71.042956 -30.167220 --dates "2021-04-10" "2021-04-13" --folder "$outfolder" -e True
python s2downloader.py --bbox -71.254443 -30.879368 -71.203631 -30.835749 --dates "2021-04-10" "2021-04-13" --folder "$outfolder" -e True
python s2downloader.py --bbox -71.038837 -31.754568 -70.898761 -31.649413 --dates "2021-04-10" "2021-04-13" --folder "$outfolder" -e True
python s2downloader.py --bbox -70.540332 -31.776752 -70.453815 -31.665778 --dates "2021-04-10" "2021-04-13" --folder "$outfolder" -e True
python s2downloader.py --bbox -71.194018 -32.694410 -71.077289 -32.606533 --dates "2021-04-10" "2021-04-13" --folder "$outfolder" -e True
python s2downloader.py --bbox -70.908374 -32.601905 -70.838336 -32.553302 --dates "2021-04-10" "2021-04-13" --folder "$outfolder" -e True
python s2downloader.py --bbox -70.394763 -33.248571 -70.194263 -33.053111 --dates "2021-04-10" "2021-04-13" --folder "$outfolder" -e True
python s2downloader.py --bbox -71.070422 -34.070413 -71.007251 -34.014654 --dates "2021-04-10" "2021-04-13" --folder "$outfolder" -e True
python s2downloader.py --bbox -70.536212 -34.122725 -70.319232 -34.052210 --dates "2021-04-10" "2021-04-13" --folder "$outfolder" -e True
python s2downloader.py --bbox -70.733966 -34.322576 -70.630969 -34.221574 --dates "2021-04-10" "2021-04-13" --folder "$outfolder" -e True

# mid south chile
python s2downloader.py --bbox -72.011127 -45.079926 -71.883411 -44.981902 --dates "2022-02-21" "2022-02-22" --folder "$outfolder" -e True
python s2downloader.py --bbox -72.045459 -46.587753 -71.949329 -46.500855 --dates "2022-02-21" "2022-02-22" --folder "$outfolder" -e True

# south chile
python s2downloader.py --bbox -71.225604 -53.038410 -71.022357 -52.926792 --dates "2021-02-10" "2021-02-10" --folder "$outfolder" -e True
python s2downloader.py --bbox -71.756381 -52.900706 -71.593646 -52.809075 --dates "2021-02-10" "2021-02-10" --folder "$outfolder" -e True
