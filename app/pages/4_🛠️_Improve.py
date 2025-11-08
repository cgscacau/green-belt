import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import os
from supabase import create_client, Client

# Configuração da página
st.set_page_config(
    page_title="Improve - Green Belt",
    page_icon="🔧",
    layout="wide"
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

# Função para carregar projeto
def load_project_from_db(project_name):
    """Carrega dados do projeto do banco"""
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

# Função para listar projetos
@st.cache_data(ttl=300)
def list_projects():
    """Lista todos os projetos disponíveis"""
    if not supabase:
        return []
    
    try:
        response = supabase.table('projects').select("project_name, project_leader, status").execute()
        if response.data:
            return response.data
        return []
    except Exception as e:
        st.error(f"Erro ao listar projetos: {str(e)}")
        return []

# Função para buscar análises realizadas
def load_analyses(project_name):
    """Carrega análises realizadas do projeto"""
    if not supabase:
        return None
    
    try:
        response = supabase.table('analyses').select("*").eq('project_name', project_name).execute()
        if response.data:
            return pd.DataFrame(response.data)
        return None
    except Exception as e:
        st.error(f"Erro ao carregar análises: {str(e)}")
        return None

# Função para salvar ação de melhoria
def save_improvement_action(project_name, action_data):
    """Salva ação de melhoria no banco"""
    if not supabase:
        return False
    
    try:
        action_data['project_name'] = project_name
        action_data['created_at'] = datetime.now().isoformat()
        action_data['updated_at'] = datetime.now().isoformat()
        
        response = supabase.table('improvement_actions').insert(action_data).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar ação: {str(e)}")
        return False

# Função para carregar ações de melhoria
def load_improvement_actions(project_name):
    """Carrega ações de melhoria do projeto"""
    if not supabase:
        return None
    
    try:
        response = supabase.table('improvement_actions').select("*").eq('project_name', project_name).order('priority').execute()
        if response.data:
            return pd.DataFrame(response.data)
        return None
    except Exception as e:
        st.error(f"Erro ao carregar ações: {str(e)}")
        return None

# Função para atualizar status de ação
def update_action_status(action_id, new_status):
    """Atualiza status de uma ação"""
    if not supabase:
        return False
    
    try:
        response = supabase.table('improvement_actions').update({
            'status': new_status,
            'updated_at': datetime.now().isoformat()
        }).eq('id', action_id).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar status: {str(e)}")
        return False

# ========================= SIDEBAR =========================

with st.sidebar:
    st.header("🗂️ Seleção de Projeto")
    
    if not supabase:
        st.error("⚠️ Supabase não configurado")
        use_local = st.checkbox("Usar modo local")
    else:
        use_local = False
        st.success("✅ Conectado ao Supabase")
    
    st.divider()
    
    # Listar projetos
    if supabase:
        projects = list_projects()
        
        if projects:
            project_names = [p['project_name'] for p in projects]
            
            default_index = 0
            if 'project_name' in st.session_state and st.session_state.project_name in project_names:
                default_index = project_names.index(st.session_state.project_name) + 1
            
            selected_project = st.selectbox(
                "Selecione um projeto:",
                [""] + project_names,
                index=default_index
            )
            
            if selected_project:
                if st.button("📂 Carregar Projeto", type="primary"):
                    project_data = load_project_from_db(selected_project)
                    if project_data:
                        st.session_state.project_name = selected_project
                        st.session_state.project_data = project_data
                        st.success(f"✅ Projeto '{selected_project}' carregado!")
                        st.rerun()
        else:
            st.warning("Nenhum projeto encontrado")
    
    # Mostrar projeto ativo
    if 'project_name' in st.session_state:
        st.divider()
        st.success(f"📁 **Projeto Ativo:**")
        st.write(f"_{st.session_state.project_name}_")
        
        # Carregar análises realizadas
        analyses_df = load_analyses(st.session_state.project_name)
        if analyses_df is not None and len(analyses_df) > 0:
            st.metric("Análises Realizadas", len(analyses_df))
            analysis_types = analyses_df['analysis_type'].unique()
            for atype in analysis_types:
                st.caption(f"✓ {atype}")

# ========================= INTERFACE PRINCIPAL =========================

st.title("🔧 Improve — Implementação de Melhorias")
st.markdown("Esta fase foca na implementação de soluções para os problemas identificados.")

# Verificar se há projeto selecionado
if 'project_name' not in st.session_state:
    st.warning("⚠️ Nenhum projeto selecionado. Por favor, selecione ou crie um projeto na página Define.")
    
    if supabase:
        projects = list_projects()
        if projects:
            st.subheader("📂 Projetos Disponíveis")
            df = pd.DataFrame(projects)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.info("👈 Use a barra lateral para selecionar um projeto")
    st.stop()

# Projeto selecionado
project_name = st.session_state.project_name
project_data = st.session_state.get('project_data', {})

st.info(f"📁 Projeto: **{project_name}**")

# Verificar se há análises realizadas
analyses_df = load_analyses(project_name)

if analyses_df is None or len(analyses_df) == 0:
    st.warning("⚠️ Nenhuma análise encontrada para este projeto.")
    st.info("""
    **Para começar a fase Improve:**
    1. Complete a fase **Analyze** primeiro
    2. Realize pelo menos uma análise de causa raiz
    3. Identifique as principais causas do problema
    """)
    
    if st.button("📊 Ir para Analyze"):
        st.switch_page("pages/3_📊_Analyze.py")
    st.stop()

# Mostrar resumo das análises
with st.expander("📊 Ver Análises Realizadas"):
    st.dataframe(
        analyses_df[['analysis_type', 'created_at']],
        use_container_width=True,
        hide_index=True
    )

# Tabs principais
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💡 Brainstorming",
    "🎯 Priorização",
    "📋 Plano de Ação",
    "🔬 Simulação",
    "📈 Dashboard"
])

