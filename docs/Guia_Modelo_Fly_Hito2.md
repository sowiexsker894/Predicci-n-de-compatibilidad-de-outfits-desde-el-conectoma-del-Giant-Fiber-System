# Guía de exposición · Modelo Fly, Hito 2

Exposición de 10 minutos, seguida de la ronda de preguntas. Son 11 diapositivas principales y 6 de respaldo. Cada diapositiva tiene también el guion resumido en las notas del orador del PPT.

**Reparto sugerido**

| Parte | Diapositivas | Tiempo | Quién |
|---|---|---|---|
| Problema, hipótesis y datos | 1 a 6 | ~5:10 | Nicole |
| Modelado, resultados y cierre | 7 a 11 | ~4:50 | Sergio |

**La idea que tiene que quedar:** el baseline ya es casi perfecto (98–99 %), pero el dataset es fácil y está generado por reglas. Por eso el modelo con conectoma no tiene que ganarle por mucho: tiene que demostrar que no es peor (no inferioridad) y, sobre todo, ver si aporta algo cuando hay pocos datos.

**La barrita de fases.** Arriba a la derecha de cada diapositiva hay seis círculos con las fases de CRISP-DM. El rojo es la fase en la que están; los grises son las fases ya cubiertas. Sirve para que el profe vea dónde están sin que lo tengan que decir.

---

## 1 · Portada (0:20)

**Qué muestra:** el nombre del proyecto, el hito y las dos fases que cubre.

**Qué decir:** "Somos Nicole y Sergio. Presentamos el Hito 2 de Modelo Fly, que cubre la Fase 3 de CRISP-DM, preparación de datos, y la Fase 4, modelado del baseline."

**Ojo:** en el PPT anterior las fases decían "Fase 3 Modelado / Fase 4 Evaluación". Eso estaba mal: en CRISP-DM la Fase 3 es Preparación, la 4 es Modelado y la 5 es Evaluación. Ya está corregido.

---

## 2 · Predecir si un outfit de 2 o 3 prendas combina (0:50)

**Qué muestra:** un esquema de entrada → modelo → dos salidas, y el ODS 12 abajo.

**Qué decir:** "Cada outfit tiene dos o tres prendas, y cada prenda entra con cuatro atributos: época, color, patrón y estilo. El modelo responde dos cosas: si el outfit combina, que es la salida principal, y un score de 0 a 1. Lo alineamos con el ODS 12 porque la idea es ayudar a combinar ropa que ya existe en vez de comprar otra."

---

## 3 · Probamos si la estructura de un circuito de escape sirve para decidir (1:00)

**Qué muestra:** el circuito de la mosca (LC4 y LPLC2 → DNp01 → TTMn y PSI → DLMn), con lo que significa cada parte en el problema de moda, y las hipótesis.

**Qué decir:** "En la mosca, LC4 y LPLC2 detectan dos propiedades distintas de algo que se acerca. La Giant Fiber, que en el dataset se llama DNp01, integra esas dos señales y decide si escapar. La respuesta sale por dos vías: TTMn, rápida, que produce el salto, y PSI hacia DLMn, más gradual. Un outfit se parece: varias señales distintas convergen en una decisión binaria que también admite un score. Por eso usamos TTMn para leer si combina y la rama de DLMn para el score."

Después, las hipótesis: "H1 dice que una red con esta conectividad rinde igual o mejor que modelos sin ella; H0, que no aporta ventaja. Si no podemos rechazar H0, eso también es un resultado."

**Frase clave:** "Es una analogía estructural, no funcional. La mosca no evolucionó para evaluar ropa, por eso lo planteamos como hipótesis y no como supuesto."

---

## 4 · De 166 000 neuronas a 327, y el subgrafo responde (1:10)

**Qué muestra:** la reducción del conectoma, las capas del subgrafo y la simulación de un estímulo looming.

**Qué decir:** "No usamos el conectoma entero. Del MaleCNS v1.0, con unas 166 000 neuronas, extrajimos solo el Giant Fiber System con su capa de entrada: 327 neuronas y 20 684 sinapsis internas. Para comprobar que el grafo extraído funciona, simulamos un objeto que se acerca sobre las conexiones reales. La rama rápida, TTMn, cruza el umbral primero, y la gradual, DLMn, sigue subiendo hasta el final. O sea, las dos salidas que vamos a usar existen en el grafo."

**Dato de apoyo:** flyvis, la librería de redes con conectoma más conocida para la mosca, cubre el lóbulo óptico pero no estas neuronas. Por eso no hay pesos preentrenados que reutilizar y la red se entrenará desde la estructura.

