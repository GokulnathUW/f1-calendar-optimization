"""Data loading utilities for distance calculations."""

import pandas as pd
from pathlib import Path
from typing import Tuple


def load_circuits_raw(filepath = "data/raw/circuits.csv"):
    """Load raw circuit data from CSV file"""
    return pd.read_csv(filepath)


def load_hq_raw(filepath = "data/raw/hq.csv"):
    """Load raw headquarters data from CSV file"""
    return pd.read_csv(filepath)


def load_processed_circuits(filepath = "data/processed/circuits.csv"):
    """Load processed circuit data with coordinates"""
    return pd.read_csv(filepath)


def load_processed_hq(filepath = "data/processed/hq.csv"):
    """Load processed headquarters data with coordinates"""
    return pd.read_csv(filepath)
