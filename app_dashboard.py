import streamlit as st
import pandas as pd
import altair as alt
import io

# Configuración de la página
st.set_page_config(page_title="Panel Nivel de Logro de Aprendizaje", layout="wide")

@st.cache_data
def cargar_datos():
    df = pd.read_csv("BD_Dashboard_Consolidado.csv")
    return df

try:
    df = cargar_datos()
except FileNotFoundError:
    st.error("No se encontró el archivo 'BD_Dashboard_Consolidado.csv'. Ejecuta procesar_notas.py primero.")
    st.stop()

# Detección de columnas
columnas = df.columns.tolist()
col_area = next((c for c in columnas if c.upper() in ['AREA', 'ÁREA']), columnas[0])
col_grado = next((c for c in columnas if c.upper() == 'GRADO'), columnas[1])
col_seccion = next((c for c in columnas if c.upper() in ['SECCION', 'SECCIÓN']), columnas[2])
col_comp = next((c for c in columnas if 'COMPETENCIA' in c.upper()), columnas[3] if len(columnas)>3 else None)
col_nivel = next((c for c in columnas if 'NIVEL' in c.upper()), 'NIVEL_DE_LOGRO')
col_estudiante = next((c for c in columnas if 'ESTUDIANTE' in c.upper()), 'ESTUDIANTE')
col_bimestre = 'BIMESTRE' if 'BIMESTRE' in columnas else None

# --- CORRECCIÓN DE EXO ---
df = df[df[col_nivel].isin(['AD', 'A', 'B', 'C', 'EXO'])]

# --- FILTROS DEPENDIENTES EN CASCADA ---
st.sidebar.header("Filtros de Búsqueda")

df_base = df.copy()

if col_bimestre:
    bimestres_disponibles = sorted(list(df_base[col_bimestre].unique()))
    bimestre_seleccionado = st.sidebar.selectbox("Bimestre:", ["Ambos (Comparativo)"] + bimestres_disponibles)
else:
    bimestre_seleccionado = "I BIMESTRE"

area = st.sidebar.selectbox("Área:", ["Todas"] + list(df_base[col_area].unique()))
if area != "Todas":
    df_base = df_base[df_base[col_area] == area]

orden_logico_grados = ['PRIMERO', 'SEGUNDO', 'TERCERO', 'CUARTO', 'QUINTO']
grados_brutos = list(df_base[col_grado].unique())
grados_disponibles = sorted(grados_brutos, key=lambda x: orden_logico_grados.index(x) if x in orden_logico_grados else 999)
grado = st.sidebar.selectbox("Grado:", ["Todos"] + grados_disponibles)
if grado != "Todos":
    df_base = df_base[df_base[col_grado] == grado]

secciones_disponibles = sorted(list(df_base[col_seccion].unique()))
seccion = st.sidebar.selectbox("Sección:", ["Todas"] + secciones_disponibles)
if seccion != "Todas":
    df_base = df_base[df_base[col_seccion] == seccion]

df_temp = df_base.copy()
if bimestre_seleccionado != "Ambos (Comparativo)" and col_bimestre:
    df_temp = df_temp[df_temp[col_bimestre] == bimestre_seleccionado]

if col_comp:
    competencias_lista = sorted(list(df_temp[col_comp].dropna().unique()))
    competencias = st.sidebar.multiselect("Competencias:", competencias_lista, default=competencias_lista)
else:
    competencias = []

df_filtrado = df_temp.copy()
if len(competencias) > 0 and col_comp:
    df_filtrado = df_filtrado[df_filtrado[col_comp].isin(competencias)]

# --- CABECERA DINÁMICA ---
col_logo, col_titulo = st.columns([1, 4])
with col_logo:
    st.image("escudo.png", width=150)
with col_titulo:
    st.title("Panel Nivel de Logro de Aprendizaje")
    if bimestre_seleccionado == "Ambos (Comparativo)":
         st.subheader("I y II BIMESTRE (CONSOLIDADO)")
    else:
         st.subheader(bimestre_seleccionado)
    st.markdown("### IE Nº 20393 Túpac Amaru - Pampa Libre")

st.divider()

# --- RESUMEN DEL NIVEL ---
st.markdown("### Resumen del NIVEL")
col_nombres, c1, c2, c3, c4, c5 = st.columns([1.5, 1, 1, 1, 1, 1])

