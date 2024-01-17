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

This will create a sub-folder ```granules``` in which the whole Sentinel-2 granules are being downloaded, the folder, ```roi_images``` and ```roi_masks```  in which the roi-extracts of the Sentinel-2 granules for training are being downloaded. The mask roi's will be created as well, based on the file ```LSM_sectors.geojson```.

The next step is the cutting into 256x256 pixel sized patches as ```*.png``` files for training and inference. To create the training patches, run:

```bash
./crop-to-tiles.sh ./roi_images ./roi_masks
```

This will create two new folders ```./roi_images_patches``` and ```./roi_masks_patches```.


### Sentinel-2 images of (almost) whole Chile

The sentinel patches for the whole chile experiment need to be downloaded manually. 
To run the download of all, in our experiments considered Chile Sentinel 2 images run:

```bash
./download-chile-cloud-free.sh
```

This will create a sub-folder ./chile_files in which the Sentinel-2 granules of Chile are being downloaded. The training roi that contains the mining sites will be downloaded with:



To create the chile patches, rune
```bash
./crop-to-tiles.sh ./chile_files ./chile_patches
```


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

