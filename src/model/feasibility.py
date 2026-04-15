"""Feasibility matrix construction for climate and cultural constraints."""

import numpy as np
import pandas as pd
from src.parameters import MIN_TEMP_F, MAX_TEMP_F, MAX_PRECIP_IN


def build_feasibility_matrix(
    climate_df, festivals_df, 
    circuits, weeks, summer_break_weeks, 
    min_temp = MIN_TEMP_F, max_temp = MAX_TEMP_F, max_precip = MAX_PRECIP_IN
):
    
    """Build feasibility matrix for circuit-weekend combinations"""

    # Initialize feasibility matrix
    feasible_df = pd.DataFrame(
        np.zeros((len(weeks), len(circuits))),
        columns=circuits,
        index=weeks
    )
    
    # Index climate data by week number
    climate_indexed = climate_df.copy()
    climate_indexed.index = climate_indexed['week_num'].astype(int).tolist()
    
    # Evaluate feasibility for each circuit
    for circuit in circuits:
        temp_col   = f"{circuit}_avg_temp"
        precip_col = f"{circuit}_avg_precip"
        
        # Check temperature and precipitation constraints
        ok_temp   = climate_indexed[temp_col].between(min_temp, max_temp)
        ok_precip = climate_indexed[precip_col] < max_precip
        
        feasible_df.loc[ok_temp & ok_precip, circuit] = 1
    
    # Mark summer break weeks as infeasible
    for week in summer_break_weeks:
        if week in feasible_df.index:
            feasible_df.loc[week, :] = 0
    
    # Mark festival dates as infeasible
    for _, row in festivals_df.iterrows():
        week_num   = row['week_num']
        circuit_id = row['circuit_id']
        
        if week_num in feasible_df.index and circuit_id in feasible_df.columns:
            feasible_df.loc[week_num, circuit_id] = 0
    
    return feasible_df


def prepare_feasibility_for_gamspy(feasible_df):
    """Convert feasibility DataFrame to GAMSPy parameter format"""
    return feasible_df.stack().reset_index().values.tolist()
