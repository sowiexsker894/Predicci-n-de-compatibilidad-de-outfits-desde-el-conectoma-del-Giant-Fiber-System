"""Las 7 reglas de armonía (DLMn) sobre un outfit y su score 0–7 (etapa 4).

Cada regla devuelve (aplica, cumple). El score es el número de reglas **no violadas**: si una
regla no aplica (p. ej. P1 en un outfit sin estampados) cuenta como cumplida (revisión §12.4).
Los valores "desconocido" se ignoran: una regla se evalúa solo con las prendas en las que se
conoce el atributo.

Polyvore no trae la escala del estampado ni su color de fondo, así que P1 y P2 usan
aproximaciones (declaradas en docs/HALLAZGOS_HITO3.md):
- "comparten un color de fondo" ≈ las prendas estampadas comparten tono;
- "misma escala y familia" ≈ el mismo tipo de patrón.
"""

from .esquema import DESCONOCIDO, NO_APLICA

REGLAS = ["C1", "C2", "P1", "P2", "P3", "E1", "Ep1"]
DESCRIPCION = {
    "C1": "Máximo dos colores no neutros y un solo acento fuerte",
    "C2": "Si hay dos o más colores no neutros, al menos una prenda neutra los une",
    "P1": "Dos estampados distintos solo si comparten un color (aprox. del color de fondo)",
    "P2": "No repetir el mismo tipo de estampado",
    "P3": "Si hay dos o más prendas estampadas, al menos una prenda de ropa lisa hace de puente",
    "E1": "Un solo elemento con volumen (oversize)",
    "Ep1": "No replicar una sola década de pies a cabeza",
}
SLOTS_ROPA = {"arriba", "abajo", "vestido", "exterior"}
DECADAS = {"1950s", "1960s", "1970s", "1980s", "1990s", "2000s", "2010s"}
SIN_DATO = {DESCONOCIDO, NO_APLICA, ""}


def _conocidos(prendas, atributo, slots=None):
    return [p for p in prendas if p[atributo] not in SIN_DATO and (slots is None or p["slot"] in slots)]


def c1(prendas):
    color = [p for p in _conocidos(prendas, "familia_color") if p["familia_color"] != "neutro"]
    if not color:
        return False, True
    no_neutros = {p["tono"] for p in color}
    fuertes = {p["tono"] for p in color if p["familia_color"] == "fuerte"}
    return True, len(no_neutros) <= 2 and len(fuertes) <= 1


def c2(prendas):
    con = _conocidos(prendas, "familia_color")
    no_neutros = {p["tono"] for p in con if p["familia_color"] != "neutro"}
    if len(no_neutros) < 2:
        return False, True
    return True, any(p["familia_color"] == "neutro" for p in con)


def _estampadas(prendas):
    return [p for p in _conocidos(prendas, "patron") if p["patron"] != "liso"]


def p1(prendas):
    est = _estampadas(prendas)
    if len({p["patron"] for p in est}) < 2:
        return False, True
    tonos = [p["tono"] for p in est if p["tono"] not in SIN_DATO]
    if len(tonos) < 2:
        return False, True  # sin color no se puede juzgar
    return True, len(tonos) > len(set(tonos))


def p2(prendas):
    est = _estampadas(prendas)
    if len(est) < 2:
        return False, True
    tipos = [p["patron"] for p in est]
    return True, len(tipos) == len(set(tipos))


def p3(prendas):
    if len(_estampadas(prendas)) < 2:
        return False, True
    return True, any(p["patron"] == "liso" for p in _conocidos(prendas, "patron", SLOTS_ROPA))


def e1(prendas):
    con = _conocidos(prendas, "calce", SLOTS_ROPA)
    if len(con) < 2:
        return False, True
    return True, sum(p["calce"] == "oversize" for p in con) <= 1


def ep1(prendas):
    con = _conocidos(prendas, "epoca", SLOTS_ROPA)
    decadas = [p["epoca"] for p in con if p["epoca"] in DECADAS]
    if len(decadas) < 2:
        return False, True
    return True, not (len(set(decadas)) == 1 and len(decadas) == len(con))


FUNCIONES = {"C1": c1, "C2": c2, "P1": p1, "P2": p2, "P3": p3, "E1": e1, "Ep1": ep1}


def evaluar(prendas):
    """Lista de prendas (dicts con slot, tono, familia_color, patron, calce, epoca) → dict con
    `aplica_<regla>`, `cumple_<regla>` y `score` (0–7)."""
    out = {}
    for r, f in FUNCIONES.items():
        aplica, cumple = f(prendas)
        out[f"aplica_{r}"] = int(aplica)
        out[f"cumple_{r}"] = int(cumple)
    out["score"] = sum(out[f"cumple_{r}"] for r in REGLAS)
    return out
