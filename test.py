"""
Testing for multi-class mining site segmentation.
"""

import logging
import pdb
import numpy as np
import hydra
from numpy.ma.extras import average
from omegaconf import DictConfig
from tqdm import tqdm
import torch
from torchmetrics import F1Score, Precision, Recall, ConfusionMatrix
from torchmetrics.classification import MulticlassAccuracy
import segmentation_models_pytorch as smp
from torch.nn import DataParallel

from dataset import load_data
from utils import matrix_to_string, set_seed, init_device


@hydra.main(config_path='./conf', config_name='config', version_base='1.2')
def test(cfg: DictConfig):
    """
    Testing.
    """
    # initialize logging
    logger = logging.getLogger('Test')

    # initialize device
    device = init_device(cfg.use_cuda, cfg.gpu_ids)
    logger.info(f"Device initialized: " + f"CUDA: {cfg.gpu_ids}" if cfg.use_cuda else "CPU")

    # fix randomness
    set_seed(cfg.seed)

    # load data
    test_dataloader = load_data(batch_size=cfg.batch_size, num_workers=cfg.num_workers, image_dir=cfg.test_image_dir,
                                mask_dir=cfg.test_mask_dir, remapping=cfg.remapping)

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

    # load checkpoint
    state = torch.load(cfg.checkpoint_path, map_location=device)
    model.load_state_dict(state['state_dict'])


    # define metrics
    confusion_matrix = ConfusionMatrix(task="multiclass", num_classes=len(cfg.classes)).to(device)

    # start evaluation
    logger.info('Start evaluation...')

    # evaluation epoch
    model.eval()
    pbar_test = tqdm(test_dataloader)
    f1_mac, f1_mic, pre_mac, pre_mic, rec_mac, rec_mic, confusion_test, acc_mac, acc_mic, weighted_test = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    for (images, targets) in pbar_test:
        with torch.no_grad():
            images = images.to(device)
            targets = targets.squeeze().to(device)
            outs = model(images)

            confusion_test += confusion_matrix(outs, targets)


    ## SUMMARY OF RESULTS ##
    # True Positives, False Positives, False Negatives, True Negatives

    TP = np.diag(confusion_test)
    FP = np.sum(confusion_test, axis=0) - TP
    FN = np.sum(confusion_test, axis=1) - TP
    TN = np.sum(confusion_test) - (TP + FP + FN)

    # Sensitivity, hit rate, recall, or true positive rate
    recall = TP / (TP + FN)
    print("rec: ", recall)

    # Precision or positive predictive value
    precision = TP / (TP + FP)
    print("precision: ", precision)

    # Overall accuracy
    accuracy = (TP + TN) / np.sum(confusion_matrix)
    print("accuracy: ", accuracy)

    # fscore
    f1 = 2 * (precision * recall) / (precision + recall)
    print("f1: ", f1)

    logger.info(f'Confusion matrix: \n{matrix_to_string(confusion_test)}')


if __name__ == '__main__':
    test()
