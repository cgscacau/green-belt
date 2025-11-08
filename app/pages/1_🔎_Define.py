import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json
from supabase import create_client, Client

# Configuração da página
st.set_page_config(
    page_title="Define - Green Belt",
    page_icon="📋",
    layout="wide"
)

# ========================= FUNÇÕES AUXILIARES =========================

# Inicializar Supabase
@st.cache_resource
def init_supabase():
    """Inicializa conexão com Supabase"""
    try:
        # Tentar pegar das secrets do Streamlit primeiro
        if "supabase" in st.secrets:
            url = st.secrets["supabase"]["url"]
            key = st.secrets["supabase"]["key"]
        else:
            # Fallback para variáveis de ambiente
            url = os.environ.get("SUPABASE_URL", "")
            key = os.environ.get("SUPABASE_KEY", "")
        
        if url and key:
            return create_client(url, key)
        return None
    except Exception as e:
        st.error(f"Erro ao conectar com Supabase: {str(e)}")
        return None

# Inicializar conexão
supabase = init_supabase()

# Função para salvar projeto
def save_project_to_db(project_data):
    """Salva ou atualiza projeto no banco de dados"""
    if not supabase:
        return False
    
    try:
        # Verificar se projeto já existe
        existing = supabase.table('projects').select("*").eq('project_name', project_data['project_name']).execute()
        
        if existing.data:
            # Atualizar projeto existente
            project_data['updated_at'] = datetime.now().isoformat()
            response = supabase.table('projects').update(project_data).eq('project_name', project_data['project_name']).execute()
        else:
            # Criar novo projeto
            project_data['created_at'] = datetime.now().isoformat()
            project_data['updated_at'] = datetime.now().isoformat()
            response = supabase.table('projects').insert(project_data).execute()
        
        return True
    except Exception as e:
        st.error(f"Erro ao salvar projeto: {str(e)}")
        return False

# Função para carregar projetos
@st.cache_data(ttl=300)
def load_projects_from_db():
    """Carrega lista de projetos do banco de dados"""
    if not supabase:
        return []
    
    try:
        response = supabase.table('projects').select("project_name, created_at, project_leader, status").execute()
        if response.data:
            return response.data
        return []
    except Exception as e:
        st.error(f"Erro ao carregar projetos: {str(e)}")
        return []

# Função para carregar detalhes do projeto
def load_project_details(project_name):
    """Carrega detalhes completos de um projeto"""
    if not supabase:
        return None
    
    try:
        response = supabase.table('projects').select("*").eq('project_name', project_name).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Erro ao carregar detalhes do projeto: {str(e)}")
        return None

# Função para criar DataFrame SIPOC
def create_sipoc_dataframe(suppliers, inputs, process, outputs, customers):
    """Cria DataFrame do SIPOC com tratamento robusto"""
    try:
        # Processar cada campo
        def process_field(field):
            if field and field.strip():
                items = [item.strip() for item in field.split('\n') if item.strip()]
                return items
            return []
        
        # Criar listas processadas
        data = {
            'Suppliers': process_field(suppliers),
            'Inputs': process_field(inputs),
            'Process': process_field(process),
            'Outputs': process_field(outputs),
            'Customers': process_field(customers)
        }
        
        # Se todas vazias, retornar DataFrame vazio
        if all(len(v) == 0 for v in data.values()):
            return pd.DataFrame(columns=['Suppliers', 'Inputs', 'Process', 'Outputs', 'Customers'])
        
        # Encontrar tamanho máximo
        max_length = max(len(v) for v in data.values())
        
        # Padronizar tamanhos
        for key in data:
            current_length = len(data[key])
            if current_length < max_length:
                data[key].extend([''] * (max_length - current_length))
        
        return pd.DataFrame(data)
        
    except Exception as e:
        st.error(f"Erro ao criar DataFrame: {str(e)}")
        return pd.DataFrame()

# Função para carregar VOCs do banco
def load_voc_items(project_name):
    """Carrega VOC items do banco de dados"""
    if not supabase:
        return []
    
    try:
        response = supabase.table('voc_items').select("*").eq('project_name', project_name).execute()
        if response.data:
            return response.data
        return []
    except Exception as e:
        st.error(f"Erro ao carregar VOCs: {str(e)}")
        return []

