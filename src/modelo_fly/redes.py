"""Redes de la fase 2 en PyTorch (etapa 7): red con la conectividad del GFS y el MLP de control.

Las dos salidas son las de la mosca: TTMn (outfit real o falso, logit) y DLMn (armonía 0–7,
regresión sobre score/7). Pérdida = BCE(TTMn) + MSE(DLMn).

Red GFS (Opción A, revisión §12): el vector del outfit entra por una capa lineal a las 311
neuronas de entrada (LC4, LPLC2) y se propaga `PASOS` veces por la matriz
W = signo ⊙ softplus(θ) ⊙ máscara (fila = post, columna = pre). Solo existe un peso por cada
conexión real de neuPrint. La lectura se hace en las 2 TTMn y en las 10 DLMn. La Opción B deja
θ fijo (pesos de neuPrint) y el experimento 6 usa la misma red con las conexiones barajadas.
"""

import numpy as np
import torch
import torch.nn.functional as F
from torch import nn

PASOS = 4  # la entrada llega a TTMn en 2 saltos y a DLMn en 3


def _softplus_inv(w):
    return np.log(np.expm1(np.maximum(w, 1e-6)))


class RedGFS(nn.Module):
    def __init__(self, n_entrada, conteo, signo, idx_entrada, idx_ttmn, idx_dlmn, entrenar_pesos=True):
        super().__init__()
        post, pre = np.nonzero(conteo)
        w0 = np.log1p(conteo)
        suma = w0.sum(axis=1, keepdims=True)
        w0 = np.divide(w0, suma, out=np.zeros_like(w0), where=suma > 0)  # cada neurona recibe en total 1
        theta0 = torch.tensor(_softplus_inv(w0[post, pre]), dtype=torch.float32)
        self.n = conteo.shape[0]
        self.register_buffer("post", torch.tensor(post, dtype=torch.long))
        self.register_buffer("pre", torch.tensor(pre, dtype=torch.long))
        self.register_buffer("signo_arista", torch.tensor(np.asarray(signo)[pre], dtype=torch.float32))
        self.register_buffer("idx_entrada", torch.tensor(idx_entrada, dtype=torch.long))
        self.register_buffer("idx_ttmn", torch.tensor(idx_ttmn, dtype=torch.long))
        self.register_buffer("idx_dlmn", torch.tensor(idx_dlmn, dtype=torch.long))
        self.theta = nn.Parameter(theta0, requires_grad=entrenar_pesos)
        self.entrada = nn.Linear(n_entrada, len(idx_entrada))
        self.sesgo = nn.Parameter(torch.zeros(self.n))
        self.ttmn = nn.Linear(len(idx_ttmn), 1)
        self.dlmn = nn.Linear(len(idx_dlmn), 1)

    def matriz(self):
        W = torch.zeros(self.n, self.n, device=self.theta.device)
        return W.index_put((self.post, self.pre), self.signo_arista * F.softplus(self.theta))

    def forward(self, x):
        u = torch.zeros(x.shape[0], self.n, device=x.device)
        u[:, self.idx_entrada] = self.entrada(x)
        W = self.matriz()
        h = F.relu(u)
        for _ in range(PASOS):
            h = F.relu(h @ W.T + self.sesgo + u)
        return self.ttmn(h[:, self.idx_ttmn]).squeeze(1), self.dlmn(h[:, self.idx_dlmn]).squeeze(1)


class MLP(nn.Module):
    """Control del experimento 5: dos capas ocultas de ancho `oculto`, mismas dos salidas."""

    def __init__(self, n_entrada, oculto):
        super().__init__()
        self.cuerpo = nn.Sequential(nn.Linear(n_entrada, oculto), nn.ReLU(), nn.Linear(oculto, oculto), nn.ReLU())
        self.ttmn = nn.Linear(oculto, 1)
        self.dlmn = nn.Linear(oculto, 1)

    def forward(self, x):
        h = self.cuerpo(x)
        return self.ttmn(h).squeeze(1), self.dlmn(h).squeeze(1)


def parametros(modelo):
    return sum(p.numel() for p in modelo.parameters() if p.requires_grad)


def ancho_mlp(n_entrada, objetivo):
    """Ancho de capa oculta con el que el MLP tiene el número de parámetros más cercano a `objetivo`."""
    n_mlp = lambda h: n_entrada * h + h + h * h + h + 2 * (h + 1)  # = parametros(MLP(n_entrada, h))
    return min(range(8, 4096), key=lambda h: abs(n_mlp(h) - objetivo))


def entrenar(modelo, X, real, score, X_val, real_val, score_val, semilla, epocas=40, paciencia=5,
             lote=512, lr=1e-3, dispositivo="cpu"):
    """Entrena con AdamW y se queda con la época de menor pérdida en validación."""
    torch.manual_seed(semilla)
    modelo.to(dispositivo)
    t = lambda a: torch.tensor(np.asarray(a), dtype=torch.float32, device=dispositivo)
    X, real, score = t(X), t(real), t(score) / 7
    X_val, real_val, score_val = t(X_val), t(real_val), t(score_val) / 7
    opt = torch.optim.AdamW([p for p in modelo.parameters() if p.requires_grad], lr=lr, weight_decay=1e-4)
    gen = torch.Generator(device="cpu").manual_seed(semilla)

    def perdida(xb, rb, sb):
        lt, d = modelo(xb)
        return F.binary_cross_entropy_with_logits(lt, rb) + F.mse_loss(d, sb)

    mejor, estado, sin_mejora, curva = np.inf, None, 0, []
    for epoca in range(epocas):
        modelo.train()
        orden = torch.randperm(len(X), generator=gen).to(dispositivo)
        for k in range(0, len(X), lote):
            b = orden[k:k + lote]
            opt.zero_grad()
            perdida(X[b], real[b], score[b]).backward()
            opt.step()
        modelo.eval()
        with torch.no_grad():
            val = perdida(X_val, real_val, score_val).item()
        curva.append(val)
        if val < mejor - 1e-4:
            mejor, sin_mejora = val, 0
            estado = {k: v.detach().clone() for k, v in modelo.state_dict().items()}
        else:
            sin_mejora += 1
            if sin_mejora >= paciencia:
                break
    modelo.load_state_dict(estado)
    return curva


def predecir(modelo, X, dispositivo="cpu", lote=4096):
    """→ (probabilidad de real, score DLMn en escala 0–7)."""
    modelo.eval()
    pr, sc = [], []
    with torch.no_grad():
        for k in range(0, len(X), lote):
            xb = torch.tensor(np.asarray(X[k:k + lote]), dtype=torch.float32, device=dispositivo)
            lt, d = modelo(xb)
            pr.append(torch.sigmoid(lt).cpu().numpy())
            sc.append((d * 7).cpu().numpy())
    return np.concatenate(pr), np.concatenate(sc)
