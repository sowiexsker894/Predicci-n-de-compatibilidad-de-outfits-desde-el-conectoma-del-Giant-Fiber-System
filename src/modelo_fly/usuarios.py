"""Usuarios simulados: perfil, clóset e historial con ruido (etapa 6, revisión §12.3).

Polyvore no trae ID de usuario, así que el gusto personal se simula. Cada usuario tiene un
**arquetipo** (minimalista, clásico, vintage, atrevido, deportivo) del que salen sus pesos,
perturbados al azar. Ante un outfit armado con su clóset calcula una utilidad:

    utilidad = − Σ_k w_k · viola_k            (7 reglas de armonía)
               + b · coincide_estilo           (prendas de su estilo favorito)
               + c · adecuado_al_clima         (abrigo en clima frío, ropa ligera en cálido)
               + d · neutros                   (gusto por colores neutros o por color)
               + e · compatibilidad_humana     (qué tan seguido la gente combina esos atributos)

    p(acepta) = sigmoide(A · (utilidad − sesgo_u)),  sesgo_u = mediana de su utilidad
    y la decisión se invierte con probabilidad ruido_u ∈ [5 %, 10 %].

`compatibilidad_humana` sale de Polyvore (outfits reales de train contra negativos aleatorios
de train, ver `Compatibilidad`). Así el gusto no depende solo de las reglas: también de lo
que combinan las personas reales, que es lo que aprende TTMn.
"""

import numpy as np
import pandas as pd

from .esquema import DESCONOCIDO, NO_APLICA
from .reglas import REGLAS, evaluar

SIN_DATO = {DESCONOCIDO, NO_APLICA, ""}
ATRIBUTOS = ["slot", "tono", "familia_color", "patron", "material", "estilo", "calce", "epoca", "largo"]

# Pesos base por arquetipo: w (una por regla, en el orden de REGLAS), b, d y estilos favoritos.
# Ep1 negativo en vintage: le gusta ir "de una sola década".
ARQUETIPOS = {
    "minimalista": {"w": [2.0, 1.5, 1.0, 1.0, 1.5, 1.5, 0.5], "b": 1.0, "d": 1.5, "estilos": ["casual", "formal"]},
    "clasico": {"w": [1.5, 1.0, 1.5, 1.5, 1.0, 1.0, 0.5], "b": 1.5, "d": 0.5, "estilos": ["formal"]},
    "vintage": {"w": [0.3, 0.5, 0.5, 0.3, 0.5, 0.5, -1.0], "b": 2.0, "d": 0.0, "estilos": ["vintage"]},
    "atrevido": {"w": [0.0, 0.3, 0.3, 0.0, 0.3, 0.3, 0.5], "b": 0.5, "d": -1.5,
                 "estilos": ["casual", "formal", "vintage", "athleisure"]},
    "deportivo": {"w": [1.0, 0.5, 1.0, 1.0, 1.0, 0.0, 0.5], "b": 2.0, "d": 0.5, "estilos": ["deportivo", "athleisure"]},
}
# Ciudades del Perú con su clima (proporción aproximada de usuarios).
CIUDADES = {"Lima": ("templado", 0.50), "Arequipa": ("templado", 0.10), "Cusco": ("frio", 0.10),
            "Puno": ("frio", 0.05), "Huancayo": ("frio", 0.05), "Piura": ("calido", 0.10),
            "Iquitos": ("calido", 0.10)}
GENEROS = {"mujer": 0.85, "hombre": 0.10, "no binario": 0.05}  # Polyvore es casi todo ropa de mujer
ESCALA = 1.5
RUIDO = (0.05, 0.10)

# Proporción de cada slot en la parte Polyvore del clóset y en la parte propia (el catálogo
# propio solo tiene ropa y calzado).
CUOTA_POLYVORE = {"arriba": 0.18, "abajo": 0.14, "vestido": 0.08, "exterior": 0.08, "calzado": 0.16,
                  "bolso": 0.12, "accesorio": 0.10, "joyeria": 0.14}
CUOTA_PROPIA = {"arriba": 0.30, "abajo": 0.25, "vestido": 0.15, "exterior": 0.15, "calzado": 0.15}
PESO_ESTILO_FAV = 3.0  # el clóset se sesga hacia el estilo favorito
# Outfits: base arriba+abajo+calzado o vestido+calzado, más complementos con la frecuencia
# aproximada de los outfits reales de Polyvore.
COMPLEMENTOS = {"exterior": 0.40, "bolso": 0.75, "accesorio": 0.45, "joyeria": 0.55}
P_VESTIDO = 0.30

