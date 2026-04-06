"""
Optimización de Cortes 1D con binpacking + visualización Matplotlib
=====================================================================
Instalación: pip install binpacking matplotlib

Muestra cada barra como una franja horizontal con las piezas
coloreadas por tipo, etiquetas de medida y resumen de eficiencia.
"""

import binpacking
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.cm as cm
import matplotlib.ticker as ticker
import csv

# ─────────────────────────────────────────────
# DATOS DEL PROBLEMA
# ─────────────────────────────────────────────

LONGITUD_BARRA = 6000   # mm
MARGEN_CORTE   = 3      # mm — kerf por corte
ALTO_BARRA     = 0.6    # altura visual de cada barra en el gráfico
SEPARACION     = 0.3    # espacio entre barras

# Piezas: (longitud_mm, cantidad, nombre)
piezas_requeridas = [
    (2400, 3, "Larguero A"),
    (1800, 4, "Larguero B"),
    (1200, 5, "Travesaño"),
    (900,  6, "Montante"),
    (600,  7, "Separador"),
    (400,  5, "Taco"),
    (300,  8, "Escuadra"),
]

# ─────────────────────────────────────────────
# EXPANDIR PIEZAS Y EMPAQUETAR
# ─────────────────────────────────────────────

lista_piezas = []   # (longitud_con_kerf, nombre)
for longitud, cantidad, nombre in piezas_requeridas:
    for _ in range(cantidad):
        lista_piezas.append((longitud + MARGEN_CORTE, nombre))

# binpacking solo acepta valores numéricos → usamos longitudes
longitudes = [p[0] for p in lista_piezas]

barras = binpacking.to_constant_volume(longitudes, LONGITUD_BARRA)

# Reconstruir nombres: relacionar longitudes con su nombre original
# Construimos un pool consumible por nombre+longitud
from collections import defaultdict
pool = defaultdict(list)
for longitud, nombre in lista_piezas:
    pool[(longitud, nombre)].append(nombre)

# Para cada barra, reconstruir lista (longitud, nombre)
barras_nombradas = []
pool_idx = defaultdict(int)
nombre_por_longitud = {}
for longitud, nombre in lista_piezas:
    nombre_por_longitud[longitud] = nombre  # última asignación (aprox)

# Reconstrucción más precisa usando contador
conteo_disponible = defaultdict(list)
for longitud, nombre in lista_piezas:
    conteo_disponible[longitud].append(nombre)

for barra in barras:
    barra_nombrada = []
    temp_pool = defaultdict(list)
    for k, v in conteo_disponible.items():
        temp_pool[k] = list(v)

    usados = defaultdict(int)
    for longitud in barra:
        nombre = conteo_disponible[longitud][usados[longitud]]
        barra_nombrada.append((longitud, nombre))
        usados[longitud] += 1
    barras_nombradas.append(barra_nombrada)

# Consumir pool global
pool_global = defaultdict(list)
for longitud, nombre in lista_piezas:
    pool_global[longitud].append(nombre)

barras_nombradas = []
for barra in barras:
    barra_nombrada = []
    conteo_local = defaultdict(int)
    for longitud in barra:
        idx   = conteo_local[longitud]
        nombre = pool_global[longitud][idx] if idx < len(pool_global[longitud]) else "Pieza"
        barra_nombrada.append((longitud, nombre))
        conteo_local[longitud] += 1
    barras_nombradas.append(barra_nombrada)

num_barras = len(barras_nombradas)

# ─────────────────────────────────────────────
# ESTADÍSTICAS
# ─────────────────────────────────────────────

area_total   = num_barras * LONGITUD_BARRA
area_usada   = sum(l for barra in barras_nombradas for l, _ in barra)
desperdicio  = area_total - area_usada
eficiencia   = area_usada / area_total * 100

print("=" * 58)
print("  OPTIMIZACIÓN DE CORTES 1D — binpacking + matplotlib")
print("=" * 58)
print(f"\n  Barras necesarias  : {num_barras}")
print(f"  Piezas colocadas   : {sum(len(b) for b in barras_nombradas)}")
print(f"  Material total     : {area_total:>7} mm")
print(f"  Material usado     : {area_usada:>7} mm")
print(f"  Desperdicio        : {desperdicio:>7} mm")
print(f"  Eficiencia global  : {eficiencia:.1f}%\n")

# ─────────────────────────────────────────────
# PALETA DE COLORES POR TIPO DE PIEZA
# ─────────────────────────────────────────────

nombres_unicos = list({nombre for _, nombre in
                        [p for barra in barras_nombradas for p in barra]})
cmap      = cm.get_cmap("tab10", len(nombres_unicos))
color_map = {nombre: cmap(i) for i, nombre in enumerate(nombres_unicos)}

