"""
Optimización de Cortes 1D con OR-Tools CP-SAT
===============================================
Instalación: pip install ortools matplotlib

Problema de Cutting Stock:
  Tenemos barras de longitud estándar y necesitamos cortar piezas
  de distintas medidas minimizando el número de barras usadas
  y el desperdicio total. CP-SAT garantiza la solución ÓPTIMA.

Ventaja sobre FFD (binpacking):
  - Garantiza optimalidad matemática
  - Reporta brecha de optimalidad (gap)
  - Permite agregar restricciones adicionales (ej. prioridades)
"""

from ortools.sat.python import cp_model
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.cm as cm
import csv
import time

# ─────────────────────────────────────────────
# DATOS DEL PROBLEMA
# ─────────────────────────────────────────────

LONGITUD_BARRA = 6000   # mm
MARGEN_CORTE   = 3      # mm — kerf
MAX_BARRAS     = 20     # cota superior (solver usa las mínimas posibles)
TIEMPO_LIMITE  = 30     # segundos máximos de búsqueda

# Piezas: (longitud_mm, cantidad, nombre)
piezas_requeridas = [
    (2400, 3, "Larguero principal"),
    (1800, 4, "Larguero secundario"),
    (1500, 2, "Travesaño largo"),
    (1200, 5, "Travesaño medio"),
    (900,  6, "Montante"),
    (750,  4, "Refuerzo"),
    (600,  7, "Separador"),
    (400,  5, "Taco"),
    (300,  8, "Escuadra"),
]

# ─────────────────────────────────────────────
# EXPANDIR LISTA DE PIEZAS
# ─────────────────────────────────────────────

lista_piezas = []  # (longitud_con_kerf, nombre, id_original)
for longitud, cantidad, nombre in piezas_requeridas:
    for _ in range(cantidad):
        lista_piezas.append((longitud + MARGEN_CORTE, nombre))

N = len(lista_piezas)   # total de piezas
B = MAX_BARRAS          # número máximo de barras

print("=" * 62)
print("   OPTIMIZACIÓN DE CORTES 1D — OR-Tools CP-SAT")
print("=" * 62)
print(f"\nLongitud barra estándar : {LONGITUD_BARRA} mm")
print(f"Margen de corte (kerf)  : {MARGEN_CORTE} mm")
print(f"Total piezas            : {N}")
print(f"Tiempo límite solver    : {TIEMPO_LIMITE} s")
print(f"\nPiezas requeridas:")
for longitud, cantidad, nombre in piezas_requeridas:
    print(f"  {nombre:<25} {longitud:>5} mm  x{cantidad}")

# ─────────────────────────────────────────────
# MODELO CP-SAT
# ─────────────────────────────────────────────

model  = cp_model.CpModel()
solver = cp_model.CpSolver()

# ── Variables de decisión ──────────────────────────────────────────
#
#   x[i][b] = 1  si la pieza i se corta de la barra b
#   y[b]    = 1  si la barra b es utilizada
#
x = [[model.NewBoolVar(f"x_p{i}_b{b}") for b in range(B)] for i in range(N)]
y = [model.NewBoolVar(f"y_b{b}") for b in range(B)]

# ── Restricciones ─────────────────────────────────────────────────

# 1. Cada pieza se asigna a exactamente UNA barra
for i in range(N):
    model.Add(sum(x[i][b] for b in range(B)) == 1)

# 2. La suma de piezas en cada barra no supera su longitud
for b in range(B):
    model.Add(
        sum(lista_piezas[i][0] * x[i][b] for i in range(N)) <= LONGITUD_BARRA * y[b]
    )

# 3. Simetría: si la barra b no se usa, tampoco se usa b+1
#    (evita soluciones equivalentes y acelera la búsqueda)
for b in range(B - 1):
    model.Add(y[b] >= y[b + 1])

# ── Función objetivo: minimizar barras usadas ─────────────────────
model.Minimize(sum(y))

# ── Configurar solver ────────────────────────────────────────────
solver.parameters.max_time_in_seconds   = TIEMPO_LIMITE
solver.parameters.num_search_workers    = 4   # paralelismo
solver.parameters.log_search_progress   = False

# ─────────────────────────────────────────────
# RESOLVER
# ─────────────────────────────────────────────

print(f"\n{'─'*62}")
print("  Resolviendo...")
t0     = time.time()
status = solver.Solve(model)
t_sol  = time.time() - t0

# ─────────────────────────────────────────────
# PROCESAR SOLUCIÓN
# ─────────────────────────────────────────────

STATUS_STR = {
    cp_model.OPTIMAL:    "ÓPTIMO ✓",
    cp_model.FEASIBLE:   "FACTIBLE (no garantizado óptimo)",
    cp_model.INFEASIBLE: "INFACTIBLE ✗",
    cp_model.UNKNOWN:    "DESCONOCIDO",
}

print(f"  Estado   : {STATUS_STR.get(status, 'DESCONOCIDO')}")
print(f"  Tiempo   : {t_sol:.3f} s")

if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print("  No se encontró solución. Aumenta MAX_BARRAS o TIEMPO_LIMITE.")
    exit(1)

# Reconstruir asignación
asignacion = {}   # barra_idx → lista de índices de pieza
for b in range(B):
    if solver.Value(y[b]) == 1:
        asignacion[b] = [i for i in range(N) if solver.Value(x[i][b]) == 1]

barras_usadas = sorted(asignacion.keys())
num_barras    = len(barras_usadas)

# ─────────────────────────────────────────────
# MOSTRAR RESULTADOS EN CONSOLA
# ─────────────────────────────────────────────

