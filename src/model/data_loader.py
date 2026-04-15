"""Data loading and preprocessing utilities for the optimization model."""

import pandas as pd
from typing import Tuple, Dict
from pathlib import Path
from src.parameters import EMISSION_FACTORS_TONNE_KM, AVERAGE_TEAM_FREIGHT_TONNES


def load_model_data(
    circuits_path = "data/processed/circuits.csv",
    distances_path = "data/processed/distances.csv",
    climate_path = "data/processed/climate.csv",
    festivals_path = "data/processed/festivals.csv",
    hq_path = "data/processed/hq.csv"
):
    """Load all processed data required for model construction"""
    circuits_df  = pd.read_csv(circuits_path)
    distances_df = pd.read_csv(distances_path)
    climate_df   = pd.read_csv(climate_path)
    festivals_df = pd.read_csv(festivals_path)
    teams_df     = pd.read_csv(hq_path)
    
    return {
        "circuits": circuits_df,
        "distances": distances_df,
        "climate": climate_df,
        "festivals": festivals_df,
        "teams": teams_df
    }


def create_symmetric_distances(distances_df):
    """Create symmetric distance matrix by adding reverse routes"""
    rev_df = distances_df.rename(columns={"from": "to", "to": "from"})
    
    symmetric_df = (
        pd.concat([distances_df, rev_df], ignore_index=True)
        .drop_duplicates(subset=["from", "to"])
    )
    
    return symmetric_df


def extract_race_emissions(distances_df, circuits):
    """Extract emissions between race circuits"""
    return distances_df[
        distances_df['from'].isin(circuits) &
        distances_df['to'].isin(circuits)
    ][["from", "to", "emissions_kgCO2e"]]


def extract_hq_emissions(distances_df, teams, circuits):
    """Extract emissions from team headquarters to circuits"""
    return distances_df[
        distances_df['from'].isin(teams)
    ][["from", "to", "emissions_kgCO2e"]]
