import os

import cv2
import torch
from torch.utils.data import DataLoader, Dataset


class MiningSectorDataset(Dataset):
    def __init__(self, image_dir, mask_dir):
        self.image_dir = image_dir
        self.mask_dir = mask_dir
        self.filenames = os.listdir(image_dir)[:]
    
    def __len__(self):
        return len(self.filenames)
    
    def __getitem__(self, idx):
        image_filename = self.filenames[idx]
        image_path = os.path.join(self.image_dir, image_filename)
        mask_path = os.path.join(self.mask_dir, image_filename)  # Adjust file extension if needed
        
        # read data
        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mask = cv2.imread(mask_path, 0)

        # convert data
        image = torch.from_numpy(image.transpose(2, 0, 1).astype('float32'))
        mask = torch.from_numpy(mask.astype('int64')).unsqueeze(0)
        
        return image, mask


def load_data(root='./', batch_size=2, num_workers=0):
    """
    Data loading.
    """
    train_dataset = MiningSectorDataset(os.path.join(root, "patches_img_trainset"), os.path.join(root, "patches_mask_trainset"))
    test_dataset = MiningSectorDataset(os.path.join(root, "patches_img_testset"), os.path.join(root, "patches_mask_testset"))

    # check two splits don`t intersects with each other
    assert set(test_dataset.filenames).isdisjoint(set(train_dataset.filenames))

    print(f"Train size: {len(train_dataset)}")
    print(f"Test size: {len(test_dataset)}")

    train_dataloader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=num_workers)
    test_dataloader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers)

    return train_dataloader, test_dataloader