# Função para carregar SIPOC do banco
def load_sipoc(project_name):
    """Carrega SIPOC do banco de dados"""
    if not supabase:
        return None
    
    try:
        response = supabase.table('sipoc').select("*").eq('project_name', project_name).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Erro ao carregar SIPOC: {str(e)}")
        return None

# ========================= INTERFACE PRINCIPAL =========================

# Título e descrição
st.title("📋 Define — Definição do Projeto")
st.markdown("Defina claramente o problema, escopo e objetivos do projeto Lean Six Sigma")

# ========================= SIDEBAR =========================

with st.sidebar:
    st.header("🗂️ Gerenciar Projetos")
    
    # Verificar conexão com Supabase
    if not supabase:
        st.error("⚠️ Supabase não configurado")
        st.info("Configure as variáveis SUPABASE_URL e SUPABASE_KEY")
        use_local = st.checkbox("Usar armazenamento local (sessão)")
    else:
        use_local = False
        st.success("✅ Conectado ao Supabase")
    
    st.divider()
    
    # Opções de projeto
    project_mode = st.radio(
        "Escolha uma opção:",
        ["Criar Novo Projeto", "Selecionar Projeto Existente"],
        key="project_mode_radio"
    )
    
    if project_mode == "Selecionar Projeto Existente":
        if supabase:
            projects = load_projects_from_db()
            
            if projects:
                # Criar DataFrame para melhor visualização
                projects_df = pd.DataFrame(projects)
                project_names = projects_df['project_name'].tolist()
                
                selected_project = st.selectbox(
                    "Selecione um projeto:",
                    [""] + project_names,
                    key="project_selector"
                )
                
                if selected_project:
                    # Mostrar detalhes do projeto selecionado
                    project_info = projects_df[projects_df['project_name'] == selected_project].iloc[0]
                    st.info(f"**Líder:** {project_info.get('project_leader', 'N/A')}")
                    st.info(f"**Status:** {project_info.get('status', 'active')}")
                    
                    if st.button("📂 Carregar Projeto", type="primary"):
                        project_details = load_project_details(selected_project)
                        if project_details:
                            st.session_state.project_name = selected_project
                            st.session_state.project_data = project_details
                            
                            # Carregar VOCs e SIPOC
                            voc_items = load_voc_items(selected_project)
                            if voc_items:
                                st.session_state.voc_items = voc_items
                            
                            sipoc_data = load_sipoc(selected_project)
                            if sipoc_data:
                                st.session_state.sipoc_suppliers = sipoc_data.get('suppliers', '')
                                st.session_state.sipoc_inputs = sipoc_data.get('inputs', '')
                                st.session_state.sipoc_process = sipoc_data.get('process', '')
                                st.session_state.sipoc_outputs = sipoc_data.get('outputs', '')
                                st.session_state.sipoc_customers = sipoc_data.get('customers', '')
                            
                            st.success(f"✅ Projeto '{selected_project}' carregado!")
                            st.rerun()
            else:
                st.info("Nenhum projeto encontrado")
        else:
            st.warning("Modo local: histórico não disponível")
    
    # Mostrar projeto ativo
    if 'project_name' in st.session_state:
        st.divider()
        st.success(f"📁 **Projeto Ativo:**")
        st.write(f"_{st.session_state.project_name}_")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Trocar", use_container_width=True):
                for key in ['project_name', 'project_data', 'voc_items']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        with col2:
            if st.button("🗑️ Excluir", use_container_width=True):
                if supabase and st.session_state.get('confirm_delete'):
                    try:
                        supabase.table('projects').delete().eq('project_name', st.session_state.project_name).execute()
                        st.success("Projeto excluído!")
                        for key in list(st.session_state.keys()):
                            if 'project' in key or 'sipoc' in key or 'voc' in key:
                                del st.session_state[key]
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {str(e)}")
                else:
                    st.session_state.confirm_delete = True
                    st.warning("Clique novamente para confirmar")

# ========================= CONTEÚDO PRINCIPAL =========================

