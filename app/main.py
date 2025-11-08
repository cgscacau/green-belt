# main.py ou Home.py
import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

# Configuração da página
st.set_page_config(
    page_title="Green Belt Project Management System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #2E7D32;
        text-align: center;
        margin-bottom: 2rem;
    }
    .phase-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Inicializar Supabase
try:
    from supabase import create_client, Client
    
    @st.cache_resource
    def init_supabase():
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "")
        if url and key:
            return create_client(url, key)
        return None
    
    supabase = init_supabase()
except Exception as e:
    st.error(f"Erro ao conectar com Supabase: {e}")
    supabase = None

# Inicializar session state
if 'current_project_id' not in st.session_state:
    st.session_state.current_project_id = None
if 'current_project_name' not in st.session_state:
    st.session_state.current_project_name = None
if 'current_phase' not in st.session_state:
    st.session_state.current_phase = 'Define'

# Header
st.markdown('<h1 class="main-header">🎯 Green Belt Project Management System</h1>', unsafe_allow_html=True)

# Verificar conexão com Supabase
if not supabase:
    st.error("""
    ⚠️ **Supabase não configurado!**
    
    Para configurar:
    1. Crie uma conta em [supabase.com](https://supabase.com)
    2. Crie um novo projeto
    3. Execute o script SQL fornecido no SQL Editor
    4. Adicione as credenciais no arquivo `.streamlit/secrets.toml`:
    ```
    SUPABASE_URL = "sua-url-aqui"
    SUPABASE_KEY = "sua-key-aqui"
    ```
    """)
    st.stop()

# Sidebar - Seleção/Criação de Projeto
with st.sidebar:
    st.header("📁 Gestão de Projetos")
    
    # Carregar projetos existentes
    try:
        projects_response = supabase.table('projects').select("*").order('created_at', desc=True).execute()
        projects = projects_response.data if projects_response.data else []
    except Exception as e:
        st.error(f"Erro ao carregar projetos: {e}")
        projects = []
    
    # Seleção de projeto
    if projects:
        project_names = ["Novo Projeto..."] + [p['name'] for p in projects]
        selected_project = st.selectbox("Selecione um Projeto:", project_names)
        
        if selected_project != "Novo Projeto...":
            selected_project_data = next(p for p in projects if p['name'] == selected_project)
            if st.button("📂 Carregar Projeto"):
                st.session_state.current_project_id = selected_project_data['id']
                st.session_state.current_project_name = selected_project_data['name']
                st.session_state.current_phase = selected_project_data.get('current_phase', 'Define')
                st.success(f"Projeto '{selected_project}' carregado!")
                st.rerun()
    
    # Criar novo projeto
    st.divider()
    st.subheader("➕ Criar Novo Projeto")
    
    with st.form("new_project_form"):
        project_name = st.text_input("Nome do Projeto*")
        project_description = st.text_area("Descrição")
        company = st.text_input("Empresa")
        department = st.text_input("Departamento")
        project_type = st.selectbox(
            "Tipo de Projeto",
            ["Manufacturing", "Service", "Transactional", "Healthcare", "IT", "Other"]
        )
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Data de Início")
        with col2:
            target_date = st.date_input("Data Alvo")
        
        champion = st.text_input("Champion/Sponsor")
        project_leader = st.text_input("Líder do Projeto (Green Belt)")
        expected_savings = st.number_input("Economia Esperada (R$)", min_value=0.0, step=1000.0)
        
        submitted = st.form_submit_button("Criar Projeto", type="primary")
        
        if submitted and project_name:
            try:
                new_project = {
                    'name': project_name,
                    'description': project_description,
                    'company': company,
                    'department': department,
                    'project_type': project_type,
                    'start_date': start_date.isoformat(),
                    'target_date': target_date.isoformat(),
                    'champion': champion,
                    'project_leader': project_leader,
                    'expected_savings': expected_savings
                }
                
                response = supabase.table('projects').insert(new_project).execute()
                
                if response.data:
                    st.session_state.current_project_id = response.data[0]['id']
                    st.session_state.current_project_name = project_name
                    st.success(f"✅ Projeto '{project_name}' criado com sucesso!")
                    st.rerun()
                    
            except Exception as e:
                st.error(f"Erro ao criar projeto: {e}")

