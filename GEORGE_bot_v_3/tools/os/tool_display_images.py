tool_type_for_TOOL_MANAGER = "web"
tool_display_images_short_description = "Displays images one by one from a list of URLs or local file paths (full or relative) or from a given folder."
import  requests
import os
import logging
from typing import List, Dict, Any
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def tool_display_images(image_paths_or_folder: str, delay: float = 1):
    """
    Displays images one by one from a list of URLs or local file paths (full or relative) or from a given folder.

    Args:
        image_paths_or_folder (str): A single string representing either:
            - A list of image URLs or local file paths separated by commas (e.g., "http://example.com/image1.jpg, path/to/image2.png, ../../image3.jpg")
            - A folder path containing images (e.g., "path/to/images").
        delay (float, optional): The delay between displaying images in seconds. Defaults to 1.

    Returns:
        dict: A dictionary containing the status "success" or "failure" and a message.
    """
    try:
        image_paths = []

        # Check if the input is a folder path (exists and is a directory)
        if os.path.isdir(image_paths_or_folder):
            # Get all image files from the folder
            for filename in os.listdir(image_paths_or_folder):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    image_paths.append(os.path.join(image_paths_or_folder, filename))

        # Otherwise, assume it's a comma-separated list of paths
        else:
            image_paths = [path.strip() for path in image_paths_or_folder.split(",")]

        if not image_paths:
            return {"status": "failure", "message": "No image paths or images found in the provided folder or list."}

        # Display each image
        for i, image_path in enumerate(image_paths):
            print(f"Displaying image {i+1} of {len(image_paths)}: {image_path}")

            # Check if the image path is a URL
            if image_path.startswith(("http://", "https://")):
                # Display from URL (using Pillow or OpenCV)
                from PIL import Image
                from io import BytesIO
                response = requests.get(image_path)
                img = Image.open(BytesIO(response.content))
                img.show()
            else:
                # Display from local file path (full or relative)
                # Resolve relative paths
                image_path = os.path.abspath(image_path)
                from PIL import Image
                img = Image.open(image_path)
                img.show()

            time.sleep(delay)

        return {"status": "success", "message": "All images displayed."}

    except Exception as e:
        logger.error(f"An error occurred while displaying images: {str(e)}")
        return {"status": "failure", "message": f"Error displaying images: {str(e)}"}