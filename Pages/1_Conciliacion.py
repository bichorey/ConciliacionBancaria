# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import sys
import os

# Agregar la carpeta padre al path para importar reconciliacion
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reconciliacion import conciliacion_mvp, is_previous_result, extract_mayor_from_previous, merge_with_previous

# Configuración de página
st.set_page_config(
    page_title="Conciliación Bancaria - Ofizant",
    page_icon="🏦",
    layout="wide"
)

# CSS personalizado
st.markdown("""
<style>
    .nav-buttons {
        position: fixed;
        top: 10px;
        right: 10px;
        z-index: 999;
        background: white;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .main-title {
        text-align: center;
        color: #1f4e79;
        margin-bottom: 2rem;
    }
    
    .section-header {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .app-closed {
        text-align: center;
        padding: 3rem 2rem;
        background: linear-gradient(90deg, #1f4e79 0%, #2d5aa0 100%);
        color: white;
        border-radius: 15px;
        margin: 2rem auto;
        max-width: 600px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    .app-closed h2 {
        font-size: 2.5rem;
        margin-bottom: 1rem;
        font-weight: 300;
    }
    
    .app-closed p {
        font-size: 1.2rem;
        opacity: 0.9;
        margin-top: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Botones de navegación fijos
st.markdown("""
<div class="nav-buttons">
""", unsafe_allow_html=True)

col_nav1, col_nav2 = st.columns(2)
with col_nav1:
    if st.button("🏠 Inicio", help="Volver a la página principal"):
        st.switch_page("app.py")

with col_nav2:
    if st.button("❌ Cerrar", help="Cerrar aplicación"):
        st.markdown("""
        <div class="app-closed">
            <h2>👋 La aplicación ha sido cerrada</h2>
            <p>Gracias por usar las herramientas de Ofizant</p>
            <p style="font-size: 1rem; margin-top: 2rem; opacity: 0.7;">
                Puedes cerrar esta pestaña del navegador
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

st.markdown("</div>", unsafe_allow_html=True)

# Título principal
st.markdown("""
<div class="main-title">
    <h1>🏦 Conciliación Bancaria</h1>
    <p>Automatiza la conciliación entre registros del Mayor y extractos bancarios</p>
</div>
""", unsafe_allow_html=True)

# Sidebar con controles
st.sidebar.header("⚙️ Configuración")

# Controles de tolerancia
st.sidebar.subheader("📅 Tolerancia de Fechas")
tolerancia_dias = st.sidebar.number_input(
    "Días de diferencia permitidos",
    min_value=0,
    max_value=365,
    value=3,
    help="Número máximo de días de diferencia entre fechas para considerar una conciliación válida"
)

st.sidebar.subheader("💰 Tolerancia de Valor")
tolerancia_valor = st.sidebar.number_input(
    "Diferencia de importe permitida",
    min_value=0.0,
    max_value=999.99,
    value=0.0,
    step=0.01,
    format="%.2f",
    help="Diferencia máxima permitida entre importes para considerar una conciliación válida (ej: 0.50 para 50 centavos)"
)

# Controles de agrupación
st.sidebar.subheader("🔗 Agrupación")
max_items_grupo = st.sidebar.number_input(
    "Máximo de registros por grupo",
    min_value=1,
    max_value=10,
    value=3,
    help="Número máximo de registros del Mayor que se pueden agrupar para conciliar con un registro del Banco"
)

direccion = st.sidebar.selectbox(
    "Dirección de agrupación",
    ["MAYOR→BANCO", "BANCO→MAYOR"],
    help="Dirección para la agrupación: varios registros del Mayor hacia uno del Banco, o viceversa"
)

# Sección principal
st.markdown('<div class="section-header"><h3>📁 Carga de Archivos</h3></div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Archivo del Mayor")
    mayor_file = st.file_uploader(
        "Selecciona el archivo del Mayor",
        type=['csv', 'xlsx', 'xls'],
        key="mayor_upload",
        help="Archivo con los registros contables del Mayor"
    )

with col2:
    st.subheader("🏦 Archivo del Banco")
    banco_file = st.file_uploader(
        "Selecciona el archivo del Banco",
        type=['csv', 'xlsx', 'xls'],
        key="banco_upload",
        help="Archivo con el extracto bancario"
    )

# Opción de resultado previo
st.markdown('<div class="section-header"><h3>🔄 Resultado Previo (Opcional)</h3></div>', unsafe_allow_html=True)

resultado_previo_file = st.file_uploader(
    "Archivo de resultado previo para combinar",
    type=['csv', 'xlsx', 'xls'],
    key="previo_upload",
    help="Archivo de un resultado de conciliación anterior que se combinará con el nuevo resultado"
)

# Función para cargar archivos
@st.cache_data
def load_file(file):
    """Carga un archivo CSV o Excel"""
    if file is None:
        return None
    
    try:
        if file.name.endswith('.csv'):
            return pd.read_csv(file)
        else:
            return pd.read_excel(file)
    except Exception as e:
        st.error(f"Error al cargar el archivo {file.name}: {str(e)}")
        return None

# Función para convertir DataFrame a Excel
@st.cache_data
def convert_to_excel(df):
    """Convierte DataFrame a bytes de Excel"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Conciliacion')
    return output.getvalue()

# Procesamiento principal
if mayor_file is not None and banco_file is not None:
    
    # Cargar archivos
    with st.spinner("Cargando archivos..."):
        df_mayor = load_file(mayor_file)
        df_banco = load_file(banco_file)
        df_previo = load_file(resultado_previo_file) if resultado_previo_file else None
    
    if df_mayor is not None and df_banco is not None:
        
        # Mostrar información de los archivos
        st.markdown('<div class="section-header"><h3>📋 Información de Archivos</h3></div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📊 Registros Mayor", len(df_mayor))
            
        with col2:
            st.metric("🏦 Registros Banco", len(df_banco))
            
        with col3:
            if df_previo is not None:
                st.metric("🔄 Registros Previos", len(df_previo))
            else:
                st.metric("🔄 Registros Previos", 0)
        
        # Botón de procesamiento
        if st.button("🚀 Ejecutar Conciliación", type="primary", use_container_width=True):
            
            with st.spinner("Procesando conciliación..."):
                try:
                    # Determinar el DataFrame del Mayor a usar
                    if df_previo is not None and is_previous_result(df_previo):
                        st.info("📋 Detectado resultado previo. Extrayendo datos del Mayor...")
                        df_mayor_usar = extract_mayor_from_previous(df_previo)
                    else:
                        df_mayor_usar = df_mayor
                    
                    # Ejecutar conciliación
                    detalle, resumen = conciliacion_mvp(
                        df_mayor_usar,
                        df_banco,
                        tolerancia_dias=tolerancia_dias,
                        max_items_grupo=max_items_grupo,
                        direccion=direccion,
                        tolerancia_valor=tolerancia_valor
                    )
                    
                    # Combinar con resultado previo si existe
                    if df_previo is not None and is_previous_result(df_previo):
                        st.info("🔗 Combinando con resultado previo...")
                        detalle = merge_with_previous(df_previo, detalle)
                        resumen = detalle["estado"].value_counts().rename_axis("estado").reset_index(name="cantidad")
                    
                    # Guardar en session_state
                    st.session_state['detalle'] = detalle
                    st.session_state['resumen'] = resumen
                    
                    st.success("✅ Conciliación completada exitosamente!")
                    
                except Exception as e:
                    st.error(f"❌ Error durante la conciliación: {str(e)}")
                    st.exception(e)

# Mostrar resultados si existen
if 'detalle' in st.session_state and 'resumen' in st.session_state:
    
    detalle = st.session_state['detalle']
    resumen = st.session_state['resumen']
    
    st.markdown('<div class="section-header"><h3>📊 Resultados de la Conciliación</h3></div>', unsafe_allow_html=True)
    
    # Resumen en métricas
    col1, col2, col3, col4 = st.columns(4)
    
    total_registros = len(detalle)
    conciliados = len(detalle[detalle['estado'].str.contains('Conciliado', na=False)])
    solo_mayor = len(detalle[detalle['estado'] == 'Solo en Mayor'])
    solo_banco = len(detalle[detalle['estado'] == 'Solo en Banco'])
    
    with col1:
        st.metric("📋 Total Registros", total_registros)
    with col2:
        st.metric("✅ Conciliados", conciliados)
    with col3:
        st.metric("📊 Solo en Mayor", solo_mayor)
    with col4:
        st.metric("🏦 Solo en Banco", solo_banco)
    
    # Resumen detallado
    st.subheader("📈 Resumen por Estado")
    st.dataframe(resumen, use_container_width=True)
    
    # Detalle completo
    st.subheader("📋 Detalle Completo")
    st.dataframe(detalle, use_container_width=True)
    
    # Botones de descarga
    st.markdown('<div class="section-header"><h3>💾 Descargar Resultados</h3></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Descarga del detalle
        excel_data = convert_to_excel(detalle)
        st.download_button(
            label="📥 Descargar Detalle (Excel)",
            data=excel_data,
            file_name=f"conciliacion_detalle_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with col2:
        # Descarga del resumen
        resumen_excel = convert_to_excel(resumen)
        st.download_button(
            label="📊 Descargar Resumen (Excel)",
            data=resumen_excel,
            file_name=f"conciliacion_resumen_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# Información de ayuda
with st.expander("ℹ️ Ayuda y Documentación"):
    st.markdown("""
    ### 🔧 Cómo usar esta herramienta:
    
    1. **Carga de archivos**: Selecciona los archivos del Mayor y del Banco en formato CSV o Excel.
    
    2. **Configuración de tolerancias**:
       - **Tolerancia de fechas**: Días de diferencia permitidos entre fechas
       - **Tolerancia de valor**: Diferencia máxima permitida entre importes
    
    3. **Agrupación**: Configura si quieres agrupar varios registros del Mayor con uno del Banco.
    
    4. **Resultado previo**: Opcionalmente, carga un resultado anterior para combinarlo con el nuevo.
    
    ### 📊 Estados de conciliación:
    - **Conciliado exacto**: Fechas e importes coinciden exactamente
    - **Conciliado por tolerancia de fecha**: Importes iguales, fechas dentro de tolerancia
    - **Conciliado por tolerancia de valor**: Fechas iguales, importes dentro de tolerancia
    - **Conciliado por agrupación**: Varios registros del Mayor suman el importe del Banco
    - **Solo en Mayor**: Registros que no tienen correspondencia en el Banco
    - **Solo en Banco**: Registros que no tienen correspondencia en el Mayor
    
    ### 💡 Consejos:
    - Ajusta las tolerancias según tus necesidades específicas
    - Usa la agrupación para casos donde varios pagos se consolidan en una transferencia
    - Guarda los resultados para futuras referencias o combinaciones
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🏢 <strong>Ofizant</strong> - Conciliación Bancaria v1.0</p>
    <p><em>Optimizando procesos financieros</em></p>
</div>
""", unsafe_allow_html=True)