# Hallazgos y decisiones del Hito 3 (para el informe)

Registro de lo que se descubrió y se decidió en cada etapa del código, con las cifras exactas. Cada punto dice **en qué parte del informe** va. Lo mantiene el equipo de código; Sergio lo usa para redactar.

- **Plan completo y justificación:** `docs/REVISION_Hito2_y_brechas_Hito3.md` (§12 y §12.12).
- **Dónde reproducir cada cifra:** el notebook indicado en cada sección.

Última actualización: 06/11/2026.

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
| Usuarios simulados | 300 mixtos + 50 de transferencia (clóset 100 % propio); gusto = reglas + estilo + clima + neutros + **compatibilidad humana** aprendida de Polyvore | 06/11/2026 | Fase 3 · Preparación |

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

### Paso 4a · Validación manual de atributos (`notebooks/hito3/02_validacion_muestra.ipynb`)

- **Por qué:** responde a la crítica del profesor sobre datos sin verificar. Una persona compara los atributos que sacamos con la foto real y se mide la **precisión** de cada atributo con intervalo de confianza del 95 % (Wilson). → *Fase 5 · Evaluación de la calidad de datos.*
- **Muestra:** 25 prendas por slot (8 slots → **200**), al azar con semilla fija (2026), entre las 60 486 prendas de outfits vestibles **que tienen foto** (hace falta verla para juzgar). En la muestra, el tono de 141 prendas viene de la foto y el de 59 del nombre, así que también se mide la precisión de cada fuente.
- Solo se bajan esas 200 fotos de Kaggle (7 MB; no se suben a git). Planilla: `data/revision/polyvore_muestra_revision.xlsx`, con la miniatura de la foto y columnas `ok_<atributo>` (si / no / `-` si es desconocido o no aplica).
- **Regla escrita antes de revisar** (en el notebook): qué cuenta como neutro, suave y fuerte; liso = no se ve estampado; el estilo solo se marca `no` si claramente no corresponde.
- **Cómo se revisó (02/11/2026):** Nicole revisó las 200 filas y corrigió escribiendo directamente sobre la columna del atributo; lo que no cambió lo dio por correcto. El notebook convierte eso en marcas (`incorporar_ediciones`): valor conocido cambiado = `no`; valor sin cambio = `si` (*aceptación implícita*); desconocido rellenado = etiqueta manual, que no cuenta como error. La planilla tal como ella la guardó queda en el historial de git (commit `ed88f5f`).
- **Resultado** (`results/hito3/validacion_atributos.csv`, IC 95 % de Wilson):

  | atributo | revisadas | correctas | precisión | IC 95 % |
  |---|---|---|---|---|
  | slot | 200 | 200 | 100 % | 98,1–100 |
  | tono | 200 | 200 | 100 % | 98,1–100 |
  | familia de color | 200 | 200 | 100 % | 98,1–100 |
  | patrón | 199 | 198 | 99,5 % | 97,2–99,9 |
  | material | 70 | 70 | 100 % | 94,8–100 |
  | estilo | 30 | 28 | 93,3 % | 78,7–98,2 |
  | calce | 20 | 20 | 100 % | 83,9–100 |
  | largo | 23 | 23 | 100 % | 85,7–100 |

  Errores encontrados: un bolso marcado *liso* que es de cuadros, y dos zapatillas urbanas (Converse, Stan Smith) marcadas *athleisure* que la revisora considera *casual*. → *Fase 5 · Evaluación.*