# ─────────────────────────────────────────────
# FIGURA PRINCIPAL: DIAGRAMA DE BARRAS
# ─────────────────────────────────────────────

altura_total = num_barras * (ALTO_BARRA + SEPARACION) + SEPARACION
fig_h        = max(5, min(altura_total + 2.5, 18))
fig, ax      = plt.subplots(figsize=(13, fig_h))

ax.set_xlim(-20, LONGITUD_BARRA + 120)
ax.set_ylim(-0.5, altura_total + 0.8)
ax.set_xlabel("Longitud (mm)", fontsize=10)
ax.set_title(
    f"Cortes 1D — binpacking FFD  |  {num_barras} barras  |  Eficiencia {eficiencia:.1f}%",
    fontsize=12, fontweight="bold", pad=14
)
ax.set_yticks([])
ax.xaxis.set_major_locator(ticker.MultipleLocator(500))
ax.xaxis.set_minor_locator(ticker.MultipleLocator(100))
ax.tick_params(axis="x", labelsize=8)
ax.grid(axis="x", which="major", linestyle="--", alpha=0.3, color="#888")
ax.spines[["top", "left", "right"]].set_visible(False)

etiquetas_leyenda = set()

for idx, barra in enumerate(barras_nombradas):
    y_base  = idx * (ALTO_BARRA + SEPARACION) + SEPARACION
    usado   = sum(l for l, _ in barra)
    sobrante = LONGITUD_BARRA - usado
    efs     = usado / LONGITUD_BARRA * 100

    # Fondo gris (material sobrante)
    ax.add_patch(patches.FancyBboxPatch(
        (0, y_base), LONGITUD_BARRA, ALTO_BARRA,
        boxstyle="round,pad=0,rounding_size=0",
        facecolor="#e8e8e8", edgecolor="#bbb", linewidth=0.8, zorder=1
    ))

    # Etiqueta izquierda: número de barra
    ax.text(-15, y_base + ALTO_BARRA / 2, f"#{idx+1}",
            ha="right", va="center", fontsize=8,
            fontweight="bold", color="#444")

    # Dibujar piezas
    cursor = 0
    piezas_sorted = sorted(barra, key=lambda x: x[0], reverse=True)
    for longitud, nombre in piezas_sorted:
        color = color_map[nombre]
        label = nombre if nombre not in etiquetas_leyenda else ""
        etiquetas_leyenda.add(nombre)

        # Rectángulo de la pieza (sin kerf visual)
        ancho_visual = longitud - MARGEN_CORTE
        rect = patches.Rectangle(
            (cursor, y_base + 0.04), ancho_visual, ALTO_BARRA - 0.08,
            facecolor=color, edgecolor="white",
            linewidth=1.2, alpha=0.90, zorder=2, label=label
        )
        ax.add_patch(rect)

        # Línea de corte (kerf)
        ax.plot([cursor + ancho_visual, cursor + ancho_visual],
                [y_base + 0.06, y_base + ALTO_BARRA - 0.06],
                color="white", linewidth=1.5, zorder=3, alpha=0.6)

        # Etiqueta de medida dentro de la pieza
        if ancho_visual >= 200:
            cx = cursor + ancho_visual / 2
            cy = y_base + ALTO_BARRA / 2
            ax.text(cx, cy, f"{ancho_visual}",
                    ha="center", va="center",
                    fontsize=7, color="white", fontweight="bold", zorder=4)

        cursor += longitud

    # Zona sobrante (cross-hatch)
    if sobrante > 0:
        hatch = patches.Rectangle(
            (cursor, y_base + 0.04), sobrante, ALTO_BARRA - 0.08,
            facecolor="none", edgecolor="#aaa",
            linewidth=0.7, hatch="///", zorder=2, alpha=0.5
        )
        ax.add_patch(hatch)
        if sobrante > 150:
            ax.text(cursor + sobrante / 2, y_base + ALTO_BARRA / 2,
                    f"-{sobrante}mm",
                    ha="center", va="center",
                    fontsize=6.5, color="#888", style="italic", zorder=4)

    # Barra de eficiencia (derecha)
    bar_x = LONGITUD_BARRA + 20
    bar_w = 80
    ax.add_patch(patches.Rectangle(
        (bar_x, y_base + 0.1), bar_w, ALTO_BARRA - 0.2,
        facecolor="#ddd", edgecolor="#bbb", linewidth=0.6, zorder=2
    ))
    ax.add_patch(patches.Rectangle(
        (bar_x, y_base + 0.1), bar_w * efs / 100, ALTO_BARRA - 0.2,
        facecolor="#4caf50" if efs >= 85 else "#ff9800" if efs >= 70 else "#f44336",
        edgecolor="none", alpha=0.85, zorder=3
    ))
    ax.text(bar_x + bar_w / 2, y_base + ALTO_BARRA / 2,
            f"{efs:.0f}%",
            ha="center", va="center", fontsize=7,
            fontweight="bold", color="white", zorder=4)

