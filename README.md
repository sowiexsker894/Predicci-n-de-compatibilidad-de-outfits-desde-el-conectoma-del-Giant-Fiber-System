# Modelo Fly · Predicción de compatibilidad de outfits desde el conectoma del Giant Fiber System

Proyecto del curso de Machine Learning (1ACC0057, UPC). Equipo: Nicole Sihuincha Schermuly y Sergio Iglesias Pérez. Metodología CRISP-DM.

**Qué hace:** recomienda outfits armados con la ropa que el usuario **ya tiene** (ODS 12), en dos etapas:

1. **Fase 1 · DeepFM (filtro personal):** aprende el gusto de cada usuario con su historial y se queda con el 25 % de los outfits de su clóset que más le gustarían.
2. **Fase 2 · ¿El outfit combina?:** reordena ese top con dos salidas, como en la mosca: **TTMn** (outfit real o falso) y **DLMn** (armonía 0–7 según 7 reglas). Se comparan una red con la conectividad del **Giant Fiber System** de *Drosophila* (MaleCNS v1.0, 327 neuronas) y sus controles: un MLP del mismo tamaño, la misma red con las conexiones barajadas, XGBoost y Random Forest.

**Hipótesis H1:** la red GFS ordena igual o mejor que sus controles (NDCG@5 por usuario, prueba de Wilcoxon).

| Documento | Para qué |
|---|---|
| [`docs/HALLAZGOS_HITO3.md`](docs/HALLAZGOS_HITO3.md) | Hallazgos y decisiones con sus cifras, ordenados por sección del informe |
| [`docs/DICCIONARIO_DATOS.md`](docs/DICCIONARIO_DATOS.md) | Diccionario de datos de la BD común (116 columnas) |
| [`docs/REVISION_Hito2_y_brechas_Hito3.md`](docs/REVISION_Hito2_y_brechas_Hito3.md) | Plan del Hito 3 (§12) y revisión del Hito 2 |

## Resultados del Hito 3

Ranking final sobre 100 outfits candidatos de test por usuario (350 usuarios simulados), con la media de 3 semillas:

| Exp. | Sistema | NDCG@5 |
|---|---|---|
| — | Azar | 0,492 |
| 1 | DeepFM solo | 0,750 |
| 2 | DeepFM + XGBoost | 0,758 |
| **3** | **DeepFM + Random Forest** | **0,767** |
| 4 | DeepFM + red GFS | 0,744 |
| 5 | DeepFM + MLP del mismo tamaño | 0,744 |
| 6 | DeepFM + GFS barajada | 0,748 |
| — | Techo (gusto real de la simulación) | 0,919 |

- **H1:** la red GFS empata con el MLP de igual tamaño (p = 0,98), pero no se distingue de su versión barajada (p = 0,48). Los datos **no apoyan** que la conectividad específica de la mosca aporte.
- **Mejor sistema:** DeepFM + Random Forest (experimento 3). Es el que usa `recomendar()`.
- **Impacto ODS 12:** el usuario aceptaría el 80,3 % de las recomendaciones, frente al 52,4 % si eligiera outfits al azar de su clóset. Todo se arma con prendas que ya tiene.

## Estructura

