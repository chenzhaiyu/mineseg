# Mining area segmentation

This code implements semantic segmentation of mining areas from satellite images.

## Dependencies

* pytorch
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

**Training**
```python
python train.py model=unet gpu_id=0
```

**Evaluation**
```python
python test.py
```

**Prediction**
```python
python predict.py
```
