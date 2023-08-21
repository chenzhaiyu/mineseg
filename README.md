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

Install all requirements:
```
pip install -r requirements.txt
```

## Usage

**Configuration**

Configure paths, model architecture, training and test settings in `./conf/config.yaml`.

**Training**

```bash
python train.py model=unet gpu_id=0
```

The implemented models are `unet`, `unetplusplus`, `fpn`, `deeplabv3`, and `deeplabv3plus`. Checkpoints will be saved into `./checkpoints/${model}`.

**Evaluation**

```bash
python test.py model=unet
```

**Prediction**

```bash
python predict.py model=unet
```

Prediction results will be saved into `./outputs/${model}`.

