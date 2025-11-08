import streamlit as st
import pandas as pd
from datetime import datetime
import os
from supabase import create_client, Client
import json

# Configuração da página
st.set_page_config(
    page_title="Define - Green Belt",
    page_icon="📋",
    layout="wide"
)

# Inicializar Supabase
@st.cache_resource
def init_supabase():
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")
    if url and key:
        return create_client(url, key)
    return None

supabase = init_supabase()

# Função para salvar projeto no banco
def save_project_to_db(project_data):
    """Salva ou atualiza projeto no banco de dados"""
    if not supabase:
        return False
    
    try:
        # Verificar se projeto já existe
        existing = supabase.table('projects').select("*").eq('project_name', project_data['project_name']).execute()
        
        if existing.data:
            # Atualizar projeto existente
            response = supabase.table('projects').update(project_data).eq('project_name', project_data['project_name']).execute()
        else:
            # Criar novo projeto
            response = supabase.table('projects').insert(project_data).execute()
        
        return True
    except Exception as e:
        st.error(f"Erro ao salvar projeto: {str(e)}")
        return False

# Função para carregar projetos do banco
@st.cache_data(ttl=300)
def load_projects_from_db():
    """Carrega lista de projetos do banco de dados"""
    if not supabase:
        return []
    
    try:
        response = supabase.table('projects').select("project_name, created_at").execute()
        if response.data:
            return response.data
        return []
    except Exception as e:
        st.error(f"Erro ao carregar projetos: {str(e)}")
        return []

# Função para carregar projeto específico
def load_project_details(project_name):
    """Carrega detalhes de um projeto específico"""
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

# Título e descrição
st.title("📋 Define — Definição do Projeto")
st.markdown("Defina claramente o problema, escopo e objetivos do projeto Lean Six Sigma")

# Sidebar para seleção/criação de projeto
with st.sidebar:
    st.header("🗂️ Gerenciar Projetos")
    
    # Opção de criar novo ou selecionar existente
    project_mode = st.radio(
        "Escolha uma opção:",
        ["Criar Novo Projeto", "Selecionar Projeto Existente"]
    )
    
    if project_mode == "Selecionar Projeto Existente":
        projects = load_projects_from_db()
        
        if projects:
            project_names = [p['project_name'] for p in projects]
            selected_project = st.selectbox(
                "Selecione um projeto:",
                [""] + project_names
            )
            
            if selected_project and st.button("Carregar Projeto", type="primary"):
                project_details = load_project_details(selected_project)
                if project_details:
                    # Carregar dados no session_state
                    st.session_state.project_name = selected_project
                    st.session_state.project_data = project_details
                    st.success(f"✅ Projeto '{selected_project}' carregado!")
                    st.rerun()
        else:
            st.info("Nenhum projeto encontrado. Crie um novo projeto.")
    
    # Mostrar projeto atual
    if 'project_name' in st.session_state:
        st.divider()
        st.success(f"📁 Projeto Ativo: **{st.session_state.project_name}**")
        
        if st.button("🔄 Desselecionar Projeto"):
            del st.session_state.project_name
            if 'project_data' in st.session_state:
                del st.session_state.project_data
            st.rerun()

