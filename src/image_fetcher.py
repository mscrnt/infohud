################################################################################
# FILE: image_fetcher.py
# DESCRIPTION: Fetches and returns the next image from a directory.
# AUTHOR: MSCRNT LLC.
#
# THIS CODE IS PROPRIETARY PROPERTY OF MSCRNT LLC.
################################################################################

import os
import logging
import logging.handlers
from PIL import Image

# Configure logging with single daily log file
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, "infoHUD.log")

logger = logging.getLogger("image_fetcher")
logger.setLevel(logging.INFO)
handler = logging.handlers.TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=7, utc=True)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Image directory
IMAGE_DIR = "assets/images"

class ImageFetcher:
    def __init__(self):
        """Initialize the image fetcher."""
        self.image_files = self._get_image_files()
        self.current_index = 0

    def _get_image_files(self):
        """Retrieve a list of image files from the directory."""
        if not os.path.exists(IMAGE_DIR):
            os.makedirs(IMAGE_DIR, exist_ok=True)
            logger.warning(f"Image directory '{IMAGE_DIR}' did not exist. Created it.")
            return []

        images = sorted([
            os.path.join(IMAGE_DIR, f)
            for f in os.listdir(IMAGE_DIR)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp"))
        ])

        if not images:
            logger.warning("No images found in the directory.")

        return images

    def fetch_next_image(self):
        """Return the next image in the sequence."""
        if not self.image_files:
            logger.error("No images available to fetch.")
            return None

        image_path = self.image_files[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.image_files)

        logger.info(f"Fetched image: {image_path}")
        return Image.open(image_path)

if __name__ == "__main__":
    """Test the image fetcher by displaying the next image."""
    fetcher = ImageFetcher()
    image = fetcher.fetch_next_image()
    if image:
        image.show()