# ========================= TAB 1: BRAINSTORMING =========================

with tab1:
    st.header("💡 Sessão de Brainstorming")
    st.markdown("Gere e organize ideias de melhoria baseadas nas análises realizadas")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Formulário para adicionar ideias
        with st.form("brainstorming_form", clear_on_submit=True):
            st.subheader("Nova Ideia de Melhoria")
            
            idea_title = st.text_input("Título da Ideia *")
            idea_description = st.text_area("Descrição Detalhada *", height=100)
            
            col_form1, col_form2 = st.columns(2)
            with col_form1:
                category = st.selectbox(
                    "Categoria",
                    ["Processo", "Tecnologia", "Pessoas", "Materiais", "Ambiente", "Método"]
                )
                expected_impact = st.select_slider(
                    "Impacto Esperado",
                    options=["Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"],
                    value="Médio"
                )
            
            with col_form2:
                implementation_effort = st.select_slider(
                    "Esforço de Implementação",
                    options=["Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"],
                    value="Médio"
                )
                responsible = st.text_input("Responsável Sugerido")
            
            benefits = st.text_area("Benefícios Esperados", height=80)
            risks = st.text_area("Riscos Potenciais", height=80)
            
            submitted = st.form_submit_button("➕ Adicionar Ideia", type="primary")
            
            if submitted:
                if idea_title and idea_description:
                    # Adicionar ao session_state
                    if 'brainstorm_ideas' not in st.session_state:
                        st.session_state.brainstorm_ideas = []
                    
                    idea = {
                        'title': idea_title,
                        'description': idea_description,
                        'category': category,
                        'impact': expected_impact,
                        'effort': implementation_effort,
                        'responsible': responsible,
                        'benefits': benefits,
                        'risks': risks,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    st.session_state.brainstorm_ideas.append(idea)
                    st.success("✅ Ideia adicionada!")
                    st.rerun()
                else:
                    st.error("Preencha os campos obrigatórios")
    
    with col2:
        st.info("""
        **💡 Dicas para Brainstorming:**
        
        **Técnicas:**
        - SCAMPER
        - 6 Thinking Hats
        - Mind Mapping
        - Reverse Brainstorming
        
        **Regras:**
        - Quantidade sobre qualidade
        - Sem julgamentos
        - Construa sobre outras ideias
        - Pense fora da caixa
        """)
    
    # Exibir ideias cadastradas
    if 'brainstorm_ideas' in st.session_state and st.session_state.brainstorm_ideas:
        st.divider()
        st.subheader("💭 Ideias Geradas")
        
        ideas_df = pd.DataFrame(st.session_state.brainstorm_ideas)
        
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            filter_category = st.multiselect(
                "Filtrar por Categoria",
                ideas_df['category'].unique()
            )
        with col2:
            filter_impact = st.multiselect(
                "Filtrar por Impacto",
                ["Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"]
            )
        
        # Aplicar filtros
        filtered_df = ideas_df.copy()
        if filter_category:
            filtered_df = filtered_df[filtered_df['category'].isin(filter_category)]
        if filter_impact:
            filtered_df = filtered_df[filtered_df['impact'].isin(filter_impact)]
        
        # Cards de ideias
        for idx, idea in filtered_df.iterrows():
            with st.expander(f"💡 {idea['title']} - {idea['category']}"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Descrição:** {idea['description']}")
                    if idea['benefits']:
                        st.write(f"**Benefícios:** {idea['benefits']}")
                    if idea['risks']:
                        st.write(f"**Riscos:** {idea['risks']}")
                with col2:
                    st.metric("Impacto", idea['impact'])
                    st.metric("Esforço", idea['effort'])
                    if idea['responsible']:
                        st.caption(f"Responsável: {idea['responsible']}")

# ========================= TAB 2: PRIORIZAÇÃO =========================

with tab2:
    st.header("🎯 Matriz de Priorização")
    st.markdown("Priorize as ideias usando a matriz Impacto vs Esforço")
    
    if 'brainstorm_ideas' in st.session_state and st.session_state.brainstorm_ideas:
        # Converter impacto e esforço para valores numéricos
        impact_map = {
            "Muito Baixo": 1, "Baixo": 2, "Médio": 3, 
            "Alto": 4, "Muito Alto": 5
        }
        effort_map = {
            "Muito Baixo": 1, "Baixo": 2, "Médio": 3,
            "Alto": 4, "Muito Alto": 5
        }
        
        # Preparar dados para o gráfico
        plot_data = []
        for idea in st.session_state.brainstorm_ideas:
            plot_data.append({
                'title': idea['title'],
                'impact_value': impact_map[idea['impact']],
                'effort_value': effort_map[idea['effort']],
                'category': idea['category']
            })
        
        plot_df = pd.DataFrame(plot_data)
        
        # Criar scatter plot
        fig = px.scatter(
            plot_df,
            x='effort_value',
            y='impact_value',
            text='title',
            color='category',
            title='Matriz de Priorização: Impacto vs Esforço',
            labels={'effort_value': 'Esforço →', 'impact_value': 'Impacto →'},
            hover_data=['title', 'category']
        )
        
        # Adicionar quadrantes
        fig.add_hline(y=3, line_dash="dash", line_color="gray", opacity=0.5)
        fig.add_vline(x=3, line_dash="dash", line_color="gray", opacity=0.5)
        
        # Adicionar anotações dos quadrantes
        fig.add_annotation(x=1.5, y=4.5, text="Quick Wins", showarrow=False,
                          font=dict(size=12, color="green"))
        fig.add_annotation(x=4.5, y=4.5, text="Grandes Projetos", showarrow=False,
                          font=dict(size=12, color="orange"))
        fig.add_annotation(x=1.5, y=1.5, text="Fill Ins", showarrow=False,
                          font=dict(size=12, color="gray"))
        fig.add_annotation(x=4.5, y=1.5, text="Questionáveis", showarrow=False,
                          font=dict(size=12, color="red"))
        
        fig.update_layout(
            xaxis=dict(range=[0.5, 5.5], tickvals=[1,2,3,4,5],
                      ticktext=['Muito Baixo', 'Baixo', 'Médio', 'Alto', 'Muito Alto']),
            yaxis=dict(range=[0.5, 5.5], tickvals=[1,2,3,4,5],
                      ticktext=['Muito Baixo', 'Baixo', 'Médio', 'Alto', 'Muito Alto']),
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Análise dos quadrantes
        st.divider()
        st.subheader("📊 Análise da Priorização")
        
        # Quick Wins (Alto impacto, Baixo esforço)
        quick_wins = plot_df[(plot_df['impact_value'] >= 3) & (plot_df['effort_value'] <= 3)]
        grandes_projetos = plot_df[(plot_df['impact_value'] >= 3) & (plot_df['effort_value'] > 3)]
        fill_ins = plot_df[(plot_df['impact_value'] < 3) & (plot_df['effort_value'] <= 3)]
        questionaveis = plot_df[(plot_df['impact_value'] < 3) & (plot_df['effort_value'] > 3)]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🎯 Quick Wins", len(quick_wins))
            if len(quick_wins) > 0:
                for title in quick_wins['title']:
                    st.caption(f"• {title}")
        
        with col2:
            st.metric("🚀 Grandes Projetos", len(grandes_projetos))
            if len(grandes_projetos) > 0:
                for title in grandes_projetos['title']:
                    st.caption(f"• {title}")
        
        with col3:
            st.metric("📌 Fill Ins", len(fill_ins))
            if len(fill_ins) > 0:
                for title in fill_ins['title']:
                    st.caption(f"• {title}")
        
        with col4:
            st.metric("❓ Questionáveis", len(questionaveis))
            if len(questionaveis) > 0:
                for title in questionaveis['title']:
                    st.caption(f"• {title}")
        
        # Recomendação
        st.success(f"""
        **💡 Recomendação:**
        Priorize as {len(quick_wins)} ideias classificadas como **Quick Wins**.
        Estas oferecem alto impacto com baixo esforço de implementação.
        """)
    else:
        st.info("Adicione ideias na aba Brainstorming primeiro")

# ========================= TAB 3: PLANO DE AÇÃO =========================

with tab3:
    st.header("📋 Plano de Ação Detalhado")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("action_plan_form", clear_on_submit=True):
            st.subheader("Nova Ação")
            
            action_title = st.text_input("Título da Ação *")
            action_description = st.text_area("Descrição Detalhada *", height=100)
            
            col_form1, col_form2, col_form3 = st.columns(3)
            
            with col_form1:
                responsible = st.text_input("Responsável *")
                impact_level = st.selectbox(
                    "Nível de Impacto",
                    ["Baixo", "Médio", "Alto", "Crítico"]
                )
            
            with col_form2:
                due_date = st.date_input("Data de Conclusão", 
                                        min_value=datetime.now().date())
                effort_level = st.selectbox(
                    "Nível de Esforço",
                    ["Baixo", "Médio", "Alto", "Muito Alto"]
                )
            
            with col_form3:
                status = st.selectbox(
                    "Status",
                    ["Não Iniciado", "Em Andamento", "Pausado", "Concluído", "Cancelado"]
                )
                priority = st.number_input("Prioridade (1-10)", 1, 10, 5)
            
            success_criteria = st.text_area("Critérios de Sucesso", height=80)
            resources_needed = st.text_area("Recursos Necessários", height=80)
            
            submitted = st.form_submit_button("➕ Adicionar Ação", type="primary")
            
            if submitted:
                if all([action_title, action_description, responsible]):
                    action = {
                        'action_title': action_title,
                        'description': action_description,
                        'responsible': responsible,
                        'due_date': due_date.isoformat(),
                        'status': status,
                        'impact_level': impact_level,
                        'effort_level': effort_level,
                        'priority': priority,
                        'success_criteria': success_criteria,
                        'resources_needed': resources_needed
                    }
                    
                    if save_improvement_action(project_name, action):
                        st.success("✅ Ação adicionada com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro ao salvar ação")
                else:
                    st.error("Preencha os campos obrigatórios")
    
    with col2:
        st.info("""
        **📋 Estrutura 5W2H:**
        
        - **What:** O que será feito?
        - **Why:** Por que fazer?
        - **Who:** Quem fará?
        - **When:** Quando será feito?
        - **Where:** Onde será feito?
        - **How:** Como será feito?
        - **How Much:** Quanto custará?
        """)
    
    # Exibir plano de ação
    actions_df = load_improvement_actions(project_name)
    
    if actions_df is not None and len(actions_df) > 0:
        st.divider()
        st.subheader("📊 Ações Cadastradas")
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_status = st.multiselect(
                "Filtrar por Status",
                actions_df['status'].unique(),
                default=["Não Iniciado", "Em Andamento"]
            )
        with col2:
            filter_responsible = st.multiselect(
                "Filtrar por Responsável",
                actions_df['responsible'].unique()
            )
        with col3:
            filter_impact = st.multiselect(
                "Filtrar por Impacto",
                actions_df['impact_level'].unique()
            )
        
        # Aplicar filtros
        filtered_actions = actions_df.copy()
        if filter_status:
            filtered_actions = filtered_actions[filtered_actions['status'].isin(filter_status)]
        if filter_responsible:
            filtered_actions = filtered_actions[filtered_actions['responsible'].isin(filter_responsible)]
        if filter_impact:
            filtered_actions = filtered_actions[filtered_actions['impact_level'].isin(filter_impact)]
        
        # Exibir ações
        for idx, action in filtered_actions.iterrows():
            with st.expander(f"📌 {action['action_title']} - {action['status']}"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**Descrição:** {action['description']}")
                    if pd.notna(action.get('success_criteria')):
                        st.write(f"**Critérios de Sucesso:** {action['success_criteria']}")
                    if pd.notna(action.get('resources_needed')):
                        st.write(f"**Recursos:** {action['resources_needed']}")
                
                with col2:
                    st.metric("Responsável", action['responsible'])
                    st.metric("Prioridade", action['priority'])
                    st.metric("Impacto", action['impact_level'])
                
                with col3:
                    st.metric("Prazo", action['due_date'])
                    st.metric("Esforço", action['effort_level'])
                    
                    # Botão para atualizar status
                    new_status = st.selectbox(
                        "Atualizar Status",
                        ["Não Iniciado", "Em Andamento", "Pausado", "Concluído", "Cancelado"],
                        index=["Não Iniciado", "Em Andamento", "Pausado", "Concluído", "Cancelado"].index(action['status']),
                        key=f"status_{action['id']}"
                    )
                    
                    if st.button("Atualizar", key=f"update_{action['id']}"):
                        if update_action_status(action['id'], new_status):
                            st.success("Status atualizado!")
                            st.rerun()
        
        # Gantt Chart
        st.divider()
        st.subheader("📅 Cronograma de Ações (Gantt)")
        
        # Preparar dados para Gantt
        gantt_data = []
        for idx, action in filtered_actions.iterrows():
            gantt_data.append({
                'Task': action['action_title'],
                'Start': datetime.now().date(),
                'Finish': pd.to_datetime(action['due_date']).date(),
                'Resource': action['responsible'],
                'Status': action['status']
            })
        
        if gantt_data:
            gantt_df = pd.DataFrame(gantt_data)
            
            # Criar gráfico Gantt
            fig = px.timeline(
                gantt_df,
                x_start="Start",
                x_end="Finish",
                y="Task",
                color="Status",
                hover_data=["Resource", "Status"],
                title="Cronograma de Implementação"
            )
            
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(height=400)
            
            st.plotly_chart(fig, use_container_width=True)

# ========================= TAB 4: SIMULAÇÃO =========================

with tab4:
    st.header("🔬 Simulação de Melhorias")
    st.markdown("Simule o impacto das melhorias propostas")
    
    # Dados do projeto
    baseline = project_data.get('baseline_value', 100)
    target = project_data.get('target_value', 80)
    metric = project_data.get('primary_metric', 'Métrica')
    
    st.subheader("📊 Simulação de Cenários")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Parâmetros da simulação
        st.write("**Configure os Parâmetros:**")
        
        improvement_percentage = st.slider(
            "Melhoria Esperada (%)",
            min_value=0,
            max_value=100,
            value=20,
            step=5
        )
        
        confidence_level = st.slider(
            "Nível de Confiança (%)",
            min_value=50,
            max_value=99,
            value=80,
            step=5
        )
        
        implementation_time = st.slider(
            "Tempo de Implementação (dias)",
            min_value=7,
            max_value=180,
            value=30,
            step=7
        )
        
        # Calcular valores simulados
        current_value = baseline
        expected_value = current_value * (1 - improvement_percentage/100)
        
        # Simular variação
        np.random.seed(42)
        days = np.arange(0, implementation_time + 1)
        
        # Cenários
        best_case = current_value - (current_value - expected_value) * 1.2
        worst_case = current_value - (current_value - expected_value) * 0.5
        
        # Simulação com ruído
        simulated_values = []
        for day in days:
            progress = day / implementation_time
            value = current_value - (current_value - expected_value) * progress
            noise = np.random.normal(0, value * 0.05)
            simulated_values.append(value + noise)
        
        # Criar gráfico de simulação
        fig = go.Figure()
        
        # Linha de simulação
        fig.add_trace(go.Scatter(
            x=days,
            y=simulated_values,
            mode='lines',
            name='Simulação',
            line=dict(color='blue', width=2)
        ))
        
        # Linha de meta
        fig.add_hline(
            y=target,
            line_dash="dash",
            line_color="green",
            annotation_text=f"Meta: {target}"
        )
        
        # Linha baseline
        fig.add_hline(
            y=baseline,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Baseline: {baseline}"
        )
        
        # Área de confiança
        upper_bound = [v * (1 + (100-confidence_level)/200) for v in simulated_values]
        lower_bound = [v * (1 - (100-confidence_level)/200) for v in simulated_values]
        
        fig.add_trace(go.Scatter(
            x=days,
            y=upper_bound,
            fill=None,
            mode='lines',
            line_color='rgba(0,100,80,0)',
            showlegend=False
        ))
        
        fig.add_trace(go.Scatter(
            x=days,
            y=lower_bound,
            fill='tonexty',
            mode='lines',
            line_color='rgba(0,100,80,0)',
            name=f'Intervalo {confidence_level}%',
            fillcolor='rgba(0,100,80,0.2)'
        ))
        
        fig.update_layout(
            title=f"Simulação de Melhoria - {metric}",
            xaxis_title="Dias",
            yaxis_title=metric,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.write("**📊 Resultados da Simulação:**")
        
        st.metric("Valor Atual", f"{current_value:.1f}")
        st.metric("Valor Esperado", f"{expected_value:.1f}",
                 f"{expected_value - current_value:.1f}")
        
        st.divider()
        
        st.metric("Melhor Cenário", f"{best_case:.1f}")
        st.metric("Pior Cenário", f"{worst_case:.1f}")
        
        st.divider()
        
        # Probabilidade de sucesso
        prob_success = confidence_level if expected_value <= target else confidence_level * (target/expected_value)
        st.metric("Prob. de Atingir Meta", f"{prob_success:.0f}%")
        
        # ROI estimado
        if project_data.get('expected_savings'):
            roi = (project_data['expected_savings'] * improvement_percentage/100) / 1000
            st.metric("ROI Estimado", f"R$ {roi:.0f}k")

# ========================= TAB 5: DASHBOARD =========================

with tab5:
    st.header("📈 Dashboard de Acompanhamento")
    
    # Métricas gerais
    col1, col2, col3, col4 = st.columns(4)
    
    # Carregar dados
    actions_df = load_improvement_actions(project_name)
    
    if actions_df is not None and len(actions_df) > 0:
        with col1:
            total_actions = len(actions_df)
            st.metric("Total de Ações", total_actions)
        
        with col2:
            completed = len(actions_df[actions_df['status'] == 'Concluído'])
            completion_rate = (completed / total_actions * 100) if total_actions > 0 else 0
            st.metric("Taxa de Conclusão", f"{completion_rate:.0f}%")
        
        with col3:
            in_progress = len(actions_df[actions_df['status'] == 'Em Andamento'])
            st.metric("Em Andamento", in_progress)
        
        with col4:
            high_priority = len(actions_df[actions_df['priority'] >= 8])
            st.metric("Alta Prioridade", high_priority)
        
        st.divider()
        
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de status
            status_counts = actions_df['status'].value_counts()
            
            fig_status = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Distribuição por Status",
                color_discrete_map={
                    'Concluído': 'green',
                    'Em Andamento': 'blue',
                    'Não Iniciado': 'gray',
                    'Pausado': 'orange',
                    'Cancelado': 'red'
                }
            )
            st.plotly_chart(fig_status, use_container_width=True)
        
        with col2:
            # Gráfico de responsáveis
            resp_counts = actions_df['responsible'].value_counts().head(5)
            
            fig_resp = px.bar(
                x=resp_counts.values,
                y=resp_counts.index,
                orientation='h',
                title="Top 5 Responsáveis",
                labels={'x': 'Número de Ações', 'y': 'Responsável'}
            )
            st.plotly_chart(fig_resp, use_container_width=True)
        
        # Timeline de ações
        st.divider()
        st.subheader("📅 Timeline de Ações")
        
        # Preparar dados para timeline
        timeline_data = []
        for idx, action in actions_df.iterrows():
            color = {
                'Concluído': 'green',
                'Em Andamento': 'blue',
                'Não Iniciado': 'gray',
                'Pausado': 'orange',
                'Cancelado': 'red'
            }.get(action['status'], 'gray')
            
            timeline_data.append({
                'Ação': action['action_title'][:30] + '...' if len(action['action_title']) > 30 else action['action_title'],
                'Responsável': action['responsible'],
                'Prazo': pd.to_datetime(action['due_date']),
                'Status': action['status'],
                'Prioridade': action['priority']
            })
        
        timeline_df = pd.DataFrame(timeline_data)
        timeline_df = timeline_df.sort_values('Prazo')
        
        # Exibir tabela
        st.dataframe(
            timeline_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Prioridade": st.column_config.ProgressColumn(
                    "Prioridade",
                    min_value=0,
                    max_value=10,
                    format="%d"
                ),
                "Prazo": st.column_config.DateColumn("Prazo", format="DD/MM/YYYY")
            }
        )
    else:
        st.info("Nenhuma ação cadastrada ainda. Adicione ações na aba 'Plano de Ação'.")

# Footer
st.divider()
st.caption("💡 **Dica:** Foque primeiro nas ações classificadas como 'Quick Wins' para obter resultados rápidos")
