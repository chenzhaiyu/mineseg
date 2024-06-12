import colorsys
import geopandas as gpd
from rasterio.features import geometry_mask
import xml.etree.ElementTree as ET
import numpy as np
import rasterio
import os
import pdb
import subprocess
import imagecodecs
from pyproj import Proj, transform
import shapely.geometry
from PIL import Image
import os
from osgeo import gdal, osr, gdalconst
import requests
from pystac_client import Client
gdal.UseExceptions()
from PIL import Image
import os
import re
from collections import defaultdict





class CopernicusDL:

    def __init__(self, username: "", password: ""):
        self.username = username
        self.password = password
        self.access_token = self.get_access_token(username, password)
        self.catalog = []

    def get_access_token(self, username: str, password: str) -> str:
        data = {
            "client_id": "cdse-public",
            "username": username,
            "password": password,
            "grant_type": "password",
        }
        try:
            r = requests.post("https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
                              data=data,
                              )
            r.raise_for_status()
        except Exception as e:
            raise Exception(
                f"Access token creation failed. Reponse from the server was: {r.json()}"
            )
        return r.json()["access_token"]

    def open_catalog(self, url):
        self.catalog = Client.open(url)
        return self.catalog



def stack_images(directory):
    # Dictionary to hold images grouped by filename
    images_dict = defaultdict(list)

    # Regular expression to match the filename pattern and capture the row and column IDs
    pattern = re.compile(r'(.+)_(\d+)_(\d+)\.png')

    # Scan the directory for matching files and group them by filename
    for filename in os.listdir(directory):
        match = pattern.match(filename)
        if match:
            base_filename, row_id, col_id = match.groups()
            row_id, col_id = int(row_id), int(col_id)
            # Check if both row_id and col_id are even, then add to the list
            if row_id % 2 == 0 and col_id % 2 == 0:
                images_dict[base_filename].append((row_id, col_id, filename))

    # Process each group of images
    for base_filename, files in images_dict.items():
        # Sort files first by row_id then by col_id
        files.sort()
        # Separate the images by row for horizontal stacking and then stack vertically
        prev_row_id = -1
        vertical_stack = []
        for row_id, col_id, filename in files:
            with Image.open(os.path.join(directory, filename)) as img:
                if row_id != prev_row_id:
                    # New row, reset horizontal stack and update row_id
                    if prev_row_id >= 0:
                        # Stack the previous row images horizontally and add to vertical stack
                        vertical_stack.append(hstack)
                    hstack = img
                    prev_row_id = row_id
                else:
                    # Continue stacking horizontally in the same row
                    hstack = get_concat_h(hstack, img)

        # Add the last row's horizontal stack to vertical stack
        vertical_stack.append(hstack)
        
        # Stack vertically
        final_img = get_concat_v_multi(vertical_stack)
        
        # Save the final image
        final_img.save(f"{base_filename}.png")

def get_concat_h(im1, im2):
    """Concatenate two images horizontally"""
    dst = Image.new('RGB', (im1.width + im2.width, max(im1.height, im2.height)))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (im1.width, 0))
    return dst

def get_concat_v_multi(images):
    """Concatenate a list of images vertically"""
    width = max(img.width for img in images)
    height = sum(img.height for img in images)
    dst = Image.new('RGB', (width, height))
    y_offset = 0
    for img in images:
        dst.paste(img, (0, y_offset))
        y_offset += img.height
    return dst

# Specify the directory containing the images
# directory = 'path/to/your/images'
# stack_images(directory)





