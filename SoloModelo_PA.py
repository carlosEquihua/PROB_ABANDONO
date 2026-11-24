#LIGHTGBM
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.metrics import confusion_matrix, roc_auc_score
import Arturito as Ar
import Automata as au
from datetime import datetime
from dateutil.relativedelta import relativedelta
from lightgbm import LGBMClassifier

# =========================================================
# BLOQUE 0: PARÁMETROS Y CONFIGURACIÓN GENERAL (NUEVO)
# =========================================================
# Rutas Base (Facilita la migración entre equipos)
BASE_DIR = r"C:/Users/cequihua/Documents/Anslytics/Anslytics/Probabilidad_Abandono"

MES_EJECUCION = "202610"
#MES_EJECUCION = (datetime.now() - relativedelta(months=1)).strftime("%Y%m")

# Umbrales y Parámetros de Negocio
#UMBRAL_RIESGO_CRITICO = 0.80  # Riesgo inminente interno
DIAS_INACTIVIDAD_CRITICA = 90   # 3 meses sin comprar
UMBRAL_IRF_NORMAL = 1.2         # Límite superior del rango "Normal (1.0-1.2)"
PISO_PA_INACTIVO = 0.97         # Probabilidad mínima asignada por inactividad fuera de ciclo
UMBRAL_RIESGO_REPORTE = 0.70  # Corte para reportes de sucursales
INDICE_FUGA_TARGET = 2.0      # Corte para clasificar como abandono

# Pesos del Scorecard A (Nuevas Variables)
W_CAT, W_LEA, W_VEN = 0.20, 0.15, 0.20
W_MAR, W_REC = 0.10, -0.05
W_MOM, W_FUG = 0.20, -0.10

# Pesos del Scorecard B (Tradicional)
W_TRAD = np.array([0.3, 0.25, 0.25, 0.1, -0.1])

# Hiperparámetros de Modelos IA
KMEANS_CLUSTERS = 7
RF_ESTIMATORS = 150
RF_MAX_DEPTH = 15
RF_MIN_LEAF = 5
#Query
query_sql = "SELECT * FROM TEMP_CAEL_HIST_3_OCTUBRE"
query_sql2 = "SELECT * FROM BI_Octubre_class"
#Columnas finales 
columnas_finales = {
    'Mes Ejecucion': 'Mes Ejecucion', 'Ranking': 'Ranking', 'clave': 'Cliente RED',
    'Nueva Clasificacion Cliente': 'Nueva Clasificacion Cliente', 'Segmentacion Clientes': 'Segmentacion Clientes',
    'categorias': 'Variedad Categoria', 'skus': 'Variedad SKU', 'meses_compra': 'Frecuencia en Meses',
    'dias_compra': 'Frecuencia en Dias', 'venta_neta': 'Venta Acumulada', 'costo': 'Costo Acumulado',
    'transacciones': 'Notas Acumuladas', 'Com_Mens_Prom':'Promedio de Venta Mensual', 'Dias_prom':'Frecuencia en Dias Mensual',
    'Margen': 'Margen', 'Margen Financiero': 'Margen Financiero', 'mesulti': 'Mes Ultima Compra',
    'suc': 'Suc Mayor Compra', 'venta_trimestral': 'Venta Trimestre', 'Notas al dia ': 'Notas al dia',
    'Ultima_compra': 'Ultima Comprar', 'DiasUltimaCompra': 'Dias Ultima Compra', 'Lealtad': 'Lealtad',
    'fec_alta': 'Dia Alta', 'Tiempo_Zorro': 'Tiempo Zorro', 'Venta_Acumulada_Mes': 'Venta Acumulada Ultimo Mes',
    'RECENCY': 'RECENCY', 'FRECUENCY': 'FRECUENCY', 'MONETARY': 'MONETARY', 'RFM': 'RFM',
    'P Variedad Categoria': 'P Variedad Categoria', 'P Lealtad': 'P Lealtad', 'P Venta Acumulada': 'P Venta Acumulada', 'P Margen Financiero': 'P Margen Financiero', 'P Recencia': 'P Recencia', 'P Momentum': 'P Momentum', 'P Riesgo Fuga': 'P Riesgo Fuga',
    'C Variedad Categoria': 'C Variedad Categoria', 'C Lealtad': 'C Lealtad', 'C Venta Acumulada': 'C Venta Acumulada', 'C Margen Financiero': 'C Margen Financiero', 'C Recencia': 'C Recencia', 'C Momentum': 'C Momentum', 'C Riesgo Fuga': 'C Riesgo Fuga',
    'Calificacion': 'Calificacion', 'Momentum_Venta': 'Momentum Venta', 
    'Indice_Fuga': 'Indice de Riesgo Fuga',
    'Segmento_Vida': 'Segmento de Madurez (Tiempo Zorro)', 
    'Cluster_Natural': 'Cluster Diagnostico (IA)',
    'Cuadrante_PA_IRF': 'Diagnostico Cuadrante',
    'Ranking_Tradicional': 'Ranking Sin Momentum',
    'Diferencia_Ranking': 'Diferencia de Ranking',
    'Accion_Sugerida': 'Accion Estrategica Sugerida',
    'Probabilidad_Abandono': 'Probabilidad Abandono',
    'Probabilidad_Recompra': 'Probabilidad Recompra',
    'Ciclo_Compra_Dias': 'Ciclo Natural (Dias)',
    'Fecha_Prox_Compra_Est': 'Fecha Estimada Recompra',
    'Dias_Para_Prox_Compra': 'Dias Para Recompra',
    'Estatus_Recompra': 'Estatus Recompra',
    'Categorias_Antes':'Categorias Consumo Historico (Antes)',
    'Categorias_Ahora': 'Categorias Consumo Actual (Ahora)'
}

# En Mapa_final (resumen ejecutivo):
Mapa_final = [
    'Mes Ejecucion','Cliente RED','Venta Acumulada', 'Notas Acumuladas','Suc Mayor Compra','Ultima Comprar','Dias Ultima Compra',
    'Nueva Clasificacion Cliente','Segmentacion Clientes','Cluster Diagnostico (IA)',
    'Diagnostico Cuadrante','Indice de Riesgo Fuga','Probabilidad Abandono',
    'Probabilidad Recompra','Fecha Estimada Recompra','Dias Para Recompra','Estatus Recompra',
    'Accion Estrategica Sugerida'
]

#Venta Acumulada, Notas Acumuladas,Suc Mayor Compra,Ultima Comprar
Mapa_final = [
    'Mes Ejecucion','Cliente RED','Venta Acumulada', 'Notas Acumuladas','Suc Mayor Compra','Ultima Comprar','Dias Ultima Compra',
    'Nueva Clasificacion Cliente','Segmentacion Clientes','Cluster Diagnostico (IA)',
    'Diagnostico Cuadrante','Indice de Riesgo Fuga','Probabilidad Abandono','Probabilidad Recompra',
    'Fecha Estimada Recompra','Dias Para Recompra','Estatus Recompra','Accion Estrategica Sugerida'
]


# Leemos la tabla
dq = Ar.get_query(query_sql, use_parquet=True, parquet_path="Historico_clientes_V1_OCTUBRE.parquet")

