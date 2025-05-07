from ortools.linear_solver import pywraplp
import gurobipy as gp

from ortools.linear_solver import pywraplp
import gurobipy as gp
from gurobipy import GRB

def convert_gurobi_to_ortools(gurobi_model):
    """Converts a Gurobi MILP model to an OR-Tools model."""
    # Initialize OR-Tools solver
    solver = pywraplp.Solver.CreateSolver('SCIP')

    # Mapping of Gurobi variables to OR-Tools variables
    ortools_vars = {}

    # Convert variables
    for v in gurobi_model.getVars():
        if v.vtype == GRB.CONTINUOUS:
            ortools_var = solver.NumVar(v.lb, v.ub, v.VarName)
        else:  # Integer or Binary
            ortools_var = solver.IntVar(v.lb, v.ub, v.VarName)
        ortools_vars[v.VarName] = ortools_var

    # Convert constraints
    for c in gurobi_model.getConstrs():
        expr = sum(gurobi_model.getCoeff(c, v) * ortools_vars[v.VarName] for v in gurobi_model.getVars())
        if c.Sense == GRB.LESS_EQUAL:
            solver.Add(expr <= c.RHS)
        elif c.Sense == GRB.GREATER_EQUAL:
            solver.Add(expr >= c.RHS)
        elif c.Sense == GRB.EQUAL:
            solver.Add(expr == c.RHS)

    # Convert objective function
    gurobi_obj = gurobi_model.getObjective()
    ortools_obj_expr = sum(gurobi_obj.getCoeff(v) * ortools_vars[v.VarName] for v in gurobi_model.getVars())

    if gurobi_model.ModelSense == GRB.MINIMIZE:
        solver.Minimize(ortools_obj_expr)
    else:
        solver.Maximize(ortools_obj_expr)

    return solver

# Example usage
# gurobi_model = gp.read("example_model.mps")  # Load a Gurobi model
# ortools_solver = convert_gurobi_to_ortools(gurobi_model)

    
