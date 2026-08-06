import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------
# Configuración de la página
# ---------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Cobertura de Stock Mínimo - Línea de Picking",
    page_icon="📦",
    layout="wide"
)

st.title("📦 Cobertura de Stock Mínimo en Líneas de Picking")
st.markdown("Visualización e indicador del nivel de abastecimiento por ubicación de picking.")

# ---------------------------------------------------------
# Carga y preparación de datos
# ---------------------------------------------------------
@st.cache_data
def load_data(file):
    df_l1 = pd.read_excel(file, sheet_name='ANALISIS L1')
    df_l2 = pd.read_excel(file, sheet_name='ANALISIS L2')
    
    # Limpiar espacios en nombres de columnas
    df_l1.columns = df_l1.columns.str.strip()
    df_l2.columns = df_l2.columns.str.strip()
    
    # Unificar L1 y L2
    df = pd.concat([df_l1, df_l2], ignore_index=True)
    
    # Formateo de tipos de datos
    df['ESTACION'] = df['ESTACION'].astype(str)
    df['POSICIÓN'] = df['POSICIÓN'].astype(str)
    df['SECTOR'] = df['SECTOR'].astype(str)
    df['LINEA'] = df['LINEA'].astype(str)
    df['LOGICA'] = df['LOGICA'].fillna('-').astype(str)
    
    return df

# Carga mediante subida manual o archivo local predeterminado
uploaded_file = st.file_uploader(
    "Sube el archivo de Cobertura (.xlsm / .xlsx)", 
    type=['xlsx', 'xlsm']
)

if uploaded_file is not None:
    df = load_data(uploaded_file)
else:
    try:
        # Intenta cargar primero versión .xlsm y luego .xlsx
        try:
            df = load_data("Cobertura de abastecimiento de Línea de picking.xlsm")
        except Exception:
            df = load_data("Cobertura de abastecimiento de Línea de picking.xlsx")
        st.success("Archivo base 'Cobertura de abastecimiento de Línea de picking' cargado correctamente.")
    except Exception:
        st.info("Por favor, sube el archivo de Cobertura (.xlsm / .xlsx) para continuar.")
        st.stop()

# ---------------------------------------------------------
# Filtros laterales (Línea, Sector, Estación, Posición)
# ---------------------------------------------------------
st.sidebar.header("🔍 Filtros de Búsqueda")

# Filtro 1: Línea
lineas_opts = sorted(df['LINEA'].unique().tolist())
selected_lineas = st.sidebar.multiselect("Línea:", lineas_opts, default=lineas_opts)

# Filtro 2: Sector
df_f1 = df[df['LINEA'].isin(selected_lineas)]
sector_opts = sorted(df_f1['SECTOR'].unique().tolist())
selected_sectores = st.sidebar.multiselect("Sector:", sector_opts, default=sector_opts)

# Filtro 3: Estación
df_f2 = df_f1[df_f1['SECTOR'].isin(selected_sectores)]
estacion_opts = sorted(df_f2['ESTACION'].unique().tolist())
selected_estaciones = st.sidebar.multiselect("Estación:", estacion_opts, default=estacion_opts)

# Filtro 4: Posición
df_f3 = df_f2[df_f2['ESTACION'].isin(selected_estaciones)]
posicion_opts = sorted(df_f3['POSICIÓN'].unique().tolist())
selected_posiciones = st.sidebar.multiselect("Posición:", posicion_opts, default=posicion_opts)

# Aplicar todos los filtros
df_filtered = df[
    (df['LINEA'].isin(selected_lineas)) &
    (df['SECTOR'].isin(selected_sectores)) &
    (df['ESTACION'].isin(selected_estaciones)) &
    (df['POSICIÓN'].isin(selected_posiciones))
]

# ---------------------------------------------------------
# Indicadores Clave (KPIs)
# ---------------------------------------------------------
df_valid = df_filtered[df_filtered['LOGICA'] != '-']
total_bins = len(df_valid)
bins_ok = len(df_valid[df_valid['LOGICA'] == 'OK'])
bins_revisar = len(df_valid[df_valid['LOGICA'] == 'REVISAR'])
pct_cobertura = (bins_ok / total_bins * 100) if total_bins > 0 else 0.0

