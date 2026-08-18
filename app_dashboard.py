import streamlit as st
import pandas as pd
import altair as alt
import io

# Configuración de la página
st.set_page_config(page_title="Panel Nivel de Logro de Aprendizaje", layout="wide")

@st.cache_data
def cargar_datos():
    # AHORA LEE EL NUEVO ARCHIVO CONSOLIDADO
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
df_temp = df.copy()

# 0. Filtro de Bimestre (EL NUEVO FILTRO)
if col_bimestre:
    bimestres_disponibles = sorted(list(df_temp[col_bimestre].unique()))
    bimestre_seleccionado = st.sidebar.selectbox("Bimestre:", ["Ambos (Comparativo)"] + bimestres_disponibles)
    if bimestre_seleccionado != "Ambos (Comparativo)":
        df_temp = df_temp[df_temp[col_bimestre] == bimestre_seleccionado]
else:
    bimestre_seleccionado = "I BIMESTRE"

# 1. Filtro de Área
area = st.sidebar.selectbox("Área:", ["Todas"] + list(df_temp[col_area].unique()))
if area != "Todas":
    df_temp = df_temp[df_temp[col_area] == area]

# 2. Filtro de Grado 
orden_logico_grados = ['PRIMERO', 'SEGUNDO', 'TERCERO', 'CUARTO', 'QUINTO']
grados_brutos = list(df_temp[col_grado].unique())
grados_disponibles = sorted(grados_brutos, key=lambda x: orden_logico_grados.index(x) if x in orden_logico_grados else 999)
grado = st.sidebar.selectbox("Grado:", ["Todos"] + grados_disponibles)
if grado != "Todos":
    df_temp = df_temp[df_temp[col_grado] == grado]

# 3. Filtro de Sección 
secciones_disponibles = sorted(list(df_temp[col_seccion].unique()))
seccion = st.sidebar.selectbox("Sección:", ["Todas"] + secciones_disponibles)
if seccion != "Todas":
    df_temp = df_temp[df_temp[col_seccion] == seccion]

# 4. Filtro de Competencias
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

espacio_superior = "<div style='height: 15px;'></div>"
titulo_visible = "<div style='font-size: 0.95rem; font-weight: 600; color: #31333F; margin-bottom: 5px;'>ÁREA Y COMPETENCIA</div>"
titulo_invisible = "<div style='font-size: 0.95rem; margin-bottom: 5px;'>&nbsp;</div>"

col_nombres.markdown(espacio_superior, unsafe_allow_html=True)
col_nombres.markdown(titulo_visible, unsafe_allow_html=True)

for col in [c1, c2, c3, c4, c5]:
    col.markdown(espacio_superior, unsafe_allow_html=True)
    col.markdown(titulo_invisible, unsafe_allow_html=True)

if col_comp and not df_filtrado.empty:
    competencias_presentes = sorted(df_filtrado[col_comp].dropna().unique())
    html_nombres, html_ad, html_a, html_b, html_c, html_exo = "", "", "", "", "", ""
    
    for comp in competencias_presentes:
        df_comp = df_filtrado[df_filtrado[col_comp] == comp]
        area_name = df_comp[col_area].iloc[0] if not df_comp.empty and col_area in df_comp.columns else "Área"
        comp_name = str(comp).split('_')[-1] if '_' in str(comp) else str(comp)
        
        row_style = "font-size: 0.90rem; color: #4F4F4F; margin-top: 4px; height: 22px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;"
        
        html_nombres += f"<div style='{row_style} font-weight: 600;'>{area_name} ({comp_name})</div>"
        
        cant_ad = len(df_comp[df_comp[col_nivel] == 'AD'])
        cant_a = len(df_comp[df_comp[col_nivel] == 'A'])
        cant_b = len(df_comp[df_comp[col_nivel] == 'B'])
        cant_c = len(df_comp[df_comp[col_nivel] == 'C'])
        cant_exo = len(df_comp[df_comp[col_nivel] == 'EXO'])
        
        html_ad += f"<div style='{row_style}'>{comp_name}={cant_ad}</div>" if cant_ad > 0 else f"<div style='{row_style}'>-</div>"
        html_a += f"<div style='{row_style}'>{comp_name}={cant_a}</div>" if cant_a > 0 else f"<div style='{row_style}'>-</div>"
        html_b += f"<div style='{row_style}'>{comp_name}={cant_b}</div>" if cant_b > 0 else f"<div style='{row_style}'>-</div>"
        html_c += f"<div style='{row_style}'>{comp_name}={cant_c}</div>" if cant_c > 0 else f"<div style='{row_style}'>-</div>"
        html_exo += f"<div style='{row_style}'>{comp_name}={cant_exo}</div>" if cant_exo > 0 else f"<div style='{row_style}'>-</div>"

    col_nombres.markdown(html_nombres, unsafe_allow_html=True)
    c1.markdown(html_ad, unsafe_allow_html=True)
    c2.markdown(html_a, unsafe_allow_html=True)
    c3.markdown(html_b, unsafe_allow_html=True)
    c4.markdown(html_c, unsafe_allow_html=True)
    c5.markdown(html_exo, unsafe_allow_html=True)

