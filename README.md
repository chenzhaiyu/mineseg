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
python predict.py model=unet
```

Prediction results will be saved into `./outputs/${model}${run_suffix}`.

