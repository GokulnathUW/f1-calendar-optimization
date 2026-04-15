"""
F1 Calendar Optimization Model using GAMSPy.
Implements a Traveling Salesman Problem (TSP) formulation to minimize
carbon emissions from freight logistics across the F1 race calendar.
"""

from src.model.data_loader import load_model_data, create_symmetric_distances
from src.model.constants import ModelConfig
from src.model.feasibility import build_feasibility_matrix
from src.model.model_builder import F1CalendarModel

__all__ = [
    "load_model_data",
    "create_symmetric_distances",
    "ModelConfig",
    "build_feasibility_matrix",
    "F1CalendarModel",
]
