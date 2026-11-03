"""Color dominante de la foto de un producto de Polyvore (decisión B del 01/11/2026).

Las fotos de Polyvore son productos recortados sobre fondo blanco o transparente. El método:
1. Se reduce la imagen a 64×64 y se quita el fondo: píxeles transparentes o casi blancos
   (los tres canales ≥ 240).
2. Cada píxel restante se asigna al tono de la paleta más cercano en el espacio CIELAB
   (distancia euclídea, ΔE76). Cada tono tiene varios prototipos (claro, medio, oscuro).
3. El tono dominante es el que tiene más píxeles. Si casi no queda nada después de quitar
   el fondo (< 3 % de la imagen), la prenda es blanca.

No distingue metales: el dorado y el plateado se ven como amarillo/beige y gris. Eso se
corrige después según el slot (joyería y accesorios), fuera de este módulo.
"""

import numpy as np

UMBRAL_BLANCO = 240
MIN_PRENDA = 0.03
LADO = 64

PROTOTIPOS = {
    "negro": [(0, 0, 0), (30, 30, 30), (45, 40, 40)],
    "blanco": [(245, 245, 245), (232, 232, 232)],
    "crema": [(240, 230, 205), (245, 238, 220), (230, 215, 185)],
    "gris": [(90, 90, 90), (128, 128, 128), (170, 170, 170), (205, 205, 205), (65, 70, 75)],
    "beige": [(215, 190, 160), (195, 170, 135), (225, 205, 180), (185, 160, 120)],
    "marron": [(80, 50, 30), (110, 70, 40), (140, 90, 55), (165, 115, 75), (95, 65, 50)],
    "azul": [(25, 35, 80), (30, 60, 150), (70, 110, 160), (90, 130, 200), (150, 180, 220), (55, 75, 110)],
    "teal": [(0, 128, 128), (60, 160, 160), (20, 90, 100)],
    "verde": [(40, 120, 50), (85, 107, 47), (110, 140, 60), (150, 200, 150), (40, 70, 45)],
    "rojo": [(200, 20, 30), (170, 30, 40), (130, 20, 35), (90, 20, 30)],
    "rosa": [(240, 150, 180), (230, 80, 150), (250, 200, 210), (215, 140, 150)],
    "naranja": [(240, 130, 40), (210, 100, 60), (250, 170, 130), (190, 90, 50)],
    "amarillo": [(240, 210, 50), (220, 180, 60), (250, 235, 140)],
    "morado": [(110, 50, 140), (180, 150, 210), (80, 40, 80), (150, 90, 160)],
}
NEUTROS = {"negro", "blanco", "crema", "gris", "beige", "marron"}

# Ajustes después de leer la foto, calibrados el 01/11/2026 con la partición oficial train
# (ver docs/HALLAZGOS_HITO3.md). El gris se queda con las sombras de las prendas blancas y con
# los azules apagados: si el segundo tono tiene al menos MIN_SEGUNDO de los píxeles, gana él;
# un gris muy claro es blanco y uno muy oscuro es negro.
MIN_SEGUNDO = 0.15
L_BLANCO = 80
L_NEGRO = 35
# En joyería la foto no distingue el metal: los tonos cálidos son dorado y los claros fríos plateado.
METAL_JOYERIA = {"amarillo": "dorado", "beige": "dorado", "crema": "dorado", "marron": "dorado",
                 "naranja": "dorado", "gris": "plateado", "blanco": "plateado"}


def rgb_a_lab(rgb):
    """RGB (0-255, forma [..., 3]) → CIELAB con iluminante D65."""
    c = np.asarray(rgb, dtype=float) / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    m = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ m.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], axis=-1)


_NOMBRES = [t for t, ps in PROTOTIPOS.items() for _ in ps]
_LAB_PROTO = rgb_a_lab([p for ps in PROTOTIPOS.values() for p in ps])


def familia(tono, lab_medio):
    """neutro / suave / fuerte, con la misma idea que el catálogo propio (denim y navy = neutro)."""
    L, a, b = lab_medio
    croma = float(np.hypot(a, b))
    if tono in NEUTROS:
        return "neutro"
    if tono == "azul" and croma < 35:
        return "neutro"
    return "suave" if L > 70 and croma < 40 else "fuerte"


def color_dominante(imagen):
    """Imagen PIL → dict con tono, familia, fracción de prenda y segundo tono."""
    img = imagen.convert("RGBA").resize((LADO, LADO))
    px = np.asarray(img, dtype=np.uint8).reshape(-1, 4)
    fondo = (px[:, 3] < 128) | (px[:, :3].min(axis=1) >= UMBRAL_BLANCO)
    prenda = px[~fondo, :3]
    frac_prenda = len(prenda) / len(px)
    if frac_prenda < MIN_PRENDA:
        return {"tono_img": "blanco", "familia_img": "neutro", "frac_tono": 1.0, "tono2_img": "",
                "frac_tono2": 0.0, "frac_prenda": round(frac_prenda, 4), "L": 97.0, "a": 0.0, "b": 0.0}
    lab = rgb_a_lab(prenda)
    dist = ((lab[:, None, :] - _LAB_PROTO[None, :, :]) ** 2).sum(axis=2)
    tonos = np.array(_NOMBRES)[dist.argmin(axis=1)]
    valores, cuentas = np.unique(tonos, return_counts=True)
    orden = np.argsort(-cuentas)
    t1 = valores[orden[0]]
    lab1 = lab[tonos == t1].mean(axis=0)
    t2 = valores[orden[1]] if len(orden) > 1 else ""
    return {
        "tono_img": str(t1),
        "familia_img": familia(t1, lab1),
        "frac_tono": round(float(cuentas[orden[0]]) / len(tonos), 4),
        "tono2_img": str(t2),
        "frac_tono2": round(float(cuentas[orden[1]]) / len(tonos), 4) if t2 else 0.0,
        "frac_prenda": round(frac_prenda, 4),
        "L": round(float(lab1[0]), 1), "a": round(float(lab1[1]), 1), "b": round(float(lab1[2]), 1),
    }


def ajustar(color, slot):
    """Salida de `color_dominante` (una fila por prenda) + slot → tono y familia finales de la foto."""
    tono, fam = [], []
    for c, s in zip(color.to_dict("records"), slot):
        t, segundo = c["tono_img"], c["tono2_img"] if isinstance(c["tono2_img"], str) else ""
        if t == "gris" and segundo and c["frac_tono2"] >= MIN_SEGUNDO:
            # No hay L*a*b* medio del segundo tono: se toma como acento fuerte si no es neutro.
            t, f = segundo, "neutro" if segundo in NEUTROS else "fuerte"
        else:
            if t == "gris" and c["L"] >= L_BLANCO:
                t = "blanco"
            elif t == "gris" and c["L"] < L_NEGRO:
                t = "negro"
            f = familia(t, (c["L"], c["a"], c["b"]))
        if s == "joyeria" and t in METAL_JOYERIA:
            t, f = METAL_JOYERIA[t], "neutro"
        tono.append(t)
        fam.append(f)
    return tono, fam
