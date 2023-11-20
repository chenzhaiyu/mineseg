from pystac_client import Client
import os
import tools


# whole chile -76.154831,-56.269693,-65.827683,-17.186103

# S2 downloader
# search with AWS api
# download with Google cloud
# use cloud coverage and bbox

if __name__ == "__main__":

    out_folder = "./dl"

    stac_search_params = {
        "collections": ["sentinel-2-l1c"],
        # "bbox": [-76.154831, -56.269693, -65.827683, -17.186103], # north chile
        # "bbox": [-75.000219, -38.937122, -67.763672, -24.44715],  # mid chile
        # "bbox": [-76.289063, -51.890054, -70.919534, -38.243365],  # mid-south chile
        # "bbox": [-69.505005, -56.102683 , -65.093994, -53.265213],  # south-east
        # "bbox": [-73.740234, -55.590763, -68.334961, -51.426614],  # south chile

        # "datetime": "2021-12-14T00:00:00Z/2021-12-14T23:59:59Z", # mid-chile
        "datetime": "2022-11-05T00:00:00Z/2022-11-05T23:59:59Z",  # mid-south-chile
        # , "sortby": "properties.eo:cloud_cover"
    }

    client = Client.open("https://earth-search.aws.element84.com/v1")
    search_results = client.search(**stac_search_params, limit=100)
    print(f"{search_results.matched()} items found")


    list_of_granules = []
    for idx, item in enumerate(search_results.items()):
        gc = item.properties["grid:code"][5:]
        sat = item.properties["platform"]
        if not tools.update_granule_list(granule_list=list_of_granules,
                                         target_granuleID=gc+sat,
                                         new_cloud_cover=item.properties["eo:cloud_cover"],
                                         new_foldername=os.path.join(out_folder, item.properties["s2:product_uri"] + ".zip")
                                         ):

            prod_uri = item.properties["s2:product_uri"]
            baseurl = ('gs://gcp-public-data-sentinel-2/tiles/' + gc[0:2] + '/' + gc[2] + '/' + gc[3:] + '/' + prod_uri)

            new_granule = {
                "granuleID": gc+sat,
                "least_cloud_cover": item.properties["eo:cloud_cover"],
                "baseurl": baseurl,
                "filename": prod_uri,
                "out_path": out_folder
            }

            list_of_granules.append(new_granule)
            tools.dl_task(params=new_granule)
            print("created granule entry")

    print("finished :)")
