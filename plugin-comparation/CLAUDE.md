# Investigación: Impacto del Plugin de Scheduling en Energía (TeaStore / Kubernetes)

## Objetivo
Comparar el consumo energético y la tasa de transacciones exitosas del cluster TeaStore
**con** y **sin** un plugin de scheduling energético de Kubernetes.

La hipótesis central es que el plugin **consolida pods en menos nodos**, lo que reduce
el consumo total al permitir que los nodos inactivos entren en estados de reposo más profundos
y reducir el tráfico de red inter-nodo.

---

## Infraestructura
- **4 nodos**: aspire, leo, nitro5, scorpius
- **7 servicios TeaStore**: teastore-auth, teastore-db, teastore-registry,
  teastore-webui, teastore-image, teastore-recommender, teastore-persistence
- **3 fases por experimento**: fase1 (warmup), fase2 (setup), fase3 (load test activo)
- **3 intensidades de carga**: low, medium, high
- **Herramienta de energía**: ecofloc (por nodo × componente: cpu, ram, nic, sd)
- **Herramienta de carga**: limbo (CSV con time-series de transacciones por segundo)

---

## Estructura de directorios

```
plugin-comparation/
├── with-plugin/        → experimentos CON el plugin de scheduling
│   ├── fase1/
│   ├── fase2/
│   └── fase3/
│       └── exp(HH:MM:SS)_fase3_{intensity}_iter{N}/
│           ├── ecofloc_raw/
│           │   ├── ecofloc_fase3_{tipo}_{intensity}_{iter}_{node}_{component}.txt
│           │   └── ecofloc_summary.csv   ← generado por summarize_ecofloc_energy.py
│           ├── limbo/
│           │   ├── limbo_results_*.csv
│           │   └── requests_info.csv     ← generado por summarize_limbo_requests.py
│           └── node_distribution/
│               ├── kps_crictl_ps_all*.txt
│               └── node_distribution.csv ← generado por analyze_node_distribution.py
├── without-plugin/     → experimentos SIN el plugin (scheduler por defecto)
│   └── (misma estructura que with-plugin/)
├── python-files/       → scripts de análisis propios de plugin-comparation
│   ├── summarize_limbo_requests.py
│   ├── analyze_node_distribution.py
│   ├── summarize_ecofloc_energy.py
│   └── generate_report.py
└── results/
    ├── report.txt      → reporte en inglés (autogenerado)
    ├── report_es.txt   → traducción al español (generado manualmente)
    └── graficos/       → 6 gráficas PNG
        ├── energy_by_intensity.png
        ├── requests_by_intensity.png
        ├── energy_efficiency.png
        ├── failed_tx_comparison.png
        ├── node_energy_breakdown.png
        └── pod_distribution_heatmap.png
```

---

## Pipeline de procesamiento

> **IMPORTANTE**: Usar siempre el intérprete Python del venv de new_data_set:
> `/home/josec/green_computing/microservices/historyexecutions/experiments-data/new_data_set/venv/bin/python3`
>
> NO usar `source venv/bin/activate` dentro de comandos encadenados con `&&` —
> no propaga correctamente el entorno. Usar la ruta absoluta al intérprete directamente.

Directorio de trabajo base:
`/home/josec/green_computing/microservices/historyexecutions/experiments-data/`

### Flujo completo para nuevos experimentos en plugin-comparation:

```
Paso 1 — Preservar kps_crictl (ANTES de normalizar):
  python3 new_data_set/python-files/prepare_new_experiments.py \
    --path plugin-comparation/

Paso 2 — Normalizar estructura de carpetas:
  python3 new_data_set/python-files/normalize_experiment_structure.py \
    --path plugin-comparation/

Paso 3 — Resumir datos de limbo (requests):
  python3 plugin-comparation/python-files/summarize_limbo_requests.py

Paso 4 — Analizar distribución de pods (node_distribution):
  python3 plugin-comparation/python-files/analyze_node_distribution.py --fase fase3

Paso 5 — Resumir energía ecofloc:
  python3 plugin-comparation/python-files/summarize_ecofloc_energy.py --fase fase3

Paso 6 — Generar reporte y gráficas:
  python3 plugin-comparation/python-files/generate_report.py
```

Los pasos 1 y 2 son **idempotentes** (saltan carpetas ya procesadas).
Los pasos 3–5 también detectan si el CSV de salida ya existe y lo sobreescriben.

---

## Descripción de scripts

