"""
Optimización de Cortes 1D con binpacking
=========================================
Instalación: pip install binpacking

Problema: Tenemos barras de longitud estándar (6000 mm) y necesitamos
cortar piezas de distintas medidas minimizando el desperdicio.
"""

import binpacking

# ─────────────────────────────────────────────
# DATOS DEL PROBLEMA
# ─────────────────────────────────────────────

LONGITUD_BARRA = 6000  # mm — longitud de cada barra estándar
MARGEN_CORTE   = 3     # mm — pérdida por cada corte (kerf)

# Piezas requeridas: {longitud_mm: cantidad}
piezas = {
    2400: 3,
    1800: 5,
    1200: 4,
    900:  6,
    600:  8,
    300:  10,
}

# ─────────────────────────────────────────────
# PREPARAR LISTA DE PIEZAS (expandir cantidades)
# ─────────────────────────────────────────────

lista_piezas = []
for longitud, cantidad in piezas.items():
    lista_piezas.extend([longitud + MARGEN_CORTE] * cantidad)  # incluir kerf

print("=" * 55)
print("  OPTIMIZACIÓN DE CORTES 1D — binpacking")
print("=" * 55)
print(f"\nLongitud de barra estándar : {LONGITUD_BARRA} mm")
print(f"Margen de corte (kerf)     : {MARGEN_CORTE} mm")
print(f"Total de piezas a cortar   : {len(lista_piezas)}")
print(f"\nPiezas requeridas:")
for longitud, cantidad in sorted(piezas.items(), reverse=True):
    print(f"  {longitud:>5} mm  x {cantidad}")

# ─────────────────────────────────────────────
# EJECUTAR ALGORITMO First Fit Decreasing (FFD)
# ─────────────────────────────────────────────

barras = binpacking.to_constant_bin_number(lista_piezas, LONGITUD_BARRA)
# Alternativa: binpacking.to_constant_volume(lista_piezas, LONGITUD_BARRA)
# → usa el mínimo número de barras necesarias

# ─────────────────────────────────────────────
# MOSTRAR RESULTADOS
# ─────────────────────────────────────────────

print(f"\n{'─'*55}")
print(f"  RESULTADO: {len(barras)} barra(s) necesaria(s)")
print(f"{'─'*55}")

total_material    = len(barras) * LONGITUD_BARRA
total_usado       = sum(lista_piezas)
total_desperdicio = total_material - total_usado
eficiencia        = (total_usado / total_material) * 100

for i, barra in enumerate(barras, 1):
    usado       = sum(barra)
    desperdicio = LONGITUD_BARRA - usado
    piezas_reales = [p - MARGEN_CORTE for p in barra]  # quitar kerf para mostrar

    print(f"\n  Barra #{i}:")
    print(f"    Piezas    : {sorted(piezas_reales, reverse=True)}")
    print(f"    Usado     : {usado:>5} mm  ({usado/LONGITUD_BARRA*100:.1f}%)")
    print(f"    Desperdicio: {desperdicio:>4} mm")

    # Visualización ASCII del corte
    escala   = 50 / LONGITUD_BARRA
    barra_vis = ""
    for p in sorted(barra, reverse=True):
        ancho = max(1, int(p * escala))
        barra_vis += "█" * ancho + "░"
    relleno = 50 - len(barra_vis.replace("░", ""))
    print(f"    [{barra_vis:<52}]")

print(f"\n{'─'*55}")
print(f"  RESUMEN GLOBAL")
print(f"{'─'*55}")
print(f"  Barras utilizadas  : {len(barras)}")
print(f"  Material total     : {total_material:>6} mm")
print(f"  Material usado     : {total_usado:>6} mm")
print(f"  Desperdicio total  : {total_desperdicio:>6} mm")
print(f"  Eficiencia         : {eficiencia:.1f}%")
print(f"{'─'*55}\n")

# ─────────────────────────────────────────────
# EXPORTAR A CSV (opcional)
# ─────────────────────────────────────────────

import csv

with open("resultado_cortes.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Barra", "Pieza #", "Longitud (mm)", "Desperdicio (mm)"])
    for i, barra in enumerate(barras, 1):
        piezas_reales = sorted([p - MARGEN_CORTE for p in barra], reverse=True)
        desperdicio   = LONGITUD_BARRA - sum(barra)
        for j, pieza in enumerate(piezas_reales, 1):
            writer.writerow([i, j, pieza, desperdicio if j == 1 else ""])

print("  Archivo 'resultado_cortes.csv' generado correctamente.")
