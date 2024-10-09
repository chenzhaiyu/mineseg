# Mining area segmentation

This code implements semantic segmentation of mining areas from satellite images.

## Python Dependencies
* torch
* segmentation-models-pytorch
* torchmetrics
* opencv-python
* numpy
* matplotlib
* hydra-core
* omegaconf
* tqdm

## python Dependencies to (re-)download of data set S2 images
* rasterio
* gdal
* geopandas
* gsutil (+ google cloud account)

## Packages
* gdal-bin


Install all requirements:
```
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia
pip install -r requirements.txt
apt-get update && apt-get install libgl1
```


## Folder Structure
	.
	├── annotations
	│   ├── annotation_doc.pdf                           # documentation of annotation classes and naming conventions
	│   ├── ASM_Ghana.geojson                            # Artisanal Mining Site Annotations
	│   ├── chile_all_sites_from_maus_et_al.geojson      # All Chilean Mining Sites according to Maus et al
	│   ├── LSM_Chile_sectors.geojson                    # Large Scale Mining Site Annotations
	│   ├── metadata.csv                                 # Large Scale Mining Site Metadata
	│   ├── metadata-sources.txt                         # Large Scale Mining Site Metadata Sources
	│   ├── metadata.xlsx                                # Large Scale Mining Site Metadata
	│   ├── show-LSM.qgz                                 # QGIS Project file (only visualization)
	│   ├── test_sites.geojson                           # Large Scale Mining Sites that are used for the Test Set
	│   └── train_sites.geojson                          # Large Scale Mining Sites that are used for the Training Set
	├── checkpoints                                      # Training Checkpoints
	├── conf                                             # hydra configuration
	│   ├── config.yaml                                  # hydra configuration file (learn-rate, batch-size, paths, epochs, etc.)
	│   └── hydra
	│       └── job_logging
	│           └── custom.yaml
	├── create_footprints.sh                             # creates a geojson with the footprints of all geotiffs in the given folder
	├── dataset_aug.py                                   # alternative data loader including some baseline augmentation
	├── dataset.py                                       # default data loader
	├── dl_chile_WCS.py                                  # download Sentinel Imagery of training, test, and CHILE set via WCS
	├── dockerfile                                       # dockerfile for creation of running environment
	├── merge_patches.sh                                 # merging of (predicted mask) patches into large tiles and a virtual raster tile
	├── outputs                                          # outpuf folder of prediction masks and ground truth comparison plot
	│   └── unet_merged                                  # classifier subfolder
	│       ├── _Chile_0_179_combined_mask.tif           # mask files
	│       ├── Chile_0_179_combined_mask.tif
	│       ├── ...
	│       ├── _Chile_9_9_combined_mask.tif
	│       └── Chile_9_9_combined_mask.tif
	├── output.vrt                                       # Virtual Raster Tile output of merge_patches.sh
	├── predict.py                                       # running prediction of files in prediction path defined in hydra configuration file
	├── raster_footprint.dbf                                       
	├── raster_footprint.geojson                         # footprints of all chilean raster tiles
	├── README.md                                        # readme
	├── requirements.txt                                 # python requirements
	├── select_10000_random_patches.sh                   # random selection of patches for retrieving background samples
	├── siteID_distances.csv                             # min-Distance of each Site to the closest located site
	├── test.py                                          # running prediction and evaluation of test-set with best-performing model
	├── tools.py                                         # helper functions
	├── train.py                                         # run training       
	└── utils.py                                         # helper functions



## Data download and preparation
The data set contains the extents of the mining sites as sentinel-2 images and their corresponding mask files. However, if you desire to reproduce the download process or to add images of different dates, you could do it as follows. You will need an environment with gdal installed. We suggest using a conda environment and install gdal with:

```bash
conda install -c conda-forge gdal
```

### (re-)Download of data set S2 images

Run the following command

```bash
./download-train-bbox.sh
```

This will create the sub-folders ```granules```, ```roi_images```, and ```roi_masks```. In ```granules```, the images are downloaded in the ```.SAFE``` format. In ```roi_images```, the mine site ROI's are stored and in ```roi_masks``` the corresponding masks, based on the file ```LSM_sectors.geojson``` are stored.

The next step is the creation of the 256x256 pixel sized patches as ```*.png``` files for training and inference. To create the training patches, run:

```bash
./crop-to-tiles.sh ./roi_images ./roi_masks
```

This will create two new folders ```./roi_images_patches``` and ```./roi_masks_patches```.


### (re-)Download of Sentinel-2 images of whole Chile

The sentinel patches for the whole chile experiment are downloaded with the Copernicus/SentinelHub WMTS service. To use this service, a few preparations are necessary:

- create an account for [dataspace.copernicus.eu](dataspace.copernicus.eu)
- add a ```configuration instance``` with a ```True color``` layer in the [Configuration Utility](https://shapps.dataspace.copernicus.eu/dashboard/#/configurations)
- set ```image quality``` to 100
- use your ```service endpoint ID``` and the ```secret ID``` in the ```./dl_chile_SHUB.py``` script

To run the download of all patches of whole chile, simply run:

```bash
./dl_chile_SHUB.py
```

This will create a sub folder ./chile_patches in which the patches of whole chile are being downloaded. It will take a while and download around 300.000 ```.png``` files with a sum of around 8.5Gb of space.

the final folder structure will look like this:

```
./
./...
./data
├── chile_files/
├── granules/
├── mask/
├── roi_images/
├── roi_images_patches/
├── roi_masks/
├── roi_masks_patches/
```


## Usage


**Configuration**

Configure paths, model architecture, training and test settings in `./conf/config.yaml`.
The following structure is expected under the `${data_root}` directory:
```
./data
├── patches_img_testset
├── patches_img_trainset
├── patches_mask_testset
└── patches_mask_trainset
```

**Training**

```bash
python train.py model=unet encoder="resnet50" gpu_ids="[0, 1]" run_suffix='_res50' wandb=True
```

Available models are `unet`, `unetplusplus`, `fpn`, `deeplabv3`, and `deeplabv3plus`. Check multiple options of [available encoders](https://smp.readthedocs.io/en/latest/encoders.html) as well. Checkpoints will be saved into `./checkpoints/${model}`.

**Evaluation**

```bash
python test.py model=unet gpu_ids="[0, 1]"
```

**Prediction**

```bash
python predict.py model=unet gpu_ids="[0]" num_examples=1000
```

Prediction results will be saved into `./outputs/${model}${run_suffix}`.

