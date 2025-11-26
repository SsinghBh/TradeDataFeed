# Import necessary modules
import asyncio
import json
import ssl
import websockets
import requests
import os
from datetime import datetime
import socket
from google.protobuf.json_format import MessageToDict

from . import MarketDataFeedV3_pb2 as pb
from .data_models.market_info import MarketInfoEvent
from .data_models.live_feed import LiveFeed
from utils import fetch_token
import logging


class InvalidTokenError(Exception):
    """Raised when the API indicates the access token is invalid or expired."""
    pass

logger = logging.getLogger(__name__)

MAX_WEBSOCKET_CONN_RETRIES = 3
FETCH_TOKEN_API = os.getenv("API_FETCH_TOKEN", None)
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", None)
GET_INSTRUMENTS_URL = os.getenv("GET_INSTRUMENTS_URL", None)

raw = os.getenv("INSTRUMENTS_LIST", "")
tokens = [i.strip() for i in raw.split(",") if i.strip()]
INSTRUMENTS_LIST = tokens if tokens else None

def get_market_data_feed_authorize_v3(access_token):
    """Get authorization for market data feed.

    Raises
    ------
    InvalidTokenError
        If the API responds with status "error" and error_code "UDAPI100050".
    """
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    url = 'https://api.upstox.com/v3/feed/market-data-feed/authorize'
    api_response = requests.get(url=url, headers=headers)

    # Parse and handle potential error response structure
    try:
        payload = api_response.json()
    except ValueError:
        # If not JSON, raise with HTTP status context
        api_response.raise_for_status()
        # If no exception raised by raise_for_status, rethrow a generic error
        raise Exception("Unexpected non-JSON response from authorize endpoint.")

    # Handle error structure: {"status": "error", "errors": [{"error_code": "...", "message": "..."}]}
    if isinstance(payload, dict) and payload.get("status") == "error":
        errors = payload.get("errors") or []
        for err in errors:
            if isinstance(err, dict) and err.get("error_code") == "UDAPI100050":
                message = err.get("message") or "Invalid or expired access token."
                raise InvalidTokenError(message)
        # For other errors, raise a generic exception including first error message if present
        if errors:
            raise Exception(errors[0].get("message") if isinstance(errors[0], dict) else "Authorization failed with error status.")
        raise Exception("Authorization failed with error status.")

    return payload


def decode_protobuf(buffer):
    """Decode protobuf message."""
    feed_response = pb.FeedResponse()
    feed_response.ParseFromString(buffer)
    return feed_response

def get_instruments():
    """
    Retrieves the list of instruments for market data subscription.

    This function fetches the list of instruments from a specified URL or returns a predefined 
    list of instruments. If neither a URL nor a predefined list is available, an exception is raised.

    Returns
    -------
    list
        A list of instruments for market data subscription.

    Raises
    ------
    Exception
        If neither a URL nor a predefined list of instruments is provided.

    Notes
    -----
    - If a URL is provided via the GET_INSTRUMENTS_URL variable, the function sends an HTTP GET request to retrieve the instruments list.
    - If the URL is not provided, it returns the predefined list from the INSTRUMENTS_LIST variable.
    """
    
    if INSTRUMENTS_LIST is not None:
        return INSTRUMENTS_LIST

    elif GET_INSTRUMENTS_URL is not None:
        data = requests.get(GET_INSTRUMENTS_URL)
        instruments_list = data.json()["instruments"]

        print(instruments_list)

        return instruments_list
    
    raise Exception(f"Cannot fetch instruments list. Terminating app...")

