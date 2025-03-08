################################################################################
# FILE: display_manager.py
# DESCRIPTION: Handles ePaper display image management and updates.
# AUTHOR: MSCRNT LLC
#
# THIS CODE IS PROPRIETARY PROPERTY OF MSCRNT LLC.
# The contents of this file may not be disclosed, copied, or duplicated in any
# form, in whole or in part, without the prior written permission of
# MSCRNT LLC.
################################################################################

import os
import sys
import logging
import time
import cairosvg
import logging.handlers
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageOps
from io import BytesIO  # Needed for SVG to PNG conversion

# Ensure Python can find lib/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../lib")))
from waveshare_epd import epd4in0e  # Waveshare ePaper display

# Configure logging
LOG_DIR = "logs"
TMP_DIR = "./tmp/generated"
MAX_IMAGES = 10

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(TMP_DIR, exist_ok=True)

log_file = os.path.join(LOG_DIR, "infoHUD.log")
logger = logging.getLogger("display_manager")
logger.setLevel(logging.INFO)
handler = logging.handlers.TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=7, utc=True)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Display settings
DISPLAY_WIDTH = 600  # Landscape width
DISPLAY_HEIGHT = 400  # Landscape height
HEADER_HEIGHT = 62  # Header height at the top (Before rotation)
BODY_HEIGHT = DISPLAY_HEIGHT - HEADER_HEIGHT  # Body height for the image

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
HEADER_FONT_SIZE = 24
BODY_FONT_SIZE = 18  # ✅ Smaller font for text overlay on images
ICON_SIZE = 48  # ✅ Weather icon size
ICON_PADDING = 20  # ✅ Spacing between icon and temperature
ICON_DIR = "./assets/icons/"  # ✅ Directory for weather icons


