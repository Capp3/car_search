#!/usr/bin/env python3
"""
Example script demonstrating how to use the Smartcar API client.

This script shows how to:
1. Obtain vehicle information
2. Connect to a real vehicle via OAuth
3. Get real-time vehicle data
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.services.api_clients.smartcar import SmartcarAPIClient

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()


def main():
    """Run the example script."""
    # Get API key from environment variables
    api_key = os.getenv("SMARTCAR_API_KEY")
    client_secret = os.getenv("SMARTCAR_CLIENT_SECRET")
    redirect_uri = os.getenv("SMARTCAR_REDIRECT_URI")
    
    if not api_key:
        logger.error("SMARTCAR_API_KEY environment variable not set")
        sys.exit(1)
    
    # Initialize the Smartcar API client
    client = SmartcarAPIClient(
        api_key=api_key,
        client_secret=client_secret or "",
        redirect_uri=redirect_uri or ""
    )
    
    # Example 1: Get car details by make, model, and year
    print("\n=== Example 1: Get Car Details ===")
    make = "Toyota"
    model = "Camry"
    year = 2020
    
    print(f"Getting details for {make} {model} {year}...")
    
    try:
        car = client.get_car_details(make, model, year)
        
        if car:
            print(f"Retrieved car: {car.get_attribute('title')}")
            print("\nCar attributes:")
            for attr_name, attribute in car.attributes.items():
                print(f"  {attr_name}: {attribute.value}")
        else:
            print("No car details found")
    except Exception as e:
        print(f"Error getting car details: {str(e)}")
    
    # Example 2: Get reliability data
    print("\n=== Example 2: Get Reliability Data ===")
    
    try:
        reliability = client.get_reliability_data(make, model, year)
        
        if reliability:
            print("Reliability data:")
            if "score" in reliability:
                print(f"  Score: {reliability['score']}")
            
            if "commonIssues" in reliability:
                print("\nCommon issues:")
                for issue in reliability["commonIssues"]:
                    print(f"  - {issue}")
        else:
            print("No reliability data found")
    except Exception as e:
        print(f"Error getting reliability data: {str(e)}")
    
    # Example 3: Get maintenance schedule
    print("\n=== Example 3: Get Maintenance Schedule ===")
    
    try:
        maintenance = client.get_maintenance_schedule(make, model, year)
        
        if maintenance:
            print("Maintenance schedule:")
            for item in maintenance:
                print(f"  - {item.get('mileage', 'N/A')} miles: {item.get('description', 'N/A')}")
        else:
            print("No maintenance schedule found")
    except Exception as e:
        print(f"Error getting maintenance schedule: {str(e)}")
    
    # Example 4: Generate auth URL for vehicle connection
    if client_secret and redirect_uri:
        print("\n=== Example 4: Generate Auth URL ===")
        
        # Define the required scopes
        scopes = [
            "read_vehicle_info",
            "read_location",
            "read_odometer",
            "read_fuel",
            "read_battery",
            "read_tires",
            "read_engine_oil"
        ]
        
        try:
            auth_url = client.get_auth_url(scopes)
            print("To connect a vehicle, open the following URL in a browser:")
            print(auth_url)
            print("\nAfter authorization, you'll be redirected to the redirect URI with a code parameter.")
            print("Use this code to exchange for an access token with client.exchange_code_for_token(code)")
        except Exception as e:
            print(f"Error generating auth URL: {str(e)}")
    
    # Example 5: Exchange code for token (manual step required)
    print("\n=== Example 5: Exchange Code for Token ===")
    print("This step requires user interaction and a valid authorization code.")
    print("Uncomment the following code block and replace 'AUTHORIZATION_CODE' with the actual code:")
    print("""
    try:
        code = "AUTHORIZATION_CODE"  # Replace with actual code from redirect
        token_data = client.exchange_code_for_token(code)
        
        print("Access token obtained successfully")
        print(f"Access token: {token_data.get('access_token')}")
        print(f"Refresh token: {token_data.get('refresh_token')}")
        print(f"Expires in: {token_data.get('expires_in')} seconds")
    except Exception as e:
        print(f"Error exchanging code for token: {str(e)}")
    """)
    
    # Example 6: Get vehicle data (requires valid token)
    print("\n=== Example 6: Get Vehicle Data ===")
    print("This step requires a valid access token.")
    print("Uncomment the following code block after obtaining an access token:")
    print("""
    try:
        # Get list of connected vehicles
        vehicles = client.get_vehicles()
        
        if vehicles:
            vehicle_id = vehicles[0]["id"]
            print(f"Using vehicle with ID: {vehicle_id}")
            
            # Get vehicle info
            info = client.get_vehicle_info(vehicle_id)
            print(f"Vehicle info: {info}")
            
            # Get vehicle location
            location = client.get_vehicle_location(vehicle_id)
            print(f"Location: {location}")
            
            # Get odometer reading
            odometer = client.get_vehicle_odometer(vehicle_id)
            print(f"Odometer: {odometer}")
            
            # Get fuel level
            fuel = client.get_vehicle_fuel(vehicle_id)
            print(f"Fuel: {fuel}")
            
            # Get battery level (for electric vehicles)
            battery = client.get_vehicle_battery(vehicle_id)
            print(f"Battery: {battery}")
        else:
            print("No connected vehicles found")
    except Exception as e:
        print(f"Error getting vehicle data: {str(e)}")
    """)


if __name__ == "__main__":
    main() 