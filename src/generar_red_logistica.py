"""
Generador de Red Logística Petrolera
Simula pozos, refinerías, centros de distribución y rutas
"""

import pandas as pd
import numpy as np
import json

np.random.seed(42)

# Definir ubicaciones estratégicas (latitud, longitud)
# Región del Golfo de México y Texas
ubicaciones = {
    # Pozos petroleros
    'pozos': [
        {'id': f'POZO-{i:02d}', 'lat': np.random.uniform(27.5, 30.0),
         'lon': np.random.uniform(-97.5, -94.0), 'produccion_bbl_dia': np.random.uniform(500, 3000)}
        for i in range(1, 16)
    ],
    # Refinerías
    'refinerias': [
        {'id': 'REF-01', 'lat': 29.76, 'lon': -95.37, 'nombre': 'Houston Refinery', 'capacidad': 450000},
        {'id': 'REF-02', 'lat': 29.31, 'lon': -94.80, 'nombre': 'Texas City Refinery', 'capacidad': 400000},
        {'id': 'REF-03', 'lat': 30.06, 'lon': -93.88, 'nombre': 'Port Arthur Refinery', 'capacidad': 350000},
        {'id': 'REF-04', 'lat': 28.00, 'lon': -97.00, 'nombre': 'Corpus Christi Refinery', 'capacidad': 300000},
    ],
    # Centros de distribución
    'centros_dist': [
        {'id': 'CD-01', 'lat': 32.78, 'lon': -96.80, 'nombre': 'Dallas DC', 'demanda_bbl_dia': 50000},
        {'id': 'CD-02', 'lat': 29.42, 'lon': -98.49, 'nombre': 'San Antonio DC', 'demanda_bbl_dia': 35000},
        {'id': 'CD-03', 'lat': 30.27, 'lon': -97.74, 'nombre': 'Austin DC', 'demanda_bbl_dia': 40000},
        {'id': 'CD-04', 'lat': 31.76, 'lon': -106.49, 'nombre': 'El Paso DC', 'demanda_bbl_dia': 25000},
    ],
    # Puertos de exportación
    'puertos': [
        {'id': 'PUERTO-01', 'lat': 29.31, 'lon': -94.79, 'nombre': 'Puerto Houston', 'capacidad_export': 200000},
        {'id': 'PUERTO-02', 'lat': 27.80, 'lon': -97.40, 'nombre': 'Puerto Corpus Christi', 'capacidad_export': 150000},
    ]
}

def calcular_distancia(lat1, lon1, lat2, lon2):
    """Calcula distancia aproximada en km usando fórmula haversine simplificada"""
    R = 6371  # Radio de la Tierra en km
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return R * c

def generar_rutas():
    """Genera todas las rutas posibles entre nodos"""
    rutas = []

    # Rutas: Pozos -> Refinerías
    for pozo in ubicaciones['pozos']:
        for refineria in ubicaciones['refinerias']:
            distancia_km = calcular_distancia(pozo['lat'], pozo['lon'],
                                              refineria['lat'], refineria['lon'])
            costo_por_km = np.random.uniform(2.5, 4.0)  # USD por km
            tiempo_hrs = distancia_km / 80  # 80 km/h promedio

            rutas.append({
                'origen_id': pozo['id'],
                'origen_tipo': 'pozo',
                'destino_id': refineria['id'],
                'destino_tipo': 'refineria',
                'distancia_km': round(distancia_km, 2),
                'costo_usd_km': round(costo_por_km, 2),
                'costo_total_usd': round(distancia_km * costo_por_km, 2),
                'tiempo_hrs': round(tiempo_hrs, 2),
                'capacidad_bbl': min(pozo['produccion_bbl_dia'], 5000)
            })

    # Rutas: Refinerías -> Centros de Distribución
    for refineria in ubicaciones['refinerias']:
        for cd in ubicaciones['centros_dist']:
            distancia_km = calcular_distancia(refineria['lat'], refineria['lon'],
                                              cd['lat'], cd['lon'])
            costo_por_km = np.random.uniform(1.8, 3.0)
            tiempo_hrs = distancia_km / 90

            rutas.append({
                'origen_id': refineria['id'],
                'origen_tipo': 'refineria',
                'destino_id': cd['id'],
                'destino_tipo': 'centro_dist',
                'distancia_km': round(distancia_km, 2),
                'costo_usd_km': round(costo_por_km, 2),
                'costo_total_usd': round(distancia_km * costo_por_km, 2),
                'tiempo_hrs': round(tiempo_hrs, 2),
                'capacidad_bbl': 8000
            })

    # Rutas: Refinerías -> Puertos (exportación)
    for refineria in ubicaciones['refinerias']:
        for puerto in ubicaciones['puertos']:
            distancia_km = calcular_distancia(refineria['lat'], refineria['lon'],
                                              puerto['lat'], puerto['lon'])
            costo_por_km = np.random.uniform(2.0, 3.5)
            tiempo_hrs = distancia_km / 85

            rutas.append({
                'origen_id': refineria['id'],
                'origen_tipo': 'refineria',
                'destino_id': puerto['id'],
                'destino_tipo': 'puerto',
                'distancia_km': round(distancia_km, 2),
                'costo_usd_km': round(costo_por_km, 2),
                'costo_total_usd': round(distancia_km * costo_por_km, 2),
                'tiempo_hrs': round(tiempo_hrs, 2),
                'capacidad_bbl': 10000
            })

    return rutas

print("Generando red logistica petrolera...")

# Generar datasets
rutas = generar_rutas()
df_rutas = pd.DataFrame(rutas)

# Agregar métricas ambientales
df_rutas['co2_ton_km'] = 0.095  # Toneladas CO2 por km
df_rutas['co2_total_ton'] = (df_rutas['distancia_km'] * df_rutas['co2_ton_km']).round(2)

# Crear dataset de nodos
nodos = []
for tipo, lista in ubicaciones.items():
    for item in lista:
        nodo = {
            'nodo_id': item['id'],
            'tipo': tipo,
            'lat': round(item['lat'], 4),
            'lon': round(item['lon'], 4),
            'nombre': item.get('nombre', item['id'])
        }

        # Agregar atributos específicos
        if 'produccion_bbl_dia' in item:
            nodo['produccion_bbl_dia'] = round(item['produccion_bbl_dia'], 0)
        if 'capacidad' in item:
            nodo['capacidad_bbl_dia'] = item['capacidad']
        if 'demanda_bbl_dia' in item:
            nodo['demanda_bbl_dia'] = item['demanda_bbl_dia']
        if 'capacidad_export' in item:
            nodo['capacidad_export_bbl_dia'] = item['capacidad_export']

        nodos.append(nodo)

df_nodos = pd.DataFrame(nodos)

# Guardar datos
df_rutas.to_csv('data/rutas.csv', index=False)
df_nodos.to_csv('data/nodos.csv', index=False)

with open('data/red_logistica.json', 'w') as f:
    json.dump(ubicaciones, f, indent=2)

print(f"\n[OK] Red logistica generada!")
print(f"   Total rutas: {len(df_rutas)}")
print(f"   Total nodos: {len(df_nodos)}")
print(f"\nDistribucion de rutas:")
print(df_rutas.groupby(['origen_tipo', 'destino_tipo']).size())
print(f"\nEstadisticas de costos:")
print(f"   Costo promedio ruta: ${df_rutas['costo_total_usd'].mean():.2f} USD")
print(f"   Distancia promedio: {df_rutas['distancia_km'].mean():.2f} km")
print(f"   CO2 total (si se usan todas): {df_rutas['co2_total_ton'].sum():.2f} ton/dia")
