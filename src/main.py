#!/usr/bin/env python3
"""
Intelligent Car Shopping with LLM - Command Line Interface

This module serves as the entry point for the car search application,
providing a command line interface for testing core functionality.
"""

import sys
import argparse
from typing import Optional, List, Dict, Any

from src.config import settings
from src.models import (
    Car, 
    SearchParameters, 
    TransmissionType, 
    FuelType
)


def setup_argparse() -> argparse.ArgumentParser:
    """Set up command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Intelligent Car Shopping Assistant",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Main commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for cars")
    search_parser.add_argument(
        "--postcode", type=str, 
        default=settings.app.default_postcode,
        help="UK postcode to search from"
    )
    search_parser.add_argument(
        "--radius", type=int, 
        default=settings.app.default_radius,
        help="Search radius in miles"
    )
    search_parser.add_argument(
        "--max-price", type=float, 
        default=settings.app.default_max_price,
        help="Maximum price"
    )
    search_parser.add_argument(
        "--min-price", type=float, 
        default=None,
        help="Minimum price"
    )
    search_parser.add_argument(
        "--make", type=str, 
        default=None,
        help="Car make (e.g., Ford, BMW)"
    )
    search_parser.add_argument(
        "--model", type=str, 
        default=None,
        help="Car model (e.g., Focus, 3 Series)"
    )
    search_parser.add_argument(
        "--transmission", type=str, 
        choices=["automatic", "manual", "any"],
        default="any",
        help="Transmission type"
    )
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_parser.add_argument(
        "--show", action="store_true",
        help="Show current configuration"
    )
    config_parser.add_argument(
        "--set", nargs=2, metavar=("KEY", "VALUE"),
        action="append", dest="set_values",
        help="Set a configuration value (can be used multiple times)"
    )
    
    # Car info command
    info_parser = subparsers.add_parser("info", help="Get information about a specific car")
    info_parser.add_argument(
        "car_id", type=str,
        help="ID of the car to get information about"
    )
    
    return parser


def handle_search(args: argparse.Namespace) -> None:
    """Handle the search command."""
    print(f"Searching for cars with parameters:")
    print(f"  Postcode: {args.postcode}")
    print(f"  Radius: {args.radius} miles")
    print(f"  Price range: {args.min_price or 'Any'} - {args.max_price or 'Any'}")
    print(f"  Make: {args.make or 'Any'}")
    print(f"  Model: {args.model or 'Any'}")
    print(f"  Transmission: {args.transmission}\n")
    
    # Create search parameters
    transmission = TransmissionType.AUTOMATIC if args.transmission == "automatic" else \
                  TransmissionType.MANUAL if args.transmission == "manual" else \
                  TransmissionType.ANY
    
    search_params = SearchParameters(
        postcode=args.postcode,
        radius_miles=args.radius,
        min_price=args.min_price,
        max_price=args.max_price,
        make=args.make,
        model=args.model,
        transmission=transmission
    )
    
    print("AutoTrader URL parameters:")
    print(search_params.to_autotrader_params())
    
    # In a real implementation, this would call the search functionality
    print("\nThis is a test implementation. Search functionality will be added in Phase 2.")


def handle_config(args: argparse.Namespace) -> None:
    """Handle the config command."""
    if args.show:
        print("Current configuration:")
        print("\nAPI Settings:")
        for key, value in vars(settings.api).items():
            if key.endswith("_api_key") and value:
                # Mask API keys for security
                print(f"  {key}: {'*' * 8}{value[-4:]}")
            else:
                print(f"  {key}: {value}")
        
        print("\nApp Settings:")
        for key, value in vars(settings.app).items():
            print(f"  {key}: {value}")
    
    if args.set_values:
        for key, value in args.set_values:
            # This is a simplified version - in a real app, would need proper type conversion
            parts = key.split(".")
            if len(parts) == 2 and parts[0] in ["api", "app"]:
                section = getattr(settings, parts[0])
                if hasattr(section, parts[1]):
                    # Attempt basic type conversion
                    orig_value = getattr(section, parts[1])
                    if isinstance(orig_value, bool):
                        value = value.lower() in ["true", "yes", "1"]
                    elif isinstance(orig_value, int):
                        value = int(value)
                    elif isinstance(orig_value, float):
                        value = float(value)
                    
                    setattr(section, parts[1], value)
                    print(f"Set {key} to {value}")
                else:
                    print(f"Unknown setting: {key}")
            else:
                print(f"Invalid setting key: {key}. Use format 'section.setting'")
        
        # Save the updated configuration
        settings.save_user_config()
        print("Configuration saved.")


def handle_info(args: argparse.Namespace) -> None:
    """Handle the info command."""
    print(f"Getting information for car ID: {args.car_id}")
    print("This is a test implementation. Car info functionality will be added in Phase 2.")


def main() -> int:
    """Main entry point for the application."""
    parser = setup_argparse()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    try:
        if args.command == "search":
            handle_search(args)
        elif args.command == "config":
            handle_config(args)
        elif args.command == "info":
            handle_info(args)
        else:
            print(f"Unknown command: {args.command}")
            return 1
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
