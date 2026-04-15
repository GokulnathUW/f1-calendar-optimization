"""Haversine distance calculations for pairwise route distances."""

import numpy as np
import pandas as pd
from typing import Tuple


EARTH_RADIUS_KM = 6371  # Earth radius in kilometers
EUROPE_ROAD_FACTOR = 1.2  # Adjustment factor for road travel in Europe


def compute_haversine(df) -> np.ndarray:
    """Compute haversine distances for pairs of coordinates"""
    lat1 = np.radians(df['latitude_from'].values)
    lon1 = np.radians(df['longitude_from'].values)
    lat2 = np.radians(df['latitude_to'].values)
    lon2 = np.radians(df['longitude_to'].values)
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    
    return EARTH_RADIUS_KM * c


def compute_pairwise_distances(df_a, df_b, id_col_a = 'circuit_id', id_col_b = 'circuit_id', suffix_a = '_from', suffix_b = '_to'):
    """Compute pairwise distances between two sets of locations"""
    # Create merged DataFrame with all pairs
    distance_df = pd.merge(
        df_a, df_b, how='cross',
        suffixes=(suffix_a, suffix_b)
    )
    
    # Compute haversine distance
    distance_df['distance_km'] = compute_haversine(distance_df)
    
    # Adjust distances for land travel in Europe
    europe_mask = (
        (distance_df[f'continent{suffix_a}'] == 'Europe') &
        (distance_df[f'continent{suffix_b}'] == 'Europe')
    )
    distance_df.loc[europe_mask, 'distance_km'] *= EUROPE_ROAD_FACTOR
    
    return distance_df
