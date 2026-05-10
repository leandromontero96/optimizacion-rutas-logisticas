"""
Optimizador de Rutas Logísticas
Implementa múltiples algoritmos de optimización
"""

import pandas as pd
import numpy as np
import json
from collections import defaultdict
import heapq

np.random.seed(42)

# Cargar datos
df_rutas = pd.read_csv('data/rutas.csv')
df_nodos = pd.read_csv('data/nodos.csv')

print("Optimizando rutas logisticas...")
print(f"Datos cargados: {len(df_rutas)} rutas, {len(df_nodos)} nodos\n")

# ============= ALGORITMO 1: DIJKSTRA (Camino más corto) =============
def dijkstra(grafo, inicio, fin):
    """Encuentra el camino más corto entre dos nodos"""
    # Obtener todos los nodos del grafo
    todos_nodos = set([inicio, fin])
    for nodo in grafo:
        todos_nodos.add(nodo)
        for vecino, _ in grafo[nodo]:
            todos_nodos.add(vecino)

    distancias = {nodo: float('inf') for nodo in todos_nodos}
    distancias[inicio] = 0
    pq = [(0, inicio)]
    padres = {}

    while pq:
        dist_actual, nodo_actual = heapq.heappop(pq)

        if nodo_actual == fin:
            break

        if dist_actual > distancias[nodo_actual]:
            continue

        for vecino, peso in grafo.get(nodo_actual, []):
            distancia = dist_actual + peso

            if distancia < distancias[vecino]:
                distancias[vecino] = distancia
                padres[vecino] = nodo_actual
                heapq.heappush(pq, (distancia, vecino))

    # Si no hay camino, retornar None
    if distancias[fin] == float('inf'):
        return None, None

    # Reconstruir camino
    camino = []
    nodo = fin
    while nodo in padres:
        camino.append(nodo)
        nodo = padres[nodo]
    camino.append(inicio)
    camino.reverse()

    return camino, distancias[fin]

# Construir grafo
grafo_costo = defaultdict(list)
grafo_distancia = defaultdict(list)

for _, ruta in df_rutas.iterrows():
    origen = ruta['origen_id']
    destino = ruta['destino_id']
    grafo_costo[origen].append((destino, ruta['costo_total_usd']))
    grafo_distancia[origen].append((destino, ruta['distancia_km']))

# Optimizar rutas de ejemplo
print("="*60)
print("ALGORITMO 1: DIJKSTRA - Camino mas corto")
print("="*60)

ejemplos_optimizacion = [
    ('POZO-01', 'REF-01'),
    ('POZO-05', 'REF-03'),
    ('REF-01', 'CD-01'),
    ('REF-02', 'PUERTO-01')
]

resultados_dijkstra = []
for origen, destino in ejemplos_optimizacion:
    camino, costo = dijkstra(grafo_costo, origen, destino)
    camino_dist, distancia = dijkstra(grafo_distancia, origen, destino)

    if camino is None:
        print(f"\nRuta: {origen} -> {destino}")
        print(f"  No hay camino directo disponible")
        continue

    print(f"\nRuta: {origen} -> {destino}")
    print(f"  Camino optimo: {' -> '.join(camino)}")
    print(f"  Costo total: ${costo:.2f} USD")
    print(f"  Distancia total: {distancia:.2f} km")

    resultados_dijkstra.append({
        'origen': origen,
        'destino': destino,
        'camino': ' -> '.join(camino),
        'costo_usd': costo,
        'distancia_km': distancia,
        'algoritmo': 'Dijkstra'
    })

# ============= ALGORITMO 2: GREEDY - Selección por menor costo =============
print("\n" + "="*60)
print("ALGORITMO 2: GREEDY - Seleccion de rutas de menor costo")
print("="*60)

# Seleccionar mejores rutas por tipo
rutas_optimizadas = []

# Pozos -> Refinerías (top 2 por cada pozo)
for pozo_id in df_rutas[df_rutas['origen_tipo'] == 'pozo']['origen_id'].unique():
    rutas_pozo = df_rutas[df_rutas['origen_id'] == pozo_id].nsmallest(2, 'costo_total_usd')
    rutas_optimizadas.extend(rutas_pozo.to_dict('records'))

# Refinerías -> Centros (top 1 por cada CD)
for cd_id in df_rutas[df_rutas['destino_tipo'] == 'centro_dist']['destino_id'].unique():
    ruta_cd = df_rutas[df_rutas['destino_id'] == cd_id].nsmallest(1, 'costo_total_usd')
    rutas_optimizadas.extend(ruta_cd.to_dict('records'))

# Refinerías -> Puertos (top 1 por cada refinería)
for ref_id in df_rutas[df_rutas['origen_tipo'] == 'refineria']['origen_id'].unique():
    ruta_puerto = df_rutas[(df_rutas['origen_id'] == ref_id) &
                           (df_rutas['destino_tipo'] == 'puerto')].nsmallest(1, 'costo_total_usd')
    if not ruta_puerto.empty:
        rutas_optimizadas.extend(ruta_puerto.to_dict('records'))

