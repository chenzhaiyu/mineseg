# SentinelHub configuration with your client ID and client secret
# config = SHConfig()
# config.sh_client_id = 'sh-88c69072-5120-4de8-bf84-d4326f36bfbc'
# config.sh_client_secret = 'NMxn75qH0zD80uteBet7zX0wzirn5FqR'
import csv
import math
from osgeo import gdal
import os.path
import time
import geopandas as gpd
from shapely.geometry import Polygon, box
from urllib.request import urlretrieve
from geopy.distance import geodesic
from geopy.point import Point
from pyproj import Proj, Transformer
import simplekml
import urllib.request
import tools



class SentinelDownloader:
    def __init__(self, settings):

        # take all settings
        self.parameter = settings


        if "country" in self.parameter:

            # get country polygon
            print("Download country polygon")
            self.country_polygon = self.get_polygon_of_country(self.parameter["country"])

            # get get Download URLs
            print("get download Urls")
            self.urls = self.get_urls(self.country_polygon, self.parameter)

        elif "roi_bbox" in self.parameter:

            # get bbox polygon
            print("Download bbox polygon")
            self.bbox_polygon = box(self.parameter["roi_bbox"][0],
                                    self.parameter["roi_bbox"][1],
                                    self.parameter["roi_bbox"][2],
                                    self.parameter["roi_bbox"][3])

            self.urls = self.get_urls(self.bbox_polygon, parameter=self.parameter)


        else:
            print("Define a country or bbox")
            exit(1)



        pass


    def download_urls(self, path="out"):

        print("Downloading ", len(self.urls), " urls")

        # go through all urls
        for url in self.urls:

            if "country" in self.parameter:
                f_name, f_name_mask = self.download_url(url, self.parameter["country"], out_path=path)
            else:
                suff = self.parameter["roi_bbox"]
                f_name, f_name_mask = self.download_url(url, "roi_" + str(suff), out_path=path)

            dim_size, big_img_size = self.get_tile_sizes(self.parameter["desired_tile_size"],
                                                         self.parameter["max_request_size"])

            # split the image files into desired tiles
            print("    Split ", f_name)
            self.split_geotiff(f_name, "./out/patches", dim_size)

            # split the mask files into desired tiles
            print("    Split mask ", f_name_mask)
            self.split_geotiff(f_name_mask, "./out/masks/patches", dim_size)



    def create_rectangle_kml(self, nw, se, filename="rectangle.kml"):
        """
        Generates a KML file with a rectangle defined by the north-west and south-east corners.
        call: create_rectangle_kml((pos_west, pos_north), (pos_east, pos_south))
        Args:
        nw (tuple): North-west corner as (latitude, longitude).
        se (tuple): South-east corner as (latitude, longitude).
        filename (str): Name of the output KML file.

        The function calculates the north-east and south-west corners to complete the rectangle.
        """
        # Calculate the missing corners
        ne = (nw[0], se[1])  # North-east corner (same latitude as nw, longitude of se)
        sw = (se[0], nw[1])  # South-west corner (same longitude as nw, latitude of se)

        # Define the rectangle corners in order
        corners = [nw, ne, se, sw, nw]  # Added nw again to close the polygon

        kml = simplekml.Kml()
        # Create a polygon
        pol = kml.newpolygon(name="Rectangle")
        pol.linestyle.width = 2
        pol.polystyle.outline = 1
        pol.linestyle.color = "ff0000ff"
        pol.polystyle.color = '00000000'

        # Define the outer boundary of the polygon
        pol.outerboundaryis = corners

        # Save the KML to a file
        kml.save(filename)
        print(f"KML file '{filename}' has been created.")


    # must be square
    def get_tile_sizes(self, desired_tile_size=256, max_request_size=2500):
        if 32 <= desired_tile_size <= 1024:
            num_tiles = max_request_size // desired_tile_size
            return num_tiles, desired_tile_size * num_tiles
        else:
            return "Value must be between 32 and 1024"


    def deg_to_tile(self, lat, lon, zoom):
        lat_rad = math.radians(lat)
        n = 2.0 ** zoom
        x_tile = int((lon + 180.0) / 360.0 * n)
        y_tile = int((1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
        return int(x_tile/2), int(y_tile/2)


    def tile_to_deg(self, x_tile, y_tile, zoom):

        n = 2.0 ** zoom
        lon = x_tile*2 / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y_tile*2 / n)))
        lat = math.degrees(lat_rad)

        return lat, lon


    def tile_to_polygon(self, x_tile, y_tile, zoom):
        min_lat, min_lon = self.tile_to_deg(x_tile, y_tile + 1, zoom)
        max_lat, max_lon = self.tile_to_deg(x_tile + 1, y_tile, zoom)
        return box(min_lon, min_lat, max_lon, max_lat)


    # e.g. Chile
    def get_polygon_of_country(self, CountryName):

        # load natural earth low res shapefile
        # download the file
        url = ("https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip")
        urlretrieve(url, "ne_110m_admin_0_countries.zip")

        ne = gpd.read_file("ne_110m_admin_0_countries.zip")

        # get AOI geometry
        country = CountryName
        try:
            geom = ne[ne.NAME == country].iloc[0].geometry
        except:
            print("Country not found:")
            exit(-1)


        return geom


    def get_utm_zone(self, longitude):
        """
        Calculate UTM zone number from longitude.
        """
        return int((longitude + 180) / 6) + 1


    def convert_to_utm(self, lat, lon):
        """
        Convert latitude and longitude to UTM coordinates using the appropriate UTM zone.
        """
        zone = self.get_utm_zone(lon)
        # North vs South hemisphere
        hemisphere = 'north' if lat >= 0 else 'south'
        proj_utm = Proj(proj='utm', zone=zone, ellps='WGS84', datum='WGS84', south=hemisphere=='south')
        proj_latlon = Proj(proj='latlong', datum='WGS84')
        transformer = Transformer.from_proj(proj_latlon, proj_utm)
        return transformer.transform(lat, lon), zone


    # country bbox: (lon_min, lat_min, lon_max, lat_max)
    # country bbox: (west,    south,   east,    north)
    def get_urls(self, country_polygon, parameter):

        west, south, east, north = country_polygon.bounds

        tiles_per_dim, tile_collection_px_per_dim = self.get_tile_sizes(desired_tile_size=parameter["desired_tile_size"],
                                                                   max_request_size=parameter["max_request_size"])

        # get the bigbox distance in meters
        dist_in_meter = parameter["desired_tile_size"] * tiles_per_dim * parameter["gsd"]

        self.create_rectangle_kml((west, north), (east, south))

        pos_east = east
        pos_north = north
        pos_south = 0
        pos_west = 0
        bbox_list = []

        hpos, vpos = 0, 0
        url_dict = {}
        url_dict_list = []

        all_boxes_kml = simplekml.Kml()

        # from north to south
        while pos_north > south:

            # from east to west
            hpos = 0
            while pos_east > west:
                pos_south, pos_west = self.precise_new_location(pos_north, pos_east, dist_in_meter, dist_in_meter)

                # define bbox
                bbox = pos_west, pos_south, pos_east, pos_north

                print(vpos, " ", hpos)

                # check if bbox is in polygon
                if country_polygon.intersects(box(pos_west, pos_south, pos_east, pos_north)):

                    # create polygon for kml file
                    pol = all_boxes_kml.newpolygon(name=f"Polygon {vpos} {hpos}")
                    bbox_poly = box(pos_west, pos_south, pos_east, pos_north)
                    pol.outerboundaryis = list(bbox_poly.exterior.coords)
                    pol.linestyle.width = 1
                    pol.linestyle.color = "ff0000ff"
                    pol.polystyle.color = '00000000'

                    # generate url
                    url = ("https://sh.dataspace.copernicus.eu/ogc/wcs/"
                           f"{parameter['client_id']}?"
                           "SERVICE=WCS&"
                           "VERSION=1.0.0&"
                           "REQUEST=GetCoverage&"
                           "FORMAT=GeoTIFF&"
                           "COVERAGE=1_TRUE_COLOR&"
                           f"BBOX={bbox[0]},"
                           f"{bbox[1]},"
                           f"{bbox[2]},"
                           f"{bbox[3]}&"
                           f"MAXCC={parameter['maxcc']}&"
                           f"PRIORITY={parameter['priority']}&"
                           f"TIME={parameter['time_start']}/{parameter['time_end']}&"
                           "CRS=EPSG:4326&"
                           "RESPONSE_CRS=EPSG:3857&"
                           f"WIDTH={tile_collection_px_per_dim}&"
                           f"HEIGHT={tile_collection_px_per_dim}")

                    # fill the url list
                    url_dict = {"url": url, "hpos": hpos, "vpos": vpos}
                    url_dict_list.append(url_dict)

                # go dist_in_meter in west direction
                pos_east = pos_west
                hpos += 1

            # reset to the farthest east point
            pos_east = east

            # go dist_in_meter in south direction
            pos_north = pos_south
            vpos += 1

        # save the kml with the boxes
        all_boxes_kml.save("big_boxes.kml")

        return url_dict_list


    def get_tiles_in_polygon(self, polygon, zoom, tilematrixset):

        zoom = int(zoom)
        if "256" in tilematrixset:
            zoom += 1

        # get the bounding box coordinates in DD (decimal degree)
        min_lon, min_lat, max_lon, max_lat = polygon.bounds

        # get the tile coordinates of the polygon bounding box
        min_x, min_y = self.deg_to_tile(min_lat, min_lon, zoom)
        max_x, max_y = self.deg_to_tile(max_lat, max_lon, zoom)

        tiles = []
        # go through all tiles in the polygon bounding box and
        # check if a tile overlaps with the actual polygon
        for x in range(min_x, max_x + 1):
            for y in range(max_y, min_y + 1):

                # convert to polygon for intersection analysis
                tile_polygon = self.tile_to_polygon(x, y, zoom)

                # check for intersection of polygon and tile
                if polygon.intersects(tile_polygon):
                    tiles.append((x, y))
                    # print(tile_polygon.bounds, " in polygon")

        return tiles


    def download_url(self, url, file_name_suffix="img", out_path="./out/"):

        os.makedirs(out_path, exist_ok=True)
        os.makedirs(os.path.join(out_path, "masks"), exist_ok=True)

        # generate image file name and path
        f_name = file_name_suffix + "_" + str(url["hpos"]) + "_" + str(url["vpos"])
        f_path = os.path.join(out_path, f_name + ".tif")

        # check if file already exist
        if not os.path.exists(f_path):

            # request the url
            print(url)
            urllib.request.urlretrieve(url["url"], f_path)
            print("finished download of " + f_path)

            time.sleep(1)

        # generate mask file name and path
        f_path_msk = os.path.join(out_path, "masks", f_name + ".tif")

        # check if file already exist
        if self.parameter["labels"]:
            if not os.path.exists(f_path_msk):
                tools.create_binary_raster(self.parameter["labels"], f_path_msk, f_path)

        return f_path, f_path_msk


    def precise_new_location(self, lat, lon, dist_to_west, dist_to_south):

        # Start with the original point
        start_point = Point(lat, lon)

        # Calculate the new point after moving east
        # Bearing of 90 degrees (east), distance in kilometers (convert meters to km)
        west_point = geodesic(kilometers=dist_to_west / 1000).destination(start_point, bearing=270)

        # Now move south from the new eastern point
        # Bearing of 180 degrees (south), distance in kilometers
        final_point = geodesic(kilometers=dist_to_south / 1000).destination(west_point, bearing=180)

        return final_point.latitude, final_point.longitude


    def split_geotiff(self, input_file, output_folder, dim_size):

        # Open the input GeoTIFF
        ds = gdal.Open(input_file)
        width = ds.RasterXSize
        height = ds.RasterYSize
        bands = ds.RasterCount

        # Calculate the size of each tile
        tile_width = width // dim_size
        tile_height = height // dim_size

        # Create output folder if it doesn't exist
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Loop over the 3x3 grid and create each tile
        for i in range(dim_size):
            for j in range(dim_size):

                # Calculate the offsets (should be always 0)
                x_offset = j * tile_width
                y_offset = i * tile_height

                # Create the output file name
                old_name = os.path.splitext(os.path.basename(input_file))
                output_file = os.path.join(output_folder, old_name[0] + f'_{i}_{j}.tif')

                # Define the gdal translate command to extract the sub-region
                gdal.Translate(output_file, ds, srcWin=[x_offset, y_offset, tile_width, tile_height])

        # Close the dataset
    ds = None



