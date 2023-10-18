import matplotlib.pyplot as plt
import numpy as np
import torch
import os
import random


def matrix_to_string(matrix):
    return '\n'.join([''.join(['{:10}'.format(item) for item in row]) for row in matrix])


def prepare_plot(filename, origImage, origMask, predMask):
    # initialize our figure
    figure, ax = plt.subplots(nrows=1, ncols=3, figsize=(10, 10))

    # plot the original image, its mask, and the predicted mask
    ax[0].imshow(origImage)
    ax[1].imshow(origMask)
    ax[2].imshow(predMask)

    # set the titles of the subplots
    ax[0].set_title("Image")
    ax[1].set_title("GT Mask")
    ax[2].set_title("Predicted Mask")

    # set the layout of the figure and display it
    figure.tight_layout()
    figure.show()
    figure.savefig(filename)
    plt.close()


def set_seed(seed: int) -> None:
    """
    Set singular seed to fix randomness.
    May need to be repeatedly invoked (at least for np.random).
    """
    np.random.seed(seed)
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    # When running on the CuDNN backend, two further options must be set
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    # Set a fixed value for the hash seed
    os.environ["PYTHONHASHSEED"] = str(seed)


def init_device(use_cuda, gpu_ids):
    """
    Init CUDA environment.

    Parameters
    ----------
    use_cuda: bool
        Use CUDA if set True
    gpu_ids: list of int
        GPU indices to use
    """
    torch.multiprocessing.set_sharing_strategy('file_system')

    # does not work after import torch with PyTorch 2.0
    # os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
    # os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_ids)[1:-1]

    # the first cuda device scatters and gathers data
    return torch.device(f'cuda:{gpu_ids[0]}' if use_cuda and torch.cuda.is_available() else 'cpu')