- **⚠ Cautela al informar el color:** el 100 % de tono no cuadra con el acuerdo texto–foto del paso 3b (57 % de tono exacto). Con aceptación implícita, un error que no se ve a simple vista cuenta como correcto. Por eso el color se volvió a revisar aparte (siguiente punto), y el 100 % de la tabla de arriba debe presentarse solo como **cota superior**. → *Limitaciones.*
- **Re-chequeo del color a ciegas (02/11/2026, `results/hito3/validacion_color.csv`):** 40 prendas (5 por slot, de la muestra de 200, semilla 7), con la foto grande y **sin el nombre ni el origen del color**; cada fila se marcó explícitamente (0 sin marcar).

  | | revisadas | tono correcto | IC 95 % | familia correcta | IC 95 % |
  |---|---|---|---|---|---|
  | **todas** | 40 | **82,5 %** | 68,0–91,3 | **92,5 %** | 80,1–97,4 |
  | color de la foto | 30 | 86,7 % | 70,3–94,7 | 93,3 % | 78,7–98,2 |
  | color del nombre | 10 | 70,0 % | 39,7–89,2 | 90,0 % | 59,6–98,2 |

  Estas son las **cifras a informar** para el color. Los 7 tonos marcados como incorrectos: marrón → "marrón claro", negro → "vino", blanco → "hueso", plateado → negro, negro → blanco, blanco → "acuamarina", marrón → "colorido" (prenda multicolor). Varios son matices (hueso ≈ crema, marrón claro ≈ beige), así que la cifra es estricta. Las 3 familias incorrectas: dos que la revisora ve *suaves* (marcadas fuerte y neutro) y una naranja que ve *neutra*. → *Fase 5 · Evaluación.*
- **Lectura:** el color de la foto acierta más (87 %) que su acuerdo con el nombre (57 %, paso 3b); eso indica que buena parte del desacuerdo viene del **nombre** (colores de un detalle, nombres de fantasía), no de la foto. Con solo 10 casos, la precisión del color del nombre (70 %) tiene un intervalo muy ancho. Una limitación del método: las prendas multicolor reciben un solo tono. → *Fase 5 / Limitaciones.*
- **Hallazgo — estilo desconocido:** donde el método dejó el estilo *desconocido*, la revisora pudo asignarlo en 66 prendas: formal 24, casual 23, vintage 8, athleisure 6, deportivo 2 (más 3 valores fuera del vocabulario: "verano" ×2, "collar" ×1, que no se cuentan). Es decir, el 82 % de estilo desconocido no significa que la prenda no tenga estilo, sino que el nombre no lo dice; la mayoría son casual o formal. → *Fase 2 · Calidad / Limitaciones.*
- También rellenó 5 materiales desconocidos (cuero 2, seda 2, lana 1).

### Paso 4b · Partición 70/15/15 sin fuga de productos (`notebooks/hito3/03_particion.ipynb`)

- **Hallazgo:** los productos se repiten mucho entre outfits. Al unir outfits que comparten productos, **un solo grupo junta 10 625 outfits (70,8 %)**; el resto son 3 795 grupos chicos (3 382 outfits no comparten nada). Una partición al azar 70/15/15 dejaría al **70 % de los outfits de valid/test con algún producto ya visto en train** (5 199 productos en dos particiones): la evaluación saldría inflada. → *Fase 3 · Preparación / Fase 5.*
- **Método:** se parte de la partición oficial de Han et al. (2017), que ya no comparte productos, y se mueven a valid y test **grupos completos** de outfits de train que no tocan el resto de train (cada grupo va a la partición que está más lejos de su meta; semilla 2026). Se verifica que **0 productos** quedan en dos particiones.
- **Resultado:** train **10 625 (70,8 %)**, valid **2 194 (14,6 %)**, test **2 193 (14,6 %)**. Es lo más cerca de 70/15/15 que se puede llegar sin fuga: train ya es exactamente el grupo grande. Salida: `data/processed/hito3/particion_outfits.csv` (se sube a git para que todo el equipo use la misma). → *Fase 3.*
- **Diferencia entre particiones:** valid/test tienen más outfits con vestido (36,6–36,9 % frente a 24,1 % en train) y algo menos de prendas (5,1 frente a 5,55), porque los grupos que se pueden mover son outfits con productos poco repetidos. Conviene informar las métricas también por tipo de outfit (vestido / arriba+abajo). → *Fase 5 / Limitaciones.*

---

## Etapa 4 · Negativos y reglas de armonía (`notebooks/hito3/04_negativos_reglas.ipynb`)

*(En el plan §12.10 este notebook se llamaba `02_reglas_y_negativos`; se renumeró porque la validación y la partición ocuparon el 02 y el 03.)*

### Negativos (etiqueta TTMn: real = 1 / falso = 0)

