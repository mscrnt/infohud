################################################################################
# FILE: infoHUD.py
# DESCRIPTION: Main script to manage ePaper display updates.
# AUTHOR: MSCRNT LLC
#
# THIS CODE IS PROPRIETARY PROPERTY OF MSCRNT LLC.
################################################################################

import time
import logging
import threading
import os
import json
from dotenv import load_dotenv
from display_manager import DisplayManager
from stock_ticker import fetch_stock_data
from news_fetcher import fetch_news
from image_fetcher import ImageFetcher
from image_generator import generate_stock_image, generate_news_image, generate_weather_image
import weather_fetcher

# Load environment variables from .env file
load_dotenv()

# Configure logging
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, "infoHUD.log")

logger = logging.getLogger("infoHUD")
logger.setLevel(logging.INFO)
handler = logging.handlers.TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=7, utc=True)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Read enabled features from .env
ENABLE_IMAGES = os.getenv("ENABLE_IMAGES", "True").lower() == "true"
ENABLE_STOCKS = os.getenv("ENABLE_STOCKS", "True").lower() == "true"
ENABLE_NEWS = os.getenv("ENABLE_NEWS", "True").lower() == "true"
ENABLE_WEATHER = os.getenv("ENABLE_WEATHER", "True").lower() == "true"

# Read location from .env
LOCATION = os.getenv("LOCATION", "Irvine, CA")

# Read display times from .env (fallback to defaults if not set)
IMAGE_DISPLAY_TIME = int(os.getenv("IMAGE_DISPLAY_TIME", 60))  # Seconds
STOCK_DISPLAY_TIME = int(os.getenv("STOCK_DISPLAY_TIME", 30))
NEWS_DISPLAY_TIME = int(os.getenv("NEWS_DISPLAY_TIME", 30))
WEATHER_DISPLAY_TIME = int(os.getenv("WEATHER_DISPLAY_TIME", 20))  # ✅ New for weather

# Initialize components
display_manager = DisplayManager()
image_fetcher = ImageFetcher()

def fetch_and_prepare_content(mode):
    """Fetches content and prepares it for display."""
    logger.info(f"Fetching and preparing content: {mode}")

    if mode == "stock" and ENABLE_STOCKS:
        stock_data = fetch_stock_data()
        if stock_data:
            stock_image = generate_stock_image(stock_data)
            if stock_image:
                return stock_image, "stock"

    elif mode == "news" and ENABLE_NEWS:
        news_data = fetch_news()
        if news_data:
            logger.debug(f"News data sent to image generator:\n{json.dumps(news_data, indent=2)}")
            news_image = generate_news_image(news_data)
            if news_image:
                return news_image, "news"

    elif mode == "image" and ENABLE_IMAGES:
        raw_image = image_fetcher.fetch_next_image()
        if raw_image:
            return raw_image, "image"

    elif mode == "weather" and ENABLE_WEATHER:
        weather_data = weather_fetcher.get_weather(LOCATION)  # ✅ Fetch latest weather
        if weather_data:
            weather_image = generate_weather_image(weather_data)  # ✅ Generate forecast image
            if weather_image:
                return weather_image, "weather", weather_data  # ✅ Pass weather data

    logger.warning(f"No content available for {mode}.")
    return None, None  # Return only two values if not weather mode

def main_loop():
    """Main loop to cycle through different display modes."""
    display_modes = []
    if ENABLE_IMAGES:
        display_modes.append("image")
    if ENABLE_STOCKS:
        display_modes.append("stock")
    if ENABLE_NEWS:
        display_modes.append("news")
    if ENABLE_WEATHER:
        display_modes.append("weather")

    if not display_modes:
        logger.error("No display modes enabled! Check .env settings.")
        return

    current_mode_index = 0
    weather_data = weather_fetcher.get_weather(LOCATION)  # ✅ Fetch initial weather data

    while True:
        current_mode = display_modes[current_mode_index]
        logger.info(f"Displaying: {current_mode}")

        # ✅ Properly handle cases where weather data is returned
        result = fetch_and_prepare_content(current_mode)

        if len(result) == 3:  # Weather data included
            content, content_type, weather_data = result
        else:  # Regular content
            content, content_type = result
            # Preserve the last fetched weather data
            weather_data = weather_data if ENABLE_WEATHER else None  

        # ✅ Pass the weather data to display_manager for the header
        display_manager.display_image(content, content_type, weather_data)

        # Determine sleep time based on current mode
        sleep_time = {
            "image": IMAGE_DISPLAY_TIME,
            "stock": STOCK_DISPLAY_TIME,
            "news": NEWS_DISPLAY_TIME,
            "weather": WEATHER_DISPLAY_TIME
        }.get(current_mode, 10)  # Default to 10s if mode is unknown

        # Cycle to the next mode
        current_mode_index = (current_mode_index + 1) % len(display_modes)

        # Wait before switching to the next mode
        time.sleep(sleep_time)

if __name__ == "__main__":
    logger.info("Starting infoHUD...")
    main_thread = threading.Thread(target=main_loop, daemon=True)
    main_thread.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down infoHUD...")
