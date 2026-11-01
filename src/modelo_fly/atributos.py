"""Atributos de prenda a partir del nombre en inglés de Polyvore (paso 3 de la etapa 3).

Cada atributo se busca con un diccionario de palabras clave sobre el texto limpio
(`limpiar_texto`). Las frases de varias palabras se buscan antes que las sueltas, y las
frases que confunden ("long sleeve", "rose gold") se quitan antes de buscar.

Supuestos declarados (revisión §12.2):
- Sin palabra de patrón → "liso"; sin palabra de época → "contemporaneo". Si no hay nombre,
  todo queda "desconocido".
- Si el nombre no dice el estilo, el calce o el largo, se usa la pista de la categoría
  (Skinny Jeans → ajustado, Gowns → formal, Mini Skirts → corto…).
- Los metales (dorado, plateado) son neutros en joyería y accesorios; en ropa son acento fuerte.
"""

import re

from .esquema import DESCONOCIDO, NO_APLICA
from .texto import limpiar_texto

SLOTS_ROPA = {"arriba", "abajo", "vestido", "exterior"}

# Frases que contienen palabras clave pero no describen el atributo.
QUITAR = {
    "largo": ["long sleeve", "long sleeves", "short sleeve", "short sleeves", "long strap", "long necklace"],
    "tono": ["rose gold"],  # se trata aparte como dorado
}

TONO = {
    "negro": ["black", "jet", "onyx", "noir"],
    "blanco": ["white", "optic white", "snow"],
    "crema": ["cream", "ivory", "off white", "ecru", "bone", "vanilla", "champagne"],
    "gris": ["grey", "gray", "charcoal", "heather", "slate", "silver grey", "ash"],
    "beige": ["beige", "nude", "camel", "tan", "khaki", "taupe", "sand", "oatmeal", "neutral"],
    "marron": ["brown", "cognac", "chocolate", "mocha", "tobacco", "chestnut", "espresso", "rust brown"],
    "azul": ["blue", "navy", "cobalt", "indigo", "denim blue", "sky blue", "baby blue", "royal blue", "midnight"],
    "teal": ["teal", "turquoise", "aqua", "petrol"],
    "verde": ["green", "olive", "mint", "emerald", "sage", "khaki green", "forest", "lime", "army"],
    "rojo": ["red", "burgundy", "wine", "maroon", "crimson", "scarlet", "oxblood", "bordeaux", "cherry"],
    "rosa": ["pink", "blush", "fuchsia", "magenta", "rose", "dusty pink", "hot pink", "salmon"],
    "naranja": ["orange", "coral", "rust", "tangerine", "peach", "terracotta"],
    "amarillo": ["yellow", "mustard", "lemon", "ochre"],
    "morado": ["purple", "lilac", "lavender", "violet", "plum", "mauve", "aubergine"],
    "plateado": ["silver", "silver tone", "silvertone", "chrome", "pewter"],
    "dorado": ["gold", "golden", "gold tone", "goldtone", "rose gold", "brass", "bronze", "copper"],
}
NEUTROS = {"negro", "blanco", "crema", "gris", "beige", "marron"}
# Tonos azules que funcionan como neutro, igual que el denim del catálogo propio.
AZUL_NEUTRO = ["navy", "denim", "indigo", "midnight"]
SUAVE = ["light", "pale", "pastel", "baby", "soft", "dusty", "washed", "faded", "powder", "mint", "lilac",
         "lavender", "blush", "sky", "sage", "peach"]

PATRON = {
    "floral": ["floral", "flower", "flowers", "rose print", "botanical", "blossom", "daisy"],
    "rayas": ["stripe", "striped", "stripes", "breton", "pinstripe"],
    "cuadros": ["plaid", "check", "checked", "checkered", "tartan", "gingham", "houndstooth"],
    "lunares": ["polka", "polka dot", "dot", "dots", "dotted"],
    "animal": ["leopard", "zebra", "snake", "snakeskin", "python", "tiger", "animal print", "cheetah"],
    "grafico": ["graphic", "logo", "slogan", "letter", "print tee", "printed tee", "embroidered slogan"],
    "holografico": ["holographic", "iridescent", "hologram"],
    "estampado": ["print", "printed", "pattern", "patterned", "paisley", "camo", "camouflage", "tie dye",
                  "abstract", "geometric"],
}

