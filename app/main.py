import streamlit as st
import pandas as pd
from datetime import datetime
import os
from supabase import create_client, Client

# Configuração da página
st.set_page_config(
    page_title="Green Belt - Lean Six Sigma",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================= FUNÇÕES AUXILIARES =========================

# Inicializar Supabase
@st.cache_resource
def init_supabase():
    """Inicializa conexão com Supabase"""
    try:
        if "supabase" in st.secrets:
            url = st.secrets["supabase"]["url"]
            key = st.secrets["supabase"]["key"]
        else:
            url = os.environ.get("SUPABASE_URL", "")
            key = os.environ.get("SUPABASE_KEY", "")
        
        if url and key:
            return create_client(url, key)
        return None
    except Exception as e:
        st.error(f"Erro ao conectar com Supabase: {str(e)}")
        return None

supabase = init_supabase()

# Função para listar projetos
@st.cache_data(ttl=300)
def list_projects():
    """Lista todos os projetos disponíveis"""
    if not supabase:
        return []
    
    try:
        response = supabase.table('projects').select("*").execute()
        if response.data:
            return response.data
        return []
    except Exception as e:
        st.error(f"Erro ao listar projetos: {str(e)}")
        return []

# Função para carregar projeto
def load_project(project_name):
    """Carrega dados de um projeto específico"""
    if not supabase:
        return None
    
    try:
        response = supabase.table('projects').select("*").eq('project_name', project_name).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Erro ao carregar projeto: {str(e)}")
        return None

# ========================= INTERFACE PRINCIPAL =========================

# Header
st.title("🎯 Green Belt - Lean Six Sigma")
st.markdown("Sistema completo para gestão de projetos de melhoria contínua usando a metodologia DMAIC")

# Sidebar
with st.sidebar:
    st.header("📊 Navegação")
    
    # Status da conexão
    if supabase:
        st.success("✅ Conectado ao Supabase")
    else:
        st.warning("⚠️ Modo offline")
    
    st.divider()
    
    # Seleção de projeto
    st.subheader("🗂️ Projeto Ativo")
    
    projects = list_projects()
    
    if projects:
        # CORREÇÃO: Usar 'project_name' ao invés de 'name'
        project_names = ["Novo Projeto..."] + [p.get('project_name', 'Sem nome') for p in projects]
        
        selected_index = 0
        if 'project_name' in st.session_state:
            try:
                selected_index = project_names.index(st.session_state.project_name)
            except ValueError:
                selected_index = 0
        
        selected = st.selectbox(
            "Selecione um projeto:",
            project_names,
            index=selected_index
        )
        
        if selected != "Novo Projeto..." and selected != st.session_state.get('project_name'):
            project_data = load_project(selected)
            if project_data:
                st.session_state.project_name = selected
                st.session_state.project_data = project_data
                st.rerun()
    else:
        st.info("Nenhum projeto encontrado")
        if st.button("➕ Criar Primeiro Projeto"):
            st.switch_page("pages/1_📋_Define.py")
    
    # Mostrar informações do projeto ativo
    if 'project_name' in st.session_state and st.session_state.project_name != "Novo Projeto...":
        st.divider()
        st.caption(f"**Projeto:** {st.session_state.project_name}")
        
        if 'project_data' in st.session_state:
            project_info = st.session_state.project_data
            if project_info.get('project_leader'):
                st.caption(f"**Líder:** {project_info['project_leader']}")
            if project_info.get('start_date'):
                st.caption(f"**Início:** {project_info['start_date']}")
    
    st.divider()
    
    # Links para páginas
st.subheader("📋 Fases DMAIC")

# Criar 5 colunas para os botões ficarem lado a lado
col1, col2, col3, col4, col5 = st.columns(5)

# Botão Define
with col1:
    if st.button("🔎\nDefine", use_container_width=True, key="btn_define"):
        st.switch_page("pages/1_🔎_Define.py")

# Botão Measure
with col2:
    if st.button("🔪\nMeasure", use_container_width=True, key="btn_measure"):
        st.switch_page("pages/2_🔪_Measure.py")

# Botão Analyze
with col3:
    if st.button("📊\nAnalyze", use_container_width=True, key="btn_analyze"):
        st.switch_page("pages/3_📊_Analyze.py")

# Botão Improve
with col4:
    if st.button("🛠️\nImprove", use_container_width=True, key="btn_improve"):
        st.switch_page("pages/4_🛠️_Improve.py")

# Botão Control
with col5:
    if st.button("✅\nControl", use_container_width=True, key="btn_control"):
        st.switch_page("pages/5_✅_Control.py")

# Ferramentas adicionais
st.divider()
st.subheader("⚙️ Ferramentas")

if st.button("🔍 Diagnóstico Supabase", use_container_width=True, key="btn_diagnostico"):
    st.switch_page("pages/6_🔍_Diagnostico_Supabase.py")

# Conteúdo principal
# Criar 3 colunas para métricas
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Total de Projetos",
        value=len(projects) if projects else 0,
        delta="Ativos"
    )

