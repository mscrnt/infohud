################################################################################
# FILE: image_generator.py
# DESCRIPTION: Generates images for stock ticker and news headlines.
# AUTHOR: MSCRNT LLC.
#
# THIS CODE IS PROPRIETARY PROPERTY OF MSCRNT LLC.
################################################################################

import os
import time
import logging
import logging.handlers
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import cairosvg

# Configure logging
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, "infoHUD.log")

logger = logging.getLogger("image_generator")
logger.setLevel(logging.DEBUG)
handler = logging.handlers.TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=7, utc=True)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Display settings (600x400 for ePaper screen)
DISPLAY_WIDTH = 600
DISPLAY_HEIGHT = 400
IMG_WIDTH = 600
IMG_HEIGHT = 338
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_SIZE = 26  # Larger font size for readability
TMP_DIR = "./tmp/generated"
MAX_IMAGES = 10  # Keep only the latest 10 images of each type
ICON_SIZE = 40
ICON_PADDING = 10
ICON_DIR = "./assets/icons/"


# Ensure the generated image directory exists
os.makedirs(TMP_DIR, exist_ok=True)

def cleanup_old_images(image_type):
    """Deletes older images, keeping only the latest MAX_IMAGES."""
    images = sorted([f for f in os.listdir(TMP_DIR) if f.startswith(image_type)], reverse=True)
    
    if len(images) > MAX_IMAGES:
        for old_image in images[MAX_IMAGES:]:
            os.remove(os.path.join(TMP_DIR, old_image))
            logger.info(f"Deleted old {image_type} image: {old_image}")

def convert_to_6color(image):
    """Converts an image to the 6-color palette for Waveshare ePaper display."""
    logger.info("Converting image to 6-color mode.")

    # Define the 6-color palette
    pal_image = Image.new("P", (1, 1))
    pal_image.putpalette([
        0, 0, 0,       # BLACK
        255, 255, 255, # WHITE
        255, 255, 0,   # YELLOW
        255, 0, 0,     # RED
        0, 0, 255,     # BLUE
        0, 255, 0      # GREEN
    ] + [0, 0, 0] * 250)  # Fill rest of the palette with black

    # Convert the image to the limited 6-color palette
    converted_image = image.convert("RGB").quantize(palette=pal_image)

    logger.info("Image successfully converted to 6-color mode.")
    return converted_image

def save_image(image, image_type):
    """Converts image to 6-color mode, saves it, and cleans up old images."""
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    image_path = os.path.join(TMP_DIR, f"{image_type}_{timestamp}.png")

    # Convert the image before saving
    image = convert_to_6color(image)

    image.save(image_path)
    logger.info(f"{image_type.capitalize()} image saved: {image_path}")

    cleanup_old_images(image_type)
    return image  # ✅ Return properly formatted image

def fit_text_to_width(text, max_width, font_path, max_font_size):
    """Dynamically adjusts font size to fit text within a given width."""
    font_size = max_font_size
    font = ImageFont.truetype(font_path, font_size)
    while font.getsize(text)[0] > max_width and font_size > 10:
        font_size -= 1
        font = ImageFont.truetype(font_path, font_size)
    return text, font

def fit_text_to_area(text, max_width, max_height, font_path, max_font_size):
    """Dynamically adjusts font size to fit text within a given height."""
    font_size = max_font_size
    font = ImageFont.truetype(font_path, font_size)
    lines = []
    words = text.split()

    while font_size > 10:
        temp_lines = []
        line = ""
        for word in words:
            test_line = f"{line} {word}".strip()
            if font.getsize(test_line)[0] <= max_width:
                line = test_line
            else:
                temp_lines.append(line)
                line = word
        temp_lines.append(line)

        if sum(font.getsize(line)[1] for line in temp_lines) <= max_height:
            lines = temp_lines
            break

        font_size -= 1
        font = ImageFont.truetype(font_path, font_size)

    return "\n".join(lines), font

def _load_svg_icon(icon_name):
    """Loads an SVG file and converts it to a PIL image."""
    icon_path = os.path.join(ICON_DIR, icon_name)
    if os.path.exists(icon_path):
        try:
            png_bytes = cairosvg.svg2png(url=icon_path, output_width=ICON_SIZE, output_height=ICON_SIZE)
            return Image.open(BytesIO(png_bytes)).convert("RGBA")
        except Exception as e:
            logger.error(f"❌ Failed to load SVG icon {icon_name}: {e}")
    return None  # Return None if icon is missing

