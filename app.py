import streamlit as st
import sys

# Configuración de página
st.set_page_config(
    page_title="Suite de Herramientas de Ofizant",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personalizado para mejorar el diseño
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #1f4e79 0%, #2d5aa0 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .tool-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border: 1px solid #e0e0e0;
        text-align: center;
        margin: 1rem 0;
        transition: transform 0.2s;
    }
    
    .tool-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }
    
    .tool-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    
    .tool-title {
        font-size: 1.5rem;
        font-weight: bold;
        color: #1f4e79;
        margin-bottom: 0.5rem;
    }
    
    .tool-description {
        color: #666;
        margin-bottom: 1.5rem;
    }
    
    .coming-soon {
        opacity: 0.6;
        background: #f8f9fa;
    }
    
    .footer {
        text-align: center;
        margin-top: 3rem;
        padding: 2rem;
        color: #666;
        border-top: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# Header principal
st.markdown("""
<div class="main-header">
    <h1>🏢 Suite de Herramientas de Ofizant</h1>
    <p style="font-size: 1.2rem; margin-top: 1rem;">
        Herramientas especializadas para optimizar los procesos de tu negocio
    </p>
</div>
""", unsafe_allow_html=True)

# Botón de cerrar app en la parte superior
col1, col2, col3 = st.columns([1, 2, 1])
with col3:
    if st.button("❌ Cerrar App", type="secondary", help="Cierra completamente la aplicación"):
        st.markdown("<h2 style='text-align:center'>👋 La aplicación ha sido cerrada</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#666; margin-top:2rem;'>Gracias por usar las herramientas de Ofizant</p>", unsafe_allow_html=True)
        st.stop()

st.markdown("---")

# Herramientas disponibles
st.markdown("### 🛠️ Herramientas Disponibles")

# Layout de herramientas en columnas
col1, col2, col3 = st.columns(3)

# Herramienta 1: Conciliación Bancaria
with col1:
    st.markdown("""
    <div class="tool-card">
        <div class="tool-icon">🏦</div>
        <div class="tool-title">Conciliación Bancaria</div>
        <div class="tool-description">
            Automatiza la conciliación entre registros del Mayor y extractos bancarios.
            Incluye tolerancias de fecha y valor para mayor flexibilidad.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚀 Abrir Conciliación", key="conciliacion", type="primary", use_container_width=True):
        st.switch_page("pages/1_Conciliacion.py")

# Herramienta 2: Próximamente
with col2:
    st.markdown("""
    <div class="tool-card coming-soon">
        <div class="tool-icon">📊</div>
        <div class="tool-title">Reportes Financieros</div>
        <div class="tool-description">
            Genera reportes automáticos y análisis de datos financieros.
            <br><em>Próximamente...</em>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.button("🔒 Próximamente", key="reportes", disabled=True, use_container_width=True)

# Herramienta 3: Próximamente
with col3:
    st.markdown("""
    <div class="tool-card coming-soon">
        <div class="tool-icon">📈</div>
        <div class="tool-title">Análisis de Datos</div>
        <div class="tool-description">
            Herramientas avanzadas para análisis y visualización de datos empresariales.
            <br><em>Próximamente...</em>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.button("🔒 Próximamente", key="analisis", disabled=True, use_container_width=True)

# Información adicional
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### ℹ️ Información")
    st.markdown("""
    - **Versión**: 1.0.0
    - **Desarrollado por**: Ofizant
    - **Soporte**: Contacta a tu equipo de desarrollo
    """)

with col2:
    st.markdown("### 🎯 Características")
    st.markdown("""
    - ✅ Interfaz intuitiva y fácil de usar
    - ✅ Procesamiento rápido de datos
    - ✅ Exportación de resultados
    - ✅ Tolerancias configurables
    """)

# Footer
st.markdown("""
<div class="footer">
    <p>© 2024 Ofizant - Suite de Herramientas Empresariales</p>
    <p><em>Optimizando procesos, maximizando resultados</em></p>
</div>
""", unsafe_allow_html=True)