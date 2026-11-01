# Modelo Fly · Revisión del proyecto al cierre del Hito 2 y brechas para el Hito 3

Revisión hecha el 21/10/2026 sobre la carpeta `ENTREGA_PARCIAL/`. Se leyeron todos los documentos y notebooks, y varias cifras se volvieron a calcular directamente desde los CSV (pandas) para confirmarlas.

> **Actualización 22/10/2026:** el proyecto pivotó a un recomendador en dos etapas (DeepFM → conectoma GFS) sobre outfits reales de Polyvore y usuarios simulados. **El plan vigente es §12**; §8 y §10 quedan solo como historial.
>
> **Actualización 29/10/2026:** se **combina Polyvore con el catálogo propio de 500 prendas** (§12.12). Polyvore aporta la verdad de compatibilidad; el catálogo propio entra como prendas de clóset, sin sus 100 000 etiquetas.
>
> **Actualización 31/10/2026 (etapa 1):** el repositorio se reorganizó. Las rutas `src/…` de este documento ahora son `notebooks/hito2/` (`Copia de EDA` → `01_EDA`, `baseline` → `02_baseline`, `Connectome` → `03_conectoma_neuprint`); `EDA.ipynb` se retiró (§2.3). Quedan resueltos §2.3 y casi todo §2.11 (rutas, `outfits_unido.csv`, última celda del baseline, `requirements.txt`). Falta `nodes.csv`/`edges.csv` (etapa 5).

**Archivos revisados**

| Archivo | Qué es | Estado |
|---|---|---|
| `TP1 Hito 2_.docx` | Informe escrito (Fases 1–4 + diagnóstico) | Contenido sólido, con errores de numeración, tablas faltantes y un resumen desactualizado (ver §3) |
| `Hito 2 — Modelo FLY.pdf` | Versión anterior de la presentación | Portada con fases mal nombradas; **no coincide con el PPTX** |
| `Modelo_Fly_Hito2.pptx` | Presentación final (12 + 6 de respaldo) | Correcta y coherente con el CSV de métricas |
| `Guia_Modelo_Fly_Hito2.md` | Guion de la exposición | Coherente; tiene un "dato pendiente" que en realidad ya existe |
| `src/Connectome.ipynb` | Extracción del subgrafo GFS desde neuPrint + simulación looming | Funciona (Colab). Simulación débil como validación (§2.9) |
| `src/EDA.ipynb` | Primer EDA genérico | **Lee mal el catálogo** (1 columna). Debería retirarse (§2.3) |
| `src/Copia de EDA.ipynb` | EDA real (unión, tasas, Cramér, reglas) | Correcto. Genera `outfits_unido.csv` |
| `src/baseline.ipynb` | Preparación + logística/árbol + Ridge | Correcto en lo que hace; protocolo de partición con fuga (§2.4). Última celda falla |
| `data/*.csv`, `outfits_{train,validation,test}_100k.csv` | Datos crudos y particiones | Las 3 particiones suman exactamente los 100 000 outfits |
| `metricas_baseline*.csv`, `figuras_*/` | Salidas | Coinciden con los notebooks |

---

## 1. Alcance del proyecto hasta ahora

### 1.1 Qué se plantea

Probar si la **conectividad del Giant Fiber System** de *Drosophila* (MaleCNS v1.0, 327 neuronas, 20 684 sinapsis) sirve como arquitectura para una decisión binaria trasladada a moda: **¿un outfit de 2 o 3 prendas combina?** Entradas por prenda: época, color, patrón y estilo. Salida principal en TTMn (binaria) y secundaria en PSI→DLMn (score 0–1). ODS 12.

- **H1:** la red con conectividad GFS rinde igual o mejor que modelos sin esa estructura.
- **H0:** no aporta ventaja.
- Criterios de éxito: accuracy ≥ 0.82, F1 ≥ 0.85, AUC ≥ 0.88.

### 1.2 Avance por fase CRISP-DM

| Fase | Qué está hecho | Qué falta |
|---|---|---|
| 1 · Negocio | Problema, hipótesis, analogía estructural, ODS 12, criterios de éxito | Reformular criterios (el F1 ≥ 0.85 no discrimina: el trivial ya lo cumple). Definir margen de no inferioridad |
| 2 · Datos | EDA de moda (tasas, heatmaps, Cramér, reglas simples); EDA del conectoma (tipos, conteos, aristas de literatura, flyvis) | Incluir `categoria` en el EDA (§2.1). Limpiar semántica de color/patrón (§2.5) |
| 3 · Preparación | Unión con catálogo, "ninguna" para prenda 3, one-hot A (288) y B (396), partición 70/15/15 estratificada | Partición agrupada por combinación (§2.4). Representación invariante al orden (§2.6). Decidir dataset nuevo o depurado |
| 4 · Modelado | Baseline: logística y árbol (A/B), Ridge para score | **Todo el Hito 3:** RF, XGBoost, red GFS, controles, tuning |
| 5 · Evaluación | Test único, subgrupo 2 prendas, 30 casos, reajuste sin combinaciones vistas, diagnóstico de 5 brechas del dataset | Validación cruzada, análisis de errores sistemático, prueba estadística de H1 |
| 6 · Despliegue | Intento de exportar `modelo_baseline.joblib` para un dashboard (falló, §2.11) | Integración con la base de datos común |

### 1.3 Resultados actuales (test, 15 000 outfits)

| Modelo | Accuracy | F1 | AUC |
|---|---|---|---|
| Siempre compatible | 0.750 | 0.857 | — |
| Árbol A / B (prof. 8) | 0.912 / 0.914 | 0.942 / 0.942 | 0.952 / 0.957 |
| Logística A / B (umbral 0.70) | 0.982 / 0.992 | 0.988 / 0.995 | 0.984 / 0.995 |
| Logística B, solo 2 prendas (n = 8 236) | 0.985 | 0.987 | 0.986 |
| Logística B, 30 casos tras quitar sus combinaciones del train | **0.800** | 0.750 | 0.742 |

La última fila es el número más honesto que tienen: cuando el modelo no ha visto la combinación, cae por debajo de la meta.

---

## 2. Observaciones técnicas (de mayor a menor impacto)

Las marcadas con ★ **no aparecen** en ninguno de los documentos actuales; son hallazgos nuevos de esta revisión.

### 2.1 ★ La variable `categoria` nunca entró al análisis, y explica buena parte de la etiqueta

El catálogo tiene `categoria` (Camiseta, Pantalón, Vestido, Chaqueta, Falda, Blusa, Short, Calzado), pero ni el EDA ni el baseline la usan. Recalculado sobre los 54 910 outfits de 2 prendas:

| Combinación de categorías | n | Tasa compatible |
|---|---|---|
| Blusa + Falda | 5 457 | 0.877 |
| Camiseta + Pantalón | 7 618 | 0.825 |
| Calzado + Vestido | 2 607 | 0.809 |
| Chaqueta + Vestido | 5 242 | 0.807 |
| … (10 combinaciones "arriba + abajo" o "vestido + complemento") | | 0.44 – 0.88 |
| Camiseta + Vestido, Pantalón + Vestido, Camiseta + Camiseta, Pantalón + Short, Calzado + Pantalón… (26 combinaciones) | ~16 000 | **0.000** |

- Dos prendas de la **misma categoría** (6 % de los outfits de 2) son **siempre** incompatibles.
- Cualquier par que no sea una plantilla "arriba + abajo" (o vestido + chaqueta/calzado) es siempre incompatible.

**Consecuencias:**
1. La etiqueta sí tiene una lógica de moda razonable, pero vive en `categoria`, que el modelo no ve. El modelo la reconstruye de forma indirecta a través de colores raros (por eso la diapositiva A2 muestra colores puntuales como los coeficientes más altos).
2. La lectura "la misma época baja la compatibilidad (0.43 vs 0.77)", que se presentó como contraintuitiva y como evidencia de que el dataset sale de reglas, **puede estar confundida por la categoría**. Hay que repetir esa comparación controlando la plantilla de categorías antes de seguir afirmándolo. Ojo también con la regla Ep1, que se justificó con esa misma cifra.
3. `categoria` debe entrar como variable (por prenda y como plantilla del outfit) en el Hito 3.

