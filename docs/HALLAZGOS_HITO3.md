# Hallazgos y decisiones del Hito 3 (para el informe)

Registro de lo que se descubrió y se decidió en cada etapa del código, con las cifras exactas. Cada punto dice **en qué parte del informe** va. Lo mantiene el equipo de código; Sergio lo usa para redactar.

- **Plan completo y justificación:** `docs/REVISION_Hito2_y_brechas_Hito3.md` (§12 y §12.12).
- **Dónde reproducir cada cifra:** el notebook indicado en cada sección.

Última actualización: 01/11/2026.

---

## Decisiones generales

| Decisión | Valor | Fecha | Sección del informe |
|---|---|---|---|
| Fuentes de datos | Polyvore (outfits reales) + catálogo propio de 500 prendas | 29/10/2026 | Fase 2 · Comprensión de los datos |
| Rol de cada fuente | Polyvore da la verdad de compatibilidad (fase 2 se entrena solo con Polyvore). El catálogo propio solo aporta prendas para los clósets | 29/10/2026 | Fase 2 |
| Etiquetas del Hito 2 | Los 100 000 outfits etiquetados del Hito 2 **se descartan** como verdad (fuga entre particiones y outfits de 3 prendas siempre compatibles) | 29/10/2026 | Resumen de cambios respecto al Hito 2 |
| Composición del clóset | 70 % prendas de Polyvore / 30 % del catálogo propio | 01/11/2026 | Fase 3 · Preparación (usuarios simulados) |
| Partición de los datos | 70 / 15 / 15 (train / validación / test) | 01/11/2026 | Fase 3 y Fase 5 |
| Partición del DeepFM | Por usuario y en orden de fecha: de ~50 interacciones, 35 / 7 / 8 | 01/11/2026 | Fase 3 |
| Color en Polyvore | Si el nombre no dice el color, se saca **de la foto del producto** (color dominante) | 01/11/2026 | Fase 3 · Preparación |

---

## Etapa 1 · Reproducibilidad del Hito 2 (`notebooks/hito2/`)

- Se volvieron a ejecutar `01_EDA` y `02_baseline` en un entorno limpio (Python 3.13, `requirements.txt`). Las métricas salieron **idénticas** a las entregadas (diferencia 0,0). → *Resumen de cambios; Anexo de reproducibilidad.*
- `EDA.ipynb` se retiró: leía el catálogo **sin `sep=';'`** y lo dejaba en una sola columna. El párrafo 2.1 del informe del Hito 2 ("en las descripciones se repiten vintage, casual y formal") salía de esa lectura equivocada. → *Resumen de cambios.*
- La última celda del baseline fallaba (`NameError`) porque se ejecutó sin el resto del notebook. No era un error del código. → *Anexo.*
- Los archivos `outfits_{train,validation,test}_100k.csv` de la entrega **no los genera ningún notebook**; el baseline hace su propia partición en memoria (semilla 42). → *Anexo, como limitación de la entrega anterior.*

---

## Etapa 2 · Catálogo propio de 500 prendas (`notebooks/hito3/01b_catalogo_propio.ipynb`)

### Problemas encontrados en el catálogo (lo generó una IA)

| Hallazgo | Cifra | Sección |
|---|---|---|
| El estilo de la columna coincide con el "Estilo …" de la descripción | solo **66 / 500** (13 %, lo mismo que el azar entre 8 valores) | Fase 2 · Calidad de los datos |
| Columna y descripción se complementan (una es estilo y la otra calce) | 229 prendas | Fase 2 |
| Columna y descripción se contradicen | **205 prendas** | Fase 2 |
| Color, categoría y época de la descripción coinciden con sus columnas | 500 / 500 | Fase 2 |
| Camisetas de cuero, denim o terciopelo | 38 de 88 camisetas | Fase 2 |
| Patrones repartidos casi por igual en todas las categorías | 57–72 prendas por patrón | Fase 2 |
| Tallas sin sentido (calzado con talla XL o L, camisetas talla 36) | 22 calzados con talla de ropa | Fase 2 |
| Columna `color` con 69 valores, algunos no son colores ("Vintage", "Desteñido", "Pastel") y otros son sinónimos | 20 prendas sin color real | Fase 2 |
| `patron` mezcla patrones con materiales; `estilo` mezcla estilo con calce; `epoca` mezcla décadas con estilos | — | Fase 2 |

