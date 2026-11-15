# Clasificación de departamentos en CABA

**Los Outliers**  
**ASIG00202 - Programación Avanzada para Ciencia de Datos - 2/2026**  
**Profesor:** Juan Carlos Cifuentes Durán  
**Integrantes:** Alejandra Beatriz Bertran · Ariel Abal · Sebastián Ezequiel Gines

Proyecto de clasificación de avisos de departamentos en **segmento de precio alto o estándar**, usando superficie, ambientes y barrio. Se utiliza exclusivamente el dataset oficial de **2020**.

## Archivos principales

| Archivo o carpeta | Función |
| --- | --- |
| `proyecto_inmuebles.ipynb` | Desarrollo y ejecución del análisis |
| `resultados/analisis_papermill.ipynb` | Notebook ejecutado con Papermill |
| `inmuebles/` | Código de preparación, entrenamiento, evaluación y persistencia |
| `ejecutar.py` | Ejecución del mismo flujo por consola |
| `dashboard.py` | Presentación interactiva de los resultados con Streamlit |
| `datasets/departamentos_2020.csv` | Datos originales |
| `resultados/departamentos_2020/` | Modelo, base SQLite, métricas, predicciones, gráficos y registro |
| `mongodb/` | Exportación de datos y resultados e instrucciones de importación |
| `presentacion/` | Siete filminas en PDF y PowerPoint e imágenes |
| `tests/` | Comprobaciones de la metodología |

## Instalación

Entorno usado: **Python 3.14.3**. Desde la carpeta que contiene `dashboard.py` y `requirements.txt`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

En Windows, crear el entorno con `py -3.14 -m venv .venv` y, desde Símbolo del sistema, activarlo con `.venv\Scripts\activate.bat`.

## Abrir la aplicación

```bash
python -m streamlit run dashboard.py
```

Abrir la dirección indicada como **Local URL** en la terminal, normalmente `http://localhost:8501`. Mantener la terminal abierta; `Ctrl + C` detiene el servidor.

La aplicación utiliza la base SQLite, los CSV y JSON de resultados, las imágenes de `presentacion/recursos/`, `presentacion/defensa.pdf` y `mongodb/manifest.json`. No requiere volver a entrenar, cargar el modelo joblib ni conectarse a MongoDB.

El recorrido tiene seis secciones: objetivo, exploración, preparación y aprendizaje, comparación de modelos, almacenamiento y conclusiones. El modo presentación permite avanzar con los botones Anterior y Siguiente.

Los filtros de barrio, superficie y ambientes modifican la visualización, no el entrenamiento. Los indicadores y las descargas usan todos los avisos seleccionados. La dispersión muestra hasta 5.000 puntos y la tabla hasta 1.000 filas para mantener fluidez.

La sección de aprendizaje relaciona las fases **Validar, Transformar, Separar, Ajustar y Predecir** con el proyecto. Incluye un diagrama de entrenamiento, validación y test. En la comparación se pueden consultar tres avisos reales de test y las predicciones guardadas de cada modelo. Son ejemplos ilustrativos; las métricas se calculan con todo el test.

## Ejecutar el análisis completo

Con el entorno activo:

```bash
python -m papermill proyecto_inmuebles.ipynb resultados/analisis_papermill.ipynb -p run_id departamentos_2020 -p cuantil 0.75 -p semilla 42 --execution-timeout 1800
```

Como alternativa, `python ejecutar.py` ejecuta el flujo de entrenamiento por consola. El notebook añade la exportación para MongoDB; también se puede ejecutar por separado con `python preparar_mongodb.py`.

`run_id` identifica la carpeta de resultados. Repetir un nombre reemplaza sus archivos. La semilla mantiene la división aleatoria; cambiar `cuantil` redefine las categorías y cambia el problema que se evalúa.

## Fuente y preparación

