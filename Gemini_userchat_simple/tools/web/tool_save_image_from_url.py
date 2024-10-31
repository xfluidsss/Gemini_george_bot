tool_type_for_TOOL_MANAGER = "web"
tool_save_image_from_url_short_description = "Saves an image from a URL to a specified path."

import requests
import os
import logging

# Set up logging (optional, but recommended)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def tool_save_image_from_url(image_url: str, save_path: str):
    """
    Saves an image from a URL to the specified path.

    Args:
        image_url (str): The URL of the image.
        save_path (str): The full path where the image should be saved including filename. Defaults ./

    Returns:
        dict: A dictionary containing the status  success or failure  and a message.
    """
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        # Create directories if they don't exist
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, 'wb') as out_file:
            for chunk in response.iter_content(chunk_size=8192):
                out_file.write(chunk)

        logger.info(f"Image saved successfully to: {save_path}")
        return {"status": "success", "message": f"Image saved successfully to: {save_path}"}

    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading image: {e}")
        return {"status": "failure", "message": f"Error downloading image: {e}"}
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        return {"status": "failure", "message": f"An unexpected error occurred: {e}"}