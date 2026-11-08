# Diccionario de datos · `data/BD_modelo_fly.xlsx`

Generado por `notebooks/hito3/08b_bd_comun.ipynb`. Las columnas marcadas OCULTO son parámetros de la simulación: el modelo no las ve; sirven para evaluar.

## `items`

Prendas con sus atributos (Polyvore + catálogo propio). Escribe: Preparación (etapas 2–4). Filas: 65 866.

| Columna | Tipo | Descripción |
|---|---|---|
| `item_id` | str | ID de la prenda: 'pv_' + ID de Polyvore, o 'P' + número del catálogo propio |
| `origen` | str | items: polyvore / propio · closets: de dónde viene la prenda · candidatos y predicciones: historial / nuevo (evaluación) o recomendar (escrito por recomendar()) |
| `particion` | str | train / valid / test (en historial y candidatos es temporal por usuario; en outfits e items es por outfit de Polyvore) |
| `name` | str | Texto original de la prenda (nombre en Polyvore o descripción del catálogo propio) |
| `slot` | str | Lugar en el outfit: arriba, abajo, vestido, exterior, calzado, bolso, accesorio, joyeria |
| `tono` | str | Tono del color (claro, medio, oscuro…) |
| `familia_color` | str | Familia de color (neutro, cálido, frío…) |
| `patron` | str | Patrón (liso, rayas, cuadros, floral…) |
| `material` | str | Material principal |
| `estilo` | str | Estilo (clasico, minimalista, vintage, atrevido, deportivo…) |
| `calce` | str | Calce (ajustado, regular, oversize) |
| `epoca` | str | Década o época que evoca |
| `largo` | str | Largo de la prenda (corto, medio, largo) |

## `outfits`

Outfits de Polyvore (reales y negativos) con las 7 reglas: datos de la fase 2. Escribe: Preparación (etapa 4). Filas: 45 036.

