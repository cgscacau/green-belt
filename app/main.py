import streamlit as st
from pathlib import Path
import yaml

st.set_page_config(
    page_title="Greenpeace DMAIC", 
    page_icon="🌿", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Carrega configurações
CONFIG = {}
cfg_path = Path(__file__).parent / "settings.yaml"
if cfg_path.exists():
    try:
        CONFIG = yaml.safe_load(cfg_path.read_text())
    except:
        CONFIG = {}

# Header principal
st.title(f"🌿 {CONFIG.get('project_name', 'Greenpeace DMAIC')}")
st.caption(f"Sistema completo de análise DMAIC - {CONFIG.get('org', 'Greenpeace')}")

# Tabs para visão geral
tab1, tab2, tab3 = st.tabs(["📋 Sobre", "🎯 Como Usar", "📊 Status"])

with tab1:
    st.markdown("""
    ### Metodologia DMAIC
    
    **DMAIC** é uma abordagem estruturada para melhoria de processos:
    
    - **D**efine: Definir o problema e objetivos
    - **M**easure: Medir e coletar dados
    - **A**nalyze: Analisar dados e identificar causas
    - **I**mprove: Implementar melhorias
    - **C**ontrol: Controlar e monitorar resultados
    
    ### Navegação
    Use o menu lateral para navegar pelas 5 fases do DMAIC.
    """)

with tab2:
    st.markdown("""
    ### 🚀 Quick Start
    
    1. **Define** → Configure o projeto e defina objetivos
    2. **Measure** → Faça upload dos dados (CSV/Excel)
    3. **Analyze** → Execute análises estatísticas
    4. **Improve** → Crie planos de ação
    5. **Control** → Monitore indicadores
    
    ### 📁 Dados de Exemplo
    Use o arquivo `sample_data/greenpeace_example.csv` para testar.
    """)

with tab3:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Fase Atual", "Define", "Início")
    
    with col2:
        st.metric("Datasets", "0", "Aguardando upload")
    
    with col3:
        st.metric("Análises", "0", "Não iniciado")

# Footer
st.divider()
st.markdown("""
<small>💡 Dica: Comece pela página **Define** no menu lateral para configurar seu projeto.</small>
""", unsafe_allow_html=True)