def process_image(img_path):
    dataset_orig = gdal.Open(img_path, gdal.GA_ReadOnly)

    # Get information about the dataset
    width = dataset_orig.RasterXSize
    height = dataset_orig.RasterYSize
    bands = dataset_orig.RasterCount
    band = dataset_orig.GetRasterBand(1)

    # create new file
    output_file = img_path[:-4] + "_deriv_vert.tif"
    driver = gdal.GetDriverByName("GTiff")
    output_dataset = driver.Create(output_file, width, height, bands, gdalconst.GDT_UInt16)

    # Set the georeferencing information
    output_dataset.SetGeoTransform(dataset_orig.GetGeoTransform())
    output_dataset.SetProjection(dataset_orig.GetProjection())

    # process the image
    # img_proc, fn_apx = horizontal_diff(dataset_orig, output_dataset)
    img_proc, fn_apx = vertical_diff(dataset_orig, output_dataset)

    # Close the output GeoTIFF file

    print("Processing and saving completed.")


def horizontal_diff(img_orig, output_dataset):
    for band_nr in range(img_orig.RasterCount):
        band = img_orig.GetRasterBand(band_nr + 1)
        band_new = output_dataset.GetRasterBand(band_nr + 1)
        data = band.ReadAsArray().astype(float)
        data_diff = np.abs(data[0:-1, :] - data[1:, :]).astype(int)
        data_diff = np.vstack((data_diff, np.expand_dims(data_diff[-1, :], 0)))
        band_new.WriteArray(data_diff)

    print("finished")
    return img_orig, "_diff"


def vertical_diff(img_orig, output_dataset):
    for band_nr in range(img_orig.RasterCount):
        band = img_orig.GetRasterBand(band_nr + 1)
        band_new = output_dataset.GetRasterBand(band_nr + 1)
        data = band.ReadAsArray().astype(float)
        data_diff = np.abs(data[:, 0:-1] - data[:, 1:]).astype(int)
        data_diff = np.hstack((data_diff, np.expand_dims(data_diff[:, -1], 1)))
        band_new.WriteArray(data_diff)

    print("finished")
    return img_orig, "_diff"


pass


def progress_bar(x, of_x, what=""):
    percentage = np.round(x / of_x * 100, 2)
    print(f"\r{what} -> Current Index: {x + 1}/{of_x} ({percentage}%)", end="")


def create_binary_raster(input_geojson, output_raster, jp2_file):
    # Read GeoJSON file
    gdf = gpd.read_file(input_geojson)

    # Read JP2 file to get dimensions
    with rasterio.open(jp2_file) as src:
        width = src.width
        height = src.height
        transform = src.transform
        jp2_file_bbox = src.bounds

    # Define the source and target coordinate reference systems
    src_crs = gdf.crs
    tgt_crs = src.crs

    # If the CRS of the GeoJSON is different from the JP2, perform a transformation
    if src_crs != tgt_crs:
        # Transform GDF geometry to the CRS of the JP2 file
        gdf = gdf.to_crs(tgt_crs)

    # Create a binary raster with the same dimensions
    raster_data = np.zeros((height, width), dtype=np.uint8)

    # Iterate through polygons and set pixels to 1 where they overlap
    for idx, geom in enumerate(gdf.geometry):
        progress_bar(idx, len(gdf.geometry), "Polygon")

        # create a polygon from bbox of image
        box_polygon = shapely.geometry.box(jp2_file_bbox[0], jp2_file_bbox[1], jp2_file_bbox[2], jp2_file_bbox[3])

        # check if bbox and geom overlap
        if shapely.geometry.Polygon.intersects(geom, box_polygon):

            # create the mask
            mask = geometry_mask([geom], transform=transform, invert=True, out_shape=(height, width))

            if mask.any():
                print("has overlap: ")
                print("    on: ", jp2_file)
                raster_data[mask] = 1
        else:
            print("POLYGON does NOT TOUCH:")
            pass

        if np.max(raster_data) == 2:
            pdb.set_trace()

    os.makedirs(os.path.dirname(output_raster), exist_ok=True)

    # Define creation options for lossless compression
    creation_options = {
        'QUALITY': '100',
        'REVERSIBLE': 'YES',
        'YCBCR420': 'NO'
    }

    # Create a new raster file
    with rasterio.open(
            output_raster,
            mode='w',
            driver='GTiff',
            height=height,
            width=width,
            count=1,
            dtype=np.uint8,
            crs=src.crs,
            transform=transform,
            **creation_options
    ) as dst:
        dst.write(raster_data, 1)