**Qué es "looming":** un estímulo visual que crece en la retina, como algo que se acerca rápido. Es lo que dispara el escape.

---

## 5 · El dataset premia la diferencia entre prendas, no la coincidencia (1:00)

**Qué muestra:** cuatro cifras del dataset, un gráfico de barras y el aviso de fuga del score.

**Qué decir:** "Hay tres cosas importantes. Primero, todos los outfits de tres prendas son compatibles; la dificultad está en los de dos, que son compatibles solo el 54.5 % de las veces. Segundo, el gráfico: cuando dos prendas comparten época, la compatibilidad baja de 0.77 a 0.43, y pasa lo mismo con color y patrón. Va contra la intuición de moda, y es una señal de que el dataset se generó con reglas. Tercero, el score separa las dos clases sin solaparse, así que usarlo como variable sería hacer trampa."

**Qué es fuga (data leakage):** usar una variable que ya contiene la respuesta. Si el score de los compatibles siempre está por encima de 0.70 y el de los incompatibles por debajo de 0.35, el modelo acertaría todo solo mirando el score.

---

## 6 · Fase 3: de datos crudos a variables listas para el modelo (0:50)

**Qué muestra:** los cinco pasos de preparación y la partición.

**Qué decir:** "Primero verificamos: no hay nulos fuera de la tercera prenda. Esos vacíos no son datos perdidos, son outfits de dos prendas, así que los codificamos como la categoría 'ninguna' en vez de imputarlos. Luego hicimos one-hot de los atributos, que da la versión A con 288 columnas. La versión B agrega cruces de par entre la prenda 1 y la 2 para época, estilo y patrón, y llega a 396. El color no lo cruzamos porque tiene 69 niveles y casi todas las combinaciones tendrían menos de 30 casos. Por último, partimos 70/15/15, estratificado por la etiqueta."

**Qué es un cruce de par:** una variable nueva que junta el valor de las dos prendas, por ejemplo "Años 60 | Tumblr". Va en orden alfabético para que no importe cuál prenda está primero.

---

## 7 · Fase 4: el umbral se elige en validación y el test se usa una sola vez (0:50)

**Qué muestra:** el flujo train → validación → test y los umbrales de éxito.

**Qué decir:** "Probamos dos modelos simples: regresión logística y árbol de decisión, cada uno con las versiones A y B. Con train ajustamos; con validación elegimos la profundidad del árbol y el umbral de decisión, con el F1 como criterio. El test lo miramos una sola vez, al final, para que no influya en ninguna elección. Los umbrales de éxito los fijamos en el Hito 1: accuracy 0.82, F1 0.85 y AUC 0.88."

**Por qué importa el umbral:** la logística da una probabilidad; el umbral decide a partir de qué valor se dice "combina". Las dos logísticas terminaron con umbral 0.70 y los árboles con 0.50.

---

## 8 · Las cuatro configuraciones superan los umbrales; la logística gana (1:00)

**Qué muestra:** la tabla completa de resultados en test y la curva ROC.

| Modelo | Accuracy | F1 | AUC |
|---|---|---|---|
| Siempre compatible | 0.750 | 0.857 | — |
| Árbol A (prof. 8) | 0.912 | 0.942 | 0.952 |
| Árbol B (prof. 8) | 0.914 | 0.942 | 0.957 |
| Logística A | 0.982 | 0.988 | 0.984 |
| Logística B | 0.992 | 0.995 | 0.995 |

**Qué decir:** "Todas las configuraciones cumplen los tres umbrales. La logística le gana al árbol en las dos versiones, y los cruces de par suman cerca de un punto de accuracy. Pero ojo: predecir siempre 'compatible' ya da un F1 de 0.857, así que ese umbral no sirve para distinguir modelos. Lo que separa es la accuracy y el AUC."

**Nota:** el F1 y la accuracy de esta tabla se calcularon a partir de las matrices de confusión que guardó el notebook; el AUC viene de la curva ROC.

---

## 9 · La dificultad real está en los outfits de 2 prendas (1:10)

**Qué muestra:** la accuracy solo en los outfits de dos prendas y tres datos clave.

**Qué decir:** "Como los outfits de tres prendas siempre son compatibles, inflan las métricas. Si miramos solo los de dos prendas, que son 8 236 en test, predecir siempre compatible cae a 0.545. La logística se mantiene en 0.966 y 0.985. Además, todos los errores van en una sola dirección: el modelo nunca dice que un outfit compatible no combina. Lo que falla es marcar como compatibles outfits que no lo son, y los cruces de par bajan esos errores de 277 a 121. Por último, de los 30 casos predefinidos, 22 ya estaban en el train, así que no sirven como validación independiente."

