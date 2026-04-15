"""Model configuration and constants."""

from dataclasses import dataclass


@dataclass
class ModelConfig:
    """Configuration parameters for the F1 calendar optimization model."""
    
    # Summer break configuration
    break_start_week   = 24        # Week number when break starts
    break_end_week     = 26        # Week number when break ends
    races_before_break = 14        # Number of races before summer break
    
    # Fixed races
    first_race = "AUS"             # Opening race circuit ID
    last_race  = "ABD"             # Closing race circuit ID
    
    # Operational constraints
    max_triple_headers = 3         # Maximum consecutive triple-headers
    
    # Solver configuration
    solver          = "gurobi"     # Optimization solver
    time_limit      = 300          # Solver time limit in seconds
    optimality_gap  = 0.05         # Relative optimality gap tolerance
    
    # Team ratio for emissions calculation
    team_ratio   = 1.0             # Multiplier for team emissions
    team_count   = 10              # Number of F1 teams

    @property
    def pre_break_week(self) -> str:
        """Get week identifier for weekend before break."""
        return str(self.break_start_week - 1)
    
    @property
    def post_break_week(self) -> str:
        """Get week identifier for weekend after break."""
        return str(self.break_end_week + 1)