| Columna | Tipo | Descripción |
|---|---|---|
| `outfit_id` | str | ID del outfit (Polyvore: set_id y sufijo del negativo; usuarios: U###_O## historial, U###_V/T### candidatos, U###_R<fecha>_### recomendar()) |
| `tipo` | str | real (outfit armado por una persona en Polyvore) o el tipo de negativo (aleatorio, dificil) |
| `real` | int64 | 1 = outfit real de Polyvore, 0 = negativo. Etiqueta de TTMn (fase 2) |
| `set_id_origen` | int64 | Outfit real del que sale el negativo (agrupa los folds de la validación cruzada) |
| `particion` | str | train / valid / test (en historial y candidatos es temporal por usuario; en outfits e items es por outfit de Polyvore) |
| `n_items` | int64 | Cantidad de prendas del outfit |
| `cambiadas` | int64 | Prendas cambiadas para armar el negativo |
| `item_ids` | texto | Prendas del outfit separadas por '|' (llaves de la hoja items) |
| `aplica_C1` | int64 | 1 si la regla C1 aplica al outfit |
| `aplica_C2` | int64 | 1 si la regla C2 aplica al outfit |
| `aplica_P1` | int64 | 1 si la regla P1 aplica al outfit |
| `aplica_P2` | int64 | 1 si la regla P2 aplica al outfit |
| `aplica_P3` | int64 | 1 si la regla P3 aplica al outfit |
| `aplica_E1` | int64 | 1 si la regla E1 aplica al outfit |
| `aplica_Ep1` | int64 | 1 si la regla Ep1 aplica al outfit |
| `cumple_C1` | int64 | 1 si el outfit cumple la regla C1 |
| `cumple_C2` | int64 | 1 si el outfit cumple la regla C2 |
| `cumple_P1` | int64 | 1 si el outfit cumple la regla P1 |
| `cumple_P2` | int64 | 1 si el outfit cumple la regla P2 |
| `cumple_P3` | int64 | 1 si el outfit cumple la regla P3 |
| `cumple_E1` | int64 | 1 si el outfit cumple la regla E1 |
| `cumple_Ep1` | int64 | 1 si el outfit cumple la regla Ep1 |
| `score_reglas` | int64 | Reglas de las 7 que cumple el outfit (0–7). Etiqueta de DLMn (fase 2) |

## `usuarios`

Usuarios simulados: datos de registro y parámetros ocultos del gusto. Escribe: Simulación (etapa 6). Filas: 350.

| Columna | Tipo | Descripción |
|---|---|---|
| `user_id` | str | ID del usuario simulado (U001–U350) |
| `grupo` | str | mixto (clóset 70 % Polyvore / 30 % propio) o transferencia (clóset 100 % catálogo propio) |
| `arquetipo` | str | OCULTO al modelo. Gusto programado en la simulación (minimalista, clasico, vintage, atrevido, deportivo) |
| `estilo_fav` | str | Estilo favorito declarado al registrarse |
| `edad` | int64 | Edad en años (el modelo la usa por tramos 18-24, 25-34, 35-45) |
| `genero` | str | Género declarado |
| `ciudad` | str | Ciudad del Perú |
| `clima` | str | Clima de la ciudad (frio, templado, calido) |
| `n_closet` | int64 | Prendas en el clóset del usuario |
| `w_C1` | float64 | OCULTO. Peso de la regla C1 en el gusto simulado (cuánto le molesta romperla) |
| `w_C2` | float64 | OCULTO. Peso de la regla C2 en el gusto simulado (cuánto le molesta romperla) |
| `w_P1` | float64 | OCULTO. Peso de la regla P1 en el gusto simulado (cuánto le molesta romperla) |
| `w_P2` | float64 | OCULTO. Peso de la regla P2 en el gusto simulado (cuánto le molesta romperla) |
| `w_P3` | float64 | OCULTO. Peso de la regla P3 en el gusto simulado (cuánto le molesta romperla) |
| `w_E1` | float64 | OCULTO. Peso de la regla E1 en el gusto simulado (cuánto le molesta romperla) |
| `w_Ep1` | float64 | OCULTO. Peso de la regla Ep1 en el gusto simulado (cuánto le molesta romperla) |
| `b_estilo` | float64 | OCULTO. Peso del estilo favorito en el gusto simulado |
| `d_neutros` | float64 | OCULTO. Peso de los colores neutros |
| `c_clima` | float64 | OCULTO. Peso de vestir acorde al clima |
| `e_compat` | float64 | OCULTO. Peso de la compatibilidad humana (aprendida de Polyvore) |
| `ruido` | float64 | OCULTO. Fracción de decisiones invertidas al azar (5–10 %) |
| `sesgo` | float64 | OCULTO. Mediana de la utilidad del usuario (centra su tasa de aceptación) |

## `closets`

Prendas de cada usuario. Escribe: Simulación (etapa 6). Filas: 20 997.

| Columna | Tipo | Descripción |
|---|---|---|
| `user_id` | str | ID del usuario simulado (U001–U350) |
| `item_id` | str | ID de la prenda: 'pv_' + ID de Polyvore, o 'P' + número del catálogo propio |
| `origen` | str | items: polyvore / propio · closets: de dónde viene la prenda · candidatos y predicciones: historial / nuevo (evaluación) o recomendar (escrito por recomendar()) |
| `slot` | str | Lugar en el outfit: arriba, abajo, vestido, exterior, calzado, bolso, accesorio, joyeria |

## `historial`

50 outfits por usuario con su decisión (35 train  7 valid  8 test). Escribe: Simulación (etapa 6). Filas: 17 500.

| Columna | Tipo | Descripción |
|---|---|---|
| `user_id` | str | ID del usuario simulado (U001–U350) |
| `orden` | int64 | Posición de la interacción en el tiempo (0–49) |
| `fecha` | str | Fecha de la interacción o de la escritura |
| `outfit_id` | str | ID del outfit (Polyvore: set_id y sufijo del negativo; usuarios: U###_O## historial, U###_V/T### candidatos, U###_R<fecha>_### recomendar()) |
| `item_ids` | str | Prendas del outfit separadas por '|' (llaves de la hoja items) |
| `n_items` | int64 | Cantidad de prendas del outfit |
| `particion` | str | train / valid / test (en historial y candidatos es temporal por usuario; en outfits e items es por outfit de Polyvore) |
| `viola_C1` | int64 | 1 si el outfit rompe la regla C1 |
| `viola_C2` | int64 | 1 si el outfit rompe la regla C2 |
| `viola_P1` | int64 | 1 si el outfit rompe la regla P1 |
| `viola_P2` | int64 | 1 si el outfit rompe la regla P2 |
| `viola_P3` | int64 | 1 si el outfit rompe la regla P3 |
| `viola_E1` | int64 | 1 si el outfit rompe la regla E1 |
| `viola_Ep1` | int64 | 1 si el outfit rompe la regla Ep1 |
| `score_reglas` | int64 | Reglas de las 7 que cumple el outfit (0–7). Etiqueta de DLMn (fase 2) |
| `p_real` | float64 | Probabilidad de aceptar según la simulación (verdad oculta; solo para evaluar y como techo) |
| `aceptado` | int64 | 1 = el usuario aceptó el outfit, 0 = lo rechazó. Etiqueta del DeepFM y de las métricas de ranking |

## `candidatos`

Outfits que se ordenan para cada usuario  con la probabilidad del DeepFM. Escribe: Etapa 7 y recomendar(). Filas: 52 500.

| Columna | Tipo | Descripción |
|---|---|---|
| `user_id` | str | ID del usuario simulado (U001–U350) |
| `outfit_id` | str | ID del outfit (Polyvore: set_id y sufijo del negativo; usuarios: U###_O## historial, U###_V/T### candidatos, U###_R<fecha>_### recomendar()) |
| `item_ids` | str | Prendas del outfit separadas por '|' (llaves de la hoja items) |
| `particion` | str | train / valid / test (en historial y candidatos es temporal por usuario; en outfits e items es por outfit de Polyvore) |
| `origen` | str | items: polyvore / propio · closets: de dónde viene la prenda · candidatos y predicciones: historial / nuevo (evaluación) o recomendar (escrito por recomendar()) |
| `n_items` | int64 | Cantidad de prendas del outfit |
| `p_real` | float64 | Probabilidad de aceptar según la simulación (verdad oculta; solo para evaluar y como techo) |
| `aceptado` | int64 | 1 = el usuario aceptó el outfit, 0 = lo rechazó. Etiqueta del DeepFM y de las métricas de ranking |
| `p_deepfm` | float64 | Fase 1: probabilidad de que el usuario lo acepte según el DeepFM |
| `en_top` | int64 | 1 = el outfit pasó el filtro del DeepFM (top 25 % del usuario) |
| `fecha` | str | Fecha de la interacción o de la escritura |

## `predicciones`

Ranking final (top 10 de evaluación y 3 recomendaciones por llamada). Escribe: Etapa 7 y recomendar(). Filas: 7 000.

| Columna | Tipo | Descripción |
|---|---|---|
| `user_id` | str | ID del usuario simulado (U001–U350) |
| `outfit_id` | str | ID del outfit (Polyvore: set_id y sufijo del negativo; usuarios: U###_O## historial, U###_V/T### candidatos, U###_R<fecha>_### recomendar()) |
| `item_ids` | str | Prendas del outfit separadas por '|' (llaves de la hoja items) |
| `experimento` | str | Sistema que generó la predicción (3 · DeepFM + Random Forest, el mejor del paso 7d) |
| `p_deepfm` | float64 | Fase 1: probabilidad de que el usuario lo acepte según el DeepFM |
| `p_ttmn` | float64 | Fase 2: probabilidad de que el outfit sea real/compatible (salida TTMn, Random Forest) |
| `dlmn` | float64 | Fase 2: armonía predicha 0–7 (salida DLMn, Random Forest) |
| `score_final` | float64 | α·pct(DeepFM) + (1 − α)·[β·pct(TTMn) + (1 − β)·pct(DLMn)], con α = 0,6 y β = 0,5 (elegidos en valid) |
| `rango` | int64 | Posición en el ranking final del usuario (1 = primera recomendación) |
| `aceptado` | int64 | 1 = el usuario aceptó el outfit, 0 = lo rechazó. Etiqueta del DeepFM y de las métricas de ranking |
| `origen` | str | items: polyvore / propio · closets: de dónde viene la prenda · candidatos y predicciones: historial / nuevo (evaluación) o recomendar (escrito por recomendar()) |
| `fecha` | str | Fecha de la interacción o de la escritura |

## `metricas`

Métricas de la fase 2 y del ranking final por semilla. Escribe: Etapa 7. Filas: 194.

| Columna | Tipo | Descripción |
|---|---|---|
| `fuente` | str | Notebook o paso que produjo la métrica |
| `experimento` | str | Sistema que generó la predicción (3 · DeepFM + Random Forest, el mejor del paso 7d) |
| `modelo` | str | Modelo o sistema evaluado |
| `semilla` | int64 | Semilla de entrenamiento |
| `metrica` | str | Nombre de la métrica |
| `valor` | float64 | Valor de la métrica |

## `impacto_ods`

Indicadores de impacto ODS 12. Escribe: Etapa 8. Filas: 8.

| Columna | Tipo | Descripción |
|---|---|---|
| `indicador` | str | Indicador de impacto |
| `valor` | str | Valor de la métrica |
| `meta_ods` | str | Meta del ODS 12 a la que aporta |
| `como_se_mide` | str | Cálculo |

## `diccionario`

Significado de cada columna. Escribe: Etapa 8. Filas: 116.

| Columna | Tipo | Descripción |
|---|---|---|
| `hoja` | texto | Hoja del libro |
| `columna` | texto | Columna |
| `tipo_dato` | texto | Tipo de dato |
| `descripcion` | texto | Significado |
