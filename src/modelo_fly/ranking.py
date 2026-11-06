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


def matrices(candidatos, columna):
    """Candidatos de una partición (misma cantidad por usuario) → (usuarios, Y, S): una fila por
    usuario con lo aceptado y el puntaje, en el orden de `candidatos`."""
    g = candidatos.groupby("user_id", sort=False)
    n = g.size()
    if n.nunique() != 1:
        raise ValueError("Todos los usuarios deben tener la misma cantidad de candidatos")
    usuarios = n.index.to_numpy()
    Y = candidatos["aceptado"].to_numpy().reshape(len(usuarios), -1)
    S = candidatos[columna].to_numpy(dtype=float).reshape(len(usuarios), -1)
    return usuarios, Y, S


def metricas_rapidas(Y, S, ks=KS):
    """Misma definición que `por_usuario`, vectorizada (empates: orden estable). → dict de arrays
    por usuario, con NaN en los usuarios que no se pueden medir."""
    orden = np.argsort(-S, axis=1, kind="stable")
    Yo = np.take_along_axis(Y, orden, axis=1)
    pos = Y.sum(axis=1)
    medible = (pos > 0) & (pos < Y.shape[1])
    descuento = 1 / np.log2(np.arange(2, Y.shape[1] + 2))
    out = {}
    for k in ks:
        dcg = (Yo[:, :k] * descuento[:k]).sum(axis=1)
        idcg = np.array([descuento[:min(k, p)].sum() for p in pos])
        hits = Yo[:, :k].sum(axis=1)
        out[f"NDCG@{k}"] = np.where(medible, dcg / np.maximum(idcg, 1e-12), np.nan)
        out[f"Recall@{k}"] = np.where(medible, hits / np.maximum(np.minimum(k, pos), 1), np.nan)
        out[f"HitRate@{k}"] = np.where(medible, (hits > 0).astype(float), np.nan)
    return out


def percentil(S):
    """Rango percentil de cada puntaje dentro de su usuario (fila), entre 0 y 1."""
    r = np.argsort(np.argsort(S, axis=1, kind="stable"), axis=1, kind="stable")
    return (r + 1) / S.shape[1]


def dos_etapas(P_dfm, T, D, alfa, beta, top):
    """Ranking final (revisión §12.4): el DeepFM elige su top `top` y la fase 2 lo reordena con
    score = α · pct(DeepFM) + (1 − α) · [β · pct(TTMn) + (1 − β) · pct(DLMn)].
    Los candidatos fuera del top quedan debajo, en el orden del DeepFM. α = 1 es el DeepFM solo."""
    dfm = percentil(P_dfm)
    fase2 = beta * percentil(T) + (1 - beta) * percentil(D)
    final = alfa * dfm + (1 - alfa) * fase2
    corte = np.sort(P_dfm, axis=1)[:, -top][:, None]
    en_top = P_dfm >= corte
    return np.where(en_top, 2 + final, dfm)
