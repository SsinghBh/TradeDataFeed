import asyncio
import pandas as pd
from datetime import datetime, timedelta
import aiosqlite
import os

# Importing from v3
# from . import data_push  # InfluxDB utility
from .data_push import (
    create_influx_query, 
    push_data_to_influxdb, 
    transform_data
)

import logging

logger = logging.getLogger(__name__)

INFLUX_BUCKET_NAME = os.getenv("INFLUX_BUCKET_NAME", None)
AVAILABLE_INTERVALS = ["I1", "I30", "1d"]
INFLUX_DB_ORG = os.getenv("INFLUX_DB_ORG", None)
INFLUX_DB_URL = os.getenv("INFLUX_DB_URL", None)
INFLUX_DB_TOKEN = os.getenv("INFLUX_DB_TOKEN", None)
DB_LOCATION = os.path.join("sqlite_db", "failed_to_push_data.sqlite")
MAX_DOCS_LIMIT = 100_000_000
LAST_PUSH_TIME_THRESHOLD = timedelta(seconds=30)

if (INFLUX_BUCKET_NAME is None) or (INFLUX_DB_ORG is None) or (INFLUX_DB_URL is None) or (INFLUX_DB_TOKEN is None):
    print(f"bucket : {INFLUX_BUCKET_NAME} :: org : {INFLUX_DB_ORG} :: URL : {INFLUX_DB_URL} :: token : {INFLUX_DB_TOKEN}")
    raise Exception(f"Incomplete influxDB credentials. Terminating process...")

async def setup_database(db_path: str = DB_LOCATION):
    """
    Sets up the SQLite database by ensuring the required table exists.
    
    Parameters:
    - db_path: str: The path to the SQLite database file.
    
    Returns:
    - None
    """
    async with aiosqlite.connect(db_path) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT
            )
        ''')
        await db.commit()
        logger.info(f"Database setup complete. Table 'data' is ready for use.")


async def save_to_db(data: str, db_path: str = DB_LOCATION, max_docs_limit: int = MAX_DOCS_LIMIT) -> None:
    """
    Asynchronously saves data to a SQLite database, respecting a maximum documents limit.
    If the database already contains the maximum number of documents, it logs an error and discards the new data.
    
    Parameters:
    - data: str: A string containing the query data.
    - db_path: str: The path to the SQLite database file.
    - max_docs_limit: int: The maximum number of rows allowed in the database.
    
    Returns:
    - None
    """
    async with aiosqlite.connect(db_path) as db:

        async with db.execute('SELECT COUNT(*) FROM data') as cursor:
            (existing_docs_count,) = await cursor.fetchone()

        if existing_docs_count >= max_docs_limit:
            logger.error(f"Error: Maximum row limit of {max_docs_limit} reached. Discarding data.")
            return None

        await db.execute('INSERT INTO data (query) VALUES (?)', (data,))
        await db.commit()

        logger.debug(f"Successfully saved data to {db_path}. Current row count: {existing_docs_count + 1}.")
        return None

async def push_data_to_db(data_queue: asyncio.Queue, success_event: asyncio.Event, threshold: int=10, url: str=INFLUX_DB_URL, 
                          org: str=INFLUX_DB_ORG, bucket: str=INFLUX_BUCKET_NAME, token: str=INFLUX_DB_TOKEN) -> None:
    """
    Processes data from the queue and attempts to push it to InfluxDB. If pushing to InfluxDB fails, 
    the data is saved locally for later processing.

    Parameters:
    -----------
    data_queue : asyncio.Queue
        An asynchronous queue containing data to be pushed to InfluxDB.

    success_event : asyncio.Event
        An event that is set when data is successfully pushed to InfluxDB. 
        This can be used to signal other coroutines that the operation was successful.

    threshold : int, optional
        The minimum number of items in the queue required to trigger a push to InfluxDB. 
        Default is 10.

    url : str, optional
        The URL of the InfluxDB instance. Default is set to the global `INFLUX_DB_URL`.

    org : str, optional
        The organization name in InfluxDB. Default is set to the global `INFLUX_DB_ORG`.

    bucket : str, optional
        The bucket name in InfluxDB where data should be stored. Default is set to the global `INFLUX_BUCKET_NAME`.

    token : str, optional
        The token for authenticating with InfluxDB. Default is set to the global `INFLUX_DB_TOKEN`.

    Returns:
    --------
    None
        This function does not return any value. It operates asynchronously, 
        pushing data to InfluxDB or saving it locally on failure.
    
    Behavior:
    ---------
    The function continuously monitors the `data_queue` in an infinite loop. 
    It checks whether the queue size exceeds the specified `threshold` or if a certain amount of time has 
    passed since the last data push. If either condition is met, it processes the data and attempts to 
    push it to InfluxDB. If the push operation fails, the data is saved locally for future processing. 
    The function also sets the `success_event` to signal successful data push operations.

    Logging:
    --------
    The function logs various debug and error messages, including the conditions for pushing data, 
    success or failure of the push operation, and other operational details.
    """
    logger.debug(f"Performing data push to DB.")
    time_ref = datetime.now()

    logger.info("Starting loop to push data")
    while True:  # Infinite loop to keep the coroutine alive
        mask1 = data_queue.qsize() > threshold  # data queue size is big enough
        mask2 = not data_queue.empty()  # data queue is not empty
        mask3 = datetime.now() - time_ref > LAST_PUSH_TIME_THRESHOLD  # Enough time passed since last push
        
        logger.debug(f"Calculated masks for data push :: mask1 : {mask1} :: mask2 : {mask2} :: mask3 : {mask3}")

        # Process if either enough time is passed or queue size is big enough
        if mask1 | ((mask2) & (mask3)):
            time_ref = datetime.now()
            logger.debug(f"Time reference changed : {time_ref}")
            
            # Gather data to process list from queue
            data_to_process = []
            
            while not data_queue.empty():
                data_to_process.append(await data_queue.get())
            logger.debug("Data to process list gathered")

            df = transform_data(data_to_process)  # Assuming data_to_process format

            query = create_influx_query(df)

            # Mock send data logic
            try:
                await push_data_to_influxdb(
                    influx_query=query,
                    influxdb_url=url,
                    org=org,
                    bucket_name=bucket,
                    token=token
                )
                logger.debug("Data successfully pushed to DB.")

                success_event.set() # Set the event flag
            except Exception as e:
                logger.error(f"Failed to push data to InfluxDB: {e}. Saving to DB.")
                await save_to_db(query)
        else:
            logger.debug("Sleeping for 1 second")
            await asyncio.sleep(1)  # Sleep for a bit if below threshold