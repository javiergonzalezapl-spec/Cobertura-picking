import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------
# 1. Configuración de la página
# ---------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Cobertura de Stock Mínimo - Líneas 1 y 2",
    page_icon="📦",
    layout="wide"
)

# ---------------------------------------------------------
# MÓDULO DE AUTENTICACIÓN / ACCESO PRIVADO
# ---------------------------------------------------------
def check_password():
    """Retorna True si el usuario ingresó la contraseña correcta."""
    def password_entered():
        if st.session_state["password_input"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password_input"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("🔒 Ingresa la clave de acceso:", type="password", on_change=password_entered, key="password_input")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("🔒 Clave incorrecta. Inténtalo de nuevo:", type="password", on_change=password_entered, key="password_input")
        st.error("Acceso denegado")
        return False
    else:
        return True

# Si la contraseña no es correcta, detiene la ejecución del dashboard
if not check_password():
    st.stop()

# ---------------------------------------------------------
# 2. Configuración de la página
# ---------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Cobertura de Stock Mínimo - Líneas 1 y 2",
    page_icon="📦",
    layout="wide"
)

# Estilos CSS para replicar las tarjetas de indicadores de los ejemplos
st.markdown("""
<style>
    .kpi-card {
        background-color: #FFFFFF;
        border-radius: 6px;
        padding: 15px 18px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.08);
        border: 1px solid #E2E8F0;
        margin-bottom: 15px;
    }
    .kpi-title {
        font-size: 11px;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 800;
        margin-bottom: 2px;
        line-height: 1.1;
    }
    .kpi-sub {
        font-size: 11px;
        color: #94A3B8;
        margin: 0;
    }
    .card-total { border-top: 5px solid #002060; }
    .card-total .kpi-value { color: #002060; }
    
    .card-ok { border-top: 5px solid #0066C0; }
    .card-ok .kpi-value { color: #0066C0; }
    
    .card-l2 { border-top: 5px solid #F59E0B; }
    .card-l2 .kpi-value { color: #D97706; }
    
    .card-danger { border-top: 5px solid #E53935; }
    .card-danger .kpi-value { color: #E53935; }
</style>
""", unsafe_allow_html=True)

# Paletas de color exactas
COLOR_OK_L1 = '#0066C0'       # Azul Natura L1
COLOR_OK_L2 = '#F59E0B'       # Amarillo / Ámbar L2
COLOR_QUIEBRE = '#E53935'     # Rojo Quiebre / Sin Cobertura
COLOR_STACK_BG = '#D1E8FF'    # Azul claro para fondo de Bins Sin Cobertura

# ---------------------------------------------------------
# 3. Carga y preparación de datos
# ---------------------------------------------------------
@st.cache_data
def load_data(file_path_or_buffer):
    df_l1 = pd.read_excel(file_path_or_buffer, sheet_name='ANALISIS L1')
    df_l2 = pd.read_excel(file_path_or_buffer, sheet_name='ANALISIS L2')
    
    df_l1.columns = df_l1.columns.str.strip()
    df_l2.columns = df_l2.columns.str.strip()
    
    df = pd.concat([df_l1, df_l2], ignore_index=True)
    
    df['ESTACION'] = df['ESTACION'].astype(str)
    df['POSICIÓN'] = df['POSICIÓN'].astype(str)
    df['SECTOR'] = df['SECTOR'].astype(str)
    df['LINEA'] = df['LINEA'].astype(str)
    df['LOGICA'] = df['LOGICA'].fillna('-').astype(str)
    
    return df, df_l1, df_l2

uploaded_file = st.file_uploader("Sube la base de Cobertura (.xlsm / .xlsx)", type=['xlsx', 'xlsm'])

if uploaded_file is not None:
    df_all, df_l1_raw, df_l2_raw = load_data(uploaded_file)
else:
    try:
        try:
            df_all, df_l1_raw, df_l2_raw = load_data("Cobertura de abastecimiento de Línea de picking.xlsm")
        except Exception:
            df_all, df_l1_raw, df_l2_raw = load_data("Cobertura de abastecimiento de Línea de picking.xlsx")
    except Exception:
        st.info("Por favor, sube el archivo 'Cobertura de abastecimiento de Línea de picking.xlsm' para continuar.")
        st.stop()

