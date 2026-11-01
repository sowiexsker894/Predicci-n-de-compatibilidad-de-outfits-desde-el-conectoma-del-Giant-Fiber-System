"""Validación manual de los atributos de Polyvore con una muestra (paso 4 de la etapa 3).

Se sacan 25 prendas por slot (200 en total) entre las que tienen foto, se bajan solo esas
fotos de Kaggle y se arma una planilla con la foto y los atributos. Quien revisa marca `si`
o `no` en cada atributo; los desconocidos y los que no aplican vienen con `-`.
"""

import io
import math
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from PIL import Image

from .esquema import DESCONOCIDO, NO_APLICA

DATASET = "akshaypujari124/polyvore-images"
PREFIJO = "Re-PolyVore/Re-PolyVore/Re-PolyVore"
A_REVISAR = ["slot", "tono", "familia_color", "patron", "material", "estilo", "calce", "largo"]
RESPUESTAS = ["si", "no", "-"]
MINIATURA = 110  # píxeles


def muestra_estratificada(items, por_slot, semilla):
    """`por_slot` prendas al azar de cada slot, en un orden mezclado para no revisar por bloques."""
    m = items.groupby("slot", group_keys=False).sample(n=por_slot, random_state=semilla)
    return m.sample(frac=1, random_state=semilla).reset_index(drop=True)


def ruta_foto(carpeta, fila):
    return carpeta / f"{fila['clave_foto']}.jpg"


def descargar_fotos(muestra, carpeta):
    """Baja de Kaggle solo las fotos que faltan. Usa el token de KAGGLE_CONFIG_DIR (fuera del repo)."""
    carpeta.mkdir(parents=True, exist_ok=True)
    kaggle = Path(sys.executable).with_name("kaggle.exe" if os.name == "nt" else "kaggle")

    def bajar(f):
        remoto = f"{PREFIJO}/{f['carpeta_foto']}/{f['clave_foto']}.jpg"
        tmp = carpeta / f"_tmp_{f['clave_foto']}"
        r = subprocess.run([str(kaggle), "datasets", "download", DATASET, "-f", remoto, "-p", str(tmp), "-q"],
                           capture_output=True, text=True)
        bajado = next(tmp.rglob(f"{f['clave_foto']}.jpg"), None) if tmp.exists() else None
        if bajado is not None:
            bajado.replace(ruta_foto(carpeta, f))
        shutil.rmtree(tmp, ignore_errors=True)
        return None if bajado is not None else (f["item_key"], (r.stderr or r.stdout).strip()[-200:])

    pendientes = [f for _, f in muestra.iterrows() if not ruta_foto(carpeta, f).exists()]
    with ThreadPoolExecutor(max_workers=8) as ex:
        return [x for x in ex.map(bajar, pendientes) if x]


def _miniatura(ruta):
    img = Image.open(ruta).convert("RGB")
    img.thumbnail((MINIATURA, MINIATURA))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return XLImage(buf)


def escribir_planilla(muestra, carpeta_fotos, ruta, previa=None):
    """Planilla con foto, atributos y columnas `ok_<atributo>` para marcar si/no.

    Si `previa` trae respuestas ya escritas (misma `item_key`), se conservan.
    """
    info = ["n", "item_key", "foto", "name", "categoria", *A_REVISAR, "origen_tono"]
    manual = [f"ok_{a}" for a in A_REVISAR] + ["correccion", "nota"]
    df = muestra.copy()
    df.insert(0, "n", range(1, len(df) + 1))
    df["foto"] = ""
    for a in A_REVISAR:
        df[f"ok_{a}"] = df[a].map(lambda v: "-" if v in (DESCONOCIDO, NO_APLICA) else "")
    df["correccion"] = df["nota"] = ""
    if previa is not None:
        previa = previa.set_index("item_key")
        for c in manual:
            if c in previa.columns:
                hay = df["item_key"].map(previa[c]).fillna("").astype(str).str.strip()
                df[c] = hay.where(hay != "", df[c])

    wb = Workbook()
    ws = wb.active
    ws.title = "revision"
    columnas = info + manual
    ws.append(columnas)
    gris, amarillo = PatternFill("solid", fgColor="DDDDDD"), PatternFill("solid", fgColor="FFF2CC")
    for j, c in enumerate(columnas, start=1):
        celda = ws.cell(row=1, column=j)
        celda.font = Font(bold=True)
        celda.fill = amarillo if c in manual else gris
    for i, (_, f) in enumerate(df.iterrows(), start=2):
        ws.append([f[c] for c in columnas])
        ws.row_dimensions[i].height = MINIATURA * 0.78
        foto = ruta_foto(carpeta_fotos, f)
        if foto.exists():
            ws.add_image(_miniatura(foto), f"C{i}")
        for j in range(1, len(columnas) + 1):
            ws.cell(row=i, column=j).alignment = Alignment(vertical="center", wrap_text=True)
    anchos = {"n": 5, "item_key": 13, "foto": 17, "name": 38, "categoria": 16, "origen_tono": 12,
              "correccion": 28, "nota": 28}
    for j, c in enumerate(columnas, start=1):
        ws.column_dimensions[ws.cell(row=1, column=j).column_letter].width = anchos.get(c, 11)
    dv = DataValidation(type="list", formula1='"' + ",".join(RESPUESTAS) + '"', allow_blank=True)
    ws.add_data_validation(dv)
    for c in manual[:-2]:
        letra = ws.cell(row=1, column=columnas.index(c) + 1).column_letter
        dv.add(f"{letra}2:{letra}{len(df) + 1}")
    ws.freeze_panes = "D2"
    wb.save(ruta)
    return df


def wilson(k, n, z=1.96):
    """Intervalo de confianza de Wilson (95 %) para una proporción k/n."""
    if n == 0:
        return (math.nan, math.nan)
    p = k / n
    centro = (p + z * z / (2 * n)) / (1 + z * z / n)
    margen = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (centro - margen, centro + margen)


def precision(revision):
    """Precisión por atributo (y por origen del tono) con las respuestas si/no de la planilla."""
    filas = []
    for a in A_REVISAR:
        r = revision[f"ok_{a}"].astype(str).str.strip().str.lower()
        k, n = int((r == "si").sum()), int(r.isin(["si", "no"]).sum())
        bajo, alto = wilson(k, n)
        filas.append({"atributo": a, "revisadas": n, "correctas": k,
                      "precision_%": round(100 * k / n, 1) if n else math.nan,
                      "ic95_bajo_%": round(100 * bajo, 1), "ic95_alto_%": round(100 * alto, 1),
                      "sin_marcar": int((r.isin(["", "nan"])).sum())})
    return pd.DataFrame(filas)
