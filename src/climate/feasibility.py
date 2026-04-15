"""Climate feasibility analysis for F1 race weekends."""

import pandas as pd
from tqdm import tqdm
from src.climate.api_client import fetch_historical_weather
from src.parameters import MIN_TEMP_C, MAX_TEMP_C, MAX_PRECIP_MM


def process_circuit_climate_data(race_weekends_df, circuits_df, circuit_ids = None, show_progress = True):
    """Fetch and append historical climate data for each circuit and race weekend"""
    if show_progress:
        tqdm.pandas()
    
    for index, circuit in circuits_df.iterrows():
        circuit_id = circuit['circuit_id']
        
        # Skip if specific circuit_ids are provided and this one isn't in the list
        if circuit_ids and circuit_id not in circuit_ids:
            continue
        
        coords = f"{circuit['latitude']},{circuit['longitude']}"
        
        print(f"Processing circuit: {circuit_id} at {coords} [{index+1}/{len(circuits_df)}]")
        
        race_weekends_df[[
            f'{circuit_id}_avg_temp',
            f'{circuit_id}_avg_precip'
        ]] = race_weekends_df.progress_apply(
            lambda row: fetch_historical_weather(row['race_date'], coords),
            axis=1
        )
    
    return race_weekends_df


def evaluate_climate_feasibility(race_weekends_df,circuit_id, min_temp = MIN_TEMP_C, max_temp = MAX_TEMP_C, max_precip = MAX_PRECIP_MM):
    """Evaluate whether climate conditions are feasible for a race"""
    temp_col = f'{circuit_id}_avg_temp'
    precip_col = f'{circuit_id}_avg_precip'
    
    feasible = (
        (race_weekends_df[temp_col] >= min_temp) &
        (race_weekends_df[temp_col] <= max_temp) &
        (race_weekends_df[precip_col] <= max_precip)
    )
    
    return feasible
