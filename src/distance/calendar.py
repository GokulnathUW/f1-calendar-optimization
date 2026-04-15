"""Calendar utilities for generating race dates."""

import pandas as pd


def generate_sundays(year = 2026):
    """Generate all Sundays of a given year"""
    dates = pd.date_range(
        start=f'{year}-01-01',
        end=f'{year}-12-31',
        freq='W-SUN'
    )
    
    return pd.DataFrame({
        'race_date': dates,
        'week_num': dates.isocalendar().week,
        'month': dates.month
    })
