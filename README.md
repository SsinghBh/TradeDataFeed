# TradeDataFeed

## Overview

**TradeDataFeed** is a service that receives real-time trading data via websocket from brokers and stores it in InfluxDB. The service is designed for algorithmic trading applications, ensuring data integrity and fault tolerance.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Running the Project](#running-the-project)
   - [Option A: Data Feed Service Only](#option-a-data-feed-service-only)
   - [Option B: Data Feed Service with InfluxDB](#option-b-data-feed-service-with-influxdb)
4. [Configuration](#configuration)

## Prerequisites

- **Python 3.7+**
- **Docker** and **Docker Compose** (for running with Docker)
- **Upstox Account and API Keys** (or other supported brokers)

## Installation

### Clone the Repository

```bash
git clone https://github.com/SsinghBh/TradeDataFeed.git
cd TradeDataFeed
```

# Install Dependencies
If running locally without Docker:

```bash
pip install -r requirements.txt
```

# Running the Project
## Option A: Data Feed Service Only
In this setup, it is assumed that you have an existing InfluxDB instance. You need to configure the service to connect to your InfluxDB database.

1. Edit the Configuration: Modify the config.py file to include your InfluxDB connection details.

2. Run the Service: Start the data feed service.

```bash
python src/main.py
```
## Option B: Data Feed Service with InfluxDB
This setup initializes both the data feed service and an InfluxDB container. Docker Compose is used to manage the containers.

1. Set Up Environment Variables: You can either create a .env file or pass environment variables at runtime.
Example .env file:
    ```text
    INFLUXDB_BUCKET_NAME=stock_data
    INFLUXDB_ORG=my-org
    INFLUXDB_URL=http://localhost:8086
    API_FETCH_TOKEN_URL=your-api-fetch-token-url
    INSTRUMENT_KEYS_LIST_URL=your-instruments-list-url
    DATA_FEED_UPDATE_INFORM_URL=your-data-feed-update-notification-url
    ```
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
           -p 5000:5000 yourusername/data-feed-service
    ```

# Configuration
**Configuration File (config.py)**  
+ INFLUXDB_BUCKET_NAME: The name of the InfluxDB bucket to store data.
+ INFLUXDB_ORG: The InfluxDB organization name.
+ INFLUXDB_URL: The URL of the InfluxDB instance.
+ API_FETCH_TOKEN_URL: The URL endpoint to fetch the API token.
+ INSTRUMENT_KEYS_LIST_URL: The URL endpoint to get the list of instrument keys.
+ DATA_FEED_UPDATE_INFORM_URL: The URL endpoint to inform about data feed updates.

You can configure these settings either directly in the config.py file or through environment variables.