| Script | Propósito | Salida |
|---|---|---|
| `summarize_limbo_requests.py` | Agrega time-series de limbo en un resumen por experimento | `limbo/requests_info.csv` |
| `analyze_node_distribution.py` | Parsea kps_crictl_ps_all.txt y cuenta pods por nodo | `node_distribution/node_distribution.csv` |
| `summarize_ecofloc_energy.py` | Extrae total_energy y avg_energy de cada txt de ecofloc | `ecofloc_raw/ecofloc_summary.csv` |
| `generate_report.py` | Cruza los 3 CSVs, genera report.txt y 6 gráficas PNG | `results/report.txt` + `results/graficos/*.png` |

### Detalles técnicos críticos

**summarize_limbo_requests.py**
- El header CSV de limbo tiene 8 tokens; las filas de datos tienen 7 → usar `pd.read_csv(path, index_col=0)`
- Promedio ponderado de avg_response_time: `sum(rt × tx) / sum(tx)` (solo filas donde tx > 0)
- Si hay múltiples CSVs por experimento (medium=2, high=3), los combina en uno solo

**analyze_node_distribution.py**
- Regex `Running\s+(\S+)` para extraer nombre del pod (evita problema con longitud variable del campo CREATED)
- Mapeo de nodos por substring: Nitro→nitro5, Aspire→aspire, scorpius→scorpius, leo→leo
- Siempre emite los 4 nodos aunque alguno no aparezca en el archivo
- Argumento CLI: `--fase {fase1,fase2,fase3}` (default: fase3)

**summarize_ecofloc_energy.py**
- Línea 1 del txt: `Average Power NODE COMPONENT : VALUE Watts` → avg_energy
- Línea 2 del txt: `Total Energy NODE COMPONENT : VALUE Joules` → total_energy
- Nodo y componente extraídos de las últimas dos partes del nombre de archivo
- Argumento CLI: `--fase {fase1,fase2,fase3}` (default: fase3)
- Solo stdlib (no requiere pandas/matplotlib)

**generate_report.py**
- Requiere matplotlib y numpy (disponibles en new_data_set/venv)
- Agrupa experimentos por `(group, intensity)` donde group = with-plugin | without-plugin
- Calcula por experimento: total_energy_J, successful_tx, failed_tx, dropped_tx, avg_response_time, energy_per_tx
- `plot_pod_distribution_heatmap`: genera grid `n_rows × 2` (una fila por intensidad con datos en ambos grupos,
  una columna por grupo). Degrada graciosamente si falta alguna intensidad.
  Cada subplot muestra la distribución promedio de pods por (nodo × servicio).
- RQ3 en el reporte: muestra `avg_teastore_nodes_used` para **todas** las intensidades (no solo low)

---

## Estado actual del dataset (última actualización: 2026-02-27)

| Grupo | Intensidad | N experimentos |
|---|---|---|
| with-plugin | low | 19 |
| with-plugin | medium | 15 |
| with-plugin | high | 18 |
| without-plugin | low | 21 |
| without-plugin | medium | 18 |
| without-plugin | high | 15 |
| **Total** | | **106** |

---

## Resultados actuales (report.txt — 2026-02-27)

### RQ1: ¿El plugin reduce el consumo energético?
| Intensidad | Con plugin | Sin plugin | Diferencia |
|---|---|---|---|
| low | 940.99 J (std 314.50) | 970.51 J (std 325.69) | **-3.0%** con plugin |
| medium | 875.58 J (std 338.70) | 1150.95 J (std 407.17) | **-23.9%** con plugin |
| high | 911.59 J (std 384.61) | 1141.58 J (std 447.46) | **-20.1%** con plugin |

**Conclusión**: El plugin usa consistentemente MENOS energía, pero la ventaja se moderó
respecto a datos anteriores (N pequeño). La reducción en low es marginal (-3%).

### RQ2: ¿El plugin mejora los requests exitosos?
| Intensidad | Con plugin | Sin plugin | Diferencia |
|---|---|---|---|
| low | 609.9 tx (std 508.3) | 1183.6 tx (std 1568.9) | **-48.5%** con plugin |
| medium | 960.1 tx (std 901.0) | 1821.4 tx (std 1517.9) | **-47.3%** con plugin |
| high | 898.7 tx (std 1382.5) | 1852.5 tx (std 2061.3) | **-51.5%** con plugin |

**Conclusión**: Con dataset completo (N≈50), el plugin logra consistentemente ~50% MENOS
transacciones. Los resultados favorables previos (N=2–4) no eran representativos.