**Conclusión para el informe:** los atributos del catálogo parecen asignados casi al azar. Por eso el catálogo no se usa como fuente de verdad, solo como prendas para recomendar.

### Decisiones de limpieza

| Decisión | Detalle | Sección |
|---|---|---|
| Estilo vs descripción | Se reparten entre `estilo` y `calce`. En las 205 contradicciones **manda la columna** y la prenda queda con `conflicto_estilo = 1` para el análisis de errores (decisión del 31/10/2026) | Fase 3 |
| Color | 69 valores → 15 tonos + familia (neutro 297, fuerte 114, suave 71, desconocido 18). El denim cuenta como neutro | Fase 3 |
| Patrón y material | Cuero, Denim, Encaje y Terciopelo pasan a `material` (esas prendas quedan con patrón liso) | Fase 3 |
| Época | Décadas → 1950s…1990s; Tumblr → 2010s; Retro y Vintage → `vintage_generico` | Fase 3 |
| Tallas peruanas (ropa) | 36 XS, 37 S, 38 M, 39 L, 40 XL, 41 XXL, 42 XXXL. El calzado conserva su número | Fase 3 |
| Texto limpio | Columna `texto`: minúsculas, sin tildes ni símbolos | Fase 3 |

### Revisión manual (respuesta a la crítica del profesor sobre datos inventados)

- El código marcó **153 prendas** como sospechosas: camiseta de cuero/denim/terciopelo (38), deportivo o athleisure de cuero/encaje/terciopelo (65), formal con patrón gráfico u holográfico (24), calzado con talla de ropa (22), color ilegible (20).
- La regla de exclusión se escribió **antes** de revisar: se excluye solo si la combinación no existe en tiendas reales o si un atributo es ilegible y no se puede corregir.
- El equipo revisó las 153 y las marcó todas como **ok**. Quedan **500 prendas utilizables**. → *Fase 2 · Verificación de calidad.*

### Nota técnica

- Los "símbolos raros" que se veían en Excel ("AÃ±os") **no eran datos dañados**: los archivos estaban bien en UTF-8, pero Excel los abría con otra codificación. Ahora los CSV se guardan con BOM. → *Anexo (opcional).*

---

## Etapa 3 · Polyvore (`notebooks/hito3/00_polyvore_descarga.ipynb`, `01_atributos.ipynb`)

### Paso 0 · El dataset

| Dato | Valor | Sección |
|---|---|---|
| Fuente | Han et al. (2017), repositorio `xthan/polyvore-dataset`, licencia Apache 2.0 | Fase 2 · Recolección |
| Outfits | 21 889 (train 17 316, valid 1 497, test 3 076) | Fase 2 |
| Ítems | 142 480; **111 589 productos distintos** | Fase 2 |
| Productos compartidos entre las particiones oficiales | **0** (la partición oficial separa productos) | Fase 3 · Partición |
| Ítems sin nombre | 1 871 | Fase 2 |
| Ítems por outfit | de 4 a 8 (los autores recortaron a 8) | Fase 2 |

Cita: Han, X., Wu, Z., Jiang, Y.-G. y Davis, L. S. (2017). *Learning Fashion Compatibility with Bidirectional LSTMs*. ACM Multimedia.

### Paso 1 · Categorías → slot (`data/mappings/polyvore_categorias.csv`)

- Las 380 categorías de Polyvore se asignaron a 8 slots o se excluyeron con su motivo. La tabla la **revisó el equipo** (01/11/2026), que cambió 4 categorías: *Suits* → arriba, *Men's Swimwear* → abajo, *Wallets* y *Men's Bags & Wallets* → accesorio.
- **Se excluye el 22,3 % de los ítems:** belleza, hogar, tecnología y comida (28 127), genéricos o ambiguos como *Clothing*, que incluye logos (2 124), ropa interior o de dormir (704), niños o maternidad (456), ropa de baño (418).
- Decisiones: cárdigan, chaleco y blazer → exterior; enterizo y jumpsuit → vestido; medias y calcetines → accesorio; relojes → accesorio. → *Fase 3.*

### Paso 2 · Outfits vestibles

Regla: un vestido solo, o una prenda de abajo con una o dos de arriba; exactamente un calzado; como mucho un exterior; bolso, accesorios y joyería libres. Motivo: en Polyvore se ponían alternativas en un mismo set (dos zapatos, dos vestidos), y el paso 4 arma cada negativo cambiando **una** prenda.