# =========================================================
# BLOQUE 1: CONFIGURACIÓN DE RUTAS E INSUMOS
# =========================================================
#pathdf = os.path.join(BASE_DIR, "Paso 1", f"Ranking_File_{MES_EJECUCION}.txt")
#pathvar = os.path.join(BASE_DIR, "Paso 1", f"Variables_Tiempo_{MES_EJECUCION}.txt")
#pathspending = os.path.join(BASE_DIR, "Paso 1", f"Gasto_Final_{MES_EJECUCION}.txt")

path_reporte_maestro = os.path.join(BASE_DIR, f"Clientes_Clasificacion_octubre_2026_Final.csv")
path_reporte_sucursales = os.path.join(BASE_DIR, "Reporte_Riesgo_Semanal_Sucursales_octubre.csv")
folder_sucursales = os.path.join(BASE_DIR, "Alertas_Sucursales_octubre")

#print("Cargando e integrando insumos...")
#BASE_DIR = r"C:/Users/cequihua/Documents/Anslytics/ClasificacionDeClientes/Clasificacion Cts"
#df_base = pd.read_csv(pathdf, sep="\t", encoding='latin-1')
#df_var = pd.read_csv(pathvar, sep="\t", encoding='latin-1')
#df_spending = pd.read_csv(pathspending, sep="\t", encoding='latin-1')

#for d in [df_base, df_var, df_spending]:
#    c = 'clave' if 'clave' in d.columns else 'ClaveCliente'
#    d[c] = d[c].astype(str).str.zfill(9)

#df = pd.merge(df_base, df_var, how="left", left_on='clave', right_on='ClaveCliente')
#df = pd.merge(df, df_spending, how="left", left_on='clave', right_on='ClaveCliente').fillna(0)

#del df_base, df_var, df_spending
#query_sql = "SELECT * FROM TEMP_CAEL_HIST_3_Enero"TEMP_CAEL_HIST_3_JUNIO
df = Ar.get_query(query_sql2, use_parquet=True, parquet_path="Clasificacion_V1_OCTUBRE.parquet")
df = df[df['clave'] != '000000001'].reset_index(drop=True)

# =========================================================
# BLOQUE 2: MÉTRICAS DE NEGOCIO Y VARIABLES PREDICTIVAS
# =========================================================
print("Calculando métricas de negocio...")
df["Margen Financiero"] = df["venta_neta"] - df["costo"]
df["Margen"] = (df["Margen Financiero"] / df["venta_neta"].replace(0, np.nan)).fillna(0)
df["Margen evaluar"] = df["Margen Financiero"].clip(lower=0)
df["Lealtad"] = df["dias_compra"] / (df["meses_compra"] * 30).replace(0, np.nan)
df["Notas al dia "] = df["transacciones"] / df["dias_compra"].replace(0, np.nan)

df['Venta_Promedio_Mensual_Trim'] = df['venta_trimestral'] / 3
df['Momentum_Venta'] = (df['Venta_Acumulada_Mes'] / df['Venta_Promedio_Mensual_Trim'].replace(0, np.nan)).fillna(0).clip(upper=3)
# =========================================================
# AJUSTE IRF (RELOJ NATURAL DE CICLOS DE COMPRA)
# =========================================================
# 1. Calculamos el ciclo real en días (Ej. 30 días / 4 visitas al mes = compra cada 7.5 días)
df['Ciclo_Compra_Dias'] = 30 / df['Dias_prom'].replace(0, np.nan)

# 2. Establecemos límites para evitar ciclos irreales (piso de 7 días, tope de 45 días)
df['Ciclo_Compra_Dias'] = df['Ciclo_Compra_Dias'].clip(lower=7, upper=45)

# 3. Calculamos el IRF Real (Días de ausencia / Ciclo natural en días del cliente)
df['Indice_Fuga'] = (
    (df['DiasUltimaCompra'] / df['Ciclo_Compra_Dias']).fillna(0).clip(upper=5)
)

# 4. Regla de seguridad original: Si lleva menos de 7 días sin comprar, 
# forzamos su IRF a máximo 1.0 (Sin Riesgo Operativo de Fuga aún).
df['Indice_Fuga'] = np.where(
    df['DiasUltimaCompra'] < 7,
    np.minimum(df['Indice_Fuga'], 1.0),
    df['Indice_Fuga'],
)
condiciones_madurez = [(df['Tiempo_Zorro'] <= 365), (df['Tiempo_Zorro'] > 365) & (df['Tiempo_Zorro'] <= 1095), (df['Tiempo_Zorro'] > 1095)]
df['Segmento_Vida'] = np.select(condiciones_madurez, ['NUEVO', 'FIDELIZADO', 'HISTORICO'], default='DESCONOCIDO')
df = df.fillna(0)

