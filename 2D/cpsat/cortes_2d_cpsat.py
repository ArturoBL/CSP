"""
Optimización de Cortes 2D con OR-Tools CP-SAT
===============================================
Instalación: pip install ortools matplotlib

Problema de 2D Bin Packing:
  Colocar piezas rectangulares en láminas estándar minimizando
  el número de láminas usadas. CP-SAT garantiza la solución ÓPTIMA
  mediante restricciones de no solapamiento con disyuntivas 2D.

Restricciones del modelo:
  - Cada pieza se asigna a exactamente una lámina
  - Las piezas no se solapan (restricción 2D disjuntiva)
  - Las piezas caben dentro de los límites de la lámina
  - Se permite rotación 90°
  - Se minimiza el número de láminas usadas
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

ANCHO_LAMINA = 2440   # mm
ALTO_LAMINA  = 1220   # mm
MAX_LAMINAS  = 8      # cota superior
MARGEN_CORTE = 4      # mm — kerf
TIEMPO_LIMITE = 60    # segundos

# Piezas: (ancho_mm, alto_mm, cantidad, nombre)
piezas_requeridas = [
    (800,  600,  2, "Panel lateral"),
    (1200, 400,  2, "Panel base"),
    (600,  350,  4, "Repisa"),
    (400,  300,  4, "Cajón frontal"),
    (900,  180,  3, "Travesaño"),
    (500,  500,  2, "Fondo cuadrado"),
    (300,  200,  5, "Separador"),
    (700,  420,  2, "Panel puerta"),
]

# ─────────────────────────────────────────────
# PREPARAR LISTA DE PIEZAS
# ─────────────────────────────────────────────

lista_piezas = []  # (ancho+kerf, alto+kerf, nombre)
for ancho, alto, cantidad, nombre in piezas_requeridas:
    for _ in range(cantidad):
        lista_piezas.append((ancho + MARGEN_CORTE, alto + MARGEN_CORTE, nombre))

N = len(lista_piezas)
B = MAX_LAMINAS

print("=" * 64)
print("   OPTIMIZACIÓN DE CORTES 2D — OR-Tools CP-SAT")
print("=" * 64)
print(f"\nLámina estándar       : {ANCHO_LAMINA} × {ALTO_LAMINA} mm")
print(f"Margen de corte (kerf): {MARGEN_CORTE} mm")
print(f"Total piezas          : {N}")
print(f"Tiempo límite solver  : {TIEMPO_LIMITE} s")
print(f"\nPiezas requeridas:")
for ancho, alto, cant, nombre in piezas_requeridas:
    print(f"  {nombre:<22} {ancho:>5}×{alto:<5} mm  ×{cant}")

# ─────────────────────────────────────────────
# MODELO CP-SAT
# ─────────────────────────────────────────────

model  = cp_model.CpModel()
solver = cp_model.CpSolver()

# ── Variables de decisión ─────────────────────────────────────────
#
#  y[b]        = 1 si la lámina b es usada
#  assigned[i][b] = 1 si la pieza i va en la lámina b
#  rotated[i]  = 1 si la pieza i está rotada 90°
#  pos_x[i]    = posición X de la esquina inferior izquierda de pieza i
#  pos_y[i]    = posición Y de la esquina inferior izquierda de pieza i
#  lam[i]      = índice de lámina asignada a pieza i
#

y          = [model.NewBoolVar(f"y_{b}")          for b in range(B)]
assigned   = [[model.NewBoolVar(f"a_{i}_{b}")     for b in range(B)] for i in range(N)]
rotated    = [model.NewBoolVar(f"rot_{i}")         for i in range(N)]
pos_x      = [model.NewIntVar(0, ANCHO_LAMINA,     f"px_{i}") for i in range(N)]
pos_y      = [model.NewIntVar(0, ALTO_LAMINA,      f"py_{i}") for i in range(N)]

# Ancho y alto efectivos (con rotación)
ancho_ef = []
alto_ef  = []
for i, (w, h, _) in enumerate(lista_piezas):
    # Si rotated=0 → ancho=w, alto=h
    # Si rotated=1 → ancho=h, alto=w
    aw = model.NewIntVar(min(w, h), max(w, h), f"aw_{i}")
    ah = model.NewIntVar(min(w, h), max(w, h), f"ah_{i}")
    model.Add(aw == w).OnlyEnforceIf(rotated[i].Not())
    model.Add(aw == h).OnlyEnforceIf(rotated[i])
    model.Add(ah == h).OnlyEnforceIf(rotated[i].Not())
    model.Add(ah == w).OnlyEnforceIf(rotated[i])
    ancho_ef.append(aw)
    alto_ef.append(ah)

# ── Restricción: no rotar si es cuadrado ──────────────────────────
for i, (w, h, _) in enumerate(lista_piezas):
    if w == h:
        model.Add(rotated[i] == 0)

# ── Restricción: cada pieza va a exactamente una lámina ──────────
for i in range(N):
    model.Add(sum(assigned[i][b] for b in range(B)) == 1)

# ── Restricción: lámina usada si tiene al menos una pieza ────────
for b in range(B):
    for i in range(N):
        model.Add(y[b] >= assigned[i][b])
    model.Add(y[b] <= sum(assigned[i][b] for i in range(N)))

# ── Simetría: láminas se usan en orden ───────────────────────────
for b in range(B - 1):
    model.Add(y[b] >= y[b + 1])

# ── Restricción: pieza dentro de los límites de su lámina ────────
for i in range(N):
    model.Add(pos_x[i] + ancho_ef[i] <= ANCHO_LAMINA)
    model.Add(pos_y[i] + alto_ef[i]  <= ALTO_LAMINA)

# ── Restricción 2D disjuntiva: piezas no se solapan ──────────────
# Para cada par (i, j) en la misma lámina, al menos una separación:
#   izquierda/derecha/arriba/abajo debe cumplirse.
# Usamos variables booleanas auxiliares para las 4 disyuntivas.

for i in range(N):
    for j in range(i + 1, N):
        for b in range(B):
            # b_ij = 1 si ambas piezas están en la lámina b
            both_in_b = model.NewBoolVar(f"both_{i}_{j}_{b}")
            model.AddBoolAnd([assigned[i][b], assigned[j][b]]).OnlyEnforceIf(both_in_b)
            model.AddBoolOr([assigned[i][b].Not(), assigned[j][b].Not()]).OnlyEnforceIf(both_in_b.Not())

            # Si ambas en b → no solapamiento
            no_overlap_L = model.NewBoolVar(f"nol_L_{i}_{j}_{b}")  # i a la izquierda de j
            no_overlap_R = model.NewBoolVar(f"nol_R_{i}_{j}_{b}")  # i a la derecha de j
            no_overlap_B = model.NewBoolVar(f"nol_B_{i}_{j}_{b}")  # i debajo de j
            no_overlap_T = model.NewBoolVar(f"nol_T_{i}_{j}_{b}")  # i encima de j

            model.Add(pos_x[i] + ancho_ef[i] <= pos_x[j]).OnlyEnforceIf(no_overlap_L)
            model.Add(pos_x[j] + ancho_ef[j] <= pos_x[i]).OnlyEnforceIf(no_overlap_R)
            model.Add(pos_y[i] + alto_ef[i]  <= pos_y[j]).OnlyEnforceIf(no_overlap_B)
            model.Add(pos_y[j] + alto_ef[j]  <= pos_y[i]).OnlyEnforceIf(no_overlap_T)

            # Al menos uno debe cumplirse cuando ambas están en b
            model.AddBoolOr([no_overlap_L, no_overlap_R,
                              no_overlap_B, no_overlap_T]).OnlyEnforceIf(both_in_b)

# ── Objetivo: minimizar láminas usadas ───────────────────────────
model.Minimize(sum(y))

# ── Configurar solver ─────────────────────────────────────────────
solver.parameters.max_time_in_seconds  = TIEMPO_LIMITE
solver.parameters.num_search_workers   = 4
solver.parameters.log_search_progress  = False

# ─────────────────────────────────────────────
# RESOLVER
# ─────────────────────────────────────────────

print(f"\n{'─'*64}")
print("  Resolviendo (esto puede tomar varios segundos)...")
t0     = time.time()
status = solver.Solve(model)
t_sol  = time.time() - t0

STATUS_STR = {
    cp_model.OPTIMAL:    "ÓPTIMO ✓",
    cp_model.FEASIBLE:   "FACTIBLE (mejor encontrada en tiempo límite)",
    cp_model.INFEASIBLE: "INFACTIBLE ✗",
    cp_model.UNKNOWN:    "DESCONOCIDO",
}
print(f"  Estado   : {STATUS_STR.get(status, 'DESCONOCIDO')}")
print(f"  Tiempo   : {t_sol:.2f} s")

if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print("  No se encontró solución. Aumenta MAX_LAMINAS o TIEMPO_LIMITE.")
    exit(1)

# ─────────────────────────────────────────────
# RECONSTRUIR SOLUCIÓN
# ─────────────────────────────────────────────

# pieza i → (lámina, x, y, ancho_ef, alto_ef, rotada)
solucion = {}
for i in range(N):
    for b in range(B):
        if solver.Value(assigned[i][b]) == 1:
            solucion[i] = {
                "lamina":  b,
                "x":       solver.Value(pos_x[i]),
                "y":       solver.Value(pos_y[i]),
                "ancho":   solver.Value(ancho_ef[i]),
                "alto":    solver.Value(alto_ef[i]),
                "rotada":  bool(solver.Value(rotated[i])),
                "nombre":  lista_piezas[i][2],
            }

laminas_con_piezas = sorted({v["lamina"] for v in solucion.values()})
num_laminas        = len(laminas_con_piezas)

# ─────────────────────────────────────────────
# MOSTRAR RESULTADOS EN CONSOLA
# ─────────────────────────────────────────────

area_lamina   = ANCHO_LAMINA * ALTO_LAMINA
total_area    = num_laminas * area_lamina
usada_total   = sum(v["ancho"] * v["alto"] for v in solucion.values())
desperdicio   = total_area - usada_total
eficiencia    = usada_total / total_area * 100

print(f"\n{'─'*64}")
print(f"  DETALLE POR LÁMINA")
print(f"{'─'*64}")

for b in laminas_con_piezas:
    piezas_b = [i for i, v in solucion.items() if v["lamina"] == b]
    area_b   = sum(solucion[i]["ancho"] * solucion[i]["alto"] for i in piezas_b)
    efs_b    = area_b / area_lamina * 100
    sobre_b  = area_lamina - area_b

    print(f"\n  Lámina #{b+1}  →  {len(piezas_b)} piezas  |  {efs_b:.1f}% usado  |  -{sobre_b/1000:.0f} cm² sobrante")
    for i in piezas_b:
        v = solucion[i]
        rot_str = " [rotada]" if v["rotada"] else ""
        w_real  = v["ancho"] - MARGEN_CORTE
        h_real  = v["alto"]  - MARGEN_CORTE
        print(f"    ({v['x']:>4}, {v['y']:>4})  {w_real}×{h_real} mm  — {v['nombre']}{rot_str}")

print(f"\n{'─'*64}")
print(f"  RESUMEN GLOBAL")
print(f"{'─'*64}")
print(f"  Láminas usadas     : {num_laminas}  (máx disponible: {MAX_LAMINAS})")
print(f"  Piezas colocadas   : {len(solucion)} / {N}")
print(f"  Área total         : {total_area/1e6:.4f} m²")
print(f"  Área usada         : {usada_total/1e6:.4f} m²")
print(f"  Desperdicio        : {desperdicio/1e6:.4f} m²  ({100-eficiencia:.1f}%)")
print(f"  Eficiencia global  : {eficiencia:.2f}%")
print(f"  Garantía           : {'Solución ÓPTIMA' if status == cp_model.OPTIMAL else 'Mejor encontrada en tiempo límite'}")
print(f"{'─'*64}\n")

# ─────────────────────────────────────────────
# VISUALIZACIÓN
# ─────────────────────────────────────────────

nombres_unicos = list({v["nombre"] for v in solucion.values()})
cmap           = cm.get_cmap("tab20", len(nombres_unicos))
color_map      = {n: cmap(i) for i, n in enumerate(nombres_unicos)}

cols  = min(num_laminas, 2)
rows  = (num_laminas + 1) // 2
ratio = ALTO_LAMINA / ANCHO_LAMINA
fig, axes = plt.subplots(rows, cols, figsize=(cols * 7, rows * 7 * ratio + 0.8))
fig.suptitle(
    f"Cortes 2D — OR-Tools CP-SAT  |  {num_laminas} láminas  |  Eficiencia {eficiencia:.1f}%",
    fontsize=12, fontweight="bold"
)

if num_laminas == 1:
    ax_flat = [axes]
elif rows == 1:
    ax_flat = list(axes)
else:
    ax_flat = [ax for row in axes for ax in row]

for idx, b in enumerate(laminas_con_piezas):
    ax = ax_flat[idx]
    ax.set_xlim(0, ANCHO_LAMINA)
    ax.set_ylim(0, ALTO_LAMINA)
    ax.set_aspect("equal")
    ax.set_xlabel("mm", fontsize=8)
    ax.set_ylabel("mm", fontsize=8)

    piezas_b = [i for i, v in solucion.items() if v["lamina"] == b]
    area_b   = sum(solucion[i]["ancho"] * solucion[i]["alto"] for i in piezas_b)
    efs_b    = area_b / area_lamina * 100

    ax.set_title(f"Lámina #{b+1}  —  {len(piezas_b)} piezas  |  {efs_b:.1f}%", fontsize=9)

    # Fondo
    ax.add_patch(patches.Rectangle((0, 0), ANCHO_LAMINA, ALTO_LAMINA,
                                    facecolor="#f0f0f0", edgecolor="#bbb", linewidth=1))

    etiquetas = set()
    for i in piezas_b:
        v      = solucion[i]
        color  = color_map[v["nombre"]]
        label  = v["nombre"] if v["nombre"] not in etiquetas else ""
        etiquetas.add(v["nombre"])
        w_real = v["ancho"] - MARGEN_CORTE
        h_real = v["alto"]  - MARGEN_CORTE

        rect = patches.Rectangle(
            (v["x"], v["y"]), v["ancho"], v["alto"],
            facecolor=color, edgecolor="white",
            linewidth=1.5, alpha=0.88, label=label
        )
        ax.add_patch(rect)

        # Etiqueta centrada
        cx = v["x"] + v["ancho"] / 2
        cy = v["y"] + v["alto"]  / 2
        rot_sym = "↺ " if v["rotada"] else ""
        ax.text(cx, cy, f"{rot_sym}{w_real}×{h_real}",
                ha="center", va="center",
                fontsize=6.5, color="white", fontweight="bold")

    ax.legend(loc="upper right", fontsize=6, framealpha=0.85)
    ax.tick_params(labelsize=7)

for j in range(num_laminas, len(ax_flat)):
    ax_flat[j].set_visible(False)

plt.tight_layout()
plt.savefig("cortes_2d_cpsat.png", dpi=150, bbox_inches="tight")
print("  Imagen 'cortes_2d_cpsat.png' generada.")

# ─────────────────────────────────────────────
# EXPORTAR CSV
# ─────────────────────────────────────────────

with open("resultado_2d_cpsat.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Lámina", "Pieza", "Nombre", "X (mm)", "Y (mm)",
                     "Ancho (mm)", "Alto (mm)", "Rotada", "Área (m²)"])
    for i, v in sorted(solucion.items(), key=lambda x: (x[1]["lamina"], x[1]["x"])):
        w_real = v["ancho"] - MARGEN_CORTE
        h_real = v["alto"]  - MARGEN_CORTE
        writer.writerow([
            v["lamina"] + 1, i + 1, v["nombre"],
            v["x"], v["y"], w_real, h_real,
            "Sí" if v["rotada"] else "No",
            f"{w_real * h_real / 1e6:.6f}"
        ])

print("  Archivo 'resultado_2d_cpsat.csv' generado.")
plt.show()
