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


# Campos del usuario que ve el DeepFM. Son los que daría una persona al registrarse en la app;
# el arquetipo y los pesos del gusto simulado quedan ocultos (son lo que el modelo debe aprender).
CAMPOS_USUARIO = ["user_id", "edad", "genero", "ciudad", "clima", "estilo_fav"]
GRUPOS_SLOT = {s: [i for i, c in enumerate(COLUMNAS) if c.startswith(f"{s}|")] for s in SLOTS}


def _edad(e):
    return "18-24" if e < 25 else ("25-34" if e < 35 else "35-45")


def codificar_usuarios(usuarios):
    """Tabla de usuarios → (dict user_id → fila de índices, uno por campo, y tamaño del vocabulario).
    Cada campo tiene su propio rango de índices en un vocabulario común."""
    valores = usuarios.assign(edad=usuarios["edad"].map(_edad))[CAMPOS_USUARIO].astype(str)
    indice, base = {}, 0
    for campo in CAMPOS_USUARIO:
        for v in sorted(valores[campo].unique()):
            indice[(campo, v)] = base
            base += 1
    filas = {u: [indice[(c, r[c])] for c in CAMPOS_USUARIO]
             for u, r in zip(usuarios["user_id"], valores.to_dict("records"))}
    return filas, base