def adjust_coordinates(x, min_val, max_val):
    return max(min(x, max_val), min_val)


def transform_coordinates(src_srs, dst_srs, coordinates):
    # Create coordinate transformation
    transform = osr.CoordinateTransformation(src_srs, dst_srs)

    # Perform the transformation
    transformed_coords = transform.TransformPoints(coordinates)

    return transformed_coords


def cut_region_of_interest(input_file, output_path, bbox):
    # Open the input file
    dataset = gdal.Open(input_file)

    # Get the geotransform parameters
    geotransform = dataset.GetGeoTransform()

    # Extracting geospatial information
    origin_x = geotransform[0]
    origin_y = geotransform[3]
    pixel_width = geotransform[1]
    pixel_height = geotransform[5]
    width = dataset.RasterXSize
    height = dataset.RasterYSize

    # Calculate the extent
    xmin = origin_x
    ymin = origin_y + pixel_height * height
    xmax = origin_x + pixel_width * width
    ymax = origin_y

    # Get the input SRS
    input_srs = osr.SpatialReference()
    input_srs.ImportFromWkt(dataset.GetProjection())

    # Set the target SRS (WGS 84)
    target_srs = osr.SpatialReference()
    target_srs.ImportFromEPSG(4326)  # EPSG code for WGS 84

    # Transform bounding box coordinates to the input coordinate system
    bbox_tr = transform_coordinates(target_srs, input_srs, [(bbox[1], bbox[0]), (bbox[3], bbox[2])])

    print("")
    print("Coordinate extents of image")
    print(xmin, " ", ymin, " ", xmax, " ", ymax)
    print("")
    print("Coordinate extents of bbox")
    print(bbox_tr)
    print("")

    # Construct output file name
    orig_fname = os.path.basename(input_file)[:-4]
    output_file = os.path.join(output_path, orig_fname + f"{bbox[0]}_{bbox[1]}_{bbox[2]}_{bbox[3]}.jp2")

    if not os.path.isfile(output_file):
        # finally output the files with
        gdal.Warp(output_file, dataset, outputBounds=(bbox_tr[0][0], bbox_tr[0][1], bbox_tr[1][0], bbox_tr[1][1]),
                  srcSRS=input_srs, dstSRS=input_srs, format='JP2OpenJPEG')
    else:
        print("ROI Image exist already")

    return output_file


def process_image(file_path):
    try:
        # Open the image file
        img = Image.open(file_path)

        # Iterate through each band (R, G, B, etc.)
        for band in img.split():
            # Change pixels with value 0 to transparent
            band.putpalette([0, 0, 0] + [255, 255, 255] * 255)

        # Save the modified image
        img.save(file_path)
        print(f"Processed: {file_path}")

    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")


