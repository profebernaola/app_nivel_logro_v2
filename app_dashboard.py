import streamlit as st
import pandas as pd
import altair as alt

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

# Limpieza estricta: Reemplazo de EXO a A y filtrado de notas válidas
df[col_nivel] = df[col_nivel].replace('EXO', 'A')
df = df[df[col_nivel].isin(['AD', 'A', 'B', 'C'])]

# Cabecera con imagen a 150x150
col_logo, col_titulo = st.columns([1, 4])
with col_logo:
    st.image("escudo.png", width=150)
with col_titulo:
    # NUEVO TÍTULO Y SUBTÍTULO
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
if area != "Todas":
    df_filtrado = df_filtrado[df_filtrado[col_area] == area]
if grado != "Todos":
    df_filtrado = df_filtrado[df_filtrado[col_grado] == grado]
if seccion != "Todas":
    df_filtrado = df_filtrado[df_filtrado[col_seccion] == seccion]
if len(competencias) > 0 and col_comp:
    df_filtrado = df_filtrado[df_filtrado[col_comp].isin(competencias)]

# --- RESUMEN DEL NIVEL SEPARADO Y DETALLADO (ALINEADO) ---
st.markdown("### Resumen del NIVEL")

# Creamos 5 columnas: La primera para Estudiantes Únicos y Áreas, las otras 4 para los datos
col_nombres, c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1, 1])

# CONTEO EXACTO
total_estudiantes_unicos = df_filtrado[col_estudiante].nunique()

count_ad = len(df_filtrado[df_filtrado[col_nivel] == 'AD'])
count_a = len(df_filtrado[df_filtrado[col_nivel] == 'A'])
count_b = len(df_filtrado[df_filtrado[col_nivel] == 'B'])
count_c = len(df_filtrado[df_filtrado[col_nivel] == 'C'])

# Imprimimos las métricas principales
col_nombres.metric("Estudiantes Únicos", total_estudiantes_unicos)
c1.metric("Logro Destacado (AD)", count_ad)
c2.metric("Logro Esperado (A)", count_a)
c3.metric("En Proceso (B)", count_b)
c4.metric("En Inicio (C)", count_c)

# Título de la sección de desglose
col_nombres.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
col_nombres.markdown("<div style='font-size: 0.95rem; font-weight: 600; color: #31333F; margin-bottom: 5px;'>ÁREA Y COMPETENCIA</div>", unsafe_allow_html=True)

# Lógica para sincronizar las filas horizontalmente
if col_comp and not df_filtrado.empty:
    competencias_presentes = sorted(df_filtrado[col_comp].dropna().unique())
    
    html_nombres = ""
    html_ad = ""
    html_a = ""
    html_b = ""
    html_c = ""
    
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
        
        html_ad += f"<div style='{row_style}'>{comp_name}={cant_ad}</div>" if cant_ad > 0 else f"<div style='{row_style}'>-</div>"
        html_a += f"<div style='{row_style}'>{comp_name}={cant_a}</div>" if cant_a > 0 else f"<div style='{row_style}'>-</div>"
        html_b += f"<div style='{row_style}'>{comp_name}={cant_b}</div>" if cant_b > 0 else f"<div style='{row_style}'>-</div>"
        html_c += f"<div style='{row_style}'>{comp_name}={cant_c}</div>" if cant_c > 0 else f"<div style='{row_style}'>-</div>"

    col_nombres.markdown(html_nombres, unsafe_allow_html=True)
    c1.markdown(html_ad, unsafe_allow_html=True)
    c2.markdown(html_a, unsafe_allow_html=True)
    c3.markdown(html_b, unsafe_allow_html=True)
    c4.markdown(html_c, unsafe_allow_html=True)

st.divider()

# --- COLUMNA / SECCIÓN DE ESTUDIANTES QUE REQUIEREN APOYO ---
st.markdown("#### Estudiantes que requieren apoyo (C)")
df_apoyo = df_filtrado[df_filtrado[col_nivel] == 'C']

if not df_apoyo.empty:
    df_agrupado = df_apoyo.groupby(col_estudiante).agg({
        col_comp: lambda x: ', '.join(x)
    }).reset_index()
    df_agrupado = df_agrupado.rename(columns={col_comp: 'COMPETENCIAS A MEJORAR'})
    st.dataframe(df_agrupado, hide_index=True, use_container_width=True)
else:
    st.info("No hay estudiantes con calificación 'C' en esta selección.")

st.divider()

# Gráfico y Tabla General
st.markdown(f"**Visualizando Padrón General:** {area} | {grado} | {seccion}")

conteo_notas = df_filtrado[col_nivel].value_counts().reset_index()
conteo_notas.columns = ['NIVEL', 'CANTIDAD']

colores_minedu = {
    'AD': '#1f77b4',
    'A': '#2ca02c', 
    'B': '#ffcc00', 
    'C': '#d62728'  
}

grafico = alt.Chart(conteo_notas).mark_bar().encode(
    x=alt.X('NIVEL', sort=['AD', 'A', 'B', 'C'], title='Nivel de Logro', axis=alt.Axis(labelAngle=0)),
    y=alt.Y('CANTIDAD', title='Número de Estudiantes'),
    color=alt.Color('NIVEL', scale=alt.Scale(domain=list(colores_minedu.keys()), range=list(colores_minedu.values())), legend=None),
    tooltip=['NIVEL', 'CANTIDAD']
).properties(height=350)

st.altair_chart(grafico, use_container_width=True)

# Tabla General
st.dataframe(df_filtrado.reset_index(drop=True), use_container_width=True)

# Botón de Descarga
st.divider()
st.markdown("### Exportar Datos")

@st.cache_data
def convertir_df(df_a_convertir):
    return df_a_convertir.to_csv(index=False).encode('utf-8')

csv = convertir_df(df_filtrado)

st.download_button(
    label="📥 Descargar reporte filtrado (Excel/CSV)",
    data=csv,
    file_name='reporte_estudiantes_filtrado.csv',
    mime='text/csv',
)