ABRIGO = {"lana", "punto", "terciopelo", "gamuza", "cuero"}
LIGERO = {"algodon", "seda"}
ROPA = {"arriba", "abajo", "vestido", "exterior"}


class Compatibilidad:
    """Log-cociente de cuántas veces aparece cada par de atributos (por slot) en outfits reales
    frente a negativos aleatorios. El puntaje de un outfit es el promedio sobre sus pares."""

    PARES = ["tono", "patron", "material", "estilo"]

    def __init__(self, reales, negativos, atrib):
        cr, cn = self._contar(reales, atrib), self._contar(negativos, atrib)
        nr, nn = sum(cr.values()), sum(cn.values())
        self.tabla = {k: np.log((cr.get(k, 0) + 1) / (nr + 1)) - np.log((cn.get(k, 0) + 1) / (nn + 1))
                      for k in set(cr) | set(cn)}

    def _claves(self, prendas):
        for i in range(len(prendas)):
            for j in range(i + 1, len(prendas)):
                a, b = prendas[i], prendas[j]
                for x in self.PARES:
                    if a[x] not in SIN_DATO and b[x] not in SIN_DATO:
                        yield (x, *sorted([(a["slot"], a[x]), (b["slot"], b[x])]))

    def _contar(self, outfits, atrib):
        cuenta = {}
        for tids in outfits:
            for k in self._claves([atrib[t] for t in tids]):
                cuenta[k] = cuenta.get(k, 0) + 1
        return cuenta

    def puntaje(self, prendas):
        valores = [self.tabla.get(k, 0.0) for k in self._claves(prendas)]
        return float(np.mean(valores)) if valores else 0.0


def generar_perfiles(n, semilla, grupo, inicio=0):
    rng = np.random.default_rng(semilla)
    ciudades = list(CIUDADES)
    filas = []
    for i in range(n):
        arq = rng.choice(list(ARQUETIPOS))
        base = ARQUETIPOS[arq]
        ciudad = rng.choice(ciudades, p=[CIUDADES[c][1] for c in ciudades])
        ruido = rng.lognormal(0, 0.3, size=len(REGLAS) + 2)
        fila = {"user_id": f"U{inicio + i + 1:03d}", "grupo": grupo, "arquetipo": arq,
                "estilo_fav": rng.choice(base["estilos"]),
                "edad": int(rng.integers(18, 46)),
                "genero": rng.choice(list(GENEROS), p=list(GENEROS.values())),
                "ciudad": ciudad, "clima": CIUDADES[ciudad][0],
                "n_closet": int(rng.integers(40, 81))}
        for r, w, z in zip(REGLAS, base["w"], ruido):
            fila[f"w_{r}"] = round(w * z, 3)
        fila["b_estilo"] = round(base["b"] * ruido[-2], 3)
        fila["d_neutros"] = round(base["d"] * ruido[-1], 3)
        fila["c_clima"] = round(float(rng.uniform(0.5, 1.5)), 3)
        fila["e_compat"] = round(float(rng.uniform(0.5, 1.5)), 3)
        fila["ruido"] = round(float(rng.uniform(*RUIDO)), 3)
        filas.append(fila)
    return pd.DataFrame(filas)


def _cuotas(n, cuota):
    bruto = {s: n * p for s, p in cuota.items()}
    k = {s: max(1, int(v)) for s, v in bruto.items()}
    for s in sorted(bruto, key=lambda s: bruto[s] - int(bruto[s]), reverse=True)[: n - sum(k.values())]:
        k[s] += 1
    return k


def _muestrear(rng, pool, k, estilo_fav):
    peso = np.where(pool["estilo"].to_numpy() == estilo_fav, PESO_ESTILO_FAV, 1.0)
    k = min(k, len(pool))
    return pool["item_id"].to_numpy()[rng.choice(len(pool), size=k, replace=False, p=peso / peso.sum())]


def armar_closet(rng, usuario, items_polyvore, items_propios, frac_polyvore):
    n = usuario["n_closet"]
    n_poly = round(n * frac_polyvore)
    elegidos = []
    for origen, pool, m, cuota in [("polyvore", items_polyvore, n_poly, CUOTA_POLYVORE),
                                   ("propio", items_propios, n - n_poly, CUOTA_PROPIA)]:
        if m == 0:
            continue
        for slot, k in _cuotas(m, cuota).items():
            ids = _muestrear(rng, pool[pool["slot"] == slot], k, usuario["estilo_fav"])
            elegidos += [(usuario["user_id"], i, origen, slot) for i in ids]
    return pd.DataFrame(elegidos, columns=["user_id", "item_id", "origen", "slot"])


