"""Integración con la BD común (etapa 8): `recomendar(user_id)` sobre el Excel `BD_modelo_fly.xlsx`.

Flujo (revisión §9.2 y §12.8), con el mejor sistema del paso 7d (experimento 3, DeepFM + Random
Forest, α y β elegidos en validación):
1. Lee del Excel el perfil del usuario, su clóset, los atributos de las prendas y su historial.
2. Arma outfits nuevos con su clóset (que no estén en su historial).
3. Fase 1: el DeepFM puntúa todos y se queda con el top 25 %.
4. Fase 2: el Random Forest da p(real) (TTMn) y la armonía 0–7 (DLMn) del top.
5. Puntaje final = α·pct(DeepFM) + (1 − α)·[β·pct(TTMn) + (1 − β)·pct(DLMn)].
6. Elige 3 outfits que no repitan prendas y escribe en las hojas `candidatos` y `predicciones`
   (`guardar`; con `escribir=False` solo devuelve las filas, para guardar varias en una sola escritura).
"""

from datetime import datetime

import numpy as np
import pandas as pd
from openpyxl import load_workbook

from .caracteristicas import GRUPOS_SLOT, codificar, codificar_usuarios
from .deepfm_numpy import DeepFMNumpy
from .ranking import dos_etapas
from .usuarios import ATRIBUTOS, armar_outfit, cargar_items

EXPERIMENTO = "3 · DeepFM + Random Forest"
ALFA, BETA = 0.6, 0.5  # results/hito3/ranking/ranking_alfa_beta.csv, experimento 3, semilla 0
TOP = 0.25
N_CANDIDATOS = 200
N_RECOMENDACIONES = 3
HOJAS_LECTURA = ["usuarios", "closets", "items", "historial"]


def leer_bd(ruta):
    return {h: pd.read_excel(ruta, sheet_name=h, dtype={"user_id": str, "item_id": str}, keep_default_na=False)
            for h in HOJAS_LECTURA}


def cargar_modelos(root):
    """DeepFM (pesos exportados en el paso 8a) y Random Forest de la fase 2, reentrenado en train
    con los hiperparámetros elegidos en el paso 7b. → (deepfm, rf_ttmn, rf_dlmn)."""
    import json

    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

    deepfm = DeepFMNumpy(root / "models" / "deepfm_pesos.npz", list(GRUPOS_SLOT.values()))
    hp = json.loads((root / "results" / "hito3" / "fase2" / "fase2_hiperparametros.json").read_text())["random_forest"]
    _, atrib, outfits = cargar_items(root / "data" / "processed" / "hito3")
    tr = outfits[outfits["particion"] == "train"]
    X = codificar(tr["ids"].tolist(), atrib)
    comun = {"n_estimators": 200, "n_jobs": -1, "random_state": 0}
    rf_ttmn = RandomForestClassifier(**comun, **hp["ttmn"]).fit(X, tr["real"].to_numpy())
    rf_dlmn = RandomForestRegressor(**comun, **hp["dlmn"]).fit(X, tr["score"].to_numpy(dtype=float))
    return deepfm, rf_ttmn, rf_dlmn


def _distintos(ids_por_outfit, orden, n):
    """Los `n` primeros outfits del orden que no comparten ninguna prenda."""
    elegidos, usadas = [], set()
    for i in orden:
        prendas = set(ids_por_outfit[i])
        if not prendas & usadas:
            elegidos.append(i)
            usadas |= prendas
        if len(elegidos) == n:
            break
    return elegidos


