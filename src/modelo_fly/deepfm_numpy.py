"""DeepFM en numpy, solo para predecir (etapa 8).

El modelo se entrena en Colab con PyTorch (`deepfm.py`) y sus pesos se exportan a
`models/deepfm_pesos.npz`. Esta versión hace exactamente el mismo cálculo hacia adelante sin
PyTorch, para que `recomendar()` funcione en cualquier computadora con el `requirements.txt`.
"""

import numpy as np


class DeepFMNumpy:
    def __init__(self, ruta, grupos_slot):
        p = np.load(ruta)
        self.emb_u, self.lin_u = p["emb_u.weight"], p["lin_u.weight"]
        self.emb_o, self.lin_o_w, self.lin_o_b = p["emb_o"], p["lin_o.weight"], p["lin_o.bias"]
        capas = sorted({int(k.split(".")[1]) for k in p.files if k.startswith("deep.")})
        self.deep = [(p[f"deep.{i}.weight"], p[f"deep.{i}.bias"]) for i in capas]
        self.grupos = [np.asarray(g) for g in grupos_slot]

    def logit(self, U, X):
        U, X = np.asarray(U), np.asarray(X, dtype=np.float32)
        eu = self.emb_u[U]                                        # (B, 6, k)
        lineal = self.lin_u[U].sum(axis=(1, 2)) + X @ self.lin_o_w[0] + self.lin_o_b[0]
        suma = eu.sum(1) + X @ self.emb_o
        cuad = (eu ** 2).sum(1) + (X ** 2) @ (self.emb_o ** 2)
        fm = 0.5 * (suma ** 2 - cuad).sum(1)
        h = np.concatenate([eu.reshape(len(U), -1), *[X[:, g] @ self.emb_o[g] for g in self.grupos]], axis=1)
        for i, (w, b) in enumerate(self.deep):
            h = h @ w.T + b
            if i < len(self.deep) - 1:
                h = np.maximum(h, 0)  # ReLU; el dropout no actúa al predecir
        return lineal + fm + h[:, 0]

    def predecir(self, U, X):
        return 1 / (1 + np.exp(-self.logit(U, X)))