if __name__ == "__main__":

    settings = {}
    # settings["client_id"] = "15705528-7c35-4373-b499-d1b6b86015a6"  # matthias.kahl@tum.de
    settings["labels"] = "./LSM_sectors.geojson"
    settings["client_id"] = "3c701f12-dc13-482a-b9eb-27d02019b503"  # matthias.kahl@tum.de
    settings["desired_tile_size"] = 256
    settings["max_request_size"] = 2500
    settings["gsd"] = 10
    settings["maxcc"] = "15"
    settings["priority"] = "leastCC"
    settings["showLogo"] = "false"
    settings["transparent"] = "false"
    settings["layers"] = "1_TRUE_COLOR"
    settings["format"] = "image/tiff"
    settings["time_start"] = "2021-01-01"
    settings["time_end"] = "2022-12-31"



    ### DOWNLOAD Mine Sites ROIs ###

    with open("mine_rois.csv", newline="") as csvfile:

        # csv reader
        reader = csv.reader(csvfile)

        # go through each line in csv
        for row in reader:

            # csv reader
            reader = csv.reader("mine_rois.csv")

            # read coordinates
            if row:
                coordinates = list(float(coord) for coord in row)

                # settings["roi_bbox"] = [west, south, east, north]
                settings["roi_bbox"] = coordinates

                # create an instance of the downloader
                myDownloader = SentinelDownloader(settings)

                # download all urls
                myDownloader.download_urls("rois")



    ### DOWNLOAD WHOLE CHILE ###

    # set parameter
    settings["country"] = "Chile"
    settings["roi_bbox"] = []

    # create an instance of the downloader
    myDownloader = SentinelDownloader(settings)

    # download all urls
    myDownloader.download_urls("CHILE")
    
    