- **Dos negativos por outfit real**, siempre con productos de **la misma partición** del paso 4b (así la partición sigue sin fuga):
  - `aleatorio`: se cambian **todas** las prendas por otras del mismo slot (protocolo de compatibilidad de Han et al., 2017).
  - `dificil`: se cambia **una sola** prenda por otra del mismo slot y, si se conoce, del mismo estilo (riesgo §12.11, "negativos demasiado fáciles").
- **Controles:** 30 024 negativos (15 012 de cada tipo); 100 % con los mismos slots y el mismo número de prendas que su real (no reaparece el atajo `n_prendas` del Hito 2); 100 % de los productos en su partición; 0 negativos iguales a un outfit real y 0 repetidos. → *Fase 3 · Preparación.*
- Total para la fase 2: **45 036 outfits** (train 31 875, valid 6 582, test 6 579; 1/3 reales). En la etapa 7 se decide si se entrena con uno o los dos tipos de negativo.
- **Decisión técnica:** se trabaja por producto (`tid`); se verificó que un mismo producto tiene siempre los mismos atributos en todos sus outfits.

### Reglas de armonía (etiqueta DLMn: 0–7)

- **Cómo se calculan** (`src/modelo_fly/reglas.py`): el score es el número de reglas **no violadas**; una regla que no aplica cuenta como cumplida (§12.4). Los atributos desconocidos se ignoran. → *Fase 3.*

  | Regla | Cómo se mide con los datos que hay |
  |---|---|
  | C1 | Como máximo 2 tonos no neutros distintos y 1 tono fuerte |
  | C2 | Si hay ≥ 2 tonos no neutros, al menos una prenda neutra |
  | P1 | Si hay dos tipos de estampado distintos, deben compartir un tono (**aproximación** del "color de fondo") |
  | P2 | No repetir el mismo tipo de estampado (**aproximación** de "misma escala y familia") |
  | P3 | Si hay ≥ 2 prendas estampadas, al menos una prenda de ropa lisa |
  | E1 | Como máximo una prenda de ropa oversize (necesita ≥ 2 prendas de ropa con calce conocido) |
  | Ep1 | No todas las prendas de ropa de la misma década (necesita ≥ 2 con década concreta; "contemporáneo" y "vintage genérico" no son década) |

- **Limitación:** Polyvore no trae la escala del estampado ni su color de fondo, así que P1 y P2 son aproximaciones. Las fuentes de cada regla siguen en §12.9 de la revisión (hay que verificar las citas). → *Limitaciones.*

### Hallazgos

- **Cuánto aplica cada regla en los outfits reales:** C1 58,5 %, C2 15,6 %, P2 y P3 9,0 %, P1 4,3 %, E1 3,2 %, **Ep1 0 %** (ningún outfit de Polyvore tiene dos prendas con década concreta: el 97 % es contemporáneo). Ep1 solo podrá actuar con el catálogo propio. → *Fase 2 / Limitaciones.*
- **El score casi siempre es alto:** el **80,8 %** de los outfits reales tiene 7/7 (reglas que no aplican cuentan como cumplidas). La etiqueta DLMn está muy desbalanceada; conviene reportar MAE junto con un baseline que siempre prediga 7. → *Fase 4 · Modelado.*
- **Las reglas sí separan algo lo real de lo falso, pero poco:**

  | | score medio real | score medio negativo | AUC del score | Mann-Whitney (p) |
  |---|---|---|---|---|
  | aleatorio | 6,768 | 6,678 | **0,539** | 1,8·10⁻⁵⁸ |
  | difícil | 6,768 | 6,740 | 0,512 | 2,2·10⁻⁷ |

  La diferencia es estadísticamente significativa pero pequeña. Eso **apoya el diseño de dos salidas**: las reglas (DLMn) no bastan para saber si un outfit es real (TTMn), así que el modelo tiene que aprender algo más que las reglas. → *Fase 5 · Evaluación / Discusión.*
- **Regla por regla** (% de outfits que la violan, real vs. aleatorio): C1 **13,3 % vs 21,0 %** (la que más separa), P1 3,0 % vs 5,3 %, P3 1,6 % vs 2,4 %. **P2 va al revés:** los outfits reales repiten el mismo tipo de estampado **más** que los aleatorios (3,4 % vs 2,3 %). Es decir, la gente sí combina estampados iguales (conjuntos de dos piezas, rayas con rayas), y esa regla de la literatura no se cumple en Polyvore. C2 casi nunca se viola (≈ 1 %): casi todos los outfits tienen alguna prenda neutra. → *Discusión (hallazgo interesante para el informe).*

