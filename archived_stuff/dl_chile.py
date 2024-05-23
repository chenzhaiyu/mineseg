#NOTE:
# THIS DOWNLOADS ONLY ALREADY CLASSIED MAPS

# use requests library to download them
import requests
from tqdm.auto import tqdm  # provides a progressbar
from pathlib import Path
import geopandas as gpd
import subprocess

s3_url_prefix = "https://esa-worldcover.s3.eu-central-1.amazonaws.com"

# load natural earth low res shapefile
# download the file:
# https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/110m/cultural/ne_110m_admin_0_countries.zip
ne = gpd.read_file("ne_110m_admin_0_countries.zip")

# get AOI geometry (Italy in this case)
country = 'Chile'
geom = ne[ne.NAME == country].iloc[0].geometry

# load worldcover grid
url = f'{s3_url_prefix}/esa_worldcover_grid.geojson'
grid = gpd.read_file(url)

# get grid tiles intersecting AOI
tiles = grid[grid.intersects(geom)]

year = 2021  # setting this to 2020 will download the v100 product instead

# select version tag, based on the year
version = {2020: 'v100',
           2021: 'v200'}[year]

output_folder = './chile_cloudfree/'  # use current directory or set a different one to store downloaded files
for tile in tqdm(tiles.ll_tile):
    url = f"{s3_url_prefix}/{version}/{year}/map/ESA_WorldCover_10m_{year}_{version}_{tile}_InputQuality.tif"

    r = requests.get(url, allow_redirects=True)
    # out_fn = Path(output_folder) / Path(url).name

    out_fn = output_folder + Path(url).name
    with open(out_fn, 'wb') as f:
        f.write(r.content)
