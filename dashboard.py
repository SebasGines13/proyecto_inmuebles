"""Presentación interactiva: python -m streamlit run dashboard.py."""

import json
from pathlib import Path
import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st


RAIZ = Path(__file__).resolve().parent
RESULTADOS = RAIZ / "resultados" / "departamentos_2020"
RECURSOS = RAIZ / "presentacion" / "recursos"
NOMBRES = {"base": "Referencia: siempre estándar", "logistica": "Regresión logística",
           "random_forest": "Random Forest"}
COLORES = ["#1976b9", "#bc3695", "#e7b431"]
VISTAS = ["El proyecto", "Explorar los datos", "Cómo aprende el modelo",
          "Comparar modelos", "Base de datos", "Conclusiones"]
ACENTOS = ["#102440", "#1976b9", "#bc3695", "#1976b9", "#102440", "#bc3695"]
INTEGRANTES = ["Alejandra Beatriz Bertran", "Ariel Abal", "Sebastián Ezequiel Gines"]
MATERIA = "ASIG00202 - Programación Avanzada para Ciencia de Datos - 2/2026"
PROFESOR = "Juan Carlos Cifuentes Durán"

st.set_page_config(page_title="Los Outliers · Departamentos en CABA",
                   page_icon=str(RECURSOS / "logo_los_outliers.png"), layout="wide",
                   initial_sidebar_state="collapsed")


@st.cache_data
def cargar():
    """Consulta resultados de 2020 guardados; los filtros no reentrenan."""
    resumen = json.loads((RESULTADOS / "resumen.json").read_text(encoding="utf-8"))
    # La conexión es de sólo lectura y apunta a una ruta fija del proyecto.
    with sqlite3.connect((RESULTADOS / "proyecto.sqlite").as_uri() + "?mode=ro",
                         uri=True) as conexion:
        datos = pd.read_sql_query("SELECT * FROM datos_limpios", conexion)
    metricas = pd.read_csv(RESULTADOS / "metricas.csv")
    return datos, metricas, resumen



@st.cache_data
def cargar_ejemplos(modelo):
    """Lee tres avisos reales de test y sus predicciones ya calculadas."""
    with sqlite3.connect((RESULTADOS / "proyecto.sqlite").as_uri() + "?mode=ro",
                         uri=True) as conexion:
        return pd.read_sql_query(
            "SELECT d.fila_fuente, d.barrio, d.superficie, d.ambientes, "
            "d.precio_usd, d.segmento_alto, p.prediccion "
            "FROM datos_limpios d JOIN predicciones p USING (fila_fuente) "
            "WHERE d.particion = 'test' AND p.modelo = ? "
            "AND d.fila_fuente IN (2662, 11588, 21496) ORDER BY d.fila_fuente",
            conexion, params=(modelo,))


def grafico(fig):
    """Una paleta consistente facilita seguir los modelos durante la exposición."""
    fig.update_layout(template="plotly_white", font=dict(size=15, color="#233344"),
                      paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
                      margin=dict(l=15, r=15, t=45, b=15))
    st.plotly_chart(fig, width="stretch")


def barras_modelos(metricas):
    tabla = metricas.assign(Modelo=metricas.modelo.map(NOMBRES)).melt(
        id_vars="Modelo", value_vars=["f1_cv_mean", "f1_test"],
        var_name="Evaluación", value_name="F1")
    tabla["Evaluación"] = tabla["Evaluación"].map({
        "f1_cv_mean": "Validación cruzada", "f1_test": "Prueba"})
    fig = px.bar(tabla, x="Modelo", y="F1", color="Evaluación", barmode="group",
                 color_discrete_sequence=COLORES, range_y=[0, 1])
    fig.update_traces(hovertemplate="F1: %{y:.4f}<extra>%{fullData.name}</extra>")
    fig.add_annotation(x="Referencia: siempre estándar", y=.08, text="F1 = 0<br>No detecta avisos altos",
                       showarrow=False, font=dict(size=13, color="#627184"))
    grafico(fig)


