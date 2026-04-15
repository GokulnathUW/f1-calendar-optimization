#!/usr/bin/env python3
"""
Main script for processing F1 circuit climate data.
Fetches historical weather data for all circuits and race weekends in 2026,
then saves the processed climate data.
"""

import argparse
import sys
from pathlib import Path

from src.climate.data_loader import load_race_weekends, load_circuits
from src.climate.feasibility import process_circuit_climate_data


def main():
    """Execute climate data processing pipeline."""
    parser = argparse.ArgumentParser(description="Process F1 circuit climate data")
    parser.add_argument(
        "--circuits",
        default="data/processed/circuits.csv",
        help="Path to circuits CSV file"
    )
    parser.add_argument(
        "--sundays",
        default="data/processed/sundays_2026.csv",
        help="Path to sundays CSV file"
    )
    parser.add_argument(
        "--output",
        default="data/processed/climate.csv",
        help="Path to output climate data CSV file"
    )
    parser.add_argument(
        "--circuit-ids",
        nargs="+",
        default=None,
        help="Specific circuit IDs to process (default: all)"
    )
    
    args = parser.parse_args()
    
    # Load data
    print("Loading race weekends data...")
    race_weekends_df, start_date, end_date = load_race_weekends(args.sundays)
    print(f"Season: {start_date} to {end_date}")
    
    print("Loading circuits data...")
    circuits_df = load_circuits(args.circuits)
    print(f"Found {len(circuits_df)} circuits")
    
    # Process climate data
    print("\nFetching historical weather data...")
    climate_df = process_circuit_climate_data(
        race_weekends_df,
        circuits_df,
        circuit_ids=args.circuit_ids
    )
    
    # Save output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    climate_df.to_csv(args.output, index=False)
    print(f"\nClimate data saved to {args.output}")
    
    return climate_df


if __name__ == "__main__":
    try:
        result = main()
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
