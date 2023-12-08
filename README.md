# Mining area segmentation

This code implements semantic segmentation of mining areas from satellite images.

## Dependencies

* torch
* segmentation-models-pytorch
* torchmetrics
* opencv-python
* numpy
* matplotlib
* hydra-core
* omegaconf
* tqdm

Install all requirements:
```
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia
pip install -r requirements.txt
apt-get update && apt-get install libgl1
```

## Data download and preparation
The data set contains the extents of the mining sites as sentinel-2 images and their corresponding mask files. The sentinel patches for the whole chile experiment need to be downloaded manually. To run the download of all, in our experiments considered Chile Sentinel 2 images run:

```bash
./download-chile-cloud-free.sh
```

This will create a sub-folder ./chile in which the Sentinel-2 granules of chile are being downloaded. The training data with mining site content will be downloaded with:

```bash
./download-train-bbox.sh
```

This will create a sub-folder ./train in which the Sentinel-2 granules for training are being downloaded. The last step is the cutting into 256x256 pixel sized patches as *.png files for training and inference. To create the training patches, run:

```bash
./crop-to-tiles.sh ./train /train_patches
./crop-to-tiles.sh ./mask /masks_patches
# choose the folder in which ./train and ./mask lie
./crop-to-tiles.sh ./
```

To create the chile patches, r
```bash
./crop-to-tiles.sh ./dl /chile
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

