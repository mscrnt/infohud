################################################################################
# FILE: news_fetcher.py
# DESCRIPTION: Fetches and formats the top news article for the ePaper display.
# AUTHOR: MSCRNT LLC
#
# THIS CODE IS PROPRIETARY PROPERTY OF MSCRNT LLC.
################################################################################

import feedparser
import requests
from bs4 import BeautifulSoup  # Ensure this is installed: pip install beautifulsoup4
import logging
import logging.handlers
import json
import os

# Configure logging (consistent with infoHUD.py)
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, "infoHUD.log")

logger = logging.getLogger("news_fetcher")
logger.setLevel(logging.INFO)
handler = logging.handlers.TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=7, utc=True)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# News RSS Feed
RSS_FEED_URL = "https://feedx.net/rss/ap.xml"
OLLAMA_SERVER_URL = "http://192.168.69.197:11434/api/generate"  # Ollama API endpoint
OLLAMA_TIMEOUT = 10  # Increased timeout to 10 seconds

def fetch_news():
    """Fetch the top news article from the RSS feed and process it for display."""
    logger.info("Fetching latest news article from RSS feed.")

    try:
        feed = feedparser.parse(RSS_FEED_URL)

        if not feed.entries:
            logger.error("No news articles found in RSS feed.")
            return None

        entry = feed.entries[0]  # Get the first/top article
        title = entry.title.strip()
        summary = extract_rss_summary(entry)  # Extract full summary
        image_url = extract_image_url(entry.description)  # Extract image URL

        logger.debug(f"Extracted raw summary: {summary}")

        if not summary or len(summary.split()) < 5:
            logger.error("No valid news content extracted. Aborting fetch.")
            return None

        # Send the **original summary** to Ollama for refinement
        shortened_summary = summarize_text(summary)  

        news_data = {
            "title": title,
            "summary": shortened_summary,
            "thumbnail_url": image_url
        }

        logger.info(f"News article fetched: {title}")
        logger.debug(f"Final processed news data: {news_data}")

        return news_data

    except Exception as e:
        logger.error(f"Failed to fetch news: {e}")
        return None

def extract_rss_summary(entry):
    """Extracts the original summary from the RSS feed entry."""
    try:
        if "description" in entry:
            soup = BeautifulSoup(entry.description, "html.parser")

            # Extract all paragraphs exactly as written
            paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]

            if paragraphs:
                original_summary = "\n\n".join(paragraphs)  # Preserve full structure
                logger.debug(f"Extracted original summary from RSS: {original_summary}")
                return original_summary

    except Exception as e:
        logger.error(f"Error extracting summary: {e}")

    return ""  # Fallback to empty string

def extract_image_url(html):
    """Extracts the first image URL from an HTML string."""
    try:
        soup = BeautifulSoup(html, "html.parser")
        img_tag = soup.find("img")
        image_url = img_tag["src"] if img_tag else None

        logger.debug(f"Extracted image URL: {image_url}")
        return image_url

    except Exception as e:
        logger.error(f"Error extracting image URL: {e}")
        return None

def summarize_text(text):
    """Uses Deepseek-R1 14B on Ollama to generate a concise summary, with a fallback to the original text."""
    logger.info("Summarizing news article with Ollama.")

    try:
        response = requests.post(
            OLLAMA_SERVER_URL,
            json={"model": "deepseek-r1:14b", "prompt": f"Summarize this news article in one sentence:\n{text}"},
            timeout=OLLAMA_TIMEOUT
        )

        logger.debug(f"Ollama raw response: {response.text}")

        if response.status_code == 200:
            try:
                response_data = json.loads(response.text.strip().split("\n")[-1])  # Extract last JSON object
                ollama_summary = response_data.get("response", "").strip()

                # Validate the response to prevent nonsense summaries
                if not ollama_summary or len(ollama_summary.split()) < 5 or "I need to summarize" in ollama_summary:
                    logger.warning("Ollama returned an invalid response. Falling back to extracted summary.")
                    logger.info(f"Final summary used: {text}")
                    return text  # Fallback to original summary

                logger.info(f"Final summary used: {ollama_summary}")
                return ollama_summary

            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error from Ollama: {e}")
                logger.info(f"Final summary used: {text}")
                return text  # Fallback to original summary

        else:
            logger.warning(f"Ollama returned an error: {response.status_code} {response.text}")
            logger.info(f"Final summary used: {text}")
            return text  # Fallback to original summary

    except Exception as e:
        logger.error(f"Failed to summarize text: {e}")
        logger.info(f"Final summary used: {text}")
        return text  # Fallback to original summary