MATERIAL = {
    "cuero": ["leather", "faux leather", "vegan leather", "pu", "patent", "lambskin", "calfskin"],
    "denim": ["denim", "jean", "jeans", "chambray"],
    "encaje": ["lace", "crochet lace", "broderie"],
    "terciopelo": ["velvet", "velour", "crushed velvet"],
    "gamuza": ["suede", "nubuck", "faux suede"],
    "lana": ["wool", "cashmere", "merino", "alpaca", "mohair", "tweed", "angora"],
    "seda": ["silk", "satin", "charmeuse"],
    "algodon": ["cotton", "linen", "poplin", "jersey", "canvas"],
    "punto": ["knit", "knitted", "ribbed", "cable knit", "crochet"],
}

ESTILO = {
    "formal": ["formal", "evening", "cocktail", "tailored", "suit", "tuxedo", "gown", "office", "work"],
    "deportivo": ["sport", "sports", "athletic", "running", "training", "gym", "performance", "tennis"],
    "athleisure": ["jogger", "joggers", "sweatpants", "track", "tracksuit", "yoga", "hoodie", "sweatshirt"],
    "vintage": ["vintage", "retro"],
    "casual": ["casual", "everyday", "basic", "relaxed tee"],
}

CALCE = {
    "oversize": ["oversized", "oversize", "boyfriend", "baggy", "loose", "relaxed", "wide leg", "slouchy",
                 "boxy", "mom jeans", "mom jean"],
    "ajustado": ["skinny", "slim", "fitted", "bodycon", "tight", "body con", "second skin", "stretch fit"],
    "recto": ["straight", "straight leg", "regular fit", "classic fit"],
}

LARGO = {
    "corto": ["mini", "short", "shorts", "cropped", "crop", "micro"],
    "midi": ["midi", "knee", "knee length", "calf length", "tea length"],
    "largo": ["maxi", "long", "floor length", "full length", "ankle length", "gown"],
}

EPOCA = {
    "1950s": ["50s", "1950s", "fifties"],
    "1960s": ["60s", "1960s", "sixties"],
    "1970s": ["70s", "1970s", "seventies"],
    "1980s": ["80s", "1980s", "eighties"],
    "1990s": ["90s", "1990s", "nineties"],
    "2000s": ["y2k", "2000s", "00s"],
    "vintage_generico": ["vintage", "retro"],
}

# Pistas por categoría cuando el nombre no dice nada (nombre de Polyvore → valor).
ESTILO_CATEGORIA = {
    "formal": ["Gowns", "Cocktail Dresses", "Wedding Dresses", "Blazers", "Suits", "Pumps", "Ties", "Bow Ties",
               "Men's Dress Shoes", "Men's Dress Pants", "Men's Dress Shirts", "Men's Sportcoats & Blazers",
               "Oxfords", "Men's Oxfords", "Cuff Links", "Clutches"],
    "deportivo": ["Activewear Tops", "Activewear Pants", "Activewear Skirts", "Activewear Shorts",
                  "Activewear Jackets", "Activewear Tank Tops", "Athletic Shoes", "Men's Athletic Shoes",
                  "Men's Activewear Tops", "Men's Activewear Pants", "Men's Activewear Shorts",
                  "Men's Activewear Jackets"],
    "athleisure": ["Sweatshirts", "Hoodies", "Men's Sweatshirts", "Men's Hoodies", "Leggings", "Sneakers",
                   "Men's Sneakers"],
}
CALCE_CATEGORIA = {
    "ajustado": ["Skinny Jeans", "Leggings"],
    "oversize": ["Boyfriend Jeans", "Wide Leg Jeans"],
    "recto": ["Straight Leg Jeans"],
}
MATERIAL_CATEGORIA = {"denim": ["Jeans", "Skinny Jeans", "Bootcut Jeans", "Wide Leg Jeans", "Boyfriend Jeans",
                                "Straight Leg Jeans", "Flared Jeans", "Men's Jeans"]}


