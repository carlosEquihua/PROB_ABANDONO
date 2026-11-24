import pyodbc
import pandas as pd
import time
import numpy as np
import warnings

warnings.filterwarnings('ignore')

def obtener_conexion():
    driver_name = '{SQL Anywhere 17}' 
    server = 'svrsapiq' 
    port = '2638'
    database = 'dwh'
    username = 'GZA_USR_RED'
    password = 'Asezor624_2021'

    connection_string = f'DRIVER={driver_name};HOST={server}:{port};DBN={database};UID={username};PWD={password}'

    try:
        conn = pyodbc.connect(connection_string, autocommit=True)
        return conn
    except Exception as e:
        print(f"\n❌ Error al conectar: {e}")
        return None

def get_query(sql_query):
    conn = obtener_conexion()
    if conn is None: 
        print("No se pudo establecer la conexión a la base de datos.")
        return None   
    try:
        print(f"Ejecutando consulta...")
        df = pd.read_sql(sql_query, conn)
        df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
        return df
    except Exception as e:
        print(f"❌ Error al ejecutar query: {e}")
        return None
    finally:
        conn.close()
##
import time
import pandas as pd
import numpy as np
import re  

def crear_y_cargar_tabla_nueva(df, nombre_tabla_nueva):
    """
    Crea una tabla totalmente nueva en la base de datos basándose en la 
    estructura del DataFrame y carga los datos blindando nombres de columnas y nulos.
    """
    conn = obtener_conexion()
    if conn is None:
        print("No se pudo establecer la conexión a la base de datos.")
        return False
    
    mapa_tipos = {
        'int64': 'BIGINT',#BIGINT-INTEGER
        'float64': 'DOUBLE',
        'bool': 'BIT',
        'datetime64[ns]': 'TIMESTAMP',
        'object': 'VARCHAR(500)'
    }
    
    def limpiar_columna(nombre):
        # Sustituye cualquier caracter que no sea letra o número por "_"
        col_limpia = re.sub(r'[^a-zA-Z0-9_]', '_', str(nombre).strip())
        # Si empieza con un número, le agregamos una letra al inicio (ej. "2024_ventas" -> "c_2024_ventas")
        if col_limpia[0].isdigit():
            col_limpia = "c_" + col_limpia
        return col_limpia

    columnas_sql = []
    for col, dtype in df.dtypes.items():
        col_limpia = limpiar_columna(col)
        tipo_sql = mapa_tipos.get(str(dtype), 'VARCHAR(500)')
        columnas_sql.append(f"{col_limpia} {tipo_sql}")
    
    definicion_columnas = ", ".join(columnas_sql)
    sql_drop = f"DROP TABLE IF EXISTS {nombre_tabla_nueva};"
    sql_create = f"CREATE TABLE {nombre_tabla_nueva} ({definicion_columnas});"
    
    columnas_insert_list = [limpiar_columna(c) for c in df.columns]
    columnas_insert = ', '.join(columnas_insert_list)
    
    placeholders = ', '.join(['?'] * len(df.columns))
    sql_insert = f"INSERT INTO {nombre_tabla_nueva} ({columnas_insert}) VALUES ({placeholders})"
    
    df_limpio = df.replace([np.inf, -np.inf], np.nan)
    
    try:
        cursor_ddl = conn.cursor()
        print(f"Verificando si la tabla '{nombre_tabla_nueva}' ya existe para reemplazarla...")
        cursor_ddl.execute(sql_drop)
        print(f"Creando la tabla nueva '{nombre_tabla_nueva}'...")
        cursor_ddl.execute(sql_create)
        cursor_ddl.close()
        
        tamano_lote = 1000 
        total_filas = len(df_limpio)
        print(f"Cargando {total_filas} filas en lotes seguros de {tamano_lote}...")
        
        tiempo_inicio_total = time.time()
        
        for i in range(0, total_filas, tamano_lote):
            inicio_bloque = time.time()
            
            lote_df = df_limpio.iloc[i:i+tamano_lote]
            
            datos_a_insertar = []
            for row in lote_df.itertuples(index=False, name=None):
                fila_limpia = tuple(None if pd.isna(val) else val for val in row)
                datos_a_insertar.append(fila_limpia)
            
            cursor_insercion = conn.cursor()
            
            if len(lote_df) == tamano_lote:
                cursor_insercion.fast_executemany = True
            else:
                cursor_insercion.fast_executemany = False
                
            cursor_insercion.executemany(sql_insert, datos_a_insertar)
            cursor_insercion.close()
            
            fin_bloque = time.time()
            tiempo_bloque = fin_bloque - inicio_bloque
            
            filas_insertadas = min(i + tamano_lote, total_filas)
            print(f"✅ Bloque cargado ({filas_insertadas}/{total_filas} filas). Tiempo: {tiempo_bloque:.2f} seg.")
            
        tiempo_fin_total = time.time()
        tiempo_total_minutos = (tiempo_fin_total - tiempo_inicio_total) / 60
        
        print(f"\n🎉 Proceso completado. Tabla '{nombre_tabla_nueva}' creada y cargada con éxito en {tiempo_total_minutos:.2f} minutos.")
        return True
        
    except Exception as e:
        print(f"\n❌ Error durante el proceso: {e}")
        return False
        
    finally:
        conn.close()