total_estudiantes_unicos = df_filtrado[col_estudiante].nunique()
count_ad = len(df_filtrado[df_filtrado[col_nivel] == 'AD'])
count_a = len(df_filtrado[df_filtrado[col_nivel] == 'A'])
count_b = len(df_filtrado[df_filtrado[col_nivel] == 'B'])
count_c = len(df_filtrado[df_filtrado[col_nivel] == 'C'])
count_exo = len(df_filtrado[df_filtrado[col_nivel] == 'EXO'])

col_nombres.metric("Estudiantes Únicos", total_estudiantes_unicos)
c1.metric("Logro Destacado (AD)", count_ad)
c2.metric("Logro Esperado (A)", count_a)
c3.metric("En Proceso (B)", count_b)
c4.metric("En Inicio (C)", count_c)
c5.metric("Exonerado (EXO)", count_exo)

st.divider()

# --- TABLAS DE APOYO, EXO Y ALERTA TEMPRANA CON EXPANSORES ---
col_t1, col_t2 = st.columns(2)

with col_t1:
    # Expansor 1: Apoyo Focalizado
    with st.expander("🟡 Ver estudiantes que requieren Apoyo Focalizado (2 a más 'C')"):
        df_apoyo = df_filtrado[df_filtrado[col_nivel] == 'C']
        if not df_apoyo.empty:
            df_agrupado = df_apoyo.groupby(col_estudiante).agg(
                CANTIDAD_C=(col_comp, 'count'),
                COMPETENCIAS_A_MEJORAR=(col_comp, lambda x: ', '.join(sorted(set(x))))
            ).reset_index()
            
            df_apoyo_focalizado = df_agrupado[df_agrupado['CANTIDAD_C'] >= 2]
            
            if not df_apoyo_focalizado.empty:
                df_mostrar = df_apoyo_focalizado[[col_estudiante, 'COMPETENCIAS_A_MEJORAR']]
                st.dataframe(df_mostrar, hide_index=True, use_container_width=True)
            else:
                st.success("✅ Ningún estudiante requiere apoyo focalizado (2 a más 'C') en esta selección.")
        else:
            st.success("✅ No hay estudiantes con calificación 'C' en esta selección.")

    # Expansor 2: Exonerados
    with st.expander("⚪ Ver Estudiantes Exonerados (EXO)"):
        df_exo = df_filtrado[df_filtrado[col_nivel] == 'EXO']
        if not df_exo.empty:
            df_exo_agrupado = df_exo.groupby(col_estudiante).agg({col_comp: lambda x: ', '.join(sorted(set(x)))}).reset_index()
            df_exo_agrupado = df_exo_agrupado.rename(columns={col_comp: 'COMPETENCIAS EXONERADAS'})
            st.dataframe(df_exo_agrupado, hide_index=True, use_container_width=True)
        else:
            st.info("No hay estudiantes exonerados en esta selección.")

with col_t2:
    # Expansor 3: Riesgo Crónico
    if bimestre_seleccionado == "I BIMESTRE":
        with st.expander("🔴 Ver Alerta de Riesgo Crónico"):
            st.info("💡 Esta alerta se activa a partir del II Bimestre o en la vista Comparativa para identificar patrones de estancamiento.")
    else:
        with st.expander("🔴 Ver Alerta de Riesgo Crónico (C en I y II Bimestre)"):
            if col_bimestre and area != "Todas" and grado != "Todos" and seccion != "Todas":
                df_b1_c = df_base[(df_base[col_bimestre] == 'I BIMESTRE') & (df_base[col_nivel] == 'C')]
                df_b2_c = df_base[(df_base[col_bimestre] == 'II BIMESTRE') & (df_base[col_nivel] == 'C')]
                
                df_cronicos = pd.merge(df_b1_c, df_b2_c, on=[col_estudiante, col_comp])
                
                if not df_cronicos.empty:
                    df_cronicos_agrupado = df_cronicos.groupby(col_estudiante).agg({col_comp: lambda x: ', '.join(sorted(set(x)))}).reset_index()
                    df_cronicos_agrupado = df_cronicos_agrupado.rename(columns={col_comp: 'COMPETENCIA EN RIESGO CRÓNICO'})
                    st.error("⚠️ Atención: Estudiantes estancados en nivel de inicio (C) desde el I Bimestre.")
                    st.dataframe(df_cronicos_agrupado, hide_index=True, use_container_width=True)
                else:
                    st.success("✅ ¡Excelentes noticias! Ningún estudiante repite 'C' en ambos bimestres para esta selección.")
            else:
                st.info("Para ver el análisis de Riesgo Crónico, debes seleccionar un Área, Grado y Sección específica.")

