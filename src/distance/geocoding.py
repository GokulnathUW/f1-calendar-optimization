"""Geocoding utilities for converting location names to coordinates."""

import time
import pandas as pd
from geopy.geocoders import Nominatim
from typing import Optional


# Global geolocator instance (reuses connection)
_geolocator = None


def _get_geolocator(user_agent = "f1_calendar_optimization") -> Nominatim:
    """Get or create geolocator instance."""
    global _geolocator
    if _geolocator is None:
        _geolocator = Nominatim(user_agent=user_agent)
    return _geolocator


def geocode_location(city, country, locator = None):
    """Geocode a city and country to latitude/longitude"""
    if locator is None:
        locator = _get_geolocator()
    
    lat_long = [None, None]
    
    try:
        location = locator.geocode(f"{city}, {country}")
        if location:
            lat_long = [location.latitude, location.longitude]
    except Exception as e:
        print(f"Error geocoding {city}, {country}: {e}")
    
    time.sleep(1)  # Respect Nominatim's usage policy
    return pd.Series(lat_long)
