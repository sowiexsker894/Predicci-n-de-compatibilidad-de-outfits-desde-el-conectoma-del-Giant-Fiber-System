"""Pasa el catálogo propio de 500 prendas al esquema común (revisión §12.12).

Reglas declaradas:
- Estilo/calce: la columna `estilo` y el "Estilo X" de `descripcion` se reparten entre
  estilo y calce. Si los dos son del mismo tipo y no coinciden, manda la columna
  (decisión del 31/10/2026) y la prenda queda con conflicto_estilo = 1.
- Patrón/material: Cuero, Denim, Encaje y Terciopelo son materiales; esas prendas quedan
  con patrón "liso". Las estampadas quedan con material desconocido.
- Época: las décadas se mantienen; Tumblr -> 2010s; Retro y Vintage -> vintage_generico.
- Color: tono base + familia (neutro / suave / fuerte). Los denim cuentan como neutros.
  Los valores que no son un color (Vintage, Desteñido, Pastel…) quedan desconocidos.
- Largo: solo se deduce cuando la categoría lo fija (Short, Pantalón).
"""

import unicodedata

import pandas as pd

from .esquema import COLUMNAS, DESCONOCIDO, NO_APLICA, valores_validos


def clave(texto):
    """Minúsculas, sin tildes ni espacios sobrantes."""
    texto = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return " ".join(texto.lower().split())


SLOT_POR_CATEGORIA = {
    "camiseta": "arriba",
    "blusas": "arriba",
    "pantalon": "abajo",
    "faldas y minifaldas": "abajo",
    "short": "abajo",
    "vestido": "vestido",
    "chaqueta": "exterior",
    "calzado": "calzado",
}

LARGO_POR_CATEGORIA = {
    "short": "corto",
    "pantalon": "largo",
    "calzado": NO_APLICA,
}

# color original -> (tono, familia)
COLOR = {
    "negro": ("negro", "neutro"),
    "negro vintage": ("negro", "neutro"),
    "blanco": ("blanco", "neutro"),
    "blanco destenido": ("blanco", "neutro"),
    "blanco marfil": ("crema", "neutro"),
    "marfil": ("crema", "neutro"),
    "crudo": ("crema", "neutro"),
    "crema": ("crema", "neutro"),
    "gris": ("gris", "neutro"),
    "gris charcoal": ("gris", "neutro"),
    "gris carbon": ("gris", "neutro"),
    "gris humo": ("gris", "neutro"),
    "gris claro": ("gris", "neutro"),
    "gris denim": ("gris", "neutro"),
    "beige": ("beige", "neutro"),
    "beige neutro": ("beige", "neutro"),
    "beige neutral": ("beige", "neutro"),
    "beige antiguo": ("beige", "neutro"),
    "nude": ("beige", "neutro"),
    "caqui": ("beige", "neutro"),
    "caqui faded": ("beige", "neutro"),
    "marron": ("marron", "neutro"),
    "marron tierra": ("marron", "neutro"),
    "marron cuero": ("marron", "neutro"),
    "marron vintage": ("marron", "neutro"),
    "denim": ("azul", "neutro"),
    "azul denim": ("azul", "neutro"),
    "azul destenido": ("azul", "suave"),
    "faded blue": ("azul", "suave"),
    "azul faded": ("azul", "suave"),
    "azul cielo": ("azul", "suave"),
    "azul suave": ("azul", "suave"),
    "azul clasico": ("azul", "fuerte"),
    "azul oscuro": ("azul", "fuerte"),
    "azul": ("azul", "fuerte"),
    "teal": ("teal", "fuerte"),
    "teal palido": ("teal", "suave"),
    "teal antiguo": ("teal", "suave"),
    "teal destenido": ("teal", "suave"),
    "verde": ("verde", "fuerte"),
    "verde lima": ("verde", "fuerte"),
    "verde menta": ("verde", "suave"),
    "verde palido": ("verde", "suave"),
    "rojo": ("rojo", "fuerte"),
    "rojo vino": ("rojo", "fuerte"),
    "rojo clasico": ("rojo", "fuerte"),
    "neon rosa": ("rosa", "fuerte"),
    "rosa palido": ("rosa", "suave"),
    "rosa pastel": ("rosa", "suave"),
    "rosa antiguo": ("rosa", "suave"),
    "naranja": ("naranja", "fuerte"),
    "naranja retro": ("naranja", "fuerte"),
    "naranja quemado": ("naranja", "fuerte"),
    "amarillo chillon": ("amarillo", "fuerte"),
    "amarillo limon": ("amarillo", "fuerte"),
    "neon amarillo": ("amarillo", "fuerte"),
    "mostaza": ("amarillo", "fuerte"),
    "amarillo mostaza": ("amarillo", "fuerte"),
    "amarillo mantequilla": ("amarillo", "suave"),
    "purpura": ("morado", "fuerte"),
    "purpura neon": ("morado", "fuerte"),
    "purpura palido": ("morado", "suave"),
    "plateado": ("plateado", "fuerte"),
    # No son colores: no se puede saber el tono.
    "vintage": (DESCONOCIDO, DESCONOCIDO),
    "destenido": (DESCONOCIDO, DESCONOCIDO),
    "estampado vintage": (DESCONOCIDO, DESCONOCIDO),
    "cuero destenido": (DESCONOCIDO, DESCONOCIDO),
    "faded colors": (DESCONOCIDO, DESCONOCIDO),
    "pastel": (DESCONOCIDO, "suave"),
}

