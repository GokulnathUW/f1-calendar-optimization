#!/usr/bin/env python3
"""
Main script for F1 calendar optimization.
Runs the complete optimization pipeline: data loading, model construction,
solver execution, and results visualization.
"""

import argparse
import sys
from pathlib import Path

from src.model.data_loader import (
    load_model_data,
    create_symmetric_distances,
    extract_race_emissions,
    extract_hq_emissions
)
from src.model.constants import ModelConfig
from src.model.feasibility import build_feasibility_matrix
from src.model.model_builder import F1CalendarModel
from src.model.results import (
    extract_race_schedule,
    build_circuit_coordinates,
    create_race_sequence,
    calculate_total_emissions,
    print_optimization_summary
)
from src.model.visualization import create_race_map


def main():
    """Execute F1 calendar optimization pipeline."""
    parser = argparse.ArgumentParser(
        description="F1 Calendar Optimization Model"
    )
    
    # Data paths
    parser.add_argument(
        "--circuits", default="data/processed/circuits.csv",
        help="Path to processed circuits CSV"
    )
    parser.add_argument(
        "--distances", default="data/processed/distances.csv",
        help="Path to processed distances CSV"
    )
    parser.add_argument(
        "--climate", default="data/processed/climate.csv",
        help="Path to processed climate CSV"
    )
    parser.add_argument(
        "--festivals", default="data/processed/festivals.csv",
        help="Path to processed festivals CSV"
    )
    parser.add_argument(
        "--hq", default="data/processed/hq.csv",
        help="Path to processed headquarters CSV"
    )
    
    # Solver options
    parser.add_argument(
        "--solver", default="gurobi",
        help="Optimization solver (default: gurobi)"
    )
    parser.add_argument(
        "--time-limit", type=int, default=300,
        help="Solver time limit in seconds (default: 300)"
    )
    parser.add_argument(
        "--gap", type=float, default=0.05,
        help="Relative optimality gap tolerance (default: 0.05)"
    )
    
    # Model configuration
    parser.add_argument(
        "--first-race", default="AUS",
        help="Opening race circuit ID (default: AUS)"
    )
    parser.add_argument(
        "--last-race", default="ABD",
        help="Closing race circuit ID (default: ABD)"
    )
    parser.add_argument(
        "--break-start", type=int, default=24,
        help="Summer break start week (default: 24)"
    )
    parser.add_argument(
        "--break-end", type=int, default=26,
        help="Summer break end week (default: 26)"
    )
    parser.add_argument(
        "--races-before-break", type=int, default=14,
        help="Number of races before break (default: 14)"
    )
    
    # Output options
    parser.add_argument(
        "--output-dir", default="data/output",
        help="Directory for output files"
    )
    parser.add_argument(
        "--save-map", action="store_true",
        help="Save race map visualization"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("F1 CALENDAR OPTIMIZATION")
    print("=" * 60)
    
    # Load data
    print("\n1. Loading data...")
    data = load_model_data(
        circuits_path=args.circuits,
        distances_path=args.distances,
        climate_path=args.climate,
        festivals_path=args.festivals,
        hq_path=args.hq
    )
    
    circuits_df = data['circuits']
    distances_df = data['distances']
    climate_df = data['climate']
    festivals_df = data['festivals']
    teams_df = data['teams']
    
    print(f"   Loaded {len(circuits_df)} circuits, {len(teams_df)} teams")
    print(f"   Loaded {len(distances_df)} distance records")
    print(f"   Loaded {len(climate_df)} climate records")
    
    # Create symmetric distances
    print("\n2. Preprocessing data...")
    symmetric_distances = create_symmetric_distances(distances_df)
    
    # Extract data
    teams = teams_df["team_id"].tolist()[:-1]
    circuits = circuits_df["circuit_id"].tolist()
    weeks = climate_df['week_num'].astype(int).tolist()
    summer_break_weeks = climate_df.loc[
        climate_df['week_num'].between(args.break_start, args.break_end),
        'week_num'
    ].astype(int).tolist()
    
    race_emissions_df = extract_race_emissions(symmetric_distances, circuits)
    hq_emissions_df = extract_hq_emissions(symmetric_distances, teams, circuits)
    
    print(f"   Circuits: {len(circuits)}")
    print(f"   Teams: {len(teams)}")
    print(f"   Weeks: {len(weeks)}")
    print(f"   Summer break weeks: {summer_break_weeks}")
    
    # Build feasibility matrix
    print("\n3. Building feasibility matrix...")
    feasibility_df = build_feasibility_matrix(
        climate_df=climate_df,
        festivals_df=festivals_df,
        circuits=circuits,
        weeks=weeks,
        summer_break_weeks=summer_break_weeks
    )
    feasible_count = feasibility_df.sum().sum()
    total_count = len(weeks) * len(circuits)
    print(f"   Feasible combinations: {feasible_count:.0f}/{total_count} "
          f"({100*feasible_count/total_count:.1f}%)")
    
    # Configure model
    print("\n4. Configuring model...")
    config = ModelConfig(
        break_start_week=args.break_start,
        break_end_week=args.break_end,
        races_before_break=args.races_before_break,
        first_race=args.first_race,
        last_race=args.last_race,
        solver=args.solver,
        time_limit=args.time_limit,
        optimality_gap=args.gap
    )
    
    # Build and solve model
    print("\n5. Building optimization model...")
    model = F1CalendarModel(config)
    model.build(
        circuits=circuits,
        teams=teams,
        weeks=weeks,
        summer_break_weeks=summer_break_weeks,
        race_emissions_df=race_emissions_df,
        hq_emissions_df=hq_emissions_df,
        feasibility_df=feasibility_df
    )
    
    print("\n6. Solving model...")
    result = model.solve()
    
    # Extract and display results
    print("\n7. Extracting results...")
    route_df, schedule_df = extract_race_schedule(model)
    
    sequence_df = create_race_sequence(
        route_df=route_df,
        schedule_df=schedule_df,
        circuits_df=circuits_df,
        climate_df=climate_df
    )
    
    emissions = calculate_total_emissions(model, route_df, schedule_df, config)
    
    # Print summary
    print_optimization_summary(
        sequence_df=sequence_df,
        emissions=emissions,
        solver_status=result.solver_status,
        solve_time=result.solve_time
    )
    
    # Save outputs
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save sequence
    sequence_path = output_dir / "optimized_calendar.csv"
    sequence_df.to_csv(sequence_path, index=False)
    print(f"\nSaved optimized calendar to {sequence_path}")
    
    # Save visualization
    if args.save_map:
        map_path = output_dir / "race_map.html"
        create_race_map(
            sequence_df=sequence_df,
            circuits_df=circuits_df,
            output_path=str(map_path)
        )
        print(f"Saved race map to {map_path}")
    
    return sequence_df, emissions


if __name__ == "__main__":
    try:
        result = main()
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