df_optimizado = pd.DataFrame(rutas_optimizadas)

costo_original = df_rutas['costo_total_usd'].sum()
costo_optimizado = df_optimizado['costo_total_usd'].sum()
ahorro = costo_original - costo_optimizado
ahorro_pct = (ahorro / costo_original) * 100

print(f"\nRutas originales: {len(df_rutas)}")
print(f"Rutas optimizadas: {len(df_optimizado)}")
print(f"Costo original: ${costo_original:,.2f} USD/dia")
print(f"Costo optimizado: ${costo_optimizado:,.2f} USD/dia")
print(f"AHORRO: ${ahorro:,.2f} USD/dia ({ahorro_pct:.1f}%)")

# ============= ALGORITMO 3: MULTI-OBJETIVO =============
print("\n" + "="*60)
print("ALGORITMO 3: OPTIMIZACION MULTI-OBJETIVO")
print("="*60)

# Normalizar métricas (0-1)
df_rutas['costo_norm'] = (df_rutas['costo_total_usd'] - df_rutas['costo_total_usd'].min()) / \
                         (df_rutas['costo_total_usd'].max() - df_rutas['costo_total_usd'].min())

df_rutas['tiempo_norm'] = (df_rutas['tiempo_hrs'] - df_rutas['tiempo_hrs'].min()) / \
                          (df_rutas['tiempo_hrs'].max() - df_rutas['tiempo_hrs'].min())

df_rutas['co2_norm'] = (df_rutas['co2_total_ton'] - df_rutas['co2_total_ton'].min()) / \
                       (df_rutas['co2_total_ton'].max() - df_rutas['co2_total_ton'].min())

# Función objetivo (minimizar)
# Pesos: 50% costo, 30% tiempo, 20% CO2
df_rutas['score_multi'] = (0.5 * df_rutas['costo_norm'] +
                           0.3 * df_rutas['tiempo_norm'] +
                           0.2 * df_rutas['co2_norm'])

# Seleccionar mejores rutas
rutas_multi = []
for pozo_id in df_rutas[df_rutas['origen_tipo'] == 'pozo']['origen_id'].unique():
    mejor_ruta = df_rutas[df_rutas['origen_id'] == pozo_id].nsmallest(1, 'score_multi')
    rutas_multi.extend(mejor_ruta.to_dict('records'))

for cd_id in df_rutas[df_rutas['destino_tipo'] == 'centro_dist']['destino_id'].unique():
    mejor_ruta = df_rutas[df_rutas['destino_id'] == cd_id].nsmallest(1, 'score_multi')
    rutas_multi.extend(mejor_ruta.to_dict('records'))

df_multi = pd.DataFrame(rutas_multi)

co2_original = df_rutas['co2_total_ton'].sum()
co2_optimizado = df_multi['co2_total_ton'].sum()
reduccion_co2 = co2_original - co2_optimizado
reduccion_co2_pct = (reduccion_co2 / co2_original) * 100

print(f"Costo optimizado: ${df_multi['costo_total_usd'].sum():,.2f} USD/dia")
print(f"Tiempo promedio: {df_multi['tiempo_hrs'].mean():.2f} hrs")
print(f"CO2 total: {co2_optimizado:.2f} ton/dia")
print(f"Reduccion CO2: {reduccion_co2:.2f} ton/dia ({reduccion_co2_pct:.1f}%)")

# ============= GUARDAR RESULTADOS =============
df_optimizado.to_csv('data/rutas_optimizadas.csv', index=False)

# Resumen de impacto
ahorro_anual_usd = ahorro * 365
reduccion_co2_anual = reduccion_co2 * 365

resumen = {
    'total_rutas_originales': len(df_rutas),
    'total_rutas_optimizadas': len(df_optimizado),
    'ahorro_diario_usd': round(ahorro, 2),
    'ahorro_anual_usd': round(ahorro_anual_usd, 2),
    'ahorro_porcentaje': round(ahorro_pct, 2),
    'reduccion_co2_diaria_ton': round(reduccion_co2, 2),
    'reduccion_co2_anual_ton': round(reduccion_co2_anual, 2),
    'reduccion_co2_porcentaje': round(reduccion_co2_pct, 2)
}

with open('data/resumen_optimizacion.json', 'w') as f:
    json.dump(resumen, f, indent=2)

print("\n" + "="*60)
print("RESUMEN DE IMPACTO ANUAL")
print("="*60)
print(f"Ahorro economico: ${ahorro_anual_usd/1e6:.1f}M USD/año")
print(f"Reduccion CO2: {reduccion_co2_anual:,.0f} ton/año")
print(f"Rutas optimizadas: {len(df_rutas)} -> {len(df_optimizado)} ({ahorro_pct:.1f}% reduccion)")

print("\n[OK] Optimizacion completada. Resultados guardados en /data")