st.divider()

# --- SECCIÓN DE GRÁFICOS ORGANIZADA EN PESTAÑAS ---
st.markdown(f"**Visualizando Padrón General:** {area} | {grado} | {seccion}")

descripciones = {'AD': 'AD (Logro destacado)', 'A': 'A (Logro Esperado)', 'B': 'B (En Proceso)', 'C': 'C (En Inicio)', 'EXO': 'EXO (Exonerado)'}
colores_minedu = {'AD (Logro destacado)': '#1f77b4', 'A (Logro Esperado)': '#2ca02c', 'B (En Proceso)': '#ffcc00', 'C (En Inicio)': '#d62728', 'EXO (Exonerado)': '#808080'}
orden_niveles = ['AD (Logro destacado)', 'A (Logro Esperado)', 'B (En Proceso)', 'C (En Inicio)', 'EXO (Exonerado)']

tab_gen, tab_cant, tab_pct, tab_comp, tab_calor = st.tabs([
    "📊 Gráfico General", 
    "📊 Por Competencia", 
    "📈 Distribución %",
    "⚖️ Comparativo I vs II",
    "🔥 Mapa de Calor del Salón"
])

with tab_gen:
    conteo_notas = df_filtrado[col_nivel].value_counts().reset_index()
    conteo_notas.columns = ['NIVEL', 'CANTIDAD']
    conteo_notas['LEYENDA'] = conteo_notas['NIVEL'].map(descripciones)

    grafico_gen = alt.Chart(conteo_notas).mark_bar().encode(
        x=alt.X('NIVEL', sort=['AD', 'A', 'B', 'C', 'EXO'], title='Nivel de Logro', axis=alt.Axis(labelAngle=0)),
        y=alt.Y('CANTIDAD', title='Número de Estudiantes'),
        color=alt.Color('LEYENDA', scale=alt.Scale(domain=list(colores_minedu.keys()), range=list(colores_minedu.values())), sort=orden_niveles, legend=alt.Legend(title="Significado")),
        tooltip=['NIVEL', 'LEYENDA', 'CANTIDAD']
    ).properties(height=350)
    st.altair_chart(grafico_gen, use_container_width=True)

