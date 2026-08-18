import pandas as pd
import os

def extraer_datos_excel(file_path, sheet_name, bimestre_label):
    print(f"Procesando: {file_path} ...")
    if not os.path.exists(file_path):
        print(f"  -> ADVERTENCIA: No se encontró el archivo '{file_path}'. Saltando...")
        return pd.DataFrame()
        
    try:
        df_raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
    except Exception as e:
        print(f"  -> Error al leer la hoja '{sheet_name}'. Detalle: {e}")
        return pd.DataFrame()

    row5 = df_raw.iloc[5].tolist()
    row6 = df_raw.iloc[6].tolist()

    mapping = []
    current_area = None
    for i in range(len(row5)):
        val5 = str(row5[i]).strip() if pd.notna(row5[i]) else ""
        val6 = str(row6[i]).strip() if pd.notna(row6[i]) else ""
        
        if val5 and val5 not in ['ITEM', 'APELLIDOS Y NOMBRES', 'GRADO', 'SECCION', 'NIVEL DE LOGRO DE APRENDIZAJE']:
            current_area = val5
        
        if val6 in ['C1', 'C2', 'C3', 'C4']:
            mapping.append({'col_index': i, 'area': current_area, 'comp': val6})

    data_rows = []
    for index, row in df_raw.iloc[7:].iterrows():
        estudiante = row[1]
        grado = row[2]
        seccion = row[3]
        
        if pd.isna(estudiante) or str(estudiante).strip() == "":
            continue 
            
        for m in mapping:
            nota = row[m['col_index']]
            if pd.notna(nota) and str(nota).strip() != "":
                area_clean = str(m['area']).replace("  ", " ").strip()
                comp_combined = f"{area_clean}_{m['comp']}"
                nota_limpia = str(nota).strip().upper()
                
                if nota_limpia in ['AD', 'A', 'B', 'C', 'EXO']:
                    data_rows.append({
                        'ESTUDIANTE': str(estudiante).strip(),
                        'GRADO': str(grado).strip(),
                        'SECCION': str(seccion).strip(),
                        'AREA': area_clean,
                        'COMPETENCIA': comp_combined,
                        'NIVEL_DE_LOGRO': nota_limpia,
                        'BIMESTRE': bimestre_label # <-- ¡EL NUEVO DATO ESTRELLA!
                    })
                    
    return pd.DataFrame(data_rows)

def procesar_excel_a_csv():
    # 1. Configurar los dos archivos
    file_1 = "CONSOLIDADO NIVEL DEL LOGRO DE LOS APRENDIZAJE - I BIMESTRE - 2026.xlsx"
    sheet_1 = "DATA_I_BIMESTRE_2026"
    
    file_2 = "CONSOLIDADO NIVEL DEL LOGRO DE LOS APRENDIZAJE - II BIMESTRE - 2026.xlsx"
    sheet_2 = "DATA_II_BIMESTRE_2026"
    
    # 2. Extraer datos de ambos
    df_bim1 = extraer_datos_excel(file_1, sheet_1, "I BIMESTRE")
    df_bim2 = extraer_datos_excel(file_2, sheet_2, "II BIMESTRE")
    
    # 3. Unir todo en una sola super-tabla
    df_final = pd.concat([df_bim1, df_bim2], ignore_index=True)
    
    if df_final.empty:
        print("Error: No se procesó ningún dato. Verifica los nombres de tus archivos.")
        return

    # 4. Generar el nuevo archivo consolidado
    output_csv = "BD_Dashboard_Consolidado.csv"
    df_final.to_csv(output_csv, index=False, encoding='utf-8-sig')
    
    print(f"\n¡Éxito total! Se procesaron {len(df_final)} calificaciones uniendo ambos bimestres.")
    print(f"Se ha creado el archivo maestro: '{output_csv}'")

if __name__ == "__main__":
    print("--- INICIANDO PROCESAMIENTO DE BIMESTRES ---")
    procesar_excel_a_csv()