df["RECENCY"] = pd.qcut(df["DiasUltimaCompra"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
df["MONETARY"] = pd.qcut(df['venta_neta'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5]).astype(int)
df["FRECUENCY"] = pd.qcut(df['dias_compra'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5]).astype(int)
df["RFM"] = df["RECENCY"].astype(str) + df["FRECUENCY"].astype(str) + df["MONETARY"].astype(str)

# =========================================================
# BLOQUE 3: ESTANDARIZACIÓN Y SCORECARD
# =========================================================
print("Generando Scorecard y Matrices de Ranking...")
variables_z = ['categorias', 'Lealtad', 'venta_neta', 'Margen evaluar', 'DiasUltimaCompra', 'Momentum_Venta', 'Indice_Fuga']
scaler = StandardScaler()
df_zscores = pd.DataFrame(scaler.fit_transform(df[variables_z]), columns=['Z' + col for col in variables_z])
df = pd.concat([df, df_zscores], axis=1)

nuevas_columnas_scorecard = {
    'C Variedad Categoria': df['Zcategorias'] * W_CAT,
    'C Lealtad': df['ZLealtad'] * W_LEA,
    'C Venta Acumulada': df['Zventa_neta'] * W_VEN,
    'C Margen Financiero': df['ZMargen evaluar'] * W_MAR,
    'C Recencia': df['ZDiasUltimaCompra'] * W_REC,
    'C Momentum': df['ZMomentum_Venta'] * W_MOM,
    'C Riesgo Fuga': df['ZIndice_Fuga'] * W_FUG
}
df = df.assign(**nuevas_columnas_scorecard)

df['Calificacion'] = (
    df['C Variedad Categoria'] + df['C Lealtad'] + df['C Venta Acumulada'] + 
    df['C Margen Financiero'] + df['C Recencia'] + df['C Momentum'] + df['C Riesgo Fuga']
).round(4)

df = df.sort_values(by='Calificacion', ascending=False).reset_index(drop=True)
df['Ranking'] = df.index + 1

variables_tradicionales = ['Zcategorias', 'ZLealtad', 'Zventa_neta', 'ZMargen evaluar', 'ZDiasUltimaCompra']
df['Calificacion_Tradicional'] = df[variables_tradicionales].dot(W_TRAD)
df['Ranking_Tradicional'] = df['Calificacion_Tradicional'].rank(ascending=False, method='first').astype(int)
df['Diferencia_Ranking'] = df['Ranking_Tradicional'] - df['Ranking']

total_reg = len(df)
clasf_corte = round(total_reg * 0.275)
c_top = round(clasf_corte * 0.05)
c_pre = round((clasf_corte * 0.15) + c_top)
c_bla = round((clasf_corte * 0.35) + c_pre)
c_gol = round((clasf_corte * 0.45) + c_bla)
c_pot = round(((total_reg - clasf_corte) * 0.2) + c_gol)
c_pro = round(((total_reg - clasf_corte) * 0.35) + c_pot)

df['Nueva Clasificacion Cliente'] = np.where(df['Ranking'] <= clasf_corte, 'COMERCIANTE', 'CONSUMIDOR FINAL')
cond_seg = [(df['Ranking'] <= c_top), (df['Ranking'] <= c_pre), (df['Ranking'] <= c_bla), (df['Ranking'] <= c_gol), (df['Ranking'] <= c_pot), (df['Ranking'] <= c_pro)]
labels_seg = ['TOP', 'PREMIUM', 'BLACK', 'GOLDEN', 'POTENCIALES', 'PROMOCIONALES']
df['Segmentacion Clientes'] = np.select(cond_seg, labels_seg, default='OCASIONALES')

# =========================================================
# BLOQUE 4: K-MEANS (CLUSTERING IA NO SUPERVISADO)
# =========================================================

print("Calculando Clusters Diagnósticos Naturales...")
X_kmeans = df[['Zcategorias','ZLealtad','Zventa_neta','ZMargen evaluar','ZDiasUltimaCompra',
    'ZMomentum_Venta','ZIndice_Fuga',]]

kmeans = KMeans(n_clusters=KMEANS_CLUSTERS, random_state=42, n_init=10)
df['Cluster_ID'] = kmeans.fit_predict(X_kmeans)

cluster_order = (
    df.groupby('Cluster_ID')['venta_neta']
    .mean()
    .sort_values(ascending=False)
    .index
)

nombres_perfil_puro = [
    "VIPS ESTRATÉGICOS",# Compradores de volumen masivo y alta frecuencia
    "LEALES DE ALTO VOLUMEN",# Clientes consolidados de consumo constante elevado
    "COMPRADORES DE MEDIANO VOLUMEN",# Compradores recurrentes de nivel medio-alto
    "COMPRADORES ESPECIALIZADOS ",# Clientes concentrados en un ticket medio (sin volatilidad del ticket)
    "COMPRADORES OCASIONALES ",# clientes de volumen intermedio y compras periódicas
    "COMPRADORES DE TICKET MENOR",# Clientes de baja facturación por visita
    "ESPORÁDICOS DE COMPRA MÍNIMA",# Clientes de consumo marginal o de muy baja frecuencia
]

cluster_mapping_7 = {
    old_id: f"SEGMENTO {new_id + 1}: {nombre}"
    for new_id, (old_id, nombre) in enumerate(
        zip(cluster_order, nombres_perfil_puro)
    )
}

df['Cluster_Natural'] = df['Cluster_ID'].map(cluster_mapping_7)


# =========================================================
# BLOQUE 5: RANDOM FOREST / LIGHTGBM (ARQUITECTURA PREDICTIVA)
# =========================================================

# =========================================================
# FASE 1 OPTIMIZADA: Target Dinámico y Variables Históricas
# =========================================================
print("-> Procesando Target Dinámico y Nuevas Variables Históricas...")

# 1. Preparar fechas base (conversión rápida)
dq['Mes_Snapshot'] = dq['Ano'].astype(str) + dq['Mes'].astype(str).str.zfill(2)
dq['Fecha_Actual'] = pd.to_datetime(dq['Mes_Snapshot'], format='%Y%m')

# 2. Recencia, Lealtad y Margen Histórico
dq['Ultima_Compra_Mes'] = pd.to_datetime(
    dq['Ultima_Compra_Mes'].astype(str), format='%Y%m%d'
)
dq['Fin_de_Mes'] = dq['Fecha_Actual'] + pd.offsets.MonthEnd(0)
dq['DiasUltimaCompra'] = (dq['Fin_de_Mes'] - dq['Ultima_Compra_Mes']).dt.days
dq['Lealtad'] = dq['Dias_Compra_Mes'] / dq['Fecha_Actual'].dt.daysinmonth

dq['Margen_Financiero'] = dq['Venta_Acumulada'] - dq['Costo_Acumulado']
dq['Margen_Evaluar'] = dq['Margen_Financiero'].clip(lower=0)

dq['Tasa_Devoluciones'] = dq['Tasa_Devoluciones'].fillna(0)
dq['Penetracion_Marca_Propia'] = dq['Penetracion_Marca_Propia'].fillna(0)

# 3. Cruzar el Ciclo de Vida del Cliente (Dias_prom) desde el DataFrame principal
df_ciclo = df[['clave', 'Dias_prom']].rename(columns={'clave': 'ClaveCliente'})
dq = pd.merge(dq, df_ciclo, on='ClaveCliente', how='left')
dq['Dias_prom'] = dq['Dias_prom'].replace(0, np.nan).fillna(30)

# 4. ORDENAMIENTO ÚNICO (Clave para acelerar Pandas)
dq = dq.sort_values(by=['ClaveCliente', 'Fecha_Actual']).reset_index(drop=True)

# 4.1 Momentum de Venta (VECTORIZADO: Se eliminó el lambda lento)
# Usamos shift() y rolling() nativo de pandas por grupo
dq['Venta_Shift'] = dq.groupby('ClaveCliente')['Venta_Acumulada'].shift(1)
dq['Venta_Prom_Trim_Ant'] = dq.groupby('ClaveCliente')['Venta_Shift'].rolling(
    window=3, min_periods=1
).mean().reset_index(level=0, drop=True)

dq['Momentum_Venta'] = (
    dq['Venta_Acumulada'] / dq['Venta_Prom_Trim_Ant'].replace(0, np.nan)
).fillna(1).clip(upper=3)
dq.drop(columns=['Venta_Shift'], inplace=True)

# 4.2 Volatilidad del Ticket (VECTORIZADO: Se eliminó el lambda lento)
dq['Ticket_Promedio_Mensual'] = dq['Venta_Acumulada'] / dq[
    'Notas_Acumuladas'
].clip(lower=1)
dq['Volatilidad_Ticket'] = dq.groupby('ClaveCliente')[
    'Ticket_Promedio_Mensual'
].rolling(window=6, min_periods=2).std().reset_index(level=0, drop=True).fillna(0)

####--INICIO DE BOQUE VIEJO
# 5. TARGET INTELIGENTE
#dq['Siguiente_Compra_Historica'] = dq.groupby('ClaveCliente')[
#    'Ultima_Compra_Mes'
#].shift(-1)
#dq['Dias_Para_Regresar'] = (
#    dq['Siguiente_Compra_Historica'] - dq['Fin_de_Mes']
#).dt.days


# =====================================================================
# 🎛️ INTERRUPTOR DE ESTRATEGIA (OPCIÓN A vs OPCIÓN B)
# Descomenta las líneas de la opción que desees probar y comenta la otra.
# =====================================================================

# Condición base común para ambas opciones
#condicion_nunca_volvio = dq['Siguiente_Compra_Historica'].isnull()

# ---------------------------------------------------------------------
# 🚀 OPCIÓN A: Fuga Estricta (Solo considera abandono si NUNCA MÁS volvió)
# ---------------------------------------------------------------------
#print("[CONFIG] Ejecutando OPCIÓN A: Fuga Estricta (Nunca volvió)")
#dq['Target_Abandono_Real'] = np.where(condicion_nunca_volvio, 1, 0)

# ---------------------------------------------------------------------
# 📈 OPCIÓN B: Mayor Tolerancia al Retraso (Fuga si supera un umbral drástico)
# ---------------------------------------------------------------------
#print("[CONFIG] Ejecutando OPCIÓN B: Mayor Tolerancia al Retraso (Umbral Expandido)")
#UMBRAL_FUGA_TOLERANTE = 3.5  # Puedes ajustar a 4.0, 4.5 o 5.0 según tus pruebas
#condicion_tardo_extremo = (dq['Dias_Para_Regresar'] / dq['Dias_prom']) > UMBRAL_FUGA_TOLERANTE
#dq['Target_Abandono_Real'] = np.where(condicion_nunca_volvio | condicion_tardo_extremo, 1, 0)
# =====================================================================


# --- EL SALVAVIDAS (Corrección del Falso Abandono) ---
#clientes_vivos_hoy = set(df['clave'])
#es_falsa_alarma = dq['Siguiente_Compra_Historica'].isnull() & dq['ClaveCliente'].isin(clientes_vivos_hoy)

#dq['Target_Abandono_Real'] = np.where(es_falsa_alarma, 0, dq['Target_Abandono_Real'])

# Limpiamos columnas temporales
#dq_final = dq.drop(columns=[
#    'Fin_de_Mes', 'Venta_Prom_Trim_Ant', 'Siguiente_Compra_Historica', 'Dias_Para_Regresar', 'Dias_prom'
#])

# Filtrado para entrenamiento histórico
#fecha_ejecucion_dt = pd.to_datetime(MES_EJECUCION, format='%Y%m')
#fecha_corte = fecha_ejecucion_dt - pd.DateOffset(months=1)
#mes_corte_str = fecha_corte.strftime('%Y%m')

#df_train = dq_final[dq_final['Mes_Snapshot'] < mes_corte_str].copy()
###### FIN DE BLOQUE VIEJO 
# Mapeamos los nombres históricos para que empaten con los de Enero 2026
######----INICIO NUEVO BLOQUE 
# 5. TARGET INTELIGENTE SIN FUGA DE DATOS (VENTANA REAL DE 90 DÍAS)
dq['Siguiente_Compra_Historica'] = dq.groupby('ClaveCliente')[
    'Ultima_Compra_Mes'
].shift(-1)

dq['Dias_Para_Regresar'] = (
    dq['Siguiente_Compra_Historica'] - dq['Fin_de_Mes']
).dt.days

# Definimos abandono si nunca volvió o tardó más de 90 días (DIAS_INACTIVIDAD_CRITICA) en volver
condicion_nunca_volvio = dq['Siguiente_Compra_Historica'].isnull()
condicion_supero_ventana = dq['Dias_Para_Regresar'] > DIAS_INACTIVIDAD_CRITICA

dq['Target_Abandono_Real'] = np.where(
    condicion_nunca_volvio | condicion_supero_ventana, 1, 0
)

# Limpiamos columnas temporales (eliminamos el "Salvavidas" porque causaba Data Leakage)
dq_final = dq.drop(columns=[
    'Fin_de_Mes', 'Venta_Prom_Trim_Ant', 'Siguiente_Compra_Historica', 'Dias_Para_Regresar', 'Dias_prom'
], errors='ignore')

# Filtrado para entrenamiento histórico:
# Cortamos 3 meses antes de MES_EJECUCION (ej. julio 2026 si ejecutas octubre 2026)
# para garantizar que todos los meses de entrenamiento tuvieron 90 días reales para observar si regresaban.
fecha_ejecucion_dt = pd.to_datetime(MES_EJECUCION, format='%Y%m')
fecha_corte_target = fecha_ejecucion_dt - pd.DateOffset(months=3)
mes_corte_str = fecha_corte_target.strftime('%Y%m')

df_train = dq_final[dq_final['Mes_Snapshot'] <= mes_corte_str].copy()
######---- FIN NUEVO BLOQUE
df_train = df_train.rename(columns={
    'Variedad_Categoria': 'categorias',
    'Venta_Acumulada': 'venta_neta',
    'Notas_Acumuladas': 'transacciones',
    'Margen_Evaluar': 'Margen evaluar'
})

# Cruzar las últimas variables de comportamiento conocidas al DataFrame del presente (df)
df_nuevas_vars = dq.groupby('ClaveCliente')[
    ['Volatilidad_Ticket', 'Tasa_Devoluciones', 'Penetracion_Marca_Propia']
].last().reset_index()

df = pd.merge(df, df_nuevas_vars.rename(columns={'ClaveCliente': 'clave'}), on='clave', how='left')

# Llenamos nulos en el presente por si hay clientes súper nuevos
df['Volatilidad_Ticket'] = df['Volatilidad_Ticket'].fillna(0)
df['Tasa_Devoluciones'] = df['Tasa_Devoluciones'].fillna(0)
df['Penetracion_Marca_Propia'] = df['Penetracion_Marca_Propia'].fillna(0)

###############################################
# --- FASE 2: Entrenamiento del Modelo ---
#print("Entrenando Modelo Predictivo Supervisado para Abandono...")
# ¡AÑADIMOS EL MARGEN AL ENTRENAMIENTO!
#features_rf = ['categorias', 'venta_neta', 'transacciones', 'DiasUltimaCompra', 'Lealtad', 'Momentum_Venta', 'Margen evaluar','Volatilidad_Ticket','Tasa_Devoluciones','Penetracion_Marca_Propia']
#X_hist = df_train[features_rf]
#y_hist = df_train['Target_Abandono_Real']

#X_train_h, X_test_h, y_train_h, y_test_h = train_test_split(X_hist, y_hist, test_size=0.3, random_state=42, stratify=y_hist)

#model_rf = RandomForestClassifier(
#    n_estimators=RF_ESTIMATORS, 
#    max_depth=RF_MAX_DEPTH, # Asegúrate de que en el Bloque 0 lo dejaste en 15
#    min_samples_leaf=RF_MIN_LEAF, 
#    random_state=42,
#    n_jobs=-1,
#    class_weight='balanced'
#)

#model_rf.fit(X_train_h, y_train_h)

#y_pred_h = model_rf.predict(X_test_h)
#print(f"-> ¡Precisión Real del Modelo (Con Margen Histórico)!: {accuracy_score(y_test_h, y_pred_h) * 100:.2f}%")

# --- FASE 3: Predicción del Presente (Enero 2026) ---
#X_actual = df[features_rf] 
#df['Probabilidad_Abandono'] = model_rf.predict_proba(X_actual)[:, 1]
#df['Riesgo_Critico'] = np.where(df['Probabilidad_Abandono'] >= UMBRAL_RIESGO_CRITICO, 1, 0)
##########################################################
# --- FASE 2: Entrenamiento del Modelo (AHORA CON LIGHTGBM) ---
print("Entrenando Modelo Predictivo Supervisado para Abandono (LightGBM)...")

features_model = ['categorias', 'venta_neta', 'transacciones', 'DiasUltimaCompra', 'Lealtad', 
                  'Momentum_Venta', 'Margen evaluar', 'Volatilidad_Ticket', 'Tasa_Devoluciones', 
                  'Penetracion_Marca_Propia']
### INICIO BLOQUE VIEJO 
#X_hist = df_train[features_model]
#y_hist = df_train['Target_Abandono_Real']
#X_train_h, X_test_h, y_train_h, y_test_h = train_test_split(X_hist, y_hist, test_size=0.3, random_state=42, stratify=y_hist)
### FIN BLOQUE VIEJO 
### INICIO BLOQUE NUEVO
# Validación Temporal (Out-of-Time):
# Entrenamos con los meses anteriores y evaluamos sobre el último mes disponible de df_train
mes_val = df_train['Mes_Snapshot'].max()
train_mask = df_train['Mes_Snapshot'] < mes_val
val_mask = df_train['Mes_Snapshot'] == mes_val

X_train_h = df_train.loc[train_mask, features_model]
y_train_h = df_train.loc[train_mask, 'Target_Abandono_Real']

X_test_h = df_train.loc[val_mask, features_model]
y_test_h = df_train.loc[val_mask, 'Target_Abandono_Real']

print(f"-> Meses de Entrenamiento: < {mes_val} ({len(X_train_h):,} registros)")
print(f"-> Mes de Validación (Out-of-Time): {mes_val} ({len(X_test_h):,} registros)")
### FIN BLOQUE NUEVO
### INICIO BLOQUE VIEJO
# Inicializamos el nuevo motor LightGBM
#model_lgb = LGBMClassifier(
#    n_estimators=200,           # Los 200 árboles de tu comité
#    max_depth=15,               # Límite de profundidad
#   num_leaves=50,              # Límite de reglas finales por árbol (exclusivo de LGBM para evitar sobreajuste)
#    min_child_samples=10,       # Tu regla de oro: mínimo 10 clientes para crear un patrón
#   class_weight='balanced',    # Sensibilidad alta a las fugas
#    random_state=42,
#    n_jobs=-1,
#    verbose=-1                  # Apaga las advertencias innecesarias en la consola
#)
### FIN BLOQUE VIEJO
### INICIO BLOQUE NUEVO 
model_lgb = LGBMClassifier(
    n_estimators=200,
    learning_rate=0.05,
    max_depth=15,
    num_leaves=50,
    min_child_samples=30,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1,
    verbose=-1
)
### FIN BLOQUE NUEVO 
model_lgb.fit(X_train_h, y_train_h)

y_pred_h = model_lgb.predict(X_test_h)
print(f"-> ¡Precisión Real del Modelo (LightGBM)!: {accuracy_score(y_test_h, y_pred_h) * 100:.2f}%")

# --- FASE 3: Predicción del Presente (Enero 2026) ---
#X_actual = df[features_model] 
#df['Probabilidad_Abandono'] = model_lgb.predict_proba(X_actual)[:, 1]
######################-----------NUEVO BLOQUE
# --- FASE 3: Predicción del Presente (Escala Mensual Homologada) ---
# 1. Extraemos el último snapshot mensual de cada cliente desde dq
df_ultimo_mes = (
    dq.sort_values(by=['ClaveCliente', 'Fecha_Actual'])
    .groupby('ClaveCliente')
    .last()
    .reset_index()
    .rename(columns={
        'ClaveCliente': 'clave',
        'Variedad_Categoria': 'categorias',
        'Venta_Acumulada': 'venta_neta',
        'Notas_Acumuladas': 'transacciones',
        'Margen_Evaluar': 'Margen evaluar'
    })
)

# 2. Mantenemos el orden exacto de filas de 'df' y su recencia real al corte
df_pred_presente = pd.merge(
    df[['clave', 'DiasUltimaCompra']], 
    df_ultimo_mes.drop(columns=['DiasUltimaCompra'], errors='ignore'), 
    on='clave', 
    how='left'
).fillna(0)

# 3. Predecimos usando la misma escala mensual con la que se entrenó LightGBM
X_actual = df_pred_presente[features_model]
df['Probabilidad_Abandono'] = model_lgb.predict_proba(X_actual)[:, 1]
######################-----------

# NUEVA REGLA DURA (Castigo por inactividad extrema ignorando el histórico leal)
# REGLA DURA AJUSTADA: Castigo al 85% solo si lleva >= 90 días sin comprar Y está fuera de su IRF normal
condicion_inactivo_fuera_ciclo = (
    (df['DiasUltimaCompra'] >= DIAS_INACTIVIDAD_CRITICA) & 
    (df['Indice_Fuga'] > UMBRAL_IRF_NORMAL)
)

df['Probabilidad_Abandono'] = np.where(
    condicion_inactivo_fuera_ciclo, 
    np.maximum(df['Probabilidad_Abandono'], PISO_PA_INACTIVO), 
    df['Probabilidad_Abandono']
)
### SOLO UNA LINEA BLOQUE VIEJO 
#df['Riesgo_Critico'] = np.where(df['Probabilidad_Abandono'] >= UMBRAL_RIESGO_CRITICO, 1, 0)

#Validacion modelo
### INICIO BLOQUE VIEJO
#y_pred_h = model_lgb.predict(X_test_h)
#y_prob_h = model_lgb.predict_proba(X_test_h)[:, 1]

#print(f"-> ¡Precisión Real del Modelo (LightGBM)!: {accuracy_score(y_test_h, y_pred_h) * 100:.2f}%")
#print(f"-> ROC-AUC Score: {roc_auc_score(y_test_h, y_prob_h):.4f}")

#print("\n--- REPORTE DE CLASIFICACIÓN ---")
#print(classification_report(y_test_h, y_pred_h, target_names=['Activo (0)', 'Abandono (1)']))

#print("\n--- MATRIZ DE CONFUSIÓN ---")
#print(confusion_matrix(y_test_h, y_pred_h))
### FIN DE BLOQUE VIEJO 
### INICIO BLOQUE NUEVO 
from sklearn.metrics import precision_recall_curve, confusion_matrix, roc_auc_score

y_prob_h = model_lgb.predict_proba(X_test_h)[:, 1]

# Calculamos el umbral óptimo que maximiza el F1-Score de la clase minoritaria (Abandono)
precisions, recalls, thresholds = precision_recall_curve(y_test_h, y_prob_h)
f1_scores = 2 * (precisions * recalls) / (precisions + recalls + 1e-8)
best_idx = np.argmax(f1_scores)
best_threshold = thresholds[best_idx]

y_pred_opt = (y_prob_h >= best_threshold).astype(int)

print(f"-> ROC-AUC Score: {roc_auc_score(y_test_h, y_prob_h):.4f}")
print(f"-> Umbral Óptimo (F1-Max): {best_threshold:.4f}")
print(f"-> Precisión con Umbral Óptimo: {accuracy_score(y_test_h, y_pred_opt) * 100:.2f}%")

print("\n--- REPORTE DE CLASIFICACIÓN (UMBRAL ÓPTIMO) ---")
print(classification_report(y_test_h, y_pred_opt, target_names=['Activo (0)', 'Abandono (1)']))

print("\n--- MATRIZ DE CONFUSIÓN (UMBRAL ÓPTIMO) ---")
print(confusion_matrix(y_test_h, y_pred_opt))
### INICIO BLOQUE NUEVO
# Definimos los umbrales dinámicos basados en el punto óptimo del mes
umbral_medio = round(best_threshold * 0.55, 4)
umbral_alto = round(best_threshold, 4)
umbral_critico = round(min(best_threshold * 1.90, 0.75), 4)

print(f"-> Cortes Dinámicos Aplicados | Medio: {umbral_medio:.2%} | Alto: {umbral_alto:.2%} | Crítico: {umbral_critico:.2%}")

df['Riesgo_Critico'] = np.where(df['Probabilidad_Abandono'] >= umbral_critico, 1, 0)
### FIN DE BLOQUE NUEVO 
### INICIO BLOQUE NUEVO 
#print("\n--- DISTRIBUCIÓN DE PROBABILIDADES EN EL PRESENTE (df) ---")
#print(df['Probabilidad_Abandono'].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.85, 0.9, 0.95]))
# =========================================================
# --- FASE 3.1: PROBABILIDAD DE RECOMPRA (PR) Y VENTANA ---
# =========================================================
print("-> Calculando Probabilidad de Recompra (PR) y ventana esperada...")

# 1. Probabilidad de Recompra (complemento calibrado de PA)
df['Probabilidad_Recompra'] = (1 - df['Probabilidad_Abandono']).round(4)

# 2. Fecha estimada de próxima compra según su ciclo natural
ult_compra_dt = pd.to_datetime(df['Ultima_compra'].astype(str), format='%Y%m%d', errors='coerce')
df['Fecha_Prox_Compra_Est'] = (
    ult_compra_dt + pd.to_timedelta(df['Ciclo_Compra_Dias'].round(0), unit='D')
).dt.strftime('%Y%m%d')

# 3. Días restantes para su próxima compra (negativo = días de atraso frente a su ciclo)
df['Dias_Para_Prox_Compra'] = (df['Ciclo_Compra_Dias'] - df['DiasUltimaCompra']).round(0).astype(int)

# 4. Estatus operativo de recompra
condiciones_recompra = [
    # En ventana óptima: le faltan entre 0 y 5 días para tocar recompra y tiene buena PR
    (df['Dias_Para_Prox_Compra'].between(0, 5)) & (df['Probabilidad_Recompra'] >= 0.50),
    # Atraso leve pero aún rescatable (lleva hasta 1 ciclo completo de atraso y PR >= 40%)
    (df['Dias_Para_Prox_Compra'] < 0) & (df['Indice_Fuga'] <= 2.0) & (df['Probabilidad_Recompra'] >= 0.40),
    # Comprador activo / adelantado dentro de su ciclo normal
    (df['Dias_Para_Prox_Compra'] > 5) & (df['Probabilidad_Recompra'] >= 0.50),
    # Baja probabilidad de regreso
    (df['Probabilidad_Recompra'] < 0.30)
]

labels_recompra = [
    '1. EN VENTANA DE RECOMPRA (CONTACTAR)',
    '2. ATRASADO RECUPERABLE (RECORDATORIO)',
    '3. ACTIVO EN CICLO (CROSS-SELLING)',
    '4. RIESGO ALTO / BAJA RECOMPRA'
]

df['Estatus_Recompra'] = np.select(
    condiciones_recompra,
    labels_recompra,
    default='5. SEGUIMIENTO REGULAR'
)

# =========================================================
# --- FASE 4: Cálculo de Contracción de Categorías (100% desde el Histórico) ---
# =========================================================
print("-> Calculando contracción mensual de categorías desde la historia...")

# 1. EL "ANTES": Promedio de categorías por mes en su historia
df_cat_antes = dq.groupby('ClaveCliente')['Variedad_Categoria'].mean().round(0).reset_index()
df_cat_antes = df_cat_antes.rename(columns={'ClaveCliente': 'clave', 'Variedad_Categoria': 'Categorias_Antes'})

# 2. EL "AHORA": Las categorías que compró en su ÚLTIMO mes registrado
# Ordenamos por fecha para asegurar que el último registro sea el más reciente
dq_ordenado = dq.sort_values(by=['ClaveCliente', 'Fecha_Actual'])
df_cat_ahora = dq_ordenado.groupby('ClaveCliente')['Variedad_Categoria'].last().reset_index()
df_cat_ahora = df_cat_ahora.rename(columns={'ClaveCliente': 'clave', 'Variedad_Categoria': 'Categorias_Ahora'})

# 3. Cruzamos ambas métricas puras a nuestro DataFrame del presente (df)
df = pd.merge(df, df_cat_antes, on='clave', how='left')
df = pd.merge(df, df_cat_ahora, on='clave', how='left')

# Si por alguna razón el cliente es muy nuevo y sale nulo, le ponemos 1 como base
df['Categorias_Antes'] = df['Categorias_Antes'].fillna(1).astype(int)
df['Categorias_Ahora'] = df['Categorias_Ahora'].fillna(1).astype(int)

# =========================================================
# BLOQUE 6: ESTRATEGIA PRESCRIPTIVA Y ACCIONES SUGERIDAS
# =========================================================
print("Generando acciones sugeridas combinadas...")
#INICIO DEL BLOQIE VIEJO 
#condiciones_accion = [
    # 1. VIPs en riesgo de abandono
#    (df['Cluster_Natural'].str.contains("VIPS")) & (df['Probabilidad_Abandono'] > 0.50),
    # 2. Oportunidad inmediata: cliente sano que toca recompra en los próximos 5 días
#    (df['Estatus_Recompra'] == '1. EN VENTANA DE RECOMPRA (CONTACTAR)') & (df['Nueva Clasificacion Cliente'] == 'COMERCIANTE'),
    # 3. Compradores de mediano volumen sanos con alta PR para escalar canasta (cross-selling)
#    (df['Cluster_Natural'].str.contains("COMPRADORES")) & (df['Probabilidad_Recompra'] >= 0.70),
    # 4. Riesgo crítico general (Fuga inminente detectada por LightGBM)
#    (df['Riesgo_Critico'] == 1),
    # 5. Clientes de compra mínima o muy baja actividad
#    (df['Cluster_Natural'].str.contains("ESPORÁDICOS")),
    # 6. Clientes nuevos con señal temprana de fuga
#    (df['Probabilidad_Abandono'] > 0.40) & (df['Segmento_Vida'] == 'NUEVO'),
#]
### FIN DEL BLOQUE VIEJO
### INICO NUEVO BLOQUE
condiciones_accion = [
    # 1. VIPs en riesgo de abandono (desde riesgo alto dinámico)
    (df['Cluster_Natural'].str.contains("VIPS")) & (df['Probabilidad_Abandono'] >= umbral_alto),
    # 2. Oportunidad inmediata: cliente sano que toca recompra en los próximos 5 días
    (df['Estatus_Recompra'] == '1. EN VENTANA DE RECOMPRA (CONTACTAR)') & (df['Nueva Clasificacion Cliente'] == 'COMERCIANTE'),
    # 3. Compradores de mediano volumen sanos (por debajo del umbral medio) para escalar canasta
    (df['Cluster_Natural'].str.contains("COMPRADORES")) & (df['Probabilidad_Abandono'] < umbral_medio),
    # 4. Riesgo crítico general (Fuga inminente detectada por LightGBM o inactividad >= 90 días)
    (df['Riesgo_Critico'] == 1),
    # 5. Clientes de compra mínima o muy baja actividad
    (df['Cluster_Natural'].str.contains("ESPORÁDICOS")),
    # 6. Clientes nuevos con señal temprana de fuga
    (df['Probabilidad_Abandono'] >= umbral_alto) & (df['Segmento_Vida'] == 'NUEVO'),
]
### FIN DEL NUEVO BLOQUE

labels_accion = [
    'BLINDAJE: CRÍTICO EN VIP',
    'IMPULSAR RECOMPRA: TOCA PEDIDO ESTA SEMANA',
    'CROSS-SELLING: POTENCIAL ESCALADA',
    'RESCATE INMEDIATO: FUERA DE CICLO',
    'OBSERVAR: CUENTA DORMIDA',
    'RETENER: ALERTA TEMPRANA EN NUEVO',
]

df['Accion_Sugerida'] = np.select(
    condiciones_accion, labels_accion, default='SEGUIMIENTO ESTÁNDAR'
)

# =========================================================
# BLOQUE 7: ASIGNACIÓN DE CUADRANTES Y MATRIZ PA x IRF (OPTIMIZADO)
# =========================================================
print("Clasificando clientes en la Matriz PA x IRF...")
# INICIO BLOQUE NUEVO
# 1. Definimos los cortes de rangos
#df['Rango_PA'] = pd.cut(
#    df['Probabilidad_Abandono'],
    #bins=[-0.01, 0.20, 0.50, 0.70, 1.01],
#    bins=[-0.01, 0.10, 0.25, 0.45, 1.01],
#    labels=[
#        'Baja (<=20%)',
#        'Media (20-50%)',
#        'Alta (50-70%)',
#        'Crítica (>=70%)',
#    ],
#)
### FIN BLOQUE VIEJO
### INICIO BLOQUE NUEVO
# 1. Definimos los cortes y etiquetas dinámicas
bins_pa = [-0.01, umbral_medio, umbral_alto, umbral_critico, 1.01]
labels_pa = [
    f'Baja (<={umbral_medio*100:.0f}%)',
    f'Media ({umbral_medio*100:.0f}-{umbral_alto*100:.0f}%)',
    f'Alta ({umbral_alto*100:.0f}-{umbral_critico*100:.0f}%)',
    f'Crítica (>={umbral_critico*100:.0f}%)',
]

df['Rango_PA'] = pd.cut(
    df['Probabilidad_Abandono'],
    bins=bins_pa,
    labels=labels_pa,
)

df['Rango_IRF'] = pd.cut(
    df['Indice_Fuga'],
    bins=[-0.01, 1.00, 1.20, 2.00, 5.01],
    labels=[
        'Adelantado (<=1.0)',
        'Normal (1.0-1.2)',
        'Retraso Leve (1.2-2.0)',
        'Crítico (>=2.0)',
    ],
)

# 2. Mapeo Exhaustivo de Cuadrantes usando las etiquetas dinámicas
condiciones_matriz = [
    # --- RANGO DE RIESGO CRÍTICO ---
    (df['Rango_PA'] == labels_pa[3]) & (df['Rango_IRF'] == 'Crítico (>=2.0)'),
    (df['Rango_PA'] == labels_pa[3]) & (df['Rango_IRF'].isin(['Adelantado (<=1.0)', 'Normal (1.0-1.2)'])),
    (df['Rango_PA'] == labels_pa[3]) & (df['Rango_IRF'] == 'Retraso Leve (1.2-2.0)'),
    # --- RANGO DE RIESGO ALTO ---
    (df['Rango_PA'] == labels_pa[2]) & (df['Rango_IRF'].isin(['Retraso Leve (1.2-2.0)', 'Crítico (>=2.0)'])),
    (df['Rango_PA'] == labels_pa[2]) & (df['Rango_IRF'].isin(['Adelantado (<=1.0)', 'Normal (1.0-1.2)'])),
    # --- RANGO DE RIESGO MEDIO ---
    (df['Rango_PA'] == labels_pa[1]) & (df['Rango_IRF'].isin(['Retraso Leve (1.2-2.0)', 'Crítico (>=2.0)'])),
    (df['Rango_PA'] == labels_pa[1]) & (df['Rango_IRF'].isin(['Adelantado (<=1.0)', 'Normal (1.0-1.2)'])),
    # --- RANGO DE RIESGO BAJO ---
    (df['Rango_PA'] == labels_pa[0]) & (df['Rango_IRF'].isin(['Adelantado (<=1.0)', 'Normal (1.0-1.2)'])),
    (df['Rango_PA'] == labels_pa[0]) & (df['Rango_IRF'].isin(['Retraso Leve (1.2-2.0)', 'Crítico (>=2.0)'])),
]

valores_matriz = [
    '1. ABANDONADOR CRÍTICO (Fuga Confirmada)',  # PA Crítica + IRF Crítico
    '2. FUGA SILENCIOSA (Deterioro Comercial Activo)',  # PA Crítica + IRF Al día
    '3. DESACELERACIÓN AGUDA (Alerta de Fuga)',  # PA Crítica + IRF Leve
    '4. RIESGO ALTO EN SEGUIMIENTO',  # PA Alta + IRF en Retraso
    '5. ALERTA TEMPRANA COMERCIAL',  # PA Alta + IRF al día
    '6. RETRASO ESPORÁDICO DE RECURRENCIA',  # PA Media + IRF en Retraso
    '7. COMPORTAMIENTO ESTABLE EN OBSERVACIÓN',  # PA Media + IRF al día
    '8. CLIENTE SALUDABLE / COMPRADOR ACTIVO',  # PA Baja + IRF al día
    '9. ANOMALÍA OPERATIVA / RETRASO LOGÍSTICO',  # PA Baja + IRF en Retraso
]

df['Cuadrante_PA_IRF'] = np.select(
    condiciones_matriz, valores_matriz, default='7. COMPORTAMIENTO ESTABLE EN OBSERVACIÓN'
)

# 3. Matriz de Calor
matriz_pivote = pd.crosstab(df['Rango_PA'], df['Rango_IRF'], dropna=False)

plt.figure(figsize=(9.5, 7), dpi=300)
sns.heatmap(
    matriz_pivote,
    annot=True,
    fmt="d",
    cmap="YlOrRd",
    linewidths=0.8,
    annot_kws={"size": 10, "weight": "bold"},
)
plt.title(
    'Matriz de Calor Re-calibrada: PA vs IRF (100% Cobertura)',
    fontsize=12,
    weight='bold',
    pad=15,
)
plt.ylabel(
    'Probabilidad de Abandono (PA) [Salud Comercial]',
    fontsize=10,
    weight='bold',
)
plt.xlabel(
    'Índice de Riesgo Fuga (IRF) [Recencia Operativa]',
    fontsize=10,
    weight='bold',
)
plt.tight_layout()

matriz_salida = os.path.join(BASE_DIR, "Matriz_Calor_PA_IRF.png")
plt.savefig(matriz_salida, dpi=300)
plt.close()

# =========================================================
# BLOQUE 8: EXPORTACIONES FINALES DE ARCHIVOS (ENFOQUES A Y B)
# =========================================================
print("Generando reportes operativos integrados (Enfoque A: Top Riesgo x Sucursal + Enfoque B: Valor de Cartera)...")
os.makedirs(folder_sucursales, exist_ok=True)

# 1. Definimos las columnas clave para gerentes (incluye Perfil K-Means)
columnas_operativas = [
    'clave', 'suc', 'Ranking', 'Segmentacion Clientes', 'Cluster_Natural', 'venta_neta', 
    'Categorias_Antes', 'Categorias_Ahora', 
    'DiasUltimaCompra', 'Indice_Fuga', 'Probabilidad_Abandono', 'Probabilidad_Recompra',
    'Fecha_Prox_Compra_Est', 'Dias_Para_Prox_Compra', 'Estatus_Recompra',
    'Cuadrante_PA_IRF', 'Accion_Sugerida'
]

# Base de trabajo limpia para alertas
df_alertas_base = df[columnas_operativas].copy()
df_alertas_global = df_alertas_base.rename(columns={
    'clave': 'Cliente RED', 
    'suc': 'Sucursal', 
    'Ranking': 'Ranking General', 
    'Segmentacion Clientes': 'Segmento Comercial', 
    'Cluster_Natural': 'Perfil Cliente (K-Means)',
    'venta_neta': 'Venta Acumulada', 
    'Categorias_Antes': 'Categorias Antes', 
    'Categorias_Ahora': 'Categorias Ahora', 
    'DiasUltimaCompra': 'Dias Sin Comprar', 
    'Indice_Fuga': 'Indice Riesgo Fuga', 
    'Probabilidad_Abandono': 'Probabilidad Abandono', 
    'Probabilidad_Recompra': 'Probabilidad Recompra',
    'Fecha_Prox_Compra_Est': 'Fecha Estimada Recompra',
    'Dias_Para_Prox_Compra': 'Dias Para Recompra', 
    'Estatus_Recompra': 'Estatus Recompra',
    'Cuadrante_PA_IRF': 'Diagnostico Cuadrante',
    'Accion_Sugerida': 'Accion Estrategica Sugerida'
})

df_alertas_global['Cliente RED'] = df_alertas_global['Cliente RED'].astype(str).str.zfill(9)
df_alertas_global['Sucursal'] = df_alertas_global['Sucursal'].astype(str).str.strip()

# --- ENFOQUE A: TOP 15% MÁS CRÍTICO POR SUCURSAL ---
df_alertas_global['Percentil_Riesgo_Sucursal'] = df_alertas_global.groupby('Sucursal')['Probabilidad Abandono'].rank(pct=True)
df_top_riesgo = df_alertas_global[df_alertas_global['Percentil_Riesgo_Sucursal'] >= 0.85].copy()

# --- ENFOQUE B: FILTRAR Y ORDENAR POR VALOR COMERCIAL ---
condicion_prioridad = (df_top_riesgo['Segmento Comercial'] != 'OCASIONALES') | (df_top_riesgo['Probabilidad Abandono'] >= 0.90)
df_reportes_sucursales = df_top_riesgo[condicion_prioridad].copy()

# Generación de archivos por Sucursal
lista_sucursales = df_reportes_sucursales['Sucursal'].unique()

orden_segmentos = {'TOP': 1, 'PREMIUM': 2, 'BLACK': 3, 'GOLDEN': 4, 'POTENCIALES': 5, 'PROMOCIONALES': 6, 'OCASIONALES': 7}

for sucursal in lista_sucursales:
    if sucursal in ['', '0', '0.0', 'nan', 'None'] or pd.isna(sucursal):
        continue
        
    df_sucursal = df_reportes_sucursales[df_reportes_sucursales['Sucursal'] == sucursal].copy()
    
    if not df_sucursal.empty:
        df_sucursal['Prioridad_Comercial'] = df_sucursal['Segmento Comercial'].map(orden_segmentos)
        df_sucursal = df_sucursal.sort_values(by=['Prioridad_Comercial', 'Venta Acumulada'], ascending=[True, False])
        df_sucursal = df_sucursal.drop(columns=['Percentil_Riesgo_Sucursal', 'Prioridad_Comercial'])
        
        nombre_archivo = f"Alertas_Foco_Sucursal_{sucursal}.csv"
        ruta_salida_sucursal = os.path.join(folder_sucursales, nombre_archivo)
        df_sucursal.to_csv(ruta_salida_sucursal, index=False, encoding='utf-8-sig')

print(f"-> Archivos por sucursal generados en: {folder_sucursales}")

# --- 8.2 Inyección de Variables Informativas en Reporte Maestro ---
df['Mes Ejecucion'] = MES_EJECUCION
pesos_labels = ['P Variedad Categoria', 'P Lealtad', 'P Venta Acumulada', 'P Margen Financiero', 'P Recencia', 'P Momentum', 'P Riesgo Fuga']
pesos_vals = [W_CAT, W_LEA, W_VEN, W_MAR, abs(W_REC), W_MOM, abs(W_FUG)] 

nuevas_columnas_pesos = dict(zip(pesos_labels, pesos_vals))
df = df.assign(**nuevas_columnas_pesos)

# Reporte maestro completo
final_report = df[list(columnas_finales.keys())].rename(columns=columnas_finales)
cols_dec = final_report.select_dtypes(include=[np.number]).columns
final_report[cols_dec] = final_report[cols_dec].round(4)
final_report['Cliente RED'] = final_report['Cliente RED'].astype(str).str.zfill(9)

final_report.to_csv(path_reporte_maestro, index=False, encoding='utf-8-sig')
print(f"-> Reporte Maestro completo generado en: {path_reporte_maestro}")

# --- 8.4 Generación de Reporte_BD (Dinámico por Mes) ---
Reporte_BD = final_report[Mapa_final].copy()

# Ruta dinámica corregida según la variable MES_EJECUCION
path_reporte_bd = os.path.join(BASE_DIR, f"Reporte_BD_{MES_EJECUCION}.csv")
Reporte_BD.to_csv(path_reporte_bd, index=False, encoding='utf-8-sig')
print(f"-> Reporte BD (Ultra Resumen) generado dinámicamente en: {path_reporte_bd}")

# --- 8.5 Reporte Resumen Directivo de Sucursales ---
col_sucursal = 'Suc Mayor Compra'
if col_sucursal in final_report.columns:
    final_report['Sucursal_Limpia'] = final_report[col_sucursal].astype(str).str.strip()
    final_report['Percentil_Riesgo'] = final_report.groupby('Sucursal_Limpia')['Probabilidad Abandono'].rank(pct=True)
    
    final_report['Es_Riesgo_Foco'] = np.where(final_report['Percentil_Riesgo'] >= 0.85, 1, 0)
    
    reporte_sucursales = final_report.groupby(col_sucursal).agg(
        Total_Clientes=('Cliente RED', 'count'),
        Clientes_Riesgo_Foco=('Es_Riesgo_Foco', 'sum'),
        Venta_Top_Riesgo_En_Peligro=('Venta Acumulada', lambda x: x[final_report['Es_Riesgo_Foco'] == 1].sum()),
        Venta_Total_Sucursal=('Venta Acumulada', 'sum'),
        Probabilidad_Promedio_Fuga=('Probabilidad Abandono', 'mean')
    ).reset_index()
    
    reporte_sucursales['%_Clientes_Criticos_Foco'] = (reporte_sucursales['Clientes_Riesgo_Foco'] / reporte_sucursales['Total_Clientes']).round(4)
    reporte_sucursales['%_Venta_En_Riesgo'] = (reporte_sucursales['Venta_Top_Riesgo_En_Peligro'] / reporte_sucursales['Venta_Total_Sucursal']).round(4)
    
    reporte_sucursales = reporte_sucursales.sort_values(by='Venta_Top_Riesgo_En_Peligro', ascending=False)
    reporte_sucursales.to_csv(path_reporte_sucursales, index=False, encoding='utf-8-sig')
    print(f"-> Reporte Directivo Semanal generado en: {path_reporte_sucursales}")

print("\n¡Pipeline Analítico finalizado con éxito!")