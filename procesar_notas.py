import pandas as pd

def procesar_excel_a_csv():
    # Nombre de tu nuevo archivo consolidado
    file_path = "CONSOLIDADO NIVEL DEL LOGRO DE LOS APRENDIZAJE - I BIMESTRE - 2026.xlsx"
    
    print(f"Leyendo el archivo: {file_path} ...")
    
    try:
        # Leemos el archivo sin encabezados fijos para navegar por la estructura
        df_raw = pd.read_excel(file_path, sheet_name='DATA_I_BIMESTRE_2026', header=None)
    except Exception as e:
        print(f"Error al leer el Excel. Verifica que el nombre sea exacto y esté en la misma carpeta.")
        print(f"Detalle del error: {e}")
        return

    # Extraer las Áreas (Fila 6 en Excel -> índice 5) y Competencias (Fila 7 -> índice 6)
    row5 = df_raw.iloc[5].tolist()
    row6 = df_raw.iloc[6].tolist()

    mapping = []
    current_area = None
    for i in range(len(row5)):
        val5 = str(row5[i]).strip() if pd.notna(row5[i]) else ""
        val6 = str(row6[i]).strip() if pd.notna(row6[i]) else ""
        
        # Identificar el Área
        if val5 and val5 not in ['ITEM', 'APELLIDOS Y NOMBRES', 'GRADO', 'SECCION', 'NIVEL DE LOGRO DE APRENDIZAJE']:
            current_area = val5
        
        # Identificar la Competencia (C1, C2, C3 o C4)
        if val6 in ['C1', 'C2', 'C3', 'C4']:
            mapping.append({'col_index': i, 'area': current_area, 'comp': val6})

    print(f"Se detectaron {len(mapping)} columnas de competencias.")

    # Procesar las calificaciones desde la fila 8 (índice 7 en Python)
    data_rows = []
    for index, row in df_raw.iloc[7:].iterrows():
        estudiante = row[1]
        grado = row[2]
        seccion = row[3]
        
        # Ignorar filas en blanco
        if pd.isna(estudiante) or str(estudiante).strip() == "":
            continue 
            
        # Extraer nota por nota
        for m in mapping:
            nota = row[m['col_index']]
            
            # Si la celda tiene una nota...
            if pd.notna(nota) and str(nota).strip() != "":
                area_clean = str(m['area']).replace("  ", " ").strip() # Limpieza de espacios extra
                comp_combined = f"{area_clean}_{m['comp']}"
                nota_limpia = str(nota).strip().upper()
                
                # Filtrar solo notas válidas
                if nota_limpia in ['AD', 'A', 'B', 'C', 'EXO']:
                    data_rows.append({
                        'ESTUDIANTE': str(estudiante).strip(),
                        'GRADO': str(grado).strip(),
                        'SECCION': str(seccion).strip(),
                        'AREA': area_clean,
                        'COMPETENCIA': comp_combined,
                        'NIVEL_DE_LOGRO': nota_limpia
                    })

    # Convertir a formato tabla y generar el archivo
    df_clean = pd.DataFrame(data_rows)
    output_csv = "BD_Dashboard_IBimestre.csv"
    
    # Usamos utf-8-sig para que Excel respete las tildes (como en COMUNICACIÓN)
    df_clean.to_csv(output_csv, index=False, encoding='utf-8-sig')
    
    print(f"\n¡Éxito! Se procesaron {len(df_clean)} calificaciones en total.")
    print(f"El archivo '{output_csv}' ha sido actualizado y está listo para Streamlit.")

if __name__ == "__main__":
    procesar_excel_a_csv()