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

# Limpieza básica de datos
df = df[df[col_nivel].isin(['AD', 'A', 'B', 'C', 'EXO'])]

# --- BARRA LATERAL: NAVEGACIÓN Y FILTROS ---
with st.sidebar:
    st.image("escudo.png", width=120)
    st.title("Navegación")
    modo_vista = st.radio("Selecciona el módulo:", ["📊 Vista General", "👤 Perfil Individual"])
    
    st.divider()
    st.header("Filtros de Búsqueda")

df_base = df.copy()

# Filtros Globales (Área, Grado, Sección)
area = st.sidebar.selectbox("Área:", ["Todas"] + sorted(list(df_base[col_area].unique())))
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

# Orden lógico de bimestres
orden_b = ['I BIMESTRE', 'II BIMESTRE', 'III BIMESTRE', 'IV BIMESTRE']

# Diccionarios de formato MINEDU
descripciones = {'AD': 'AD (Logro destacado)', 'A': 'A (Logro Esperado)', 'B': 'B (En Proceso)', 'C': 'C (En Inicio)', 'EXO': 'EXO (Exonerado)'}
colores_minedu = {'AD (Logro destacado)': '#1f77b4', 'A (Logro Esperado)': '#2ca02c', 'B (En Proceso)': '#ffcc00', 'C (En Inicio)': '#d62728', 'EXO (Exonerado)': '#808080'}
orden_niveles = ['AD (Logro destacado)', 'A (Logro Esperado)', 'B (En Proceso)', 'C (En Inicio)', 'EXO (Exonerado)']

