from ortools.sat.python import cp_model

def expanse_array(a, mx):
    res = []
    for i in range(len(a)):
        q = a[i]["quantity"]
        if q == -1:
            r = mx
        else:
            r = q
        l = a[i]["length"]
        
        for j in range(r):
            if mx == 0:
                res.append({"length":l})
            else:
                lt = a[i]["ltrim"]
                rt = a[i]["rtrim"]                
                res.append({"length":l, "ltrim":lt,"rtrim":rt})
    return res

def optimize(sawwidth, cuts, bars):
    c = expanse_array(cuts,0)    
    b = expanse_array(bars,len(c))
    cn = len(c)  #cut number
    bn = len(b)  #bar number
    
    # Create model
    model = cp_model.CpModel()

    # Create bar variables
    bv = [model.NewIntVar(0, 1, f"B{i}") for i in range(bn)]

    # Create the cut varibles for each bar
    # The Ci_j var tell us if a j cut is included in the i bar
    cv = [[model.NewIntVar(0, 1, f"C{i}_{j}")for j in range(cn)]for i in range(bn)]

    # Create the waste var
    bl = sum([b[i]["length"] for i in range(bn)])    
    waste = model.NewIntVar(0, bl, "waste")

    # Definimos la restricción de que los cortes deben ser menores o iguales a la longitud del tramo seleccionado, una restricción por tramo
    for i in range(bn):
        lti = 0
        rti = 0
        if b[i]["ltrim"] > 0:
            lti = 1
        if b[i]["rtrim"] > 0:
            rti = 1
        #Cantidad de cortes n-1*saw + 1*sawi + 1*sawd + despizq + desp 
        if lti > 0 or rti > 0:
            model.Add(sum([cv[i][j] * c[j]["length"] + cv[i][j] * sawwidth
                       for j in range(cn)]) - sawwidth + lti*sawwidth + rti*sawwidth + b[i]["ltrim"] + b[i]["rtrim"]
                        <= bv[i] * b[i]["length"])
        else:
            model.Add(sum([cv[i][j] * c[j]["length"]
                       for j in range(cn)]) <= bv[i] * b[i]["length"])
    
    # Definimos la restricción de que cada medida debe seleccionarse 1 y sólo una vez
    for j in range(cn):
        model.Add(sum([cv[i][j]
                       for i in range(bn)]) == 1)
    
    # restricción de desperdicio
    model.Add(waste == sum([bv[i] * b[i]["length"]
                                  for i in range(bn)]) - sum([c[j]["length"] for j in range(cn)]))

    # Minimizar el desperdicio
    model.Minimize(waste)

    # Crear el solver y resolver el modelo
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    #UNKNOWN = cp_model_pb2.UNKNOWN
    #MODEL_INVALID = cp_model_pb2.MODEL_INVALID
    #FEASIBLE = cp_model_pb2.FEASIBLE
    #INFEASIBLE = cp_model_pb2.INFEASIBLE
    #OPTIMAL = cp_model_pb2.OPTIMAL

    barlist = [] 
    if status == cp_model.OPTIMAL:
        for i in range(bn):
            if solver.Value(bv[i]) == 1:
                cutlist = []
                for j in range(cn):
                    if solver.Value(cv[i][j]) == 1:
                        cutlist.append(c[j]["length"])
                barlist.append({"length":b[i]["length"],"cuts":cutlist})

    return status, barlist, solver.Value(waste)