### Salidas (en git)

- `data/processed/hito3/fase2_outfits.csv`: 45 036 filas (outfit_id, tipo, real, partición, productos, aplica/cumple por regla, score).
- `data/processed/hito3/fase2_productos.csv`: 65 366 productos con sus atributos. Con estos dos archivos las etapas siguientes no necesitan volver a descargar Polyvore.

---

## Etapa 5 · Conectoma del Giant Fiber System (`notebooks/hito3/05a_conectoma_descarga_colab.ipynb`, `05b_conectoma_red.ipynb`)

*(`05a` se corre en Google Colab porque necesita el token de neuPrint, que se lee del secreto `NEUPRINT_TOKEN` y nunca se escribe. `05b` corre en local, sin token.)*

### Descarga (05a, 05/11/2026)

- **Es el mismo subgrafo del Hito 2:** MaleCNS v1.0 (`male-cns:v1.0`), 7 tipos (`LC4`, `LPLC2`, `DNp01`, `PSI`, `TTMn`, `DLMn a, b`, `DLMn c-f`) y **327 neuronas**. Se volvió a consultar por dos motivos: `nodes.csv`/`edges.csv` del Hito 2 no se guardaron en el repositorio, y faltaba el neurotransmisor para fijar el signo (Opción A). → *Fase 2 · Comprensión de los datos.*
- **Corrección de una cifra del Hito 2:** **20 684 no son sinapsis, son conexiones** (pares pre→post distintos). El subgrafo tiene **79 950 sinapsis químicas**. Hay que corregirlo en el informe (revisión §1 dice "327 neuronas, 20 684 sinapsis"). → *Resumen de cambios respecto al Hito 2.*
- **Control:** el peso total de cada par (`ConnectsTo.weight`) coincide en los 20 684 pares con la suma por ROI que usaba el Hito 2 (0 diferencias). No hay autoconexiones. → *Fase 3.*

### Signo de cada conexión (`src/modelo_fly/conectoma.py`)

- **Regla de decisión** del neurotransmisor de cada neurona: (1) `consensusNt` de MaleCNS si no es "unclear"; (2) si no, la predicción del tipo si su confianza es ≥ 0,5; (3) si no, la literatura para ese tipo. Signo: acetilcolina **+1**; glutamato, GABA e histamina **−1** (convención de Shiu et al., 2024, modelo de cerebro completo de *Drosophila*). El signo es el de la neurona **presináptica**. → *Fase 3 · Preparación / Fase 4 · Modelado.*

  | Tipo | Neuronas | Lo que dice neuPrint | Confianza del tipo | Neurotransmisor usado | Origen | Signo |
  |---|---|---|---|---|---|---|
  | LC4 | 126 | acetilcolina | 0,96 | acetilcolina | consenso | + |
  | LPLC2 | 185 | acetilcolina | 0,95 | acetilcolina | consenso | + |
  | DNp01 (Giant Fiber) | 2 | acetilcolina | 0,53 | acetilcolina | consenso | + |
  | PSI | 2 | unclear | 0,37 | acetilcolina | literatura | + |
  | TTMn | 2 | consenso glutamato; predicción histamina | 0,52 | glutamato | consenso | − |
  | DLMn a, b | 2 | unclear | 0,38 | glutamato | literatura | − |
  | DLMn c-f | 8 | unclear | 0,45 | glutamato | literatura | − |

- **12 de 327 neuronas** (PSI y los DLMn) no tienen neurotransmisor fiable en neuPrint y se toma de la literatura: PSI colinérgico (sinapsis PSI→DLMn) y motoneuronas glutamatérgicas. **Sergio: verificar y citar ambas fuentes** (p. ej. la revisión del GFS de Allen et al., 2006, y el uso de glutamato en la unión neuromuscular de *Drosophila*). → *Fase 3 / Limitaciones.*

### Hallazgos

