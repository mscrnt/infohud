################################################################################
# FILE: stock_ticker.py
# DESCRIPTION: Fetches stock ticker data and returns it in a display-agnostic format.
# AUTHOR: MSCRNT LLC.
#
# THIS CODE IS PROPRIETARY PROPERTY OF MSCRNT LLC.
################################################################################

import os
import logging
import logging.handlers
from stockdex import Ticker

# Configure logging with single daily log file
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, "infoHUD.log")

logger = logging.getLogger("stock_ticker")
logger.setLevel(logging.INFO)
handler = logging.handlers.TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=7, utc=True)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# List of stocks to track (configurable)
STOCK_SYMBOLS = ["RDDT", "TSLA", "MSFT", "NVDA", "TSM", "AMZN", "METV", "META", "CHPT", "TLRY"]  # Modify as needed

def fetch_stock_data():
    """Fetch stock price data and return in a structured format."""
    stock_info = []
    try:
        for symbol in STOCK_SYMBOLS:
            ticker = Ticker(ticker=symbol)
            logger.info(f"Fetching stock data for: {symbol}")

            # Fetch stock price and previous close
            price_data = ticker.yahoo_api_price(range='1d', dataGranularity='1d')

            # Log raw response for debugging
            logger.debug(f"Raw price data for {symbol}: {price_data}")

            # Ensure proper column casing
            price_data.columns = price_data.columns.str.lower()

            # Validate response
            if price_data is not None and not price_data.empty and "close" in price_data.columns:
                current_price = price_data.iloc[-1]["close"]  # Get the latest closing price
                prev_close = price_data.iloc[-2]["close"] if len(price_data) > 1 else current_price

                # Calculate price change
                change = current_price - prev_close
                percent_change = (change / prev_close) * 100 if prev_close > 0 else 0

                # Determine up/down indicator
                direction = "▲" if change > 0 else "▼"

                stock_info.append({
                    "symbol": symbol,
                    "current_price": round(current_price, 2),
                    "change": round(change, 2),
                    "percent_change": round(percent_change, 2),
                    "direction": direction
                })

                logger.info(f"{symbol}: {current_price:.2f} ({direction} {change:.2f}, {percent_change:.2f}%)")
            else:
                logger.warning(f"No 'close' data found for {symbol}, data: {price_data}")
                stock_info.append({
                    "symbol": symbol,
                    "current_price": "No Data",
                    "change": 0,
                    "percent_change": 0,
                    "direction": ""
                })

        return stock_info

    except Exception as e:
        logger.error(f"Failed to fetch stock data: {e}")
        return []

if __name__ == "__main__":
    stock_data = fetch_stock_data()
    print(stock_data)  # Print structured output for debugging
