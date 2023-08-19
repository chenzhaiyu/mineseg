import matplotlib.pyplot as plt
import numpy as np
import torch
import cv2
import os
import random


def print_matrix(matrix):
	print('\n'.join([''.join(['{:10}'.format(item) for item in row]) for row in matrix]))


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

