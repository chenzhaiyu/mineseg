"""
Supervised training for multi-class mining site segmentation.
"""

import os

import hydra
from omegaconf import DictConfig
from tqdm import tqdm
import torch
from torchmetrics import Accuracy, F1Score, Precision, Recall, ConfusionMatrix
from torchmetrics.classification import MulticlassAccuracy
import segmentation_models_pytorch as smp
from torch.nn import DataParallel

from dataset import load_data
from utils import print_matrix, set_seed, init_device


@hydra.main(config_path='./conf', config_name='config', version_base='1.2')
def train(cfg: DictConfig):
    """
    Training.
    """
    # initialize device
    init_device(cfg.gpu_ids)
    device = torch.device('cuda' if cfg.device == 'cuda' and torch.cuda.is_available() else 'cpu')

    # fix randomness
    set_seed(cfg.seed)

    # load data
    train_dataloader = load_data(batch_size=cfg.batch_size, num_workers=cfg.num_workers,
                                 image_dir=cfg.train_image_dir, mask_dir=cfg.train_mask_dir)
    test_dataloader = load_data(batch_size=cfg.batch_size, num_workers=cfg.num_workers,
                                image_dir=cfg.test_image_dir, mask_dir=cfg.test_mask_dir)

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
        activation='softmax2d',               # activation function after the final convolution layer
    )

    # freeze encoder if specified
    if cfg.freeze_encoder:
        for param in model.encoder.parameters():
            param.requires_grad = False

    # port model to GPUs
    model = DataParallel(model)
    model.to(device)

    # define loss
    loss = smp.losses.DiceLoss(mode='multiclass')

    # define optimizer
    optimizer = torch.optim.Adam(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)

    # define metrics
    accuracy = Accuracy(task="multiclass", num_classes=len(cfg.classes)).to(device)
    mca_a = MulticlassAccuracy(num_classes=len(cfg.classes), average="macro").to(device)
    mca_i = MulticlassAccuracy(num_classes=len(cfg.classes), average="micro").to(device)
    mca_w = MulticlassAccuracy(num_classes=len(cfg.classes), average="weighted").to(device)
    f1 = F1Score(task="multiclass", num_classes=len(cfg.classes)).to(device)
    precision = Precision(task="multiclass", average='macro', num_classes=len(cfg.classes)).to(device)
    recall = Recall(task="multiclass", average='macro', num_classes=len(cfg.classes)).to(device)
    confusion_matrix = ConfusionMatrix(task="multiclass", num_classes=len(cfg.classes)).to(device)

    # warm start from checkpoint if applicable
    if cfg.warm:
        state = torch.load(cfg.checkpoint_path)
        model.load_state_dict(state['state_dict'])
        optimizer.load_state_dict(state['optimizer'])
        epoch_generator = range(state['epoch'] + 1, cfg.num_epochs)
        best_accuracy = state['accuracy']
        print('resume training...')

    else:
        epoch_generator = range(cfg.num_epochs)
        best_accuracy = 0
        print('start training...')

    # start training
    for i in epoch_generator:

        # training epoch
        model.train()
        pbar_train = tqdm(train_dataloader, desc=f'epoch {i}')
        for (images, targets) in pbar_train:
            images = images.to(device)
            targets = targets.squeeze().to(device)

            optimizer.zero_grad()
            outs = model(images)
            loss_ = loss(outs, targets)

            pbar_train.set_postfix_str(
                'loss={:.2f}, accuracy={:.2f}, mca_a={:.2f}, mca_i={:.2f}, mca_w={:.2f}, f1={:.2f}, precision={:.2f}, recall={:.2f}'.format(
                    loss_, accuracy(outs, targets), mca_a(outs, targets), mca_i(outs, targets), mca_w(outs, targets) , f1(outs, targets), precision(outs, targets), recall(outs, targets)))

            loss_.backward()
            optimizer.step()

        # evaluation epoch
        torch.cuda.empty_cache()
        model.eval()
        pbar_test = tqdm(test_dataloader)
        accuracy_test, f1_test, precision_test, recall_test, confusion_test, mca_a_test, mca_i_test, mca_w_test = 0, 0, 0, 0, 0, 0, 0, 0
        for (images, targets) in pbar_test:
            with torch.no_grad():
                images = images.to(device)
                targets = targets.squeeze().to(device)
                outs = model(images)

                accuracy_test += accuracy(outs, targets)
                mca_a_test += mca_a(outs, targets)
                mca_i_test += mca_i(outs, targets)
                mca_w_test += mca_w(outs, targets)
                f1_test += f1(outs, targets)
                precision_test += precision(outs, targets)
                recall_test += recall(outs, targets)
                confusion_test += confusion_matrix(outs, targets)

        accuracy_test /= len(pbar_test)
        f1_test /= len(pbar_test)
        precision_test /= len(pbar_test)
        recall_test /= len(pbar_test)
        mca_a_test /= len(pbar_test)
        mca_i_test /= len(pbar_test)
        mca_w_test /= len(pbar_test)

        print('Test: accuracy={:.2f}, mca_a={:.2f}, mca_i={:.2f}, mca_w={:.2f}, f1={:.2f}, precision={:.2f}, recall={:.2f}'.format(accuracy_test, mca_a_test, mca_i_test, mca_w_test, f1_test,
                                                                                         precision_test, recall_test))
        print(f'Confusion matrix:')
        print_matrix(confusion_test)

        # save checkpoint
        state = {
            'epoch': i,
            'state_dict': model.state_dict(),
            'optimizer': optimizer.state_dict(),
            'acc. macro': mca_a,
        }
        if not os.path.exists(f'{cfg.checkpoint_dir}'):
            os.makedirs(f'{cfg.checkpoint_dir}')
        torch.save(state, f'{cfg.checkpoint_dir}/checkpoint_{i}.pth')
        if mca_a_test > best_accuracy:
            print('checkpoint saved...')
            torch.save(state, f'{cfg.checkpoint_path}')
            best_accuracy = mca_a_test


if __name__ == '__main__':
    train()
