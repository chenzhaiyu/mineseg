from datasets import Dataset, DatasetDict, Features, Image
from huggingface_hub import login
import glob, os

def make_items(root):
    imgs = sorted(glob.glob(os.path.join(root, "images", "*")))
    items = []
    for img in imgs:
        base = os.path.splitext(os.path.basename(img))[0]
        # assume same name in masks/
        mask = os.path.join(root, "masks", base + ".png")
        if os.path.exists(mask):
            items.append({"image": img, "mask": mask})
    return items

features = Features({"image": Image(), "mask": Image()})   # masks are label-indexed images

ds = DatasetDict({
    "train": Dataset.from_list(make_items("/home/matthias/Documents/MineSegDataSet/img_sector/multiclass_image_data/train")).cast(features),
    "validation": Dataset.from_list(make_items("/home/matthias/Documents/MineSegDataSet/img_sector/multiclass_image_data/validation")).cast(features),
    "test": Dataset.from_list(make_items("/home/matthias/Documents/MineSegDataSet/img_sector/multiclass_image_data/test")).cast(features),
})

login()  # or `hf auth login` in a terminal first
ds.push_to_hub("maduschek/LAMES")