- **La red es casi toda excitadora:** solo **55 de 20 684 conexiones (0,27 %)** y **166 de 79 950 sinapsis (0,21 %)** son inhibidoras, y todas salen de las motoneuronas (TTMn y DLMn hacia DNp01, PSI y entre DLMn). En el camino de entrada → decisión → salida **no hay ninguna conexión inhibidora**. Consecuencia para el modelo: en la Opción A el signo casi no restringe nada; lo que realmente aporta la biología es la **máscara** (qué neurona se conecta con cuál). Conviene decirlo en la discusión para no sobrevender el "signo por neurotransmisor". → *Fase 4 / Discusión.*
- **La máscara es poco densa:** 19,3 % de los 327 × 327 pares posibles tienen conexión. → *Fase 4.*
- **Casi toda la señal se queda en la entrada:** el **84,8 %** de las sinapsis son entre neuronas de entrada (LPLC2→LPLC2 46 178, LC4→LC4 18 392). Las **311 neuronas de entrada** conectan directo con el Giant Fiber (11 224 sinapsis). → *Fase 2 / Fase 4.*
- **Cuello de botella en la salida:** todo pasa por **2 neuronas DNp01**. De ahí a TTMn hay solo 2 conexiones (90 sinapsis) y a PSI 4 conexiones (16 sinapsis); de PSI a los DLMn, 10 conexiones (449 sinapsis). Camino más corto desde la entrada: **2 saltos a TTMn** (entrada → GF → TTMn) y **3 a DLMn** (entrada → GF → PSI → DLMn), como describe la literatura del reflejo de escape. → *Fase 4 · Modelado (arquitectura) / Discusión.*
- **Las sinapsis eléctricas no están:** neuPrint solo cuenta sinapsis químicas. Las conexiones GF→TTMn y GF→PSI son en buena parte **eléctricas** (gap junctions, ShakB), así que los pesos 90 y 16 subestiman justo el camino de salida (revisión §12, punto ya anotado). Para la Opción B (pesos fijos) esto pesa más que para la A, donde los pesos se aprenden. → *Limitaciones.*
- **Figura:** `results/hito3/fig_conectoma_tipos.png`, sinapsis entre tipos (fila = envía, columna = recibe, con su signo). → *Fase 2.*

### Salidas (en git)

- Crudos de neuPrint: `data/processed/hito3/gfs_nodes.csv` (327 neuronas, 51 propiedades), `gfs_edges.csv` (20 684 conexiones), `gfs_meta.json` (dataset, fecha y versión).
- Para el modelo: `gfs_neuronas.csv` (327 neuronas en el orden de la red: capa, tipo, lado, neurotransmisor, origen y signo; la columna `idx` es la fila/columna de la matriz) y `gfs_conexiones.csv` (aristas con `idx_pre`, `idx_post`, sinapsis y signo). Las etapas siguientes ya no necesitan el token.

---

## Etapa 6 · Usuarios simulados (`notebooks/hito3/06_usuarios_simulados.ipynb`)

*(En el plan §12.10 este notebook se llamaba `03_usuarios_simulados`; se renumeró.)*

### Diseño (`src/modelo_fly/usuarios.py`) → *Fase 3 · Preparación de los datos*

- **350 usuarios:** 300 **mixtos** (clóset 70 % Polyvore / 30 % catálogo propio; en promedio 41,7 + 17,9 prendas) y 50 de **transferencia** (clóset 100 % catálogo propio, 62,5 prendas en promedio) para la prueba de cambio de dominio (§12.12).
- **Perfil:** arquetipo (minimalista 76, clásico 80, deportivo 71, vintage 62, atrevido 61), estilo favorito, edad (18–45), género (85 % mujer, porque Polyvore es casi todo ropa de mujer), ciudad del Perú y su clima (templado 216, frío 73, cálido 61). Los pesos de cada usuario salen de su arquetipo, perturbados al azar (log-normal, σ = 0,3). Se guardan todos (`usuarios.csv`) para medir si el DeepFM recupera los gustos programados.
- **Clóset:** 40–80 prendas con cuotas por slot y **sesgo ×3 hacia su estilo favorito** (el 44 % de las prendas con estilo conocido son de su estilo). Las prendas Polyvore salen **solo de valid y test** de la partición del paso 4b: la fase 2 nunca las ve al entrenar.
- **Outfits mostrados:** arriba + abajo + calzado, o vestido + calzado (30 %), más complementos con la frecuencia de los outfits reales (exterior 40 %, bolso 75 %, accesorio 45 %, joyería 55 %). Mayormente de 4 a 6 prendas, como en Polyvore.
- **Gusto simulado:**
  `utilidad = − Σ w_k · viola_k + b · coincide_estilo + c · clima + d · neutros + e · compatibilidad_humana`
  `p(acepta) = sigmoide(1,5 · (utilidad − sesgo_u))`, donde el sesgo es la mediana de la utilidad del usuario (≈ 50 % de aceptación). Después la decisión se invierte con probabilidad de 5–10 % (ruido, §12.3).
