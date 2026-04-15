#!/usr/bin/env python3
"""
Main script for processing F1 distance and emissions data.
Computes pairwise distances between circuits and team headquarters,
determines transport modes, and calculates carbon emissions.
"""

import argparse
import sys
from pathlib import Path
from tqdm import tqdm
import pandas as pd

from src.distance.geocoding import geocode_location
from src.distance.haversine import compute_pairwise_distances
from src.distance.emissions import calculate_emissions, determine_transport_mode
from src.distance.data_loader import load_circuits_raw, load_hq_raw
from src.distance.calendar import generate_sundays


def geocode_circuits(circuits_df):
    """Add latitude and longitude to circuits DataFrame."""
    tqdm.pandas()
    print("Geocoding circuits...")
    circuits_df[['latitude', 'longitude']] = circuits_df.progress_apply(
        lambda row: geocode_location(row['city'], row['country']),
        axis=1
    )
    return circuits_df


def geocode_hq(hq_df):
    """Add latitude and longitude to HQ DataFrame using airport_city."""
    tqdm.pandas()
    print("Geocoding team headquarters...")
    hq_df[['latitude', 'longitude']] = hq_df.progress_apply(
        lambda row: geocode_location(row['airport_city'], row['country']),
        axis=1
    )
    return hq_df


def compute_circuit_distances(circuits_df):
    """Compute pairwise distances between all circuits."""
    print("Computing circuit-to-circuit distances...")
    
    # Create pairs (only unique pairs where id_from < id_to)
    distance_df = pd.merge(
        circuits_df, circuits_df, how='cross',
        suffixes=('_from', '_to')
    )
    distance_df = distance_df[
        distance_df['circuit_id_from'] < distance_df['circuit_id_to']
    ]
    
    # Compute distances and adjust for European road travel
    distance_df = compute_pairwise_distances(
        circuits_df, circuits_df,
        id_col_a='circuit_id',
        id_col_b='circuit_id'
    )
    
    # Determine transport mode
    distance_df['transport_mode'] = determine_transport_mode(
        distance_df['continent_from'],
        distance_df['continent_to']
    )
    
    # Calculate emissions
    distance_df['emissions_kgCO2e'] = calculate_emissions(
        distance_df['distance_km'],
        distance_df['transport_mode']
    )
    
    # Select and rename columns
    distance_df = distance_df[[
        'circuit_id_from', 'circuit_id_to',
        'distance_km', 'transport_mode', 'emissions_kgCO2e'
    ]]
    distance_df.columns = ['from', 'to', 'distance_km', 'transport_mode', 'emissions_kgCO2e']
    
    return distance_df


def compute_hq_distances(
    hq_df,
    circuits_df
):
    """Compute distances from team HQs to all circuits."""
    print("Computing HQ-to-circuit distances...")
    
    # Create all pairs
    hq_merge_df = pd.merge(
        hq_df, circuits_df, how='cross',
        suffixes=('_from', '_to')
    )
    
    # Compute distances and adjust for European road travel
    hq_merge_df = compute_pairwise_distances(
        hq_df, circuits_df,
        id_col_a='team_id',
        id_col_b='circuit_id'
    )
    
    # Determine transport mode
    hq_merge_df['transport_mode'] = determine_transport_mode(
        hq_merge_df['continent_from'],
        hq_merge_df['continent_to']
    )
    
    # Calculate emissions
    hq_merge_df['emissions_kgCO2e'] = calculate_emissions(
        hq_merge_df['distance_km'],
        hq_merge_df['transport_mode']
    )
    
    # Select and rename columns
    hq_merge_df = hq_merge_df[[
        'team_id', 'circuit_id',
        'distance_km', 'transport_mode', 'emissions_kgCO2e'
    ]]
    hq_merge_df.columns = ['from', 'to', 'distance_km', 'transport_mode', 'emissions_kgCO2e']
    
    return hq_merge_df


def main():
    """Execute distance processing pipeline."""
    parser = argparse.ArgumentParser(
        description="Process F1 circuit and HQ distances and emissions"
    )
    parser.add_argument(
        "--raw-circuits",
        default="data/raw/circuits.csv",
        help="Path to raw circuits CSV"
    )
    parser.add_argument(
        "--raw-hq",
        default="data/raw/hq.csv",
        help="Path to raw HQ CSV"
    )
    parser.add_argument(
        "--output-circuits",
        default="data/processed/circuits.csv",
        help="Path to output processed circuits CSV"
    )
    parser.add_argument(
        "--output-hq",
        default="data/processed/hq.csv",
        help="Path to output processed HQ CSV"
    )
    parser.add_argument(
        "--output-distances",
        default="data/processed/distances.csv",
        help="Path to output distances CSV"
    )
    parser.add_argument(
        "--output-sundays",
        default="data/processed/sundays_2026.csv",
        help="Path to output Sundays calendar CSV"
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2026,
        help="Year to generate Sundays for"
    )
    
    args = parser.parse_args()
    
    # Load raw data
    print("Loading raw data...")
    circuits_df = load_circuits_raw(args.raw_circuits)
    hq_df = load_hq_raw(args.raw_hq)
    
    # Geocode circuits
    circuits_df = geocode_circuits(circuits_df)
    output_path = Path(args.output_circuits)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    circuits_df.to_csv(args.output_circuits, index=False)
    print(f"Saved {args.output_circuits}")
    
    # Geocode HQs
    hq_df = geocode_hq(hq_df)
    output_path = Path(args.output_hq)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    hq_df.to_csv(args.output_hq, index=False)
    print(f"Saved {args.output_hq}")
    
    # Compute circuit-to-circuit distances
    circuit_distances = compute_circuit_distances(circuits_df)
    
    # Compute HQ-to-circuit distances
    hq_distances = compute_hq_distances(hq_df, circuits_df)
    
    # Combine and save
    distances_df = pd.concat([circuit_distances, hq_distances], ignore_index=True)
    output_path = Path(args.output_distances)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    distances_df.to_csv(args.output_distances, index=False)
    print(f"Saved {args.output_distances}")
    
    # Generate Sundays calendar
    print(f"Generating Sundays for {args.year}...")
    sundays_df = generate_sundays(args.year)
    output_path = Path(args.output_sundays)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sundays_df.to_csv(args.output_sundays, index=False)
    print(f"Saved {args.output_sundays}")
    
    print(f"\nDone! Generated {len(distances_df)} distance records")
    print(distances_df.head())
    
    return distances_df


if __name__ == "__main__":
    try:
        result = main()
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