```
data/
  raw/                 Datos originales (catálogo de 500 prendas; outfits del Hito 2)
  mappings/            Tablas editables a mano (categoría de Polyvore → slot)
  external/            Descargas (Polyvore); no se suben a git
  processed/hito2/     Datos del Hito 2
  processed/hito3/     Datos del Hito 3 (prendas, outfits, conectoma, usuarios, candidatos, predicciones)
  revision/            Planillas de revisión manual
  BD_modelo_fly.xlsx   Base de datos común (lee y escribe recomendar())
notebooks/hito2/       01_EDA → 02_baseline · 03_conectoma_neuprint
notebooks/hito3/       00 → 08b (ver la tabla de abajo)
src/modelo_fly/        Código compartido por los notebooks
app/                   Dashboard: backend FastAPI y frontend HTML/JS
models/                Pesos del DeepFM para recomendar() (el resto de modelos no se sube)
results/hito2/         Métricas y figuras del Hito 2
results/hito3/         Métricas, figuras y tablas del Hito 3 (fase1/, fase2/, ranking/)
docs/                  Hallazgos, diccionario de datos, revisión y guía
entregas/hito2/        Informe, presentación y PDF tal como se entregaron
```

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
```

Los notebooks encuentran solos la raíz del repositorio, así que funcionan abiertos desde cualquier subcarpeta. Los que terminan en `_colab` se corren en **Google Colab**: clonan el repositorio solos y al final descargan un `.zip` con resultados, que se pega **sin descomprimir** en la carpeta del repositorio, al lado de este README. Necesitan PyTorch, XGBoost o una GPU, que no están en `requirements.txt`.

**Credenciales** (el repositorio es público, nunca se suben):
- **neuPrint** (05a): en Colab, secreto `NEUPRINT_TOKEN`.
- **Kaggle** (01c): en Colab, secretos `KAGGLE_USERNAME` y `KAGGLE_KEY`. En local, `kaggle.json` **fuera** del repositorio y la variable `KAGGLE_CONFIG_DIR` apuntando a su carpeta.

## Notebooks del Hito 3

Cada notebook explica en su primera celda qué hace, qué lee y qué escribe. Las salidas de `04` en adelante ya están en git, así que **desde `05a` cualquier notebook se puede correr sin repetir los anteriores**. Los pasos `00` a `04` van en orden, porque `00` descarga Polyvore y sus tablas intermedias no se suben (pesan mucho). `01c` no hace falta repetirlo: su tabla de colores está en git.

| Notebook | Dónde | Qué hace | Salida principal |
|---|---|---|---|
| `00_polyvore_descarga` | local | Descarga los metadatos de Polyvore (Han et al., 2017) | `polyvore_items.csv`, `polyvore_outfits.csv` |
| `01c_color_imagenes_colab` | Colab | Color dominante de las fotos de Polyvore (Kaggle) | `color_imagen_polyvore.csv` |
| `01_atributos` | local | Atributos de cada prenda desde su nombre y su foto | `polyvore_items_atributos.csv` |
| `01b_catalogo_propio` | local | Catálogo propio de 500 prendas → esquema común | `catalogo_propio.csv` |
| `02_validacion_muestra` | local | Validación manual de atributos (200 prendas) | `results/hito3/validacion_atributos.csv` |
| `03_particion` | local | Partición 70/15/15 sin productos compartidos | `particion_outfits.csv` |
| `04_negativos_reglas` | local | Outfits falsos (TTMn) y las 7 reglas (DLMn) | `fase2_productos.csv`, `fase2_outfits.csv` |
| `05a_conectoma_descarga_colab` | Colab | Descarga el Giant Fiber System de neuPrint | `gfs_nodes.csv`, `gfs_edges.csv` |
| `05b_conectoma_red` | local | Signo, máscara y estructura de la red | `gfs_neuronas.csv`, `gfs_conexiones.csv` |
| `06_usuarios_simulados` | local | 350 usuarios con clóset e historial de 50 decisiones | `usuarios.csv`, `closets.csv`, `historial.csv` |
| `07a_candidatos` | local | Candidatos de valid (50) y test (100) por usuario | `candidatos.csv` |
| `07b_fase2_colab` | Colab (GPU) | Fase 2: XGBoost, RF, red GFS y controles, con tuning y validación cruzada | `results/hito3/fase2/`, `fase2_pred_usuarios.csv.gz` |
| `07c_deepfm_colab` | Colab (GPU) | Fase 1: DeepFM con tuning y 3 semillas | `results/hito3/fase1/`, `deepfm_pred_candidatos.csv.gz` |
| `07d_ranking_final` | local | Los 6 experimentos, prueba de H1 y análisis de errores | `results/hito3/ranking/` |
| `08a_exportar_deepfm_colab` | Colab | Exporta los pesos del DeepFM ganador | `models/deepfm_pesos.npz` |
| `08b_bd_comun` | local | Arma la BD común, prueba `recomendar()` e impacto ODS 12 | `data/BD_modelo_fly.xlsx` |

Los CSV sin carpeta están en `data/processed/hito3/`.

## Recomendar a un usuario

```python
from pathlib import Path
import sys
sys.path.insert(0, "src")
from modelo_fly.recomendador import cargar_modelos, recomendar

