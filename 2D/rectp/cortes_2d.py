"""
Optimización de Cortes 2D con rectpack
========================================
Instalación: pip install rectpack matplotlib

Problema: Tenemos láminas/tableros de tamaño estándar y necesitamos
cortar piezas rectangulares minimizando el desperdicio de material.
"""

import rectpack
from rectpack import newPacker, PackingMode, PackingBin
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.cm as cm
import csv
import random

# ─────────────────────────────────────────────
# DATOS DEL PROBLEMA
# ─────────────────────────────────────────────

ANCHO_LAMINA  = 2440  # mm — tablero estándar (ej. MDF, melamina)
ALTO_LAMINA   = 1220  # mm
MAX_LAMINAS   = 10    # máximo de láminas disponibles
MARGEN_CORTE  = 4     # mm — kerf (pérdida por disco de sierra)

# Piezas requeridas: (ancho, alto, cantidad, nombre)
piezas_requeridas = [
    (800,  600,  3, "Panel lateral"),
    (1200, 600,  2, "Panel base"),
    (600,  400,  5, "Repisa"),
    (400,  300,  6, "Cajón frontal"),
    (1000, 200,  4, "Travesaño"),
    (500,  500,  3, "Fondo cuadrado"),
    (300,  200,  8, "Separador"),
    (700,  450,  2, "Panel puerta"),
]

# ─────────────────────────────────────────────
# PREPARAR LISTA DE PIEZAS
# ─────────────────────────────────────────────

lista_piezas = []  # (ancho, alto, id, nombre)
pid = 1
for ancho, alto, cantidad, nombre in piezas_requeridas:
    for _ in range(cantidad):
        # Incluir margen de corte en cada pieza
        lista_piezas.append((ancho + MARGEN_CORTE, alto + MARGEN_CORTE, pid, nombre))
        pid += 1

total_piezas = len(lista_piezas)

print("=" * 60)
print("   OPTIMIZACIÓN DE CORTES 2D — rectpack")
print("=" * 60)
print(f"\nLámina estándar     : {ANCHO_LAMINA} x {ALTO_LAMINA} mm")
print(f"Margen de corte     : {MARGEN_CORTE} mm")
print(f"Total piezas        : {total_piezas}")
print(f"\nPiezas requeridas:")
for ancho, alto, cant, nombre in piezas_requeridas:
    area = ancho * alto * cant
    print(f"  {nombre:<20} {ancho:>4}x{alto:<4} mm  x{cant}  ({area/1e6:.4f} m²)")

# ─────────────────────────────────────────────
# CONFIGURAR Y EJECUTAR EL PACKER
# ─────────────────────────────────────────────

# Crear packer con algoritmo Maximal Rectangles (mejor calidad)
packer = newPacker(
    mode=PackingMode.Offline,       # conocemos todas las piezas de antemano
    bin_algo=PackingBin.BFF,        # Best Fit First para láminas
    sort_algo=rectpack.SORT_SSIDE,  # ordenar por lado más corto
    rotation=True                   # permitir rotación de piezas
)

# Agregar láminas disponibles
for _ in range(MAX_LAMINAS):
    packer.add_bin(ANCHO_LAMINA, ALTO_LAMINA)

# Agregar piezas al packer (ancho, alto, rid)
for ancho, alto, pid, nombre in lista_piezas:
    packer.add_rect(ancho, alto, rid=pid)

# Ejecutar optimización
packer.pack()

# ─────────────────────────────────────────────
# PROCESAR RESULTADOS
# ─────────────────────────────────────────────

laminas_usadas = packer.bin_list()
piezas_colocadas = 0
resultados = []  # (lamina_idx, x, y, ancho, alto, pid)

for i, lamina in enumerate(packer):
    rects = list(lamina)
    piezas_colocadas += len(rects)
    for rect in rects:
        resultados.append((i, rect.x, rect.y, rect.width, rect.height, rect.rid))

# Piezas no colocadas
ids_colocados = {r[5] for r in resultados}
ids_todos     = {p[2] for p in lista_piezas}
no_colocados  = ids_todos - ids_colocados

# ─────────────────────────────────────────────
# MOSTRAR RESUMEN EN CONSOLA
# ─────────────────────────────────────────────

area_lamina = ANCHO_LAMINA * ALTO_LAMINA
num_laminas = len(packer.bin_list())

print(f"\n{'─'*60}")
print(f"   RESULTADO")
print(f"{'─'*60}")
print(f"  Láminas necesarias  : {num_laminas}")
print(f"  Piezas colocadas    : {piezas_colocadas} / {total_piezas}")
if no_colocados:
    print(f"  ⚠ Piezas sin colocar: {len(no_colocados)} (aumentar MAX_LAMINAS)")