### 2.2 ★ Los outfits de 3 prendas tienen etiquetas sin sentido

Los 45 090 outfits de 3 prendas son compatibles, incluidos `Camiseta + Pantalón + Pantalón` (1 238), `Camiseta + Camiseta + Pantalón` (1 163) y `Blusa + Falda + Falda` (964). Esto refuerza la brecha 5.2 del informe: la etiqueta de 3 prendas no es confiable y no debería usarse para evaluar sin depurarla.

### 2.3 ★ `EDA.ipynb` lee mal el catálogo

`pd.read_csv('prendas_base_500_mejorado.csv')` sin `sep=';'` → el catálogo queda en **1 columna** (se ve en la salida: "500 filas × 1 columnas"). El word cloud y las estadísticas del catálogo de ese notebook salen de una sola cadena de texto. El párrafo 2.1 del informe ("El catálogo de 500 prendas no tiene valores vacíos… en las descripciones se repiten vintage, casual y formal") viene de ahí. Además, ese notebook aplica IQR/z-score a la etiqueta binaria (los "25 000 outliers" de `compatible` son simplemente la clase 0), lo cual no tiene sentido metodológico. Recomendación: retirar `EDA.ipynb`, renombrar `Copia de EDA.ipynb` → `01_EDA.ipynb`, y reescribir §2.1 del informe con lo que da el notebook correcto.

### 2.4 La partición por filas filtra combinaciones entre train y test

Confirmado: hay 41 211 combinaciones distintas en 100 000 filas, y **8 890 combinaciones aparecen en más de una partición**. Los compatibles de 2 prendas son solo **43 pares** repetidos hasta ~760 veces. El 0.99 mide sobre todo memorización. El informe ya lo reconoce (§5), pero el Hito 3 tiene que corregirlo en el protocolo:

- Clave de grupo = conjunto ordenado de `prenda_id`.
- Deduplicar (o agregar por grupo) y usar **`StratifiedGroupKFold`** para la validación cruzada y para el test final.
- Volver a correr el baseline con ese protocolo para que la comparación con los modelos nuevos sea justa.

Diferencia menor: al recontar obtuve 29 910 filas / 22 739 combinaciones (informe: 29 917 / 22 733). Probablemente son las 6 combinaciones con etiquetas contradictorias contadas en otro grupo. Conviene dejar escrita la definición exacta de la clave.

### 2.5 ★ Las categorías de color, patrón, época y estilo mezclan conceptos

- **Color (69 niveles)** incluye valores que no son colores (`Vintage`, `Denim`, `Estampado Vintage`, `Faded Colors`, `Desteñido`, `Cuero Desteñido`, `Pastel`) y sinónimos (`Gris Carbón` / `Gris Charcoal`, `Beige Neutral` / `Beige Neutro`, `Azul Faded` / `Faded Blue`). 29 colores tienen 3 prendas o menos.
- **Patrón** mezcla patrones (Floral, Gráfico, Liso) con materiales (Cuero, Denim, Terciopelo, Encaje). Es justo la duda pendiente del informe §7.
- **Época** mezcla décadas (Años 50–90) con etiquetas de estilo (Retro, Vintage, Tumblr).
- **Estilo** mezcla estilo (Casual, Formal, Deportivo) con calce (Oversize, Ajustado, Recto).

Proponer un mapeo documentado: color → familia (neutro / acento suave / acento fuerte, más el tono base), patrón → {liso, estampado} + material, estilo → {estilo, calce}. Así se reduce la dispersión del one-hot y quedan resueltas las tres decisiones pendientes del §7 del informe.

### 2.6 ★ La representación depende del orden de las columnas

`epoca_1` y `epoca_2` son variables distintas, aunque el orden de las prendas no significa nada. Los cruces de par solo usan las prendas 1 y 2 e ignoran la 3. Alternativas para el Hito 3:
- **Bolsa de atributos:** conteo de cada valor en el outfit (invariante al orden, sirve para 2 o 3 prendas).
- Cruces sobre **todos** los pares (1-2, 1-3, 2-3) agregados.
- Si la red GFS recibe prendas por separado, compartir pesos entre posiciones.

### 2.7 Ajustes de protocolo del baseline

- El umbral elegido (0.70) está en el **borde** de la grilla 0.30–0.70: hay que ampliarla (0.05–0.95) o usar la curva PR completa.
- No se ajustó `C` de la logística (lo dice el propio notebook). El Hito 3 pide ajuste de hiperparámetros.
- No se calcularon métricas en train (el informe lo marca como pendiente). Son necesarias para la curva de aprendizaje y para hablar de sobreajuste.

### 2.8 El score continuo no aporta como segunda salida

`score_compatibilidad` está pegado a la etiqueta (r = 0.955, sin solape entre clases). El R² del Ridge (0.67–0.74) viene casi todo de separar las clases (lo dice la diapositiva A3). Opciones: (a) dejarlo como salida auxiliar y reportarlo sin darle peso en H1; (b) redefinirlo en el dataset nuevo como una medida graduada (por ejemplo, el número de reglas que se cumplen). Hay que decidirlo antes de diseñar la rama DLMn.

### 2.9 ★ La simulación del looming valida poco

- Todas las sinapsis se tratan como excitatorias, aunque `predictedNt` está disponible. Hay que revisar si hay tipos GABA/glutamato en el subgrafo y aplicarles signo.
- La actividad no está acotada (máximo 20.8) y el umbral de TTMn (0.05) se cruza en t = 7: casi cualquier grafo conectado "pasaría" esta prueba. Faltó el control: la misma simulación sobre un grafo aleatorio con el mismo número de aristas.
- Las conexiones GF→TTMn y GF→PSI se describen en la literatura como en buena parte **eléctricas** (gap junctions, ShakB). El conteo de neuPrint solo ve sinapsis químicas, así que los pesos 90 y 16 subestiman justo el camino de salida. El informe ya dice que no se separan los tipos; conviene añadir esta consecuencia, con una cita verificada.
- Recomendación: presentarla como prueba de cordura, no como validación, y añadir el control aleatorio.

### 2.10 ★ Falta especificar cómo se construye la red GFS

Es el núcleo de H1 y todavía no tiene diseño. Hay que definir:
- **Entrada:** cómo pasan las ~300 variables (o la bolsa de atributos) a las 311 neuronas LC4/LPLC2. ¿Una capa de proyección aprendible? ¿Una neurona por atributo?
- **Conectividad:** máscara fija con la adyacencia (327×327); pesos aprendibles con el signo fijado o libres; inicialización con el conteo sináptico.
- **Dinámica:** red recurrente de T pasos (como la simulación) o feed-forward por capas.
- **Cuello de botella:** TTMn son 2 neuronas con grado de entrada 1 (solo reciben de DNp01), y DNp01 son 2 neuronas. Toda la información pasa por 2 unidades. Es un rasgo interesante para la hipótesis, pero hay que anticiparlo.
- **Controles:** (i) la misma arquitectura con aristas barajadas (mismo grado y densidad); (ii) un MLP denso con un número parecido de parámetros.

### 2.11 Reproducibilidad

- `baseline.ipynb` necesita `data/outfits_unido.csv`, que **no está** en la carpeta. Lo genera `Copia de EDA` en `/content` de Colab.
- `Connectome.ipynb` exporta `nodes.csv`, `edges.csv` y `type_resolution.json`, que tampoco están en la carpeta. Sin ellos no se puede construir la red GFS sin volver a consultar neuPrint con un token.
- Las rutas están mezcladas: Colab (`/content`) y local (`D:\UPChexk\...`).
- La última celda de `baseline.ipynb` falla (`NameError: modelos_ajustados`), así que `dashboard/modelo_baseline.joblib` nunca se guardó.
- No hay `requirements.txt` ni un orden de ejecución numerado.

---

## 3. Inconsistencias en los documentos entregados

