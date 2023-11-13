#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Sentinel2Downloader.py
# Author            : Yuanyuan Wang <y.wang@tum.de>
# Edited            : Matthias Kahl <matthias.kahl@tum.de> + chatgpt :)
# Date              : 12.04.2019 13:49:16
# Last Modified Date: 12.04.2019 13:49:16
# Last Modified By  : Yuanyuan Wang <y.wang@tum.de>


import argparse
import asyncio
import csv
import os
import subprocess
import shutil
import time
import itertools
import gzip
import pandas
import pdb
import multiprocessing
import concurrent.futures


def dl_task(params):
    # print("########  WORKER: ", concurrent.futures.thread_name())
    filename = params["filename"]
    hdfs_file_path = params["hdfs_file_path"]
    hdfs_dir_path = params["hdfs_dir_path"]
    baseurl = params["baseurl"]
    outf = params["outf"]

    if not os.path.isfile(hdfs_file_path) or os.path.isdir(hdfs_dir_path):
        print(filename + " does not exist.")
        subprocess.call(f"gsutil -m cp -r {baseurl} {outf}", shell=True)
        # subprocess.Popen(f"gsutil -m cp -r {baseurl} {outf}", shell=True)
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


# hdfs dfs to check if data is already available on calvalus
def run_cmd(args_list):
    print('Running system command: {0}'.format(' '.join(args_list)))
    proc = subprocess.Popen(args_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    s_output, s_err = proc.communicate()
    s_return = proc.returncode
    return s_return, s_output, s_err


#  minlat maxlat minlon maxlon
# -17.296715 -28.81443843 -71.535610 -66.97079090 !!!


def main():
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
    parser.add_argument("-b", "--bbox", nargs=4, type=float, required=True,
                        help="bbox lat lon (4 floats, e.g. 31.6355 30.6432 -9.6665 -8.8971")
    parser.add_argument("-y", "--year", type=str, required=True, help="Years to download (multiple years supported)")
    parser.add_argument("-d", "--dir", type=str, required=True, help="Output directory.")
    args = parser.parse_args()

    max_cloud_cover = args.cloud
    years = args.year.split(",")
    out_folder = args.dir
    roi_bbox = args.bbox

    # download 8 images
    # go through the csv file
    with gzip.open(path_to_csv, 'rt') as f:  # 'rt' for reading as text
        reader = csv.reader(f)
        header = next(reader)

        for row in reader:
            # Lon_min, Lat_min, Lon_max, Lat_max
            bbox = [float(row[11]), float(row[10]), float(row[12]), float(row[9])]

            # check if the point is in the defined bounding box
            if is_point_in_bbox(bbox, roi_bbox):
                granule = row[3]
                date = row[4][0:4]
                quality = row[7]  # geometric_quality_flag
                cloud_cover = int(float(row[6]))
                baseurl = row[13]
                filename = baseurl.rsplit('/', 1)[-1]

                # if cloud cover is below or equal threshold
                if cloud_cover <= max_cloud_cover:
                    for year in list(years):
                        if year == date:
                            hdfs_file_path = os.path.join(out_folder, filename + ".zip")
                            hdfs_dir_path = os.path.join(out_folder, filename)

                            dl_params = {'hdfs_file_path': hdfs_file_path,
                                         'hdfs_dir_path': hdfs_dir_path,
                                         'filename': filename,
                                         'baseurl': baseurl,
                                         'outf': out_folder}

                            dl_task(params=dl_params)


if __name__ == "__main__":
    main()
