import os
from PIL import Image

def delete_black_images(folder_path):
    # Iterate over all PNG files in the given folder
    for filename in os.listdir(folder_path):
        if filename.endswith(".png"):
            file_path = os.path.join(folder_path, filename)
            try:
                # Open the image
                with Image.open(file_path) as img:
                    # Convert image to RGBA (to handle images with alpha channel)
                    img = img.convert("RGBA")
                    # Extract all pixels
                    pixels = list(img.getdata())
                    # Check if all pixels are black (including transparent pixels)
                    if all(pixel[:3] == (0, 0, 0) for pixel in pixels):
                        # Delete the image if all pixels are black
                        os.remove(file_path)
                        os.remove('./roi_masks_patches/' + os.path.basename(file_path))
                        print(f"Deleted '{filename}' as it contains only black pixels.")                        
            except Exception as e:
                print(f"Error processing {filename}: {e}")

# Specify the folder to check
folder_path = './roi_images_patches/'
delete_black_images(folder_path)