Fuente: [BA Data — Departamentos en venta](https://data.buenosaires.gob.ar/dataset/departamentos-venta).

[Descarga del CSV de 2020](https://cdn.buenosaires.gob.ar/datosabiertos/datasets/secretaria-de-desarrollo-urbano/departamentos-venta/departamentos-en-venta-2020.csv).

Cada fila representa una publicación, no una venta efectiva ni necesariamente una propiedad única. Se eliminaron **205 duplicados exactos** de 156.258 registros: quedaron **156.053 avisos**.

Se dejaron como faltantes 18 superficies fuera de 10–1000 m² y 29 cantidades de ambientes fuera de 1–20. Son límites de plausibilidad declarados. Se unificó la escritura de barrios y direcciones y se conservaron las zonas de la fuente. Hay diez barrios faltantes. No se reconstruyeron superficies a partir del precio. Nota exploratoria: el archivo de 2020 no incluye antigüedad.

## Definición del objetivo y separación

Se reservó el 20 % de los grupos de dirección normalizada mediante `GroupShuffleSplit`, con semilla 42. Quedaron **124.576 avisos para entrenamiento y 31.477 para test**: 79,83 % y 20,17 % de las filas. Los avisos de una misma dirección permanecen juntos; variantes de escritura no detectadas son una limitación.

La consigna solicita clasificar segmentos de valor, pero no fija un corte. Para este proyecto se definió como **alto** al precio mayor al **percentil 75 del entrenamiento**, USD 235.000. El objetivo es identificar aproximadamente el cuarto más caro de esa muestra. Los precios menores o iguales al límite son estándar. Es una definición relativa, no una certificación de lujo ni un criterio externo del mercado.

El precio se usa para construir la categoría correcta. Las características de entrada son únicamente **superficie, ambientes y barrio**. Se excluyen precio y derivados, cotización, dirección y la propia categoría.

## Pipeline y comparación

La limpieza de reglas fijas precede a la separación. Los ajustes que dependen de los datos se aprenden dentro del `Pipeline` usando sólo entrenamiento:

- Variables numéricas: faltantes completados con mediana y escalado con `StandardScaler`.
- Barrio: categoría para faltantes y columnas de ceros y unos con `OneHotEncoder`.
- Modelo: regresión logística o Random Forest, con una referencia que siempre predice estándar.

`ColumnTransformer` aplica la preparación a cada tipo de columna. `GridSearchCV` prueba configuraciones utilizando las mismas tres divisiones `StratifiedGroupKFold`, sin compartir direcciones entre ajuste y validación.

Se probaron C de 0.1, 1 y 10 y pesos normales o balanceados en regresión logística. Para Random Forest se usaron 120 árboles, profundidad 12 o sin límite y mínimo de 5 o 20 ejemplos por hoja.

Se eligió el algoritmo por **F1 promedio de validación**, antes de evaluar test. Cada búsqueda vuelve a ajustar su mejor configuración con todo entrenamiento; los datos de test permanecen reservados.

## Resultados

| Modelo | F1 validación | Accuracy test | Precision test | Recall test | F1 test |
| --- | --- | --- | --- | --- | --- |
| Referencia estándar | 0,0000 | 0,7508 | 0,0000 | 0,0000 | 0,0000 |
| Regresión logística | 0,7983 | 0,8953 | 0,7425 | 0,8878 | 0,8087 |
| Random Forest | 0,7915 | 0,9057 | 0,8354 | 0,7743 | 0,8037 |

Se seleccionó regresión logística con **C = 10 y clases balanceadas**. Detectó el 88,8 % de los avisos altos de test. Random Forest tuvo mayor Accuracy y Precision, pero menor Recall; no se modificó el criterio de selección después de mirar test.

Accuracy mide los aciertos totales. Precision indica cuántos de los marcados altos realmente eran altos. Recall indica cuántos de los altos reales se detectaron. F1 combina Precision y Recall mediante su media armónica.

Las matrices usan filas para la categoría real y columnas para la predicción. En regresión logística hubo 21.219 estándar y 6.963 altos bien clasificados, 2.415 falsos positivos y 880 falsos negativos.

## Almacenamiento

SQLite conserva cinco tablas:

| Tabla | Contenido |
| --- | --- |
| `datos_limpios` | Avisos, categoría y separación entre entrenamiento y test |
| `datos_preprocesados` | Valores preparados por el Pipeline ajustado con entrenamiento |
| `predicciones` | Categoría real, predicción y probabilidad por modelo en test |
| `metricas` | Métricas de validación y test de cada modelo |
| `configuracion` | Parámetros, versiones y huella digital del dataset |

`fila_fuente` relaciona los avisos con las predicciones. Hay 156.053 entradas y 94.431 predicciones, correspondientes a tres modelos sobre 31.477 avisos de test.

Para MongoDB se generaron tres colecciones JSON, con un documento por línea:

| Colección | Documentos | Contenido |
| --- | ---: | --- |
| `datos_entrada` | 156.053 | Avisos limpios y valores preparados |
| `resultados_modelo` | 94.434 | Predicciones y tres documentos de métricas globales |
| `configuracion` | 1 | Opciones de la ejecución y esquema de preparación |

Los JSON están en `mongodb/colecciones/`; `mongodb/LEEME.md` explica su importación. `mongodb/manifest.json` describe los archivos y no se importa como colección. Para ahorrar espacio, de los valores preparados sólo se guardan los distintos de cero; la configuración permite reconstruir el orden completo.

La exportación fue comprobada localmente. La aplicación no se conecta a MongoDB ni verifica el estado de la importación remota. `mongodb/validar_importacion.mongodb.js` contiene controles de sólo lectura para ejecutar con mongosh después de importar.

## Publicación en Streamlit Community Cloud

Subir el contenido de esta carpeta a un repositorio GitHub conservando las rutas y respetando `.gitignore`. La base SQLite debe estar incluida. Los JSON grandes de `mongodb/colecciones/` no son necesarios para la aplicación y están excluidos de Git.

En [Streamlit Community Cloud](https://share.streamlit.io/), crear una aplicación con ese repositorio, seleccionar la rama y `dashboard.py` como archivo principal. En Advanced settings, elegir Python 3.14 si está disponible para coincidir con el entorno usado. La plataforma instalará `requirements.txt`.

## Verificación y límites

`python -m unittest discover -s tests -v` comprueba limpieza, separación por direcciones, definición del límite con entrenamiento, barrios desconocidos, exclusión de precios y persistencia SQLite.

Los resultados describen avisos históricos de 2020, concentrados en el segundo trimestre. No representan un censo equilibrado ni precios actuales de cierre. Los coeficientes y las importancias describen relaciones predictivas, no causalidad.

La validación usada para seleccionar puede ser optimista; la variación entre rondas no es un intervalo de confianza. No se cambian opciones usando test ni se vuelve a entrenar con test. Para evaluar otro período se necesitarían datos recientes y una prueba temporal independiente.

Las ilustraciones son generadas y no corresponden a avisos reales. Los logos son los proporcionados por el equipo. Su procedencia se documenta en `presentacion/recursos/PROCEDENCIA.json`.