| Resultado | Outfits |
|---|---|
| Originales | 21 889 |
| Con núcleo + calzado (regla amplia) | 16 616 |
| **Vestibles (regla estricta, sin duplicados)** | **15 012 (69 %)** |

Motivos de descarte: sin núcleo 3 402 · sin calzado 878 · sin ninguna prenda de moda 861 · más de un calzado 631 · vestido con arriba o abajo 429 · más de un vestido 270 · más de una prenda abajo 257 · más de un exterior 102 · más de dos arriba 40 · duplicados 7.

Composición de los 15 012: 4 172 con vestido, 10 840 arriba + abajo (570 con dos prendas arriba), 5 907 con exterior, 11 369 con bolso. → *Fase 3, tabla del embudo de datos.*

### Paso 3 · Atributos desde el nombre en inglés

- Diccionarios de palabras clave inglés → vocabulario en español, más pistas por categoría (*Skinny Jeans* → ajustado y denim, *Gowns* → formal y largo). Se guarda el **origen** de cada valor (texto, categoría o supuesto).
- Se ampliaron los valores posibles con lo que aparece en Polyvore: dorado; rayas, cuadros, lunares, animal print, estampado; gamuza, lana, seda, algodón, punto.
- **Supuestos declarados:** sin palabra de patrón → liso; sin palabra de época → contemporáneo; los metales (dorado, plateado) son neutros en joyería y accesorios y acento fuerte en ropa.

**Cobertura sobre 81 372 prendas** (→ *Fase 2 · Calidad y Fase 3*):

| Atributo | Leído (texto o categoría) | Supuesto | Desconocido |
|---|---|---|---|
| Color | 30,3 % | — | **69,7 %** |
| Patrón | 10,1 % | 89,2 % (liso) | 0,7 % |
| Material | 32,3 % | — | 67,7 % |
| Estilo | 18,0 % | — | 82,0 % |
| Calce (solo ropa) | 17,2 % | — | 82,8 % |
| Época | 2,2 % | 97,1 % (contemporáneo) | 0,7 % |
| Largo (solo ropa) | 27,5 % | — | 72,5 % |

- **Limitación principal:** solo en el **1,1 % de los outfits** se conoce el color de todas las prendas por el texto (en el 20 % no se conoce ninguno). El color sostiene las reglas C1 y C2.
- **Decisión (01/11/2026):** completar el color con el **color dominante de la foto** del producto (imágenes de Polyvore en Kaggle). El texto manda; la foto solo rellena lo que falta. *(Hecho: ver paso 3b.)*

### Paso 3b · Color desde la foto (`notebooks/hito3/01c_color_imagenes_colab.ipynb`, se ejecuta en Google Colab)