**Informe (`TP1 Hito 2_.docx`)**
- El resumen ejecutivo dice que el informe cubre solo Negocio y Datos y que "el modelado y la evaluación quedan para el siguiente hito". Está desactualizado.
- Numeración: falta 4.5 (aunque §5.4 la cita), **4.6 "Score continuo" aparece dos veces** junto con un párrafo duplicado, falta la sección 6, y la introducción de §3 menciona "secciones 7 y 8", pero no existe la 8.
- Tabla 4.3: la accuracy de Logística A dice **0.9878**, pero es 0.9815 (0.9878 es su F1). Erratas: "simpere", "0,70" con coma.
- §4.4 dice "los resultados cambian:" y **no hay tabla** después (deberían ir 0.7667 / 0.80). También falta la tabla de falsos positivos del subgrupo de 2 prendas (277 → 121).
- Se usa `es_compatible` en el texto, pero la columna se llama `compatible`.
- Los anexos terminan con notas sueltas ("info", "¿Cómo iniciar un proyecto de machine learning?").
- Fecha "Septiembre 2026": hay que actualizarla para el Hito 3.

**PDF vs PPTX**
- La portada del PDF dice "Fase 3 Modelado / Fase 4 Evaluación". El PPTX ya está corregido ("Fase 3 Preparación / Fase 4 Modelado"), pero el PDF es una exportación anterior. Si el PDF fue lo que se subió, el profesor vio la versión con error.

**Guía**
- La sección "Dato pendiente" dice que no están la accuracy de los 30 casos ni la del reajuste, pero ambas están en `metricas_baseline_extra.csv` (1.0 sin reajuste; 0.7667 / 0.80 con reajuste).

**Mensaje entre documentos**
- El PPTX (diap. 8) dice "Las cuatro configuraciones superan los umbrales", mientras que el informe (§3 y §5) dice que esas métricas "no son válidas todavía" y que no se usarán para H1. En el Hito 3 conviene alinear el mensaje: el baseline cumple los umbrales bajo el protocolo antiguo, pero no es válido con el protocolo agrupado.

---

## 4. Lo que falta para el Hito 3

### 4.1 Requisitos del hito y su estado

| Requisito | Estado | Qué hay que hacer |
|---|---|---|
| **Modelado avanzado** (XGBoost, RF o series temporales) | ✗ | Random Forest + XGBoost (opcional LightGBM) como "modelos sin estructura" fuertes; **red GFS**; controles (GFS barajada + MLP). Las series temporales no aplican al problema. |
| **Ajuste de hiperparámetros** | ✗ | Búsqueda aleatoria u Optuna **dentro** de la CV agrupada (CV anidada, o CV interna en train y test agrupado aparte). Grilla documentada para cada modelo. |
| **Validación cruzada** | ✗ | `StratifiedGroupKFold` (k = 5, repetido) por combinación de prendas. Reportar media ± desviación estándar. |
| **Análisis de errores** | Parcial (FP en 2 prendas, 30 casos) | Por subgrupo: plantilla de categorías, n_prendas, rareza del color, combinación vista o no vista. Revisar los FP uno a uno. Calibración. Matriz de confusión por fold. |
| **Contraste de H1** | ✗ | Prueba de no inferioridad con margen Δ fijado de antemano (por ejemplo, 2 puntos de AUC), IC por bootstrap y McNemar pareado. Curvas de aprendizaje con 500, 1 000, 5 000 y todo el conjunto, GFS vs controles. |
| **Integración con BD común** | ✗ | Ver §6, preguntas 3–4. Como mínimo: tabla de predicciones, script o API que escribe, y evidencia (consulta + captura). |
| **Informe Fase 4 avanzada + Fase 5** | ✗ | Estructura propuesta en §4.3 |

### 4.2 Correcciones previas (arrastradas del Hito 2)

1. Decidir el dataset: **regenerar** con las 7 reglas o **depurar** el actual (deduplicar, incluir `categoria`, tratar los 3 prendas). Ver pregunta 2.
2. Normalizar color, patrón, época y estilo (§2.5).
3. Representación invariante al orden + `categoria` (§2.1, §2.6).
4. Volver a correr el baseline (logística + árbol) con el protocolo agrupado: será la nueva línea base.
5. Corregir el informe y el PDF (§3).
6. Reproducibilidad: numerar los notebooks (`01_EDA`, `02_preparacion`, `03_baseline`, `04_modelos_avanzados`, `05_gfs`, `06_integracion`), guardar `outfits_unido.csv`, `nodes.csv` y `edges.csv` en `data/`, y añadir `requirements.txt`.

> **Advertencia sobre regenerar con reglas:** si la etiqueta nueva sale de reglas deterministas aplicadas sobre los mismos atributos que ve el modelo, cualquier árbol o XGBoost llegará otra vez a ~100 %, y H1 seguirá sin poder discriminar. Para evitarlo: (a) añadir ruido de etiqueta controlado, (b) que unas pocas reglas dependan de interacciones que no sean triviales, o (c) etiquetar a mano una muestra pequeña (por ejemplo, 200 outfits) como test externo de verdad. La curva de aprendizaje con pocos datos es donde H1 todavía puede mostrar algo.

### 4.3 Estructura sugerida del informe del Hito 3

1. Resumen de cambios respecto al Hito 2 (qué se corrigió y por qué)
2. Fase 3 (revisada): dataset v2, normalización, representación, protocolo agrupado
3. **Fase 4 avanzada:** RF, XGBoost, red GFS (arquitectura y figura), controles, espacio de hiperparámetros, mejores configuraciones
4. **Fase 5 Evaluación:** CV agrupada (tabla media ± DE), test final, curvas de aprendizaje, no inferioridad (IC y p), análisis de errores, importancia (SHAP para XGBoost), interpretación de la red GFS (actividad de DNp01/TTMn)
5. Integración: arquitectura módulo de IA → BD común, esquema, evidencia
6. Conclusión sobre H1/H0, limitaciones y siguientes pasos (Fase 6)

---

## 5. Orden de trabajo propuesto

1. Cerrar las preguntas de §6 (sobre todo las observaciones del profesor y la BD).
2. Dataset v2 + normalización + `categoria` → `02_preparacion.ipynb`.
3. Protocolo agrupado y baseline v2 → nueva línea base.
4. RF + XGBoost con tuning dentro de la CV.
5. Red GFS + 2 controles (PyTorch, con máscara de adyacencia) + curvas de aprendizaje.
6. Evaluación de no inferioridad + análisis de errores.
7. Integración con la BD (escritura de predicciones) + evidencia.
8. Informe + PPT + guía.

---

## 6. Preguntas abiertas (respondidas el 21/10/2026)

| # | Pregunta | Respuesta |
|---|---|---|
| 1 | Observaciones del profesor | Ver §7.1 |
| 2 | Dataset | Lo generó una IA; las 7 reglas también salieron de pedirle a una IA reglas "de grandes marcas". El equipo cree que no representan cómo se viste cada persona. → Se reemplaza (§7) |
| 3 | Base de datos común | **No es un motor de BD: es el archivo Excel** donde se reúnen los datos → §7.7 |
| 4 | Dashboard | No existe todavía |
| 5 | Archivos faltantes | No los tienen → hay que volver a correr `Connectome.ipynb` (requiere el token de neuPrint) y `Copia de EDA` |
| 6 | Modelo del Hito 3 | Debe quedar entrenado con Random Forest o el algoritmo que mejor se adecue → §7.8 |
| 7 | Formato y fecha | *Pendiente* |

---

## 7. Respuesta a las observaciones del profesor y propuesta de dataset v2

### 7.1 Qué pidió el profesor

1. Generar los datos con **validación de expertos**, no con reglas inventadas.
2. Más **dimensionalidad**: más columnas por prenda (por ejemplo, el largo).
3. Usar **otro dataset** que aporte columnas y mejore la clasificación.
4. Tener presente que un dataset creado por IA puede traer ejemplos poco realistas.

### 7.2 El repositorio de Fashion-MNIST no sirve para este problema

| Lo que necesita el proyecto | Lo que trae Fashion-MNIST |
|---|---|
| Atributos por prenda (color, largo, calce, material…) | Solo imágenes 28×28 en **escala de grises** (no hay color) |
| Outfits armados con etiqueta de compatibilidad | Prendas sueltas; no hay outfits |
| Muchas columnas | Una sola etiqueta: 10 clases (camiseta, pantalón, jersey, vestido, abrigo, sandalia, camisa, zapatilla, bolso, botín) |