async def fetch_market_data(q: asyncio.Queue):
    """
    Fetches market data using WebSocket and places it into the provided asyncio Queue.

    This function establishes a WebSocket connection to the Upstox market data feed, subscribes 
    to specified instruments, and continuously listens for incoming data. The received data is 
    decoded and placed into the provided queue for further processing.

    Parameters
    ----------
    q : asyncio.Queue
        The queue where decoded market data will be placed.

    Raises
    ------
    Exception
        If neither an access token nor a URL to fetch the token is provided.

    Notes
    -----
    - The function includes retry logic for handling WebSocket connection failures.
    - It operates within an infinite loop and is designed to run as a long-lived task within an 
      asyncio event loop.
    """

    # Create default SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    retrying_period_access_token = 1

    while True:
        try:
            # Access token
            if ACCESS_TOKEN is not None:
                access_token = ACCESS_TOKEN
            elif FETCH_TOKEN_API is not None:
                access_token = await fetch_token(url=FETCH_TOKEN_API)
            else:
                raise Exception(f"Neither access token nor url to fetch is provided. Terminating...")

            # Get market data feed authorization
            response = get_market_data_feed_authorize_v3(access_token=access_token)
            
            
            retry_no = 1
            count = 0
            # Connect to the WebSocket with SSL context
            while retry_no <= MAX_WEBSOCKET_CONN_RETRIES:
                try:
                    async with websockets.connect(response["data"]["authorized_redirect_uri"], ssl=ssl_context) as websocket:
                        print('Connection established')

                        await asyncio.sleep(1)  # Wait for 1 second

                        # Data to be sent over the WebSocket
                        data = {
                            "guid": "someguid",
                            "method": "sub",
                            "data": {
                                "mode": "full",
                                "instrumentKeys": get_instruments()
                            }
                        }

                        # Convert data to binary and send over WebSocket
                        binary_data = json.dumps(data).encode('utf-8')
                        await websocket.send(binary_data)

                        # Continuously receive and decode data from WebSocket
                        message = await websocket.recv()  # Recieve market info
                        market_info = MessageToDict(decode_protobuf(message))
                        MarketInfoEvent(**market_info)
                        print("Market data : \n", market_info)
                        await websocket.recv()  # Recieve market snapshot
                        while True:
                            message = await websocket.recv()
                            decoded_data = decode_protobuf(message)

                            # Convert the decoded data to a dictionary
                            data_dict = MessageToDict(decoded_data)

                            # print("data dict : ", data_dict, "\n\n")

                            start_time = datetime.now()
                            live_data = LiveFeed(**data_dict)
                            end_time = datetime.now()
                            print(f"Time taken to parse data using pydantic : {(end_time - start_time).total_seconds()*1000} ms")

                            # Put data in q
                            await q.put(live_data)
                            # print(live_data.model_dump_json(), "\n\n")

                            # Print the dictionary representation
                            logger.debug("Data received from websocket.")
                except (
                    websockets.exceptions.ConnectionClosed,
                    websockets.exceptions.InvalidHandshake,
                    asyncio.TimeoutError,
                    socket.gaierror,     # DNS resolution failed
                    OSError              # Covers WinError 121 and other low-level I/O issues
                ) as e:
                    
                    print(f"WebSocket connection closed unexpectedly or failed to connect: {e} :: Will try to re-establish connection :: retry no : {retry_no}")
                    await asyncio.sleep(2)  # Wait for a sec

                    retry_no += 1  # Increment by 1
            print(f"Max retries exceeded for establishing websocket connection :: Will retry with updated token.")

        except (
            ConnectionError, 
            requests.exceptions.RequestException
        ) as e:
            logger.warning(f"Network/Authorization call failed: {e}. Retrying in 10s...")
            await asyncio.sleep(10)
            continue

        except InvalidTokenError as e:
            print(f"Could not get market data feed authorization :: Error occured : {str(e)} :: Retrying with updating token after {retrying_period_access_token} seconds")
            await asyncio.sleep(retrying_period_access_token)

            retrying_period_access_token = min(100, retrying_period_access_token * 2)
        except Exception as e:
            logger.error(f"Unknown exception occured. Raising error and terminating... {str(e)}")
            raise e
        
if __name__ == "__main__":
    # Execute the function to fetch market data
    asyncio.run(fetch_market_data())
