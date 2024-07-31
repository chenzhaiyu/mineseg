"""
Supervised training for multi-class mining site segmentation.
"""
import os
import logging
import pdb
import wandb
import hydra
from omegaconf import DictConfig
from tqdm import tqdm
import torch
from torchmetrics import F1Score, Precision, Recall, ConfusionMatrix
from torchmetrics.classification import MulticlassAccuracy
import segmentation_models_pytorch as smp
from torch.nn import DataParallel, CrossEntropyLoss
from dataset import load_data
from utils import matrix_to_string, set_seed, init_device


@hydra.main(config_path='./conf', config_name='config', version_base='1.2')
def train(cfg: DictConfig):
    """
    Training.
    """
    # initialize logging
    logger = logging.getLogger('Train')
    wandb_mode = 'online' if cfg.wandb else 'disabled'
    wandb.init(mode=wandb_mode, project=cfg.wandb_project, entity=cfg.wandb_entity, dir=cfg.wandb_dir)
    wandb.save('./outputs/.hydra/*')

    # initialize device
    device = init_device(cfg.use_cuda, cfg.gpu_ids)
    logger.info(f"Device initialized: " + f"CUDA: {cfg.gpu_ids}" if cfg.use_cuda else "CPU")

    # fix randomness
    set_seed(cfg.seed)
    logger.info(f"Random seed set to {cfg.seed}")

    # load data
    train_dataloader = load_data(batch_size=cfg.batch_size, num_workers=cfg.num_workers,
                                 image_dir=cfg.train_image_dir, mask_dir=cfg.train_mask_dir, remapping=cfg.remapping)
    test_dataloader = load_data(batch_size=cfg.batch_size, num_workers=cfg.num_workers,
                                image_dir=cfg.test_image_dir, mask_dir=cfg.test_mask_dir, remapping=cfg.remapping)
    valid_dataloader = load_data(batch_size=cfg.batch_size, num_workers=cfg.num_workers,
                                image_dir=cfg.valid_image_dir, mask_dir=cfg.valid_mask_dir, remapping=cfg.remapping)


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
        raise ValueError(f'Unexpected model architecture: {cfg.model}')
    model = _model(
        encoder_name=cfg.encoder,             # choose encoder, e.g. mobilenet_v2 or efficientnet-b7
        encoder_weights=cfg.encoder_weights,  # use `imagenet` pre-trained weights for encoder initialization
        in_channels=cfg.in_channel,           # model input channels (1 for gray-scale images, 3 for RGB, etc.)
        classes=len(cfg.classes),             # model output channels (number of classes in your dataset)
        activation=cfg.activation,            # activation function after the final convolution layer
    )

    # freeze encoder if specified
    if cfg.freeze_encoder:
        logger.info(f'Freezing encoder')
        for param in model.encoder.parameters():
            param.requires_grad = False

    # port model to GPUs
    model = DataParallel(model, device_ids=cfg.gpu_ids)
    model.to(device)

    # Class weighting for imbalance handling
    # class_weights = torch.FloatTensor([1, 20]).cuda()

    # define loss
    if cfg.loss == 'dice':
        loss = smp.losses.DiceLoss(mode='multiclass')
    elif cfg.loss == 'focal':
        loss = smp.losses.FocalLoss(mode='multiclass')
    elif cfg.loss == 'ce':
        # loss = CrossEntropyLoss(weight=class_weights)
        loss = CrossEntropyLoss()
    else:
        raise ValueError(f'Unexpected loss: {cfg.loss}')

    # define optimizer and scheduler
    optimizer = torch.optim.Adam(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    # https://github.com/pytorch/pytorch/issues/90414 & https://github.com/pytorch/pytorch/pull/91400

    
    scheduler = torch.optim.lr_scheduler.CyclicLR(optimizer, base_lr=cfg.scheduler.base_lr, max_lr=cfg.scheduler.max_lr,
                                                  step_size_up=cfg.scheduler.step_size_up, mode=cfg.scheduler.mode,
                                                  cycle_momentum=False)

    # scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min')

    # define metrics
    metric_macro = MulticlassAccuracy(num_classes=len(cfg.classes), average="macro").to(device)
    metric_micro = MulticlassAccuracy(num_classes=len(cfg.classes), average="micro").to(device)
    metric_weighted = MulticlassAccuracy(num_classes=len(cfg.classes), average="weighted").to(device)
    f1 = F1Score(task="multiclass", num_classes=len(cfg.classes)).to(device)
    precision = Precision(task="multiclass", average='macro', num_classes=len(cfg.classes)).to(device)
    recall = Recall(task="multiclass", average='macro', num_classes=len(cfg.classes)).to(device)
    confusion_matrix = ConfusionMatrix(task="multiclass", num_classes=len(cfg.classes)).to(device)

    # warm start from checkpoint if applicable
    if cfg.warm:
        state = torch.load(cfg.checkpoint_path)
        model.load_state_dict(state['state_dict'])
        if state['epoch'] > cfg.num_epochs:
            logger.info(f'Expected epoch reached from checkpoint')
            return
        epoch_generator = range(state['epoch'] + 1, cfg.num_epochs)
        best_accuracy = state['accuracy']
        logger.info(f'Resuming from {cfg.checkpoint_path}')

        if cfg.warm_optimizer:
            try:
                optimizer.load_state_dict(state['optimizer'])
                logger.info(f'Optimizer loaded from checkpoint')
            except (KeyError, ValueError) as error:
                logger.warning(f'Optimizer not loaded from checkpoint: {error}')

        if cfg.warm_scheduler:
            try:
                scheduler.load_state_dict(state['scheduler'])
                logger.info(f'Scheduler loaded from checkpoint')
            except (KeyError, ValueError) as error:
                logger.warning(f'Scheduler not loaded from checkpoint: {error}')

    else:
        epoch_generator = range(cfg.num_epochs)
        best_accuracy = 0
        logger.info('Start training...')

    # start training
    for i in epoch_generator:

        print(f"\n\n")

        # training epoch
        model.train()
        pbar_train = tqdm(train_dataloader, desc=f'epoch {i}')

        # wandb epoch logging
        wandb.log({"epoch": i})
        wandb.log({"learning_rate": optimizer.param_groups[0]['lr']})

        # show training progress
        for (images, targets) in pbar_train:
            images = images.to(device)
            targets = targets.squeeze().to(device)

            optimizer.zero_grad()
            outs = model(images).float()

            # compute metrics
            loss_train = loss(outs, targets)
            macro_train = metric_macro(outs, targets)
            micro_train = metric_micro(outs, targets)
            weighted_train = metric_weighted(outs, targets)
            f1_train = f1(outs, targets)
            precision_train = precision(outs, targets)
            recall_train = recall(outs, targets)

            # wandb training logging
            wandb.log({"loss": loss_train})
            wandb.log({"macro_train": macro_train})
            wandb.log({"micro_train": micro_train})
            wandb.log({"weighted_train": weighted_train})
            wandb.log({"f1_train": f1_train})
            wandb.log({"precision_train": precision_train})
            wandb.log({"recall_train": recall_train})

            pbar_train.set_postfix_str(
                'loss={:.4f}, metric_macro={:.4f}, metric_micro={:.4f}, metric_weighted={:.4f}, f1={:.4f}, precision={:.4f}, '
                'recall={:.4f}'.format(loss_train, macro_train, micro_train, weighted_train, f1_train, precision_train, recall_train))

            loss_train.backward()
            optimizer.step()


        f1_valid, precision_valid, recall_valid, confusion_valid, macro_valid, micro_valid, weighted_valid = 0, 0, 0, 0, 0, 0, 0


        # VALIDATION DATASET
        # show validation progress
        pbar_valid = tqdm(valid_dataloader, desc=f'epoch {i}')
        for (images, targets) in pbar_valid:
            images = images.to(device)
            targets = targets.squeeze().to(device)

            optimizer.zero_grad()
            outs = model(images)
            
            # compute metrics
            loss_valid = loss(outs, targets)
            macro_valid += metric_macro(outs, targets)
            micro_valid += metric_micro(outs, targets)
            weighted_valid += metric_weighted(outs, targets)
            f1_valid += f1(outs, targets)
            precision_valid += precision(outs, targets)
            recall_valid += recall(outs, targets)
            confusion_valid += confusion_matrix(outs, targets)

            scheduler.step()
            # scheduler.step(loss_valid)  # for ReduceLROnPlateau Scheduler

        # calculate the average
        loss_valid /= len(pbar_valid)
        macro_valid /= len(pbar_valid)
        micro_valid /= len(pbar_valid)
        weighted_valid /= len(pbar_valid)
        f1_valid /= len(pbar_valid)
        precision_valid /= len(pbar_valid)
        recall_valid /= len(pbar_valid)
        

        # console evaluation logging
        print("\nperformance on VALIDATION Set:")
        logger.info(
            'metric_macro={:.4f}, metric_micro={:.4f}, metric_weighted={:.4f}, f1={:.4f}, precision={:.4f}, '
            'recall={:.4f}'.format(macro_valid, micro_valid, weighted_valid, f1_valid, precision_valid, recall_valid))
        logger.info(f'Confusion matrix VALID: \n{matrix_to_string(confusion_valid)}')

        # wandb valid logging
        wandb.log({"macro_valid": macro_valid})
        wandb.log({"micro_valid": micro_valid})
        wandb.log({"weighted_valid": weighted_valid})
        wandb.log({"f1_valid": f1_valid})
        wandb.log({"precision_valid": precision_valid})
        wandb.log({"recall_valid": recall_valid})


        # TEST DATASET
        # evaluation epoch
        torch.cuda.empty_cache()
        model.eval()
        pbar_test = tqdm(test_dataloader)
        f1_test, precision_test, recall_test, confusion_test, macro_test, micro_test, weighted_test = 0, 0, 0, 0, 0, 0, 0
    
        for (images, targets) in pbar_test:
            with torch.no_grad():
                images = images.to(device)
                targets = targets.squeeze().to(device)
                outs = model(images)

                macro_test += metric_macro(outs, targets)
                micro_test += metric_micro(outs, targets)
                weighted_test += metric_weighted(outs, targets)
                f1_test += f1(outs, targets)
                precision_test += precision(outs, targets)
                recall_test += recall(outs, targets)
                confusion_test += confusion_matrix(outs, targets)

        f1_test /= len(pbar_test)
        precision_test /= len(pbar_test)
        recall_test /= len(pbar_test)
        macro_test /= len(pbar_test)
        micro_test /= len(pbar_test)
        weighted_test /= len(pbar_test)

        # console evaluation logging
        print("\nperformance on TEST Set:")
        logger.info(
            'TEST: metric_macro={:.2f}, metric_micro={:.2f}, metric_weighted={:.2f}, f1={:.2f}, precision={:.2f}, '
            'recall={:.2f}'.format(macro_test, micro_test, weighted_test, f1_test, precision_test, recall_test))
        logger.info(f'Confusion matrix TEST: \n{matrix_to_string(confusion_test)}')

        # wandb evaluation logging
        wandb.log({"macro_test": macro_test})
        wandb.log({"micro_test": micro_test})
        wandb.log({"weighted_test": weighted_test})
        wandb.log({"f1_test": f1_test})
        wandb.log({"precision_test": precision_test})
        wandb.log({"recall_test": recall_test})
        
        # save checkpoint
        state = {
            'epoch': i,
            'state_dict': model.state_dict(),
            'optimizer': optimizer.state_dict(),
            'scheduler': scheduler.state_dict(),
            'accuracy': metric_macro,
        }
        if not os.path.exists(f'{cfg.checkpoint_dir}'):
            os.makedirs(f'{cfg.checkpoint_dir}')

        # Cannot pickle 'WeakMethod' object when saving state_dict for CyclicLr
        # https://github.com/pytorch/pytorch/pull/91400
        torch.save(state, f'{cfg.checkpoint_dir}/checkpoint_{i}.pth')
        if macro_valid > best_accuracy:
            torch.save(state, f'{cfg.checkpoint_path}')
            logger.info(f'Saving checkpoint to {cfg.checkpoint_path}.')
            best_accuracy = macro_valid


if __name__ == '__main__':
    train()