Resuelve otro problema (clasificar el tipo de prenda a partir de una imagen). No añade dimensiones a la compatibilidad, y las categorías que aporta ya están en `categoria`. Se puede citar como dataset revisado y descartado, con esta justificación.

### 7.3 Datasets que sí aportan

| Dataset | Qué trae | Para qué sirve aquí |
|---|---|---|
| **Polyvore Outfits** (Han et al., 2017; Vasileva et al., 2018) | ~68 000 outfits **armados por usuarios reales** de la red social Polyvore; cada prenda con categoría semántica, título y descripción | Fuente de **outfits compatibles reales**. Es el benchmark estándar de compatibilidad de outfits. La señal viene de miles de personas distintas, no de reglas, y eso responde a "cada persona se viste a su manera" |
| **Fashion Product Images** (Kaggle, P. Aggarwal) | ~44 000 productos con tabla `styles.csv`: género, categoría, subcategoría, tipo de artículo, color base, temporada, año, uso (casual, formal, deporte…) | Columnas tabulares listas para usar (temporada, ocasión, color base, tipo); también sirve de catálogo alternativo |
| **Fashionpedia** (Jia et al., 2020) | Ontología de atributos de ropa definida con expertos: largo, silueta, cintura, cuello, manga, apertura, textura… | **Justificación experta de las columnas nuevas.** Se cita la ontología aunque no se usen sus imágenes |

> Antes de comprometerse, hay que verificar los enlaces de descarga y la licencia de uso académico de cada uno. Polyvore suele estar en el repositorio de Vasileva (`mvasil/fashion-compatibility`) y en espejos de Kaggle.

### 7.4 Catálogo v2: de 4 a ~14 atributos por prenda

| Columna | Valores | Origen |
|---|---|---|
| `region` | superior / inferior / completo / calzado / exterior | Derivada de la categoría |
| `capa` | base / media / exterior | Derivada |
| `largo` | crop / cintura / cadera / rodilla / midi / maxi / tobillo | Fashionpedia (*length*) |
| `calce` | ajustado / recto / holgado / oversize | Fashionpedia (*silhouette*); se separa del estilo |
| `tiro_cintura` | alta / media / baja (solo inferiores) | Fashionpedia (*waistline*) |
| `manga` | sin / corta / 3-4 / larga | Fashionpedia |
| `cuello` | redondo / V / camisero / alto… | Fashionpedia |
| `material` | algodón / denim / cuero / punto / seda / terciopelo / encaje… | Sale del actual `patron` |
| `patron` | liso / rayas / cuadros / floral / gráfico / animal | Limpio |
| `color_tono`, `color_saturacion`, `color_luminosidad` | numéricos (HSV) | Derivados del nombre del color |
| `es_neutro` | 0/1 | Derivado |
| `formalidad` | 1–5 | Panel de expertos o `usage` |
| `temporada` | verano / invierno / entretiempo / todo el año | Fashion Product (`season`) |
| `ocasion` | casual / trabajo / fiesta / deporte | Fashion Product (`usage`) |
| `estetica` | Y2K, minimalista, vintage… (sustituye a "época") | Limpio |

**Variables por outfit (derivadas):** cobertura completa (superior + inferior, o completo), diferencia máxima de formalidad, contraste de luminosidad, número de colores no neutros, número de estampados, conflicto de capas, coincidencia de temporada.

### 7.5 Etiquetas con validación de expertos (sustituye a las 7 reglas)

1. **Positivos:** outfits reales de Polyvore, traducidos a las columnas del catálogo v2. Los atributos se extraen del título y la descripción por palabras clave (*midi*, *cropped*, *oversized*, *black*…).
2. **Negativos:** se sustituye una prenda del outfit por otra al azar de la **misma región** (es el protocolo estándar de Polyvore). Así el negativo es estructuralmente plausible, y el modelo tiene que aprender algo más que "camiseta + vestido no va".
3. **Panel de expertos:** 3–5 evaluadores (estudiantes de diseño de moda, estilistas, asesores de tienda) puntúan una muestra de **300–500 outfits** de 1 a 5, con una guía de evaluación escrita.
4. **Acuerdo entre expertos:** Fleiss κ o α de Krippendorff. Si el acuerdo es bajo, eso cuantifica la subjetividad ("cada persona se viste a su manera"), y eso también es un resultado.
5. **Etiqueta y score:** la etiqueta binaria es la mayoría; el **score es la media normalizada de las puntuaciones**. Con esto la salida DLMn predice algo real y desaparece la fuga del score actual.
6. **Uso en el modelo:** Polyvore se usa para entrenar; los outfits evaluados por expertos quedan como **test externo**, que nunca entra en el entrenamiento. Esto reemplaza a los 30 casos.

Ya no se escriben reglas a mano. Si alguna regla se conserva, solo es para generar negativos difíciles, y cada una debe tener un % de acuerdo del panel.

**Alternativa si no se consigue Polyvore:** usar el catálogo propio de 500 prendas, completar a mano las columnas v2 (hay una `descripcion` por prenda) y hacer que el panel etiquete 800–1 000 outfits candidatos. Es más chico, pero la validación es 100 % experta.

### 7.6 Cómo encaja con el circuito de la mosca

Con 4 atributos no había forma de darle sentido a las **dos** poblaciones de entrada. Con el catálogo v2 sí la hay:

| Circuito | Qué codifica en la mosca | En el outfit |
|---|---|---|
| **LPLC2** | Tamaño angular: *cómo es* el estímulo | **Canal de estructura:** región, capa, largo, calce, cobertura (la forma del outfit) |
| **LC4** | Velocidad angular: *cuánto cambia* | **Canal de contraste:** diferencias entre prendas en color, patrón, material, formalidad y temporada |
| **DNp01** | Integra los dos canales y decide si escapar | Integra estructura y contraste en una decisión |
| Umbral de DNp01 | La decisión de escape depende del contexto | **Contexto o estilo personal:** sesgo aprendible por `ocasion` (o por evaluador) |
| **TTMn** | Salto rápido | ¿Combina? (binaria) |
| **PSI → DLMn** | Respuesta gradual | Score = media de los expertos |

Esto vuelve **contrastable** la analogía: se compara la red GFS con los canales bien asignados contra la misma red con los canales intercambiados o asignados al azar. Si la asignación con sentido no gana, la estructura no aporta (H0).

### 7.7 Integración: el Excel como base de datos común

Libro `BD_modelo_fly.xlsx`:

| Hoja | Contenido | Quién escribe |
|---|---|---|
| `catalogo` | Prendas con las columnas v2 | Preparación |
| `outfits` | outfit_id, prendas, fuente (polyvore / negativo / panel) | Preparación |
| `evaluaciones` | outfit_id, evaluador, puntuación, fecha | Panel de expertos |
| `predicciones` | outfit_id, modelo, versión, probabilidad, predicción, score_predicho, fold, fecha | **Módulo de IA** (`06_integracion.ipynb`) |
| `metricas` | modelo, fold, accuracy, F1, AUC… | Módulo de IA |

La evidencia para el informe: el notebook lee `outfits` y escribe en `predicciones` (pandas + openpyxl), con capturas antes y después, conteo de filas y marca de tiempo. Más adelante el dashboard puede leer de este mismo libro.

### 7.8 Modelos del Hito 3

- **Random Forest y XGBoost** (y LightGBM, opcional), con ajuste de hiperparámetros dentro de `StratifiedGroupKFold`. El "mejor algoritmo" se elige por CV; en datos tabulares suele ser XGBoost o LightGBM.
- **Red GFS** (PyTorch, con la matriz de adyacencia como máscara), más los dos controles (red barajada y MLP). Un Random Forest no puede usar el conectoma: RF/XGBoost marcan **el listón** que la red GFS debe alcanzar para no ser inferior.
- La red GFS necesita `nodes.csv` y `edges.csv` → volver a correr `Connectome.ipynb` (token de neuPrint).

### 7.9 Plan revisado

