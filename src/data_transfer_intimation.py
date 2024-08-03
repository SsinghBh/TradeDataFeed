import asyncio
import logging
import json
import os
import aiohttp
import logging

logger = logging.getLogger(__name__)

SLEEP_TIME = int(os.getenv("NOTIFICATION_SLEEP_TIME", 60))
WAIT_TIME = int(os.getenv("NOTIFICATION_WAIT_TIME", 50))
DATA_FEED_UPDATE_URL = os.getenv("DATA_FEED_UPDATE_URL", None)

async def send_data_feed_update_notification():
    """
    Sends a notification to the trading bot informing that the data feed 
    has been successfully transferred to InfluxDB.

    Returns:
        bool: True if the notification was sent successfully, False otherwise.

    Exceptions Handled:
        aiohttp.ClientError: Handles client-related errors.
        asyncio.TimeoutError: Handles request timeout errors.
        Exception: Handles any unexpected errors.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(DATA_FEED_UPDATE_URL, json={"message": "Data feed has been successfully transferred to InfluxDB"}) as response:
                if response.status == 200:
                    logger.info("Successfully informed the trading bot about data feed update.")
                    return True
                else:
                    logger.error(f"Failed to inform the trading bot. Status code: {response.status}")
                    return False
    except aiohttp.ClientError as e:
        logger.error(f"Client error occurred: {e}")
        return False
    except asyncio.TimeoutError:
        logger.error("Request timed out.")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return False

async def monitor_data_transfer(success_event):
    """
    Monitors the data transfer process and sends a notification when the data feed
    has been successfully transferred to InfluxDB.

    Args:
        success_event (asyncio.Event): An event flag indicating the success of the data transfer.

    Behavior:
        - Waits for a specified sleep time.
        - If the success event is set, attempts to send a notification.
        - Clears the success event and resets the wait time if the notification is successful.
        - Keeps the wait time unchanged if the notification fails.
        - Logs the status of the data transfer process.
    """
    wait_time = SLEEP_TIME
    while True:
        await asyncio.sleep(wait_time)  # Check every 5 minutes
        if success_event.is_set():
            logger.info("Data feed has been successfully transferred to InfluxDB.")
            success = await send_data_feed_update_notification()
            if success:
                success_event.clear()  # Reset the event flag if the notification was successful
                wait_time = SLEEP_TIME
            else:
                wait_time = 50  # Keep the wait time unchanged
        else:
            logger.info("No new data has been transferred to InfluxDB in the last 5 minutes.")
            wait_time = 50  # Edit to 50