"""Results extraction and processing utilities."""

import pandas as pd
import numpy as np
from typing import Dict, Optional


def extract_race_schedule(model):
    """Extract optimized race schedule from model variables"""
    x_values = model.get_variable_values('x')
    y_values = model.get_variable_values('y')
    
    # Filter active connections (x[i,j] > 0.5)
    route_df = x_values[x_values['level'] > 0.5].copy()
    
    # Filter race assignments (y[i,t] > 0.5)
    schedule_df = y_values[y_values['level'] > 0.5].copy()
    
    return route_df, schedule_df


def build_circuit_coordinates(circuits_df):
    """Build dictionary of circuit coordinates"""
    return dict(
        zip(
            circuits_df['circuit_id'],
            zip(circuits_df['latitude'], circuits_df['longitude'])
        )
    )


def create_race_sequence(route_df, schedule_df, circuits_df, climate_df
):
    """Create complete race sequence with dates and coordinates"""
    # Merge schedule with circuit info
    sequence_df = schedule_df.merge(
        circuits_df[['circuit_id', 'circuit_name', 'latitude', 'longitude', 'city', 'country']],
        left_on='circuit_id',
        right_on='circuit_id',
        how='left'
    )
    
    # Merge with climate data to get actual dates
    climate_indexed = climate_df.copy()
    climate_indexed['week_num'] = climate_indexed['week_num'].astype(int)
    
    sequence_df = sequence_df.merge(
        climate_indexed[['week_num', 'race_date']],
        left_on='weekend',
        right_on='week_num',
        how='left'
    )
    
    # Sort by weekend
    sequence_df = sequence_df.sort_values('weekend').reset_index(drop=True)
    sequence_df['position'] = range(1, len(sequence_df) + 1)
    
    return sequence_df


def calculate_total_emissions(model, route_df, schedule_df, config):
    """Calculate breakdown of total emissions"""
    # Get objective value from model
    total_objective = model.container.getVariable('objective').records
    
    emissions_breakdown = {'total_kgCO2e': total_objective['level'].values[0] if len(total_objective) > 0 else None}
    
    return emissions_breakdown


def print_optimization_summary(sequence_df, emissions, solver_status, solve_time):
    """Print summary of optimization results"""
    print("=" * 60)
    print("F1 CALENDAR OPTIMIZATION RESULTS")
    print("=" * 60)
    print(f"\nSolver Status: {solver_status}")
    print(f"Solve Time: {solve_time:.2f} seconds")
    print(f"\nTotal Emissions: {emissions.get('total_kgCO2e', 'N/A'):,.0f} kg CO2e")
    print(f"Number of Races: {len(sequence_df)}")
    
    print("\n" + "-" * 60)
    print("RACE SEQUENCE:")
    print("-" * 60)
    
    for _, row in sequence_df.iterrows():
        print(f"{row['position']:2d}. {row['circuit_id']:10s} | "
              f"{row['circuit_name']:35s} | "
              f"Week {row['weekend']:2d} | "
              f"{row['race_date']}")
    
    print("=" * 60)