# Área principal
if st.session_state.current_project_id:
    # Carregar dados do projeto atual
    try:
        project_data = supabase.table('projects').select("*").eq('id', st.session_state.current_project_id).single().execute()
        project = project_data.data
    except:
        project = {}
    
    # Header do projeto
    st.success(f"📊 Projeto Ativo: **{st.session_state.current_project_name}**")
    
    # Métricas principais
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Fase Atual",
            project.get('current_phase', 'Define'),
            delta=f"{project.get('progress_percentage', 0)}% completo"
        )
    
    with col2:
        days_elapsed = (datetime.now().date() - datetime.fromisoformat(project.get('start_date', datetime.now().isoformat())).date()).days
        st.metric("Dias Decorridos", days_elapsed)
    
    with col3:
        days_remaining = (datetime.fromisoformat(project.get('target_date', datetime.now().isoformat())).date() - datetime.now().date()).days
        st.metric("Dias Restantes", days_remaining)
    
    with col4:
        st.metric("Economia Esperada", f"R$ {project.get('expected_savings', 0):,.0f}")
    
    with col5:
        st.metric("Status", project.get('status', 'Active'))
    
    # Tabs para cada fase DMAIC
    st.markdown("---")
    st.header("📋 Fases DMAIC")
    
    define_tab, measure_tab, analyze_tab, improve_tab, control_tab = st.tabs([
        "1️⃣ DEFINE",
        "2️⃣ MEASURE",
        "3️⃣ ANALYZE",
        "4️⃣ IMPROVE",
        "5️⃣ CONTROL"
    ])
    
    with define_tab:
        st.header("Define - Definição do Projeto")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📝 Project Charter")
            
            # Verificar se existe charter
            try:
                charter_response = supabase.table('project_charter').select("*").eq('project_id', st.session_state.current_project_id).execute()
                charter = charter_response.data[0] if charter_response.data else {}
            except:
                charter = {}
            
            if charter:
                st.info("**Problem Statement:**")
                st.write(charter.get('problem_statement', 'Não definido'))
                
                st.info("**Goal Statement:**")
                st.write(charter.get('goal_statement', 'Não definido'))
                
                st.info("**Escopo:**")
                col_in, col_out = st.columns(2)
                with col_in:
                    st.write("✅ **Dentro do Escopo:**")
                    st.write(charter.get('in_scope', 'Não definido'))
                with col_out:
                    st.write("❌ **Fora do Escopo:**")
                    st.write(charter.get('out_scope', 'Não definido'))
            else:
                st.warning("Charter não definido. Acesse a página Define para criar.")
        
        with col2:
            st.subheader("📊 Métricas Principais")
            
            if charter:
                primary_metric = charter.get('primary_metric', 'Não definida')
                current_value = charter.get('primary_metric_current', 0)
                target_value = charter.get('primary_metric_target', 0)
                unit = charter.get('primary_metric_unit', '')
                
                st.metric(
                    primary_metric,
                    f"{current_value} {unit}",
                    delta=f"Meta: {target_value} {unit}"
                )
                
                # Progress bar
                if current_value and target_value:
                    progress = min(abs((target_value - current_value) / current_value * 100), 100)
                    st.progress(progress / 100)
                    st.caption(f"Melhoria necessária: {progress:.1f}%")
    
    with measure_tab:
        st.header("Measure - Coleta e Validação de Dados")
        
        # Estatísticas de medições
        try:
            measurements_count = supabase.table('measurements').select("count", count='exact').eq('project_id', st.session_state.current_project_id).execute()
            total_measurements = measurements_count.count if measurements_count else 0
        except:
            total_measurements = 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de Medições", total_measurements)
        
        with col2:
            st.metric("Período de Coleta", "30 dias")  # Placeholder
        
        with col3:
            st.metric("Taxa de Defeitos", "5.2%")  # Placeholder
        
        if total_measurements > 0:
            st.info(f"✅ {total_measurements} medições coletadas. Acesse a página Measure para análise detalhada.")
        else:
            st.warning("Nenhuma medição coletada ainda. Acesse a página Measure para iniciar.")
    
    with analyze_tab:
        st.header("Analyze - Análise Estatística e Identificação de Causas")
        
        # Resumo das análises
        try:
            analyses_count = supabase.table('analyze_results').select("count", count='exact').eq('project_id', st.session_state.current_project_id).execute()
            total_analyses = analyses_count.count if analyses_count else 0
            
            root_causes_count = supabase.table('root_causes').select("count", count='exact').eq('project_id', st.session_state.current_project_id).execute()
            total_root_causes = root_causes_count.count if root_causes_count else 0
        except:
            total_analyses = 0
            total_root_causes = 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Análises Realizadas", total_analyses)
        
        with col2:
            st.metric("Causas Raiz Identificadas", total_root_causes)
        
        with col3:
            st.metric("Causas Validadas", 0)  # Placeholder
        
        if total_root_causes > 0:
            st.info(f"✅ {total_root_causes} causas raiz identificadas. Acesse a página Analyze para detalhes.")
        else:
            st.warning("Análise pendente. Acesse a página Analyze para identificar causas raiz.")
    
    with improve_tab:
        st.header("Improve - Implementação de Melhorias")
        
        # Status das ações
        try:
            actions_count = supabase.table('action_plans').select("count", count='exact').eq('project_id', st.session_state.current_project_id).execute()
            total_actions = actions_count.count if actions_count else 0
        except:
            total_actions = 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Ações Planejadas", total_actions)
        
        with col2:
            st.metric("Ações em Andamento", 0)  # Placeholder
        
        with col3:
            st.metric("Ações Concluídas", 0)  # Placeholder
        
        if total_actions > 0:
            st.info(f"✅ {total_actions} ações planejadas. Acesse a página Improve para gerenciar.")
        else:
            st.warning("Nenhuma ação planejada. Acesse a página Improve para criar plano de ação.")
    
    with control_tab:
        st.header("Control - Controle e Sustentabilidade")
        
        # Status do controle
        try:
            control_charts_count = supabase.table('control_charts').select("count", count='exact').eq('project_id', st.session_state.current_project_id).execute()
            total_control_charts = control_charts_count.count if control_charts_count else 0
            
            control_plans_count = supabase.table('control_plans').select("count", count='exact').eq('project_id', st.session_state.current_project_id).execute()
            total_control_plans = control_plans_count.count if control_plans_count else 0
        except:
            total_control_charts = 0
            total_control_plans = 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Gráficos de Controle", total_control_charts)
        
        with col2:
            st.metric("Planos de Controle", total_control_plans)
        
        with col3:
            st.metric("Processo em Controle", "Sim" if total_control_charts > 0 else "Não")
        
        if total_control_plans > 0:
            st.info(f"✅ {total_control_plans} planos de controle ativos. Acesse a página Control para monitorar.")
        else:
            st.warning("Fase de controle pendente. Complete as fases anteriores primeiro.")
    
    # Gráfico de progresso do projeto
    st.markdown("---")
    st.header("📈 Progresso do Projeto")
    
    phases = ['Define', 'Measure', 'Analyze', 'Improve', 'Control']
    progress_values = [100, 80, 60, 30, 10]  # Placeholder - calcular baseado em dados reais
    
    fig = go.Figure(data=[
        go.Bar(
            x=phases,
            y=progress_values,
            marker_color=['green' if v == 100 else 'lightblue' for v in progress_values]
        )
    ])
    
    fig.update_layout(
        title="Progresso por Fase DMAIC",
        xaxis_title="Fase",
        yaxis_title="Progresso (%)",
        yaxis_range=[0, 100],
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
else:
    # Nenhum projeto selecionado
    st.info("""
    👋 **Bem-vindo ao Green Belt Project Management System!**
    
    Este sistema foi desenvolvido para gerenciar projetos Six Sigma usando a metodologia DMAIC:
    
    - **D**efine - Definir o problema e objetivos
    - **M**easure - Medir o processo atual
    - **A**nalyze - Analisar dados e identificar causas raiz
    - **I**mprove - Implementar melhorias
    - **C**ontrol - Controlar e sustentar as melhorias
    
    **Para começar:**
    1. Crie um novo projeto usando o formulário na barra lateral
    2. Ou selecione um projeto existente
    3. Navegue pelas páginas de cada fase no menu lateral
    
    **Recursos:**
    - 📊 Análises estatísticas avançadas
    - 📈 Gráficos interativos
    - 📋 Templates e ferramentas Six Sigma
    - 💾 Armazenamento seguro no Supabase
    - 📱 Acesso de qualquer lugar
    """)
    
    # Mostrar projetos recentes se existirem
    if projects:
        st.subheader("📂 Projetos Recentes")
        
        recent_projects = projects[:5]
        for proj in recent_projects:
            with st.expander(f"📁 {proj['name']}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Tipo:** {proj.get('project_type', 'N/A')}")
                    st.write(f"**Fase:** {proj.get('current_phase', 'Define')}")
                with col2:
                    st.write(f"**Líder:** {proj.get('project_leader', 'N/A')}")
                    st.write(f"**Status:** {proj.get('status', 'Active')}")
                with col3:
                    st.write(f"**Início:** {proj.get('start_date', 'N/A')}")
                    st.write(f"**Economia:** R$ {proj.get('expected_savings', 0):,.0f}")

# Footer
st.markdown("---")
st.caption("🎯 Green Belt Project Management System v1.0 | Desenvolvido com Streamlit + Supabase")
