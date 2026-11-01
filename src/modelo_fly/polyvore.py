"""Lectura de Polyvore (xthan/polyvore-dataset) y asignación de slots por categoría.

La asignación categoría → slot vive en data/mappings/polyvore_categorias.csv y se edita a mano.
"""

import json
import re

import pandas as pd

from .esquema import LARGOS, SLOTS
from .texto import leer_csv_editable

PARTICIONES = ["train", "valid", "test"]


def cargar_categorias(ruta):
    """Tabla de categorías con su slot; valida que todos los valores sean del esquema."""
    cat = leer_csv_editable(ruta, dtype=str, keep_default_na=False)
    slots_fuera = set(cat["slot"]) - set(SLOTS) - {"excluido"}
    largos_fuera = set(cat["largo"]) - set(LARGOS) - {""}
    if slots_fuera or largos_fuera:
        raise ValueError(f"Valores fuera del esquema: slot {sorted(slots_fuera)}, largo {sorted(largos_fuera)}")
    sin_motivo = cat[(cat["slot"] == "excluido") & (cat["motivo_exclusion"] == "")]
    if len(sin_motivo):
        raise ValueError(f"Categorías excluidas sin motivo: {sin_motivo['nombre'].tolist()}")
    con_motivo = cat[(cat["slot"] != "excluido") & (cat["motivo_exclusion"] != "")]
    if len(con_motivo):
        raise ValueError(f"Categorías con slot que conservan un motivo de exclusión: {con_motivo['nombre'].tolist()}")
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


def motivo_invalido(c):
    """Por qué un outfit no es vestible ('' si lo es). `c` cuenta los ítems de moda por slot.

    Regla (decidida el 01/11/2026): núcleo = un vestido solo, o una prenda de abajo con una o
    dos de arriba (capas); exactamente un calzado; como mucho un exterior. Bolsos, accesorios
    y joyería son libres.
    """
    if not c:
        return "sin items de moda"
    if c["vestido"] == 0 and not (c["arriba"] and c["abajo"]):
        return "sin nucleo (falta arriba, abajo o vestido)"
    if c["vestido"] and (c["arriba"] or c["abajo"]):
        return "vestido junto con arriba o abajo"
    if c["vestido"] > 1:
        return "mas de un vestido"
    if c["abajo"] > 1:
        return "mas de una prenda abajo"
    if c["arriba"] > 2:
        return "mas de dos prendas arriba"
    if c["calzado"] == 0:
        return "sin calzado"
    if c["calzado"] > 1:
        return "mas de un calzado"
    if c["exterior"] > 1:
        return "mas de un exterior"
    return ""


def filtrar_outfits(items):
    """Tabla de outfits con su composición por slot y si son vestibles.

    Solo cuentan los ítems de moda (los excluidos se quitan del outfit). Los outfits con el
    mismo conjunto de productos se marcan como duplicados y se queda el primero.
    """
    moda = items[items["slot"] != "excluido"]
    conteo = pd.crosstab(moda["set_id"], moda["slot"])
    for slot in SLOTS:
        if slot not in conteo.columns:
            conteo[slot] = 0
    outfits = items.groupby("set_id", sort=False).agg(
        particion_oficial=("particion_oficial", "first"),
        items_originales=("item_key", "size"),
    )
    outfits = outfits.join(conteo[SLOTS]).fillna(0)
    outfits[SLOTS] = outfits[SLOTS].astype(int)
    outfits["items_moda"] = outfits[SLOTS].sum(axis=1)
    outfits["motivo_invalido"] = [
        motivo_invalido({s: fila[s] for s in SLOTS} if fila["items_moda"] else {})
        for _, fila in outfits.iterrows()
    ]
    productos = moda.groupby("set_id")["tid"].agg(lambda s: "|".join(sorted(s)))
    outfits["productos"] = productos.reindex(outfits.index).fillna("")
    vestibles = outfits["motivo_invalido"] == ""
    duplicado = vestibles & outfits["productos"].duplicated() & outfits["productos"].ne("")
    outfits.loc[duplicado, "motivo_invalido"] = "duplicado (mismos productos que otro outfit)"
    outfits["valido"] = outfits["motivo_invalido"] == ""
    return outfits.reset_index()
