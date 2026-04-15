"""Carbon emissions calculations for F1 freight transport."""

import numpy as np
import pandas as pd
from src.parameters import EMISSION_FACTORS_TONNE_KM, AVERAGE_TEAM_FREIGHT_TONNES


def determine_transport_mode(continent_from, continent_to):
    """Determine transport mode based on continents"""
    return np.where(
        (continent_from == 'Europe') & (continent_to == 'Europe'),
        'land',
        'air'
    )


def calculate_emissions(distance_km, transport_mode, freight_tonnes = AVERAGE_TEAM_FREIGHT_TONNES, emission_factors = EMISSION_FACTORS_TONNE_KM):
    """Calculate carbon emissions for freight transport"""
    return (
        distance_km
        * freight_tonnes
        * transport_mode.map(emission_factors)
    )
