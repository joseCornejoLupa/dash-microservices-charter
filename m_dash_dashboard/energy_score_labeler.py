#!/usr/bin/env python3
"""
Energy Score Labeler for Kubernetes Nodes

Este script calcula el puntaje de eficiencia energética de cada nodo basándose
en los datos de consumo de energía (Ecofloc/Scaphandre) y aplica esos puntajes
como labels a los nodos de Kubernetes para que el scheduler pueda usarlos.

Uso:
    python energy_score_labeler.py --apply         # Calcula y aplica labels
    python energy_score_labeler.py --dry-run      # Solo muestra los cálculos
    python energy_score_labeler.py --source ecofloc|scaphandre  # Selecciona fuente de datos
"""

import os
import subprocess
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
from data_loader import DataLoader

# Configuración
ROOT_DIR = "/home/luish/Documents/death/dash-microservices-charter"
ENERGY_LABEL = "energy-score"

# Pesos para cada componente de energía (Ecofloc)
COMPONENT_WEIGHTS = {
    "cpu": 0.35,
    "ram": 0.15,
    "nic": 0.25,
    "sd": 0.25
}

# Mapeo manual de nombres de nodo en los datos a nombres de nodo K8s
# Actualiza este mapeo según tu cluster
NODE_NAME_MAPPING = {
    "aspire": "luish-aspire-a315-55g",
    "nitro5": "luish-nitro-an515-57",
    "nitro": "luish-nitro-an515-57",
    # Añade más mapeos según sea necesario:
    # "leo": "nombre-nodo-k8s-leo",
    # "scorpius": "nombre-nodo-k8s-scorpius",
}


