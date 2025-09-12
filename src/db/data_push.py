import pandas as pd
from typing import List, Dict, Any
import aiohttp
import os

from v3.data_models.live_feed import LiveFeed
from typing import List

REPLACE_INSTRUMENT_KEY_WITH_TRADE_SYMBOL = os.getenv("REPLACE_INSTRUMENT_KEY_WITH_TRADE_SYMBOL", "False").lower() == "true"

def create_influx_query(df: pd.DataFrame) -> str:
    """
    Creates InfluxDB line protocol queries from a pandas DataFrame for data ingestion,
    conforming to a fixed InfluxDB schema.

    InfluxDB Schema:
    ----------------
    Measurement: Derived from the 'interval' column in the DataFrame, representing the 
                 granularity of the stock data (e.g., '1m', '5m', '1h').
    Tags:        Consists of a single tag:
                 - 'feed_name': Identifier for the data source or feed.
    Fields:      Includes the following numerical stock data points:
                 - 'Open': Opening price of the stock for the interval.
                 - 'High': Highest price of the stock during the interval.
                 - 'Low': Lowest price of the stock during the interval.
                 - 'Close': Closing price of the stock at the end of the interval.
                 - 'Volume': Number of shares traded during the interval.
    Timestamp:   Denotes the exact moment the data was recorded, provided in UNIX timestamp format,
                 ensuring each data point's temporal uniqueness.

    The line protocol format for each data point is as follows:
    <measurement>,<tag_key>=<tag_value> <field_key>=<field_value>,... <timestamp>

    Parameters:
    - df: pd.DataFrame
        The DataFrame containing stock market data to be converted into InfluxDB line protocol. 
        Expected columns: 'feed_name', 'interval', 'Open', 'High', 'Low', 'Close', 'Volume', 'ts'.

    Returns:
    - str
        A multiline string where each line represents a single data point in InfluxDB line protocol format.
        This string is ready for ingestion into InfluxDB under the specified schema.

    Example Usage:
        # Assuming 'df' is your DataFrame with the necessary columns
        queries = create_influx_query(df)
        print(queries)  # Prints the line protocol queries to be ingested into InfluxDB.
    """
    df["ts"] = (df['ts'].astype('int64')).astype(str)

    queries = []

    # Format feed name
    df["feed_name"] = df["feed_name"].str.replace(" ", "_")

    for _, row in df.iterrows():
        measurement = row['interval']
        tags = f"feed_name={row['feed_name']}"
        
        fields = ",".join(
            f"{key}={value}"
            for key, value in row[['Open', 'High', 'Low', 'Close', 'Volume']].items()
            if pd.notna(value)
        )
        timestamp = row["ts"]

        query = f"{measurement},{tags} {fields} {timestamp}"
        queries.append(query)

    return "\n".join(queries)


def transform_data(data_list: List[LiveFeed]) -> pd.DataFrame:
    """
    Transforms the given data into a pandas DataFrame.
    """
    rows = []
    # for data in data_list:
    #     for feed_name, feed_data in data['feeds'].items():
    #         for interval_data in feed_data['ff']['marketFF']['marketOHLC']['ohlc']:
    #             row = {
    #                 'feed_name': feed_name,  # Assuming feed name format is consistent
    #                 'interval': interval_data['interval'],
    #                 'Open': interval_data.get('open', None),
    #                 'High': interval_data.get('high', None),
    #                 'Low': interval_data.get('low', None),
    #                 'Close': interval_data.get('close', None),
    #                 'Volume': interval_data.get('volume', 0),  # Assuming volume might not be present
    #                 'ts': interval_data.get('ts')
    #             }
    #             rows.append(row)
    for data in data_list:
        for feed_name, feed_data in data.feeds.items():
            for interval_feed in feed_data.fullFeed.marketFF.marketOHLC.ohlc:
                row = {
                    'feed_name': feed_name,# if not REPLACE_INSTRUMENT_KEY_WITH_TRADE_SYMBOL else feed_data.fullFeed.get('trade_symbol', feed_name),
                    'interval': interval_feed.interval,
                    'Open': interval_feed.open,
                    'High': interval_feed.high,
                    'Low': interval_feed.low,
                    'Close': interval_feed.close,
                    'Volume': interval_feed.vol,
                    'ts': interval_feed.ts
                }
                rows.append(row)

    return pd.DataFrame(rows)


async def push_data_to_influxdb(influx_query: str,
                                influxdb_url: str,
                                org: str,
                                bucket_name: str,
                                token: str) -> None:
    """
    Asynchronously pushes data to InfluxDB using aiohttp, based on a pre-defined query.

    Parameters:
    - data (List[Dict[str, Any]]): Data to be pushed to InfluxDB, structured according to the schema expected by the query function.
    - influxdb_url (str): URL of the InfluxDB server.
    - org (str): Organization name for InfluxDB.
    - bucket_name (str): The name of the InfluxDB bucket where the data will be written.
    - token (str): Authentication token for InfluxDB.

    Raises:
    - aiohttp.ClientError: If the HTTP request fails.
    """

    # Prepare the headers for the request
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "text/plain",
    }

    # Construct the URL for the write API
    write_url = f"{influxdb_url}/api/v2/write?org={org}&bucket={bucket_name}&precision=ms"

    # Perform the asynchronous POST request to InfluxDB
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(write_url, headers=headers, data=influx_query) as response:
                response.raise_for_status()
                print("Data pushed to influxDB successfully.")
    except Exception as e:
        # txt = await response.text()
        print(f"Failed to push data :: Error occured : {e}")
        raise e

    return None

if __name__=="__main__":
    pass