# ==========================================
# MÓDULO 1: VISTA GENERAL
# ==========================================
if modo_vista == "📊 Vista General":
    if col_bimestre:
        bimestres_disponibles = sorted(list(df_base[col_bimestre].unique()), key=lambda x: orden_b.index(x) if x in orden_b else 99)
        bimestre_seleccionado = st.sidebar.selectbox("Bimestre:", ["Consolidado (Todos)"] + bimestres_disponibles)
    else:
        bimestre_seleccionado = "I BIMESTRE"

    df_temp = df_base.copy()
    if bimestre_seleccionado != "Consolidado (Todos)" and col_bimestre:
        df_temp = df_temp[df_temp[col_bimestre] == bimestre_seleccionado]

    if col_comp:
        competencias_lista = sorted(list(df_temp[col_comp].dropna().unique()))
        competencias = st.sidebar.multiselect("Competencias:", competencias_lista, default=competencias_lista)
    else:
        competencias = []

    df_filtrado = df_temp.copy()
    if len(competencias) > 0 and col_comp:
        df_filtrado = df_filtrado[df_filtrado[col_comp].isin(competencias)]

    # Cabecera
    col_logo, col_titulo = st.columns([1, 4])
    with col_logo:
        st.image("escudo.png", width=120)
    with col_titulo:
        st.title("Panel Nivel de Logro de Aprendizaje")
        st.subheader(f"{bimestre_seleccionado}")
        st.markdown("### IE Nº 20393 Túpac Amaru - Pampa Libre")

    st.divider()

    # --- RESUMEN DEL NIVEL (Restaurado con Estudiantes Únicos) ---
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

    # --- TABLAS DE ALERTAS CON EXPANSORES ---
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        with st.expander("🟡 Ver estudiantes que requieren Apoyo Focalizado (2 a más 'C')"):
            df_apoyo = df_filtrado[df_filtrado[col_nivel] == 'C']
            if not df_apoyo.empty:
                df_agrupado = df_apoyo.groupby(col_estudiante).agg(
                    CANTIDAD_C=(col_comp, 'count'),
                    COMPETENCIAS_A_MEJORAR=(col_comp, lambda x: ', '.join(sorted(set(x))))
                ).reset_index()
                df_apoyo_focalizado = df_agrupado[df_agrupado['CANTIDAD_C'] >= 2]
                if not df_apoyo_focalizado.empty:
                    st.dataframe(df_apoyo_focalizado[[col_estudiante, 'COMPETENCIAS_A_MEJORAR']], hide_index=True, use_container_width=True)
                else:
                    st.success("✅ Ningún estudiante requiere apoyo focalizado (2 a más 'C') en esta selección.")
            else:
                st.success("✅ No hay estudiantes con calificación 'C' en esta selección.")

        with st.expander("⚪ Ver Estudiantes Exonerados (EXO)"):
            df_exo = df_filtrado[df_filtrado[col_nivel] == 'EXO']
            if not df_exo.empty:
                df_exo_agrupado = df_exo.groupby(col_estudiante).agg({col_comp: lambda x: ', '.join(sorted(set(x)))}).reset_index()
                df_exo_agrupado = df_exo_agrupado.rename(columns={col_comp: 'COMPETENCIAS EXONERADAS'})
                st.dataframe(df_exo_agrupado, hide_index=True, use_container_width=True)
            else:
                st.info("No hay estudiantes exonerados en esta selección.")

    with col_t2:
        if bimestre_seleccionado == "I BIMESTRE":
            with st.expander("🔴 Ver Alerta de Riesgo Crónico"):
                st.info("💡 Esta alerta se activa a partir del II Bimestre para medir estancamiento.")
        else:
            with st.expander("🔴 Ver Alerta de Riesgo Crónico (C Consecutivas)"):
                if col_bimestre and area != "Todas" and grado != "Todos" and seccion != "Todas":
                    # Filtro de estudiantes con C consecutivas en bimestres
                    df_b1_c = df_base[(df_base[col_bimestre] == 'I BIMESTRE') & (df_base[col_nivel] == 'C')]
                    df_b2_c = df_base[(df_base[col_bimestre] == 'II BIMESTRE') & (df_base[col_nivel] == 'C')]
                    df_cronicos = pd.merge(df_b1_c, df_b2_c, on=[col_estudiante, col_comp])
                    
                    if not df_cronicos.empty:
                        df_cronicos_agrupado = df_cronicos.groupby(col_estudiante).agg({col_comp: lambda x: ', '.join(sorted(set(x)))}).reset_index()
                        df_cronicos_agrupado = df_cronicos_agrupado.rename(columns={col_comp: 'COMPETENCIA EN RIESGO CRÓNICO'})
                        st.error("⚠️ Atención: Estudiantes estancados en nivel de inicio (C).")
                        st.dataframe(df_cronicos_agrupado, hide_index=True, use_container_width=True)
                    else:
                        st.success("✅ ¡Excelentes noticias! Ningún estudiante repite 'C' consecutivamente.")
                else:
                    st.info("Para ver el análisis de Riesgo Crónico, selecciona un Área, Grado y Sección específica.")

    st.divider()

    # --- PESTAÑAS (RESTAURADAS LAS 5 PESTAÑAS) ---
    st.markdown(f"**Visualizando Padrón General:** {area} | {grado} | {seccion}")

    tab_gen, tab_cant, tab_pct, tab_comp, tab_calor = st.tabs([
        "📊 Gráfico General", 
        "📊 Por Competencia", 
        "📈 Distribución %",
        "⚖️ Comparativo Bimestral",
        "🔥 Mapa de Calor del Salón"
    ])

    # 1. Gráfico General
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

    # 2. Por Competencia
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

    # 3. Distribución % (RESTAURADA)
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

    # 4. Comparativo Bimestral (ACTUALIZADO PARA I vs II vs III BIMESTRE)
    with tab_comp:
        if col_bimestre and bimestre_seleccionado == "Consolidado (Todos)":
            st.markdown("### Comparación de Niveles de Logro por Bimestre")
            conteo_comp = df_filtrado.groupby([col_bimestre, col_nivel]).size().reset_index(name='CANTIDAD')
            conteo_comp['LEYENDA'] = conteo_comp[col_nivel].map(descripciones)
            
            grafico_comparativo = alt.Chart(conteo_comp).mark_bar().encode(
                x=alt.X(f'{col_bimestre}:N', title='Bimestre', sort=orden_b, axis=alt.Axis(labelAngle=0)),
                y=alt.Y('CANTIDAD:Q', title='Número de Estudiantes'),
                color=alt.Color('LEYENDA:N', scale=alt.Scale(domain=list(colores_minedu.keys()), range=list(colores_minedu.values())), sort=orden_niveles, legend=alt.Legend(title="Significado")),
                xOffset=alt.XOffset('LEYENDA:N', sort=orden_niveles),
                tooltip=[col_bimestre, col_nivel, 'LEYENDA', 'CANTIDAD']
            ).properties(height=400)
            st.altair_chart(grafico_comparativo, use_container_width=True)
        else:
            st.info("💡 Para ver el gráfico comparativo bimestral, selecciona 'Consolidado (Todos)' en el filtro superior de Bimestre.")

    # 5. Mapa de Calor
    with tab_calor:
        if not df_filtrado.empty and col_comp:
            st.markdown("### Radiografía del Salón (Mapa de Calor)")
            st.caption("Analiza rápidamente el desempeño de cada estudiante. Pasa el cursor por los recuadros para ver detalles.")
            
            df_heat = df_filtrado.copy()
            if bimestre_seleccionado == "Consolidado (Todos)":
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