if not (RESULTADOS / "proyecto.sqlite").is_file():
    st.info("Primero ejecutá el notebook del proyecto para generar los resultados.")
    st.stop()

datos, metricas, resumen = cargar()
config = resumen["configuracion"]
ganador = metricas.set_index("modelo").loc[config["modelo_elegido"]]

if st.session_state.get("vista") not in VISTAS:
    st.session_state.vista = VISTAS[0]

with st.sidebar:
    st.image(str(RECURSOS / "logo_universidad.png"), width="stretch")
    st.title("Los Outliers")
    st.caption("PROYECTO INTEGRADOR · DATOS DE 2020")
    vista = st.radio("Recorrido de la presentación", VISTAS,
        label_visibility="collapsed", key="vista")
    st.divider()
    st.markdown("**Pregunta**\n\n¿Podemos identificar el segmento de precio alto "
                "con superficie, ambientes y barrio?")
    st.caption("Muestra histórica de avisos. Los precios publicados no son precios de venta.")
    st.link_button("Ver la fuente oficial", "https://data.buenosaires.gob.ar/dataset/departamentos-venta")

# Los botones cambian el mismo estado que el menú; los callbacks se ejecutan
# antes de recrear los widgets, evitando estados de navegación inconsistentes.
def cambiar_etapa(desplazamiento):
    actual = VISTAS.index(st.session_state.vista)
    st.session_state.vista = VISTAS[max(0, min(len(VISTAS) - 1, actual + desplazamiento))]


etapa = VISTAS.index(vista)
universidad, rotulo, interruptor = st.columns([1, 4, 1.2], vertical_alignment="center")
universidad.image(str(RECURSOS / "logo_universidad.png"), width=130)
rotulo.caption(f"LOS OUTLIERS · CABA 2020  /  {etapa + 1:02d} DE {len(VISTAS):02d}  /  {vista.upper()}")
rotulo.caption(f"Expone: {INTEGRANTES[0 if etapa < 2 else 1 if etapa == 2 else 2]}")
modo_presentacion = interruptor.toggle("Modo presentación", value=True, key="modo_presentacion")
if modo_presentacion:
    # Sólo estilos propios: ningún contenido del dataset se interpreta como HTML.
    st.html(f"""<style>
    .stMainBlockContainer {{ max-width: 1500px; padding-top: 5rem; }}
    @keyframes entrada_{etapa} {{
      from {{ opacity: 0; transform: translateY(12px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    .st-key-lamina_{etapa} {{ animation: entrada_{etapa} .35s ease-out; min-height: 65vh; }}
    .st-key-lamina_{etapa} h1 {{ color: {ACENTOS[etapa]}; font-size: clamp(2.2rem, 3.2vw, 3.8rem); line-height: 1.08; }}
    .st-key-lamina_{etapa} h3 {{ color: {ACENTOS[etapa]}; }}
    .st-key-lamina_{etapa} [data-testid="stMetricValue"] {{ font-size: 2.5rem; color: {ACENTOS[etapa]}; }}
    [data-testid="stProgressBar"] [role="progressbar"] > div {{ background-color: {ACENTOS[etapa]}; }}
    @media (prefers-reduced-motion: reduce) {{
      .st-key-lamina_{etapa} {{ animation: none; }}
    }}
    </style>""")
    st.progress((etapa + 1) / len(VISTAS))


