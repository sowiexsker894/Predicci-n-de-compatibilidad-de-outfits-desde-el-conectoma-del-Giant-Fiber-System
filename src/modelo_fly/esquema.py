"""Vocabulario común de atributos de prenda (catálogo propio y Polyvore).

Todos los valores van en minúsculas, sin tildes. Lo que no se puede leer de la
fuente se marca como DESCONOCIDO; lo que no tiene sentido para el slot, como NO_APLICA.
"""

DESCONOCIDO = "desconocido"
NO_APLICA = "no_aplica"

SLOTS = ["arriba", "abajo", "vestido", "exterior", "calzado", "bolso", "accesorio", "joyeria"]

TONOS = [
    "negro", "blanco", "crema", "gris", "beige", "marron",
    "azul", "teal", "verde", "rojo", "rosa", "naranja", "amarillo", "morado", "plateado",
]
# Familias de color para las reglas C1/C2 (revisión §2.5).
FAMILIAS_COLOR = ["neutro", "suave", "fuerte"]

PATRONES = ["liso", "floral", "grafico", "holografico"]
MATERIALES = ["cuero", "denim", "encaje", "terciopelo"]

ESTILOS = ["casual", "formal", "deportivo", "athleisure", "vintage"]
CALCES = ["oversize", "ajustado", "recto"]

# "vintage_generico" = pista retro/vintage sin década concreta; no cuenta como década en la regla Ep1.
EPOCAS = ["1950s", "1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "vintage_generico", "contemporaneo"]

LARGOS = ["corto", "midi", "largo"]

COLUMNAS = ["slot", "tono", "familia_color", "patron", "material", "estilo", "calce", "epoca", "largo"]


def valores_validos(columna):
    """Valores permitidos de una columna del esquema, incluidos DESCONOCIDO y NO_APLICA."""
    base = {
        "slot": SLOTS,
        "tono": TONOS,
        "familia_color": FAMILIAS_COLOR,
        "patron": PATRONES,
        "material": MATERIALES,
        "estilo": ESTILOS,
        "calce": CALCES,
        "epoca": EPOCAS,
        "largo": LARGOS,
    }[columna]
    return set(base) | {DESCONOCIDO, NO_APLICA}
