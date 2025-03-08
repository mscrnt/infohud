################################################################################
# FILE: weather_fetcher.py
# DESCRIPTION: Fetches weather data in the format required by infoHUD.
# AUTHOR: MSCRNT LLC.
################################################################################

import os
import sys
import json
import logging
import logging.handlers
import asyncio
import python_weather
from datetime import datetime, timedelta

# Ensure Python can find lib/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../lib")))

# Configure logging
LOG_DIR = "logs"
TMP_DIR = "tmp"  # ✅ Store cache in ./tmp
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(TMP_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, "infoHUD.log")

logger = logging.getLogger("weather_fetcher")
logger.setLevel(logging.DEBUG)
handler = logging.handlers.TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=7, utc=True)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

CACHE_EXPIRY = timedelta(hours=1)  # Cache updates once per hour

def get_cache_file(location):
    """Generate a location-specific cache file name."""
    safe_location = location.replace(" ", "_").replace(",", "").lower()
    return os.path.join(TMP_DIR, f"weather_cache_{safe_location}.json")

async def fetch_weather(location):
    """Fetches and formats weather data for infoHUD."""
    try:
        logger.info(f"🌤️ Fetching weather for {location}...")
        async with python_weather.Client(unit=python_weather.IMPERIAL) as client:
            forecast = await client.get(location)

            if not forecast:
                logger.error(f"❌ API response for {location} is empty.")
                return None

            logger.debug(f"✅ Raw API response for {location}: {forecast}")

            # Extract current weather details
            current_temp = getattr(forecast, "temperature", "N/A")
            current_condition = getattr(forecast, "description", "Unknown")
            wind_speed = getattr(forecast, "wind_speed", "N/A")
            humidity = getattr(forecast, "humidity", "N/A")

            # ✅ Format weather data for infoHUD
            weather_data = {
                "current": {
                    "condition": current_condition,
                    "temperature": current_temp,
                    "wind_speed": wind_speed,
                    "humidity": humidity
                },
                "forecast": [],
                "timestamp": datetime.now().isoformat()
            }

            # ✅ Extract 3-day forecast without `kind`
            for daily in forecast.daily_forecasts[:3]:
                daily_forecast = {
                    "date": daily.date.strftime("%A") if hasattr(daily, "date") else "Unknown",
                    "high_temp": daily.highest_temperature,
                    "low_temp": daily.lowest_temperature,
                    "sunrise": daily.sunrise.strftime("%I:%M %p") if hasattr(daily, "sunrise") and daily.sunrise else "N/A",
                    "sunset": daily.sunset.strftime("%I:%M %p") if hasattr(daily, "sunset") and daily.sunset else "N/A",
                    "moon_phase": f"{daily.moon_phase.name if hasattr(daily, 'moon_phase') else 'Unknown'}",
                    "moon_illumination": daily.moon_illumination
                }
                weather_data["forecast"].append(daily_forecast)

            # Cache data
            cache_file = get_cache_file(location)
            with open(cache_file, "w") as f:
                json.dump(weather_data, f, indent=4)

            logger.info(f"✅ Weather data formatted successfully for infoHUD.")
            return weather_data
    except Exception as e:
        logger.warning(f"Failed to fetch weather for {location}: {e}")
        return None


def get_cached_weather(location):
    """Returns cached weather data if it's valid (less than 1 hour old)."""
    cache_file = get_cache_file(location)

    if not os.path.exists(cache_file):
        logger.warning(f"Weather cache file does not exist for {location}.")
        return None

    try:
        with open(cache_file, "r") as f:
            weather_data = json.load(f)

        if not weather_data or "timestamp" not in weather_data:
            logger.warning(f"Cache file for {location} is empty or corrupted.")
            return None

        last_update = datetime.fromisoformat(weather_data["timestamp"])
        if datetime.now() - last_update < CACHE_EXPIRY:
            logger.info(f"Using cached weather data for {location}.")
            return weather_data
        else:
            logger.info(f"Weather cache expired for {location}.")
            return None
    except Exception as e:
        logger.warning(f"⚠️ Failed to fetch weather for {location}: {e}")
        return None

def get_weather(location):
    """Returns weather data from cache or fetches new data if needed."""
    weather_data = get_cached_weather(location)
    if weather_data is None:
        logger.info(f"Fetching new weather data for {location}...")
        weather_data = asyncio.run(fetch_weather(location))

    if weather_data is None:
        logger.warning(f"Weather data retrieval failed for {location}. Returning default placeholder.")
        return {"current": {"condition": "Unavailable", "temperature": "N/A"}}

    return weather_data

def get_formatted_weather(location):
    """Returns a formatted string for display purposes (current conditions only)."""
    weather_data = get_weather(location)
    if weather_data and "current" in weather_data:
        current = weather_data["current"]
        return f"{current.get('condition', 'Unknown')} {current.get('temperature', 'N/A')}°F"
    return "Weather Unavailable"


if __name__ == "__main__":
    """Run this script to debug weather fetching."""
    test_location = "Irvine, CA 92618"
    print("Fetching weather for:", test_location)
    weather = get_weather(test_location)
    print(json.dumps(weather, indent=4))