class EnergyScoreCalculator:
    """Calcula puntajes de eficiencia energética para nodos de Kubernetes"""

    def __init__(self, root_dir: str):
        self.data_loader = DataLoader(root_dir)
        self.root_dir = Path(root_dir)

    def get_active_kubernetes_nodes(self) -> List[Dict[str, str]]:
        """Obtiene la lista de nodos activos del cluster de Kubernetes"""
        try:
            result = subprocess.run(
                ["kubectl", "get", "nodes", "-o", "json"],
                capture_output=True,
                text=True,
                check=True
            )
            nodes_data = json.loads(result.stdout)
            
            nodes = []
            for item in nodes_data.get("items", []):
                node_name = item["metadata"]["name"]
                status = "Unknown"
                
                # Obtener el estado del nodo
                for condition in item.get("status", {}).get("conditions", []):
                    if condition["type"] == "Ready":
                        status = "Ready" if condition["status"] == "True" else "NotReady"
                        break
                
                nodes.append({
                    "name": node_name,
                    "status": status,
                    "internal_ip": self._get_node_ip(item),
                    "current_energy_score": item["metadata"].get("labels", {}).get(ENERGY_LABEL, "N/A")
                })
            
            return nodes
        
        except subprocess.CalledProcessError as e:
            print(f"Error ejecutando kubectl: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"Error parseando JSON de kubectl: {e}")
            return []

    def _get_node_ip(self, node_item: dict) -> str:
        """Extrae la IP interna del nodo"""
        addresses = node_item.get("status", {}).get("addresses", [])
        for addr in addresses:
            if addr.get("type") == "InternalIP":
                return addr.get("address", "Unknown")
        return "Unknown"

    def collect_energy_data_ecofloc(self) -> pd.DataFrame:
        """
        Recolecta datos de energía de todos los experimentos disponibles (Ecofloc)
        
        Returns:
            DataFrame con columnas: node_name, component, energy_value
        """
        all_data = []
        
        components = self.data_loader.get_available_components()
        
        for component in components:
            if component == 'unified':
                continue  # Skip unified, procesamos por componente
            
            intensities = self.data_loader.get_available_intensities(component)
            
            for intensity in intensities:
                experiments = self.data_loader.get_available_experiments(component, intensity)
                
                for exp in experiments:
                    exp_path = exp['value']
                    
                    # Cargar datos de cada componente
                    for comp_type in ['cpu', 'ram', 'sd', 'nic']:
                        df = self.data_loader.load_ecofloc_component_data(exp_path, comp_type)
                        if not df.empty:
                            # Sumar energía por nodo
                            totals = df.groupby('node_name')['energy_value'].sum().reset_index()
                            totals['component'] = comp_type
                            totals['experiment'] = exp['label']
                            all_data.append(totals)
        
        if not all_data:
            return pd.DataFrame(columns=['node_name', 'component', 'energy_value'])
        
        return pd.concat(all_data, ignore_index=True)

    def collect_energy_data_scaphandre(self) -> pd.DataFrame:
        """
        Recolecta datos de energía de todos los experimentos disponibles (Scaphandre)
        
        Returns:
            DataFrame con columnas: node_name, energy_value
        """
        all_data = []
        
        components = self.data_loader.get_available_components()
        
        for component in components:
            intensities = self.data_loader.get_available_intensities(component)
            
            for intensity in intensities:
                experiments = self.data_loader.get_available_experiments(component, intensity)
                
                for exp in experiments:
                    exp_path = exp['value']
                    df = self.data_loader.load_scaphandre_data(exp_path)
                    
                    if not df.empty:
                        totals = df.groupby('node_name')['energy_value'].sum().reset_index()
                        totals['experiment'] = exp['label']
                        all_data.append(totals)
        
        if not all_data:
            return pd.DataFrame(columns=['node_name', 'energy_value'])
        
        return pd.concat(all_data, ignore_index=True)

    def normalize_value(self, value: float, min_val: float, max_val: float) -> float:
        """Normaliza un valor entre 0 y 100"""
        if max_val == min_val:
            return 50.0  # Si todos los valores son iguales
        return ((value - min_val) / (max_val - min_val)) * 100

    def calculate_energy_scores_ecofloc(self, energy_df: pd.DataFrame) -> Dict[str, float]:
        """
        Calcula el puntaje de eficiencia energética por nodo usando datos de Ecofloc
        
        NOTA: Un valor MÁS ALTO significa MEJOR eficiencia (menor consumo = mayor score)
        
        Args:
            energy_df: DataFrame con datos de energía por componente
            
        Returns:
            Dict con node_name -> energy_score (0-100, mayor es mejor)
        """
        if energy_df.empty:
            return {}
        
        # Promedio de energía por nodo y componente
        avg_energy = energy_df.groupby(['node_name', 'component'])['energy_value'].mean().reset_index()
        
        scores = {}
        nodes = avg_energy['node_name'].unique()
        
        for node in nodes:
            node_data = avg_energy[avg_energy['node_name'] == node]
            
            # Calcular score normalizado por componente
            component_scores = {}
            
            for component in ['cpu', 'ram', 'nic', 'sd']:
                comp_data = avg_energy[avg_energy['component'] == component]
                
                if comp_data.empty:
                    continue
                
                node_comp_data = comp_data[comp_data['node_name'] == node]
                
                if node_comp_data.empty:
                    continue
                
                node_value = node_comp_data['energy_value'].values[0]
                min_val = comp_data['energy_value'].min()
                max_val = comp_data['energy_value'].max()
                
                # Normalizar (invertido: menor consumo = mayor score)
                if max_val > min_val:
                    normalized = 100 - self.normalize_value(node_value, min_val, max_val)
                else:
                    normalized = 50.0
                
                component_scores[component] = normalized
            
            # Calcular score total ponderado
            total_score = 0.0
            total_weight = 0.0
            
            for comp, score in component_scores.items():
                weight = COMPONENT_WEIGHTS.get(comp, 0.25)
                total_score += score * weight
                total_weight += weight
            
            if total_weight > 0:
                scores[node] = round(total_score / total_weight * (total_weight / sum(COMPONENT_WEIGHTS.values())), 2)
            else:
                scores[node] = 50.0
        
        return scores

    def calculate_energy_scores_scaphandre(self, energy_df: pd.DataFrame) -> Dict[str, float]:
        """
        Calcula el puntaje de eficiencia energética por nodo usando datos de Scaphandre
        
        NOTA: Un valor MÁS ALTO significa MEJOR eficiencia (menor consumo = mayor score)
        
        Args:
            energy_df: DataFrame con datos de energía
            
        Returns:
            Dict con node_name -> energy_score (0-100, mayor es mejor)
        """
        if energy_df.empty:
            return {}
        
        # Promedio de energía por nodo
        avg_energy = energy_df.groupby('node_name')['energy_value'].mean().reset_index()
        
        min_val = avg_energy['energy_value'].min()
        max_val = avg_energy['energy_value'].max()
        
        scores = {}
        
        for _, row in avg_energy.iterrows():
            node = row['node_name']
            value = row['energy_value']
            
            # Invertido: menor consumo = mayor score
            if max_val > min_val:
                score = 100 - self.normalize_value(value, min_val, max_val)
            else:
                score = 50.0
            
            scores[node] = round(score, 2)
        
        return scores

    def apply_label_to_node(self, node_name: str, score: float) -> bool:
        """
        Aplica el label energy-score a un nodo de Kubernetes
        
        Args:
            node_name: Nombre del nodo
            score: Puntaje de eficiencia energética
            
        Returns:
            True si se aplicó correctamente, False en caso contrario
        """
        try:
            # Formatear el score como string con 2 decimales
            score_str = f"{score:.2f}"
            
            cmd = [
                "kubectl", "label", "nodes", node_name,
                f"{ENERGY_LABEL}={score_str}",
                "--overwrite"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"  ✓ Label aplicado a {node_name}: {ENERGY_LABEL}={score_str}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"  ✗ Error aplicando label a {node_name}: {e.stderr}")
            return False

    def remove_label_from_node(self, node_name: str) -> bool:
        """Remueve el label energy-score de un nodo"""
        try:
            cmd = ["kubectl", "label", "nodes", node_name, f"{ENERGY_LABEL}-"]
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"  ✓ Label removido de {node_name}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"  ✗ Error removiendo label de {node_name}: {e.stderr}")
            return False


def print_header(title: str):
    """Imprime un header decorado"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_nodes_table(nodes: List[Dict[str, str]]):
    """Imprime tabla de nodos"""
    print(f"\n{'Node Name':<30} {'Status':<10} {'IP':<15} {'Current Score':<15}")
    print("-" * 70)
    for node in nodes:
        print(f"{node['name']:<30} {node['status']:<10} {node['internal_ip']:<15} {node['current_energy_score']:<15}")


def print_scores_table(scores: Dict[str, float], source: str):
    """Imprime tabla de scores calculados"""
    print(f"\n{'Node Name':<30} {'Energy Score':<15} {'Efficiency':<20}")
    print("-" * 65)
    
    # Ordenar por score (mayor primero = más eficiente)
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    for i, (node, score) in enumerate(sorted_scores):
        if score >= 70:
            efficiency = "⚡ Alta Eficiencia"
        elif score >= 40:
            efficiency = "📊 Media Eficiencia"
        else:
            efficiency = "🔥 Baja Eficiencia"
        
        rank = f"#{i+1}"
        print(f"{node:<30} {score:<15.2f} {efficiency:<20}")


def main():
    parser = argparse.ArgumentParser(
        description="Calcula y aplica puntajes de eficiencia energética a nodos de Kubernetes"
    )
    parser.add_argument(
        "--apply", "-a",
        action="store_true",
        help="Aplica los labels a los nodos de Kubernetes"
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Solo muestra los cálculos sin aplicar labels"
    )
    parser.add_argument(
        "--source", "-s",
        choices=["ecofloc", "scaphandre"],
        default="ecofloc",
        help="Fuente de datos de energía (default: ecofloc)"
    )
    parser.add_argument(
        "--remove", "-r",
        action="store_true",
        help="Remueve los labels energy-score de los nodos"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Muestra información detallada"
    )
    
    args = parser.parse_args()
    
    # Si no se especifica ninguna acción, mostrar dry-run
    if not args.apply and not args.remove:
        args.dry_run = True
    
    print_header("Energy Score Labeler for Kubernetes")
    
    calculator = EnergyScoreCalculator(ROOT_DIR)
    
    # 1. Obtener nodos activos
    print("\n📡 Obteniendo nodos activos del cluster...")
    k8s_nodes = calculator.get_active_kubernetes_nodes()
    
    if not k8s_nodes:
        print("❌ No se encontraron nodos en el cluster o kubectl no está disponible")
        return 1
    
    print_nodes_table(k8s_nodes)
    
    # 2. Si se solicita remover labels
    if args.remove:
        print_header("Removiendo Labels")
        for node in k8s_nodes:
            calculator.remove_label_from_node(node['name'])
        return 0
    
    # 3. Recolectar datos de energía
    print(f"\n📊 Recolectando datos de energía ({args.source})...")
    
    if args.source == "ecofloc":
        energy_df = calculator.collect_energy_data_ecofloc()
        
        if energy_df.empty:
            print("❌ No se encontraron datos de energía Ecofloc")
            return 1
        
        if args.verbose:
            print(f"   Registros encontrados: {len(energy_df)}")
            print(f"   Nodos con datos: {energy_df['node_name'].nunique()}")
            print(f"   Componentes: {energy_df['component'].unique().tolist()}")
        
        # 4. Calcular scores
        print("\n🧮 Calculando puntajes de eficiencia energética...")
        scores = calculator.calculate_energy_scores_ecofloc(energy_df)
        
    else:  # scaphandre
        energy_df = calculator.collect_energy_data_scaphandre()
        
        if energy_df.empty:
            print("❌ No se encontraron datos de energía Scaphandre")
            return 1
        
        if args.verbose:
            print(f"   Registros encontrados: {len(energy_df)}")
            print(f"   Nodos con datos: {energy_df['node_name'].nunique()}")
        
        # 4. Calcular scores
        print("\n🧮 Calculando puntajes de eficiencia energética...")
        scores = calculator.calculate_energy_scores_scaphandre(energy_df)
    
    if not scores:
        print("❌ No se pudieron calcular scores")
        return 1
    
    # 5. Mostrar resultados
    print_header(f"Resultados ({args.source.upper()})")
    print_scores_table(scores, args.source)
    
    # 6. Mapear scores a nodos de Kubernetes
    print_header("Mapeo a Nodos de Kubernetes")
    
    # Crear mapeo de nombres de nodo (los datos pueden usar nombres diferentes)
    node_score_mapping = {}
    k8s_node_names = [n['name'] for n in k8s_nodes]
    
    for data_node_name, score in scores.items():
        # Primero intentar mapeo manual
        if data_node_name in NODE_NAME_MAPPING:
            k8s_name = NODE_NAME_MAPPING[data_node_name]
            if k8s_name in k8s_node_names:
                node_score_mapping[k8s_name] = score
                print(f"  📌 {data_node_name} -> {k8s_name}: {score:.2f} (mapeo manual)")
                continue
        
        # Buscar coincidencia exacta o parcial
        matched = False
        for k8s_name in k8s_node_names:
            # Comparar nombres normalizados (minúsculas, sin guiones vs underscores)
            data_normalized = data_node_name.lower().replace('_', '-').replace('@', '-')
            k8s_normalized = k8s_name.lower()
            
            if data_normalized == k8s_normalized or data_normalized in k8s_normalized or k8s_normalized in data_normalized:
                node_score_mapping[k8s_name] = score
                matched = True
                print(f"  📌 {data_node_name} -> {k8s_name}: {score:.2f}")
                break
        
        if not matched:
            print(f"  ⚠️  {data_node_name}: No se encontró nodo K8s correspondiente (score={score:.2f})")
            print(f"      💡 Añade '{data_node_name}': 'nombre-k8s' en NODE_NAME_MAPPING")
    
    # Nodos sin datos de energía
    for k8s_node in k8s_nodes:
        if k8s_node['name'] not in node_score_mapping:
            print(f"  ⚠️  {k8s_node['name']}: Sin datos de energía (asignando score=50)")
            node_score_mapping[k8s_node['name']] = 50.0
    
    # 7. Aplicar labels si se solicitó
    if args.apply:
        print_header("Aplicando Labels a Kubernetes")
        
        success_count = 0
        for node_name, score in node_score_mapping.items():
            if calculator.apply_label_to_node(node_name, score):
                success_count += 1
        
        print(f"\n✅ Labels aplicados: {success_count}/{len(node_score_mapping)}")
        
        # Verificar aplicación
        print("\n📋 Verificando labels aplicados...")
        subprocess.run(["kubectl", "get", "nodes", "-L", ENERGY_LABEL])
        
    else:
        print_header("Modo Dry-Run")
        print("\nLabels que se aplicarían:")
        for node_name, score in node_score_mapping.items():
            print(f"  kubectl label nodes {node_name} {ENERGY_LABEL}={score:.2f} --overwrite")
        
        print("\n💡 Ejecuta con --apply para aplicar los labels")
    
    return 0


if __name__ == "__main__":
    exit(main())
