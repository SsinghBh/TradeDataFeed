import asyncio
import logging
import logging.handlers
from src.websocket_client import fetch_market_data
from src.db_ingestion import push_data_to_db, setup_database
from src.backed_up_data import push_failed_data
from src.data_transfer_intimation import monitor_data_transfer

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
    # Setup database
    await setup_database()

    # Initialize async queue for data storage
    q = asyncio.Queue(maxsize=1000)

    # Initialize the shared success event
    success_event = asyncio.Event()

    # Create tasks
    t1 = asyncio.create_task(fetch_market_data(q=q))
    t2 = asyncio.create_task(push_data_to_db(data_queue=q, success_event=success_event))
    t3 = asyncio.create_task(push_failed_data(success_event=success_event))
    t4 = asyncio.create_task(monitor_data_transfer(success_event=success_event))

    await asyncio.gather(t1, t2, t3, t4)

if __name__ == "__main__":
    asyncio.run(main())