1. **Ya:** convocar al panel de expertos (es lo más lento) y redactar la guía de evaluación.
2. Descargar Polyvore y Fashion Product Images; definir la ontología v2 citando Fashionpedia.
3. Extraer atributos → hojas `catalogo` y `outfits` del Excel.
4. Generar negativos; seleccionar la muestra para el panel.
5. Volver a correr `Connectome.ipynb` y guardar `nodes.csv` y `edges.csv` en `data/`.
6. Baseline v2 + RF + XGBoost con CV agrupada.
7. Red GFS + controles + curvas de aprendizaje.
8. Evaluación en el test de expertos, no inferioridad y análisis de errores.
9. Escribir predicciones en el Excel (integración).
10. Informe Fases 4–5 + PPT + guía.

> El plan de §7.9 era para la opción Polyvore. Como se eligió el catálogo propio, el plan vigente es el de §8.

---

## 8. ~~Plan: catálogo propio de 500 prendas + panel de expertos~~ (reemplazado por §12 el 22/10/2026)

> ⚠️ **Reemplazado.** El profesor descartó el panel de expertos. El plan vigente está en **§12**.

### 8.1 Por qué hace falta un panel de 3 a 5 evaluadores

- **Es lo que pidió el profesor:** que la etiqueta tenga validación de expertos y no salga de reglas inventadas.
- **Un solo evaluador = un solo gusto.** Es justo la objeción del equipo ("cada persona se viste distinto"). Con varios, la etiqueta es un **consenso** y no la opinión de una persona.
- **Permite medir la subjetividad.** Con 2 o más evaluadores se calcula el acuerdo (Fleiss κ o α de Krippendorff). Un κ bajo es un hallazgo: dice qué tan subjetiva es la tarea y cuál es el techo realista del modelo.
- **Número impar (3 o 5):** así la mayoría nunca empata.
- **Da un score real:** el promedio de las puntuaciones de 1 a 5 se normaliza a 0–1. Con eso, la rama DLMn predice algo con significado.
- **Carga de trabajo:** con 1 000 outfits y 5 evaluadores, si cada outfit lo puntúan 3, son ~600 outfits por persona. A unos 10 s cada uno, salen 1,5–2 h por evaluador, repartidas en varias sesiones.
- **Perfil:** personas con criterio de moda verificable (estudiantes de diseño de modas, estilistas, asesores de tienda, personal shoppers). Se documentan el perfil y la experiencia de cada uno.

### 8.2 Flujo

```
 FASE 3 · PREPARACIÓN DE DATOS
 ┌──────────────────────────────────────────────────────────────────────┐
 │ 1. Catálogo v2 (500 prendas)                                         │
 │    limpiar color/patrón/época/estilo + agregar largo, calce, manga,  │
 │    cuello, material, formalidad, temporada, ocasión, región, capa    │
 │    (ontología basada en Fashionpedia)        → hoja `catalogo`       │
 │                              │                                       │
 │ 2. Outfits candidatos (~1 000, todos distintos)                      │
 │    plantillas válidas e inválidas por región, 2 y 3 prendas,         │
 │    muestreo que cubra todos los atributos      → hoja `outfits`      │
 │                              │                                       │
 │ 3. Panel de expertos (3–5 personas, 3 votos por outfit, escala 1–5)  │
 │    formulario o la hoja del Excel           → hoja `evaluaciones`    │
 │                              │                                       │
 │ 4. Consolidación                                                     │
 │    etiqueta = mayoría · score = media · Fleiss κ                     │
 │    se marcan los outfits con mucho desacuerdo                        │
 │                              │                                       │
 │ 5. Variables del modelo                                              │
 │    por prenda + por outfit (contrastes), invariantes al orden        │
 └──────────────────────────────┼───────────────────────────────────────┘
                                │      ┌────────────────────────────────┐
                                │      │ 0. Conectoma (en paralelo)     │
                                │      │ volver a correr Connectome     │
                                │      │ → nodes.csv, edges.csv         │
                                │      └───────────────┬────────────────┘
 FASE 4 · MODELADO AVANZADO     ▼                      ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │ 6. Baseline v2 (logística, árbol) · Random Forest · XGBoost          │
 │    ajuste de hiperparámetros con CV anidada                          │
 │    Red GFS (LPLC2 = estructura, LC4 = contraste, sesgo por ocasión)  │
 │    + controles: GFS con aristas barajadas · MLP del mismo tamaño     │
 └──────────────────────────────┬───────────────────────────────────────┘
 FASE 5 · EVALUACIÓN            ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │ 7. CV estratificada repetida (5×5) · test reservado del 20 %         │
 │    curvas de aprendizaje (100 / 250 / 500 / todo)                    │
 │    no inferioridad GFS vs mejor modelo (IC bootstrap, McNemar)       │
 │    análisis de errores: por plantilla, atributo, outfits con         │
 │    desacuerdo entre expertos · importancia (SHAP)                    │
 └──────────────────────────────┬───────────────────────────────────────┘
 INTEGRACIÓN                    ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │ 8. El notebook escribe en BD_modelo_fly.xlsx                         │
 │    → hojas `predicciones` y `metricas` + capturas como evidencia     │
 └──────────────────────────────┬───────────────────────────────────────┘
                                ▼
 9. Informe Fases 4–5 · PPT · guía
```

### 8.3 Notebooks

| Notebook | Pasos | Salida |
|---|---|---|
| `00_conectoma.ipynb` | 0 | `data/nodes.csv`, `data/edges.csv` |
| `01_catalogo_v2.ipynb` | 1 | hoja `catalogo` |
| `02_outfits_candidatos.ipynb` | 2 | hoja `outfits` + material para el panel |
| `03_consolidacion_expertos.ipynb` | 4 | etiquetas, score y κ |
| `04_modelos.ipynb` | 5–6 | modelos ajustados |
| `05_evaluacion.ipynb` | 7 | métricas, figuras, análisis de errores |
| `06_integracion.ipynb` | 8 | escritura en el Excel |

### 8.4 Riesgos y decisiones pendientes

- **El catálogo también lo generó una IA**, así que sus atributos pueden ser incoherentes (por ejemplo, una camiseta de "patrón Cuero"). En el paso 1 hay que revisar las 500 prendas, y conviene que un experto revise una muestra.
- **¿Qué ven los evaluadores?** Solo con texto (descripción + atributos) es difícil juzgar un outfit. Lo ideal es poner una imagen de referencia por prenda. Hay que decidirlo antes del paso 3.
- **Dataset pequeño (~1 000):** es suficiente para RF/XGBoost con CV y es justo el escenario de pocos datos donde H1 puede mostrar algo. Hay que explicarlo así en el informe.
- **"Otro dataset":** con esta opción, el otro dataset es Fashionpedia (su ontología define las columnas nuevas), y opcionalmente Fashion Product Images para mapear temporada y ocasión por tipo de prenda. **Conviene confirmar con el profesor que eso cuenta.**

### 8.5 Versión simple, sin imágenes (decidida el 21/10/2026)

- Los evaluadores ven **fichas de texto**, no imágenes. Por ejemplo:
  > **Outfit 037** · ① Camiseta blanca, manga corta, algodón, ajustada, casual · ② Jean azul, largo tobillo, corte recto · *¿Combina?* 1 2 3 4 5
- **600 outfits**, cada uno calificado por **los 3 evaluadores** (≈ 1,5 h por persona, en 2 o 3 sesiones).
- Recolección con **Google Forms** (gratis) → exportar a la hoja `evaluaciones` del Excel.

---

## 9. El ecosistema explicado como producto

### 9.1 Flujo del usuario final (visión de la app; no se construye en el Hito 3)

1. **Mi clóset:** el usuario registra sus prendas eligiendo de listas (categoría, color, largo, calce, material, ocasión). No necesita foto.
2. **"¿Combina esto?":** elige 2 o 3 prendas → la app responde **Sí/No + porcentaje** (por ejemplo, "Combina · 87 %") y una razón breve.
3. **"¿Qué me pongo?":** elige una ocasión (trabajo, casual, fiesta) → la app prueba las combinaciones de su clóset y le muestra las 3 mejores.
4. **Opinión:** 👍 / 👎 → se guarda en el Excel (hoja `feedback`) para reentrenar el modelo y, más adelante, personalizarlo.