# Encabezado columna eficiencia
ax.text(LONGITUD_BARRA + 60, altura_total + 0.1, "Ef.",
        ha="center", va="bottom", fontsize=8, color="#555")

# Leyenda de tipos de pieza
handles = [patches.Patch(facecolor=color_map[n], label=n, alpha=0.9)
           for n in nombres_unicos]
ax.legend(handles=handles, loc="lower right",
          fontsize=8, framealpha=0.9,
          title="Tipo de pieza", title_fontsize=8)

plt.tight_layout()
plt.savefig("binpacking_1d.png", dpi=150, bbox_inches="tight")
print("  Imagen 'binpacking_1d.png' generada.")

# ─────────────────────────────────────────────
# FIGURA SECUNDARIA: GRÁFICO DE RESUMEN
# ─────────────────────────────────────────────

fig2, axes2 = plt.subplots(1, 3, figsize=(13, 3.5))
fig2.suptitle("Resumen de optimización", fontsize=11, fontweight="bold")

# — Gráfico 1: Eficiencia por barra —
eficiencias = [sum(l for l, _ in b) / LONGITUD_BARRA * 100
               for b in barras_nombradas]
colores_ef  = ["#4caf50" if e >= 85 else "#ff9800" if e >= 70 else "#f44336"
               for e in eficiencias]
ejes = axes2[0]
bars = ejes.bar([f"#{i+1}" for i in range(num_barras)],
                eficiencias, color=colores_ef, edgecolor="white", linewidth=0.8)
ejes.axhline(eficiencia, color="#333", linestyle="--", linewidth=1, label=f"Media {eficiencia:.1f}%")
ejes.set_ylim(0, 105)
ejes.set_ylabel("Eficiencia (%)")
ejes.set_title("Eficiencia por barra")
ejes.legend(fontsize=8)
ejes.tick_params(axis="x", labelsize=8)
for bar, ef in zip(bars, eficiencias):
    ejes.text(bar.get_x() + bar.get_width() / 2, ef + 1,
              f"{ef:.0f}%", ha="center", va="bottom", fontsize=7)

# — Gráfico 2: Distribución de material —
ax2 = axes2[1]
labels_pie = ["Usado", "Desperdicio"]
sizes_pie  = [area_usada, desperdicio]
colors_pie = ["#42a5f5", "#ef5350"]
wedges, texts, autotexts = ax2.pie(
    sizes_pie, labels=labels_pie, colors=colors_pie,
    autopct="%1.1f%%", startangle=90,
    wedgeprops={"edgecolor": "white", "linewidth": 1.5}
)
for t in autotexts:
    t.set_fontsize(9)
ax2.set_title("Distribución de material")

# — Gráfico 3: Piezas por tipo —
ax3 = axes2[2]
conteo_tipos = {}
for barra in barras_nombradas:
    for _, nombre in barra:
        conteo_tipos[nombre] = conteo_tipos.get(nombre, 0) + 1
nombres_s  = list(conteo_tipos.keys())
conteos_s  = [conteo_tipos[n] for n in nombres_s]
colores_s  = [color_map[n] for n in nombres_s]
ax3.barh(nombres_s, conteos_s, color=colores_s, edgecolor="white", linewidth=0.8)
ax3.set_xlabel("Cantidad")
ax3.set_title("Piezas por tipo")
ax3.tick_params(axis="y", labelsize=8)
for i, v in enumerate(conteos_s):
    ax3.text(v + 0.1, i, str(v), va="center", fontsize=8)

plt.tight_layout()
plt.savefig("binpacking_resumen.png", dpi=150, bbox_inches="tight")
print("  Imagen 'binpacking_resumen.png' generada.")

# ─────────────────────────────────────────────
# EXPORTAR CSV
# ─────────────────────────────────────────────

with open("resultado_binpacking.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Barra", "Posición", "Nombre", "Longitud (mm)",
                     "Con kerf (mm)", "Sobrante barra (mm)", "Eficiencia (%)"])
    for idx, barra in enumerate(barras_nombradas):
        sobrante = LONGITUD_BARRA - sum(l for l, _ in barra)
        efs      = sum(l for l, _ in barra) / LONGITUD_BARRA * 100
        cursor   = 0
        for j, (longitud, nombre) in enumerate(
                sorted(barra, key=lambda x: x[0], reverse=True)):
            writer.writerow([
                idx + 1, cursor, nombre,
                longitud - MARGEN_CORTE, longitud,
                sobrante if j == 0 else "", f"{efs:.1f}" if j == 0 else ""
            ])
            cursor += longitud

print("  Archivo 'resultado_binpacking.csv' generado.\n")
plt.show()