area_total    = num_barras * LONGITUD_BARRA
area_usada    = sum(lista_piezas[i][0] for piezas in asignacion.values() for i in piezas)
desperdicio   = area_total - area_usada
eficiencia    = area_usada / area_total * 100

print(f"\n{'─'*62}")
print(f"  DETALLE POR BARRA")
print(f"{'─'*62}")

for idx, b in enumerate(barras_usadas):
    piezas_b  = asignacion[b]
    usado     = sum(lista_piezas[i][0] for i in piezas_b)
    sobrante  = LONGITUD_BARRA - usado
    efs       = usado / LONGITUD_BARRA * 100

    longitudes = sorted([lista_piezas[i][0] - MARGEN_CORTE for i in piezas_b], reverse=True)
    print(f"\n  Barra #{idx+1}  →  {len(piezas_b)} piezas  |  {efs:.1f}% usado  |  {sobrante} mm sobrante")
    print(f"    Cortes (mm): {longitudes}")

    # Barra ASCII
    escala = 52 / LONGITUD_BARRA
    vis = ""
    for i in sorted(piezas_b, key=lambda i: lista_piezas[i][0], reverse=True):
        ancho = max(1, int(lista_piezas[i][0] * escala))
        vis += "█" * ancho + "▏"
    print(f"    |{vis:<54}|")

print(f"\n{'─'*62}")
print(f"  RESUMEN GLOBAL")
print(f"{'─'*62}")
print(f"  Barras usadas      : {num_barras}  (cota superior era {MAX_BARRAS})")
print(f"  Material total     : {area_total:>7} mm")
print(f"  Material usado     : {area_usada:>7} mm")
print(f"  Desperdicio total  : {desperdicio:>7} mm  ({100-eficiencia:.1f}%)")
print(f"  Eficiencia global  : {eficiencia:.2f}%")
print(f"  Garantía          : {'Solución ÓPTIMA' if status == cp_model.OPTIMAL else 'Mejor encontrada en tiempo límite'}")
print(f"{'─'*62}\n")

# ─────────────────────────────────────────────
# VISUALIZACIÓN MATPLOTLIB
# ─────────────────────────────────────────────

# Colores por tipo de pieza
nombres_unicos = list({lista_piezas[i][1] for i in range(N)})
cmap           = cm.get_cmap("tab10", len(nombres_unicos))
color_map      = {n: cmap(i) for i, n in enumerate(nombres_unicos)}

cols = min(num_barras, 3)
rows = (num_barras + cols - 1) // cols
fig, axes = plt.subplots(rows, cols, figsize=(cols * 5, rows * 2.2))
fig.suptitle(
    f"Cortes 1D — OR-Tools CP-SAT  |  {num_barras} barras  |  Eficiencia {eficiencia:.1f}%",
    fontsize=12, fontweight="bold"
)

ax_flat = axes.flatten() if hasattr(axes, "flatten") else [axes]

for idx, b in enumerate(barras_usadas):
    ax = ax_flat[idx]
    ax.set_xlim(0, LONGITUD_BARRA)
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_xlabel("mm", fontsize=8)

    piezas_b = sorted(asignacion[b], key=lambda i: lista_piezas[i][0], reverse=True)
    usado    = sum(lista_piezas[i][0] for i in piezas_b)
    sobrante = LONGITUD_BARRA - usado

    # Fondo (desperdicio)
    ax.add_patch(patches.Rectangle((0, 0), LONGITUD_BARRA, 1,
                                    facecolor="#eeeeee", edgecolor="#999"))

    cursor = 0
    etiquetas = set()
    for i in piezas_b:
        long_k = lista_piezas[i][0]
        nombre = lista_piezas[i][1]
        color  = color_map[nombre]
        label  = nombre if nombre not in etiquetas else ""
        etiquetas.add(nombre)

        rect = patches.Rectangle(
            (cursor, 0.05), long_k - MARGEN_CORTE, 0.9,
            facecolor=color, edgecolor="white", linewidth=1.2,
            alpha=0.88, label=label
        )
        ax.add_patch(rect)

        # Etiqueta si hay espacio
        if long_k > 250:
            ax.text(cursor + long_k / 2, 0.5,
                    f"{long_k - MARGEN_CORTE}",
                    ha="center", va="center",
                    fontsize=7, color="white", fontweight="bold")
        cursor += long_k

    efs = usado / LONGITUD_BARRA * 100
    ax.set_title(f"Barra #{idx+1}  —  {len(piezas_b)} pzas  |  {efs:.1f}%  |  -{sobrante}mm",
                 fontsize=8)
    ax.legend(fontsize=5.5, loc="upper right", framealpha=0.7)

# Ocultar ejes sobrantes
for j in range(num_barras, len(ax_flat)):
    ax_flat[j].set_visible(False)

plt.tight_layout()
plt.savefig("cortes_ortools.png", dpi=150, bbox_inches="tight")
print("  Imagen 'cortes_ortools.png' generada.")

# ─────────────────────────────────────────────
# EXPORTAR CSV
# ─────────────────────────────────────────────

with open("resultado_ortools.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Barra", "Pieza #", "Nombre", "Longitud (mm)", "Con kerf (mm)", "Sobrante barra (mm)"])
    for idx, b in enumerate(barras_usadas):
        piezas_b = sorted(asignacion[b], key=lambda i: lista_piezas[i][0], reverse=True)
        sobrante = LONGITUD_BARRA - sum(lista_piezas[i][0] for i in piezas_b)
        for j, i in enumerate(piezas_b):
            writer.writerow([
                idx + 1, j + 1,
                lista_piezas[i][1],
                lista_piezas[i][0] - MARGEN_CORTE,
                lista_piezas[i][0],
                sobrante if j == 0 else ""
            ])

print("  Archivo 'resultado_ortools.csv' generado.")
plt.show()
