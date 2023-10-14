"""
Prediction (visualization) for multi-class mining site segmentation.
"""

import os

import hydra
from omegaconf import DictConfig
from tqdm import tqdm
import numpy as np
import torch
import cv2
from torch.nn import DataParallel
from torchmetrics import Accuracy
import segmentation_models_pytorch as smp

from utils import prepare_plot, set_seed, init_device

@hydra.main(config_path='./conf', config_name='config', version_base='1.2')
def predict(cfg: DictConfig):
    """
    Prediction with one single input.
    """
    # initialize device
    device = init_device(cfg.use_cuda, cfg.gpu_ids)

    # fix randomness
    set_seed(cfg.seed)

    # define model
    # Unet, UnetPlusPlus, FPN, DeepLabV3, DeepLabV3Plus
    if cfg.model == 'unet':
        _model = smp.Unet
    elif cfg.model == 'unetplusplus':
        _model = smp.UnetPlusPlus
    elif cfg.model == 'fpn':
        _model = smp.FPN
    elif cfg.model == 'deeplabv3':
        _model = smp.DeepLabV3
    elif cfg.model == 'deeplabv3plus':
        _model = smp.DeepLabV3Plus
    else:
        raise ValueError('unexpected model architecture')    
    model = _model(
        encoder_name=cfg.encoder,             # choose encoder, e.g. mobilenet_v2 or efficientnet-b7
        encoder_weights=cfg.encoder_weights,  # use `imagenet` pre-trained weights for encoder initialization
        in_channels=cfg.in_channel,           # model input channels (1 for gray-scale images, 3 for RGB, etc.)
        classes=len(cfg.classes),             # model output channels (number of classes in your dataset)
        activation=cfg.activation,            # activation function after the final convolution layer
    )
    # port model to GPUs
    model = DataParallel(model, device_ids=cfg.gpu_ids)
    model.to(device)

    # load example image paths
    filenames = os.listdir(cfg.test_image_dir)[:cfg.num_examples]

    # load checkpoint
    state = torch.load(cfg.checkpoint_path)
    model.load_state_dict(state['state_dict'])

    # start evaluation
    print('start prediction...')

    # define metrics
    accuracy = Accuracy(task="multiclass", num_classes=len(cfg.classes)).to(device)

    # iterate over the randomly selected test image paths
    model.eval()
    for filename in tqdm(filenames):
        # load image
        image_path = os.path.join(cfg.test_image_dir, filename)
        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = image.astype("float32")

        # resize the image and make a copy of it for visualization
        orig = image.copy().astype(np.uint8)

        # find the filename and generate the path to ground truth mask
        groundTruthPath = os.path.join(cfg.test_mask_dir, filename)

        # load the ground-truth segmentation mask in grayscale mode and resize it
        gtMask = cv2.imread(groundTruthPath, 0)

        # make the channel axis to be the leading one, add a batch
        # dimension, create a PyTorch tensor, and flash it to the current device
        image = np.transpose(image, (2, 0, 1))
        image = np.expand_dims(image, 0)
        image = torch.from_numpy(image).to(device)

        # make the prediction and convert the result to a NumPy array
        with torch.no_grad():
            predMask = model(image).squeeze()
            predMask = torch.argmax(predMask, dim=0)
            predMask = predMask.cpu().numpy()

        # convert prediction to integers
        predMask = predMask.astype(np.uint8)

        # prepare a plot for visualization
        if not os.path.exists(f'{cfg.result_dir}'):
            os.makedirs(f'{cfg.result_dir}')
        prepare_plot(os.path.join(cfg.result_dir, filename), orig, gtMask, predMask)


if __name__ == '__main__':
    predict()
