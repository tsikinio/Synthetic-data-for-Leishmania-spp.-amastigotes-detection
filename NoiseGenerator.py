import cv2
import numpy as np
import os

def add_gaussian_noise(image, mean=0, std=25):
    """Applies Gaussian noise to an image while preserving transparency and keeping original brightness."""
    if image.shape[2] == 4:  # Check if image has an alpha channel
        alpha = image[:, :, 3]  # Extract alpha channel
        image_rgb = image[:, :, :3]  # Extract RGB channels
        
        gauss = np.random.normal(mean, std, image_rgb.shape).astype(np.int16)
        noisy_image = np.clip(image_rgb + gauss, 0, 255).astype(np.uint8)  # Ensure values remain valid
        
        # Merge the alpha channel back
        noisy_image = cv2.merge((noisy_image, alpha))
    else:
        gauss = np.random.normal(mean, std, image.shape).astype(np.int16)
        noisy_image = np.clip(image + gauss, 0, 255).astype(np.uint8)  # Keep brightness unchanged
    
    return noisy_image

def process_images(input_folder, output_folder, mean=0, std=25):
    """Applies Gaussian noise to all images in the input folder and saves them in the output folder."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    for filename in os.listdir(input_folder):
        if filename.lower().endswith(('png', 'jpg', 'jpeg')):
            img_path = os.path.join(input_folder, filename)
            image = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)  # Preserve transparency
            if image is None:
                continue
            
            noisy_image = add_gaussian_noise(image, mean, std)
            noisy_filename = f"noisy_{filename}"
            output_path = os.path.join(output_folder, noisy_filename)
            cv2.imwrite(output_path, noisy_image, [cv2.IMWRITE_PNG_COMPRESSION, 9])  # Preserve PNG transparency
            print(f"Saved: {output_path}")



if __name__ == "__main__":
    input_folder = "PATH_TO_IMAGES"  # Change to your input folder
    output_folder = "OUTPUT_FOLDER"  # Change to your output folder
    process_images(input_folder, output_folder)
