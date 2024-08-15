# TradeDataFeed

**TradeDataFeed** is a specialized service designed to interface with the Upstox broker, enabling real-time trading data acquisition via websocket. This project incorporates example scripts provided by Upstox, which are available on their [GitHub](https://github.com/upstox/upstox-python/tree/master/examples/websocket) and [official documentation](https://upstox.com/developer/api-documentation/get-market-data-feed). These examples serve as the foundation for establishing the connection and retrieving market data.

## Key Features

- **Upstox Broker Integration**: The current implementation is exclusively tailored for the Upstox platform. It leverages Upstox's API and websocket capabilities to fetch live market data efficiently.

- **Adaptation and Enhancement**: Building on the basic examples from Upstox, this project extends the functionality to create a robust data pipeline. Key enhancements include:
  - **Data Ingestion and Storage**: The data fetched from the websocket is processed and stored in InfluxDB, a time-series database suitable for high-performance data analytics.
  - **Error Handling and Resilience**: The code includes mechanisms to handle potential issues such as network failures or data inconsistencies, ensuring data integrity and reliability.

- **Dockerized Deployment**: To facilitate ease of deployment and scalability, the entire application is containerized using Docker. This setup allows for consistent environments across development and production, simplifying the deployment process.


## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
   - [Clone the Repository](#clone-the-repository)
3. [Running the Project](#running-the-project)
   - [Option A: Running as a Standalone Python Application](#option-a-running-as-a-standalone-python-application)
   - [Option B: Running Inside a Docker Container](#option-b-running-inside-a-docker-container)
     - [Scenario A: Using Docker Compose](#scenario-a-using-docker-compose)
     - [Scenario B: Using Dockerfile to run trade_data_feed](#scenario-b-using-dockerfile-to-run-trade_data_feed)
4. [Configuration](#configuration)
5. [Additional Notes](#additional-notes)

## Prerequisites

- **Python 3.7+**
- **Docker** and **Docker Compose** (for running with Docker)
- **Upstox Account and access token** (or other supported brokers)

## Installation

### Clone the Repository

```bash
git clone https://github.com/SsinghBh/TradeDataFeed.git
cd TradeDataFeed
```


# Running the Project
This section provides instructions for running the **trade_data_feed** service, either as a standalone Python application, inside a Docker container, or using Docker Compose.
## Option A: Running as a Standalone Python Application
In this setup, it is assumed that you have an existing InfluxDB instance. You need to configure the service to connect to your InfluxDB database.

1. **Setup the Environment**:
   - Clone the repository and navigate to the project directory.
   - Create a `.env` file in the root directory with the required environment variables. Example:

        ```text
        # Either specify API_FETCH_TOKEN or ACCESS_TOKEN, not both 
        API_FETCH_TOKEN=your-api-fetch-token-url
        ACCESS_TOKEN=your-access-token
        # Either GET_INSTRUMENTS_URL or INSTRUMENTS_LIST is required, not both
        GET_INSTRUMENTS_URL=your-instruments-list-url
        INSTRUMENTS_LIST=<instrument1>, <instrument2>,...
        DATA_FEED_UPDATE_URL=your-data-feed-update-notification-url
        NOTIFICATION_SLEEP_TIME=60
        NOTIFICATION_WAIT_TIME=50

        # InfluxDB creds
        INFLUX_BUCKET_NAME=influxdb-bucket-name
        INFLUX_DB_ORG=influxdb-org
        INFLUX_DB_URL=influxdb-url
        INFLUX_DB_TOKEN=your-influxdb-token
        ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application**:
    ```bash
    python app.py
    ```

## Option B: Running Inside a Docker Container
There are two main scenarios for running the **trade_data_feed** service inside Docker:

**Scenario A: Using Docker Compose**

Here, it is assumed that there is no influxDB instance already present and docker-compose file will build and run both, the influxDB instance and trade_data_feed application.

1. Set Up Environment Variables: You can either create a .env file or pass environment variables at runtime.  
Example .env file:
    ```text
    API_FETCH_TOKEN=your-api-fetch-token-url
    # Either GET_INSTRUMENTS_URL or INSTRUMENTS_LIST is required, not both
    GET_INSTRUMENTS_URL=your-instruments-list-url
    INSTRUMENTS_LIST=<instrument1>, <instrument2>,...
    DATA_FEED_UPDATE_URL=your-data-feed-update-notification-url
    NOTIFICATION_SLEEP_TIME=60
    NOTIFICATION_WAIT_TIME=50
    ```
    These can also be specified in the docker-compose file has well.

2. Run Docker Compose: This will build and start the containers.
    ```bash
    docker-compose up --build
    ```
    If you prefer not to use a .env file, you can pass environment variables directly:
    ```bash
    docker run -e INFLUXDB_BUCKET_NAME=stock_data \
           -e INFLUXDB_ORG=my-org \
           -e INFLUXDB_URL=http://localhost:8086 \
           -e API_FETCH_TOKEN_URL=your-api-fetch-token-url \
           -e INSTRUMENT_KEYS_LIST_URL=your-instruments-list-url \
           -e DATA_FEED_UPDATE_INFORM_URL=your-data-feed-update-notification-url \
           yourusername/data-feed-service
    ```

**Scenario B: Using Dockerfile to run trade_data_feed**  
In order to run only the trade_data_feed application inside a docker container, an influxDB instance should already be present.

1. 
    - Clone the repository and navigate to the project directory.
    - Set Up Environment Variables: You can either create a .env file or pass environment variables at runtime. All the environment variables that specify configuration for the **trade_data_feed** application as well as connection to influxDB instance should be specified.  
Example .env file:
        ```text
        # Either specify API_FETCH_TOKEN or ACCESS_TOKEN, not both 
        API_FETCH_TOKEN=your-api-fetch-token-url
        ACCESS_TOKEN=your-access-token
        # Either GET_INSTRUMENTS_URL or INSTRUMENTS_LIST is required, not both
        GET_INSTRUMENTS_URL=your-instruments-list-url
        INSTRUMENTS_LIST=<instrument1>, <instrument2>,...
        DATA_FEED_UPDATE_URL=your-data-feed-update-notification-url
        NOTIFICATION_SLEEP_TIME=60
        NOTIFICATION_WAIT_TIME=50

        # InfluxDB creds
        INFLUX_BUCKET_NAME=influxdb-bucket-name
        INFLUX_DB_ORG=influxdb-org
        INFLUX_DB_URL=influxdb-url
        INFLUX_DB_TOKEN=your-influxdb-token
        ```
        These can also be specified in the arguments while running the container. In case the **trade_data_feed** application has to communicate with another application running inside docker container on the same host, they have to be on the same docker network in order to communicate and use container Id instead of `localhost` for specifying URL. In case the app has to communicate with another application (like access token or notification URL) running on host without docker container, use `host.docker.internal` instead of `localhost`.
2. Run the Dockerfile to build the image
    ```bash
    docker build . -t trade_data_feed
    ```
3. Run the container
    ```bash
    docker run -d trade_data_feed
    ```

# Configuration
**Configuration File (.env)**  
+ INFLUXDB_BUCKET_NAME: The name of the InfluxDB bucket to store data.
+ INFLUXDB_ORG: The InfluxDB organization name.
+ INFLUXDB_URL: The URL of the InfluxDB instance.
+ INFLUX_DB_TOKEN: InfluxDB access token to communicate.
+ API_FETCH_TOKEN: The GET url endpoint to fetch the API token. The response should be in the following format:
    ```json
    {"access_token" : access_token}
    ```
+ ACCESS_TOKEN: access token which is obtained after authentication with upston. Refer to [this](https://upstox.com/developer/api-documentation/authentication). It is reset everyday at 3 'o clock at night so, a new container has to be run everyday if this argument is passed. For automation, use `API_FETCH_TOKEN` which can make this process of fetching access token dynamic and some other application (authentication service) can daily fetch the access token. Either provide this or `API_FETCH_TOKEN`, not both.
+ GET_INSTRUMENTS_URL: The URL endpoint to get the list of instrument keys.
+ INSTRUMENTS_LIST: Comma separated list of instruments (instrument_key or instrument_token).
+ DATA_FEED_UPDATE_INFORM_URL: The POST url endpoint to inform about data feed updates.
+ NOTIFICATION_SLEEP_TIME: Duration in seconds after which notification is sent to notification endpoint given the data has arrived and pushed to DB. Default to 60.
+ NOTIFICATION_WAIT_TIME: In case of failure to push data to DB (DB not online or network error), a retry logic of this duration is implemented to push data to DB. Default to 50.

## Additional Notes

- **Source Code Attribution**: Several components of the initial setup and data handling are based directly on the example scripts from Upstox's resources. These scripts have been integrated with modifications to fit the broader architecture and requirements of this project.

- **Potential for Future Extensions**: While the current implementation is focused on Upstox, the system's modular design allows for potential expansion to support other brokers. Such expansions would require additional development to accommodate different API structures and data formats.