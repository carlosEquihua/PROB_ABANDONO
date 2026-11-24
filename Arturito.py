import pyodbc
import pandas as pd
import warnings
import os
import os
import duckdb

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

def get_query(sql_query, use_parquet=False, parquet_path="cache_query.parquet"):
    # 1. SI ESTÁ ACTIVADO PARQUET: Verificar si el archivo ya existe localmente
    if use_parquet and os.path.exists(parquet_path):
        print(f"📦 Cargando datos desde el archivo local: {parquet_path}...")
        try:
            df = pd.read_parquet(parquet_path)
            return df
        except Exception as e:
            print(f"⚠️ Error al leer el Parquet local, intentando conectar a la BD... Error: {e}")

    conn = obtener_conexion()
    if conn is None: 
        print("No se pudo establecer la conexión a la base de datos.")
        return None   
    try:
        print(f"Ejecutando consulta en la base de datos...")
        df = pd.read_sql(sql_query, conn)
        
        # NOTA: Eliminamos el df.map(lambda...) para evitar el desborde de memoria.
        # Recuerda agregar TRIM(da.Descripcion) en tu consulta de SQL si es necesario.

        # 3. SI PARQUET ESTÁ ACTIVADO: Guardar el resultado para futuras ejecuciones
        if use_parquet:
            print(f"💾 Guardando respaldo en Parquet: {parquet_path}...")
            df.to_parquet(parquet_path, index=False)

        return df
    except Exception as e:
        print(f"❌ Error al ejecutar query: {e}")
        return None
    finally:
        conn.close()
#
import os
import pyodbc
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd

def get_query_duckdb(sql_query, use_parquet=False, parquet_path="cache_query.parquet", return_df=False):
    """
    Función de extracción por lotes de alto rendimiento sin saturar RAM.
    """
    if use_parquet and os.path.exists(parquet_path) and return_df:
        print(f"📦 Cargando datos desde archivo local Parquet: {parquet_path}...")
        try:
            return pd.read_parquet(parquet_path)
        except Exception as e:
            print(f"⚠️ Error al leer Parquet local: {e}")

    clean_query = sql_query.strip()
    if not clean_query.upper().startswith("SELECT"):
        clean_query = f"SELECT * FROM {clean_query}"

    conn_str = (
        "DRIVER={SQL Anywhere 17};"
        "HOST=svrsapiq:2638;"
        "DBN=dwh;"
        "UID=GZA_USR_RED;"
        "PWD=Asezor624_2021;"
    )

    print("🔌 Conectando a SAP IQ vía ODBC...")
    conn = pyodbc.connect(conn_str, autocommit=True)
    cursor = conn.cursor()
    
    # CLAVE DE VELOCIDAD: Búfer de 500,000 registros por paquete de red
    chunk_size = 500000
    cursor.arraysize = chunk_size 

    print(f"🚀 Ejecutando consulta en SAP IQ...")
    cursor.execute(clean_query)

    if not use_parquet:
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return pd.DataFrame.from_records(rows, columns=columns)

    print(f"💾 Escribiendo directamente a Parquet por lotes: {parquet_path}...")
    writer = None
    total_filas = 0

    try:
        columns = [column[0] for column in cursor.description]
        
        while True:
            rows = cursor.fetchmany(chunk_size)
            if not rows:
                break
            
            # Convertir el lote a PyArrow Table directamente
            dict_data = {col: [row[i] for row in rows] for i, col in enumerate(columns)}
            arrow_table = pa.Table.from_pydict(dict_data)

            if writer is None:
                writer = pq.ParquetWriter(parquet_path, arrow_table.schema, compression='snappy')
            
            writer.write_table(arrow_table)
            total_filas += len(rows)
            print(f"📦 Procesadas {total_filas:,} filas acumuladas...")

        tamano_gb = round(os.path.getsize(parquet_path) / (1024**3), 2)
        print(f"✅ ¡Exportación finalizada! Total filas: {total_filas:,} | Tamaño: {tamano_gb} GB")

    finally:
        if writer:
            writer.close()
        conn.close()

    if return_df:
        return pd.read_parquet(parquet_path)
    return parquet_path