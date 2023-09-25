"""
Testing for multi-class mining site segmentation.
"""

import hydra
from omegaconf import DictConfig
from tqdm import tqdm
import torch
from torchmetrics import Accuracy, F1Score, Precision, Recall, ConfusionMatrix
import segmentation_models_pytorch as smp
from torch.nn import DataParallel

from dataset import load_data
from utils import print_matrix, set_seed, init_device


@hydra.main(config_path='./conf', config_name='config', version_base='1.2')
def test(cfg: DictConfig):
    """
    Testing.
    """
    # initialize device
    init_device(cfg.gpu_ids)
    device = torch.device('cuda' if cfg.device == 'cuda' and torch.cuda.is_available() else 'cpu')

    # fix randomness
    set_seed(cfg.seed)

    # load data
    test_dataloader = load_data(batch_size=cfg.batch_size, num_workers=cfg.num_workers,
                                image_dir=cfg.test_image_dir, mask_dir=cfg.test_mask_dir)

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
        activation='softmax2d',               # activation function after the final convolution layer
    )
    # port model to GPUs
    model = DataParallel(model)
    model.to(device)

    # load checkpoint
    state = torch.load(cfg.checkpoint_path)
    model.load_state_dict(state['state_dict'])

    # define metrics
    accuracy = Accuracy(task="multiclass", num_classes=len(cfg.classes)).to(device)
    f1 = F1Score(task="multiclass", num_classes=len(cfg.classes)).to(device)
    precision = Precision(task="multiclass", average='macro', num_classes=len(cfg.classes)).to(device)
    recall = Recall(task="multiclass", average='macro', num_classes=len(cfg.classes)).to(device)
    confusion_matrix = ConfusionMatrix(task="multiclass", num_classes=len(cfg.classes)).to(device)

    # start evaluation
    print('start evaluation...')

    # evaluation epoch
    model.eval()
    pbar_test = tqdm(test_dataloader)
    accuracy_test, f1_test, precision_test, recall_test, confusion_test = 0, 0, 0, 0, 0
    for (images, targets) in pbar_test:
        with torch.no_grad():
            images = images.to(device)
            targets = targets.squeeze().to(device)
            outs = model(images)

            accuracy_test += accuracy(outs, targets)
            f1_test += f1(outs, targets)
            precision_test += precision(outs, targets)
            recall_test += recall(outs, targets)
            confusion_test += confusion_matrix(outs, targets)

    accuracy_test /= len(pbar_test)
    f1_test /= len(pbar_test)
    precision_test /= len(pbar_test)
    recall_test /= len(pbar_test)

    print('Test: accuracy={:.2f}, f1={:.2f}, precision={:.2f}, recall={:.2f}'.format(accuracy_test, f1_test, precision_test, recall_test))
    print(f'Confusion matrix:')
    print_matrix(confusion_test)


if __name__ == '__main__':
    test()