ODS 12: se combina lo que la persona ya tiene, en lugar de comprar.

### 9.2 Qué pasa por dentro cuando el usuario pregunta

Prendas elegidas → se traducen a números → **modelo** → resultado → se guarda en `predicciones`.
En la red de la mosca: **LPLC2** recibe la estructura del outfit (largo, calce, capas); **LC4** recibe el contraste entre prendas (color, material, formalidad); **DNp01** integra; **TTMn** = Sí/No; **DLMn** = porcentaje.

### 9.3 Qué se entrega en cada etapa

| Etapa | Qué existe |
|---|---|
| Hito 3 | Catálogo v2, outfits calificados por expertos, modelos entrenados y evaluados, predicciones escritas en el Excel |
| Fase 6 / futuro | App o dashboard que usa el modelo guardado (pasos 9.1) |

---

## 10. ~~Planes alternativos para el etiquetado~~ (reemplazado por §12)

| Plan | Quién etiqueta | Cómo | Qué se dice en el informe |
|---|---|---|---|
| **A** | 3 expertos | Los 600 outfits completos | "Etiqueta validada por expertos" (κ entre expertos) |
| **B (recomendado si no hay expertos)** | **Encuesta abierta** + 1 experto | Google Form en redes. Cada persona califica 15 outfits al azar y responde un perfil corto (edad, interés en moda 1–5, si trabaja en moda). Meta: ≥ 5 votos por outfit (~200 respuestas). Un solo experto revisa una muestra de 100 | "Etiqueta por consenso de la multitud, contrastada con un experto" (acuerdo multitud–experto). Además, captura que "cada persona se viste distinto" |
| **C** | Literatura experta | Solo reglas tomadas de libros o guías de asesoría de imagen y de teoría del color, **con cita por regla**; un compañero aplica las reglas a mano en una muestra para verificarlas | "Reglas de fuentes expertas publicadas". Es lo más débil: avisar al profesor |

No se recomienda usar una IA como evaluador: es justo lo que el profesor objetó.

En todos los planes, la ficha pregunta además **"¿para qué ocasión lo usarías?"** (casual / trabajo / fiesta / deporte, con selección múltiple). Así el modelo aprende la compatibilidad **según la ocasión**.

## 11. Recomendador por ocasión e historial (visión de la app; la arquitectura vigente está en §12)

1. **Ocasión:** el usuario elige trabajo, casual, fiesta o deporte.
2. **Generar:** se arman todas las combinaciones válidas de 3 prendas de su clóset (arriba + abajo + calzado, o vestido + calzado + exterior).
3. **Puntuar:** el modelo da a cada combinación un % de "combina **para esa ocasión**".
4. **Personalizar con el historial:**
   - *Gusto:* perfil de lo que eligió o marcó con 👍 (colores, estilos, calces). Puntaje final = 0.7 × modelo + 0.3 × gusto.
   - *Rotación (ODS 12):* se baja el puntaje de lo que usó hace poco y se sube el de las prendas olvidadas.
   - *Usuario nuevo:* solo el modelo, hasta que tenga historial.
5. **Mostrar 3 opciones distintas** (que no repitan la misma prenda) → el usuario elige una → se guarda en la hoja `historial` (usuario, fecha, ocasión, outfit, elegido, 👍/👎).

**Para el Hito 3:** la ocasión entra al modelo, y una función `recomendar(closet, ocasion, historial)` en `06_integracion.ipynb` lee un clóset de ejemplo del Excel y escribe las 3 recomendaciones. Eso sirve como demostración y como evidencia de integración. La app real queda para la Fase 6.

---

## 12. Plan vigente para el Hito 3: recomendador DeepFM → conectoma GFS (decidido el 22/10/2026)

### 12.1 Decisiones cerradas

| Tema | Decisión |
|---|---|
| Datos de outfits | **Polyvore (Han et al., 2017; repo `xthan/polyvore-dataset`)**, solo los JSON de metadatos, sin imágenes. Ese dataset **no trae ID de usuario** (solo contadores `views` y `likes`), así que los usuarios se **simulan** sobre outfits reales. **Se combina con el catálogo propio de 500 prendas** (§12.12) |
| Tamaño de outfit | **Variable:** núcleo (arriba + abajo, o vestido) + calzado + accesorios opcionales. No se recorta a 3 prendas |
| Atributos | Se extraen del texto (`name`, `desc`): **color, patrón, estilo, época, largo**, más **calce** (lo necesita E1) |
| Negativos | Se reemplaza una prenda por otra **del mismo slot** (zapato por zapato), con el **mismo número de ítems** que el positivo. Así no reaparece el atajo `n_prendas` ni el de categoría |
| Etiquetas | Las tres de la tabla 12.4: DeepFM = gusto del usuario; TTMn = real o falso; DLMn = reglas cumplidas (0–7) |
| Pesos del conectoma | **Opción A** (backpropagation con máscara y signo por neurotransmisor) como modelo principal; **Opción B** (pesos fijos de neuPrint, solo se entrena la salida) como experimento secundario en anexos |
| Experimentos | Los **6** de §12.6 |
| Métrica principal | Ranking por usuario: **Recall@K y NDCG@K**, medidos contra lo que el usuario **aceptó en su test**, nunca contra las reglas |

### 12.2 Pipeline de datos (orden estricto)

```
0. Descargar JSON de Polyvore ─ train/valid/test_no_dup.json, category_id.txt,
                                 fashion-compatibility-prediction.txt, fill_in_blank_test.json
1. Normalizar ítems ─ categoryid → slot (arriba, abajo, vestido, exterior, calzado,
                       bolso, accesorio, joyería); deduplicar productos repetidos (misma imagen o nombre)
2. Filtrar outfits válidos ─ (arriba + abajo | vestido) + calzado; accesorios opcionales
3. Texto → atributos ─ diccionarios EN de palabras clave → color, patrón, estilo, época, largo, calce
4. Unicidad ─ frozenset(item_ids) por outfit; se elimina cualquier duplicado ANTES de partir
5. Negativos ─ reemplazo dentro del mismo slot, misma longitud (1:1 con positivos)
6. Score de reglas ─ 7 reglas sobre cada outfit (positivo y negativo) → 0–7
7. Usuarios simulados ─ clóset, perfil, historial con ruido (§12.3)
8. Partición ─ por outfit (fase 2) y por usuario en el tiempo (fase 1), sin fuga (§12.5)
9. Excel BD común ─ todas las hojas (§12.8)
```

**Control de calidad del paso 3 (validación humana barata):** el equipo revisa a mano una muestra de 200 ítems y compara su lectura con lo que extrajo el diccionario. Se reporta la **precisión por columna** y el % de "desconocido". Esto reemplaza al panel de expertos y responde la crítica de "datos inventados".

**Cuidados por columna:**
- **Color y patrón:** salen bien del texto ("black", "floral", "striped").
- **Largo:** aparece seguido ("mini", "midi", "maxi", "cropped", "ankle").
- **Estilo:** sale a medias ("boho", "preppy", "sporty"). Se puede apoyar en la marca o en la descripción del set.
- **Época:** es la más difícil. Se busca "vintage", "retro", "70s", "90s", "y2k", etc. Si no hay pista se pone **"contemporáneo"**, y eso se declara como supuesto en el informe.
- **Calce:** "oversized", "slim", "skinny", "relaxed", "fitted".
- **Ojo:** Polyvore es mayoritariamente ropa de mujer. La variable `género` del usuario tendrá poca variación; hay que decirlo como limitación.

### 12.3 Usuarios simulados (solución a la circularidad)

Para cada usuario *u* (propuesta: 300 usuarios):

1. **Perfil:** edad, género, estilo favorito, clima de su ubicación y un **vector de preferencia** `w_u` de 7 pesos, uno por regla. Ejemplos:
   - Usuario vintage al que no le importa C1: peso bajo en C1, peso alto en estilo vintage.
   - Usuario minimalista: peso alto en C1/C2, peso negativo para prendas oversize.
