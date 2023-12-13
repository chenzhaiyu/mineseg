import requests
import pandas as pd
from shapely import geometry
import json
import os.path

import requests
from pystac_client import Client


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


if __name__ == "__main__":

    dl_path = "C:/DATA/GAZA/img_s1/"

    # open cop downloader
    cop_dl = CopernicusDL("maduschek@gmx.de", "?xn-Cen9VudY98!")

    # open catalog
    myCatalog = cop_dl.open_catalog("https://catalogue.dataspace.copernicus.eu/stac")

    bbox = [34.141933, 31.133144, 34.753735, 31.778842]
    poly = geometry.Polygon(((bbox[0], bbox[1]),
                            (bbox[0], bbox[3]),
                            (bbox[2], bbox[1]),
                            (bbox[2], bbox[3])))

    # filter
    json = requests.get(
        "https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter="
        "OData.CSC.Intersects(area=geography'SRID=4326;" + poly.wkt + "') and "
        "ContentDate/Start gt 2023-12-10T00:00:00.000Z and "
        "ContentDate/Start lt 2023-12-31T00:00:00.000Z and "
        "Collection/Name eq 'SENTINEL-1'").json()

    # create pandas data frame with search results
    df = pd.DataFrame.from_dict(json['value'])

    headers = {"Authorization": f"Bearer {cop_dl.access_token}"}
    session = requests.Session()
    session.headers.update(headers)

    # download each product
    for name, idx in zip(df['Name'].items(), df["Id"].items()):

        print("start downloading: ", name)
        url = f"https://zipper.dataspace.copernicus.eu/odata/v1/Products(" + idx[1] + ")/$value"

        if not os.path.isfile(os.path.join(dl_path, name[1] + ".zip")):

            # request for image
            response = session.get(url, headers=headers, stream=True)
            os.makedirs(dl_path, exist_ok=True)

            with open(os.path.join(dl_path, name[1] + ".zip"), "wb") as file:
                for idx, chunk in enumerate(response.iter_content(chunk_size=8192)):
                    if chunk:
                        file.write(chunk)