def armar_outfit(rng, por_slot):
    """Un outfit al azar del clóset (dict slot → item_ids)."""
    usa_vestido = "vestido" in por_slot and (rng.random() < P_VESTIDO
                                             or not {"arriba", "abajo"} <= set(por_slot))
    base = ["vestido", "calzado"] if usa_vestido else ["arriba", "abajo", "calzado"]
    slots = [s for s in base if s in por_slot]
    slots += [s for s, p in COMPLEMENTOS.items() if s in por_slot and rng.random() < p]
    return [por_slot[s][rng.integers(len(por_slot[s]))] for s in slots]


def rasgos(prendas, clima, compat):
    """Variables que ve el gusto simulado para un outfit (lista de dicts de atributos)."""
    reglas = evaluar(prendas)
    out = {f"viola_{r}": 1 - reglas[f"cumple_{r}"] for r in REGLAS}
    out["score_reglas"] = reglas["score"]
    estilos = [p["estilo"] for p in prendas if p["estilo"] not in SIN_DATO]
    out["_estilos"] = estilos
    colores = [p["familia_color"] for p in prendas if p["familia_color"] not in SIN_DATO]
    out["neutros"] = 2 * np.mean([c == "neutro" for c in colores]) - 1 if colores else 0.0
    ropa = [p for p in prendas if p["slot"] in ROPA]
    abrigo = any(p["slot"] == "exterior" or p["material"] in ABRIGO for p in ropa)
    ligero = any(p["largo"] == "corto" or p["material"] in LIGERO for p in ropa)
    if clima == "frio":
        out["clima"] = 1.0 if abrigo else (-1.0 if ligero else 0.0)
    elif clima == "calido":
        out["clima"] = -1.0 if abrigo else (1.0 if ligero else 0.0)
    else:
        out["clima"] = 0.0
    out["compat"] = compat.puntaje(prendas)
    return out


def utilidad(r, usuario, compat_media, compat_desv):
    estilo = np.mean([e == usuario["estilo_fav"] for e in r["_estilos"]]) if r["_estilos"] else 0.0
    u = -sum(usuario[f"w_{k}"] * r[f"viola_{k}"] for k in REGLAS)
    u += usuario["b_estilo"] * estilo + usuario["c_clima"] * r["clima"] + usuario["d_neutros"] * r["neutros"]
    u += usuario["e_compat"] * (r["compat"] - compat_media) / compat_desv
    return u, estilo


N_INTERACCIONES = 50
CORTES = (35, 42)  # primeras 35 a train, 7 a valid, 8 a test (revisión §12.5)
N_CALIBRACION = 200


def particion_temporal(orden):
    return "train" if orden < CORTES[0] else ("valid" if orden < CORTES[1] else "test")


def simular_historial(rng, usuario, closet, atrib, compat, compat_media, compat_desv, inicio, ocupados):
    """50 outfits mostrados al usuario, en orden de fecha, con su decisión. Devuelve también el
    sesgo calibrado (mediana de la utilidad en outfits al azar de su clóset).

    `ocupados` (outfit → particiones donde ya lo vio otro usuario) se actualiza aquí: un outfit
    no puede estar en el test de un usuario y en el train de otro (revisión §12.5)."""
    por_slot = {s: g["item_id"].tolist() for s, g in closet.groupby("slot")}

    def evaluar_outfit(ids):
        r = rasgos([atrib[i] for i in ids], usuario["clima"], compat)
        u, estilo = utilidad(r, usuario, compat_media, compat_desv)
        return r, u, estilo

    sesgo = float(np.median([evaluar_outfit(armar_outfit(rng, por_slot))[1] for _ in range(N_CALIBRACION)]))
    vistos, filas = set(), []
    fecha = inicio
    while len(filas) < N_INTERACCIONES:
        ids = armar_outfit(rng, por_slot)
        clave, part = frozenset(ids), particion_temporal(len(filas))
        otros = ocupados.get(clave, set())
        if clave in vistos or (part == "test" and "train" in otros) or (part == "train" and "test" in otros):
            continue
        vistos.add(clave)
        ocupados.setdefault(clave, set()).add(part)
        r, u, estilo = evaluar_outfit(ids)
        p = 1 / (1 + np.exp(-ESCALA * (u - sesgo)))
        gusto = int(rng.random() < p)
        invertido = int(rng.random() < usuario["ruido"])
        orden = len(filas)
        fecha = fecha + pd.Timedelta(hours=float(rng.exponential(72)))
        filas.append({"user_id": usuario["user_id"], "orden": orden, "fecha": fecha.floor("min"),
                      "outfit_id": f"{usuario['user_id']}_O{orden + 1:02d}", "item_ids": "|".join(ids),
                      "n_items": len(ids), "particion": part,
                      **{k: v for k, v in r.items() if not k.startswith("_")},
                      "coincide_estilo": round(estilo, 3), "utilidad": round(u, 4), "p_real": round(p, 4),
                      "invertido": invertido, "aceptado": gusto ^ invertido})
    return pd.DataFrame(filas), sesgo