2. **Clóset:** 40–80 ítems tomados de outfits reales de Polyvore, con sesgo hacia su estilo favorito.
3. **Historial:** unas 50 interacciones con fecha. En cada una se le muestra un outfit armado con su clóset y se calcula:
   `p(acepta) = sigmoide( a · (w_u · reglas) + b · coincide_estilo + c · adecuado_al_clima )`
4. **Ruido:** con probabilidad del 5–10 % la decisión se invierte (compra impulsiva o tendencia).
5. Se guardan los parámetros reales de cada usuario. Así se puede medir **si el DeepFM recupera los gustos** que se programaron (un análisis de error muy convincente).

> **Límite que hay que declarar:** el gusto personal sigue siendo simulado. Lo que sí es real es qué combinan los humanos (Polyvore), y eso entra por TTMn.

### 12.4 Qué aprende cada etapa

| Etapa | Salida | Etiqueta | Origen |
|---|---|---|---|
| Fase 1 · DeepFM (filtro personal) | p(le gusta a *u*) | 1/0 según perfil simulado + ruido | §12.3 |
| Fase 2 · TTMn (filtro real) | p(outfit real) | 1 = outfit real de Polyvore / 0 = negativo del mismo slot | Polyvore |
| Fase 2 · DLMn (armonía) | 0–7 | Nº de reglas **no violadas** (si una regla no aplica, p. ej. P1 sin estampados, cuenta como cumplida) | 7 reglas (§12.9) |

**Ranking final** (falta fijarlo y aplicarlo igual en los 6 experimentos):
- El DeepFM elige el **top 20–30** del clóset.
- La fase 2 reordena con `score = α · p_DeepFM + (1 − α) · fase2`, donde `fase2` combina TTMn y DLMn.
- `α` se ajusta en **validación** (por usuario), no en test.
- En el experimento 1 (DeepFM solo), α = 1.

### 12.5 Partición y validación cruzada

**Proporción: 70 / 15 / 15 (train / validación / test), decidida el 01/11/2026.**

- **Fase 2 (TTMn/DLMn):** partición 70/15/15 por outfit con la clave `frozenset`. Un positivo y sus negativos van siempre a la misma partición. Para afinar hiperparámetros: `StratifiedGroupKFold` (5 folds) dentro de train.
- **Fase 1 (DeepFM):** partición temporal por usuario con la misma proporción: de unas 50 interacciones, las primeras 35 a train, las 7 siguientes a validación y las últimas 8 a test.
- **Regla extra:** un outfit que está en el test de algún usuario no puede aparecer en el train de ningún otro.
- **Evaluación extra de la fase 2:** accuracy en la tarea **fill-in-the-blank** oficial de Polyvore (`fill_in_blank_test.json`, 4 opciones). Es un benchmark externo comparable con la literatura.

### 12.6 Cuadro de experimentos

| N.º | Arquitectura | Si el 4 le gana, demuestra que… |
|---|---|---|
| 1 | DeepFM solo | La segunda fase aporta valor |
| 2 | DeepFM + XGBoost (tuning con CV) | Supera un clasificador convencional (rúbrica) |
| 3 | DeepFM + Random Forest (tuning con CV) | Ídem (rúbrica) |
| **4** | **DeepFM + GFS, Opción A (máscara + signo)** | **Propuesta (H1)** |
| 5 | DeepFM + MLP con el **mismo nº de parámetros entrenables** que el 4 | Gana la estructura, no el tamaño |
| 6 | DeepFM + GFS con conexiones **mezcladas al azar** (mismo nº de aristas y mismos grados) | Importa la conectividad específica de la mosca |
| Anexo | DeepFM + GFS, Opción B (pesos fijos de neuPrint) | ¿La biología sin entrenar ya sirve? |

**Métricas:** Recall@5, NDCG@5, NDCG@10 y HitRate@K por usuario. Para la fase 2 sola: AUC de TTMn, MAE de DLMn y accuracy en FITB.

**Rigor:**
- Las redes (4, 5, 6) se corren con **≥ 5 semillas** y se reporta media ± desviación.
- El 6 se corre con varias mezclas distintas.
- Intervalos de confianza **bootstrap por usuario**.
- Prueba pareada por usuario (Wilcoxon) para 4 vs 5 y 4 vs 6.

**Hipótesis reformuladas:**
- **H1:** en el ranking final, el DeepFM + GFS (Opción A) obtiene un NDCG@K igual o mayor que los controles de igual tamaño (5) y de conectividad aleatoria (6).
- **H0:** no hay diferencia, o el GFS es peor.

### 12.7 Detalles del conectoma

- **Entrada:**
  - Canal de **contraste → LC4 (126):** diferencias entre prendas en color, patrón, época y estilo.
  - Canal de **estructura → LPLC2 (185):** slots presentes, largo, calce y número de accesorios.
  - Una capa lineal entrenable proyecta cada canal a su población. Es igual para los experimentos 4, 5 y 6.
- **Salidas:** TTMn → sigmoide (pérdida BCE). DLMn → regresión del score/7 (pérdida MSE). Pérdida total = BCE + λ · MSE.
- **Opción A:** `W = signo ⊙ softplus(θ) ⊙ máscara`. Así PyTorch aprende la magnitud, pero no puede crear conexiones ni cambiar el signo.
- **Signo por neurotransmisor:** neuPrint (MaleCNS) trae el neurotransmisor predicho por neurona.
  - Acetilcolina → +; GABA → −.
  - **Glutamato → −** es la convención habitual en la mosca (receptor GluCl), pero no se cumple siempre. Se declara como supuesto.
- **Opción B:** `W = signo · sinapsis / escala`, congelado; solo se entrena la capa de salida.
- **Limitación conocida:** la sinapsis Giant Fiber → TTMn es en buena parte **eléctrica** (gap junctions) y no aparece en un conectoma de sinapsis químicas. Conviene mencionarlo.
- **Pendiente:** volver a correr `Connectome.ipynb` con el token y exportar también el neurotransmisor (`nodes.csv` y `edges.csv` faltan en la carpeta).

### 12.8 Excel "BD común" (evidencia de integración)

`BD_modelo_fly.xlsx`, con estas hojas:

| Hoja | Contenido |
|---|---|
| `items` | item_id, **origen** (polyvore / propio), slot, color, patrón, material, estilo, época, largo, calce, texto original, **calidad** (ok / corregido / excluido) |
| `outfits` | outfit_id, item_ids, n_items, real (1/0), score_reglas, partición |
| `usuarios` | user_id, edad, género, estilo favorito, clima, vector de preferencia |
| `closets` | user_id, item_id |
| `historial` | user_id, fecha, outfit_id, aceptado, partición |
| `candidatos` | user_id, outfit_id, p_DeepFM (top 20–30) |
| `predicciones` | user_id, outfit_id, experimento, p_TTMn, DLMn, score final, rango |
| `metricas` | experimento, semilla, Recall@5, NDCG@5, NDCG@10, AUC, MAE, FITB |

La función `recomendar(user_id)` lee `closets` + `historial`, pasa por las dos fases y escribe en `candidatos` y `predicciones`.

### 12.9 Reglas con fuentes (tabla nueva para la sección 7 del informe)

| Regla | Criterio | Fuente propuesta |
|---|---|---|
| C1 | Máximo dos colores no neutros y un solo acento fuerte | Dior (1954), *The Little Dictionary of Fashion*; Itten (1961), *The Art of Color* |
| C2 | Un neutro combina con cualquier color | Itten (1961); Flusser (2002), *Dressing the Man* |
| P1 | Dos estampados distintos son elegibles si varían en escala o comparten un color de fondo | Flusser (2002); MasterClass, *How to Mix Prints and Patterns* |
| P2 | No repetir estampados de la misma escala y familia | Flusser (2002) |
| P3 | Una prenda lisa funciona como puente neutro | MasterClass (artículo citado en P1) |
| E1 | Un solo elemento con volumen (oversize), compensado con líneas rectas o ajustadas | Faerm (2010), *Fashion Design Course* |
| Ep1 | No replicar una sola década de pies a cabeza; mezclar épocas | Nina García (2007), *The Little Black Book of Style*; Steele (historia de la moda) |