- **Decisión nueva: compatibilidad humana.** El plan §12.3 solo usaba reglas, estilo y clima, y eso hacía la etiqueta casi circular (el DLMn aprende las mismas reglas). Se añadió un término aprendido de Polyvore: para cada par de prendas se compara qué tan seguido aparecen juntos su tono, patrón, material y estilo (por slot) en outfits **reales** frente a negativos **aleatorios**, contado **solo en train**. Así el gusto también depende de lo que combinan las personas reales, que es lo que aprende TTMn. → *Fase 3 / Fase 4.*
- **Historial:** 50 outfits por usuario, separados en promedio 3 días (2025). Partición temporal **35 / 7 / 8** (17 500 interacciones: 12 250 / 2 450 / 2 800).
- **Controles:** ningún outfit se repite dentro de un usuario; **0 outfits** de test de un usuario aparecen en train de otro (regla §12.5; la primera versión tenía 14, todos de usuarios que comparten el catálogo propio, y se corrigió).

### Hallazgos

- **La compatibilidad humana separa lo real de lo falso mucho mejor que las reglas:** AUC en valid **0,702** contra 0,535 del score de reglas (negativos aleatorios); con negativos difíciles 0,562 contra 0,518. Es decir, en Polyvore hay una señal de "qué combina la gente" que las 7 reglas no capturan. → *Fase 2 · Comprensión / Discusión.*
- **Aceptación:** 49,0 % global; el ruido invirtió el 7,4 % de las decisiones. Por arquetipo y partición se mueve entre 43 % y 54 %. → *Fase 3.*
- **Qué explica las decisiones en test** (AUC contra lo aceptado):

  | Señal | Todos | Mixtos | Transferencia |
  |---|---|---|---|
  | **Techo** (probabilidad real de la simulación) | **0,833** | 0,824 | 0,875 |
  | Compatibilidad humana | 0,722 | 0,712 | 0,794 |
  | Score de reglas (DLMn) | 0,622 | 0,619 | 0,635 |
  | Coincide con el estilo favorito | 0,594 | 0,594 | 0,587 |
  | Gusto por neutros | 0,584 | 0,586 | 0,567 |

  Ninguna señal sola llega al techo: el modelo tiene que combinarlas y aprender los pesos de cada usuario. El techo (0,833) es el **máximo que puede lograr cualquier modelo**, porque el ruido no se puede predecir; conviene reportarlo junto a los resultados de la etapa 7. → *Fase 5 · Evaluación.*
- **Figura:** `results/hito3/fig_usuarios_senales.png`. → *Fase 3 / Fase 5.*
- **Casos borde:** 9 usuarios no aceptaron ningún outfit en valid y 3 ninguno en test; 2 aceptaron todo en valid. Para ellos Recall@K no se puede calcular y se excluyen de esa métrica (hay que decirlo en la etapa 7). → *Fase 5.*

### Salidas (en git)

- `data/processed/hito3/usuarios.csv` (350 usuarios con todos sus parámetros reales y su sesgo), `closets.csv` (user_id, item_id, origen, slot), `historial.csv` (17 500 interacciones con fecha, partición, reglas violadas, rasgos, utilidad, probabilidad real, si se invirtió y la decisión final) e `items_fase1.csv` (9 937 prendas de los clósets: 9 437 Polyvore + 500 propias, con sus atributos). Los ID de Polyvore llevan el prefijo `pv_`.

---

## Etapa 7 · Modelos

### Paso 7a · Candidatos para el ranking (`notebooks/hito3/07a_candidatos.ipynb`)