def ejecutar_script_sql(script_sql):
    """
    Ejecuta bloques de código complejos en SQL Anywhere (declaración de variables, 
    tablas temporales, procedimientos almacenados) que no devuelven un DataFrame.
    """
    conn = obtener_conexion()
    if conn is None:
        print("No se pudo establecer la conexión a la base de datos.")
        return False 
        
    try:
        print("Ejecutando script complejo en la base de datos (esto puede tardar unos minutos)...")
        cursor = conn.cursor()
        
        # Enviar todo el bloque de SQL a la base de datos
        cursor.execute(script_sql)
        
        # OBLIGATORIO: Hacer commit para asegurar que las tablas creadas (como temp_insum1) se guarden
        cursor.commit()
        print("✅ Script ejecutado correctamente.")
        return True
        
    except Exception as e:
        print(f"❌ Error al ejecutar el script: {e}")
        return False
        
    finally:
        cursor.close()
        conn.close()


import os
import time
import pandas as pd
import numpy as np
import re

def crear_y_cargar_tabla_masiva(df, nombre_tabla_nueva, ruta_csv="carga_masiva.csv"):
    """
    Carga volúmenes masivos de datos (Big Data) usando un archivo CSV temporal 
    y el motor nativo de ingesta de la base de datos.
    """
    conn = obtener_conexion()
    if conn is None:
        print("No se pudo establecer la conexión a la base de datos.")
        return False
    
    # 1. Mapear tipos de datos de Pandas a SQL
    mapa_tipos = {
        'int64': 'INTEGER',
        'float64': 'DOUBLE',
        'bool': 'BIT',
        'datetime64[ns]': 'TIMESTAMP',
        'object': 'VARCHAR(500)'
    }
    
    def limpiar_columna(nombre):
        col_limpia = re.sub(r'[^a-zA-Z0-9_]', '_', str(nombre).strip())
        if col_limpia[0].isdigit():
            col_limpia = "c_" + col_limpia
        return col_limpia

    # 2. Construir dinámicamente el CREATE TABLE
    columnas_sql = []
    for col, dtype in df.dtypes.items():
        col_limpia = limpiar_columna(col)
        tipo_sql = mapa_tipos.get(str(dtype), 'VARCHAR(500)')
        columnas_sql.append(f"{col_limpia} {tipo_sql}")
    
    definicion_columnas = ", ".join(columnas_sql)
    sql_drop = f"DROP TABLE IF EXISTS {nombre_tabla_nueva};"
    sql_create = f"CREATE TABLE {nombre_tabla_nueva} ({definicion_columnas});"
    
    try:
        tiempo_inicio_total = time.time()
        
        # PASO A: Escribir el DataFrame en el disco duro (rápido y libera memoria)
        print(f"Paso 1: Escribiendo {len(df)} registros en el archivo local '{ruta_csv}'...")
        df_limpio = df.replace([np.inf, -np.inf], np.nan)
        df_limpio.to_csv(ruta_csv, index=False, header=False, na_rep='')
        
        # PASO B: Preparar la estructura en la base de datos
        print(f"Paso 2: Creando la tabla '{nombre_tabla_nueva}' en la base de datos...")
        cursor = conn.cursor()
        cursor.execute(sql_drop)
        cursor.execute(sql_create)
        
        # PASO C: Ingesta masiva (Bulk Load)
        print("Paso 3: Ordenando a la base de datos absorber el archivo completo...")
        ruta_absoluta = os.path.abspath(ruta_csv).replace('\\', '/')
        
        # ⚡ EL CAMBIO ESTÁ AQUÍ: "USING CLIENT FILE" en lugar de "FROM CLIENT FILE"
        # y eliminamos parámetros redundantes
        sql_load = f"""
        LOAD TABLE {nombre_tabla_nueva}
        USING CLIENT FILE '{ruta_absoluta}'
        DELIMITED BY ','
        ESCAPES OFF;
        """
        
        cursor.execute(sql_load)
        cursor.commit() # Forzamos que se guarden los cambios
        cursor.close()
        
        tiempo_fin_total = time.time()
        tiempo_total_minutos = (tiempo_fin_total - tiempo_inicio_total) / 60
        
        print(f"\n🎉 Proceso masivo completado. Tabla '{nombre_tabla_nueva}' cargada con éxito en {tiempo_total_minutos:.2f} minutos.")
        
        # PASO D: Limpiar la basura
        if os.path.exists(ruta_csv):
            os.remove(ruta_csv)
            print("🗑️ Archivo temporal CSV eliminado del disco.")
            
        return True
        
    except Exception as e:
        print(f"\n❌ Error durante el proceso masivo: {e}")
        return False
        
    finally:
        conn.close()