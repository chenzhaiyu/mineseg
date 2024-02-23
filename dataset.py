import os

import cv2
import torch
from torch.utils.data import DataLoader, Dataset


class MiningSectorDataset(Dataset):
    def __init__(self, image_dir, mask_dir, remapping):
        self.image_dir = image_dir
        self.mask_dir = mask_dir
        self.filenames = os.listdir(image_dir)[:]
        self.remapping = remapping
    
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

        # resize all images (just for debugging)
        # image = cv2.resize(image, (256,256))
        # mask = cv2.resize(mask, (256,256))

        # convert data
        image = torch.from_numpy(image.transpose(2, 0, 1).astype('float32'))
        mask = torch.from_numpy(mask.astype('int64')).unsqueeze(0)

        # map index for mask
        if self.remapping is not None:
            remapped_mask = mask.clone()
            for old_value, new_value in self.remapping.items():
                remapped_mask[mask == int(old_value)] = new_value
            mask = remapped_mask
        return image, mask


def load_data(batch_size, num_workers, image_dir, mask_dir, remapping=None):
    """
    Data loading.
    """
    dataset = MiningSectorDataset(image_dir, mask_dir, remapping)
    print(f"Dataset size: {len(dataset)}")
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=num_workers)
    return dataloader
