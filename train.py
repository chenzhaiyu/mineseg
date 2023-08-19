"""
Supervised training for multi-class mining site segmentation.
"""

import os
import logging
from pathlib import Path

import hydra
from omegaconf import DictConfig
from tqdm import tqdm
import torch
import torch.nn.functional as F
from torchmetrics import Accuracy, F1Score, Precision, Recall, ConfusionMatrix
import segmentation_models_pytorch as smp
from segmentation_models_pytorch.encoders import get_preprocessing_fn

from dataset import MiningSectorDataset, load_data
from utils import print_matrix, set_seed


@hydra.main(config_path='./conf', config_name='config', version_base='1.2')
def train(cfg: DictConfig):
    """
    Training.
    """

    #fix randomness
    set_seed(cfg.seed)

    # specify GPU
    os.environ['CUDA_VISIBLE_DEVICES'] = str(cfg.gpu_id)  # assume single GPU
    device = torch.device('cuda' if cfg.device=='cuda' and torch.cuda.is_available() else 'cpu')

    # load data
    train_dataloader, test_dataloader = load_data(root=cfg.data_root, batch_size=cfg.batch_size, num_workers=cfg.num_workers)

    # define model
    model = smp.Unet(
        encoder_name=cfg.encoder,             # choose encoder, e.g. mobilenet_v2 or efficientnet-b7
        encoder_weights=cfg.encoder_weights,  # use `imagenet` pre-trained weights for encoder initialization
        in_channels=cfg.in_channel,           # model input channels (1 for gray-scale images, 3 for RGB, etc.)
        classes=len(cfg.classes),             # model output channels (number of classes in your dataset)
        activation='softmax2d',               # activation function after the final convolution layer
    )
    model.to(device)

    # define preprocessing
    preprocessing_fn = smp.encoders.get_preprocessing_fn(cfg.encoder, cfg.encoder_weights)

    # define loss
    loss = smp.losses.DiceLoss(mode='multiclass')

    # define optimizer
    optimizer = torch.optim.Adam(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)

    # define metrics
    accuracy = Accuracy(task="multiclass", num_classes=len(cfg.classes)).to(device)
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

            pbar_train.set_postfix_str('loss={:.2f}, accuracy={:.2f}, f1={:.2f}, precision={:.2f}, recall={:.2f}'.format(loss_, accuracy(outs, targets), f1(outs, targets), precision(outs, targets), recall(outs, targets)))

            loss_.backward()
            optimizer.step()

        # evaluation epoch
        torch.cuda.empty_cache()
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

        # save checkpoint
        state = {
            'epoch': i,
            'state_dict': model.state_dict(),
            'optimizer': optimizer.state_dict(),
            'accuracy': accuracy_test,
        }
        torch.save(state, f'{cfg.checkpoint_dir}/checkpoint_{i}.pth')
        if accuracy_test > best_accuracy:
            print('checkpoint saved...')
            torch.save(state, f'{cfg.checkpoint_path}')
            best_accuracy = accuracy_test


if __name__ == '__main__':
    train()