with tab_cant:
    if not df_filtrado.empty and col_comp:
        df_chart = df_filtrado.copy()
        df_chart['COMP_SHORT'] = df_chart[col_comp].apply(lambda x: str(x).split('_')[-1] if '_' in str(x) else str(x))
        chart_data = df_chart.groupby(['COMP_SHORT', col_nivel]).size().reset_index(name='CANTIDAD')
        chart_data['LEYENDA'] = chart_data[col_nivel].map(descripciones)

        bars = alt.Chart(chart_data).mark_bar().encode(
            x=alt.X('COMP_SHORT:N', title='COMPETENCIA', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('CANTIDAD:Q', title='Cantidad'),
            color=alt.Color('LEYENDA:N', scale=alt.Scale(domain=list(colores_minedu.keys()), range=list(colores_minedu.values())), sort=orden_niveles),
            xOffset=alt.XOffset('LEYENDA:N', sort=orden_niveles),
            tooltip=['COMP_SHORT', 'LEYENDA', 'CANTIDAD']
        )
        text = alt.Chart(chart_data).mark_text(align='center', baseline='bottom', dy=-5, fontWeight='bold').encode(
            x=alt.X('COMP_SHORT:N'), y=alt.Y('CANTIDAD:Q'), xOffset=alt.XOffset('LEYENDA:N', sort=orden_niveles), text='CANTIDAD:Q'
        )
        st.altair_chart((bars + text).properties(height=450), use_container_width=True)
    else:
        st.info("No hay datos disponibles.")

with tab_pct:
    if not df_filtrado.empty and col_comp:
        df_chart = df_filtrado.copy()
        df_chart['COMP_SHORT'] = df_chart[col_comp].apply(lambda x: str(x).split('_')[-1] if '_' in str(x) else str(x))
        chart_data = df_chart.groupby(['COMP_SHORT', col_nivel]).size().reset_index(name='CANTIDAD')
        chart_data['LEYENDA'] = chart_data[col_nivel].map(descripciones)
        chart_data['TOTAL'] = chart_data.groupby('COMP_SHORT')['CANTIDAD'].transform('sum')
        chart_data['PORCENTAJE'] = (chart_data['CANTIDAD'] / chart_data['TOTAL']) * 100
        chart_data['PORCENTAJE_TXT'] = chart_data['PORCENTAJE'].round(1).astype(str) + '%'

        bars_pct = alt.Chart(chart_data).mark_bar().encode(
            x=alt.X('COMP_SHORT:N', title='COMPETENCIA', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('PORCENTAJE:Q', title='Porcentaje (%)', stack="normalize", axis=alt.Axis(format='%')),
            color=alt.Color('LEYENDA:N', scale=alt.Scale(domain=list(colores_minedu.keys()), range=list(colores_minedu.values())), sort=orden_niveles),
            tooltip=['COMP_SHORT', 'LEYENDA', 'CANTIDAD', 'PORCENTAJE_TXT']
        ).properties(height=450)
        st.altair_chart(bars_pct, use_container_width=True)
    else:
        st.info("No hay datos disponibles.")

with tab_comp:
    if col_bimestre and bimestre_seleccionado == "Ambos (Comparativo)":
        st.markdown("### Comparación de Niveles de Logro (I vs II Bimestre)")
        conteo_comp = df_filtrado.groupby([col_bimestre, col_nivel]).size().reset_index(name='CANTIDAD')
        conteo_comp['LEYENDA'] = conteo_comp[col_nivel].map(descripciones)
        
        grafico_comparativo = alt.Chart(conteo_comp).mark_bar().encode(
            x=alt.X(f'{col_bimestre}:N', title='Bimestre', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('CANTIDAD:Q', title='Número de Estudiantes'),
            color=alt.Color('LEYENDA:N', scale=alt.Scale(domain=list(colores_minedu.keys()), range=list(colores_minedu.values())), sort=orden_niveles, legend=alt.Legend(title="Significado")),
            xOffset=alt.XOffset('LEYENDA:N', sort=orden_niveles),
            tooltip=[col_bimestre, col_nivel, 'LEYENDA', 'CANTIDAD']
        ).properties(height=400)
        st.altair_chart(grafico_comparativo, use_container_width=True)
    else:
        st.info("💡 Para ver el gráfico comparativo, selecciona 'Ambos (Comparativo)' en el filtro superior de Bimestre.")

with tab_calor:
    if not df_filtrado.empty and col_comp:
        st.markdown("### Radiografía del Salón (Mapa de Calor)")
        st.caption("Analiza rápidamente el desempeño de cada estudiante. Pasa el cursor por los recuadros para ver detalles.")
        
        df_heat = df_filtrado.copy()
        if bimestre_seleccionado == "Ambos (Comparativo)":
            df_heat['EJE_X'] = df_heat[col_bimestre] + " - " + df_heat[col_comp].apply(lambda x: str(x).split('_')[-1])
        else:
            df_heat['EJE_X'] = df_heat[col_comp].apply(lambda x: str(x).split('_')[-1])

        df_heat['LEYENDA'] = df_heat[col_nivel].map(descripciones)

        base_heatmap = alt.Chart(df_heat).encode(
            x=alt.X('EJE_X:N', title='Competencias', axis=alt.Axis(labelAngle=-45)),
            y=alt.Y('ESTUDIANTE:N', title='Estudiantes', sort=alt.EncodingSortField(field="ESTUDIANTE", order="ascending"))
        )

        heatmap = base_heatmap.mark_rect(stroke='white', strokeWidth=1).encode(
            color=alt.Color('LEYENDA:N', scale=alt.Scale(domain=list(colores_minedu.keys()), range=list(colores_minedu.values())), legend=alt.Legend(title="Nivel de Logro"), sort=orden_niveles),
            tooltip=['ESTUDIANTE', col_bimestre, 'EJE_X', 'NIVEL_DE_LOGRO']
        )
        
        text_heatmap = base_heatmap.mark_text(baseline='middle').encode(
            text='NIVEL_DE_LOGRO:N',
            color=alt.value('white')
        )

        grafico_calor = (heatmap + text_heatmap).properties(height=max(400, len(df_heat['ESTUDIANTE'].unique()) * 25))
        st.altair_chart(grafico_calor, use_container_width=True)
    else:
        st.info("Selecciona un Área y un Grado para ver el mapa de calor.")

st.divider()

with st.expander("Ver Base de Datos Completa"):
    st.dataframe(df_filtrado.reset_index(drop=True), use_container_width=True)

st.markdown("### Exportar Datos")
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    df_filtrado.to_excel(writer, index=False, sheet_name='Reporte_Filtrado')
st.download_button(label="📥 Descargar reporte en Excel (.xlsx)", data=buffer.getvalue(), file_name='reporte_estudiantes_filtrado.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')