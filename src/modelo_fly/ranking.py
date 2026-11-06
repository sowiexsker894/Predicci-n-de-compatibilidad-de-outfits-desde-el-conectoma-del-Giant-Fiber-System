"""Métricas de ranking por usuario (etapa 7, revisión §12.6).

Cada usuario ordena sus candidatos por un puntaje y se mide contra lo que aceptó (1/0):
- NDCG@K (sklearn `ndcg_score`).
- Recall@K normalizado: aceptados dentro del top K / min(K, aceptados). Se normaliza porque
  cerca de la mitad de los candidatos son aceptados y el Recall@K clásico tendría un máximo
  bajo (5/49 con K = 5).
- HitRate@K: 1 si hay al menos un aceptado en el top K.
Los usuarios sin ningún aceptado (o con todos aceptados) no permiten medir el ranking y se
excluyen; la función devuelve cuántos quedaron fuera.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import ndcg_score

KS = (5, 10)


def por_usuario(candidatos, columna, ks=KS):
    """`candidatos`: user_id, aceptado y la columna de puntaje. → una fila por usuario medible."""
    filas = []
    for u, g in candidatos.groupby("user_id", sort=False):
        y = g["aceptado"].to_numpy()
        if y.min() == y.max():
            continue
        s = g[columna].to_numpy()
        orden = np.argsort(-s, kind="stable")
        fila = {"user_id": u}
        for k in ks:
            top = y[orden[:k]]
            fila[f"NDCG@{k}"] = ndcg_score([y], [s], k=k)
            fila[f"Recall@{k}"] = top.sum() / min(k, y.sum())
            fila[f"HitRate@{k}"] = float(top.sum() > 0)
        filas.append(fila)
    return pd.DataFrame(filas)


def resumen(candidatos, columna, ks=KS):
    """Promedio de las métricas sobre los usuarios medibles y cuántos se excluyeron."""
    d = por_usuario(candidatos, columna, ks)
    out = d.drop(columns="user_id").mean().to_dict()
    out["usuarios"] = len(d)
    out["excluidos"] = candidatos["user_id"].nunique() - len(d)
    return out
