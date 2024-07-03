import pdb 
import os
import cv2
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision.transforms import v2 as transforms

class MiningSectorDataset(Dataset):
    def __init__(self, image_dir, mask_dir, remapping):
        self.image_dir = image_dir
        self.mask_dir = mask_dir
        self.filenames = os.listdir(image_dir)[:]
        self.remapping = remapping
        
        self.transform = transforms.Compose([
            transforms.RandomApply([transforms.GaussianBlur(kernel_size=3)], p=0.5),
            transforms.RandomApply([transforms.RandomAdjustSharpness(sharpness_factor=2)], p=0.5),
            transforms.RandomApply([transforms.RandomAdjustSharpness(sharpness_factor=0.5)], p=0.5),
            transforms.RandomRotation(degrees=(90, 90)),
            transforms.RandomRotation(degrees=(180, 180)),
            transforms.RandomRotation(degrees=(270, 270)),
        ])
    
    def __len__(self):
        return len(self.filenames)
    
    def __getitem__(self, idx):
        
        image_filename = self.filenames[idx]
        image_path = os.path.join(self.image_dir, image_filename)
        mask_path = os.path.join(self.mask_dir, image_filename)  # Adjust file extension if needed
        
        # read data
        try:
            image = cv2.imread(image_path)
            # image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) # the geotiff are already RGB
            mask = cv2.imread(mask_path, 0)
        except Exception as e:
            print("error in file: ", image_path)

        # resize all images (just for debugging)
        # image = cv2.resize(image, (256,256))
        # mask = cv2.resize(mask, (256,256))

        # do padding
        # height, width = image.shape[:2]
        # desired_size = 256

        # Compute padding
        # delta_width = desired_size - width
        # delta_height = desired_size - height
        # top, bottom = delta_height//2, delta_height-(delta_height//2)
        # left, right = delta_width//2, delta_width-(delta_width//2)

        # image = cv2.copyMakeBorder(image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[0,0,0])
        # mask = cv2.copyMakeBorder(mask, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[0,0,0])

        # convert data
        image = torch.from_numpy(image.transpose(2, 0, 1).astype('float32'))
        mask = torch.from_numpy(mask.astype('int64')).unsqueeze(0)

        # map index for mask
        if self.remapping is not None:
            remapped_mask = mask.clone()
            for old_value, new_value in self.remapping.items():
                remapped_mask[mask == int(old_value)] = new_value
            mask = remapped_mask

        # Apply transformations
        augmented_images = []
        augmented_masks = []
        for transform in self.transform.transforms:
            augmented_image = transform(image)
            augmented_mask = transform(mask)
            augmented_images.append((augmented_image, mask))

        return augmented_images



def load_data(batch_size, num_workers, image_dir, mask_dir, remapping=None):
    """
    Data loading.
    """
    dataset = MiningSectorDataset(image_dir, mask_dir, remapping)
    print(f"Dataset size: {len(dataset)}")
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=num_workers)
    return dataloader

