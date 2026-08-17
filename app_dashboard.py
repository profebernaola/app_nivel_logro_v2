import streamlit as st
import pandas as pd
import plotly.express as px
import io

# Configuración de la página
st.set_page_config(page_title="Panel Nivel de Logro de Aprendizaje", layout="wide")
st.sidebar.header("Filtros de Búsqueda")

@st.cache_data
def cargar_datos():
    df = pd.read_csv("BD_Dashboard_IBimestre.csv")
    return df

try:
    df = cargar_datos()
except FileNotFoundError:
    st.error("No se encontró el archivo 'BD_Dashboard_IBimestre.csv'.")
    st.stop()

# Detección de columnas
columnas = df.columns.tolist()
col_area = next((c for c in columnas if c.upper() in ['AREA', 'ÁREA']), columnas[0])
col_grado = next((c for c in columnas if c.upper() == 'GRADO'), columnas[1])
col_seccion = next((c for c in columnas if c.upper() in ['SECCION', 'SECCIÓN']), columnas[2])
col_comp = next((c for c in columnas if 'COMPETENCIA' in c.upper()), columnas[3] if len(columnas)>3 else None)
col_nivel = next((c for c in columnas if 'NIVEL' in c.upper()), 'NIVEL_DE_LOGRO')
col_estudiante = next((c for c in columnas if 'ESTUDIANTE' in c.upper()), 'ESTUDIANTE')

# Limpieza
df[col_nivel] = df[col_nivel].replace('EXO', 'A')
df = df[df[col_nivel].isin(['AD', 'A', 'B', 'C'])]

# Cabecera
col_logo, col_titulo = st.columns([1, 4])
with col_logo:
    st.image("escudo.png", width=150)
with col_titulo:
    st.title("Panel Nivel de Logro de Aprendizaje")
    st.subheader("I BIMESTRE")
    st.markdown("### IE Nº 20393 Túpac Amaru - Pampa Libre")

st.divider()

# Filtros
area = st.sidebar.selectbox("Área:", ["Todas"] + list(df[col_area].unique()))
grado = st.sidebar.selectbox("Grado:", ["Todos"] + list(df[col_grado].unique()))
seccion = st.sidebar.selectbox("Sección:", ["Todas"] + list(df[col_seccion].unique()))

if col_comp:
    competencias_lista = list(df[col_comp].unique())
    competencias = st.sidebar.multiselect("Competencias:", competencias_lista, default=competencias_lista)
else:
    competencias = []

# Aplicar filtros
df_filtrado = df.copy()
if area != "Todas": df_filtrado = df_filtrado[df_filtrado[col_area] == area]
if grado != "Todos": df_filtrado = df_filtrado[df_filtrado[col_grado] == grado]
if seccion != "Todas": df_filtrado = df_filtrado[df_filtrado[col_seccion] == seccion]
if len(competencias) > 0 and col_comp: df_filtrado = df_filtrado[df_filtrado[col_comp].isin(competencias)]

# --- RESUMEN ---
st.markdown("### Resumen del NIVEL")
col_nombres, c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1, 1])

total_estudiantes_unicos = df_filtrado[col_estudiante].nunique()
count_ad = len(df_filtrado[df_filtrado[col_nivel] == 'AD'])
count_a = len(df_filtrado[df_filtrado[col_nivel] == 'A'])
count_b = len(df_filtrado[df_filtrado[col_nivel] == 'B'])
count_c = len(df_filtrado[df_filtrado[col_nivel] == 'C'])

col_nombres.metric("Estudiantes Únicos", total_estudiantes_unicos)
c1.metric("Logro Destacado (AD)", count_ad)
c2.metric("Logro Esperado (A)", count_a)
c3.metric("En Proceso (B)", count_b)
c4.metric("En Inicio (C)", count_c)

# Desglose Competencias
col_nombres.markdown("<br><div style='font-size: 0.95rem; font-weight: 600; color: #31333F;'>ÁREA Y COMPETENCIA</div>", unsafe_allow_html=True)
if col_comp and not df_filtrado.empty:
    competencias_presentes = sorted(df_filtrado[col_comp].dropna().unique())
    html_nombres = ""; html_ad = ""; html_a = ""; html_b = ""; html_c = ""
    for comp in competencias_presentes:
        df_comp = df_filtrado[df_filtrado[col_comp] == comp]
        area_name = df_comp[col_area].iloc[0] if not df_comp.empty else "Área"
        comp_name = str(comp).split('_')[-1] if '_' in str(comp) else str(comp)
        row_style = "font-size: 0.90rem; color: #4F4F4F; height: 22px;"
        html_nombres += f"<div style='{row_style} font-weight: 600;'>{area_name} ({comp_name})</div>"
        for cant, target in [(len(df_comp[df_comp[col_nivel]==niv]), var) for niv, var in [('AD', html_ad), ('A', html_a), ('B', html_b), ('C', html_c)]]:
            # Esta parte se simplifica para la lógica de visualización:
            pass 
        # (Lógica simplificada para brevedad)
        html_ad += f"<div style='{row_style}'>{comp_name}={len(df_comp[df_comp[col_nivel]=='AD'])}</div>"
        html_a += f"<div style='{row_style}'>{comp_name}={len(df_comp[df_comp[col_nivel]=='A'])}</div>"
        html_b += f"<div style='{row_style}'>{comp_name}={len(df_comp[df_comp[col_nivel]=='B'])}</div>"
        html_c += f"<div style='{row_style}'>{comp_name}={len(df_comp[df_comp[col_nivel]=='C'])}</div>"

    col_nombres.markdown(html_nombres, unsafe_allow_html=True)
    c1.markdown(html_ad, unsafe_allow_html=True)
    c2.markdown(html_a, unsafe_allow_html=True)
    c3.markdown(html_b, unsafe_allow_html=True)
    c4.markdown(html_c, unsafe_allow_html=True)

st.divider()

# --- GRÁFICO ESTILO 3D (PLOTLY) ---
st.markdown("### Gráfico de Rendimiento")
conteo_notas = df_filtrado[col_nivel].value_counts().reset_index()
conteo_notas.columns = ['NIVEL', 'CANTIDAD']
# Crear gráfico 3D estilizado
fig = px.bar(conteo_notas, x='NIVEL', y='CANTIDAD', color='NIVEL',
             color_discrete_map={'AD':'blue', 'A':'green', 'B':'yellow', 'C':'red'},
             category_orders={'NIVEL': ['AD', 'A', 'B', 'C']})
fig.update_traces(marker_line_width=2, opacity=0.8) # Efecto visual de profundidad
st.plotly_chart(fig, use_container_width=True)

# --- BOTONES DE DESCARGA ---
st.divider()
st.markdown("### Exportar Datos")
col_csv, col_xlsx = st.columns(2)

# CSV
csv = df_filtrado.to_csv(index=False).encode('utf-8')
col_csv.download_button("📥 Descargar CSV", csv, 'reporte.csv', 'text/csv')

# EXCEL
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    df_filtrado.to_excel(writer, index=False)
col_xlsx.download_button("📥 Descargar Excel (xlsx)", buffer.getvalue(), 'reporte.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')