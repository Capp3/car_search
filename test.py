import json
import logging
import os
import time

import requests
from prometheus_client import CollectorRegistry, Gauge, start_http_server

# --- Configuration ---
# Use environment variables or defaults
HARDWARE_URL = os.getenv(
    "HARDWARE_URL", "http://<hardware_ip>/o/1/api/status"
)  # REQUIRED: Set this env var or change the default
LISTEN_PORT = int(os.getenv("LISTEN_PORT", 8000))
SCRAPE_INTERVAL = int(os.getenv("SCRAPE_INTERVAL", 15))  # How often to fetch from hardware (seconds)
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 10))  # Timeout for hardware request

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- Prometheus Metrics Definition ---
# Use a dedicated registry for cleaner updates, especially if metrics might disappear
registry = CollectorRegistry()

# Gauges are suitable for values that can go up or down (like temperature, uptime)
# Use lowercase_snake_case for metric names as per Prometheus best practices
# Add units where applicable (e.g., _seconds, _celsius, _percent, _rpm)

# Example metrics based on the assumed JSON structure:
# Note: Adjust these based on YOUR actual JSON structure!
HARDWARE_UPTIME = Gauge("hardware_uptime_seconds", "System uptime in seconds", registry=registry)
HARDWARE_TEMPERATURE = Gauge("hardware_temperature_celsius", "Temperature sensor reading", registry=registry)
HARDWARE_HUMIDITY = Gauge("hardware_humidity_percent", "Humidity sensor reading", registry=registry)
# For lists like fan RPM, use labels to differentiate
HARDWARE_FAN_SPEED = Gauge("hardware_fan_speed_rpm", "Fan speed", ["fan_id"], registry=registry)
# For state strings like "ON"/"OFF", map them to numbers (e.g., 1 for ON, 0 for OFF)
HARDWARE_POWER_STATE = Gauge("hardware_power_state", "Power state (1=ON, 0=OFF)", registry=registry)
HARDWARE_ERROR_STATUS = Gauge("hardware_error_status", "Device error status code", registry=registry)

# Metric to track the success of scraping the hardware itself
HARDWARE_SCRAPE_SUCCESS = Gauge(
    "hardware_scrape_success", "Whether the scrape of the hardware succeeded (1=yes, 0=no)", registry=registry
)
HARDWARE_SCRAPE_DURATION = Gauge(
    "hardware_scrape_duration_seconds", "Duration of the hardware scrape", registry=registry
)


# --- Functions ---
def map_power_state(state_str):
    """Maps a power state string to a numeric value."""
    state_str_upper = state_str.upper()
    if state_str_upper == "ON":
        return 1
    elif state_str_upper == "OFF":
        return 0
    else:
        return -1  # Or some other value indicating unknown/other state


def fetch_and_update_metrics():
    """Fetches data from the hardware JSON endpoint and updates Prometheus gauges."""
    start_time = time.time()
    try:
        logging.debug(f"Fetching data from {HARDWARE_URL}")
        response = requests.get(HARDWARE_URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        data = response.json()
        logging.debug(f"Received data: {json.dumps(data)}")

        # --- Update Metrics ---
        # Use .get() for safety in case keys are missing
        uptime = data.get("uptimeSeconds")
        if uptime is not None:
            HARDWARE_UPTIME.set(float(uptime))

        temp = data.get("temperatureCelsius")
        if temp is not None:
            HARDWARE_TEMPERATURE.set(float(temp))

        humidity = data.get("humidityPercent")
        if humidity is not None:
            HARDWARE_HUMIDITY.set(float(humidity))

        # Handle list values with labels
        fan_rpms = data.get("fanRPM", [])  # Default to empty list
        if isinstance(fan_rpms, list):
            # Clear old labels for this metric if fans can appear/disappear dynamically
            # This requires careful handling if other parts of the script add labels.
            # If the number of fans is static, this might not be strictly needed,
            # but it's safer if the hardware might change its response structure slightly.
            # A simpler approach if fans are static is to just update existing labels.
            # Let's assume fans are relatively static for simplicity here.
            # If dynamic: consider clearing specific label sets or using a new registry each time.

            for i, rpm in enumerate(fan_rpms):
                if rpm is not None:
                    HARDWARE_FAN_SPEED.labels(fan_id=str(i)).set(float(rpm))
            # Q: What if a fan disappears? Its metric might become stale.
            # A more robust solution might involve tracking seen fan_ids and clearing old ones.

        power_state_str = data.get("powerState")
        if power_state_str is not None:
            HARDWARE_POWER_STATE.set(map_power_state(power_state_str))

        error_code = data.get("errorStatus")
        if error_code is not None:
            HARDWARE_ERROR_STATUS.set(int(error_code))

        # Mark scrape as successful
        HARDWARE_SCRAPE_SUCCESS.set(1)
        logging.info("Successfully fetched data and updated metrics.")

    except requests.exceptions.RequestException as e:
        logging.exception(f"Error fetching data from {HARDWARE_URL}: {e}")
        HARDWARE_SCRAPE_SUCCESS.set(0)
    except json.JSONDecodeError as e:
        logging.exception(f"Error decoding JSON from {HARDWARE_URL}: {e}")
        HARDWARE_SCRAPE_SUCCESS.set(0)
    except (KeyError, TypeError, ValueError) as e:
        logging.exception(f"Error processing data structure or values: {e}")
        # Depending on severity, you might still set success=1 if partial data was processed
        # Or set it to 0 if the error prevents core metrics from updating. Let's be strict:
        HARDWARE_SCRAPE_SUCCESS.set(0)
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")
        HARDWARE_SCRAPE_SUCCESS.set(0)
    finally:
        # Record scrape duration regardless of success/failure
        duration = time.time() - start_time
        HARDWARE_SCRAPE_DURATION.set(duration)
        logging.debug(f"Scrape duration: {duration:.4f} seconds")


# --- Main Execution ---
if __name__ == "__main__":
    if "<hardware_ip>" in HARDWARE_URL:
        logging.warning(
            "HARDWARE_URL is not set or uses the default placeholder. Please set the HARDWARE_URL environment variable or edit the script."
        )
        # You might want to exit here if the URL is mandatory:
        # import sys
        # sys.exit("Error: HARDWARE_URL is not configured.")

    # Start the Prometheus HTTP server in a background thread
    start_http_server(LISTEN_PORT, registry=registry)
    logging.info(f"Exporter started on port {LISTEN_PORT}")
    logging.info(f"Fetching metrics from {HARDWARE_URL} every {SCRAPE_INTERVAL} seconds")

    # Keep the main thread alive, periodically fetching data
    while True:
        fetch_and_update_metrics()
        time.sleep(SCRAPE_INTERVAL)
