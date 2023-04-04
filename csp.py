from ortools.sat.python import cp_model

def expandir_array(arr, cant, mx):
    res = []
    for i in range(len(arr)):
        if cant[i] == -1:
            r = mx
        else:
            r = cant[i]

        for j in range(r):
            res.append(arr[i])
    return res

def OptimizarCortes(MedidasRequeridas, CantidadesReq, TramosStock, CantidadesTramos, despizq, despder, sawwidth):
    MedidasReq = expandir_array(MedidasRequeridas, CantidadesReq, 0)
    Tramos = expandir_array(TramosStock, CantidadesTramos, len(MedidasReq))
    di = expandir_array(despizq,CantidadesTramos,len(MedidasReq))
    dd = expandir_array(despder,CantidadesTramos,len(MedidasReq))

    # Crear el modelo
    model = cp_model.CpModel()

    # Creamos las variables de los tramos usados, 1 usado 0 no usado
    T = [model.NewIntVar(0, 1, f"T{i}") for i in range(len(MedidasReq))]

    # Creamos las variables de los cortes de cada tramo
    # Esta variable Cij nos dice si la medida requerida j se cortará en el tramo i
    C = [[model.NewIntVar(0, 1, f"C{i}{j}")for j in range(
        len(MedidasReq))]for i in range(len(Tramos))]

    # Variable de desperdicio
    desperdicio = model.NewIntVar(0, sum(Tramos), "desperdicio")

    # Definimos la restricción de que los cortes deben ser menores o iguales a la longitud del tramo seleccionado, una restricción por tramo
    for i in range(len(Tramos)):
        zi = 0
        zd = 0
        if di[i] > 0:
            zi = 1
        if dd[i] > 0:
            zd = 1
        #Cantidad de cortes n-1*saw + 1*sawi + 1*sawd + despizq + desp 
        if zi > 0 or zd > 0:
            model.Add(sum([C[i][j] * MedidasReq[j] + C[i][j] * saw
                       for j in range(len(MedidasReq))]) - saw + zd*saw + zi*saw + di[i] + dd[i]
                        <= T[i] * Tramos[i])
        else:
            model.Add(sum([C[i][j] * MedidasReq[j]
                       for j in range(len(MedidasReq))]) <= T[i] * Tramos[i])

    # Definimos la restricción de que cada medida debe seleccionarse 1 y sólo una vez
    for j in range(len(MedidasReq)):
        model.Add(sum([C[i][j]
                       for i in range(len(Tramos))]) == 1)

    # restricción de desperdicio
    model.Add(desperdicio == sum([T[i] * Tramos[i]
                                  for i in range(len(Tramos))]) - sum(MedidasReq))

    # Minimizar el desperdicio
    model.Minimize(desperdicio)

    # Crear el solver y resolver el modelo
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    #UNKNOWN = cp_model_pb2.UNKNOWN
    #MODEL_INVALID = cp_model_pb2.MODEL_INVALID
    #FEASIBLE = cp_model_pb2.FEASIBLE
    #INFEASIBLE = cp_model_pb2.INFEASIBLE
    #OPTIMAL = cp_model_pb2.OPTIMAL

    Tramos_necesarios = [] 
    if status == cp_model.OPTIMAL:
        for i in range(len(Tramos)):
            if solver.Value(T[i]) == 1:
                cortes = []
                for j in range(len(MedidasReq)):
                    if solver.Value(C[i][j]) == 1:
                        cortes.append(MedidasReq[j])
                Tramos_necesarios.append([Tramos[i], cortes])

 

    return status, Tramos_necesarios, solver.Value(desperdicio)
    # tramos[número de tramo][0: medida del tramo, 1: array cortes][número de corte (medida)]


# Definir las medidas requeridas
MR = [3400, 2000, 4000]  # Medidas
CR = [2, 1, 1]  # Cantidades

# Definir las longitudes de los tramos disponibles, cantidades de cada tramo, despunte izq., despunte der.
TR = [6100, 5000,7000]
CT = [2, 1, 1]
DI = [0, 0, 0]
DD = [0, 0, 0]

saw = 0

res, tramos, desperdicio = OptimizarCortes(MR, CR, TR, CT, DI, DD, saw)

if res == cp_model.OPTIMAL:
    print("Se encontró una solución optima:")
    print(tramos)
    print(f"Desperdicio: {desperdicio} mm")