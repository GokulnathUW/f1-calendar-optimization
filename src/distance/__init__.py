"""
Distance and emissions calculation module for F1 calendar optimization.
Handles geocoding, haversine distance calculations, transport mode determination,
and carbon emissions computation for circuit-to-circuit and HQ-to-circuit routes.
"""

from src.distance.geocoding import geocode_location
from src.distance.haversine import compute_haversine, compute_pairwise_distances
from src.distance.emissions import calculate_emissions, determine_transport_mode
from src.distance.data_loader import load_circuits_raw, load_hq_raw
from src.distance.calendar import generate_sundays

__all__ = [
    "geocode_location",
    "compute_haversine",
    "compute_pairwise_distances",
    "calculate_emissions",
    "determine_transport_mode",
    "load_circuits_raw",
    "load_hq_raw",
    "generate_sundays",
]
