"""
Climate data module for F1 calendar optimization.
Handles fetching historical weather data, processing circuit climate information,
and evaluating race weekend weather feasibility.
"""

from src.climate.api_client import fetch_historical_weather
from src.climate.feasibility import evaluate_climate_feasibility, process_circuit_climate_data
from src.climate.data_loader import load_race_weekends, load_circuits

__all__ = [
    "fetch_historical_weather",
    "evaluate_climate_feasibility",
    "process_circuit_climate_data",
    "load_race_weekends",
    "load_circuits",
]