### RQ3: Eficiencia combinada (J/tx) y distribución de pods
| Intensidad | Con plugin | Sin plugin | Resultado |
|---|---|---|---|
| low | 2.5400 J/tx | 2.2554 J/tx | **12.6% peor** con plugin |
| medium | 1.2834 J/tx | 1.0631 J/tx | **20.7% peor** con plugin |
| high | 2.1558 J/tx | 1.7012 J/tx | **26.7% peor** con plugin |

**Distribución de pods** (todas las intensidades — 2026-02-27):
| Intensidad | Con plugin | Sin plugin |
|---|---|---|
| low | 3.37 nodos | 3.00 nodos |
| medium | 3.60 nodos | 3.00 nodos |
| high | 3.00 nodos | 3.00 nodos |

**HALLAZGO CLAVE**: El plugin DISPERSA la carga en más nodos (no consolida).
La hipótesis de "consolidación en 2 nodos" era artefacto del N=2–4 previo.
Con N=52, el plugin usa igual o más nodos que el scheduler por defecto.

---

## Métrica energy_per_tx — análisis crítico

### Fórmula usada
```
energy_per_tx = total_energy_J / successful_tx
```
- `total_energy_J` = suma de energía de todos los nodos × todos los componentes (cpu, ram, nic, sd) durante fase3
- `successful_tx` = transacciones HTTP completadas con éxito (limbo)

### Base científica
Variante del concepto "energy per functional unit" del Software Carbon Intensity (SCI) de la
Green Software Foundation (GSF, 2023) / ISO/IEC 21031:2024. La "functional unit" es una transacción exitosa.
Métrica estándar en papers de green computing con TeaStore (Leitner et al., 2019).

### Problema crítico: sesgo por energía idle
ecofloc mide **energía total del nodo**, no solo la atribuible a TeaStore:
```
energy_per_tx = (E_idle_cluster + E_k8s_overhead + E_teastore) / successful_tx
```
La mayor parte del valor reportado es potencia de fondo constante, no trabajo útil.

### Por qué J/tx sale peor para with-plugin en low
El plugin consume 23% menos energía PERO procesa 51% menos transacciones →
el divisor cae más que el numerador → ratio J/tx sube aunque sea más eficiente en absoluto.
```
with-plugin:    879 J / 1446 tx = 0.62 J/tx  (peor ratio)
without-plugin: 1146 J / 2959 tx = 0.56 J/tx (mejor ratio, pero consume MÁS energía total)
```

### Alternativas más sólidas
| Métrica | Fórmula | Nota |
|---|---|---|
| Energía bruta | `total_energy_J` | La más honesta para comparar el plugin |
| Potencia media | `total_energy_J / duration_s` | Comparable entre duraciones distintas |
| Throughput energético | `successful_tx / total_energy_J` (tx/J) | Versión invertida más intuitiva |
| Energía diferencial | `(E_cluster - E_baseline) / successful_tx` | Requiere medición idle — la más rigurosa |

**Recomendación**: para las conclusiones del plugin, `total_energy_J` es más honesto que `J/tx`
en baja intensidad donde el throughput difiere mucho entre grupos.

---

## Limitaciones conocidas
- sin-plugin low tiene alta varianza (mezcla de lotes: ~1500 tx vs ~4800 tx)
- ecofloc mide energía total por nodo; no puede aislar consumo individual por pod
- with-plugin tiene menos repeticiones por intensidad (N=2) vs without-plugin (N=3–12); interpretar std con cautela
- `pod_distribution_heatmap` cubre las 3 intensidades (grid 3×2)
- `energy_per_tx` tiene sesgo por energía idle — ver sección "Métrica energy_per_tx" arriba
- No se dispone de mediciones baseline (cluster idle sin carga) → energía diferencial no calculable

---

## Pendientes de investigación
- [ ] Investigar causa del menor throughput con plugin en TODAS las intensidades (~50% menos tx)
      (¿overhead de scheduling? ¿penalización por mayor dispersión inter-nodo? ¿configuración del plugin?)
- [ ] Analizar avg_response_time: si el plugin genera más latencia, explicaría el menor throughput
- [ ] Comparar componentes (CPU vs RAM vs NIC) entre ambos grupos para identificar el driver de energía
- [ ] Añadir medición baseline (cluster idle sin carga) para calcular energía diferencial
- [ ] Traducir report.txt actualizado a español (report_es.txt) tras cada ejecución de generate_report.py
