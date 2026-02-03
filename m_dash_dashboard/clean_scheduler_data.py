#!/usr/bin/env python3
"""
Script para limpiar el CSV de scheduler de TeaStore.
Extrae solo los últimos 7 registros únicos por iteración (uno por cada tipo de servicio).
Los 7 servicios son: auth, db, image, persistence, recommender, registry, webui
"""

import pandas as pd
import re
from pathlib import Path


def extract_service_type(pod_name: str) -> str:
    """
    Extrae el tipo de servicio del nombre del pod.
    Ejemplo: 'teastore-auth-84d7ccddd9-5wl62' -> 'auth'
    """
    match = re.match(r'teastore-([a-z]+)-', pod_name)
    if match:
        return match.group(1)
    return pod_name


def clean_scheduler_data(input_file: str, output_file: str = None, num_services: int = 7):
    """
    Limpia el CSV manteniendo solo los últimos registros únicos por iteración.
    
    Args:
        input_file: Ruta al archivo CSV de entrada
        output_file: Ruta al archivo CSV de salida (opcional)
        num_services: Número de servicios únicos a mantener por iteración (default: 7)
    
    Returns:
        DataFrame con los datos limpios
    """
    # Leer el CSV
    df = pd.read_csv(input_file)
    
    print(f"Total de registros originales: {len(df)}")
    print(f"Número de iteraciones: {df['Iteracion'].nunique()}")
    
    # Extraer el tipo de servicio
    df['service_type'] = df['Pod'].apply(extract_service_type)
    
    # Lista para almacenar los registros filtrados
    cleaned_records = []
    
    # Procesar cada iteración
    for iteracion in sorted(df['Iteracion'].unique()):
        iter_df = df[df['Iteracion'] == iteracion]
        
        # Por cada tipo de servicio, tomar el ÚLTIMO registro (el más reciente en el archivo)
        for service in iter_df['service_type'].unique():
            service_records = iter_df[iter_df['service_type'] == service]
            # Tomar el último registro de este servicio en esta iteración
            last_record = service_records.iloc[-1]
            cleaned_records.append(last_record)
    
    # Crear DataFrame limpio
    cleaned_df = pd.DataFrame(cleaned_records)
    
    # Eliminar la columna auxiliar service_type
    cleaned_df = cleaned_df.drop(columns=['service_type'])
    
    # Resetear el índice
    cleaned_df = cleaned_df.reset_index(drop=True)
    
    print(f"Total de registros después de limpieza: {len(cleaned_df)}")
    print(f"Registros por iteración (esperado ~{num_services}): {len(cleaned_df) / df['Iteracion'].nunique():.1f}")
    
    # Guardar si se especificó archivo de salida
    if output_file:
        cleaned_df.to_csv(output_file, index=False)
        print(f"Archivo guardado en: {output_file}")
    
    return cleaned_df


def get_iteration_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Genera un resumen por iteración.
    """
    summary = df.groupby('Iteracion').agg({
        'Pod': 'count',
        'Fecha': 'first',
        'Estado': lambda x: (x == 'Running').sum(),
        'Nodo': 'nunique'
    }).rename(columns={
        'Pod': 'total_pods',
        'Estado': 'running_pods',
        'Nodo': 'unique_nodes'
    })
    
    summary['pending_pods'] = summary['total_pods'] - summary['running_pods']
    
    return summary


if __name__ == "__main__":
    # Rutas de archivos
    script_dir = Path(__file__).parent
    input_file = script_dir / "teastore_scheduler_data.csv"
    output_file = script_dir / "teastore_scheduler_data_cleaned.csv"
    
    # Verificar que existe el archivo de entrada
    if not input_file.exists():
        print(f"Error: No se encontró el archivo {input_file}")
        exit(1)
    
    # Limpiar datos
    print("=" * 60)
    print("Limpiando datos del scheduler de TeaStore")
    print("=" * 60)
    
    cleaned_df = clean_scheduler_data(str(input_file), str(output_file))
    
    # Mostrar algunos ejemplos
    print("\n" + "=" * 60)
    print("Primeras iteraciones después de la limpieza:")
    print("=" * 60)
    for i in range(1, 4):
        print(f"\n--- Iteración {i} ---")
        iter_data = cleaned_df[cleaned_df['Iteracion'] == i]
        print(iter_data.to_string(index=False))
    
    # Mostrar resumen
    print("\n" + "=" * 60)
    print("Resumen por iteración (primeras 10):")
    print("=" * 60)
    summary = get_iteration_summary(cleaned_df)
    print(summary.head(10))
    
    print("\n" + "=" * 60)
    print("Estadísticas generales:")
    print("=" * 60)
    print(f"Total de iteraciones: {cleaned_df['Iteracion'].nunique()}")
    print(f"Total de registros limpios: {len(cleaned_df)}")
    print(f"Nodos únicos: {cleaned_df['Nodo'].unique().tolist()}")
    print(f"Estados posibles: {cleaned_df['Estado'].unique().tolist()}")
    
    # Distribución de pods por nodo
    print("\n" + "=" * 60)
    print("Distribución de pods por nodo (total acumulado):")
    print("=" * 60)
    print(cleaned_df['Nodo'].value_counts())