for i, lamina in enumerate(packer):
    rects       = list(lamina)
    area_usada  = sum(r.width * r.height for r in rects)
    desperdicio = area_lamina - area_usada
    eficiencia  = area_usada / area_lamina * 100
    print(f"\n  Lámina #{i+1}:")
    print(f"    Piezas     : {len(rects)}")
    print(f"    Usado      : {area_usada/1e6:.4f} m²  ({eficiencia:.1f}%)")
    print(f"    Desperdicio: {desperdicio/1e6:.4f} m²")

total_area_usada  = sum(r.width * r.height for lam in packer for r in lam)
total_area_total  = num_laminas * area_lamina
eficiencia_global = total_area_usada / total_area_total * 100

print(f"\n{'─'*60}")
print(f"   RESUMEN GLOBAL")
print(f"{'─'*60}")
print(f"  Material total      : {total_area_total/1e6:.4f} m²")
print(f"  Material usado      : {total_area_usada/1e6:.4f} m²")
print(f"  Desperdicio total   : {(total_area_total-total_area_usada)/1e6:.4f} m²")
print(f"  Eficiencia global   : {eficiencia_global:.1f}%")
print(f"{'─'*60}\n")

# ─────────────────────────────────────────────
# MAPA DE COLORES POR TIPO DE PIEZA
# ─────────────────────────────────────────────

# Asignar color por nombre de pieza
nombres_unicos = list({p[3] for p in lista_piezas})
colores_base   = cm.get_cmap("tab20", len(nombres_unicos))
color_map      = {nombre: colores_base(i) for i, nombre in enumerate(nombres_unicos)}

# Diccionario pid → nombre
pid_a_nombre = {p[2]: p[3] for p in lista_piezas}

# ─────────────────────────────────────────────
# VISUALIZACIÓN CON MATPLOTLIB
# ─────────────────────────────────────────────

cols     = min(num_laminas, 2)
rows     = (num_laminas + 1) // 2
fig, axes = plt.subplots(rows, cols, figsize=(14, rows * 4.5))
fig.suptitle("Optimización de Cortes 2D — rectpack", fontsize=14, fontweight="bold", y=1.01)

if num_laminas == 1:
    axes = [[axes]]
elif rows == 1:
    axes = [axes]

ax_list = [ax for row in axes for ax in (row if hasattr(row, '__iter__') else [row])]

for i, lamina in enumerate(packer):
    ax = ax_list[i]
    ax.set_xlim(0, ANCHO_LAMINA)
    ax.set_ylim(0, ALTO_LAMINA)
    ax.set_aspect("equal")
    ax.set_title(f"Lámina #{i+1}  ({len(list(lamina))} piezas)", fontsize=10)
    ax.set_xlabel("mm")
    ax.set_ylabel("mm")

    # Fondo (material sobrante)
    fondo = patches.Rectangle((0, 0), ANCHO_LAMINA, ALTO_LAMINA,
                                linewidth=1, edgecolor="#aaa",
                                facecolor="#f5f5f5")
    ax.add_patch(fondo)

    etiquetas_vistas = set()
    for rect in lamina:
        nombre = pid_a_nombre.get(rect.rid, "Pieza")
        color  = color_map[nombre]
        w_real = rect.width  - MARGEN_CORTE
        h_real = rect.height - MARGEN_CORTE

        # Rectángulo de la pieza
        r = patches.Rectangle(
            (rect.x, rect.y), rect.width, rect.height,
            linewidth=1.2, edgecolor="white",
            facecolor=color, alpha=0.85,
            label=nombre if nombre not in etiquetas_vistas else ""
        )
        ax.add_patch(r)
        etiquetas_vistas.add(nombre)

        # Etiqueta dentro de la pieza
        cx, cy = rect.x + rect.width / 2, rect.y + rect.height / 2
        ax.text(cx, cy, f"{w_real}×{h_real}",
                ha="center", va="center",
                fontsize=6.5, color="white", fontweight="bold")

    ax.legend(loc="upper right", fontsize=6, framealpha=0.8)

# Ocultar ejes sobrantes
for j in range(num_laminas, len(ax_list)):
    ax_list[j].set_visible(False)

plt.tight_layout()
plt.savefig("cortes_2d.png", dpi=150, bbox_inches="tight")
print("  Imagen 'cortes_2d.png' generada correctamente.")

# ─────────────────────────────────────────────
# EXPORTAR A CSV
# ─────────────────────────────────────────────

with open("resultado_cortes_2d.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Lámina", "Pieza", "X (mm)", "Y (mm)",
                     "Ancho (mm)", "Alto (mm)", "Área (m²)"])
    for lam_idx, x, y, w, h, pid in resultados:
        nombre = pid_a_nombre.get(pid, "Pieza")
        w_real = w - MARGEN_CORTE
        h_real = h - MARGEN_CORTE
        writer.writerow([lam_idx + 1, nombre, x, y, w_real, h_real,
                         f"{w_real*h_real/1e6:.6f}"])

print("  Archivo 'resultado_cortes_2d.csv' generado correctamente.")
plt.show()
