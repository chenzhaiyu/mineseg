import glob
import pdb
from pystac_client import Client
import os
import tools
import argparse

#             west,       south,      east,      north
# chile    -76.154831, -56.269693, -65.827683, -17.186103

# "bbox": [-76.154831, -25.269693, -65.827683, -17.186103],  # north Chile      03.05.2022
# "bbox": [-75.000219, -38.937122, -67.763672, -24.44715],   # mid-Chile        14.12.2021
# "bbox": [-76.289063, -51.890054, -70.919534, -38.243365],  # mid-south Chile  21-02-2022
# "bbox": [-69.505005, -56.102683, -65.093994, -53.265213],  # south-east       06-08-2022
# "bbox": [-73.740234, -55.590763, -68.334961, -51.426614],  # south chile      05-11-2022

# S2 downloader
# search with AWS api
# download with Google cloud
# use cloud coverage and bbox and specify date or date range

if __name__ == "__main__":

    # Definition of input parameters
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cloud", type=int, required=False, help="Maximum cloud cover", default=100)
    parser.add_argument("-b", "--bbox", nargs=4, type=float, required=True,
        help="bbox <west> <south> <east> <north> (4 floats, e.g. -76.154831 -56.269693 -65.827683 -17.186103 ")
    parser.add_argument("-d", "--dates", nargs=2, type=str, required=True, help="<start> <end> date")
    parser.add_argument("-f", "--folder", type=str, required=False, help="Output folder", default="./dl")
    parser.add_argument("-e", "--cut_exact", type=bool, required=False, help="Output folder", default=False)

    # parse the data from
    args = parser.parse_args()

    # get the params straight
    max_cloud_cover = int(args.cloud)
    dates = args.dates
    # dates_string = dates[0] + "T00:00:00Z/" + dates[1] + "T23:59:59Z"
    out_folder = args.folder
    roi_bbox = args.bbox

    # create download folder if not exist
    os.makedirs(args.folder, exist_ok=True)

    # open AWS connection
    client = Client.open("https://earth-search.aws.element84.com/v1")

    # call search
    search_results = client.search(collections=["sentinel-2-l1c"],
                                   limit=100,
                                   bbox=roi_bbox,
                                   datetime=[dates[0] + "T00:00:00Z", dates[1] + "T23:59:59Z"]
                                   # , sortby="properties.eo:cloud_cover"
                                   )

    # print number of search results
    print(f"{search_results.matched()} granules found online fitting to the search results")

    # create the list of granules to download
    list_of_granules = []

    # Get the number of elements in the generator
    n = 0
    for idx_search, item in enumerate(search_results.items()):
        tools.progress_bar(idx_search, search_results.matched(), "Granule")
        print("")

        n += 1
        if n > search_results.matched():
            print("something wrong! This could happen when you do client.search() with sortby.")

        print(n, " / ", search_results.matched())

        # get grid code and satellite
        gc = item.properties["grid:code"][5:]
        sat = item.properties["platform"]

        # search for the granules with the least cloud cover
        if not tools.update_granule_list(granule_list=list_of_granules,
                                         target_granuleID=gc+sat,
                                         new_cloud_cover=item.properties["eo:cloud_cover"],
                                         new_foldername=os.path.join(out_folder, item.properties["s2:product_uri"] + ".zip")
                                         ):

            # S2 identifier for download
            prod_uri = item.properties["s2:product_uri"]

            # build the Google cloud url
            baseurl = ('gs://gcp-public-data-sentinel-2/tiles/' + gc[0:2] + '/' + gc[2] + '/' + gc[3:] + '/' + prod_uri)

            # create a new granule if it is not yet in the list_of_granules
            new_granule = {
                "granuleID": gc+sat,
                "least_cloud_cover": item.properties["eo:cloud_cover"],
                "baseurl": baseurl,
                "filename": prod_uri,
                "out_path": out_folder
            }
            list_of_granules.append(new_granule)

            # finally download the granule
            tools.dl_task(params=new_granule)

            # cut precise
            if args.cut_exact:

                # create the subfolder for roi images and its masks
                os.makedirs("./cut", exist_ok=True)
                os.makedirs("./mask", exist_ok=True)

                # set the bbox as string
                bbox_str = (
                        str(roi_bbox[0]) + " " +
                        str(roi_bbox[1]) + " " +
                        str(roi_bbox[2]) + " " +
                        str(roi_bbox[3]))

                # output path
                file_path = os.path.join(out_folder, prod_uri)

                # get all jp2 file paths
                jp2_files = glob.glob(os.path.join(file_path, "**", "*.jp2"), recursive=True)

                # for each file and RGB Band cut the region of interest
                for idx, jp2_file in enumerate(jp2_files):

                    # check if it is in the IMG_DATA folder and is either B02, B03 or B04 (BGR)
                    if "IMG_DATA" in jp2_file:
                        if "B02" in jp2_file or "B03" in jp2_file or "B04" in jp2_file:

                            # create roi image file
                            roi_file = tools.cut_region_of_interest(jp2_file, "cut", roi_bbox)

                            # create roi mask file
                            tools.create_binary_raster(input_geojson="./LSM_sectors.geojson",
                                                       output_raster="./mask/" + os.path.basename(roi_file),
                                                       jp2_file=roi_file)



    print("finished :)")
