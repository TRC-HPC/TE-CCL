
from ortools.linear_solver import pywraplp
import gurobipy as gp
from gurobipy import GRB
import numpy as np
import cProfile
import pstats
M = 1000

def SOS1(_vars,solver):
    
    bools = [solver.NumVar(0,1,name = "b") for i in range(len(_vars))]
    
    for var,_bool in zip(_vars,bools):
        solver.Add(var <= M * _bool)

    solver.Add(solver.Sum(bools) == 1)



def convert_gurobi_to_ortools_2(gurobi_model, params):
    """Converts a Gurobi MILP model to an OR-Tools model."""
    # Initialize OR-Tools solver
    solver = pywraplp.Solver.CreateSolver('SCIP')

    print(f'Time limit is {params.time_limit}')
    solver.SetTimeLimit(1000 * params.time_limit)

    #solver = cp_model.CpModel()
    # Mapping of Gurobi variables to OR-Tools variables
    ortools_vars = {}
    # Convert variables
    

    print("b3")
    for v in gurobi_model.getVars():
        if v.vtype == GRB.CONTINUOUS:
            ortools_var = solver.NumVar(v.lb, v.ub, v.VarName)
        elif v.vtype == GRB.INTEGER:  # Integer or Binary
            ortools_var = solver.IntVar(v.lb, v.ub, v.VarName)
        else:
            assert False
            ortools_var = solver.NewBoolVar(v.lb,v.ub,v.VarName)
        ortools_vars[v.VarName] = ortools_var
    
    print("b4")
    _vars = gurobi_model.getVars()
    names = gurobi_model.getAttr("VarName",_vars)
    varToName = {var:name for var,name in zip(_vars,names)}

    # Convert constraints
    for c in gurobi_model.getConstrs():
        row = gurobi_model.getRow(c)
        row_vars = [row.getVar(i) for i in range(row.size())]
        row_coeffs = [row.getCoeff(i) for i in range(row.size())]
        expr = sum(coeff * ortools_vars[varToName[var]] for var,coeff in zip(row_vars,row_coeffs))

        if c.Sense == GRB.LESS_EQUAL:
            solver.Add(expr <= c.RHS)
        elif c.Sense == GRB.GREATER_EQUAL:
            solver.Add(expr >= c.RHS)
        elif c.Sense == GRB.EQUAL:
            solver.Add(expr == c.RHS)
    print("B4")
    for c in gurobi_model.getGenConstrs():
        if c.GenConstrType == gp.GRB.GENCONSTR_MAX:   
            var, operands, _= gurobi_model.getGenConstrMax(c)

            
            var = ortools_vars[var.VarName]
            operands = [ortools_vars[v.VarName] for v in operands]

            S = [solver.NumVar(0,M-1, name = "n") for _ in range(len(operands))]
            B = [solver.NumVar(0,1,name = "b")]

            for s,b in zip(S,B):
                SOS1([s,b],solver)

            for i in range(len(operands)):
                solver.Add(var == operands[i] + S[i])

            solver.Add(solver.Sum(B) == 1)
        if c.GenConstrType == gp.GRB.GENCONSTR_MIN:   
            var, operands, _= gurobi_model.getGenConstrMin(c)

            var = ortools_vars[var.VarName]
            operands = [ortools_vars[v.VarName] for v in operands]

            S = [solver.NumVar(0,M-1, name = "n") for _ in range(len(operands))]
            B = [solver.NumVar(0,1,name = "b")]

            for s,b in zip(S,B):
                SOS1([s,b],solver)

            for i in range(len(operands)):
                solver.Add(var == operands[i] - S[i])

            solver.Add(solver.Sum(B) == 1)    # Convert objective function
    gurobi_obj = gurobi_model.getObjective()
    
    #ortools_obj_expr = sum(gurobi_obj.getCoeff(v) * ortools_vars[v.VarName] for v in gurobi_model.getVars())
    ortools_obj_expr = sum(gurobi_obj.getCoeff(i) * ortools_vars[gurobi_obj.getVar(i).VarName] for i in range(gurobi_obj.size()))

    if gurobi_model.ModelSense == GRB.MINIMIZE:
        solver.Minimize(ortools_obj_expr)
    else:
        solver.Maximize(ortools_obj_expr)
    
    return solver

# Example usage
# gurobi_model = gp.read("example_model.mps")  # Load a Gurobi model
# ortools_solver = convert_gurobi_to_ortools(gurobi_model)
if __name__ == "__main__":
    t = np.zeros((261,261,261,1,12)).tolist()


    g = gp.Model()
    x = g.addVar(0,10,vtype = GRB.CONTINUOUS, name = "X")
    y = g.addVar(0,10,vtype = GRB.CONTINUOUS, name = "y")
    z = g.addVar(0,10,vtype=GRB.INTEGER,name="z")
    #g.addConstr(x + y <= 5)
    g.addConstr(z == gp.min_(x,y))
    #g.addConstr(z <= 4)
    g.setObjective(1 - 3 * x + y, GRB.MAXIMIZE)

    g.update()

    ortools = convert_gurobi_to_ortools(g)

    g.optimize()

    for var in g.getVars():
        print(var.VarName,var.X)


    ortools.Solve()
    for variable in ortools.variables():
        print(variable.name,variable.solution_value()) 

def convert_gurobi_to_ortools(gurobi_model, params):
    profiler = cProfile.Profile()
    profiler.enable()

    try:
        convert_gurobi_to_ortools_2(gurobi_model,params)
    finally:
        profiler.disable()
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        stats.print_stats()