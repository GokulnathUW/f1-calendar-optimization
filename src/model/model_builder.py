"""Main F1 Calendar optimization model builder.

Encapsulates GAMSPy model construction including sets, variables,
equations, objective function, and solver execution.
"""

import numpy as np
import pandas as pd
import gamspy as gp
from typing import Optional

from src.model.constants import ModelConfig
from src.model.feasibility import prepare_feasibility_for_gamspy


class F1CalendarModel:
    """GAMSPy-based F1 calendar optimization model."""
    
    def __init__(self, config = None):
        """Initialize model container and configuration."""
        self.config    = config or ModelConfig()
        self.container = gp.Container()
        gp.set_options({'USE_PY_VAR_NAME': 'yes'})
        
        # Model components
        self.sets       = {}
        self.parameters = {}
        self.variables  = {}
        self.equations  = {}
        self.model      = None
    
    def build_sets(self, circuits, teams, weeks, summer_break_weeks):
        """Define GAMSPy sets for the model."""
        self.sets['Weekend'] = gp.Set(
            self.container, records=weeks, name='Weekend'
        )
        self.sets['SummerBreak'] = gp.Set(
            self.container, domain=[self.sets['Weekend']],
            records=summer_break_weeks, name='SummerBreak'
        )
        self.sets['Team'] = gp.Set(
            self.container, records=teams, name='Team'
        )
        self.sets['Circuit'] = gp.Set(
            self.container, records=circuits, name='Circuit'
        )
        
        # Aliases
        self.sets['i'] = gp.Alias(
            self.container, alias_with=self.sets['Circuit'], name='i'
        )
        self.sets['j'] = gp.Alias(
            self.container, alias_with=self.sets['Circuit'], name='j'
        )
        self.sets['t'] = gp.Alias(
            self.container, alias_with=self.sets['Weekend'], name='t'
        )
    
    def build_parameters(self, race_emissions_df, hq_emissions_df, feasibility_records):
        """Define GAMSPy parameters for emissions and feasibility."""
        # Race-to-race emissions
        self.parameters['r_emissions'] = gp.Parameter(
            self.container,
            domain=[self.sets['Circuit'], self.sets['Circuit']],
            records=race_emissions_df,
            description="emissions between races in kgCO2e"
        )
        
        # HQ-to-race emissions
        self.parameters['hq_emissions'] = gp.Parameter(
            self.container,
            domain=[self.sets['Team'], self.sets['Circuit']],
            records=hq_emissions_df,
            description="emissions from HQ to race in kgCO2e"
        )
        
        # Feasibility matrix
        self.parameters['feasible_dates'] = gp.Parameter(
            self.container,
            domain=[self.sets['Weekend'], self.sets['Circuit']],
            records=feasibility_records,
            description="feasibility of holding race on weekend (1 if feasible, 0 otherwise)"
        )
        
        # Set summer break weeks to infeasible
        self.parameters['feasible_dates'][
            self.sets['SummerBreak'], self.sets['Circuit']
        ] = 0
        
        # Break configuration
        self.parameters['first_set'] = gp.Parameter(
            self.container,
            records=self.config.races_before_break,
            description='Number of races before the summer break'
        )
        self.parameters['break_start_date'] = gp.Parameter(
            self.container,
            records=np.array(self.config.break_start_week),
            description='Weekend where break begins'
        )
        self.parameters['break_end_date'] = gp.Parameter(
            self.container,
            records=np.array(self.config.break_end_week),
            description='Weekend where break ends'
        )
    
    def build_variables(self, circuits):
        """Define GAMSPy decision variables."""
        # x[i,j]: 1 if race i scheduled immediately before race j
        self.variables['x'] = gp.Variable(
            self.container, type='binary',
            domain=[self.sets['Circuit'], self.sets['Circuit']],
            description="1 if race i is scheduled immediately before j"
        )
        
        # y[i,t]: 1 if race i scheduled on weekend t
        self.variables['y'] = gp.Variable(
            self.container, type='binary',
            domain=[self.sets['Circuit'], self.sets['Weekend']],
            description='1 if race i is scheduled on weekend t'
        )
        
        # z[i,j]: 1 if race i is pre-break and race j is post-break
        self.variables['z'] = gp.Variable(
            self.container, type='binary',
            domain=[self.sets['i'], self.sets['j']],
            description="1 if race i on pre-break weekend and race j on post-break weekend"
        )
        
        # u[i]: Position of race i in calendar sequence
        self.variables['u'] = gp.Variable(
            self.container, type='positive',
            domain=[self.sets['Circuit']],
            description="Position of race in the calendar sequence"
        )
        
        # gap[t]: 1 if no race at week t
        self.variables['gap'] = gp.Variable(
            self.container, type='binary',
            domain=[self.sets['t']],
            description="1 if no race at week t"
        )
        
        # triple_header[t]: 1 if week t starts a triple header
        self.variables['triple_header'] = gp.Variable(
            self.container, type='binary',
            domain=[self.sets['t']],
            description="1 if week t starts a triple header"
        )
        
        # Fix self-loops to 0
        self.variables['x'].fx[self.sets['i'], self.sets['i']] = 0
        
        # Set bounds for u variable
        self.variables['u'].lo[self.sets['Circuit']] = 2
        self.variables['u'].up[self.sets['Circuit']] = gp.Card(self.sets['Circuit'])
        
        # Fix first and last race positions
        self.variables['u'].fx[self.config.first_race] = 1
        self.variables['u'].fx[self.config.last_race] = gp.Card(self.sets['Circuit'])
    
    def build_equations(self):
        """Define all model constraints."""
        circuits = self.sets['Circuit'].records
        first_ord = circuits.index(self.config.first_race) + 1
        last_ord = circuits.index(self.config.last_race) + 1
        
        # Assignment constraints
        self.equations['assign1'] = gp.Equation(
            self.container, domain=[self.sets['j']],
            description='Each circuit has exactly one predecessor'
        )
        self.equations['assign1'][self.sets['j']] = (
            gp.Sum(self.sets['i'], self.variables['x'][self.sets['i'], self.sets['j']]) == 1
        )
        
        self.equations['assign2'] = gp.Equation(
            self.container, domain=[self.sets['i']],
            description='Each circuit has exactly one successor'
        )
        self.equations['assign2'][self.sets['i']] = (
            gp.Sum(self.sets['j'], self.variables['x'][self.sets['i'], self.sets['j']]) == 1
        )
        
        self.equations['assign3'] = gp.Equation(
            self.container, domain=[self.sets['i']],
            description='Each race is held exactly once'
        )
        self.equations['assign3'][self.sets['i']] = (
            gp.Sum(self.sets['t'], self.variables['y'][self.sets['i'], self.sets['t']]) == 1
        )
        
        self.equations['assign4'] = gp.Equation(
            self.container, domain=[self.sets['t']],
            description='Each weekend has at most one race'
        )
        self.equations['assign4'][self.sets['t']] = (
            gp.Sum(self.sets['i'], self.variables['y'][self.sets['i'], self.sets['t']]) <= 1
        )
        
        # MTZ subtour elimination constraints
        self.equations['mtz'] = gp.Equation(
            self.container, domain=[self.sets['i'], self.sets['j']]
        )
        self.equations['mtz'][self.sets['i'], self.sets['j']].where[
            (self.sets['i'].ord != first_ord) &
            (self.sets['j'].ord != first_ord) &
            (self.sets['i'].ord != last_ord)
        ] = (
            self.variables['u'][self.sets['i']] - self.variables['u'][self.sets['j']] + 1 <=
            (gp.Card(self.sets['Circuit']) - 1) * (1 - self.variables['x'][self.sets['i'], self.sets['j']])
        )
        
        # Feasibility constraint
        self.equations['feasibility'] = gp.Equation(
            self.container, domain=[self.sets['i'], self.sets['t']],
            description='Race can be held only if the weekend is feasible'
        )
        self.equations['feasibility'][self.sets['i'], self.sets['t']] = (
            self.variables['y'][self.sets['i'], self.sets['t']] <=
            self.parameters['feasible_dates'][self.sets['t'], self.sets['i']]
        )
        
        # Time linking constraint
        self.equations['time_link'] = gp.Equation(
            self.container, domain=[self.sets['i'], self.sets['j']]
        )
        self.equations['time_link'][self.sets['i'], self.sets['j']].where[
            (self.sets['i'].ord != last_ord) | (self.sets['j'].ord != first_ord)
        ] = (
            gp.Sum(self.sets['t'], self.sets['t'].ord * self.variables['y'][self.sets['j'], self.sets['t']]) >=
            gp.Sum(self.sets['t'], self.sets['t'].ord * self.variables['y'][self.sets['i'], self.sets['t']]) +
            self.variables['x'][self.sets['i'], self.sets['j']] -
            (1 - self.variables['x'][self.sets['i'], self.sets['j']]) * gp.Card(self.sets['Weekend'])
        )
        
        # Triple header constraints
        self.equations['triple_header_upper'] = gp.Equation(
            self.container, domain=[self.sets['t']],
            description='If triple_header=1, then must have 3 consecutive races'
        )
        self.equations['triple_header_upper'][self.sets['t']].where[
            self.sets['t'].ord <= gp.Card(self.sets['Weekend']) - 2
        ] = (
            self.variables['triple_header'][self.sets['t']] * 3 <=
            gp.Sum(self.sets['i'], self.variables['y'][self.sets['i'], self.sets['t']]) +
            gp.Sum(self.sets['i'], self.variables['y'][self.sets['i'], self.sets['t'].lead(1)]) +
            gp.Sum(self.sets['i'], self.variables['y'][self.sets['i'], self.sets['t'].lead(2)])
        )
        
        self.equations['triple_header_lower'] = gp.Equation(
            self.container, domain=[self.sets['t']],
            description='If there are 3 consecutive races, triple_header MUST be 1'
        )
        self.equations['triple_header_lower'][self.sets['t']].where[
            self.sets['t'].ord <= gp.Card(self.sets['Weekend']) - 2
        ] = (
            gp.Sum(self.sets['i'], self.variables['y'][self.sets['i'], self.sets['t']]) +
            gp.Sum(self.sets['i'], self.variables['y'][self.sets['i'], self.sets['t'].lead(1)]) +
            gp.Sum(self.sets['i'], self.variables['y'][self.sets['i'], self.sets['t'].lead(2)]) <=
            2 + self.variables['triple_header'][self.sets['t']]
        )
        
        self.equations['triple_header_limit'] = gp.Equation(
            self.container,
            description='Limit on total triple headers'
        )
        self.equations['triple_header_limit'][...] = (
            gp.Sum(self.sets['t'], self.variables['triple_header'][self.sets['t']]) <=
            self.config.max_triple_headers
        )
        
        # Summer break constraints
        self.equations['break_partition'] = gp.Equation(
            self.container,
            description='Exactly 14 races before summer break'
        )
        self.equations['break_partition'][...] = (
            gp.Sum(
                [self.sets['i'], self.sets['t']],
                self.variables['y'][self.sets['i'], self.sets['t']].where[
                    self.sets['t'].ord < self.config.break_start_week
                ]
            ) == self.parameters['first_set']
        )
        
        self.equations['pre_break_race'] = gp.Equation(
            self.container,
            description='Exactly one race on last weekend before break'
        )
        self.equations['pre_break_race'][...] = (
            gp.Sum(self.sets['i'], self.variables['y'][self.sets['i'], self.config.pre_break_week]) == 1
        )
        
        self.equations['post_break_race'] = gp.Equation(
            self.container,
            description='Exactly one race on first weekend after break'
        )
        self.equations['post_break_race'][...] = (
            gp.Sum(self.sets['i'], self.variables['y'][self.sets['i'], self.config.post_break_week]) == 1
        )
        
        # Gap constraints
        self.equations['gap_def'] = gp.Equation(
            self.container, domain=[self.sets['t']]
        )
        self.equations['gap_def'][self.sets['t']] = (
            self.variables['gap'][self.sets['t']] == 1 - gp.Sum(self.sets['i'], self.variables['y'][self.sets['i'], self.sets['t']])
        )
        
        self.equations['max_consecutive'] = gp.Equation(
            self.container, domain=[self.sets['t']]
        )
        self.equations['max_consecutive'][self.sets['t']].where[
            self.sets['t'].ord <= gp.Card(self.sets['Weekend']) - 3
        ] = (
            self.variables['gap'][self.sets['t']] +
            self.variables['gap'][self.sets['t'].lead(1)] +
            self.variables['gap'][self.sets['t'].lead(2)] +
            self.variables['gap'][self.sets['t'].lead(3)] >= 1
        )
        
        # Break arc detection constraints (linearization of z)
        self.equations['z_lin1'] = gp.Equation(
            self.container, domain=[self.sets['i'], self.sets['j']]
        )
        self.equations['z_lin1'][self.sets['i'], self.sets['j']] = (
            self.variables['z'][self.sets['i'], self.sets['j']] <=
            self.variables['x'][self.sets['i'], self.sets['j']]
        )
        
        self.equations['z_lin2'] = gp.Equation(
            self.container, domain=[self.sets['i'], self.sets['j']]
        )
        self.equations['z_lin2'][self.sets['i'], self.sets['j']] = (
            self.variables['z'][self.sets['i'], self.sets['j']] <=
            self.variables['y'][self.sets['i'], self.config.pre_break_week]
        )
        
        self.equations['z_lin3'] = gp.Equation(
            self.container, domain=[self.sets['i'], self.sets['j']]
        )
        self.equations['z_lin3'][self.sets['i'], self.sets['j']] = (
            self.variables['z'][self.sets['i'], self.sets['j']] <=
            self.variables['y'][self.sets['j'], self.config.post_break_week]
        )
        
        self.equations['z_lin4'] = gp.Equation(
            self.container, domain=[self.sets['i'], self.sets['j']]
        )
        self.equations['z_lin4'][self.sets['i'], self.sets['j']] = (
            self.variables['z'][self.sets['i'], self.sets['j']] >=
            self.variables['x'][self.sets['i'], self.sets['j']] +
            self.variables['y'][self.sets['i'], self.config.pre_break_week] +
            self.variables['y'][self.sets['j'], self.config.post_break_week] - 2
        )
    
    def build_objective(self):
        """Build the objective function for minimizing total emissions."""
        team = self.sets['Team']
        i = self.sets['i']
        j = self.sets['j']
        
        first  = self.config.first_race
        last   = self.config.last_race
        t_pre  = self.config.pre_break_week
        t_post = self.config.post_break_week
        ratio  = self.config.team_ratio
        
        total_emissions = (
            # 1. HQ -> FIRST RACE
            gp.Sum(team, self.parameters['hq_emissions'][team, first]) * ratio
            
            # 2. Sum of all consecutive race emissions
            + gp.Sum([i, j], self.parameters['r_emissions'][i, j] * self.variables['x'][i, j]) * 10
            
            # 3. Last race -> HQ
            + gp.Sum(team, self.parameters['hq_emissions'][team, last]) * ratio
            
            # 4. REMOVE emission of break connection
            - gp.Sum([i, j], self.parameters['r_emissions'][i, j] * self.variables['z'][i, j]) * 10
            
            # 5. ADD: pre-break race -> HQ
            + gp.Sum([team, i], self.parameters['hq_emissions'][team, i] * self.variables['y'][i, t_pre]) * ratio
            
            # 6. ADD: HQ -> post-break race
            + gp.Sum([team, j], self.parameters['hq_emissions'][team, j] * self.variables['y'][j, t_post]) * ratio
            
            # 7. REMOVE LAST RACE -> FIRST RACE (loop closure)
            - self.parameters['r_emissions'][last, first] * self.variables['x'][last, first] * 10
        )
        
        return total_emissions
    
    def build(self, circuits, teams, weeks,
              summer_break_weeks, race_emissions_df,
              hq_emissions_df, feasibility_df):
        """Build complete model from data."""
        feasibility_records = prepare_feasibility_for_gamspy(feasibility_df)
        
        self.build_sets(circuits, teams, weeks, summer_break_weeks)
        self.build_parameters(race_emissions_df, hq_emissions_df, feasibility_records)
        self.build_variables(circuits)
        self.equations = {}
        self.build_equations()
        
        # Create model
        objective = self.build_objective()
        self.model = gp.Model(
            self.container,
            name="f1_calendar",
            equations=self.container.getEquations(),
            sense=gp.Sense.MIN,
            problem=gp.Problem.MIP,
            objective=objective
        )
        
        return self.model
    
    def solve(self, solver = None, time_limit = None,
              optimality_gap = None) -> gp.Container:
        """Solve the model and return results."""
        if solver is None:
            solver = self.config.solver
        if time_limit is None:
            time_limit = self.config.time_limit
        if optimality_gap is None:
            optimality_gap = self.config.optimality_gap
        
        result = self.model.solve(
            solver=solver,
            options=gp.Options(
                time_limit=time_limit,
                relative_optimality_gap=optimality_gap
            )
        )
        
        return result
    
    def get_variable_values(self, var_name):
        """Extract variable values after solving."""
        if var_name not in self.variables:
            raise ValueError(f"Variable {var_name} not found")
        
        return self.variables[var_name].records