# Verificar se há projeto ativo ou sendo criado
if project_mode == "Criar Novo Projeto" or 'project_name' in st.session_state:
    
    # Tabs principais
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Project Charter",
        "🗣️ Voice of Customer (VOC)",
        "🔄 SIPOC Diagram",
        "📊 Resumo do Projeto"
    ])
    
    # ========================= TAB 1: PROJECT CHARTER =========================
    
    with tab1:
        st.header("Project Charter")
        
        # Carregar dados existentes
        existing_data = st.session_state.get('project_data', {})
        
        with st.form("project_charter_form", clear_on_submit=False):
            # Informações Básicas
            st.subheader("📌 Informações Básicas")
            col1, col2 = st.columns(2)
            
            with col1:
                project_name = st.text_input(
                    "Nome do Projeto *",
                    value=st.session_state.get('project_name', existing_data.get('project_name', '')),
                    disabled='project_name' in st.session_state and project_mode != "Criar Novo Projeto",
                    help="Nome único para identificar o projeto"
                )
                
                project_leader = st.text_input(
                    "Líder do Projeto *",
                    value=existing_data.get('project_leader', ''),
                    help="Green Belt ou Black Belt responsável"
                )
                
                project_sponsor = st.text_input(
                    "Sponsor do Projeto",
                    value=existing_data.get('project_sponsor', ''),
                    help="Patrocinador executivo do projeto"
                )
            
            with col2:
                col_date1, col_date2 = st.columns(2)
                with col_date1:
                    start_date = st.date_input(
                        "Data de Início",
                        value=pd.to_datetime(existing_data.get('start_date')).date() if existing_data.get('start_date') else datetime.now().date()
                    )
                
                with col_date2:
                    end_date = st.date_input(
                        "Data de Término",
                        value=pd.to_datetime(existing_data.get('end_date')).date() if existing_data.get('end_date') else None
                    )
                
                team_members = st.text_area(
                    "Membros da Equipe",
                    value=existing_data.get('team_members', ''),
                    height=80,
                    help="Liste os membros da equipe (um por linha)"
                )
            
            # Definição do Problema
            st.subheader("🎯 Definição do Problema e Objetivos")
            
            problem_statement = st.text_area(
                "Declaração do Problema *",
                value=existing_data.get('problem_statement', ''),
                height=120,
                help="Descreva o problema de forma clara e específica. Use dados quando possível."
            )
            
            goal_statement = st.text_area(
                "Declaração da Meta *",
                value=existing_data.get('goal_statement', ''),
                height=120,
                help="Defina uma meta SMART (Específica, Mensurável, Atingível, Relevante, Temporal)"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                business_case = st.text_area(
                    "Business Case *",
                    value=existing_data.get('business_case', ''),
                    height=100,
                    help="Por que este projeto é importante para o negócio?"
                )
            
            with col2:
                project_scope = st.text_area(
                    "Escopo do Projeto",
                    value=existing_data.get('project_scope', ''),
                    height=100,
                    help="O que está incluído e excluído do projeto"
                )
            
            # Métricas
            st.subheader("📈 Métricas e Metas")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                primary_metric = st.text_input(
                    "Métrica Primária (Y)",
                    value=existing_data.get('primary_metric', ''),
                    help="KPI principal a ser melhorado"
                )
            
            with col2:
                baseline_value = st.number_input(
                    "Valor Baseline",
                    value=float(existing_data.get('baseline_value', 0)) if existing_data.get('baseline_value') else 0.0,
                    format="%.2f",
                    help="Valor atual da métrica"
                )
            
            with col3:
                target_value = st.number_input(
                    "Valor Meta",
                    value=float(existing_data.get('target_value', 0)) if existing_data.get('target_value') else 0.0,
                    format="%.2f",
                    help="Valor desejado da métrica"
                )
            
            with col4:
                expected_savings = st.number_input(
                    "Economia Esperada (R$)",
                    value=float(existing_data.get('expected_savings', 0)) if existing_data.get('expected_savings') else 0.0,
                    format="%.2f",
                    help="Benefício financeiro esperado"
                )
            
            # Botões de ação
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                submitted = st.form_submit_button("💾 Salvar Project Charter", type="primary", use_container_width=True)
            with col2:
                clear_form = st.form_submit_button("🔄 Limpar", use_container_width=True)
            
            if submitted:
                # Validação
                if not all([project_name, problem_statement, goal_statement, project_leader, business_case]):
                    st.error("❌ Por favor, preencha todos os campos obrigatórios (*)")
                else:
                    # Preparar dados
                    project_data = {
                        'project_name': project_name,
                        'problem_statement': problem_statement,
                        'business_case': business_case,
                        'project_scope': project_scope,
                        'goal_statement': goal_statement,
                        'start_date': start_date.isoformat() if start_date else None,
                        'end_date': end_date.isoformat() if end_date else None,
                        'team_members': team_members,
                        'project_sponsor': project_sponsor,
                        'project_leader': project_leader,
                        'primary_metric': primary_metric,
                        'baseline_value': baseline_value,
                        'target_value': target_value,
                        'expected_savings': expected_savings,
                        'status': 'active'
                    }
                    
                    # Salvar no session_state
                    st.session_state.project_name = project_name
                    st.session_state.project_data = project_data
                    st.session_state.problem_statement = problem_statement
                    
                    # Salvar no banco
                    if supabase:
                        if save_project_to_db(project_data):
                            st.success("✅ Project Charter salvo com sucesso!")
                            st.balloons()
                        else:
                            st.warning("⚠️ Erro ao salvar no banco, dados salvos localmente")
                    else:
                        st.success("✅ Project Charter salvo localmente!")
                    
                    st.rerun()
            
            if clear_form:
                for key in list(st.session_state.keys()):
                    if 'project' in key:
                        del st.session_state[key]
                st.rerun()
    
    # ========================= TAB 2: VOC =========================
    
    with tab2:
        st.header("Voice of Customer (VOC)")
        
        if 'project_name' not in st.session_state:
            st.warning("⚠️ Por favor, complete o Project Charter primeiro")
        else:
            st.info(f"📁 Projeto: **{st.session_state.project_name}**")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Formulário VOC
                with st.form("voc_form", clear_on_submit=True):
                    st.subheader("Adicionar VOC")
                    
                    col_voc1, col_voc2 = st.columns(2)
                    
                    with col_voc1:
                        customer_segment = st.text_input("Segmento de Cliente *")
                        customer_need = st.text_area("Necessidade do Cliente *", height=80)
                        current_performance = st.text_area("Performance Atual", height=80)
                    
                    with col_voc2:
                        priority = st.select_slider(
                            "Prioridade",
                            options=["Baixa", "Média", "Alta", "Crítica"],
                            value="Média"
                        )
                        
                        csat_score = st.slider("Satisfação Atual", 1, 10, 5)
                        target_csat = st.slider("Satisfação Desejada", 1, 10, 8)
                    
                    ctq = st.text_area(
                        "Critical to Quality (CTQ)",
                        height=80,
                        help="Requisitos mensuráveis derivados da voz do cliente"
                    )
                    
                    submitted_voc = st.form_submit_button("➕ Adicionar VOC", type="primary")
                    
                    if submitted_voc:
                        if customer_segment and customer_need:
                            # Preparar dados
                            voc_item = {
                                'project_name': st.session_state.project_name,
                                'customer_segment': customer_segment,
                                'customer_need': customer_need,
                                'current_performance': current_performance,
                                'priority': priority,
                                'csat_score': csat_score,
                                'target_csat': target_csat,
                                'ctq': ctq
                            }
                            
                            # Salvar no session_state
                            if 'voc_items' not in st.session_state:
                                st.session_state.voc_items = []
                            st.session_state.voc_items.append(voc_item)
                            
                            # Salvar no banco
                            if supabase:
                                try:
                                    response = supabase.table('voc_items').insert(voc_item).execute()
                                    st.success("✅ VOC adicionado com sucesso!")
                                except Exception as e:
                                    st.error(f"Erro ao salvar: {str(e)}")
                            else:
                                st.success("✅ VOC adicionado localmente!")
                            
                            st.rerun()
                        else:
                            st.error("Preencha os<span class="cursor">█</span>
