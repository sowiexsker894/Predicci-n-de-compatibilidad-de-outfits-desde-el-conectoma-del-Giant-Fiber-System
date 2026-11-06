"""Codificación de un outfit como vector de entrada para los modelos de la fase 2 (etapa 7).

Cada outfit es una bolsa de prendas. Por cada slot se cuentan las prendas y cada valor de
cada atributo (multi-hot con conteo: dos joyas doradas suman 2 en `joyeria|tono=dorado`).
Los valores desconocido / no_aplica no activan nada. Todos los modelos (XGBoost, RF, MLP y
red GFS) reciben exactamente este mismo vector.
"""

import numpy as np

from .esquema import SLOTS, valores_validos, DESCONOCIDO, NO_APLICA

ATRIBUTOS_ENTRADA = ["tono", "familia_color", "patron", "material", "estilo", "calce", "epoca", "largo"]
_VOCAB = {a: sorted(valores_validos(a) - {DESCONOCIDO, NO_APLICA}) for a in ATRIBUTOS_ENTRADA}
COLUMNAS = [f"{s}|n" for s in SLOTS] + [f"{s}|{a}={v}" for s in SLOTS for a in ATRIBUTOS_ENTRADA for v in _VOCAB[a]]
_INDICE = {c: i for i, c in enumerate(COLUMNAS)}


def codificar(outfits, atrib):
    """`outfits`: lista de listas de IDs; `atrib`: ID → dict de atributos. → matriz (n, len(COLUMNAS))."""
    X = np.zeros((len(outfits), len(COLUMNAS)), dtype=np.float32)
    for fila, ids in enumerate(outfits):
        for i in ids:
            p = atrib[i]
            s = p["slot"]
            X[fila, _INDICE[f"{s}|n"]] += 1
            for a in ATRIBUTOS_ENTRADA:
                j = _INDICE.get(f"{s}|{a}={p[a]}")
                if j is not None:
                    X[fila, j] += 1
    return X
