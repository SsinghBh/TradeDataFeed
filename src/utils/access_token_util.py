import aiohttp
from aiohttp.client_exceptions import ClientConnectorError
import asyncio

async def fetch_token(url: str) -> str:
    """
    Fetch an access token from the given API endpoint.

    This function attempts to retrieve an access token from the specified URL.
    It uses an infinite loop with a retry mechanism to handle network errors
    and unexpected issues gracefully.

    Args:
        url (str): The URL of the API endpoint to fetch the access token from.

    Returns:
        str: The access token if successfully fetched.

    Raises:
        ClientConnectorError: If a connection error occurs.
        KeyError: If the 'access_token' key is missing in the response.
        ValueError: If the access token is not of type 'str'.
        Exception: For any other unexpected errors.
    """
    while True:
        try:
            print("Attempting to fetch access token")
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        access_token = data.get("access_token")
                        print(f"API token fetched :: token : {access_token}")
                        
                        if not isinstance(access_token, str):
                            raise ValueError("Access token is not of type 'str'")
                        
                        return access_token
                    else:
                        data = await response.json()
                        error = data.get("error")
                        print(f"Failed to fetch access token. Status: {response.status}, error occured : {error} :: Will retry after 2 seconds")
                    
        except ClientConnectorError as e:
            print(f"Connection error occurred: {e} :: Will retry after 2 seconds")

        except KeyError as e:
            print(f"KeyError: {e} not found in the response data :: Will retry after 2 seconds")

        except ValueError as e:
            print(f"ValueError: {e} :: Will retry after 2 seconds")

        except Exception as e:
            print(f"An unexpected error occurred: {e} :: Aborting token fetching")
            raise

        await asyncio.sleep(2)