ROOT = Path(".")
deepfm, rf_ttmn, rf_dlmn = cargar_modelos(ROOT)          # ~1,5 min: reentrena el Random Forest
candidatos, recomendaciones = recomendar("U001", ROOT / "data" / "BD_modelo_fly.xlsx",
                                         deepfm, rf_ttmn, rf_dlmn)
```

`recomendar()` lee del Excel el clóset y el historial del usuario y arma 200 outfits nuevos. Los pasa por las dos fases y escribe los 3 mejores, sin prendas repetidas, en las hojas `candidatos` y `predicciones`. Leer el libro tarda unos 40 s. Con `escribir=False` solo devuelve las filas.

## Dashboard

Interfaz web para el usuario, sobre la misma BD común. Backend en FastAPI (`app/backend/`) y frontend en HTML, CSS y JavaScript (`app/frontend/`):

```bash
uvicorn app.backend.main:app --port 8000      # desde la raíz del repositorio
```

Abrir http://localhost:8000 (o `http://localhost:8000/#U001` para ir directo a un usuario). La primera vez tarda ~2 min en cargar; las siguientes, ~40 s.

- **Mi clóset:** elige un usuario, ve su perfil y su clóset y pide 3 outfits. Cada outfit muestra su gusto (DeepFM), si parece real (TTMn) y su armonía (DLMn). Los botones **Me gusta / No me gusta** guardan la opinión en la columna `aceptado` de la hoja `predicciones`.
- **Resultados del modelo:** NDCG@5 de los 6 experimentos e indicadores del ODS 12.

Las recomendaciones y opiniones se escriben en `data/BD_modelo_fly.xlsx` en segundo plano, porque guardar el Excel tarda 2–3 min. Para probar sin modificar la BD del repositorio, apunta a una copia: `MODELO_FLY_BD=ruta/a/copia.xlsx`.

| Método | Ruta | Qué hace |
|---|---|---|
| GET | `/api/estado` | Si el modelo está cargado y cuántas escrituras faltan |
| GET | `/api/usuarios` | Lista de usuarios |
| GET | `/api/usuarios/{id}` | Perfil, clóset, historial y recomendaciones anteriores |
| POST | `/api/usuarios/{id}/recomendar` | 3 outfits nuevos (`recomendar()`) |
| POST | `/api/opiniones` | `{"outfit_id": "...", "aceptado": true}` |
| GET | `/api/resumen` | Métricas del ranking e impacto ODS 12 |

## Hito 2

1. `notebooks/hito2/01_EDA.ipynb` → `data/processed/hito2/outfits_unido.csv` y `results/hito2/figuras_eda/`.
2. `notebooks/hito2/02_baseline.ipynb` → `results/hito2/metricas_baseline*.csv`, `results/hito2/figuras_baseline/` y `models/modelo_baseline.joblib`.
3. `notebooks/hito2/03_conectoma_neuprint.ipynb` → necesita `NEUPRINT_TOKEN`; genera `data/conectoma/`.

Las métricas del Hito 2 tienen fuga entre particiones (ver `docs/REVISION…`, §2.4). Se conservan como referencia, no como línea base válida. En el Hito 3, el dataset se rehízo desde cero.
