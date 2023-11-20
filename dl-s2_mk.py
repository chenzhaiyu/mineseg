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
import time
import gzip
import pdb
import tools


def main():
    path_to_csv = './dl/index.csv.gz'

    url = 'https://storage.googleapis.com/gcp-public-data-sentinel-2/index.csv.gz'
    if os.path.exists(path_to_csv):
        print("Index file exists!")
    else:
        subprocess.call(["wget", "-P", "dl/", url])

    now = time.time()

    if os.stat(path_to_csv).st_mtime < now - 14 * 86400:
        print("Index file is older than 14 days, updating it.")
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

        list_of_granules = []
        line = 0
        for row in reader:
            # print(row)
            line += 1
            if line % 10000 == 0:
                print("Line: ", line)

            # Lon_min, Lat_min, Lon_max, Lat_max
            bbox = [float(row[11]), float(row[10]), float(row[12]), float(row[9])]

            # check if the point is in the defined bounding box
            if tools.is_point_in_bbox(bbox, roi_bbox):

                granule = row[3]
                date = row[4][0:4]
                cloud_cover = int(float(row[6]))
                baseurl = row[13]
                filename = baseurl.rsplit('/', 1)[-1]

                # if cloud cover is below or equal threshold
                for year in list(years):
                    if year == date:
                        print("Line: ", line)
                        if not tools.update_granule_list(list_of_granules, granule, cloud_cover, out_folder, baseurl):

                            list_of_granules.append({
                                "granuleID": granule,
                                "least_cloud_cover": cloud_cover,
                                "baseurl": baseurl,
                                "filename": filename,
                                "out_path": out_folder
                            })
                            print("created granule entry")
                            # pdb.set_trace()

    # start downloading
    for granule_dict in list_of_granules:
        tools.dl_task(params=granule_dict)


if __name__ == "__main__":
    main()