# patrón original -> (patrón, material)
PATRON = {
    "liso": ("liso", DESCONOCIDO),
    "floral": ("floral", DESCONOCIDO),
    "grafico": ("grafico", DESCONOCIDO),
    "holografico": ("holografico", DESCONOCIDO),
    "cuero": ("liso", "cuero"),
    "denim": ("liso", "denim"),
    "encaje": ("liso", "encaje"),
    "terciopelo": ("liso", "terciopelo"),
}

EPOCA = {
    "anos 50": "1950s",
    "anos 60": "1960s",
    "anos 70": "1970s",
    "anos 80": "1980s",
    "anos 90": "1990s",
    "tumblr": "2010s",
    "retro": "vintage_generico",
    "vintage": "vintage_generico",
}

ESTILOS_FUENTE = {"casual", "formal", "deportivo", "athleisure", "vintage"}
CALCES_FUENTE = {"oversize", "ajustado", "recto"}


def buscar(tabla, valor, nombre):
    k = clave(valor)
    if k not in tabla:
        raise KeyError(f"{nombre} sin mapeo: {valor!r}. Añádelo a la tabla {nombre.upper()}.")
    return tabla[k]


def estilo_y_calce(col, desc):
    """Reparte la columna `estilo` y el estilo de la descripción entre estilo y calce."""
    col, desc = clave(col), clave(desc)
    estilo = calce = DESCONOCIDO
    for valor in (desc, col):  # la columna va al final para que gane si chocan
        if valor in ESTILOS_FUENTE:
            estilo = valor
        elif valor in CALCES_FUENTE:
            calce = valor
        else:
            raise KeyError(f"Estilo sin mapeo: {valor!r}")
    mismo_tipo = (col in ESTILOS_FUENTE) == (desc in ESTILOS_FUENTE)
    conflicto = int(mismo_tipo and col != desc)
    return estilo, calce, conflicto


def motivos_revision(fila):
    """Señales de prenda poco creíble. No excluyen: marcan qué revisar a mano."""
    motivos = []
    if fila["tono"] == DESCONOCIDO:
        motivos.append("color no es un color")
    if fila["categoria"] == "Camiseta" and fila["material"] in {"cuero", "denim", "terciopelo"}:
        motivos.append(f"camiseta de {fila['material']}")
    if fila["estilo"] in {"deportivo", "athleisure"} and fila["material"] in {"cuero", "encaje", "terciopelo"}:
        motivos.append(f"{fila['estilo']} de {fila['material']}")
    if fila["estilo"] == "formal" and fila["patron"] in {"grafico", "holografico"}:
        motivos.append(f"formal con patrón {fila['patron']}")
    if fila["slot"] == "calzado" and not str(fila["talla"]).isdigit():
        motivos.append(f"calzado con talla {fila['talla']}")
    return "; ".join(motivos)


def transformar(crudo):
    """Catálogo crudo (sep=';') -> DataFrame con el esquema común y columnas de trazabilidad."""
    crudo = crudo.rename(columns={"tamaño": "talla"})
    filas = []
    for r in crudo.itertuples(index=False):
        cat = clave(r.categoria)
        tono, familia = buscar(COLOR, r.color, "color")
        patron, material = buscar(PATRON, r.patron, "patron")
        estilo_desc = r.descripcion.rsplit("Estilo ", 1)[-1]
        estilo, calce, conflicto = estilo_y_calce(r.estilo, estilo_desc)
        slot = buscar(SLOT_POR_CATEGORIA, r.categoria, "slot")
        filas.append({
            "item_id": r.prenda_id,
            "origen": "propio",
            "categoria": r.categoria,
            "slot": slot,
            "tono": tono,
            "familia_color": familia,
            "patron": patron,
            "material": material,
            "estilo": estilo,
            "calce": NO_APLICA if slot == "calzado" else calce,
            "epoca": buscar(EPOCA, r.epoca, "epoca"),
            "largo": LARGO_POR_CATEGORIA.get(cat, DESCONOCIDO),
            "talla": r.talla,
            "conflicto_estilo": conflicto,
            "color_original": r.color,
            "patron_original": r.patron,
            "estilo_original": r.estilo,
            "estilo_descripcion": estilo_desc,
            "epoca_original": r.epoca,
            "texto_original": r.descripcion,
        })
    out = pd.DataFrame(filas)
    out["motivo_revision"] = out.apply(motivos_revision, axis=1)
    out["calidad"] = out["motivo_revision"].map(lambda m: "revisar" if m else "ok")
    validar(out)
    return out


def validar(df):
    """Falla si alguna columna del esquema tiene un valor fuera del vocabulario."""
    for col in COLUMNAS:
        fuera = set(df[col]) - valores_validos(col)
        if fuera:
            raise ValueError(f"Valores fuera del esquema en {col}: {sorted(fuera)}")
    if not df["item_id"].is_unique:
        raise ValueError("item_id repetido")


def aplicar_revision(df, revision):
    """Aplica las decisiones manuales (ok / corregido / excluido) de la planilla de revisión."""
    decisiones = revision.dropna(subset=["decision"]).set_index("item_id")
    invalidas = set(decisiones["decision"]) - {"ok", "corregido", "excluido"}
    if invalidas:
        raise ValueError(f"Decisiones no válidas en la revisión: {sorted(invalidas)}")
    out = df.copy()
    tiene = out["item_id"].isin(decisiones.index)
    out.loc[tiene, "calidad"] = out.loc[tiene, "item_id"].map(decisiones["decision"])
    # Las correcciones se escriben en las columnas del esquema con el prefijo corr_.
    for col in COLUMNAS:
        corr = f"corr_{col}"
        if corr in decisiones.columns:
            nuevos = decisiones[corr].dropna()
            fila = out["item_id"].isin(nuevos.index)
            out.loc[fila, col] = out.loc[fila, "item_id"].map(nuevos)
    validar(out)
    return out
