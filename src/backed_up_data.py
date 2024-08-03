import aiosqlite
import asyncio
from datetime import datetime
import logging
from . import data_push
from .utils import is_influxdb_online
from .db_ingestion import transform_data, create_influx_query
from .db_ingestion import INFLUX_BUCKET_NAME, INFLUX_DB_ORG, INFLUX_DB_TOKEN, INFLUX_DB_URL, DB_LOCATION

WAITING_TIME_THRESHOLD = 10

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def vacuum_database(database_path=DB_LOCATION):
    async with aiosqlite.connect(database_path) as conn:
        try:
            await conn.execute("VACUUM")
            await conn.commit()  # Ensure changes are committed
            logger.info("Database vacuumed successfully.")
        except aiosqlite.Error as e:
            logger.error(f"An error occurred: {e}")

async def push_failed_data(success_event: asyncio.Event, url: str = INFLUX_DB_URL, org: str = INFLUX_DB_ORG,
                           bucket: str = INFLUX_BUCKET_NAME, token: str = INFLUX_DB_TOKEN):
    """
    Continuously processes documents from the SQLite database.
    For each document, applies a function and deletes the document upon successful completion.
    """
    ref_time = datetime.now()
    logger.info(f"Starting document processing at {ref_time}")

    while True:
        # Check if InfluxDB is online
        if await is_influxdb_online(url):
            logger.info("InfluxDB is online. Proceeding with data fetching and pushing.")
            
            async with aiosqlite.connect(DB_LOCATION) as db:
                logger.info("Attempting asynchronously accessing SQLite DB")
                async with db.execute('SELECT id, query FROM data') as cursor:
                    docs = await cursor.fetchall()

                logger.info(f"Starting for loop for queries")
                for doc_id, query in docs:
                    try:
                        logger.info(f"Waiting for data push")
                        await data_push.push_data_to_influxdb(
                            influx_query=query,
                            influxdb_url=url,
                            org=org,
                            bucket_name=bucket,
                            token=token
                        )

                        # Delete
                        logger.info(f"Deleting data from SQLite for document ID {doc_id}")
                        await db.execute('DELETE FROM data WHERE id = ?', (doc_id,))
                        await db.commit()

                        success_event.set() # Set the event flag
                        logger.info(f"Document {doc_id} successfully processed and deleted.")
                    except Exception as e:
                        logger.error(f"Unsuccessful processing for doc_id {doc_id}: {e}")
                        continue  # Continue with the next document
                
                # Release space
                await vacuum_database()
        else:
            logger.warning("InfluxDB is offline. Retrying after interval.")
        
        # Wait before the next iteration
        await asyncio.sleep(WAITING_TIME_THRESHOLD)