def recomendar(user_id, ruta_bd, deepfm, rf_ttmn, rf_dlmn, semilla=None, escribir=True, bd=None):
    """Devuelve (candidatos, recomendaciones) del usuario y, si `escribir`, los guarda en el Excel.
    `bd` (lo que devuelve `leer_bd`) evita volver a leer el libro cuando se recomienda a muchos."""
    bd = leer_bd(ruta_bd) if bd is None else bd
    usuarios = bd["usuarios"]
    if user_id not in set(usuarios["user_id"]):
        raise KeyError(f"El usuario {user_id} no está en la hoja usuarios")
    fila_u, n_vocab = codificar_usuarios(usuarios)
    if n_vocab != len(deepfm.emb_u):
        raise ValueError("La hoja usuarios no coincide con la usada para entrenar el DeepFM "
                         f"({n_vocab} vs {len(deepfm.emb_u)} valores); hay que reentrenarlo")
    closet = bd["closets"].loc[bd["closets"]["user_id"] == user_id, ["item_id"]].merge(bd["items"], on="item_id")
    atrib = closet.set_index("item_id")[ATRIBUTOS].to_dict("index")
    por_slot = {s: g["item_id"].tolist() for s, g in closet.groupby("slot")}
    vistos = {frozenset(str(i).split("|")) for i in bd["historial"].loc[bd["historial"]["user_id"] == user_id, "item_ids"]}

    rng = np.random.default_rng(semilla)
    outfits = []
    for _ in range(50 * N_CANDIDATOS):
        ids = armar_outfit(rng, por_slot)
        if frozenset(ids) not in vistos:
            vistos.add(frozenset(ids))
            outfits.append(ids)
        if len(outfits) == N_CANDIDATOS:
            break

    X = codificar(outfits, atrib)
    U = np.array([fila_u[user_id]] * len(outfits))
    p_dfm = deepfm.predecir(U, X)
    p_ttmn = rf_ttmn.predict_proba(X)[:, 1]
    dlmn = rf_dlmn.predict(X)
    top = max(1, int(TOP * len(outfits)))
    final = dos_etapas(p_dfm[None], p_ttmn[None], dlmn[None], ALFA, BETA, top)[0]
    en_top = final >= 2  # dos_etapas suma 2 a los del top
    orden = np.argsort(-final, kind="stable")

    ahora = datetime.now().isoformat(timespec="seconds")
    sello = datetime.now().strftime("%Y%m%d%H%M%S")
    ids_outfit = [f"{user_id}_R{sello}_{i + 1:03d}" for i in range(len(outfits))]
    candidatos = pd.DataFrame({"user_id": user_id, "outfit_id": ids_outfit, "item_ids": ["|".join(o) for o in outfits],
                               "p_deepfm": p_dfm.round(5), "en_top": en_top.astype(int), "origen": "recomendar",
                               "fecha": ahora})
    elegidos = _distintos(outfits, [i for i in orden if en_top[i]], N_RECOMENDACIONES)
    recomendaciones = pd.DataFrame({
        "user_id": user_id, "outfit_id": [ids_outfit[i] for i in elegidos],
        "item_ids": ["|".join(outfits[i]) for i in elegidos], "experimento": EXPERIMENTO,
        "p_deepfm": p_dfm[elegidos].round(5), "p_ttmn": p_ttmn[elegidos].round(5), "dlmn": dlmn[elegidos].round(3),
        "score_final": (final[elegidos] - 2).round(5), "rango": np.arange(1, len(elegidos) + 1),
        "origen": "recomendar", "fecha": ahora})
    if escribir:
        guardar(ruta_bd, candidatos, recomendaciones)
    return candidatos, recomendaciones


def guardar(ruta, candidatos, predicciones):
    """Agrega filas al final de las hojas `candidatos` y `predicciones`, en el orden de sus columnas."""
    libro = load_workbook(ruta)
    for hoja, df in {"candidatos": candidatos, "predicciones": predicciones}.items():
        ws = libro[hoja]
        columnas = [c.value for c in ws[1]]
        for fila in df.reindex(columns=columnas).itertuples(index=False):
            ws.append([None if (isinstance(v, float) and np.isnan(v)) else (v.item() if hasattr(v, "item") else v)
                       for v in fila])
    libro.save(ruta)
