"""Negativos para la fase 2 (TTMn): outfits falsos con los mismos slots que un outfit real (etapa 4).

Por cada outfit real se arman dos negativos, siempre con productos de la **misma partición**
(así no se rompe la partición sin fuga del paso 4b):
- `aleatorio`: cada prenda se cambia por otra del mismo slot elegida al azar (protocolo de
  compatibilidad de Han et al., 2017). Mismo número de prendas y mismos slots que el real.
- `dificil`: se cambia **una sola** prenda por otra del mismo slot y, si se conoce, del mismo
  estilo (revisión §12.11, "negativos demasiado fáciles"). Es casi un outfit real.
Ningún negativo puede tener el mismo conjunto de productos que un outfit real.
"""

import numpy as np
import pandas as pd

from .esquema import DESCONOCIDO

TIPOS = ["aleatorio", "dificil"]


def _pools(productos):
    """Productos por (partición, slot) y por (partición, slot, estilo)."""
    por_slot = {k: g["tid"].to_numpy() for k, g in productos.groupby(["particion", "slot"])}
    con_estilo = productos[productos["estilo"] != DESCONOCIDO]
    por_estilo = {k: g["tid"].to_numpy() for k, g in con_estilo.groupby(["particion", "slot", "estilo"])}
    return por_slot, por_estilo


def _elegir(rng, pool, evitar, intentos=20):
    for _ in range(intentos):
        t = pool[rng.integers(len(pool))]
        if t not in evitar:
            return t
    return None


def generar(outfits, productos, semilla=2026):
    """`outfits`: set_id, particion, tids (lista ordenada de productos). `productos`: tid, slot,
    estilo, particion. Devuelve una fila por negativo: outfit_id, tipo, set_id_origen,
    particion, tids, cambiadas."""
    rng = np.random.default_rng(semilla)
    slot_de = dict(zip(productos["tid"], productos["slot"]))
    estilo_de = dict(zip(productos["tid"], productos["estilo"]))
    por_slot, por_estilo = _pools(productos)
    reales = {frozenset(t) for t in outfits["tids"]}
    vistos = set()
    filas = []
    for set_id, part, tids in zip(outfits["set_id"], outfits["particion"], outfits["tids"]):
        for tipo in TIPOS:
            for _ in range(10):  # reintentos si sale repetido o igual a uno real
                nuevo = list(tids)
                if tipo == "aleatorio":
                    cambiar = range(len(tids))
                else:
                    cambiar = [rng.integers(len(tids))]
                ok = True
                for i in cambiar:
                    original = tids[i]
                    pool = por_slot[(part, slot_de[original])]
                    if tipo == "dificil" and estilo_de[original] != DESCONOCIDO:
                        pool = por_estilo.get((part, slot_de[original], estilo_de[original]), pool)
                        if len(pool) < 2:
                            pool = por_slot[(part, slot_de[original])]
                    t = _elegir(rng, pool, set(nuevo))
                    if t is None:
                        ok = False
                        break
                    nuevo[i] = t
                clave = frozenset(nuevo)
                if ok and clave not in reales and clave not in vistos:
                    vistos.add(clave)
                    filas.append({"outfit_id": f"{set_id}_{tipo}", "tipo": tipo, "set_id_origen": set_id,
                                  "particion": part, "tids": nuevo,
                                  "cambiadas": len(tids) if tipo == "aleatorio" else 1})
                    break
    return pd.DataFrame(filas)
