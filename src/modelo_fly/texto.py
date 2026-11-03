"""Limpieza de texto común al catálogo propio y a Polyvore."""

import re
import unicodedata


def limpiar_texto(texto):
    """Texto plano: minúsculas, sin tildes, sin símbolos y con un solo espacio entre palabras.

    >>> limpiar_texto("Azul Cielo camiseta Años 50 - Estilo Oversize")
    'azul cielo camiseta anos 50 estilo oversize'
    """
    texto = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^a-z0-9]+", " ", texto.lower())
    return texto.strip()


def leer_csv_editable(ruta, **kwargs):
    """Lee un CSV que el equipo edita en Excel: acepta ',' o ';' y UTF-8 con o sin BOM."""
    import pandas as pd

    primera = ruta.read_text(encoding="utf-8-sig").splitlines()[0]
    sep = ";" if primera.count(";") > primera.count(",") else ","
    return pd.read_csv(ruta, sep=sep, encoding="utf-8-sig", **kwargs)


def guardar_csv_editable(df, ruta):
    """Guarda en el formato que Excel en español abre directo en columnas y con tildes."""
    df.to_csv(ruta, sep=";", index=False, encoding="utf-8-sig")