with col2:
    if 'project_data' in st.session_state and st.session_state.project_data:
        baseline = st.session_state.project_data.get('baseline_value', 0)
        target = st.session_state.project_data.get('target_value', 0)
        if baseline and target:
            improvement = ((baseline - target) / baseline * 100) if baseline != 0 else 0
            st.metric(
                label="Meta de Melhoria",
                value=f"{abs(improvement):.1f}%",
                delta="Do projeto ativo"
            )
    else:
        st.metric(label="Meta de Melhoria", value="N/A")

with col3:
    if 'project_data' in st.session_state and st.session_state.project_data:
        savings = st.session_state.project_data.get('expected_savings', 0)
        st.metric(
            label="Economia Esperada",
            value=f"R$ {savings:,.0f}" if savings else "N/A"
        )
    else:
        st.metric(label="Economia Esperada", value="N/A")

st.divider()

# Tabs para diferentes visualizações
tab1, tab2, tab3, tab4 = st.tabs(["🏠 Visão Geral", "📈 Dashboard", "📚 Metodologia", "❓ Ajuda"])

# Correção da seção tab1 no arquivo main.py

with tab1:
    st.header("🏠 Visão Geral do Sistema")
    
    if 'project_name' in st.session_state and st.session_state.project_name != "Novo Projeto...":
        st.success(f"📁 Trabalhando no projeto: **{st.session_state.project_name}**")
        
        # Status das fases
        st.subheader("📊 Status das Fases DMAIC")
        
        phases = {
            "Define": {"icon": "📋", "status": "complete"},
            "Measure": {"icon": "📏", "status": "in_progress"},
            "Analyze": {"icon": "📊", "status": "pending"},
            "Improve": {"icon": "🔧", "status": "pending"},
            "Control": {"icon": "✅", "status": "pending"}
        }
        
        cols = st.columns(5)
        for i, (phase, info) in enumerate(phases.items()):
            with cols[i]:
                status_color = {
                    "complete": "#4CAF50",
                    "in_progress": "#FF9800",
                    "pending": "#9E9E9E"
                }
                status_emoji = {
                    "complete": "✅",
                    "in_progress": "🔄",
                    "pending": "⏸️"
                }
                
                st.markdown(f"""
                <div style="
                    text-align: center; 
                    padding: 20px; 
                    background: white; 
                    border: 2px solid {status_color.get(info['status'], '#9E9E9E')};
                    border-radius: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                ">
                    <div style="font-size: 2em; margin-bottom: 10px;">{info['icon']}</div>
                    <div style="color: #333; font-weight: bold; margin-bottom: 5px;">{phase}</div>
                    <div style="font-size: 1.2em;">{status_emoji.get(info['status'], '⏸️')}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("👈 Selecione ou crie um projeto para começar")
        
        # Cards de início rápido - CORRIGIDO COM CORES LEGÍVEIS
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style="
                padding: 20px; 
                background: white; 
                border: 2px solid #2196F3;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            ">
                <h3 style="color: #2196F3; margin-top: 0;">🆕 Novo Projeto</h3>
                <p style="color: #666;">Inicie um novo projeto Green Belt do zero</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Criar Projeto", use_container_width=True, key="btn_create"):
                st.switch_page("pages/1_📋_Define.py")
        
        with col2:
            st.markdown("""
            <div style="
                padding: 20px; 
                background: white; 
                border: 2px solid #9C27B0;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            ">
                <h3 style="color: #9C27B0; margin-top: 0;">📂 Projetos Existentes</h3>
                <p style="color: #666;">Continue trabalhando em um projeto em andamento</p>
            </div>
            """, unsafe_allow_html=True)
            if projects:
                st.caption(f"📊 {len(projects)} projetos disponíveis")
            else:
                st.caption("📊 Nenhum projeto ainda")
        
        with col3:
            st.markdown("""
            <div style="
                padding: 20px; 
                background: white; 
                border: 2px solid #4CAF50;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            ">
                <h3 style="color: #4CAF50; margin-top: 0;">📚 Aprender</h3>
                <p style="color: #666;">Conheça a metodologia DMAIC e suas ferramentas</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Ver Metodologia", use_container_width=True, key="btn_learn"):
                # Mudar para a tab de metodologia
                st.info("Veja a aba 'Metodologia' acima para mais informações")


with tab2:
    st.header("📈 Dashboard Executivo")
    
    if projects:
        # Criar DataFrame com os projetos
        df_projects = pd.DataFrame(projects)
        
        # Métricas gerais
        st.subheader("📊 Resumo dos Projetos")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_projects = len(df_projects)
            st.metric("Total de Projetos", total_projects)
        
        with col2:
            active_projects = len(df_projects[df_projects.get('status', 'active') == 'active']) if 'status' in df_projects.columns else total_projects
            st.metric("Projetos Ativos", active_projects)
        
        with col3:
            if 'expected_savings' in df_projects.columns:
                total_savings = df_projects['expected_savings'].sum()
                st.metric("Economia Total", f"R$ {total_savings:,.0f}")
            else:
                st.metric("Economia Total", "N/A")
        
        with col4:
            if 'project_leader' in df_projects.columns:
                unique_leaders = df_projects['project_leader'].nunique()
                st.metric("Green Belts", unique_leaders)
            else:
                st.metric("Green Belts", "N/A")
        
        # Tabela de projetos
        st.subheader("📋 Lista de Projetos")
        
        # Selecionar colunas relevantes que existem
        display_columns = []
        possible_columns = ['project_name', 'project_leader', 'status', 'start_date', 'expected_savings']
        
        for col in possible_columns:
            if col in df_projects.columns:
                display_columns.append(col)
        
        if display_columns:
            st.dataframe(
                df_projects[display_columns],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.dataframe(df_projects, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum projeto cadastrado ainda")

with tab3:
    st.header("📚 Metodologia DMAIC")
    
    st.markdown("""
    ## O que é DMAIC?
    
    DMAIC é uma metodologia estruturada de solução de problemas usada em projetos Lean Six Sigma:
    
    ### 📋 **DEFINE** - Definir
    - Definir o problema e objetivos do projeto
    - Estabelecer o escopo e metas
    - Identificar stakeholders e formar a equipe
    - Criar o Project Charter
    - Mapear o processo (SIPOC)
    - Coletar a Voz do Cliente (VOC)
    
    ### 📏 **MEASURE** - Medir
    - Estabelecer o plano de coleta de dados
    - Validar o sistema de medição (MSA)
    - Coletar dados baseline
    - Calcular a capacidade atual do processo
    - Identificar métricas-chave
    
    ### 📊 **ANALYZE** - Analisar
    - Identificar causas raiz (Ishikawa, 5 Porquês)
    - Análise de Pareto
    - Testes de hipóteses
    - Análise de correlação
    - Mapear desperdícios e gargalos
    
    ### 🔧 **IMPROVE** - Melhorar
    - Gerar soluções (Brainstorming)
    - Priorizar melhorias (Matriz Impacto x Esforço)
    - Implementar pilotos
    - Validar melhorias
    - Criar plano de implementação
    
    ### ✅ **CONTROL** - Controlar
    - Estabelecer plano de controle
    - Implementar gráficos de controle
    - Documentar novos procedimentos
    - Treinar equipe
    - Monitorar sustentabilidade
    - Documentar lições aprendidas
    
    ---
    
    ### 🎯 Benefícios do DMAIC
    
    - ✅ Abordagem estruturada e sistemática
    - ✅ Decisões baseadas em dados
    - ✅ Foco em causas raiz
    - ✅ Resultados mensuráveis
    - ✅ Sustentabilidade das melhorias
    - ✅ Redução de variabilidade
    - ✅ Aumento da satisfação do cliente
    """)

with tab4:
    st.header("❓ Ajuda e Suporte")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚀 Como Começar")
        st.markdown("""
        1. **Crie um novo projeto** na página Define
        2. **Preencha o Project Charter** com as informações básicas
        3. **Colete dados** na fase Measure
        4. **Analise as causas** do problema
        5. **Implemente melhorias** identificadas
        6. **Estabeleça controles** para sustentar os ganhos
        """)
        
        st.subheader("📖 Recursos Úteis")
        st.markdown("""
        - [Lean Six Sigma Guide](https://www.isixsigma.com)
        - [ASQ - American Society for Quality](https://asq.org)
        - [Gemba Academy](https://www.gembaacademy.com)
        """)
    
    with col2:
        st.subheader("🛠️ Ferramentas Disponíveis")
        st.markdown("""
        **Fase Define:**
        - Project Charter
        - SIPOC
        - Voice of Customer (VOC)
        
        **Fase Measure:**
        - Plano de Coleta de Dados
        - MSA (Measurement System Analysis)
        - Capacidade do Processo
        
        **Fase Analyze:**
        - Diagrama de Ishikawa
        - Análise de Pareto
        - 5 Porquês
        - Testes de Hipóteses
        
        **Fase Improve:**
        - Brainstorming
        - Matriz de Priorização
        - Plano de Ação 5W2H
        
        **Fase Control:**
        - Plano de Controle
        - Gráficos de Controle
        - Documentação de Lições
        """)
        
        st.subheader("💡 Dicas")
        st.info("""
        - Use dados sempre que possível
        - Envolva a equipe em todas as fases
        - Documente todas as decisões
        - Celebre as vitórias
        - Compartilhe aprendizados
        """)

# Footer
st.divider()
st.caption("🎯 Green Belt - Sistema de Gestão de Projetos Lean Six Sigma | Versão 1.0")
st.caption(f"Última atualização: {datetime.now().strftime('%d/%m/%Y às %H:%M')}")