- El dataset de imágenes que cita el README de Polyvore (`dnepozitek/maryland-polyvore-images`) **ya no existe en Kaggle**. Se usa la copia **Re-PolyVore** (`akshaypujari124/polyvore-images`, 3,4 GB), cuyos archivos se llaman `<set_id>_<índice>.jpg`, igual que los ítems de Han et al. (2017). Se verificó con un producto de prueba (`100002074_3`, "givenchy leather medium antigona duffel black" → foto de ese bolso negro). → *Fase 2 · Recolección (fuente secundaria; es una copia subida por un tercero).*
- Se procesa en **Google Colab** porque la descarga no cabe en el equipo del equipo de trabajo; a la computadora solo vuelve una tabla de colores.
- **Método** (`src/modelo_fly/color_imagen.py`): la foto se reduce a 64×64; se quita el fondo (píxeles transparentes o casi blancos, los tres canales ≥ 240); cada píxel se asigna al tono más cercano de una paleta de 14 tonos con varios prototipos cada uno, en el espacio CIELAB (ΔE76); el tono con más píxeles es el dominante. Si queda menos del 3 % de la imagen después de quitar el fondo, la prenda es blanca. La familia sigue la misma idea del catálogo: neutros, azul poco saturado (denim, navy) = neutro, claro y poco saturado = suave, el resto = fuerte. → *Fase 3 · Preparación.*
- **Limitación:** la foto no distingue metales (dorado, plateado); se ven como amarillo/beige y gris. Se corrige solo en joyería (ver el ajuste más abajo). → *Limitaciones.*
- **Prueba del método:** acierta en la foto real (bolso negro) y en colores sintéticos (rojo, navy, denim, rosa pastel, mostaza, camel, verde oliva, blanco, fondo transparente).
- **Resultado de Colab (01/11/2026):** 126 928 fotos procesadas, **0 con error**.
- **La copia guarda cada producto una sola vez.** Solo 76 543 de sus claves coinciden con un ítem de Polyvore (la copia trae además ~10 900 outfits que no están en la versión de Han et al.), y dentro de un outfit falta la foto de los productos que ya aparecieron antes. Por eso la unión se hace por **producto** (`tid`), no por `item_key`. Se comprobó que es correcta: la carpeta de la copia coincide con la categoría de Polyvore (p. ej. *Pumps* → `shoes` en 2 904 de 2 910) y solo 2 de 61 000 productos reciben dos colores distintos. → *Fase 2 · Recolección / calidad de datos.*
- **Cobertura:** 60 486 de 81 372 prendas de outfits vestibles tienen foto (**74,3 %**; de 62,8 % en joyería a 85,6 % en bolsos). → *Fase 2.*
- **Ajuste del gris (hallazgo):** al comparar con el texto, el tono "gris" se quedaba con las sombras de las prendas blancas y con los azules apagados (de las prendas que el nombre llama negras, 882 salían grises). Se añadió un ajuste (`ajustar` en `color_imagen.py`): si el segundo tono tiene ≥ 15 % de los píxeles gana él; un gris con L* ≥ 80 es blanco y con L* < 35 es negro. En joyería, los tonos cálidos de la foto pasan a **dorado** y los claros fríos a **plateado**. Los tres umbrales se eligieron con la partición oficial *train*; se informan las cifras de *valid + test*. → *Fase 3 · Preparación.*
- **Validación del método (prendas donde el nombre sí dice el color):**

  | | prendas | mismo tono sin ajuste | mismo tono | misma familia |
  |---|---|---|---|---|
  | train (calibración) | 15 486 | 48,1 % | 61,1 % | 80,7 % |
  | **valid + test** | 2 377 | 43,7 % | **57,0 %** | **76,9 %** |

  Por slot, la familia coincide entre 72,9 % (vestidos) y 84,9 % (calzado); en joyería el tono exacto solo coincide 54,4 %. El error más común es texto "fuerte" → foto "neutro" (2 245 prendas): el color que dice el nombre a veces es un detalle (un estampado, un ribete) y no el de la mayor parte de la prenda. → *Fase 5 · Evaluación / Limitaciones.*
- **Decisión: manda el texto.** La foto solo rellena el tono y la familia cuando el nombre no dice el color (42 623 prendas, `origen_tono = foto`). Las columnas `tono_foto` y `familia_foto` se guardan para todas las prendas con foto. → *Fase 3.*
- **Efecto:** prendas con color conocido **30,3 % → 82,7 %**; outfits con el color de todas sus prendas **1,1 % → 40,0 %**; con al menos la mitad 95,7 %; sin ningún color 0,3 %. Con esto las reglas de color ya se pueden aplicar en Polyvore. → *Fase 3 / Fase 4.*
- **Época:** casi ningún nombre dice la década (97 % contemporáneo), así que la regla Ep1 casi no se puede aplicar en Polyvore. Se mantiene y se declara como limitación; en el catálogo propio sí hay décadas.
- El nombre y la descripción del outfit **no ayudan** con el estilo: solo el 11 % menciona uno.

---

## Limitaciones para la sección de conclusiones

1. El gusto de los usuarios es **simulado**; lo real es qué combinan las personas (Polyvore).
2. Polyvore es mayoritariamente ropa de mujer (3 441 ítems de categorías de hombre de 142 480).
3. Los atributos de Polyvore salen del texto y de la foto, no de etiquetas de expertos; se validan con una muestra manual de 200 prendas (paso 4, pendiente).
4. El catálogo propio fue generado por una IA y sus atributos son casi aleatorios; se usa solo como prendas de clóset.
5. El color de la foto coincide con el del nombre en el 57 % de los tonos y el 77 % de las familias (valid + test); el 17,3 % de las prendas sigue sin color (el nombre no lo dice y la copia Re-PolyVore no trae la foto).
6. 9 362 productos aparecen en más de un outfit vestible: la partición 70/15/15 debe evitar que un mismo producto quede en train y en test (se decide en el paso 4).
