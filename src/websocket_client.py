# Import necessary modules
import asyncio
import json
import ssl
import upstox_client
import websockets
from google.protobuf.json_format import MessageToDict
import src.MarketDataFeed_pb2 as pb
import json
import os
from .access_token_util import fetch_token
import requests


MAX_WEBSOCKET_CONN_RETRIES = 3
FETCH_TOKEN_API = os.getenv("API_FETCH_TOKEN", None)
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", None)
GET_INSTRUMENTS_URL = os.getenv("GET_INSTRUMENTS_URL", None)
INSTRUMENTS_LIST = [i.strip() for i in os.getenv("INSTRUMENTS_LIST", "").split(",")]

def get_market_data_feed_authorize(api_version, configuration):
    """Get authorization for market data feed."""
    api_instance = upstox_client.WebsocketApi(
        upstox_client.ApiClient(configuration))
    api_response = api_instance.get_market_data_feed_authorize(api_version)
    return api_response


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
    url = GET_INSTRUMENTS_URL
    if url:
        data = requests.get(url)
        instruments_list = data.json()["instruments"]

        print(instruments_list)

        return instruments_list
    
    elif INSTRUMENTS_LIST:
        return INSTRUMENTS_LIST
    
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

    # Configure OAuth2 access token for authorization
    configuration = upstox_client.Configuration()

    api_version = '2.0'

    retrying_period_access_token = 1

    while True:
        try:
            # Access token
            if FETCH_TOKEN_API is not None:
                configuration.access_token = await fetch_token(url=FETCH_TOKEN_API)
            elif ACCESS_TOKEN is not None:
                configuration.access_token = ACCESS_TOKEN
            else:
                raise Exception(f"Neither access token nor url to fetch is provided. Terminating...")

            # Get market data feed authorization
            response = get_market_data_feed_authorize(
                api_version, configuration)

            retry_no = 1  # 
            while retry_no <= MAX_WEBSOCKET_CONN_RETRIES:
                try:
                    # Connect to the WebSocket with SSL context
                    async with websockets.connect(response.data.authorized_redirect_uri, ssl=ssl_context) as websocket:
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
                        while True:
                            message = await websocket.recv()
                            decoded_data = decode_protobuf(message)

                            # Convert the decoded data to a dictionary
                            data_dict = MessageToDict(decoded_data)

                            # Put data in q
                            await q.put(data_dict)

                            # Print the dictionary representation
                            print("Data received from websocket.")
                
                except (
                    websockets.exceptions.ConnectionClosed,
                    websockets.exceptions.InvalidHandshake,
                    asyncio.TimeoutError
                ) as e:
                    
                    print(f"WebSocket connection closed unexpectedly or failed to connect: {e} :: Will try to re-establish connection :: retry no : {retry_no}")
                    await asyncio.sleep(2)  # Wait for a sec

                    retry_no += 1  # Increment by 1

            print(f"Max retries exceeded for establishing websocket connection :: Will retry with updated token.")
        except upstox_client.rest.ApiException as e:
            print(f"Could not get market data feed authorization :: Retrying with updating token after {retrying_period_access_token} seconds")
            await asyncio.sleep(retrying_period_access_token)

            retrying_period_access_token = min(100, retrying_period_access_token * 2)


if __name__=="__main__":
    q = asyncio.Queue()

    # Execute the function to fetch market data
    asyncio.run(fetch_market_data(q))