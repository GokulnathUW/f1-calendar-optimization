"""API client for weather data services."""

import time
import requests
import numpy as np
import pandas as pd
from typing import Optional


# Default API key for VisualCrossing weather service
DEFAULT_API_KEY = "U2333EX6VCZBN2545ACQYFPV4"
BASE_URL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"


def fetch_historical_weather(race_date, coords, years = 5, api_key = None):
    """Fetch and average historical weather data for a given date and location"""
    if api_key is None:
        api_key = DEFAULT_API_KEY
    
    params = {
        "key": api_key,
        "include": "days",
        "contentType": "json"
    }
    
    temps = []
    precips = []
    
    for year_offset in range(1, years + 1):
        year = int(race_date[:4]) - year_offset
        historical_date = f"{year}{race_date[4:]}"
        url = f"{BASE_URL}/{coords}/{historical_date}"
        
        response = requests.get(url, params=params)
        
        try:
            res = response.json()
            day_data = res['days'][0]
            temps.append(day_data['temp'])
            precips.append(day_data['precip'])
        except Exception as e:
            raise RuntimeError(
                f"Error fetching data for {coords} on {historical_date}: {e}"
            )
        
        time.sleep(1)  # Respect API rate limits
    
    return pd.Series([
        round(np.mean(temps), 2),
        round(np.mean(precips), 2)
    ])