st.divider()

# --- ESTUDIANTES QUE REQUIEREN APOYO (C) ---
st.markdown("#### Estudiantes que requieren apoyo (C)")
df_apoyo = df_filtrado[df_filtrado[col_nivel] == 'C']

if not df_apoyo.empty:
    df_agrupado = df_apoyo.groupby(col_estudiante).agg({
        col_comp: lambda x: ', '.join(sorted(set(x)))
    }).reset_index()
    df_agrupado = df_agrupado.rename(columns={col_comp: 'COMPETENCIAS A MEJORAR'})
    st.dataframe(df_agrupado, hide_index=True, use_container_width=True)
else:
    st.info("No hay estudiantes con calificación 'C' en esta selección.")

st.divider()

# --- ESTUDIANTES EXONERADOS (EXO) ---
df_exo = df_filtrado[df_filtrado[col_nivel] == 'EXO']
if not df_exo.empty:
    st.markdown("#### Estudiantes Exonerados (EXO)")
    df_exo_agrupado = df_exo.groupby(col_estudiante).agg({
        col_comp: lambda x: ', '.join(sorted(set(x)))
    }).reset_index()
    df_exo_agrupado = df_exo_agrupado.rename(columns={col_comp: 'COMPETENCIAS EXONERADAS'})
    st.dataframe(df_exo_agrupado, hide_index=True, use_container_width=True)
    st.divider()

# --- SECCIÓN DE GRÁFICOS ORGANIZADA EN PESTAÑAS ---
st.markdown(f"**Visualizando Padrón General:** {area} | {grado} | {seccion}")

descripciones = {'AD': 'AD (Logro destacado)', 'A': 'A (Logro Esperado)', 'B': 'B (En Proceso)', 'C': 'C (En Inicio)', 'EXO': 'EXO (Exonerado)'}
colores_minedu = {'AD (Logro destacado)': '#1f77b4', 'A (Logro Esperado)': '#2ca02c', 'B (En Proceso)': '#ffcc00', 'C (En Inicio)': '#d62728', 'EXO (Exonerado)': '#808080'}
orden_niveles = ['AD (Logro destacado)', 'A (Logro Esperado)', 'B (En Proceso)', 'C (En Inicio)', 'EXO (Exonerado)']

# ¡NUEVA PESTAÑA COMPARATIVA!
tab_gen, tab_cant, tab_pct, tab_comp = st.tabs([
    "📊 Gráfico General", 
    "📊 Por Competencia", 
    "📈 Distribución %",
    "⚖️ Comparativo I vs II"
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

st.dataframe(df_filtrado.reset_index(drop=True), use_container_width=True)

# --- BOTÓN DE DESCARGA ---
st.divider()
st.markdown("### Exportar Datos")
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    df_filtrado.to_excel(writer, index=False, sheet_name='Reporte_Filtrado')
st.download_button(label="📥 Descargar reporte en Excel (.xlsx)", data=buffer.getvalue(), file_name='reporte_estudiantes_filtrado.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')