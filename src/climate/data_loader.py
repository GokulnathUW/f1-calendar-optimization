"""Data loading utilities for climate data processing."""

import pandas as pd
from pathlib import Path
from typing import Tuple


def load_race_weekends(filepath = "data/processed/sundays_2026.csv", season_start_month = 3, season_end_month = 12):
    """Load and filter race weekends from sundays data"""
    sundays_df = pd.read_csv(filepath)
    
    # Get season start and end dates
    start_date = sundays_df[sundays_df['month'] == season_start_month]['race_date'].values[0]
    end_date   = sundays_df[sundays_df['month'] == season_end_month]['race_date'].values[0]
    start_week = sundays_df[sundays_df['month'] == season_start_month]['week_num'].values[0]
    
    # Filter race weekends within season
    mask = (sundays_df['race_date'] >= start_date) & (sundays_df['race_date'] <= end_date)
    race_weekends_df = sundays_df.loc[mask].reset_index(drop=True)
    
    # Normalize week numbers to start from 1
    race_weekends_df['week_num'] = race_weekends_df['week_num'] - start_week + 1
    
    return race_weekends_df, start_date, end_date


def load_circuits(filepath = "data/processed/circuits.csv"):
    """Load circuit data from CSV file"""
    return pd.read_csv(filepath)
