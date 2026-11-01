# Modelo Fly · Predicción de compatibilidad de outfits desde el conectoma del Giant Fiber System

Proyecto del curso de Machine Learning (UPC). Recomendador de outfits en dos etapas: un **DeepFM** filtra las combinaciones del clóset del usuario y una red con la conectividad del **Giant Fiber System** de la mosca (MaleCNS v1.0, 327 neuronas) da el puntaje final.

El plan vigente del Hito 3 está en [`docs/REVISION_Hito2_y_brechas_Hito3.md`](docs/REVISION_Hito2_y_brechas_Hito3.md), §12.

## Estructura

```
data/
  raw/                 Datos originales (catálogo de 500 prendas, 100 000 outfits, 30 casos)
  processed/hito2/     Particiones y outfits_unido.csv (lo genera 01_EDA)
  conectoma/           nodes.csv, edges.csv (lo genera 03_conectoma_neuprint)
  revision/            Planillas de revisión manual (las llena el equipo)
notebooks/hito2/       01_EDA → 02_baseline · 03_conectoma_neuprint
notebooks/hito3/       01b_catalogo_propio → …
src/modelo_fly/        Código compartido: esquema común de atributos y mapeo del catálogo
results/hito2/         Métricas y figuras del baseline y del EDA
results/hito3/         Resúmenes del Hito 3
docs/                  Revisión del proyecto y guía de exposición
entregas/hito2/        Informe, presentación y PDF tal como se entregaron
models/                Modelos entrenados (no se suben)
```

## Cómo ejecutar

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
```

Orden de los notebooks del Hito 2:

1. `notebooks/hito2/01_EDA.ipynb` → genera `data/processed/hito2/outfits_unido.csv` y `results/hito2/figuras_eda/`.
2. `notebooks/hito2/02_baseline.ipynb` → genera `results/hito2/metricas_baseline*.csv`, `results/hito2/figuras_baseline/` y `models/modelo_baseline.joblib`.
3. `notebooks/hito2/03_conectoma_neuprint.ipynb` → necesita un token de [neuPrint](https://neuprint.janelia.org) en la variable de entorno `NEUPRINT_TOKEN` (en Colab, como secreto con ese nombre). Genera `data/conectoma/`.

Los notebooks encuentran solos la raíz del repositorio, así que funcionan abiertos desde cualquier subcarpeta. En Colab: `!git clone <url>` y `%cd <carpeta>` antes de ejecutar.

Hito 3:

- `notebooks/hito3/01b_catalogo_propio.ipynb` → pasa el catálogo de 500 al esquema común (`data/processed/hito3/catalogo_propio.csv`) y genera la planilla `data/revision/catalogo_propio_revision.xlsx`. Después de llenar la columna `decision` de la planilla, se vuelve a ejecutar para aplicar las decisiones.

## Notas

- `data/processed/hito2/outfits_{train,validation,test}_100k.csv` venían con la entrega, pero ningún notebook los genera: `02_baseline` hace su propia partición en memoria (semilla 42).
- Las métricas del Hito 2 tienen fuga entre particiones (ver `docs/REVISION…`, §2.4). Se conservan como referencia, no como línea base válida.
