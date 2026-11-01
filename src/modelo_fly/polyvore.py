"""Lectura de Polyvore (xthan/polyvore-dataset) y asignación de slots por categoría.

La asignación categoría → slot vive en data/mappings/polyvore_categorias.csv y se edita a mano.
"""

import json
import re

import pandas as pd

from .esquema import LARGOS, SLOTS

PARTICIONES = ["train", "valid", "test"]


def cargar_categorias(ruta):
    """Tabla de categorías con su slot; valida que todos los valores sean del esquema."""
    cat = pd.read_csv(ruta, dtype=str, keep_default_na=False)
    slots_fuera = set(cat["slot"]) - set(SLOTS) - {"excluido"}
    largos_fuera = set(cat["largo"]) - set(LARGOS) - {""}
    if slots_fuera or largos_fuera:
        raise ValueError(f"Valores fuera del esquema: slot {sorted(slots_fuera)}, largo {sorted(largos_fuera)}")
    sin_motivo = cat[(cat["slot"] == "excluido") & (cat["motivo_exclusion"] == "")]
    if len(sin_motivo):
        raise ValueError(f"Categorías excluidas sin motivo: {sin_motivo['nombre'].tolist()}")
    if not cat["categoryid"].is_unique:
        raise ValueError("categoryid repetido en la tabla de categorías")
    return cat


def tid(url):
    """Id del producto en Polyvore, sacado de la URL de su imagen."""
    m = re.search(r"tid=(\d+)", url)
    return m.group(1) if m else None


def cargar_items(carpeta):
    """Un ítem por fila: outfit, posición, producto, partición oficial y texto."""
    filas = []
    for particion in PARTICIONES:
        outfits = json.loads((carpeta / f"{particion}_no_dup.json").read_text(encoding="utf-8"))
        for o in outfits:
            for it in o["items"]:
                filas.append({
                    "item_key": f"{o['set_id']}_{it['index']}",  # mismo formato que fill_in_blank_test.json
                    "set_id": o["set_id"],
                    "index": it["index"],
                    "tid": tid(it["image"]),
                    "particion_oficial": particion,
                    "categoryid": str(it["categoryid"]),
                    "name": it["name"].strip(),
                    "price": it["price"],
                    "likes": it["likes"],
                })
    items = pd.DataFrame(filas)
    if not items["item_key"].is_unique:
        raise ValueError("item_key repetido")
    return items


def asignar_slots(items, categorias):
    """Une cada ítem con el slot, largo por categoría y género de su categoría."""
    cols = categorias[["categoryid", "nombre", "slot", "motivo_exclusion", "largo", "genero"]]
    out = items.merge(cols.rename(columns={"nombre": "categoria", "largo": "largo_categoria"}),
                      on="categoryid", how="left", validate="many_to_one")
    faltan = out.loc[out["slot"].isna(), "categoryid"].unique()
    if len(faltan):
        raise ValueError(f"categoryid sin fila en la tabla de categorías: {sorted(faltan)}")
    return out
