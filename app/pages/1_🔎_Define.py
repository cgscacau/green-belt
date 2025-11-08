import streamlit as st
import pandas as pd
from datetime import datetime
import json

# Configuração da página
st.set_page_config(
    page_title="Define - Green Belt",
    page_icon="🔎",
    layout="wide"
)

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
    st.warning(f"Supabase não configurado: {e}")
    supabase = None

# Título
st.title("🔎 Define - Definição do Projeto")
st.markdown("Esta fase estabelece o escopo, objetivos e metas do projeto Six Sigma.")

# Inicializar session state
if 'project_id' not in st.session_state:
    st.session_state.project_id = None
if 'project_data' not in st.session_state:
    st.session_state.project_data = {}

# Tabs principais
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Project Charter",
    "🎯 Metas SMART",
    "👥 Stakeholders",
    "📊 SIPOC",
    "💾 Projetos Salvos"
])

# Tab 1: Project Charter
with tab1:
    st.header("Project Charter")
    
    with st.form("charter_form"):
        st.subheader("Informações do Projeto")
        
        col1, col2 = st.columns(2)
        
        with col1:
            project_name = st.text_input(
                "Nome do Projeto",
                value="Redução de Paradas de Caminhões Por Baixa Pressão de Diesel"
            )
            
            problem_statement = st.text_area(
                "Declaração do Problema",
                value="Paradas frequentes de caminhões por baixa pressão no sistema de alimentação de diesel, causando indisponibilidade da frota e custos elevados de manutenção corretiva.",
                height=150
            )
            
            goal_statement = st.text_area(
                "Declaração da Meta",
                value="Reduzir em 60% as paradas não programadas por baixa pressão de diesel em 3 meses, aumentando a disponibilidade da frota de 85% para 95%.",
                height=150
            )
        
        with col2:
            project_sponsor = st.text_input(
                "Sponsor do Projeto",
                value="Diretoria de Operações"
            )
            
            project_leader = st.text_input(
                "Líder do Projeto (Green Belt)",
                value=""
            )
            
            start_date = st.date_input(
                "Data de Início",
                value=datetime.now()
            )
            
            end_date = st.date_input(
                "Data Prevista de Término",
                value=datetime.now()
            )
        
        st.subheader("Escopo")
        
        col1, col2 = st.columns(2)
        
        with col1:
            scope_in = st.text_area(
                "Dentro do Escopo",
                value="• Sistema de alimentação de diesel\n• Processo de abastecimento\n• Manutenção preventiva\n• Treinamento de operadores\n• Qualidade do combustível",
                height=150
            )
        
        with col2:
            scope_out = st.text_area(
                "Fora do Escopo",
                value="• Sistema de injeção eletrônica\n• Motor dos caminhões\n• Outros sistemas do veículo\n• Fornecedores de combustível",
                height=150
            )
        
        st.subheader("Benefícios Esperados")
        
        expected_benefits = st.text_area(
            "Benefícios",
            value="• Redução de custos de manutenção em R$ 30.000/mês\n• Aumento da disponibilidade da frota\n• Redução de horas extras\n• Melhoria na satisfação dos clientes internos",
            height=150
        )
        
        submitted = st.form_submit_button("💾 Salvar Project Charter")
        
        if submitted:
            # Preparar dados para salvar
            charter_data = {
                'project_name': project_name,
                'problem_statement': problem_statement,
                'goal_statement': goal_statement,
                'scope_in': scope_in,
                'scope_out': scope_out,
                'expected_benefits': expected_benefits,
                'project_sponsor': project_sponsor,
                'project_leader': project_leader,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
            
            if supabase:
                try:
                    # Verificar se projeto existe
                    existing = supabase.table('projects').select("*").eq('name', project_name).execute()
                    
                    if existing.data:
                        # Atualizar projeto existente
                        project_id = existing.data[0]['id']
                        
                        # Atualizar projeto
                        supabase.table('projects').update({
                            'description': problem_statement,
                            'updated_at': datetime.now().isoformat()
                        }).eq('id', project_id).execute()
                        
                        # Salvar/atualizar documento define
                        define_doc = {
                            'project_id': project_id,
                            'document_type': 'charter',
                            'title': 'Project Charter',
                            'content': charter_data,
                            'problem_statement': problem_statement,
                            'goal_statement': goal_statement,
                            'scope_in': scope_in,
                            'scope_out': scope_out,
                            'expected_benefits': expected_benefits
                        }
                        
                        # Verificar se já existe documento
                        existing_doc = supabase.table('define_documents').select("*").eq('project_id', project_id).eq('document_type', 'charter').execute()
                        
                        if existing_doc.data:
                            # Atualizar
                            supabase.table('define_documents').update(define_doc).eq('id', existing_doc.data[0]['id']).execute()
                        else:
                            # Inserir
                            supabase.table('define_documents').insert(define_doc).execute()
                        
                        st.session_state.project_id = project_id
                        st.success(f"✅ Project Charter atualizado! (Projeto ID: {project_id})")
                    else:
                        # Criar novo projeto
                        response = supabase.table('projects').insert({
                            'name': project_name,
                            'description': problem_statement
                        }).execute()
                        
                        if response.data:
                            project_id = response.data[0]['id']
                            
                            # Salvar documento define
                            supabase.table('define_documents').insert({
                                'project_id': project_id,
                                'document_type': 'charter',
                                'title': 'Project Charter',
                                'content': charter_data,
                                'problem_statement': problem_statement,
                                'goal_statement': goal_statement,
                                'scope_in': scope_in,
                                'scope_out': scope_out,
                                'expected_benefits': expected_benefits
                            }).execute()
                            
                            st.session_state.project_id = project_id
                            st.success(f"✅ Projeto criado com sucesso! (ID: {project_id})")
                    
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                # Salvar no session state se não houver Supabase
                st.session_state.project_data = charter_data
                st.success("✅ Project Charter salvo localmente!")

# Tab 2: Metas SMART
with tab2:
    st.header("Metas SMART")
    st.info("Defina metas Específicas, Mensuráveis, Alcançáveis, Relevantes e Temporais")
    
    with st.form("smart_form"):
        specific = st.text_area(
            "**S**pecific (Específica)",
            value="Reduzir as paradas não programadas de caminhões causadas especificamente por baixa pressão no sistema de alimentação de diesel",
            height=100
        )
        
        measurable = st.text_area(
            "**M**easurable (Mensurável)",
            value="Reduzir de 15 paradas/mês (baseline atual) para 6 paradas/mês, representando uma redução de 60%",
            height=100
        )
        
        achievable = st.text_area(
            "**A**chievable (Alcançável)",
            value="Meta alcançável através de: análise de qualidade do combustível, treinamento de operadores, padronização do processo de abastecimento e manutenção preventiva",
            height=100
        )
        
        relevant = st.text_area(
            "**R**elevant (Relevante)",
            value="Impacta diretamente na disponibilidade da frota, redução de custos de manutenção e satisfação dos clientes internos",
            height=100
        )
        
        time_bound = st.text_area(
            "**T**ime-bound (Temporal)",
            value="Implementação completa em 3 meses, com checkpoints mensais para avaliar progresso",
            height=100
        )
        
        submitted = st.form_submit_button("💾 Salvar Metas SMART")
        
        if submitted:
            smart_data = {
                'specific': specific,
                'measurable': measurable,
                'achievable': achievable,
                'relevant': relevant,
                'time_bound': time_bound
            }
            
            if supabase and st.session_state.project_id:
                try:
                    # Atualizar ou criar documento SMART
                    existing = supabase.table('define_documents').select("*").eq('project_id', st.session_state.project_id).eq('document_type', 'smart').execute()
                    
                    doc_data = {
                        'project_id': st.session_state.project_id,
                        'document_type': 'smart',
                        'title': 'Metas SMART',
                        'content': smart_data,
                        'smart_specific': specific,
                        'smart_measurable': measurable,
                        'smart_achievable': achievable,
                        'smart_relevant': relevant,
                        'smart_time_bound': time_bound
                    }
                    
                    if existing.data:
                        supabase.table('define_documents').update(doc_data).eq('id', existing.data[0]['id']).execute()
                    else:
                        supabase.table('define_documents').insert(doc_data).execute()
                    
                    st.success("✅ Metas SMART salvas!")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.session_state.project_data['smart'] = smart_data
                st.success("✅ Metas SMART salvas localmente!")

# Tab 3: Stakeholders
with tab3:
    st.header("Análise de Stakeholders")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Adicionar Stakeholder")
        
        with st.form("stakeholder_form"):
            stake_name = st.text_input("Nome/Área")
            stake_role = st.selectbox(
                "Papel no Projeto",
                ["Sponsor", "Cliente", "Fornecedor", "Equipe", "Consultivo", "Afetado"]
            )
            stake_influence = st.select_slider(
                "Influência",
                options=["Baixa", "Média", "Alta"]
            )
            stake_interest = st.select_slider(
                "Interesse",
                options=["Baixo", "Médio", "Alto"]
            )
            stake_strategy = st.text_area("Estratégia de Engajamento")
            
            if st.form_submit_button("Adicionar"):
                if 'stakeholders' not in st.session_state:
                    st.session_state.stakeholders = []
                
                st.session_state.stakeholders.append({
                    'nome': stake_name,
                    'papel': stake_role,
                    'influencia': stake_influence,
                    'interesse': stake_interest,
                    'estrategia': stake_strategy
                })
                st.success(f"✅ {stake_name} adicionado!")
    
    with col2:
        st.subheader("Stakeholders Cadastrados")
        
        # Stakeholders padrão do projeto
        default_stakeholders = [
            {'nome': 'Diretoria de Operações', 'papel': 'Sponsor', 'influencia': 'Alta', 'interesse': 'Alto'},
            {'nome': 'Manutenção', 'papel': 'Equipe', 'influencia': 'Alta', 'interesse': 'Alto'},
            {'nome': 'Operadores', 'papel': 'Afetado', 'influencia': 'Média', 'interesse': 'Alto'},
            {'nome': 'Qualidade', 'papel': 'Consultivo', 'influencia': 'Média', 'interesse': 'Médio'},
            {'nome': 'Suprimentos', 'papel': 'Fornecedor', 'influencia': 'Média', 'interesse': 'Médio'}
        ]
        
        if 'stakeholders' not in st.session_state:
            st.session_state.stakeholders = default_stakeholders
        
        for stake in st.session_state.stakeholders:
            with st.expander(stake['nome']):
                st.write(f"**Papel:** {stake['papel']}")
                st.write(f"**Influência:** {stake['influencia']}")
                st.write(f"**Interesse:** {stake['interesse']}")
                if 'estrategia' in stake:
                    st.write(f"**Estratégia:** {stake['estrategia']}")

# Tab 4: SIPOC
with tab4:
    st.header("Diagrama SIPOC")
    st.info("Suppliers → Inputs → Process → Outputs → Customers")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.subheader("Suppliers")
        suppliers = st.text_area(
            "Fornecedores",
            value="• Distribuidora de Diesel\n• Fabricante de Filtros\n• Lab. de Análises\n• Consultoria Técnica",
            height=200
        )
    
    with col2:
        st.subheader("Inputs")
        inputs = st.text_area(
            "Entradas",
            value="• Diesel\n• Filtros\n• Aditivos\n• Procedimentos\n• Ferramentas",
            height=200
        )
    
    with col3:
        st.subheader("Process")
        process = st.text_area(
            "Processo",
            value="• Recebimento\n• Armazenamento\n• Filtragem\n• Abastecimento\n• Monitoramento",
            height=200
        )
    
    with col4:
        st.subheader("Outputs")
        outputs = st.text_area(
            "Saídas",
            value="• Caminhão abastecido\n• Pressão adequada\n• Relatórios\n• Indicadores",
            height=200
        )
    
    with col5:
        st.subheader("Customers")
        customers = st.text_area(
            "Clientes",
            value="• Operação\n• Motoristas\n• Manutenção\n• Gestão",
            height=200
        )
    
    if st.button("💾 Salvar SIPOC"):
        sipoc_data = {
            'suppliers': suppliers,
            'inputs': inputs,
            'process': process,
            'outputs': outputs,
            'customers': customers
        }
        
        if supabase and st.session_state.project_id:
            try:
                supabase.table('define_documents').insert({
                    'project_id': st.session_state.project_id,
                    'document_type': 'sipoc',
                    'title': 'Diagrama SIPOC',
                    'content': sipoc_data
                }).execute()
                st.success("✅ SIPOC salvo!")
            except Exception as e:
                st.error(f"Erro: {e}")

# Tab 5: Projetos Salvos
with tab5:
    st.header("Projetos Salvos")
    
    if supabase:
        try:
            projects = supabase.table('projects').select("*").order('created_at', desc=True).execute()
            
            if projects.data:
                for project in projects.data:
                    with st.expander(f"📁 {project['name']} (ID: {project['id']})"):
                        st.write(f"**Descrição:** {project.get('description', 'N/A')}")
                        st.write(f"**Criado em:** {project.get('created_at', 'N/A')}")
                        
                        if st.button(f"Carregar Projeto", key=f"load_{project['id']}"):
                            st.session_state.project_id = project['id']
                            st.success(f"Projeto {project['id']} carregado!")
                            st.rerun()
            else:
                st.info("Nenhum projeto salvo ainda.")
        except Exception as e:
            st.error(f"Erro ao carregar projetos: {e}")
    else:
        st.warning("Supabase não configurado")

# Footer com status
st.markdown("---")
if st.session_state.project_id:
    st.success(f"🎯 Projeto Ativo: ID {st.session_state.project_id}")
else:
    st.info("💡 Preencha o Project Charter para criar um novo projeto")
