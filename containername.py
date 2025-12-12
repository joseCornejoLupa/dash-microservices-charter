import csv
import re
import os

# --- Configuración de Archivos ---
INPUT_CSV = "kps_all.csv"
INPUT_TXT = "kps_crictl_ps_all.txt"
OUTPUT_CSV = "informe_pids.csv"


def parse_crictl_txt(txt_file):
    """
    Lee el archivo de texto de crictl y crea un diccionario mapeando
    Short Container ID -> Container Name
    """
    mapping = {}

    # Regex explicada:
    # ^(\S+)        -> Grupo 1: Captura el Container ID (primer palabra al inicio de linea)
    # \s+           -> Espacios
    # .* -> Cualquier cosa en el medio (imagen, tiempo)
    # \s+           -> Espacios antes del estado
    # (Running|Exited|Created|Unknown) -> Grupo 2: Estado del contenedor (ancla clave)
    # \s+           -> Espacios
    # (\S+)         -> Grupo 3: Captura el NOMBRE (palabra justo después del estado)
    regex_pattern = re.compile(
        r"^(\S+)\s+.*\s+(Running|Exited|Created|Unknown)\s+(\S+)"
    )

    print(f"📖 Leyendo {txt_file}...")
    try:
        with open(txt_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                match = regex_pattern.search(line)
                if match:
                    short_id = match.group(1)
                    name = match.group(3)
                    # Guardamos en el diccionario
                    mapping[short_id] = name
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo {txt_file}")
        return {}

    print(f"✅ Se encontraron {len(mapping)} contenedores en el TXT.")
    return mapping


def update_csv(csv_file, mapping, output_file):
    """
    Lee el CSV, busca coincidencias en el diccionario y guarda el nuevo CSV.
    """
    print(f"🔄 Procesando {csv_file}...")

    updated_rows = []
    headers = []
    match_count = 0

    try:
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

            for row in reader:
                container_id_long = row.get("containerid", "")

                # Lógica de coincidencia:
                # El ID del CSV es largo (SHA completo), el del TXT es corto (13 chars).
                # Buscamos si el ID largo empieza con alguno de los IDs cortos del mapa.

                # Opción Rápida: Asumir que el ID corto son los primeros 13 chars del largo
                short_id_candidate = container_id_long[:13]

                if short_id_candidate in mapping:
                    row["containername"] = mapping[short_id_candidate]
                    match_count += 1
                else:
                    # Búsqueda exhaustiva por seguridad (si el ID corto no es exactamente 13 chars)
                    for short_id, name in mapping.items():
                        if container_id_long.startswith(short_id):
                            row["containername"] = name
                            match_count += 1
                            break

                updated_rows.append(row)

        # Escribir el nuevo archivo
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(updated_rows)

        print(f"✅ Archivo generado exitosamente: {output_file}")
        print(f"📊 Se actualizaron {match_count} filas con nombres de contenedores.")

    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo {csv_file}")


if __name__ == "__main__":
    # 1. Obtener datos del TXT
    container_map = parse_crictl_txt(INPUT_TXT)

    # 2. Actualizar el CSV si hay datos
    if container_map:
        update_csv(INPUT_CSV, container_map, OUTPUT_CSV)