# Verificar se há projeto selecionado ou sendo criado
if project_mode == "Criar Novo Projeto" or 'project_name' in st.session_state:
    
    # Tabs principais
    tab1, tab2, tab3, tab4 = st.tabs([
        "Project Charter",
        "Voice of Customer (VOC)",
        "SIPOC Diagram",
        "Resumo do Projeto"
    ])
    
    # Tab 1: Project Charter
    with tab1:
        st.header("Project Charter")
        
        with st.form("project_charter"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Carregar dados existentes se houver
                existing_data = st.session_state.get('project_data', {})
                
                project_name = st.text_input(
                    "Nome do Projeto*",
                    value=st.session_state.get('project_name', existing_data.get('project_name', '')),
                    disabled='project_name' in st.session_state and project_mode != "Criar Novo Projeto"
                )
                
                problem_statement = st.text_area(
                    "Declaração do Problema*",
                    value=existing_data.get('problem_statement', ''),
                    height=150,
                    help="Descreva claramente o problema que será resolvido"
                )
                
                business_case = st.text_area(
                    "Business Case*",
                    value=existing_data.get('business_case', ''),
                    height=150,
                    help="Justifique a importância do projeto para o negócio"
                )
                
                project_scope = st.text_area(
                    "Escopo do Projeto*",
                    value=existing_data.get('project_scope', ''),
                    height=100,
                    help="Defina o que está incluído e excluído do projeto"
                )
            
            with col2:
                goal_statement = st.text_area(
                    "Declaração da Meta*",
                    value=existing_data.get('goal_statement', ''),
                    height=150,
                    help="Defina a meta SMART do projeto"
                )
                
                # Datas
                col_date1, col_date2 = st.columns(2)
                with col_date1:
                    start_date = st.date_input(
                        "Data de Início",
                        value=pd.to_datetime(existing_data.get('start_date', datetime.now())).date() if existing_data.get('start_date') else datetime.now().date()
                    )
                
                with col_date2:
                    end_date = st.date_input(
                        "Data de Término",
                        value=pd.to_datetime(existing_data.get('end_date', datetime.now())).date() if existing_data.get('end_date') else None
                    )
                
                # Equipe
                team_members = st.text_area(
                    "Membros da Equipe",
                    value=existing_data.get('team_members', ''),
                    height=100,
                    help="Liste os membros da equipe (um por linha)"
                )
                
                project_sponsor = st.text_input(
                    "Sponsor do Projeto",
                    value=existing_data.get('project_sponsor', '')
                )
                
                project_leader = st.text_input(
                    "Líder do Projeto*",
                    value=existing_data.get('project_leader', '')
                )
            
            # Métricas
            st.subheader("Métricas do Projeto")
            col_metric1, col_metric2 = st.columns(2)
            
            with col_metric1:
                primary_metric = st.text_input(
                    "Métrica Primária (Y)",
                    value=existing_data.get('primary_metric', ''),
                    help="Principal indicador a ser melhorado"
                )
                
                baseline_value = st.number_input(
                    "Valor Baseline",
                    value=float(existing_data.get('baseline_value', 0)) if existing_data.get('baseline_value') else 0.0,
                    format="%.2f"
                )
            
            with col_metric2:
                target_value = st.number_input(
                    "Valor Meta",
                    value=float(existing_data.get('target_value', 0)) if existing_data.get('target_value') else 0.0,
                    format="%.2f"
                )
                
                expected_savings = st.number_input(
                    "Economia Esperada (R$)",
                    value=float(existing_data.get('expected_savings', 0)) if existing_data.get('expected_savings') else 0.0,
                    format="%.2f"
                )
            
            submitted = st.form_submit_button("💾 Salvar Project Charter", type="primary")
            
            if submitted:
                if not project_name or not problem_statement or not goal_statement or not project_leader:
                    st.error("Por favor, preencha todos os campos obrigatórios (*)")
                else:
                    # Preparar dados do projeto
                    project_data = {
                        'project_name': project_name,
                        'problem_statement': problem_statement,
                        'business_case': business_case,
                        'project_scope': project_scope,
                        'goal_statement': goal_statement,
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat() if end_date else None,
                        'team_members': team_members,
                        'project_sponsor': project_sponsor,
                        'project_leader': project_leader,
                        'primary_metric': primary_metric,
                        'baseline_value': baseline_value,
                        'target_value': target_value,
                        'expected_savings': expected_savings,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    # Salvar no session_state
                    st.session_state.project_name = project_name
                    st.session_state.project_data = project_data
                    st.session_state.problem_statement = problem_statement
                    
                    # Salvar no banco de dados
                    if save_project_to_db(project_data):
                        st.success(f"✅ Project Charter salvo com sucesso! Projeto '{project_name}' está ativo.")
                        st.balloons()
                    else:
                        st.warning("⚠️ Project Charter salvo localmente, mas não foi possível salvar no banco de dados.")
    
    # Tab 2: Voice of Customer
    with tab2:
        st.header("Voice of Customer (VOC)")
        
        # Verificar se há projeto ativo
        if 'project_name' not in st.session_state:
            st.warning("⚠️ Por favor, crie ou selecione um projeto primeiro na aba 'Project Charter'")
        else:
            st.info(f"📁 Adicionando VOC ao projeto: **{st.session_state.project_name}**")
            
            # Formulário VOC
            with st.form("voc_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    customer_segment = st.text_input("Segmento de Cliente")
                    customer_need = st.text_area("Necessidade do Cliente", height=100)
                    current_performance = st.text_area("Performance Atual", height=100)
                
                with col2:
                    priority = st.select_slider(
                        "Prioridade",
                        options=["Baixa", "Média", "Alta", "Crítica"]
                    )
                    
                    csat_score = st.slider(
                        "Score de Satisfação Atual",
                        min_value=1,
                        max_value=10,
                        value=5
                    )
                    
                    target_csat = st.slider(
                        "Score de Satisfação Desejado",
                        min_value=1,
                        max_value=10,
                        value=8
                    )
                
                ctq = st.text_area(
                    "Critical to Quality (CTQ)",
                    height=100,
                    help="Traduza a voz do cliente em requisitos mensuráveis"
                )
                
                submitted_voc = st.form_submit_button("➕ Adicionar VOC")
                
                if submitted_voc:
                    if customer_segment and customer_need:
                        # Inicializar lista VOC se não existir
                        if 'voc_items' not in st.session_state:
                            st.session_state.voc_items = []
                        
                        # Adicionar novo item
                        voc_item = {
                            'timestamp': datetime.now().isoformat(),
                            'customer_segment': customer_segment,
                            'customer_need': customer_need,
                            'current_performance': current_performance,
                            'priority': priority,
                            'csat_score': csat_score,
                            'target_csat': target_csat,
                            'ctq': ctq
                        }
                        
                        st.session_state.voc_items.append(voc_item)
                        
                        # Salvar no banco
                        if supabase:
                            try:
                                voc_data = {
                                    'project_name': st.session_state.project_name,
                                    'voc_data': voc_item,
                                    'created_at': datetime.now().isoformat()
                                }
                                supabase.table('voc_items').insert(voc_data).execute()
                                st.success("✅ VOC adicionado com sucesso!")
                            except Exception as e:
                                st.error(f"Erro ao salvar VOC: {str(e)}")
                        else:
                            st.success("✅ VOC adicionado localmente!")
                        
                        st.rerun()
                    else:
                        st.error("Por favor, preencha pelo menos o segmento e a necessidade do cliente")
            
            # Exibir VOCs cadastrados
            if 'voc_items' in st.session_state and st.session_state.voc_items:
                st.subheader("VOCs Cadastrados")
                
                voc_df = pd.DataFrame(st.session_state.voc_items)
                
                # Filtros
                col1, col2 = st.columns(2)
                with col1:
                    filter_priority = st.multiselect(
                        "Filtrar por Prioridade",
                        options=["Baixa", "Média", "Alta", "Crítica"],
                        default=["Alta", "Crítica"]
                    )
                
                # Aplicar filtros
                if filter_priority:
                    filtered_df = voc_df[voc_df['priority'].isin(filter_priority)]
                else:
                    filtered_df = voc_df
                
                # Exibir tabela
                st.dataframe(
                    filtered_df[['customer_segment', 'customer_need', 'priority', 'csat_score', 'target_csat', 'ctq']],
                    use_container_width=True
                )
                
                # Métricas resumidas
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total de VOCs", len(voc_df))
                with col2:
                    st.metric("VOCs Críticos", len(voc_df[voc_df['priority'] == 'Crítica']))
                with col3:
                    avg_gap = (filtered_df['target_csat'] - filtered_df['csat_score']).mean()
                    st.metric("Gap Médio de Satisfação", f"{avg_gap:.1f}")
            else:
                # Tentar carregar do banco se não houver no session_state
                if supabase:
                    try:
                        voc_response = supabase.table('voc_items').select("*").eq('project_name', st.session_state.project_name).execute()
                        if voc_response.data:
                            st.session_state.voc_items = [item['voc_data'] for item in voc_response.data]
                            st.rerun()
                    except:
                        pass
                
                st.info("Nenhum VOC cadastrado ainda. Use o formulário acima para adicionar.")
    
    # Tab 3: SIPOC Diagram
    with tab3:
        st.header("SIPOC Diagram")
        
        if 'project_name' not in st.session_state:
            st.warning("⚠️ Por favor, crie ou selecione um projeto primeiro na aba 'Project Charter'")
        else:
            st.info(f"📁 Criando SIPOC para o projeto: **{st.session_state.project_name}**")
            
            # Layout SIPOC
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.subheader("Suppliers")
                suppliers = st.text_area(
                    "Fornecedores",
                    height=200,
                    help="Liste os fornecedores (um por linha)",
                    value=st.session_state.get('sipoc_suppliers', '')
                )
            
            with col2:
                st.subheader("Inputs")
                inputs = st.text_area(
                    "Entradas",
                    height=200,
                    help="Liste as entradas do processo (uma por linha)",
                    value=st.session_state.get('sipoc_inputs', '')
                )
            
            with col3:
                st.subheader("Process")
                process = st.text_area(
                    "Processo",
                    height=200,
                    help="Liste as etapas principais do processo (uma por linha)",
                    value=st.session_state.get('sipoc_process', '')
                )
            
            with col4:
                st.subheader("Outputs")
                outputs = st.text_area(
                    "Saídas",
                    height=200,
                    help="Liste as saídas do processo (uma por linha)",
                    value=st.session_state.get('sipoc_outputs', '')
                )
            
            with col5:
                st.subheader("Customers")
                customers = st.text_area(
                    "Clientes",
                    height=200,
                    help="Liste os clientes (um por linha)",
                    value=st.session_state.get('sipoc_customers', '')
                )
            
            # Botão para salvar SIPOC
            if st.button("💾 Salvar SIPOC", type="primary"):
                sipoc_data = {
                    'suppliers': suppliers,
                    'inputs': inputs,
                    'process': process,
                    'outputs': outputs,
                    'customers': customers
                }
                
                # Salvar no session_state
                st.session_state.sipoc_suppliers = suppliers
                st.session_state.sipoc_inputs = inputs
                st.session_state.sipoc_process = process
                st.session_state.sipoc_outputs = outputs
                st.session_state.sipoc_customers = customers
                
                # Salvar no banco
                if supabase:
                    try:
                        sipoc_record = {
                            'project_name': st.session_state.project_name,
                            'sipoc_data': sipoc_data,
                            'created_at': datetime.now().isoformat()
                        }
                        
                        # Verificar se já existe
                        existing = supabase.table('sipoc').select("*").eq('project_name', st.session_state.project_name).execute()
                        
                        if existing.data:
                            supabase.table('sipoc').update(sipoc_record).eq('project_name', st.session_state.project_name).execute()
                        else:
                            supabase.table('sipoc').insert(sipoc_record).execute()
                        
                        st.success("✅ SIPOC salvo com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao salvar SIPOC: {str(e)}")
                else:
                    st.success("✅ SIPOC salvo localmente!")
            
            # Visualização do SIPOC
            if any([suppliers, inputs, process, outputs, customers]):
                st.divider()
                st.subheader("Visualização do SIPOC")
                
                # Criar DataFrame para visualização
                sipoc_viz = pd.DataFrame({
                    'Suppliers': suppliers.split('\n') if suppliers else [],
                    'Inputs': inputs.split('\n') if inputs else [],
                    'Process': process.split('\n') if process else [],
                    'Outputs': outputs.split('\n') if outputs else [],
                    'Customers': customers.split('\n') if customers else []
                })
                
                # Ajustar tamanho das listas
                max_len = max([len(col) for col in sipoc_viz.columns if len(sipoc_viz[col]) > 0] + [0])
                for col in sipoc_viz.columns:
                    while len(sipoc_viz[col]) < max_len:
                        sipoc_viz[col].append('')
                
                st.dataframe(sipoc_viz, use_container_width=True)
    
    # Tab 4: Resumo do Projeto
    with tab4:
        st.header("📊 Resumo do Projeto")
        
        if 'project_name' in st.session_state:
            st.success(f"📁 Projeto Ativo: **{st.session_state.project_name}**")
            
            # Métricas principais
            col1, col2, col3, col4 = st.columns(4)
            
            project_data = st.session_state.get('project_data', {})
            
            with col1:
                st.metric("Líder do Projeto", project_data.get('project_leader', 'Não definido'))
            
            with col2:
                if project_data.get('start_date'):
                    st.metric("Data de Início", project_data.get('start_date', 'Não definida'))
            
            with col3:
                if project_data.get('baseline_value') and project_data.get('target_value'):
                    improvement = ((project_data.get('target_value', 0) - project_data.get('baseline_value', 0)) / 
                                 project_data.get('baseline_value', 1)) * 100
                    st.metric("Melhoria Esperada", f"{improvement:.1f}%")
            
            with col4:
                if project_data.get('expected_savings'):
                    st.metric("Economia Esperada", f"R$ {project_data.get('expected_savings', 0):,.2f}")
            
            # Detalhes do projeto
            st.divider()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📝 Declaração do Problema")
                st.info(project_data.get('problem_statement', 'Não definido'))
                
                st.subheader("🎯 Meta do Projeto")
                st.success(project_data.get('goal_statement', 'Não definida'))
            
            with col2:
                st.subheader("💼 Business Case")
                st.info(project_data.get('business_case', 'Não definido'))
                
                st.subheader("📏 Escopo")
                st.warning(project_data.get('project_scope', 'Não definido'))
            
            # Status dos componentes
            st.divider()
            st.subheader("✅ Checklist de Definição")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**Project Charter**")
                charter_complete = all([
                    project_data.get('project_name'),
                    project_data.get('problem_statement'),
                    project_data.get('goal_statement'),
                    project_data.get('project_leader')
                ])
                if charter_complete:
                    st.success("✅ Completo")
                else:
                    st.error("❌ Incompleto")
            
            with col2:
                st.write("**Voice of Customer**")
                voc_complete = 'voc_items' in st.session_state and len(st.session_state.voc_items) > 0
                if voc_complete:
                    st.success(f"✅ {len(st.session_state.voc_items)} VOCs")
                else:
                    st.error("❌ Nenhum VOC")
            
            with col3:
                st.write("**SIPOC Diagram**")
                sipoc_complete = any([
                    st.session_state.get('sipoc_suppliers'),
                    st.session_state.get('sipoc_process'),
                    st.session_state.get('sipoc_customers')
                ])
                if sipoc_complete:
                    st.success("✅ Completo")
                else:
                    st.error("❌ Incompleto")
            
            # Botão para exportar resumo
            st.divider()
            if st.button("📥 Exportar Resumo do Projeto"):
                export_data = {
                    'project_charter': project_data,
                    'voc_items': st.session_state.get('voc_items', []),
                    'sipoc': {
                        'suppliers': st.session_state.get('sipoc_suppliers', ''),
                        'inputs': st.session_state.get('sipoc_inputs', ''),
                        'process': st.session_state.get('sipoc_process', ''),
                        'outputs': st.session_state.get('sipoc_outputs', ''),
                        'customers': st.session_state.get('sipoc_customers', '')
                    },
                    'export_date': datetime.now().isoformat()
                }
                
                st.download_button(
                    label="Download JSON",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"projeto_{st.session_state.project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            # Aviso para próxima fase
            if charter_complete and voc_complete and sipoc_complete:
                st.divider()
                st.success("🎉 **Fase Define completa!** Você pode prosseguir para a fase Measure.")
                st.balloons()
            else:
                st.divider()
                st.warning("⚠️ Complete todos os componentes da fase Define antes de prosseguir para Measure.")
        else:
            st.warning("⚠️ Nenhum projeto ativo. Crie ou selecione um projeto.")

else:
    st.info("👈 Use a barra lateral para criar um novo projeto ou selecionar um existente.")

# Footer
st.divider()
st.caption("💡 **Dica:** Complete todos os campos obrigatórios do Project Charter para estabelecer uma base sólida para seu projeto.")
