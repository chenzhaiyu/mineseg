import xml.etree.ElementTree as ET
import numpy as np
import os
import pdb
import subprocess
import imagecodecs
from PIL import Image
import os


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



def dl_task(params):
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

