import os
import random
import pdb
import matplotlib.pyplot as plt
import numpy as np
import torch
from matplotlib.lines import Line2D
from matplotlib.colors import ListedColormap


def matrix_to_string(matrix):
    return '\n'.join([''.join(['{:10}'.format(item) for item in row]) for row in matrix])


def prepare_plot(filename, image, gt, prediction, classes):
    
    # check if ground truth is empty and replace it with prediction
    if gt is None:
        gt = np.zeros((256,256))
    
    # initialize our figure
    figure, ax = plt.subplots(nrows=1, ncols=3, figsize=(10, 10))

    # create colormap
    cmap = plt.get_cmap('tab10')
    colors = cmap(range(len(classes)))
    cmap = ListedColormap(colors)

    # plot the original image, its mask, and the predicted mask
    ax[0].imshow(image)
    ax[1].imshow(gt, cmap=cmap)
    ax[2].imshow(prediction, cmap=cmap)

    # create a legend with labels for each class using Line2D objects
    legend_elements = [Line2D([0], [0], marker='o', color='w', markersize=10, markerfacecolor=colors[i],
                              label=classes[i]) for i in range(len(classes))]

    # add the legend to the plot
    plt.legend(handles=legend_elements, bbox_to_anchor=(1.05, 1), loc='upper left', title='Classes')

    # set the titles of the subplots
    ax[0].set_title("Image")
    ax[1].set_title("GT Mask")
    ax[2].set_title("Predicted")

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