# Funciones auxiliares para gráficos
def create_donut_chart(title, ok_count, quiebre_count, ok_color):
    labels = ['Bins Abastecidos OK', 'Bins Sin Cobertura']
    values = [ok_count, quiebre_count]
    colors = [ok_color, COLOR_QUIEBRE]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.5,
        marker=dict(colors=colors),
        textinfo='percent',
        textfont_size=14,
        hovertemplate="<b>%{label}</b><br>Cantidad: %{value:,}<br>Porcentaje: %{percent}<extra></extra>"
    )])
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", x=0.5, xanchor='center', font=dict(size=14, color='#002060')),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
        height=380,
        margin=dict(l=20, r=20, t=50, b=40),
        paper_bgcolor='white',
        plot_bgcolor='white'
    )
    return fig

def create_station_combo_chart(df_line, title, bar_color):
    df_v = df_line[df_line['LOGICA'] != '-'].copy()
    
    # Agrupación por estación
    grp = df_v.groupby(['ESTACION', 'LOGICA']).size().unstack(fill_value=0)
    if 'OK' not in grp.columns: grp['OK'] = 0
    if 'REVISAR' not in grp.columns: grp['REVISAR'] = 0
    
    grp['TOTAL'] = grp['OK'] + grp['REVISAR']
    grp['PCT_OK'] = (grp['OK'] / grp['TOTAL'] * 100).round(0)
    grp = grp.reset_index()
    
    # Orden numérico / alfabético razonable
    try:
        grp['EST_NUM'] = pd.to_numeric(grp['ESTACION'])
        grp = grp.sort_values('EST_NUM')
    except Exception:
        grp = grp.sort_values('ESTACION')
        
    fig = go.Figure()
    
    # Barra apilada: Bins Abastecidos OK
    fig.add_trace(go.Bar(
        x=grp['ESTACION'],
        y=grp['OK'],
        name='(Ctd.) BINS ABASTECIDOS',
        marker_color=bar_color,
        hovertemplate="Estación %{x}<br>Abastecidos: %{y}<extra></extra>"
    ))
    
    # Barra apilada: Bins Sin Cobertura
    fig.add_trace(go.Bar(
        x=grp['ESTACION'],
        y=grp['REVISAR'],
        name='(Ctd.) BINS SIN COBERTURA',
        marker_color=COLOR_STACK_BG,
        hovertemplate="Estación %{x}<br>Sin Cobertura: %{y}<extra></extra>"
    ))
    
    # Línea con marcadores: % Abastecido
    fig.add_trace(go.Scatter(
        x=grp['ESTACION'],
        y=grp['PCT_OK'],
        name='(%) ABASTECIDO',
        mode='lines+markers+text',
        line=dict(color=COLOR_QUIEBRE, width=2.5),
        marker=dict(size=6, color=COLOR_QUIEBRE),
        text=grp['PCT_OK'].astype(int).astype(str) + '%',
        textposition='top center',
        textfont=dict(size=10, color='black'),
        yaxis='y2',
        hovertemplate="Estación %{x}<br>Cobertura: %{y}%<extra></extra>"
    ))
    
    fig.update_layout(
        title=dict(text=f"<b>{title}</b><br><sup>( (%) de UBICACIONES abastecidas sobre el total de posiciones por estación. )</sup>", x=0.5, xanchor='center'),
        barmode='stack',
        height=380,
        margin=dict(l=30, r=30, t=60, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        xaxis=dict(type='category', title=None),
        yaxis=dict(title=None, showgrid=True, gridcolor='#F1F5F9'),
        yaxis2=dict(title=None, overlaying='y', side='right', range=[0, 115], showgrid=False, ticksuffix='%'),
        paper_bgcolor='white',
        plot_bgcolor='white'
    )
    return fig

# ---------------------------------------------------------
# 4. PESTAÑAS PRINCIPALES DEL DASHBOARD
# ---------------------------------------------------------
tab_consolidado, tab_l1, tab_l2, tab_estacion, tab_tabla = st.tabs([
    "📊 Resumen Consolidado (L1 + L2)", 
    "🔵 Línea 1", 
    "🟡 Línea 2", 
    "🎯 Estatus por Estación",
    "📋 Detalle de Datos"
])

# =================================----------------========
# TAB 1: RESUMEN CONSOLIDADO (L1 + L2)
# =================================----------------========
with tab_consolidado:
    st.markdown("## 📊📊 Resumen de Indicadores Consolidado")
    
    df_valid_all = df_all[df_all['LOGICA'] != '-']
    tot_all = len(df_valid_all)
    ok_all = len(df_valid_all[df_valid_all['LOGICA'] == 'OK'])
    rev_all = len(df_valid_all[df_valid_all['LOGICA'] == 'REVISAR'])
    pct_ok_all = (ok_all / tot_all * 100) if tot_all > 0 else 0
    pct_rev_all = (rev_all / tot_all * 100) if tot_all > 0 else 0
    
    # Tarjetas de Indicadores Generales (Estilo Imagen 1 y 2)
    c1, c2, k3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="kpi-card card-total">
            <div class="kpi-title">TOTAL BINS PICKING</div>
            <div class="kpi-value">{tot_all:,}</div>
            <div class="kpi-sub">Posiciones evaluadas en L1 y L2</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card card-ok">
            <div class="kpi-title">COBERTURA TOTAL</div>
            <div class="kpi-value">{pct_ok_all:.1f}%</div>
            <div class="kpi-sub">{ok_all:,} Bins Abastecidos OK</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class="kpi-card card-danger">
            <div class="kpi-title">QUIEBRE DE STOCK</div>
            <div class="kpi-value">{pct_rev_all:.1f}%</div>
            <div class="kpi-sub">{rev_all:,} Bins bajo stock mínimo</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Gráficos Consolidados
    col_g1, col_g2 = st.columns([1, 1])
    
    with col_g1:
        fig_donut_all = create_donut_chart("COBERTURA ABASTECIMIENTO: ESTATUS LÍNEA 1-2", ok_all, rev_all, COLOR_OK_L1)
        st.plotly_chart(fig_donut_all, use_container_width=True)
        
    with col_g2:
        # Comparativo L1 vs L2 (Imagen 3)
        df_l1_v = df_all[(df_all['LINEA'] == 'L1') & (df_all['LOGICA'] != '-')]
        df_l2_v = df_all[(df_all['LINEA'] == 'L2') & (df_all['LOGICA'] != '-')]
        
        ok_l1 = (df_l1_v['LOGICA'] == 'OK').sum()
        rev_l1 = (df_l1_v['LOGICA'] == 'REVISAR').sum()
        ok_l2 = (df_l2_v['LOGICA'] == 'OK').sum()
        rev_l2 = (df_l2_v['LOGICA'] == 'REVISAR').sum()
        
        sub_c1, sub_c2 = st.columns(2)
        with sub_c1:
            fig_d_l1 = create_donut_chart("COBERTURA LÍNEA 1 (%)", ok_l1, rev_l1, COLOR_OK_L1)
            st.plotly_chart(fig_d_l1, use_container_width=True)
        with sub_c2:
            fig_d_l2 = create_donut_chart("COBERTURA LÍNEA 2 (%)", ok_l2, rev_l2, COLOR_OK_L2)
            st.plotly_chart(fig_d_l2, use_container_width=True)

    st.markdown("---")
    st.subheader("Nivel de Abastecimiento por Estación (Línea 1 y Línea 2)")
    fig_st_l1 = create_station_combo_chart(df_all[df_all['LINEA'] == 'L1'], "COBERTURA DE ABASTECIMIENTO POR ESTACIÓN - LÍNEA 1", COLOR_OK_L1)
    st.plotly_chart(fig_st_l1, use_container_width=True)
    
    fig_st_l2 = create_station_combo_chart(df_all[df_all['LINEA'] == 'L2'], "COBERTURA DE ABASTECIMIENTO POR ESTACIÓN - LÍNEA 2", COLOR_OK_L2)
    st.plotly_chart(fig_st_l2, use_container_width=True)

# =================================----------------========
# TAB 2: EXCLUSIVA LÍNEA 1
# =================================----------------========
with tab_l1:
    st.markdown("## 🔵 Exclusivo Línea 1")
    df_l1 = df_all[df_all['LINEA'] == 'L1']
    df_l1_valid = df_l1[df_l1['LOGICA'] != '-']
    
    t_l1 = len(df_l1_valid)
    ok_l1_cnt = (df_l1_valid['LOGICA'] == 'OK').sum()
    rev_l1_cnt = (df_l1_valid['LOGICA'] == 'REVISAR').sum()
    pct_ok_l1 = (ok_l1_cnt / t_l1 * 100) if t_l1 > 0 else 0
    pct_rev_l1 = (rev_l1_cnt / t_l1 * 100) if t_l1 > 0 else 0
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="kpi-card card-total">
            <div class="kpi-title">LÍNEA 1 - TOTAL BINS</div>
            <div class="kpi-value">{t_l1:,}</div>
            <div class="kpi-sub">Posiciones evaluadas en L1</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card card-ok">
            <div class="kpi-title">LÍNEA 1 - COBERTURA</div>
            <div class="kpi-value">{pct_ok_l1:.1f}%</div>
            <div class="kpi-sub">{ok_l1_cnt:,} Bins OK</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card card-danger">
            <div class="kpi-title">LÍNEA 1 - QUIEBRE</div>
            <div class="kpi-value">{pct_rev_l1:.1f}%</div>
            <div class="kpi-sub">{rev_l1_cnt:,} Bins en Quiebre</div>
        </div>
        """, unsafe_allow_html=True)
        
    col_a, col_b = st.columns([1, 2])
    with col_a:
        fig_d = create_donut_chart("ESTATUS LÍNEA 1", ok_l1_cnt, rev_l1_cnt, COLOR_OK_L1)
        st.plotly_chart(fig_d, use_container_width=True)
    with col_b:
        fig_st = create_station_combo_chart(df_l1, "COBERTURA POR ESTACIÓN - LÍNEA 1", COLOR_OK_L1)
        st.plotly_chart(fig_st, use_container_width=True)

# =================================----------------========
# TAB 3: EXCLUSIVA LÍNEA 2
# =================================----------------========
with tab_l2:
    st.markdown("## 🟡 Exclusivo Línea 2")
    df_l2 = df_all[df_all['LINEA'] == 'L2']
    df_l2_valid = df_l2[df_l2['LOGICA'] != '-']
    
    t_l2 = len(df_l2_valid)
    ok_l2_cnt = (df_l2_valid['LOGICA'] == 'OK').sum()
    rev_l2_cnt = (df_l2_valid['LOGICA'] == 'REVISAR').sum()
    pct_ok_l2 = (ok_l2_cnt / t_l2 * 100) if t_l2 > 0 else 0
    pct_rev_l2 = (rev_l2_cnt / t_l2 * 100) if t_l2 > 0 else 0
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="kpi-card card-total">
            <div class="kpi-title">LÍNEA 2 - TOTAL BINS</div>
            <div class="kpi-value">{t_l2:,}</div>
            <div class="kpi-sub">Posiciones evaluadas en L2</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card card-l2">
            <div class="kpi-title">LÍNEA 2 - COBERTURA</div>
            <div class="kpi-value">{pct_ok_l2:.1f}%</div>
            <div class="kpi-sub">{ok_l2_cnt:,} Bins OK</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card card-danger">
            <div class="kpi-title">LÍNEA 2 - QUIEBRE</div>
            <div class="kpi-value">{pct_rev_l2:.1f}%</div>
            <div class="kpi-sub">{rev_l2_cnt:,} Bins en Quiebre</div>
        </div>
        """, unsafe_allow_html=True)
        
    col_a, col_b = st.columns([1, 2])
    with col_a:
        fig_d = create_donut_chart("ESTATUS LÍNEA 2", ok_l2_cnt, rev_l2_cnt, COLOR_OK_L2)
        st.plotly_chart(fig_d, use_container_width=True)
    with col_b:
        fig_st = create_station_combo_chart(df_l2, "COBERTURA POR ESTACIÓN - LÍNEA 2", COLOR_OK_L2)
        st.plotly_chart(fig_st, use_container_width=True)