def generate_stock_image(stock_data):
    """Generates a properly formatted stock ticker image for a 600x338 display."""
    if not stock_data:
        logger.warning("No stock data available.")
        return None

    logger.info("Generating stock ticker image for 600x338 layout.")

    # **Define Dimensions**
    BACKGROUND_COLOR = (0, 0, 0)  # Black background

    # **Create Image**
    image = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

    # **Grid Layout for Stock Data**
    num_rows = 5
    num_columns = 2  # Two columns for better spacing
    padding = 20
    column_width = (IMG_WIDTH - (padding * (num_columns + 1))) // num_columns
    row_height = (IMG_HEIGHT - (padding * (num_rows + 1))) // num_rows

    # **Draw Stock Data in Columns**
    for index, stock in enumerate(stock_data[:10]):  # Limit to 10 stocks
        col = index % num_columns
        row = index // num_columns

        if row >= num_rows:
            break  # Prevents overflow

        x_position = padding + col * (column_width + padding)
        y_position = padding + row * (row_height + padding)

        # **Stock Symbol**
        draw.text((x_position, y_position), stock["symbol"], font=font, fill=(255, 255, 255))  # White text

        # **Current Price**
        price_text = f"{stock['current_price']:.2f}"
        price_color = (0, 255, 0) if stock["change"] > 0 else (255, 0, 0)  # Green for gain, Red for loss
        draw.text((x_position + 150, y_position), price_text, font=font, fill=price_color)

        # **Change in Value (Only if Non-Zero)**
        if stock["change"] != 0.00:
            change_text = f"{stock['change']:.2f}"
            draw.text((x_position + 250, y_position), change_text, font=font, fill=(255, 255, 255))

    logger.info("Stock ticker image generated successfully.")

    return save_image(image, "stock")  # ✅ Save and return the properly formatted image