def candidatos(rng, usuario, closet, atrib, compat, compat_media, compat_desv, historial_u, n, particion, ocupados):
    """Outfits para el ranking de valid o test (etapa 7): los del historial de esa partición más
    outfits nuevos del clóset hasta llegar a `n`, todos con la decisión simulada del usuario
    (mismo gusto, sesgo y ruido que el historial). Ninguno puede estar en el train de nadie ni
    en el historial del usuario."""
    por_slot = {s: g["item_id"].tolist() for s, g in closet.groupby("slot")}
    propios = historial_u[historial_u["particion"] == particion]
    filas = [{"user_id": usuario["user_id"], "outfit_id": o, "item_ids": i, "particion": particion,
              "origen": "historial", "p_real": p, "aceptado": a}
             for o, i, p, a in zip(propios["outfit_id"], propios["item_ids"], propios["p_real"], propios["aceptado"])]
    vistos = {frozenset(i.split("|")) for i in historial_u["item_ids"]}
    intentos = 0
    while len(filas) < n and intentos < 50 * n:
        intentos += 1
        ids = armar_outfit(rng, por_slot)
        clave = frozenset(ids)
        if clave in vistos or "train" in ocupados.get(clave, set()):
            continue
        vistos.add(clave)
        ocupados.setdefault(clave, set()).add(particion)
        r = rasgos([atrib[i] for i in ids], usuario["clima"], compat)
        u, _ = utilidad(r, usuario, compat_media, compat_desv)
        p = 1 / (1 + np.exp(-ESCALA * (u - usuario["sesgo"])))
        decision = int(rng.random() < p) ^ int(rng.random() < usuario["ruido"])
        filas.append({"user_id": usuario["user_id"], "outfit_id": f"{usuario['user_id']}_{particion[0].upper()}{len(filas) + 1:03d}",
                      "item_ids": "|".join(ids), "particion": particion, "origen": "nuevo",
                      "p_real": round(p, 4), "aceptado": decision})
    return pd.DataFrame(filas)


def cargar_items(proc):
    """Prendas de Polyvore (prefijo `pv_`) y del catálogo propio con sus atributos, como en el
    notebook 06. Devuelve la tabla, el diccionario ID → atributos y los outfits de la fase 2."""
    productos = pd.read_csv(proc / "fase2_productos.csv", dtype=str, keep_default_na=False)
    propio = pd.read_csv(proc / "catalogo_propio.csv", dtype=str, keep_default_na=False)
    propio = propio[propio["calidad"] != "excluido"]
    productos["item_id"] = "pv_" + productos["tid"]
    cols = ["item_id", "origen", "particion", "name", *ATRIBUTOS]
    items = pd.concat([productos.assign(origen="polyvore")[cols],
                       propio.assign(particion="", name=propio["texto"])[cols]], ignore_index=True)
    outfits = pd.read_csv(proc / "fase2_outfits.csv", dtype={"tids": str, "particion": str, "tipo": str})
    outfits["ids"] = outfits["tids"].str.split("|").map(lambda t: ["pv_" + x for x in t])
    return items, items.set_index("item_id")[ATRIBUTOS].to_dict("index"), outfits


def compatibilidad_polyvore(outfits, atrib):
    """La compatibilidad humana del notebook 06 (contada en train) y su media y desviación en valid."""
    tr = outfits[outfits["particion"] == "train"]
    compat = Compatibilidad(tr.loc[tr["tipo"] == "real", "ids"], tr.loc[tr["tipo"] == "aleatorio", "ids"], atrib)
    va = [compat.puntaje([atrib[i] for i in ids]) for ids in outfits.loc[outfits["particion"] == "valid", "ids"]]
    return compat, float(np.mean(va)), float(np.std(va, ddof=1))