def _patron_regex(frases):
    frases = sorted(frases, key=len, reverse=True)
    return re.compile(r"\b(" + "|".join(re.escape(f) for f in frases) + r")\b")


def _indice(tabla):
    """Una regex por valor y un orden estable (el primero que aparece en el texto gana)."""
    return {valor: _patron_regex(frases) for valor, frases in tabla.items()}


_RX = {nombre: _indice(t) for nombre, t in
       {"tono": TONO, "patron": PATRON, "material": MATERIAL, "estilo": ESTILO,
        "calce": CALCE, "largo": LARGO, "epoca": EPOCA}.items()}
_RX_QUITAR = {k: _patron_regex(v) for k, v in QUITAR.items()}
_RX_SUAVE = _patron_regex(SUAVE)
_RX_AZUL_NEUTRO = _patron_regex(AZUL_NEUTRO)
_POR_CATEGORIA = {
    "estilo": {c: v for v, cs in ESTILO_CATEGORIA.items() for c in cs},
    "calce": {c: v for v, cs in CALCE_CATEGORIA.items() for c in cs},
    "material": {c: v for v, cs in MATERIAL_CATEGORIA.items() for c in cs},
}


def buscar(atributo, texto):
    """Valor cuyo término aparece primero en el texto, o None. También devuelve el término."""
    if atributo in _RX_QUITAR:
        texto = _RX_QUITAR[atributo].sub(" ", texto)
    mejor = None
    for valor, rx in _RX[atributo].items():
        m = rx.search(texto)
        if m and (mejor is None or m.start() < mejor[2]):
            mejor = (valor, m.group(0), m.start())
    return (mejor[0], mejor[1]) if mejor else (None, None)


def familia_color(tono, texto, slot):
    if tono == DESCONOCIDO:
        return DESCONOCIDO
    if tono in {"dorado", "plateado"}:
        return "fuerte" if slot in SLOTS_ROPA else "neutro"
    if tono in NEUTROS or (tono == "azul" and _RX_AZUL_NEUTRO.search(texto)):
        return "neutro"
    return "suave" if _RX_SUAVE.search(texto) else "fuerte"


def extraer(nombre, categoria, slot, largo_categoria=""):
    """Atributos de una prenda de Polyvore. Devuelve el valor y de dónde salió cada uno."""
    texto = limpiar_texto(nombre)
    if "rose gold" in texto:
        tono, termino_tono = "dorado", "rose gold"
    else:
        tono, termino_tono = buscar("tono", texto)

    out = {"texto": texto}
    origen = {}
    if not texto:
        for a in ["tono", "familia_color", "patron", "material", "estilo", "calce", "epoca", "largo"]:
            out[a] = DESCONOCIDO
            origen[a] = "sin nombre"
    else:
        out["tono"] = tono or DESCONOCIDO
        origen["tono"] = termino_tono or "-"
        out["familia_color"] = familia_color(out["tono"], texto, slot)
        origen["familia_color"] = "regla"
        for a, sin_valor in [("patron", "liso"), ("material", DESCONOCIDO), ("estilo", DESCONOCIDO),
                             ("calce", DESCONOCIDO), ("epoca", "contemporaneo"), ("largo", DESCONOCIDO)]:
            valor, termino = buscar(a, texto)
            if valor is None and categoria in _POR_CATEGORIA.get(a, {}):
                valor, termino = _POR_CATEGORIA[a][categoria], f"categoria: {categoria}"
            if valor is None and a == "largo" and largo_categoria:
                valor, termino = largo_categoria, f"categoria: {categoria}"
            out[a] = valor or sin_valor
            origen[a] = termino or ("supuesto" if sin_valor != DESCONOCIDO else "-")

    if slot not in SLOTS_ROPA:
        out["calce"] = NO_APLICA
        out["largo"] = NO_APLICA
        origen["calce"] = origen["largo"] = "no aplica al slot"
    out.update({f"origen_{a}": v for a, v in origen.items()})
    return out
