from datetime import datetime
import pandas as pd
import aiohttp
import requests
import gzip
import json
from io import BytesIO

UPSTOX_INSTRUMENTS_URL = "https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz"


def convert_datetime_to_influxdb_string(dt) -> str:
    """
    Converts a datetime object or a string parseable by pandas to a string
    formatted according to InfluxDB's required datetime format (ISO 8601 with a 'Z' suffix).

    Parameters:
    - dt (datetime or str): The datetime object or string to convert. If `dt` is a string,
      it should be in a format parseable by pandas.to_datetime().

    Returns:
    - str: A datetime string formatted for InfluxDB ('YYYY-MM-DDTHH:MM:SSZ').

    Raises:
    - ValueError: If `dt` is neither a datetime object nor a string that can be parsed into a datetime object.
    """
    try:
        if not isinstance(dt, datetime):
            dt = pd.to_datetime(dt)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Input must be a datetime object or a parseable datetime string, got {dt}: {e}")

    influxdb_format = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    return influxdb_format

async def is_influxdb_online(url: str) -> bool:
    health_check_url = f"{url}/health"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(health_check_url) as response:
                if response.status == 200:
                    return True
                else:
                    return False
        except aiohttp.ClientError:
            return False
        
def get_instruments_data() -> pd.DataFrame:
    # Download the compressed file
    response = requests.get(UPSTOX_INSTRUMENTS_URL)
    response.raise_for_status()

    # Decompress
    with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
        data = json.load(gz)
        
    return pd.DataFrame(data)