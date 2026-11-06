"""DeepFM de la fase 1 (etapa 7): p(al usuario le gusta este outfit).

Guo et al. (2017). Cada ejemplo es (usuario, outfit) con la etiqueta aceptado 1/0 del historial.
Variables:
- usuario: 6 campos categóricos (`caracteristicas.CAMPOS_USUARIO`), uno activo por campo;
- outfit: el mismo vector multi-hot de 464 columnas que la fase 2.
Las tres partes comparten los embeddings de dimensión k:
- lineal: suma de pesos de las variables activas;
- FM: interacciones de a pares entre todas las variables (usuario × prenda y prenda × prenda);
- deep: MLP sobre los embeddings de los 6 campos del usuario y la suma por slot del outfit.
"""

import numpy as np
import torch
import torch.nn.functional as F
from torch import nn


class DeepFM(nn.Module):
    def __init__(self, n_vocab_usuario, n_outfit, grupos_slot, k=16, oculto=(128, 64), dropout=0.2):
        super().__init__()
        self.emb_u = nn.Embedding(n_vocab_usuario, k)
        self.lin_u = nn.Embedding(n_vocab_usuario, 1)
        self.emb_o = nn.Parameter(torch.randn(n_outfit, k) * 0.01)
        self.lin_o = nn.Linear(n_outfit, 1)
        nn.init.normal_(self.emb_u.weight, std=0.01)
        nn.init.zeros_(self.lin_u.weight)
        self.grupos = [torch.tensor(g, dtype=torch.long) for g in grupos_slot]
        capas, entrada = [], k * (6 + len(grupos_slot))
        for h in oculto:
            capas += [nn.Linear(entrada, h), nn.ReLU(), nn.Dropout(dropout)]
            entrada = h
        self.deep = nn.Sequential(*capas, nn.Linear(entrada, 1))

    def forward(self, u, x):
        """u: (B, 6) índices de usuario; x: (B, n_outfit) multi-hot del outfit. → logit (B,)."""
        eu = self.emb_u(u)                                   # (B, 6, k)
        lineal = self.lin_u(u).sum(dim=(1, 2)) + self.lin_o(x).squeeze(1)
        suma = eu.sum(1) + x @ self.emb_o                    # Σ x_i v_i
        cuad = (eu ** 2).sum(1) + (x ** 2) @ (self.emb_o ** 2)
        fm = 0.5 * (suma ** 2 - cuad).sum(1)
        slots = [x[:, g.to(x.device)] @ self.emb_o[g.to(x.device)] for g in self.grupos]
        deep = self.deep(torch.cat([eu.flatten(1), *slots], dim=1)).squeeze(1)
        return lineal + fm + deep


def entrenar(modelo, U, X, y, U_val, X_val, y_val, semilla, lr=1e-3, peso=1e-4, epocas=60, paciencia=6,
             lote=256, dispositivo="cpu"):
    """AdamW con parada temprana por pérdida de validación. Devuelve la curva de validación."""
    torch.manual_seed(semilla)
    modelo.to(dispositivo)
    ti = lambda a: torch.tensor(np.asarray(a), dtype=torch.long, device=dispositivo)
    tf = lambda a: torch.tensor(np.asarray(a), dtype=torch.float32, device=dispositivo)
    U, X, y, U_val, X_val, y_val = ti(U), tf(X), tf(y), ti(U_val), tf(X_val), tf(y_val)
    opt = torch.optim.AdamW(modelo.parameters(), lr=lr, weight_decay=peso)
    gen = torch.Generator(device="cpu").manual_seed(semilla)
    mejor, estado, sin_mejora, curva = np.inf, None, 0, []
    for _ in range(epocas):
        modelo.train()
        orden = torch.randperm(len(y), generator=gen).to(dispositivo)
        for k in range(0, len(y), lote):
            b = orden[k:k + lote]
            opt.zero_grad()
            F.binary_cross_entropy_with_logits(modelo(U[b], X[b]), y[b]).backward()
            opt.step()
        modelo.eval()
        with torch.no_grad():
            val = F.binary_cross_entropy_with_logits(modelo(U_val, X_val), y_val).item()
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


def predecir(modelo, U, X, dispositivo="cpu", lote=8192):
    modelo.eval()
    out = []
    with torch.no_grad():
        for k in range(0, len(U), lote):
            u = torch.tensor(np.asarray(U[k:k + lote]), dtype=torch.long, device=dispositivo)
            x = torch.tensor(np.asarray(X[k:k + lote]), dtype=torch.float32, device=dispositivo)
            out.append(torch.sigmoid(modelo(u, x)).cpu().numpy())
    return np.concatenate(out)