- **Qué es:** para medir Recall@K y NDCG@K, cada usuario tiene una lista de outfits de su clóset a ordenar: **valid 50** (sus 7 del historial + 43 nuevos, para ajustar α) y **test 100** (sus 8 del historial + 92 nuevos, para reportar). Los nuevos se etiquetan con el mismo gusto, sesgo y ruido del usuario. Se generan antes de entrenar para que todos los modelos ordenen exactamente los mismos outfits. → *Fase 5 · Evaluación (protocolo).*
- **Controles:** 52 500 candidatos; 0 están en el train de algún usuario y 0 repetidos. Aceptados por usuario en test: mediana 49 de 100 (mínimo 37).
- **Referencias del ranking en test:** NDCG@5 **al azar 0,507** y **techo 0,919** (ordenando por la probabilidad real de la simulación). Todo modelo debe quedar entre esos dos valores; conviene reportarlos en la tabla final. Como cerca de la mitad de los candidatos son aceptados, Recall@5 tiene un máximo bajo (5/49); se reportará normalizado por min(K, aceptados). → *Fase 5.*

### Paso 7b · Fase 2 en Colab (`notebooks/hito3/07b_fase2_colab.ipynb`)

- Entrada común (`src/modelo_fly/caracteristicas.py`): por cada slot, el número de prendas y el conteo de cada valor de cada atributo (464 columnas). Todos los modelos ven el mismo vector. → *Fase 3.*
- Red GFS (`src/modelo_fly/redes.py`): el outfit entra por una capa lineal a las 311 neuronas de entrada y se propaga 4 pasos por W = signo ⊙ softplus(θ) ⊙ máscara (un peso por cada conexión real, inicializado con log(1 + sinapsis) normalizado por neurona); se lee en las 2 TTMn (real/falso) y las 10 DLMn (armonía). El MLP de control tiene el mismo número de parámetros entrenables; la red barajada conserva grados de entrada y salida (solo el 24 % de sus conexiones coincide con la real). → *Fase 4 · Modelado.*
- *(Resultados pendientes de la corrida en Colab.)*

---

## Limitaciones para la sección de conclusiones

1. El gusto de los usuarios es **simulado**; lo real es qué combinan las personas (Polyvore).
2. Polyvore es mayoritariamente ropa de mujer (3 441 ítems de categorías de hombre de 142 480).
3. Los atributos de Polyvore salen del texto y de la foto, no de etiquetas de expertos; se validan con una muestra manual de 200 prendas con foto (paso 4a; la muestra no cubre las prendas sin foto).
4. El catálogo propio fue generado por una IA y sus atributos son casi aleatorios; se usa solo como prendas de clóset.
5. El color se validó a ciegas en 40 prendas: tono correcto 82,5 % (IC 68–91 %) y familia 92,5 % (IC 80–97 %); la muestra es chica. La foto y el nombre coinciden solo en el 57 % de los tonos, y las prendas multicolor reciben un solo tono; el 17,3 % de las prendas sigue sin color (el nombre no lo dice y la copia Re-PolyVore no trae la foto).
6. Para que ningún producto quede en dos particiones, la partición es 70,8/14,6/14,6 y valid/test tienen más vestidos que train (37 % frente a 24 %); los productos más populares (el grupo grande) solo están en train.
7. Las reglas P1 y P2 son aproximaciones (no hay escala ni color de fondo del estampado), Ep1 no aplica a ningún outfit de Polyvore, y el 80,8 % de los outfits reales tiene score 7/7: la etiqueta DLMn tiene poca variación.
8. El conectoma solo trae sinapsis químicas (las eléctricas GF→TTMn y GF→PSI no están); 12 de 327 neuronas (PSI y DLMn) no tienen neurotransmisor fiable en neuPrint y se toma de la literatura; y la red es casi toda excitadora (0,2 % de sinapsis inhibidoras), así que el signo por neurotransmisor restringe muy poco.
9. Los usuarios y su gusto son simulados con 5 arquetipos; el término de compatibilidad humana viene de Polyvore (real), pero los pesos de cada usuario los fijamos nosotros. La edad, el género y la ciudad no influyen en el gusto salvo por el clima, así que el modelo no debería sacar nada de ellos.