class DisplayManager:
    def __init__(self):
        """Initialize the ePaper display and setup fonts."""
        self.epd = epd4in0e.EPD()
        self.epd.init()
        self.width, self.height = self.epd.width, self.epd.height
        self.header_font = ImageFont.truetype(FONT_PATH, HEADER_FONT_SIZE)
        self.body_font = ImageFont.truetype(FONT_PATH, BODY_FONT_SIZE)
        logger.info(f"Display initialized with dimensions: {self.width}x{self.height}")

    def display_image(self, content, content_type, weather_data=None):
        """Generates a full-screen display using a structured table layout."""
        try:
            final_image = self._generate_table(content, weather_data)

            # ✅ Save for debugging
            self._save_debug_image(final_image, content_type)

            # ✅ Send to ePaper display
            buffer = self.epd.getbuffer(final_image)
            self.epd.display(buffer)
            logger.info(f"Displayed {content_type} successfully.")
        except Exception as e:
            logger.error(f"Failed to display {content_type}: {e}")

    def _generate_table(self, content, weather_data):
        """Creates a table layout for the display with a header (weather) and body (image)."""
        try:
            # ✅ Create blank image in landscape mode (600x400)
            display = Image.new("RGB", (DISPLAY_WIDTH, DISPLAY_HEIGHT), (0, 0, 0))

            # ✅ Generate header (date/time/weather) - Place at the **top** BEFORE rotation
            header = self._generate_header(weather_data)
            display.paste(header, (0, 0))  # Header at the top

            # ✅ Generate body (image content)
            body = self._generate_body(content)
            display.paste(body, (0, HEADER_HEIGHT))  # Body below the header

            # ✅ Rotate the entire display to **portrait mode (400x600)**
            display = display.rotate(-90, expand=True)

            return display
        except Exception as e:
            logger.error(f"Error generating table layout: {e}")
            return Image.new("RGB", (DISPLAY_WIDTH, DISPLAY_HEIGHT), (0, 0, 0))  # Return blank image if rendering fails

    def _generate_header(self, weather_data):
        """Creates a structured header containing time, date, and weather icon + temperature."""
        header = Image.new("RGB", (DISPLAY_WIDTH, HEADER_HEIGHT), (0, 0, 0))  # Black background
        draw = ImageDraw.Draw(header)

        # ✅ Date & Time
        current_time = datetime.now().strftime("%H:%M")
        current_date = datetime.now().strftime("%d %b %y")

        # ✅ Temperature & Condition
        temperature = "N/A"
        condition = "Unknown"
        if weather_data and "current" in weather_data:
            temperature = f"{weather_data['current'].get('temperature', 'N/A')}°F"
            condition = weather_data['current'].get('condition', 'Unknown')

        # ✅ Load weather icon instead of condition text
        icon_path = self._get_weather_icon_path(condition)
        weather_icon = self._load_svg_icon(icon_path)

        # ✅ Positioning (Header is landscape before rotation)
        padding = 10
        text_y = HEADER_HEIGHT // 2  # Centered vertically

        # ✅ Draw aligned text
        draw.text((padding, text_y), current_date, font=self.header_font, fill="white", anchor="lm")  # Left-align
        draw.text((DISPLAY_WIDTH // 2, text_y), current_time, font=self.header_font, fill="white", anchor="mm")  # Center-align

        # ✅ Place temperature & icon on the right side
        temp_width = int(draw.textlength(temperature, font=self.header_font))
        total_width = ICON_SIZE + ICON_PADDING + temp_width
        right_x = DISPLAY_WIDTH - padding

        draw.text((right_x, text_y), temperature, font=self.header_font, fill="white", anchor="rm")  # Right-align temperature

        if weather_icon:
            icon_x = right_x - total_width + ICON_SIZE // 2  # Adjust icon position
            icon_y = text_y - (ICON_SIZE // 2)  # Center vertically
            header.paste(weather_icon, (icon_x, icon_y), weather_icon)  # ✅ Properly place icon

        return header

    def _get_weather_icon_path(self, condition):
        """Maps a weather condition to its corresponding SVG icon file path."""
        condition_map = {
            "Clear": "clear-day.svg",
            "Sunny": "clear-day.svg",
            "Partly cloudy": "cloudy-3-day.svg",
            "Cloudy": "cloudy.svg",
            "Overcast": "cloudy.svg",
            "Rain": "rainy-3.svg",
            "Light rain": "rainy-3-day.svg",
            "Heavy rain": "rainy-3-night.svg",
            "Thunderstorm": "thunderstorms.svg",
            "Snow": "snowy-3.svg",
            "Fog": "fog.svg",
            "Haze": "haze.svg",
            "Wind": "wind.svg",
        }
        return os.path.join(ICON_DIR, condition_map.get(condition, "unknown.svg"))

    def _load_svg_icon(self, icon_path):
        """Loads an SVG file and converts it to a PIL image."""
        if os.path.exists(icon_path):
            try:
                png_bytes = cairosvg.svg2png(url=icon_path, output_width=ICON_SIZE, output_height=ICON_SIZE)
                return Image.open(BytesIO(png_bytes)).convert("RGBA")
            except Exception as e:
                logger.error(f"Failed to load weather icon: {e}")
        return None

    def _generate_body(self, image):
        """Places the image in the body section, ensuring it fills the space correctly."""
        try:
            body = Image.new("RGB", (DISPLAY_WIDTH, BODY_HEIGHT), (0, 0, 0))  # Blank background

            if image:
                image = ImageOps.exif_transpose(image)
                image = image.resize((DISPLAY_WIDTH, BODY_HEIGHT), Image.LANCZOS)
                body.paste(image, (0, 0))
            else:
                logger.warning("No image received for the body section.")

            return body
        except Exception as e:
            logger.error(f"Error processing body image: {e}")
            return Image.new("RGB", (DISPLAY_WIDTH, BODY_HEIGHT), (0, 0, 0))

    def _save_debug_image(self, image, image_type):
        """Saves the final formatted image for debugging and keeps only the latest 10."""
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        image_path = os.path.join(TMP_DIR, f"{image_type}_{timestamp}.png")

        image.save(image_path)
        logger.info(f"Debug image saved: {image_path}")

        self._cleanup_old_images(image_type)

    def _cleanup_old_images(self, image_type):
        """Deletes older images, keeping only the latest MAX_IMAGES."""
        images = sorted([f for f in os.listdir(TMP_DIR) if f.startswith(image_type)], reverse=True)

        if len(images) > MAX_IMAGES:
            for old_image in images[MAX_IMAGES:]:
                os.remove(os.path.join(TMP_DIR, old_image))
                logger.info(f"Deleted old {image_type} image: {old_image}")

    def clear_display(self):
        """Clears the ePaper display."""
        logger.info("Clearing display.")
        self.epd.Clear()

    def sleep(self):
        """Puts the display into sleep mode to save power."""
        logger.info("Putting display into sleep mode.")
        self.epd.sleep()
