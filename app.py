import asyncio
import logging
import logging.handlers
from dotenv import load_dotenv
import os

load_dotenv()  # This will load variables from a .env file into the environment

MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", 10_000))
DATA_FEED_UPDATE_URL = os.getenv("DATA_FEED_UPDATE_URL", None)

# Ensure the logs directory exists
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configure logging
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = logging.handlers.RotatingFileHandler('logs/app.log', maxBytes=50*1024*1024, backupCount=2)  # 50 MB limit per file
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(log_formatter)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(log_formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

async def main():
    # Import async coroutines
    from src.websocket_client import fetch_market_data
    from src.db_ingestion import push_data_to_db, setup_database
    from src.backed_up_data import push_failed_data
    from src.data_transfer_intimation import monitor_data_transfer

    # Ensure the sqlite db directory exists
    if not os.path.exists('sqlite_db'):
        os.makedirs('sqlite_db')

    # Setup database
    await setup_database()

    # Initialize async queue for data storage
    q = asyncio.Queue(maxsize=MAX_QUEUE_SIZE)

    # Initialize the shared success event
    success_event = asyncio.Event()

    # Create tasks
    tasks = [
        asyncio.create_task(fetch_market_data(q=q)),
        asyncio.create_task(push_data_to_db(data_queue=q, success_event=success_event)),
        asyncio.create_task(push_failed_data(success_event=success_event))
    ]

    # Conditionally add the monitor_data_transfer task to send data update notification
    if DATA_FEED_UPDATE_URL:
        tasks.append(asyncio.create_task(monitor_data_transfer(success_event=success_event)))

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