---

## 10 · Con un baseline en 98 %, lo defendible es no inferioridad (0:50)

**Qué muestra:** las cuatro limitaciones.

**Qué decir:** "Somos honestos con los límites. El dataset parece generado por reglas y tiene relaciones contrarias a la intuición. El 45 % de los outfits son triviales. Los 30 casos no son independientes. Y el modelo se apoya mucho en colores puntuales con pocos ejemplos, lo que puede ser memorización. Con un baseline en 98 %, no es realista superarlo por mucho; lo que vamos a defender es que el modelo con conectoma no sea inferior."

**Qué es no inferioridad:** demostrar que un modelo nuevo no es peor que el de referencia por más de un margen pequeño. Es lo que se usa cuando el de referencia ya es muy bueno.

---

## 11 · Siguientes pasos: contrastar H1 contra el baseline (0:50)

**Qué muestra:** los cuatro pasos del siguiente hito.

**Qué decir:** "En el siguiente hito entrenamos la red con la conectividad real del subgrafo: los atributos entran por LC4 y LPLC2, y las salidas se leen en TTMn y en DLMn. La comparamos contra el baseline y contra una red aleatoria del mismo tamaño, para separar el efecto de la estructura del efecto del tamaño. Y la probamos con pocos datos, 500, 1 000 y 5 000 outfits, que es donde una estructura previa podría ayudar. Gracias, ¿preguntas?"

---

## 12 · ¿Preguntas?

Pasar aquí y dejarla en pantalla durante la ronda de preguntas.

---

## Respaldo (solo si preguntan)

| Diapositiva | Úsenla si preguntan… |
|---|---|
| A1 · Conexiones de la literatura | ¿Cómo saben que el subgrafo está bien extraído? ¿Qué pesos tiene? |
| A2 · Importancia de variables | ¿En qué se basa el modelo para decidir? |
| A3 · Ridge | ¿Cómo predicen el score continuo? |
| A4 · Cramér y reglas simples | ¿No bastaba con una regla simple? |
| A5 · Matrices de confusión | ¿Por qué el árbol rinde peor? |

---

## Preguntas probables y cómo responderlas

**"Si el baseline ya da 99 %, ¿para qué el conectoma?"**
"Porque la pregunta no es solo de rendimiento. Queremos saber si la estructura del circuito aporta algo frente a una red del mismo tamaño con conexiones al azar, y si ayuda cuando hay pocos datos. Con 100 000 outfits el baseline está saturado; con 500 o 1 000 puede no estarlo."

**"¿Por qué usar un circuito de mosca para ropa?"**
"Porque los dos problemas tienen la misma forma: entradas distintas que convergen en una decisión binaria con una lectura gradual. No decimos que la mosca 'entienda' moda; es una analogía estructural que contrastamos con H0."

**"¿El dataset es real?"**
"Las prendas vienen de un catálogo de 500 piezas armado con referencias de tiendas y plataformas de moda, pero las combinaciones parecen generadas por reglas. Lo reconocemos como limitación: por eso no tiene validación humana y tiene relaciones contrarias a la intuición."

**"¿Por qué la misma época baja la compatibilidad?"**
"Es una de las señales de que el dataset sigue reglas internas y no criterio de moda real. Lo reportamos tal cual; no lo corregimos porque cambiaría la etiqueta."

**"¿Por qué no usaron el score como variable?"**
"Porque es fuga: separa las dos clases sin solaparse. El modelo acertaría todo leyendo el score y no aprendería nada de las prendas."

**"¿Los 30 casos validan el modelo?"**
"No del todo, porque 22 ya estaban en train. Lo reportamos aparte, y en el siguiente hito vamos a evaluar por separado los 8 casos que no estaban."

**"¿Por qué el color no entra en los cruces?"**
"Tiene 69 niveles. Cruzarlo entre dos prendas daría miles de combinaciones con muy pocos casos cada una, y el modelo terminaría memorizando."

**"¿Por qué un umbral de 0.70 y no 0.50?"**
"Lo elegimos en validación con el F1 como criterio. Con 0.70 el modelo es más exigente para decir 'combina', lo que reduce los falsos positivos, que son su único tipo de error."

---

## Dato pendiente

El accuracy de los 30 casos y el del reajuste sin esas combinaciones en train no aparecen en las figuras guardadas, así que no están en el PPT. Si alguien ejecuta el notebook antes de la expo, se pueden agregar a la diapositiva 9 o a una de respaldo.