def generate_news_image(news_data):
    """Generates a news image with a large centered headline, smaller image below, and a summary filling space."""
    if not news_data:
        logger.warning("No news article available.")
        return None

    logger.info("Generating news image for ePaper display.")

    # Create blank image with a dark background
    image = Image.new("RGB", (DISPLAY_WIDTH, DISPLAY_HEIGHT), (0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Font settings
    headline_font_size = FONT_SIZE * 2  # Adjusted for better balance
    headline_font = ImageFont.truetype(FONT_PATH, headline_font_size)
    summary_font = ImageFont.truetype(FONT_PATH, FONT_SIZE - 4)

    # Layout configuration
    padding = 20
    image_size = (250, 150)  # Slightly larger image size
    text_x_start = padding + image_size[0] + 15  # More padding for text

    # **Step 1: Draw the Headline (Centered at the Top)**
    headline = news_data["title"]
    fitted_headline, headline_font = fit_text_to_width(headline, DISPLAY_WIDTH - 2 * padding, FONT_PATH, headline_font_size)
    headline_width, headline_height = draw.textsize(fitted_headline, font=headline_font)
    headline_x = (DISPLAY_WIDTH - headline_width) // 2  # Center horizontally

    draw.text((headline_x, padding), fitted_headline, font=headline_font, fill=(255, 255, 255))

    # **Step 2: Download and Display the Image (Left-Aligned)**
    image_y_position = padding + headline_height + 10  # Place image below headline
    if news_data.get("thumbnail_url"):
        try:
            response = requests.get(news_data["thumbnail_url"], timeout=5)
            response.raise_for_status()
            thumbnail = Image.open(BytesIO(response.content)).convert("RGB")
            thumbnail = thumbnail.resize(image_size, Image.LANCZOS)
            image.paste(thumbnail, (padding, image_y_position))  # Left-aligned
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to fetch news thumbnail: {e}")

    # **Step 3: Fit Summary to Available Space (Right of Image)**
    summary_x_start = padding + image_size[0] + 20
    summary_y_start = image_y_position  # Align with the image

    # Available width and height for the summary text
    max_summary_width = DISPLAY_WIDTH - summary_x_start - padding
    max_summary_height = DISPLAY_HEIGHT - image_y_position - padding

    fitted_summary, summary_font = fit_text_to_area(news_data["summary"], max_summary_width, max_summary_height, FONT_PATH, FONT_SIZE - 6)

    # Draw summary in available space
    draw.multiline_text((summary_x_start, summary_y_start), fitted_summary, font=summary_font, fill=(200, 200, 200))

    # **Log the final text being displayed**
    logger.info(f"Final headline in image: {fitted_headline}")
    logger.info(f"Final summary in image: {fitted_summary}")

    logger.info("News image generated successfully.")

    return save_image(image, "news")

def generate_weather_image(weather_data):
    """Generates a 3-day weather forecast image for ePaper display using color SVG icons."""
    if "forecast" not in weather_data or len(weather_data["forecast"]) < 3:
        logger.warning("⚠️ Insufficient forecast data to generate weather image.")
        return None

    # **Dimensions for display_manager (600x338)**
    SKY_BLUE = (135, 206, 235)  # ✅ Sky Blue for column backgrounds

    # **Moon Phase SVG Mapping**
    moon_phase_map = {
        "FIRST_QUARTER": "first-quarter.svg",
        "FULL_MOON": "full-moon.svg",
        "LAST_QUARTER": "last-quarter.svg",
        "NEW_MOON": "new-moon.svg",
        "WANING_CRESCENT": "waning-crescent.svg",
        "WANING_GIBBOUS": "waning-gibbous.svg",
        "WAXING_CRESCENT": "waxing-crescent.svg",
        "WAXING_GIBBOUS": "waxing-gibbous.svg"
    }

    # ✅ Use RGB Mode for Color Support
    image = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), (255, 255, 255))  # ✅ White background
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
        small_font = ImageFont.truetype(FONT_PATH, FONT_SIZE - 4)
        moon_font = ImageFont.truetype(FONT_PATH, int(FONT_SIZE // 1.75))
        day_font = ImageFont.truetype(FONT_PATH, int(FONT_SIZE * 1.10))

        # **Title (Properly Centered, Black Color)**
        title_text = "3-Day Forecast"
        title_bbox = draw.textbbox((0, 0), title_text, font=font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(((IMG_WIDTH - title_width) // 2, 10), title_text, font=font, fill=(0, 0, 0))  # ✅ Black Text

        # **Updated Column Width & Padding**
        num_columns = 3
        col_width = (IMG_WIDTH - 80) // num_columns
        col_spacing = 20
        row_spacing = 30

        # ✅ Adjust Start X to Center the Table
        total_table_width = (col_width * num_columns) + (col_spacing * (num_columns - 1))
        table_start_x = (IMG_WIDTH - total_table_width) // 2  # ✅ Center table horizontally

        for i, day in enumerate(weather_data["forecast"][:3]):
            x_pos = table_start_x + (i * (col_width + col_spacing))  # ✅ Evenly distribute columns
            column_center = x_pos + (col_width // 2)

            # **Colored Borders for Each Column**
            border_color = (0, 0, 0)
            draw.rectangle([x_pos, 40, x_pos + col_width, IMG_HEIGHT - 10], outline=border_color, width=2)
            draw.rectangle([x_pos, 40, x_pos + col_width, IMG_HEIGHT - 10], fill=SKY_BLUE)  # ✅ Sky Blue Background for Columns

            # **Day Name (Properly Centered)**
            day_text = day.get("date", "Unknown")
            day_bbox = draw.textbbox((0, 0), day_text, font=day_font)
            day_width, day_height = day_bbox[2] - day_bbox[0], day_bbox[3] - day_bbox[1]
            draw.text((column_center - (day_width // 2), 50), day_text, font=day_font, fill=(0, 0, 0))

            # **High/Low Temps (Properly Centered Below Date)**
            high_temp_text = f"H: {day.get('high_temp', 'N/A')}°F"
            low_temp_text = f"L: {day.get('low_temp', 'N/A')}°F"

            temp_bbox = draw.textbbox((0, 0), high_temp_text, font=small_font)
            temp_width = temp_bbox[2] - temp_bbox[0]
            draw.text((column_center - (temp_width // 2), 90), high_temp_text, font=small_font, fill=(255, 0, 0))
            draw.text((column_center - (temp_width // 2), 120), low_temp_text, font=small_font, fill=(0, 0, 255))

            # **Sunrise Icon & Text (Aligned Left, Different Font Color)**
            sunrise_icon = _load_svg_icon("sunrise.svg")
            if sunrise_icon:
                sunrise_x = x_pos + 10
                image.paste(sunrise_icon, (sunrise_x, 160), sunrise_icon)
            draw.text((sunrise_x + ICON_SIZE + 5, 170), day.get("sunrise", "N/A"), font=small_font, fill=(255, 69, 0))  # 🔶 Darker Orange Sunrise

            # **Sunset Icon & Text (Aligned Left, Different Font Color)**
            sunset_icon = _load_svg_icon("sunset.svg")
            if sunset_icon:
                sunset_x = x_pos + 10
                image.paste(sunset_icon, (sunset_x, 200), sunset_icon)
            draw.text((sunset_x + ICON_SIZE + 5, 210), day.get("sunset", "N/A"), font=small_font, fill=(102, 51, 153))  # ✅ Dark Orchid for Sunset

            # **Moon Phase Icon (Now Below Sunset)**
            moon_phase_name = day.get("moon_phase", "").split()[0].upper().replace(" ", "_")
            moon_phase_icon = _load_svg_icon(moon_phase_map.get(moon_phase_name, "unknown.svg"))
            if moon_phase_icon:
                moon_x_pos = column_center - (ICON_SIZE // 2)
                image.paste(moon_phase_icon, (moon_x_pos, 240), moon_phase_icon)

            # **Moon Phase Name (Below Icon, 3x Smaller)**
            moon_phase_text = day.get("moon_phase", "Unknown").replace("_", " ").title()
            moon_text_bbox = draw.textbbox((0, 0), moon_phase_text, font=moon_font)
            moon_text_width = moon_text_bbox[2] - moon_text_bbox[0]
            draw.text((column_center - (moon_text_width // 2), 290), moon_phase_text, font=moon_font, fill=(0, 0, 0))

        return save_image(image, "weather")

    except Exception as e:
        logger.error(f"❌ Failed to generate weather image: {e}")
        return None