**Antes de entregar, verificar cada cita:**
1. **Leer la página que se cita** y anotar el número de página o la entrada. Por ejemplo, ubicar la entrada de *The Little Dictionary of Fashion* donde Dior habla de accesorios y simplicidad.
2. **MasterClass:** es un artículo web. Va con su URL y **fecha de consulta**, no "(2026)" como año de publicación, salvo que el artículo diga esa fecha.
3. **Flusser** escribe sobre ropa de hombre. Sirve para los principios de escala y color, pero la frase "explica matemáticamente" exagera: mejor "describe".
4. **Steele:** citar un libro concreto (por ejemplo, uno de sus libros de historia de la moda), no "Valerie Steele" en general.
5. Se eliminan *The Dandy Liar*, *Abby on the Internet*, *She's Not So Basic*, *Klodsy*, la "guía de calces de H&M" y la "paleta de Chanel".

### 12.10 Notebooks

| Notebook | Qué hace |
|---|---|
| `00_polyvore_descarga.ipynb` | Descarga JSON, slots, filtro, deduplicación |
| `01_atributos.ipynb` | Texto → 6 atributos + muestra de 200 para validación manual |
| `01b_catalogo_propio.ipynb` | Catálogo de 500 → esquema común, limpieza, columna `calidad` (§12.12) |
| `02_reglas_y_negativos.ipynb` | Negativos del mismo slot, score 0–7, partición por outfit |
| `03_usuarios_simulados.ipynb` | Perfiles, clósets, historiales con ruido, partición temporal |
| `04_deepfm.ipynb` | Fase 1 + tuning + Recall@K del filtro |
| `05_fase2_modelos.ipynb` | XGBoost, RF (tuning con CV), MLP, GFS A/B, GFS aleatorio |
| `06_evaluacion.ipynb` | 6 experimentos, semillas, bootstrap, Wilcoxon, análisis de errores |
| `07_integracion_excel.ipynb` | `BD_modelo_fly.xlsx` + `recomendar(user_id)` |

### 12.11 Riesgos

| Riesgo | Mitigación |
|---|---|
| Pocos outfits válidos tras el filtro | Medirlo en el notebook 00; si son pocos, aceptar exterior como pieza de núcleo |
| Época casi siempre "contemporáneo" | Reportar cobertura; Ep1 pierde fuerza y se dice |
| Negativos demasiado fáciles | Además de los aleatorios del mismo slot, crear negativos "difíciles" (mismo slot y mismo estilo) |
| El GFS no gana | Es un resultado válido (H0); se reporta con honestidad y con los controles |
| Tiempo | Prioridad: 00 → 01 → 02 → 05 (fase 2 sola ya es demostrable) → 03 → 04 → 06 → 07 |

### 12.12 Combinación Polyvore + catálogo propio de 500 prendas (decidido el 29/10/2026)

**Idea central:** cada fuente hace lo que sabe hacer.

| Fuente | Qué aporta | Qué **no** aporta |
|---|---|---|
| Polyvore | Outfits reales armados por personas → verdad de TTMn y negativos | Usuarios (no trae ID) |
| Catálogo propio (500) | Prendas en español con el esquema del proyecto; continuidad con el Hito 2; escenario "clóset del usuario" | Etiquetas de compatibilidad: los 100 000 outfits del Hito 2 **se descartan** como verdad (fuga §2.4, 3 prendas siempre compatibles §2.2) |

**Problemas del catálogo, medidos el 29/10/2026 (hay que declararlos):**
- El `estilo` de la columna coincide con el "Estilo …" de la `descripcion` solo en **66 / 500** prendas (13 %, lo mismo que el azar entre 8 valores).
- **38 de 88** camisetas son de "cuero", "denim" o "terciopelo"; los patrones se reparten casi uniformes en todas las categorías (57–72 prendas cada uno).
- No hay accesorios ni bolsos, solo 33 calzados y ninguna columna de largo.
- Conclusión: los atributos parecen asignados al azar por la IA. Por eso el catálogo **no puede ser fuente de verdad**, solo prendas a recomendar.

**Pasos (`01b_catalogo_propio.ipynb`):**
1. **Esquema común** con Polyvore: slot, color (familia + tono), patrón, material, estilo, calce, época, largo.
   - `patron` se separa en patrón (Liso, Floral, Gráfico, Holográfico) y material (Cuero, Denim, Encaje, Terciopelo).
   - `estilo` se separa en estilo (Casual, Formal, Deportivo, Athleisure, Vintage) y calce (Oversize, Ajustado, Recto).
   - `epoca`: las décadas se quedan; Tumblr → 2010s; Retro y Vintage → `vintage_generico` (pista retro sin década; no cuenta como década en Ep1). El mismo valor se usará para "vintage"/"retro" en Polyvore.
   - `color`: se unifican sinónimos (§2.5) y se traducen al mismo vocabulario que Polyvore.
   - `largo`: por categoría (Short/minifalda = corto…) o "desconocido".
2. **Conflicto columna vs descripción (decidido el 31/10/2026):** la columna y la descripción se reparten entre estilo y calce (229 prendas se complementan, 66 coinciden). En las **205 contradicciones** (los dos son estilo, o los dos son calce, y difieren) **manda la columna** y la prenda queda con `conflicto_estilo = 1` para el análisis de errores.
3. **Revisión manual** de las 500 (es barato): columna `calidad` = ok / corregido / excluido. Se excluyen las imposibles (p. ej., calzado de encaje holográfico) y se reporta cuántas quedan.
4. **Validación cruzada de vocabulario:** comprobar que cada valor del catálogo existe en Polyvore. Lo que no exista no lo podrá aprender el modelo.

**Cómo entra en el pipeline:**
- **Fase 2 (TTMn/DLMn):** se entrena **solo con Polyvore**. Las prendas propias no tienen verdad de compatibilidad.
- **Clósets simulados (§12.3):** mezcla de prendas Polyvore y propias, **70 % Polyvore / 30 % propias (confirmado el 01/11/2026)**. Es la composición del clóset, no la partición de los datos (esa es 70/15/15, §12.5). El historial se simula igual para ambas.
- **Prueba de transferencia (nueva evaluación):** usuarios cuyo clóset es **100 % catálogo propio**. Se compara NDCG@K entre clósets Polyvore, mixtos y propios. Si cae mucho en los propios, es un análisis de errores por **cambio de dominio** (muy buen material para el informe).
- **DLMn:** las 7 reglas sí se pueden calcular sobre prendas propias, así que el score de armonía se reporta también ahí.
- **Demo `recomendar(user_id)`:** se muestra con un usuario de clóset 100 % propio, que es el caso de la app.

**Resultado de la etapa 1b (31/10/2026, `notebooks/hito3/01b_catalogo_propio.ipynb`):**
- 69 colores → 15 tonos + familia (neutro 297, fuerte 114, suave 71, desconocido 18). 20 prendas tienen un "color" que no es color.
- Patrón: 312 lisas (incluye las 240 que en el crudo tenían un material), 67 holográficas, 63 florales, 58 gráficas.
- Desconocidos: estilo 14 %, calce 41 % (sin contar el calzado, que no aplica), largo 70 %.
- **153 prendas marcadas `revisar`** (camiseta de cuero/denim/terciopelo 38, deportivo/athleisure de cuero/encaje/terciopelo 65, formal con patrón gráfico u holográfico 24, calzado con talla de ropa 22, color ilegible 20). Se revisan a mano en `data/revision/catalogo_propio_revision.xlsx`.
- La talla del crudo también parece aleatoria (calzado con talla XL, camisetas con talla 36). No entra al modelo.

**Riesgos de la combinación:**
| Riesgo | Mitigación |
|---|---|
| Polyvore es casi todo ropa de mujer y el catálogo es unisex | Declararlo; la prueba de transferencia lo medirá |
| Pocas prendas propias de calzado (33) | Completar los clósets propios con calzado de Polyvore, o reportar outfits sin calzado como limitación |
| La revisión manual introduce criterio del equipo | Escribir la regla de exclusión antes de revisar y reportar el % excluido |