def mostrar_vista(vista):
    if vista == "El proyecto":
        st.caption(MATERIA)
        st.markdown(f"**Profesor:** {PROFESOR}")
        texto, imagen = st.columns([1.55, 1], vertical_alignment="center")
        with texto:
            st.caption("LOS OUTLIERS · PROYECTO INTEGRADOR")
            st.title("Segmentos de precio de departamentos en CABA")
            st.markdown("**Superficie, ambientes y barrio.** Tres características para "
                        "identificar el segmento de precio alto de los departamentos.")
            st.markdown("**Integrantes**")
            st.markdown("  \n".join(INTEGRANTES))
        with imagen:
            st.image(str(RECURSOS / "logo_los_outliers.png"), width="stretch")
        a, b, c, d = st.columns(4)
        a.metric("Publicaciones", f"{len(datos):,}".replace(",", "."))
        b.metric("Umbral del segmento alto", f"USD {config['umbral_usd']:,.0f}")
        c.metric("Aciertos en prueba", f"{ganador.accuracy_test:.1%}")
        d.metric("F1 en prueba", f"{ganador.f1_test:.3f}")
        if modo_presentacion:
            return
        st.subheader("De los avisos a una clasificación")
        st.markdown("El precio define la respuesta: un aviso es **alto** si supera el "
                    "límite de USD 235.000 calculado con los datos para aprender. El modelo reconoce esa "
                    "categoría a partir de las características del departamento.")
        st.info("Se reservan direcciones completas para prueba: "
                f"{resumen['entrenamiento']['filas']:,} avisos para entrenar y "
                f"{resumen['prueba']['filas']:,} para evaluar. "
                "Para predecir sólo se usan superficie, ambientes y barrio; el precio sería dar la respuesta.")
        st.subheader("Los modelos frente a una base de referencia")
        barras_modelos(metricas)
        st.caption("Primero elegimos con rondas de validación; al final evaluamos con los datos reservados. "
                   "F1 combina precisión y capacidad de detectar el segmento alto.")

    elif vista == "Explorar los datos":
        st.title("Explorar los avisos")
        st.caption("Estos filtros describen la muestra completa y no modifican el entrenamiento.")
        st.caption("Nota de la fuente: antigüedad no está disponible en el archivo de 2020.")
        particion = st.segmented_control("Datos a explorar", ["Todas", "Entrenamiento", "Prueba"],
                                         default="Todas", selection_mode="single")
        a, b = st.columns(2)
        barrios = a.multiselect("Barrios (vacío = todos)", sorted(datos.barrio.dropna().unique()))
        superficie = b.slider("Superficie (m²)", 10, 1000, (10, 1000))
        a, b = st.columns(2)
        ambientes = a.slider("Ambientes", 1, 20, (1, 20))
        incluir_faltantes = b.checkbox("Incluir ambientes desconocidos", value=True)
        filtro = datos.superficie.between(*superficie)
        if particion in ["Entrenamiento", "Prueba"]:
            filtro &= datos.particion.eq("train" if particion == "Entrenamiento" else "test")
        if barrios:
            filtro &= datos.barrio.isin(barrios)
        filtro &= (datos.ambientes.between(*ambientes)
                   | (datos.ambientes.isna() & incluir_faltantes))
        seleccion = datos.loc[filtro].copy()
        if seleccion.empty:
            st.info("No hay avisos con esta combinación de filtros.")
            return
        a, b, c = st.columns(3)
        a.metric("Avisos seleccionados", len(seleccion))
        b.metric("Precio mediano", f"USD {seleccion.precio_usd.median():,.0f}")
        c.metric("Segmento alto", f"{seleccion.segmento_alto.mean():.1%}")
        seleccion["Segmento"] = seleccion.segmento_alto.map({0: "Estándar", 1: "Alto"})
        tipo = st.radio("Gráfico", ["Superficie y precio", "Precio por barrio", "Distribución de precios"],
                         horizontal=True)
        if tipo == "Superficie y precio":
            # Sólo se limita la dispersión para que siga fluida online.
            muestra = seleccion.sample(min(5000, len(seleccion)), random_state=42)
            grafico(px.scatter(muestra, x="superficie", y="precio_usd", color="Segmento",
                               hover_data=["barrio", "ambientes"],
                               log_x=True, log_y=True, opacity=.5,
                               color_discrete_map={"Estándar": COLORES[0], "Alto": COLORES[1]},
                               labels={"superficie": "Superficie (m²)", "precio_usd": "Precio publicado (USD)"}))
            st.caption("Hasta 5.000 puntos. Pasá el cursor para ver características; "
                       "arrastrá para ampliar una región y hacé doble clic para volver.")
        elif tipo == "Precio por barrio":
            tabla = seleccion.groupby("barrio").agg(
                precio_mediano=("precio_usd", "median"), avisos=("fila_fuente", "count"))
            tabla = tabla.sort_values("avisos", ascending=False).head(15).sort_values("precio_mediano")
            grafico(px.bar(tabla.reset_index(), x="precio_mediano", y="barrio", orientation="h",
                           hover_data=["avisos"], color_discrete_sequence=[COLORES[0]],
                           labels={"precio_mediano": "Precio mediano (USD)", "barrio": "Barrio"}))
            st.caption("Hasta 15 barrios con más avisos en la selección. "
                       "La mediana describe los avisos; no es una tasación por barrio.")
        else:
            grafico(px.histogram(seleccion, x="precio_usd", color="Segmento", nbins=70,
                                 barmode="overlay", opacity=.65,
                                 color_discrete_map={"Estándar": COLORES[0], "Alto": COLORES[1]},
                                 labels={"precio_usd": "Precio publicado (USD)"}))
        st.caption("Todos los gráficos responden a los filtros. Los avisos sin superficie "
                   "conocida quedan fuera del filtro de superficie.")
        with st.expander("Ver avisos y descargar la selección", expanded=not modo_presentacion):
            st.dataframe(seleccion[["direccion", "barrio", "superficie", "ambientes",
                                    "precio_usd", "Segmento"]].head(1000), hide_index=True)
            st.caption("Vista de las primeras 1.000 filas; la descarga incluye toda la selección.")
            st.download_button("Descargar selección", seleccion.to_csv(index=False).encode("utf-8"),
                               "avisos_filtrados.csv", "text/csv")

    elif vista == "Comparar modelos":
        st.title("Comparar los modelos")
        st.caption("Comparamos dos formas de aprender y probamos distintas configuraciones antes de la evaluación final.")
        nombre = st.selectbox("Modelo", list(NOMBRES), index=1, format_func=NOMBRES.get)
        fila = metricas.set_index("modelo").loc[nombre]
        for columna, (titulo, campo) in zip(st.columns(4), [
                ("Accuracy", "accuracy_test"), ("Precision", "precision_test"),
                ("Recall", "recall_test"), ("F1", "f1_test")]):
            columna.metric(titulo, f"{fila[campo]:.3f}")
        st.caption("Accuracy: proporción total de aciertos. Precision: de los avisos marcados como altos, "
                   "cuántos lo eran. Recall: de los altos reales, cuántos detectamos. "
                   "F1: combina Precision y Recall.")
        izquierda, derecha = st.columns([1.2, 1])
        with izquierda:
            barras_modelos(metricas)
        with derecha:
            grafico(px.imshow(resumen["matrices_confusion"][nombre],
                               x=["Estándar", "Alto"], y=["Estándar", "Alto"],
                               text_auto=True, color_continuous_scale="Blues",
                               labels={"x": "Predicción", "y": "Clase real"},
                               title=f"Matriz de confusión · {NOMBRES[nombre]}"))
        st.subheader("Del resultado a un aviso real")
        st.caption(f"Predicciones guardadas de {NOMBRES[nombre]}. "
                   "Estos casos ilustran el resultado; las métricas usan todo el test.")
        ejemplos = cargar_ejemplos(nombre).set_index("fila_fuente")
        identificador = st.selectbox(
            "Aviso de test", ejemplos.index.tolist(), key="aviso_ejemplo",
            format_func=lambda valor: f"Aviso {valor} · {ejemplos.loc[valor, 'barrio']} · "
                                      f"{ejemplos.loc[valor, 'superficie']:g} m²")
        ejemplo = ejemplos.loc[identificador]
        superficie, ambientes, barrio = st.columns(3)
        superficie.metric("Superficie", f"{ejemplo.superficie:g} m²")
        ambientes.metric("Ambientes", f"{ejemplo.ambientes:g}")
        barrio.metric("Barrio", ejemplo.barrio)
        categorias = {0: "Estándar", 1: "Alto"}
        prediccion, realidad = st.columns(2)
        prediccion.metric("Predicción del modelo", categorias[int(ejemplo.prediccion)])
        realidad.metric("Categoría real", categorias[int(ejemplo.segmento_alto)])
        if ejemplo.prediccion == ejemplo.segmento_alto:
            st.success("Acierto: la predicción coincide con la categoría real de este aviso.")
        elif ejemplo.prediccion == 1:
            st.warning("Falso positivo: el modelo indicó alto, pero el aviso era estándar.")
        else:
            st.warning("Falso negativo: el modelo indicó estándar y no detectó un aviso alto.")
        st.caption(f"Precio publicado: USD {ejemplo.precio_usd:,.0f}. "
                   f"La categoría real se define por precio mayor a USD {config['umbral_usd']:,.0f}. "
                   "El precio no se entrega al modelo para predecir.")

        with st.expander("Ver tabla de métricas", expanded=not modo_presentacion):
            st.dataframe(metricas[["modelo", "f1_cv_mean", "f1_cv_std", "accuracy_test",
                                   "precision_test", "recall_test", "f1_test"]].rename(columns={
                "modelo": "Modelo", "f1_cv_mean": "F1 promedio de validación",
                "f1_cv_std": "Variación entre rondas", "accuracy_test": "Accuracy final",
                "precision_test": "Precision final", "recall_test": "Recall final",
                "f1_test": "F1 final"}).round(4), hide_index=True)
        with st.expander("Cómo se eligió el modelo"):
            st.write("Dividimos los datos de entrenamiento en tres grupos. En cada ronda, "
                     "el modelo aprende con dos y se revisa con el restante. Los avisos de una "
                     "misma dirección permanecen juntos. Repetimos las mismas divisiones para "
                     "comparar de forma justa y elegimos el mejor F1 promedio. Esto se llama "
                     "validación cruzada; GridSearchCV repite el proceso con distintas configuraciones.")
            st.json(config["parametros_modelo"])
        st.download_button("Descargar métricas", (RESULTADOS / "metricas.csv").read_bytes(),
                           "metricas.csv", "text/csv")

    elif vista == "Cómo aprende el modelo":
        st.caption("EL PIPELINE DE LA CURSADA APLICADO A NUESTRO PROYECTO")
        st.title("Cinco fases para entender cómo aprende el modelo")
        st.write("Validar → Transformar → Separar → Ajustar → Predecir")
        st.caption("M3-2 · Del pipeline al primer modelo · Modelado supervisado para predecir")

        # Conservamos las cinco fases de los apuntes; seleccionar una sólo cambia la explicación.
        fases = {
            "1 · Validar": (
                "Comprobar qué datos recibimos",
                "Cada fila es un aviso. Revisamos que estén las columnas necesarias, "
                "que los números tengan sentido y qué valores faltan. "
                "La superficie y los ambientes fuera de los rangos definidos se tratan como desconocidos.",
                "Avisos originales del CSV de 2020.",
                "Datos revisados y problemas identificados.",
            ),
            "2 · Transformar": (
                "Ordenar los datos para poder usarlos",
                "Unificamos la escritura de barrios y direcciones, convertimos los números "
                "y quitamos 205 avisos repetidos exactamente. Quedan 156.053 publicaciones. "
                "Esta limpieza usa reglas fijas. Los ajustes que se aprenden de los datos, "
                "como la mediana y la escala, se calculan después, al entrenar.",
                "Avisos con nombres y formatos de la fuente.",
                "Una tabla limpia con columnas y tipos consistentes.",
            ),
            "3 · Separar": (
                "Guardar una parte para la evaluación final",
                "Entrenamos con 124.576 avisos y reservamos otros 31.477 para test. "
                "Los avisos de una misma dirección permanecen juntos. "
                "Con entrenamiento calculamos el límite de USD 235.000: por encima, "
                "el aviso se etiqueta como alto; si es menor o igual, como estándar.",
                "La tabla limpia, agrupada por dirección.",
                "Datos para aprender y datos reservados para evaluar.",
            ),
            "4 · Ajustar": (
                "Aprender con ejemplos cuya respuesta conocemos",
                "Durante el entrenamiento damos las características del aviso "
                "(superficie, ambientes y barrio) junto con su categoría correcta. "
                "La logística aprende pesos para combinar esas características; "
                "Random Forest aprende reglas en muchos árboles. "
                "Probamos configuraciones con tres rondas de validación y elegimos por F1 promedio.",
                "Características de entrenamiento (X) y categorías correctas (y).",
                "Un Pipeline preparado y un modelo que ya aprendió.",
            ),
            "5 · Predecir": (
                "Aplicar lo aprendido y comprobar el resultado",
                "Al modelo ya entrenado le damos sólo las características de los avisos de test. "
                "Devuelve la categoría estimada. Después la comparamos con la categoría real "
                "para calcular Accuracy, Precision, Recall, F1 y la matriz de confusión. "
                "No volvemos a aprender con test ni cambiamos el ganador mirando esos resultados.",
                "Características de test y el Pipeline ya ajustado.",
                "Predicciones y métricas para evaluar el desempeño.",
            ),
        }
        fase = st.segmented_control("Recorrer las fases", list(fases),
                                     default="1 · Validar", key="fase_pipeline",
                                     selection_mode="single") or "1 · Validar"
        titulo, explicacion, entrada, salida = fases[fase]
        texto, imagen = st.columns([1.5, 1], vertical_alignment="center")
        with texto:
            st.subheader(titulo)
            st.write(explicacion)
            st.markdown(f"**Qué entra:** {entrada}")
            st.markdown(f"**Qué sale:** {salida}")
            if fase == "3 · Separar":
                st.caption("El percentil 75 deja aproximadamente al 25 % más caro por encima. "
                           "Es una definición del proyecto; la consigna no fija ese corte.")
            elif fase == "4 · Ajustar":
                st.info("Aprender no es recibir el precio como entrada: "
                        "el precio sólo permite construir la categoría correcta de los ejemplos.")
            elif fase == "5 · Predecir":
                st.metric("F1 final de la logística", f"{ganador.f1_test:.3f}")
        with imagen:
            st.image(str(RECURSOS / "interior_departamento.png"), width="stretch")
            st.caption("Ilustración generada; no corresponde a una publicación del dataset.")
        st.caption("Este recorrido explica la ejecución guardada. Cambiar de fase no entrena el modelo.")

        with st.expander("Cómo se reparten entrenamiento, validación y test",
                         expanded=fase in ["3 · Separar", "4 · Ajustar"]):
            # Diagrama estático de la metodología, sin volver a ajustar ningún modelo.
            st.html("""<svg viewBox="0 0 1000 270" role="img"
                aria-label="156.053 avisos se separan en 124.576 de entrenamiento y 31.477 de test.
                En entrenamiento se valida y ajusta el modelo. El test se reserva para evaluar."
                xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto">
                <defs><marker id="flecha" markerWidth="8" markerHeight="8"
                refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="#627184"/>
                </marker></defs>
                <g fill="none" stroke="#627184" stroke-width="2" marker-end="url(#flecha)">
                <path d="M225 133 H260 V48 H300"/><path d="M225 133 H260 V218 H300"/>
                <path d="M550 48 H625"/><path d="M795 80 V105"/>
                <path d="M795 165 V190"/><path d="M550 218 H625"/></g>
                <g font-family="Arial,sans-serif" text-anchor="middle" fill="#102440">
                <rect x="10" y="100" width="215" height="65" rx="8" fill="#f1f5fa"/>
                <text x="117" y="127" font-size="22" font-weight="bold">156.053 avisos</text>
                <text x="117" y="150" font-size="17">Datos limpios</text>
                <rect x="300" y="15" width="250" height="65" rx="8" fill="#e6f2fb"/>
                <text x="425" y="42" font-size="22" font-weight="bold">124.576 para aprender</text>
                <text x="425" y="65" font-size="17">Entrenamiento · 79,83 %</text>
                <rect x="300" y="185" width="250" height="65" rx="8" fill="#f9eaf5"/>
                <text x="425" y="212" font-size="22" font-weight="bold">31.477 para evaluar</text>
                <text x="425" y="235" font-size="17">Test reservado · 20,17 %</text>
                <rect x="625" y="15" width="340" height="65" rx="8" fill="#e6f2fb"/>
                <text x="795" y="42" font-size="20" font-weight="bold">Tres rondas de validación</text>
                <text x="795" y="65" font-size="17">Elegir configuración y algoritmo</text>
                <rect x="625" y="105" width="340" height="60" rx="8" fill="#e6f2fb"/>
                <text x="795" y="131" font-size="20" font-weight="bold">Modelo final ajustado</text>
                <text x="795" y="153" font-size="17">Usa todo el entrenamiento</text>
                <rect x="625" y="190" width="340" height="60" rx="8" fill="#f9eaf5"/>
                <text x="795" y="216" font-size="20" font-weight="bold">Predicciones y métricas finales</text>
                <text x="795" y="238" font-size="17">Comparar con la realidad del test</text>
                </g></svg>""")
            st.caption("La separación se hace por dirección. El 20 % corresponde a grupos de "
                       "dirección; por eso las cantidades de avisos no son exactamente 80/20. "
                       "Test no participa en las rondas de validación.")

        with st.expander("Qué aprende el Pipeline de scikit-learn"):
            st.write("El flujo de cinco fases organiza el trabajo completo. Dentro de Ajustar, "
                     "nuestro Pipeline de scikit-learn une el preprocesamiento y el modelo. "
                     "Para superficie y ambientes aprende la mediana de los faltantes y la escala; "
                     "para barrio aprende las columnas de ceros y unos. Después aprende el modelo. "
                     "En predict reutiliza esos ajustes, sin calcularlos de nuevo con test.")
            st.write("Por eso la fase Transformar del esquema no significa calcular "
                     "medianas o escalas con todo el dataset antes de separar. "
                     "Esos ajustes se aprenden sólo con los datos que corresponden a entrenamiento.")
        with st.expander("Las tres rondas para elegir antes de abrir test"):
            st.write("El siguiente esquema representa los tres grupos de entrenamiento. "
                     "Todos los modelos usan las mismas divisiones y las direcciones permanecen juntas.")
            st.table(pd.DataFrame({
                "Ronda": [1, 2, 3],
                "Aprende con": ["Grupos A y B", "Grupos A y C", "Grupos B y C"],
                "Se valida con": ["Grupo C", "Grupo B", "Grupo A"],
            }))
            st.write("GridSearchCV repite esas rondas para cada configuración. En cada ronda, "
                     "una copia del Pipeline aprende la preparación y el modelo sólo con dos grupos. "
                     "Comparamos el F1 promedio. La mejor configuración de cada algoritmo se "
                     "vuelve a ajustar con todo entrenamiento; elegimos el algoritmo por su "
                     "validación. Recién después evaluamos con los 31.477 avisos reservados.")
            st.caption("A, B y C son nombres ilustrativos de las divisiones; "
                       "no representan tres tamaños idénticos de avisos.")

    elif vista == "Base de datos":
        st.title("Los datos y resultados quedan guardados")
        destino = st.segmented_control("Consultar", ["Archivo SQLite", "Archivos MongoDB"],
                                       default="Archivo SQLite", selection_mode="single")
        if destino == "Archivos MongoDB":
            manifiesto = json.loads((RAIZ / "mongodb" / "manifest.json").read_text(encoding="utf-8"))
            st.info("Exportación local de tres colecciones. "
                    "La aplicación consulta estos archivos y no verifica una carga remota en MongoDB.")
            for columna, (nombre, info) in zip(st.columns(3), manifiesto["colecciones"].items()):
                columna.metric(nombre, f"{info['documentos']:,}".replace(",", "."))
            st.markdown("**datos_entrada** reúne entradas limpias y preprocesadas. "
                        "**resultados_modelo** conserva predicciones y métricas globales. "
                        "**configuracion** guarda cómo se prepararon los datos y qué opciones se usaron.")
            with st.expander("Estructura de los documentos", expanded=not modo_presentacion):
                nombre = st.selectbox("Ver un documento de ejemplo", list(manifiesto["ejemplos"]))
                st.json(manifiesto["ejemplos"][nombre])
                st.caption("Para ahorrar espacio, sólo guardamos los valores preparados que no son cero. "
                           "Los demás valen cero; configuracion conserva la lista y el orden de las variables.")
            return
        st.caption("SQLite local · Datos de entrada, transformación, predicciones, métricas y configuración")
        tablas = {"Datos limpios": "datos_limpios", "Datos preprocesados": "datos_preprocesados",
                  "Predicciones": "predicciones", "Métricas": "metricas", "Configuración": "configuracion"}
        nombre = st.selectbox("Tabla", list(tablas))
        # Sólo se interpolan nombres de esta lista fija; no se acepta SQL del usuario.
        tabla = tablas[nombre]
        with sqlite3.connect((RESULTADOS / "proyecto.sqlite").as_uri() + "?mode=ro", uri=True) as conexion:
            cantidad = conexion.execute(f'SELECT count(*) FROM "{tabla}"').fetchone()[0]
            muestra = pd.read_sql_query(f'SELECT * FROM "{tabla}" LIMIT 100', conexion)
        st.metric("Filas guardadas", cantidad)
        st.dataframe(muestra, hide_index=True, width="stretch")
        st.caption("Vista de las primeras 100 filas. fila_fuente vincula un aviso con su predicción.")
        with st.expander("Opciones usadas para repetir el trabajo"):
            st.json(config)

    elif vista == "Conclusiones":
        texto, imagen = st.columns([1.15, 1], vertical_alignment="center")
        with texto:
            st.caption("QUÉ NOS LLEVAMOS DEL ANÁLISIS")
            st.title("Un segmento de precio que podemos reconocer")
            st.markdown("### La logística supera la referencia\n"
                        "F1 de **0,809** en prueba y **88,8 %** de los avisos altos detectados.")
            st.markdown("### La ubicación y el tamaño aportan contexto\n"
                        "Los filtros permiten explorar cómo cambian los avisos "
                        "según barrio, superficie y ambientes.")
            st.markdown("### Resultados que podemos revisar y repetir\n"
                        "Datos, transformaciones, predicciones y métricas quedan "
                        "guardados en SQLite; las colecciones están preparadas para MongoDB.")
        with imagen:
            st.image(str(RECURSOS / "caba_editorial.png"), width="stretch")
            st.caption("Ilustración generada de arquitectura porteña.")
        st.caption("Alcance: avisos históricos de 2020, no precios de cierre ni tasaciones actuales. "
                   "Las direcciones pueden tener variantes y la muestra no es un censo.")
        st.download_button("Descargar presentación PDF", (RAIZ / "presentacion" / "defensa.pdf").read_bytes(),
                           "defensa.pdf", "application/pdf")


with st.container(key=f"lamina_{etapa}"):
    mostrar_vista(vista)

if modo_presentacion:
    st.divider()
    anterior, indice, siguiente = st.columns([1, 3, 1])
    anterior.button("← Anterior", key="anterior", disabled=etapa == 0,
                     on_click=cambiar_etapa, args=(-1,), width="stretch")
    indice.caption(f"Próxima etapa: {VISTAS[etapa + 1]}"
                   if etapa < len(VISTAS) - 1 else "Última etapa del recorrido")
    siguiente.button("Siguiente →", key="siguiente", disabled=etapa == len(VISTAS) - 1,
                      on_click=cambiar_etapa, args=(1,), width="stretch")