# =================================----------------========
# TAB 4: ESTATUS POR ESTACIÓN (Filtro detalle Imagen 5)
# =================================----------------========
with tab_estacion:
    st.markdown("## 🎯 Estatus Detallado por Estación")
    
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        linea_sel = st.selectbox("Seleccionar Línea:", options=['L1', 'L2'])
    
    df_st_subset = df_all[df_all['LINEA'] == linea_sel]
    estaciones_list = sorted(df_st_subset['ESTACION'].unique().tolist())
    
    with col_sel2:
        estacion_sel = st.selectbox("Seleccionar N° Estación:", options=estaciones_list)
        
    df_est_data = df_st_subset[df_st_subset['ESTACION'] == estacion_sel]
    df_est_valid = df_est_data[df_est_data['LOGICA'] != '-']
    
    tot_e = len(df_est_valid)
    ok_e = (df_est_valid['LOGICA'] == 'OK').sum()
    rev_e = (df_est_valid['LOGICA'] == 'REVISAR').sum()
    pct_e = (ok_e / tot_e * 100) if tot_e > 0 else 0
    
    st.markdown(f"### ESTACIÓN {estacion_sel} - {linea_sel} - (ESTATUS POR UBICACIÓN)")
    
    ec1, ec2, ec3 = st.columns(3)
    with ec1:
        st.markdown(f"""
        <div class="kpi-card card-danger">
            <div class="kpi-title">ESTATUS ESTACIÓN</div>
            <div class="kpi-value">{pct_e:.1f}%</div>
            <div class="kpi-sub">ESTACIÓN CRÍTICA | Revisar cobertura</div>
        </div>
        """, unsafe_allow_html=True)
    with ec2:
        st.markdown(f"""
        <div class="kpi-card card-ok">
            <div class="kpi-title">UBICACIONES OK</div>
            <div class="kpi-value">{ok_e} Bins</div>
            <div class="kpi-sub">Stock >= Stock Mínimo Requerido</div>
        </div>
        """, unsafe_allow_html=True)
    with ec3:
        st.markdown(f"""
        <div class="kpi-card card-danger">
            <div class="kpi-title">UBICACIONES CON QUIEBRE</div>
            <div class="kpi-value">{rev_e} Bins</div>
            <div class="kpi-sub">Stock < Stock Mínimo Requerido</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("#### Ubicaciones con Quiebre / Bajo Stock Mínimo")
    df_quiebres = df_est_data[df_est_data['LOGICA'] == 'REVISAR'].copy()
    
    if len(df_quiebres) > 0:
        # Calcular Faltante si existen las columnas
        try:
            df_quiebres['STOCK EWM NUM'] = pd.to_numeric(df_quiebres['STOCK EWM'], errors='coerce').fillna(0)
            df_quiebres['MIN NUM'] = pd.to_numeric(df_quiebres['STOCK MINIMO (UNIDAD)'], errors='coerce').fillna(0)
            df_quiebres['CANTIDAD QUIEBRE'] = df_quiebres['MIN NUM'] - df_quiebres['STOCK EWM NUM']
            df_quiebres['CANTIDAD QUIEBRE'] = df_quiebres['CANTIDAD QUIEBRE'].apply(lambda x: f"{max(0, int(x))} Unid.")
        except Exception:
            df_quiebres['CANTIDAD QUIEBRE'] = 'Revisar'
            
        cols_disp = ['ESTACION', 'POSICIÓN', 'UBICACIÓN', 'CM', 'DESCRIPCIÓN', 'UXC', 'CANTIDAD QUIEBRE']
        cols_disp = [c for c in cols_disp if c in df_quiebres.columns]
        st.dataframe(df_quiebres[cols_disp], use_container_width=True)
    else:
        st.success("🎉 ¡Excelente! Esta estación no presenta ubicaciones en quiebre.")

# =================================----------------========
# TAB 5: TABLA DE DATOS Y FILTROS GLOBALES
# =================================----------------========
with tab_tabla:
    st.markdown("## 📋 Filtros Globales y Base Detallada")
    
    st.sidebar.header("🔍 Filtros Globales")
    
    selected_lineas = st.sidebar.multiselect("Línea:", sorted(df_all['LINEA'].unique()), default=sorted(df_all['LINEA'].unique()))
    
    df_f1 = df_all[df_all['LINEA'].isin(selected_lineas)]
    selected_sectores = st.sidebar.multiselect("Sector:", sorted(df_f1['SECTOR'].unique()), default=sorted(df_f1['SECTOR'].unique()))
    
    df_f2 = df_f1[df_f1['SECTOR'].isin(selected_sectores)]
    selected_estaciones = st.sidebar.multiselect("Estación:", sorted(df_f2['ESTACION'].unique()), default=sorted(df_f2['ESTACION'].unique()))
    
    df_f3 = df_f2[df_f2['ESTACION'].isin(selected_estaciones)]
    selected_posiciones = st.sidebar.multiselect("Posición:", sorted(df_f3['POSICIÓN'].unique()), default=sorted(df_f3['POSICIÓN'].unique()))
    
    df_filtered = df_all[
        (df_all['LINEA'].isin(selected_lineas)) &
        (df_all['SECTOR'].isin(selected_sectores)) &
        (df_all['ESTACION'].isin(selected_estaciones)) &
        (df_all['POSICIÓN'].isin(selected_posiciones))
    ]
    
    st.write(f"Mostrando **{len(df_filtered):,}** registros filtrados:")
    
    default_cols = ['LINEA', 'SECTOR', 'ESTACION', 'POSICIÓN', 'UBICACIÓN', 'CM', 'DESCRIPCIÓN', 'STOCK EWM', 'STOCK MINIMO (UNIDAD)', 'LOGICA']
    selected_cols = st.multiselect("Seleccionar columnas a mostrar:", options=df_all.columns.tolist(), default=[c for c in default_cols if c in df_all.columns])
    
    st.dataframe(df_filtered[selected_cols], use_container_width=True)
