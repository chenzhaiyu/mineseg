# SentinelHub configuration with your client ID and client secret
# config = SHConfig()
# config.sh_client_id = 'sh-88c69072-5120-4de8-bf84-d4326f36bfbc'
# config.sh_client_secret = 'NMxn75qH0zD80uteBet7zX0wzirn5FqR'

import math
import time
import requests
from PIL import Image
from io import BytesIO
import geopandas as gpd
from shapely.geometry import Polygon, box
from shapely.geometry.polygon import Polygon as ShapelyPolygon
import pdb


def deg_to_tile(lat, lon, zoom):
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    x_tile = int((lon + 180.0) / 360.0 * n)
    y_tile = int((1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return int(x_tile/2), int(y_tile/2)


def tile_to_deg(x_tile, y_tile, zoom):
    pdb.set_trace
    n = 2.0 ** zoom
    lon = x_tile*2 / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y_tile*2 / n)))
    lat = math.degrees(lat_rad)

    return lat, lon


def tile_to_polygon(x_tile, y_tile, zoom):
    min_lat, min_lon = tile_to_deg(x_tile, y_tile + 1, zoom)
    max_lat, max_lon = tile_to_deg(x_tile + 1, y_tile, zoom)
    return box(min_lon, min_lat, max_lon, max_lat)


# e.g. Chile
def get_polygon_of_country(CountryName):

    # load natural earth low res shapefile
    # download the file:
    # https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/110m/cultural/ne_110m_admin_0_countries.zip
    ne = gpd.read_file("ne_110m_admin_0_countries.zip")

    # get AOI geometry 
    country = CountryName
    geom = ne[ne.NAME == country].iloc[0].geometry
    
    return geom


def get_tiles_in_polygon(polygon, zoom):

    # get the bounding box coordinates in DD (decimal degree)
    min_lon, min_lat, max_lon, max_lat = polygon.bounds

    # get the tile coordinates of the polygon bounding box
    min_x, min_y = deg_to_tile(min_lat, min_lon, zoom)
    max_x, max_y = deg_to_tile(max_lat, max_lon, zoom)

    tiles = []
    # go through all tiles in the polygon bounding box and
    # check if a tile overlaps with the actual polygon
    for x in range(min_x, max_x + 1):
        for y in range(max_y, min_y + 1):

            # convert to polygon for intersection analysis
            tile_polygon = tile_to_polygon(x, y, zoom)

            # check for intersection of polygon and tile
            if polygon.intersects(tile_polygon):
                tiles.append((x, y))
                # print(tile_polygon.bounds, " in polygon")

    return tiles


country_name = "Chile"
countryPolygon = get_polygon_of_country(country_name)
zoomLevel = 14 # 10m/pixel
tiles = get_tiles_in_polygon(countryPolygon, zoomLevel)

param["maxcc"] = "15"
param["priority"] = "leastCC"
param["showLogo"] = "false"
param["transparent"] = "false"
param["layers"] = "1_TRUE_COLOR"
param["tilematrix"] = "14"
param["tilematrixset"] = "PopularWebMercator512"
param["format"] = "image/png"
param["time_start"] = "2021-01-01"
param["time_end"] = "2022-12-31"

pdb.set_trace()

for tile in tiles:

    url = (f"https://sh.dataspace.copernicus.eu/ogc/wmts/784ca3c2-8e61-4f9f-8c2e-9a33fb2fad58?SERVICE=WMTS&REQUEST="
           f"GetTile&"
           f"VERSION=1.0.0&"
           f"LAYER={param["layers"]}&"
           f"STYLE=&"
           f"priority={param["priority"]}&"
           f"maxcc={param["maxcc"]}&"
           f"FORMAT={param["format"]}&"
           f"TILEMATRIXSET={param["tilematrixset"]}&"
           f"TILEMATRIX={param["tilematrix"]}&"
           f"TILEROW={tile[1]}&"
           f"TILECOL={tile[0]}&"
           f"TIME={param["time_start"]}/{param["time_end"]}&"
           f"transparent={param["transparent"]}")

    time.sleep(1)
    print(url)

    response = requests.get(url)
    if response.status_code == 200:
        with Image.open(BytesIO(response.content)) as img:
            f_name = country_name + "_" + str(tile[0]) + "_" + str(tile[1])
            img.save(f_name + ".png", "png")
            print("saved ", f_name)
    else:
        print(f"Error fetching tile: HTTP {response.status_code} - {response.text}")