st.markdown("### 📊 Resumen de Indicadores")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric("Total Bins Asignados", f"{total_bins:,}")
kpi2.metric("Bins Abastecidos (OK)", f"{bins_ok:,}")
kpi3.metric("Bins Sin Cobertura (REVISAR)", f"{bins_revisar:,}")
kpi4.metric("% Nivel de Abastecimiento", f"{pct_cobertura:.1f}%")

st.divider()

# ---------------------------------------------------------
# Gráficos Dinámicos
# ---------------------------------------------------------
st.markdown("### 📈 Análisis Gráfico")

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Estado de Cobertura por Estación")
    df_est = df_valid.groupby(['ESTACION', 'LOGICA']).size().reset_index(name='Ctd')
    fig_est = px.bar(
        df_est, 
        x='ESTACION', 
        y='Ctd', 
        color='LOGICA',
        barmode='stack',
        title="Bins Abastecidos vs Sin Cobertura por Estación",
        color_discrete_map={'OK': '#2ca02c', 'REVISAR': '#d62728'},
        labels={'ESTACION': 'N° Estación', 'Ctd': 'Cantidad de Bins', 'LOGICA': 'Estado'}
    )
    fig_est.update_layout(xaxis_type='category', height=420)
    st.plotly_chart(fig_est, use_container_width=True)

with col_right:
    st.subheader("% Abastecimiento por Sector")
    df_sec = df_valid.groupby('SECTOR')['LOGICA'].apply(
        lambda x: (x == 'OK').sum() / len(x) * 100 if len(x) > 0 else 0
    ).reset_index(name='PCT_OK')
    
    fig_sec = px.bar(
        df_sec, 
        x='SECTOR', 
        y='PCT_OK',
        text='PCT_OK',
        title="% Cobertura por Sector / Brazo",
        color='PCT_OK',
        color_continuous_scale='RdYlGn',
        labels={'SECTOR': 'Sector', 'PCT_OK': '% Abastecido'}
    )
    fig_sec.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig_sec.update_layout(yaxis_range=[0, 110], height=420)
    st.plotly_chart(fig_sec, use_container_width=True)

col_left2, col_right2 = st.columns(2)

with col_left2:
    st.subheader("Distribución por Posición")
    df_pos = df_valid.groupby(['POSICIÓN', 'LOGICA']).size().reset_index(name='Ctd')
    fig_pos = px.bar(
        df_pos, 
        x='POSICIÓN', 
        y='Ctd', 
        color='LOGICA',
        barmode='group',
        title="Comparativo por Posición (FRONTAL / TRASERA / MUSEO)",
        color_discrete_map={'OK': '#1f77b4', 'REVISAR': '#ff7f0e'},
        labels={'POSICIÓN': 'Posición', 'Ctd': 'Cantidad de Bins'}
    )
    fig_pos.update_layout(height=400)
    st.plotly_chart(fig_pos, use_container_width=True)

with col_right2:
    st.subheader("Proporción General de Stock")
    fig_pie = px.pie(
        df_valid, 
        names='LOGICA', 
        hole=0.4,
        title="Proporción General (OK vs REVISAR)",
        color='LOGICA',
        color_discrete_map={'OK': '#2ca02c', 'REVISAR': '#d62728'}
    )
    fig_pie.update_traces(textinfo='percent+label')
    fig_pie.update_layout(height=400)
    st.plotly_chart(fig_pie, use_container_width=True)

# ---------------------------------------------------------
# Tabla de datos
# ---------------------------------------------------------
st.markdown("### 📋 Base de Datos Detallada")

selected_cols = st.multiselect(
    "Seleccionar columnas a mostrar:",
    options=df_filtered.columns.tolist(),
    default=['LINEA', 'SECTOR', 'ESTACION', 'POSICIÓN', 'UBICACIÓN', 'CM', 'DESCRIPCIÓN', 'STOCK EWM', 'STOCK MINIMO (UNIDAD)', 'LOGICA']
)

st.dataframe(df_filtered[selected_cols], use_container_width=True)