def process_folder(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(".jp2"):
                file_path = os.path.join(root, file)
                process_image(file_path)


# hdfs dfs to check if data is already available on calvalus
def run_cmd(args_list):
    print('Running system command: {0}'.format(' '.join(args_list)))
    proc = subprocess.Popen(args_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    s_output, s_err = proc.communicate()
    s_return = proc.returncode
    return s_return, s_output, s_err


def update_granule_list(granule_list, target_granuleID, new_cloud_cover, new_foldername):
    for granule in granule_list:
        if granule["granuleID"] == target_granuleID:
            # cloud_cover = check_cloud_mask(baseurl)  # contains the same as new_cloud_cover
            if granule["least_cloud_cover"] > new_cloud_cover and new_cloud_cover < 5:
                print("CLOUDCOVER OLD: ", granule["least_cloud_cover"], "   NEW:", new_cloud_cover)

                # if check_mask_cover(baseurl):
                print("before: ", granule["least_cloud_cover"])
                granule["least_cloud_cover"] = new_cloud_cover
                granule["foldername"] = new_foldername
                print("after: ", granule["least_cloud_cover"])
                # print("updated: ", granule, " new coverage: ", new_cloud_cover)
            else:
                print("no change")
            return True
    return False


def check_mask_cover(baseurl):
    try:
        mask_url = baseurl + "/" + "GRANULE" + "/**/" + "MSK_DETFOO_B01.jp2"
        subprocess.call(f"gsutil -m cp -r {mask_url} .", shell=True)

        mask_path = "./MSK_DETFOO_B01.jp2"
        img_array = np.array(imagecodecs.imread(mask_path))

        # Count the number of 0 pixels
        zero_pixel_count = np.count_nonzero(img_array == 0)
        print("##### ZERO-PIXEL: ", zero_pixel_count)
        os.remove(mask_path)
    except:
        print("ERROR")
        return False

    if zero_pixel_count == 0:
        return True
    else:
        print("FALSE")
        return False


def check_cloud_mask(baseurl):
    metadata_path = baseurl + "/" + "GRANULE" + "/**/" + "MTD_TL.xml"
    subprocess.call(f"gsutil -m cp -r {metadata_path} .", shell=True)

    # pdb.set_trace()
    tree = ET.parse("./MTD_TL.xml")
    root = tree.getroot()

    # Find the CLOUDY_PIXEL_PERCENTAGE element
    cloudy_pixel_percentage = root.find('.//CLOUDY_PIXEL_PERCENTAGE')

    print("##### Cloudyness: ", cloudy_pixel_percentage.text)

    # Get the value of CLOUDY_PIXEL_PERCENTAGE
    value = float(cloudy_pixel_percentage.text)

    return value


def dl_task_copernicus(params):
    headers = {"Authorization": f"Bearer {params['headers'].access_token}"}
    session = requests.Session()
    session.headers.update(headers)

    filename = params["filename"]
    out_path = params["out_path"]
    baseurl = params["baseurl"]

    if not os.path.isdir(os.path.join(out_path, filename)):
        print(filename + " does not exist.")
        subprocess.call(f"gsutil -m cp -r {baseurl} {out_path}", shell=True)
        # print("Compressing folder " + filename)
        # shutil.make_archive(os.path.join(outf, filename), 'zip', outf, filename)
        # shutil.rmtree(os.path.join(outf, filename))
    else:
        print(filename + " already exists.")


def dl_task_gcloud(params):
    filename = params["filename"]
    out_path = params["out_path"]
    baseurl = params["baseurl"]

    if not os.path.isdir(os.path.join(out_path, filename)):
        print(filename + " does not exist.")
        subprocess.call(f"gsutil -m cp -r {baseurl} {out_path}", shell=True)
        # print("Compressing folder " + filename)
        # shutil.make_archive(os.path.join(outf, filename), 'zip', outf, filename)
        # shutil.rmtree(os.path.join(outf, filename))
    else:
        print(filename + " already exists.")


def is_point_in_bbox(bbox_small, bbox_big):
    """
    Check if a point defined by latitude and longitude lies within a bounding box.

    Parameters:
    - lat: Latitude of the point
    - lon: Longitude of the point
    - bbox: Bounding box defined as (min_lat, min_lon, max_lat, max_lon)

    Returns:
    - True if the point is inside the bounding box, False otherwise
    """
    min_lon, min_lat, max_lon, max_lat = bbox_big

    lon = bbox_small[0] - (bbox_small[0] - bbox_small[2]) / 2
    lat = bbox_small[1] - (bbox_small[1] - bbox_small[3]) / 2

    if min_lon < lon < max_lon and min_lat < lat < max_lat:
        return True
    else:
        return False


def download_via_stac(start_url):
    import requests

    url = f"https://zipper.dataspace.copernicus.eu/odata/v1/Products(a5ab498a-7b2f-4043-ae2a-f95f457e7b3b)/$value"

    headers = {"Authorization": f"Bearer {access_token}"}

    session = requests.Session()
    session.headers.update(headers)
    response = session.get(url, headers=headers, stream=True)

    with open("product.zip", "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file.write(chunk)

    pass
