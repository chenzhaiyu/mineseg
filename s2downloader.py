from pystac_client import Client
import os
import tools
import argparse

#             west,       south,      east,      north
# chile    -76.154831, -56.269693, -65.827683, -17.186103

# "bbox": [-76.154831, -56.269693, -65.827683, -17.186103],  # north Chile      03.05.2022
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

    # parse the data from
    args = parser.parse_args()

    # get the params straight
    max_cloud_cover = int(args.cloud)
    dates = args.dates
    dates_string = dates[0] + "T00:00:00Z/" + dates[1] + "T23:59:59Z"
    out_folder = args.folder
    roi_bbox = args.bbox

    # create download folder if not exist
    os.makedirs(args.folder, exist_ok=True)

    # set the search parameter
    stac_search_params = {
        "collections": ["sentinel-2-l1c"],
        "datetime": dates_string,
        "sortby": "properties.eo:cloud_cover"
    }

    # open AWS connection
    client = Client.open("https://earth-search.aws.element84.com/v1")

    # call search
    search_results = client.search(**stac_search_params, limit=100)

    # print number of search results
    print(f"{search_results.matched()} items found")

    # create the list of granules to download
    list_of_granules = []
    for idx, item in enumerate(search_results.items()):

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
            print("created granule entry")

    print("finished :)")
