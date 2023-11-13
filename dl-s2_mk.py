#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Sentinel2Downloader.py
# Author            : Yuanyuan Wang <y.wang@tum.de>
# Edited            : Matthias Kahl <matthias.kahl@tum.de> + chatgpt :)
# Date              : 12.04.2019 13:49:16
# Last Modified Date: 12.04.2019 13:49:16
# Last Modified By  : Yuanyuan Wang <y.wang@tum.de>


import argparse
import csv
import os
import subprocess
import shutil
import time
import itertools
import gzip
import pandas
import pdb


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

    lon = bbox_small[0] # - (bbox_small[0] - bbox_small[2]) / 2
    lat = bbox_small[1] # - (bbox_small[1] - bbox_small[3]) / 2

    if min_lon < lon < max_lon and min_lat < lat < max_lat:
        return True
    else:
        return False


# hdfs dfs to check if data is already available on calvalus
def run_cmd(args_list):
    print('Running system command: {0}'.format(' '.join(args_list)))
    proc = subprocess.Popen(args_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    s_output, s_err = proc.communicate()
    s_return = proc.returncode
    return s_return, s_output, s_err


path_to_csv = './dl/index.csv.gz'

url = 'https://storage.googleapis.com/gcp-public-data-sentinel-2/index.csv.gz'
if os.path.exists(path_to_csv):
    print("Index file exists!")
else:
    subprocess.call(["wget", "-P", "dl/", url])

now = time.time()

if os.stat(path_to_csv).st_mtime < now - 7 * 86400:
    print("Index file is older than 7 days, updating it.")
    os.remove(path_to_csv)
    subprocess.call(["wget", "-P", "dl/", url])
else:
    print("Index file is up-to-date.")

# Definition of input parameters
parser = argparse.ArgumentParser()
parser.add_argument("-c", "--cloud", type=int, required=True, help="Maximum cloud cover")
# parser.add_argument("-g", "--granule", type=str, required=False, help="Granule ID to download (5 characters, e.g. 31UFS,31UFT - multiple granules supported)")
parser.add_argument("-b", "--bbox",  nargs=4, type=float, required=True, help="bbox lat lon (4 floats, e.g. 31.6355 30.6432 -9.6665 -8.8971")
parser.add_argument("-y", "--year", type=str, required=True, help="Years to download (multiple years supported)")
parser.add_argument("-d", "--dir", type=str, required=True, help="Output directory.")
args = parser.parse_args()

th = args.cloud
yr = args.year
outf = args.dir
yr = yr.split(",")
bb = args.bbox
print(yr)


#  minlat maxlat minlon maxlon
# -17.296715 -28.81443843 -71.535610 -66.97079090 !!!

with gzip.open(path_to_csv, 'rt') as f:  # 'rt' for reading as text
    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        # Lon_min, Lat_min, Lon_max, Lat_max
        bbox = [float(row[11]), float(row[10]), float(row[12]), float(row[9])]
        # print(bbox, row[3])
        # print(" ", bb)
        if is_point_in_bbox(bbox, bb):
            granule = row[3]
            date = row[4]
            date = date[0:4]
            quality = row[7]  # geometric_quality_flag
            cloud = row[6]
            cl = int(float(cloud))
            baseurl = row[13]
            filename = baseurl.rsplit('/', 1)[-1]

            if cl <= th:
                for a in list(yr):
                    if a == date:
                        hdfs_file_path = os.path.join(outf, filename + ".zip")
                        hdfs_dir_path = os.path.join(outf, filename)

                        if not os.path.isfile(hdfs_file_path) or os.path.isdir(hdfs_dir_path):
                            print(filename + " does not exist.")
                            subprocess.call(f"gsutil -m cp -r {baseurl} {outf}", shell=True)

                            print("Compressing folder " + filename)
                            shutil.make_archive(os.path.join(outf, filename), 'zip', outf, filename)
                            shutil.rmtree(os.path.join(outf, filename))
                        else:
                            print(filename + " already exists.")
