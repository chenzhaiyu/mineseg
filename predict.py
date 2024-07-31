"""
Prediction (visualization) for multi-class mining site segmentation.
"""

import os
import pdb
import hydra
from omegaconf import DictConfig
from tqdm import tqdm
import numpy as np
import torch
import cv2
from torch.nn import DataParallel
import segmentation_models_pytorch as smp
import rasterio
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

    # define model: Unet, UnetPlusPlus, FPN, DeepLabV3, DeepLabV3Plus
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
    filenames = os.listdir(cfg.pred_image_dir)[:cfg.num_examples]

    # load checkpoint
    state = torch.load(cfg.checkpoint_path)
    model.load_state_dict(state['state_dict'])

    # start evaluation
    print('start prediction...')

    # iterate over the randomly selected test image paths
    model.eval()
    for filename in tqdm(filenames):

        # load image
        image_path = os.path.join(cfg.pred_image_dir, filename)
        # image_cv2 = cv2.imread(image_path)
        # image_cv2 = cv2.cvtColor(image_cv2, cv2.COLOR_BGR2RGB)
        # image_cv2 = image_cv2.astype("float32")

        # read the geotiff meta data
        with rasterio.open(image_path) as geo_tiff:
            meta = geo_tiff.meta  # Keep the original metadata

            # for mask
            meta.update({
                'count': 1  # Number of bands; grayscale has only one band
                #'dtype': grayscale_data.dtype  # Ensure dtype matches the data type of grayscale_data
            })

            image = np.fliplr(np.rot90(geo_tiff.read().T[:, :, :-1], 3))
            image = image.astype("float32")

        # do padding
        height, width = image.shape[:2]
        desired_size = 256

        # Compute padding
        delta_width = desired_size - width
        delta_height = desired_size - height
        top, bottom = delta_height//2, delta_height-(delta_height//2)
        left, right = delta_width//2, delta_width-(delta_width//2)

        image = cv2.copyMakeBorder(image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[0,0,0])
        # mask = cv2.copyMakeBorder(mask, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[0,0,0])

        # resize the image and make a copy of it for visualization
        origin = image.copy().astype(np.uint8)

        # make the channel axis to be the leading one, add a batch
        # dimension, create a PyTorch tensor, and flash it to the current device
        image = np.transpose(image, (2, 0, 1))
        image = np.expand_dims(image, 0)
        image = torch.from_numpy(image).to(device)

        # make the prediction and convert the result to a NumPy array
        with torch.no_grad():
            pred_mask = model(image).squeeze()
            pred_mask = torch.argmax(pred_mask, dim=0)
            pred_mask = pred_mask.cpu().numpy()

        # convert prediction to integers
        pred_mask = pred_mask.astype(np.uint8)

        # in case we have no GT data
        if cfg.pred_mask_dir == '':

            # if mine site is found
            if pred_mask.max() > 0:

                # write the prediction mask as png image
                # cv2.imwrite(os.path.join(cfg.result_dir, "_" + filename[:-4] + "_mask.png"), pred_mask)

                # save the geotiff meta data to mask file
                with rasterio.open(os.path.join(cfg.result_dir, "_" + filename[:-4] + "_mask.tif"), "w", **meta) as dst:
                    dst.write(np.expand_dims(pred_mask, axis=0))

                # prepare plot for visual comparison
                prepare_plot(os.path.join(cfg.result_dir, "_" + filename[:-4] + ".png"), origin, None, pred_mask, cfg.classes)

            else:
                # write the prediction mask as png image
                # cv2.imwrite(os.path.join(cfg.result_dir, filename[:-4] + "_mask.png"), pred_mask)

                # save the geotiff meta data to mask file
                with rasterio.open(os.path.join(cfg.result_dir, filename[:-4] + "_mask.tif"), "w", **meta) as dst:
                    dst.write(np.expand_dims(pred_mask, axis=0))

                # prepare plot for visual comparison
                prepare_plot(os.path.join(cfg.result_dir, filename[:-4] + ".png"), origin, None, pred_mask,
                             cfg.classes)

            if not os.path.exists(f'{cfg.result_dir}'):
                os.makedirs(f'{cfg.result_dir}')

        else:

            # find the filename and generate the path to ground truth mask
            gt_path = os.path.join(cfg.test_mask_dir, filename)

            # load the ground-truth segmentation mask in grayscale mode and resize it
            gt_mask = cv2.imread(gt_path, 0)

            # remap gt mask if needed
            if cfg.remapping is not None:
                remapped_mask = gt_mask.copy()
                for old_value, new_value in cfg.remapping.items():
                    remapped_mask[gt_mask == int(old_value)] = new_value
                gt_mask = remapped_mask

            # prepare a plot for visualization
            if not os.path.exists(f'{cfg.result_dir}'):
                os.makedirs(f'{cfg.result_dir}')
            prepare_plot(os.path.join(cfg.result_dir, filename), origin, gt_mask, pred_mask, cfg.classes)
            print("after: ", np.unique(gt_mask))

if __name__ == '__main__':
    predict()
