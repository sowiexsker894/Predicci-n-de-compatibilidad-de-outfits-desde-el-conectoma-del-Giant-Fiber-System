"""Conectoma del Giant Fiber System (MaleCNS v1.0, 327 neuronas) como red del modelo (etapa 5).

Los archivos crudos salen de neuPrint con notebooks/hito3/05a_conectoma_descarga_colab.ipynb
(necesita token). Aquí se fija el signo de cada neurona y se arman las matrices, sin token.

Convención de matrices (igual que la simulación del Hito 2): fila = neurona postsináptica,
columna = presináptica. La Opción A del modelo usa W = signo ⊙ softplus(θ) ⊙ máscara, con el
signo de la neurona **presináptica** (revisión §12).

Neurotransmisor de cada neurona, en este orden:
1. `consensusNt` (anotación consolidada de MaleCNS), si no es "unclear";
2. `celltypePredictedNt` (predicción agregada del tipo), si su confianza es ≥ CONF_MIN;
3. la literatura para el tipo (NT_LITERATURA); hay que verificar las citas en el informe.
Signo: acetilcolina excitadora (+1); glutamato, GABA e histamina inhibidores (−1), la
convención de los modelos de cerebro completo de Drosophila (Shiu et al., 2024).
"""

import numpy as np
import pandas as pd

CAPAS = ["entrada", "decision", "salida"]
TIPOS = ["LC4", "LPLC2", "DNp01", "PSI", "TTMn", "DLMn a, b", "DLMn c-f"]
SALIDA_TTMN = ["TTMn"]
SALIDA_DLMN = ["DLMn a, b", "DLMn c-f"]
SIGNO_NT = {"acetylcholine": 1, "glutamate": -1, "gaba": -1, "histamine": -1}
CONF_MIN = 0.5
# Tipos que neuPrint deja en "unclear": PSI es colinérgico (sinapsis PSI→DLMn) y las motoneuronas
# de Drosophila son glutamatérgicas.
NT_LITERATURA = {"PSI": "acetylcholine", "TTMn": "glutamate", "DLMn a, b": "glutamate", "DLMn c-f": "glutamate"}
SIN_NT = {"unclear", ""}


def neurotransmisor(nodes):
    """Neurotransmisor final, su origen y el signo de cada neurona (mismo índice que `nodes`)."""
    def elegir(fila):
        consenso = fila["consensusNt"] if isinstance(fila["consensusNt"], str) else ""
        tipo_nt = fila["celltypePredictedNt"] if isinstance(fila["celltypePredictedNt"], str) else ""
        if consenso not in SIN_NT:
            return consenso, "consenso"
        if tipo_nt not in SIN_NT and fila["celltypePredictedNtConfidence"] >= CONF_MIN:
            return tipo_nt, "prediccion_tipo"
        if fila["type"] in NT_LITERATURA:
            return NT_LITERATURA[fila["type"]], "literatura"
        raise ValueError(f"Sin neurotransmisor para {fila['bodyId']} ({fila['type']})")

    nt, origen = zip(*(elegir(f) for f in nodes.to_dict("records")))
    fuera = set(nt) - set(SIGNO_NT)
    if fuera:
        raise ValueError(f"Neurotransmisor sin signo definido: {sorted(fuera)}")
    return pd.DataFrame({"nt": list(nt), "origen_nt": list(origen), "signo": [SIGNO_NT[n] for n in nt]}, index=nodes.index)


def neuronas(nodes):
    """Tabla de las 327 neuronas en el orden de la red (capa, tipo, lado, bodyId) con su signo."""
    orden = nodes.assign(_capa=nodes["capa"].map(CAPAS.index), _tipo=nodes["type"].map(TIPOS.index))
    orden = orden.sort_values(["_capa", "_tipo", "side", "bodyId"]).reset_index(drop=True)
    base = orden[["bodyId", "type", "side", "capa", "predictedNt", "consensusNt",
                  "celltypePredictedNt", "celltypePredictedNtConfidence"]]
    return pd.concat([base, neurotransmisor(orden)], axis=1).rename_axis("idx").reset_index()


def matrices(tabla, edges):
    """`tabla` de `neuronas()` y aristas (bodyId_pre, bodyId_post, weight) → conteo sináptico,
    máscara y matriz con signo (N×N, fila = post, columna = pre)."""
    idx = dict(zip(tabla["bodyId"], tabla["idx"]))
    n = len(tabla)
    conteo = np.zeros((n, n))
    conteo[edges["bodyId_post"].map(idx), edges["bodyId_pre"].map(idx)] = edges["weight"]
    mascara = (conteo > 0).astype(np.int8)
    con_signo = conteo * tabla["signo"].to_numpy()[None, :]
    return conteo, mascara, con_signo