# ==========================================
# MÓDULO 2: PERFIL INDIVIDUAL (FASE 2)
# ==========================================
elif modo_vista == "👤 Perfil Individual":
    st.title("👤 Perfil Individual Diagnóstico")
    st.markdown("Busca a un estudiante para analizar su trayectoria de calificaciones a lo largo de los bimestres.")
    
    lista_estudiantes = sorted(list(df_base[col_estudiante].unique()))
    
    if len(lista_estudiantes) == 0:
        st.warning("⚠️ No se encontraron estudiantes con los filtros actuales de Área, Grado y Sección.")
    else:
        estudiante_seleccionado = st.selectbox("🔍 Seleccionar Estudiante:", lista_estudiantes)
        
        df_est = df_base[df_base[col_estudiante] == estudiante_seleccionado]
        
        bimestres_del_est = sorted(df_est[col_bimestre].unique(), key=lambda x: orden_b.index(x) if x in orden_b else 99)
        ultimo_bimestre = bimestres_del_est[-1] if bimestres_del_est else "Sin datos"
        
        st.subheader(f"Resumen de Calificaciones ({ultimo_bimestre})")
        df_ultimo = df_est[df_est[col_bimestre] == ultimo_bimestre]
        
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("🟢 Logro Destacado (AD)", len(df_ultimo[df_ultimo[col_nivel]=='AD']))
        c2.metric("✅ Logro Esperado (A)", len(df_ultimo[df_ultimo[col_nivel]=='A']))
        c3.metric("🟡 En Proceso (B)", len(df_ultimo[df_ultimo[col_nivel]=='B']))
        c4.metric("🔴 En Inicio (C)", len(df_ultimo[df_ultimo[col_nivel]=='C']))
        c5.metric("⚪ Exonerado (EXO)", len(df_ultimo[df_ultimo[col_nivel]=='EXO']))
        
        st.divider()
        st.subheader("📈 Trayectoria por Competencias (I, II y III Bimestre)")
        st.markdown("Compara el progreso del estudiante en cada competencia evaluada a lo largo del año.")
        
        pivot_df = df_est.pivot_table(
            index=[col_area, col_comp], 
            columns=col_bimestre, 
            values=col_nivel, 
            aggfunc='first'
        ).reset_index()
        
        cols_finales = [col_area, col_comp]
        for b in orden_b:
            if b in pivot_df.columns:
                cols_finales.append(b)
        pivot_df = pivot_df[cols_finales]
        
        def colorear_notas(val):
            if val == 'AD': return 'background-color: #1f77b4; color: white; text-align: center; font-weight: bold'
            elif val == 'A': return 'background-color: #2ca02c; color: white; text-align: center; font-weight: bold'
            elif val == 'B': return 'background-color: #ffcc00; color: black; text-align: center; font-weight: bold'
            elif val == 'C': return 'background-color: #d62728; color: white; text-align: center; font-weight: bold'
            return 'text-align: center'
        
        columnas_bimestres = [c for c in cols_finales if 'BIMESTRE' in c]
        
        st.dataframe(
            pivot_df.style.map(colorear_notas, subset=columnas_bimestres),
            use_container_width=True, 
            hide_index=True
        )

        st.markdown("<br>", unsafe_allow_html=True)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            pivot_df.to_excel(writer, index=False, sheet_name='Ficha_Diagnostica')
        
        st.download_button(
            label=f"📥 Descargar Ficha de {estudiante_seleccionado} (.xlsx)", 
            data=buffer.getvalue(), 
            file_name=f'Ficha_{estudiante_seleccionado.replace(" ", "_")}.xlsx', 
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )