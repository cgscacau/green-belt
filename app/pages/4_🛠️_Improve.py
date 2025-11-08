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

def save_improvement_action(project_name, action_data):
    """Salva ação de melhoria no banco com tratamento de campos opcionais"""
    if not supabase:
        return False
    
    try:
        # Garantir que todos os campos necessários existam
        action_record = {
            'project_name': project_name,
            'action_title': action_data.get('action_title', ''),
            'description': action_data.get('description', ''),
            'responsible': action_data.get('responsible', ''),
            'due_date': action_data.get('due_date'),
            'status': action_data.get('status', 'Não Iniciado'),
            'impact_level': action_data.get('impact_level', 'Médio'),
            'effort_level': action_data.get('effort_level', 'Médio'),
            'priority': action_data.get('priority', 5),
            'success_criteria': action_data.get('success_criteria', ''),
            'resources_needed': action_data.get('resources_needed', ''),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Remover campos None para evitar erros
        action_record = {k: v for k, v in action_record.items() if v is not None}
        
        response = supabase.table('improvement_actions').insert(action_record).execute()
        return True
        
    except Exception as e:
        st.error(f"Erro ao salvar ação: {str(e)}")
        
        # Debug - mostrar estrutura esperada
        if "could not find" in str(e).lower():
            st.error("Estrutura da tabela incorreta. Execute o script SQL fornecido.")
            with st.expander("Ver script SQL de correção"):
                st.code("""
                ALTER TABLE improvement_actions 
                ADD COLUMN IF NOT EXISTS success_criteria TEXT,
                ADD COLUMN IF NOT EXISTS resources_needed TEXT;
                """)
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

# ========================= TAB 1: BRAINSTORMING (CORRIGIDO) =========================

with tab1:
    st.header("💡 Sessão de Brainstorming")
    st.markdown("Gere e organize ideias de melhoria baseadas nas análises realizadas")
    
    # Funções para gerenciar ideias de brainstorming
    def save_brainstorm_idea(project_name, idea_data):
        """Salva ideia de brainstorming no banco"""
        if not supabase:
            return False
        
        try:
            idea_data['project_name'] = project_name
            idea_data['created_at'] = datetime.now().isoformat()
            
            response = supabase.table('brainstorm_ideas').insert(idea_data).execute()
            return True
        except Exception as e:
            st.error(f"Erro ao salvar ideia: {str(e)}")
            return False
    
    def load_brainstorm_ideas(project_name):
        """Carrega ideias de brainstorming do projeto"""
        if not supabase:
            return None
        
        try:
            response = supabase.table('brainstorm_ideas').select("*").eq('project_name', project_name).order('created_at', desc=True).execute()
            if response.data:
                return pd.DataFrame(response.data)
            return None
        except Exception as e:
            st.error(f"Erro ao carregar ideias: {str(e)}")
            return None
    
    def update_idea_status(idea_id, new_status):
        """Atualiza status de uma ideia"""
        if not supabase:
            return False
        
        try:
            response = supabase.table('brainstorm_ideas').update({
                'status': new_status
            }).eq('id', idea_id).execute()
            return True
        except Exception as e:
            st.error(f"Erro ao atualizar status: {str(e)}")
            return False
    
    def delete_brainstorm_idea(idea_id):
        """Exclui uma ideia"""
        if not supabase:
            return False
        
        try:
            response = supabase.table('brainstorm_ideas').delete().eq('id', idea_id).execute()
            return True
        except Exception as e:
            st.error(f"Erro ao excluir ideia: {str(e)}")
            return False
    
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
            
            submitted = st.form_submit_button("💾 Salvar Ideia", type="primary")
            
            if submitted:
                if idea_title and idea_description:
                    idea = {
                        'title': idea_title,
                        'description': idea_description,
                        'category': category,
                        'expected_impact': expected_impact,
                        'implementation_effort': implementation_effort,
                        'responsible': responsible,
                        'benefits': benefits,
                        'risks': risks,
                        'status': 'proposed'
                    }
                    
                    # Salvar no banco de dados
                    if save_brainstorm_idea(project_name, idea):
                        st.success("✅ Ideia salva com sucesso no banco de dados!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.warning("⚠️ Erro ao salvar no banco de dados")
                else:
                    st.error("❌ Preencha os campos obrigatórios")
    
    with col2:
        st.info("""
        **💡 Dicas para Brainstorming:**
        
        **Técnicas:**
        - SCAMPER
        - 6 Thinking Hats
        - Mind Mapping
        - Reverse Brainstorming
        
        **Status das Ideias:**
        - **proposed**: Proposta inicial
        - **under_review**: Em análise
        - **approved**: Aprovada
        - **rejected**: Rejeitada
        - **implemented**: Implementada
        """)
    
    # Carregar e exibir ideias cadastradas
    st.divider()
    st.subheader("💭 Ideias Cadastradas")
    
    # Carregar ideias do banco
    ideas_df = load_brainstorm_ideas(project_name)
    
    if ideas_df is not None and len(ideas_df) > 0:
        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total de Ideias", len(ideas_df))
        with col2:
            high_impact_count = len(ideas_df[ideas_df['expected_impact'].isin(['Alto', 'Muito Alto'])]) if 'expected_impact' in ideas_df.columns else 0
            st.metric("Alto Impacto", high_impact_count)
        with col3:
            low_effort_count = len(ideas_df[ideas_df['implementation_effort'].isin(['Baixo', 'Muito Baixo'])]) if 'implementation_effort' in ideas_df.columns else 0
            st.metric("Baixo Esforço", low_effort_count)
        with col4:
            approved_count = len(ideas_df[ideas_df['status'] == 'approved']) if 'status' in ideas_df.columns else 0
            st.metric("Aprovadas", approved_count)
        
        st.divider()
        
        # Filtros - CORRIGIDO
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'category' in ideas_df.columns:
                unique_categories = ideas_df['category'].unique().tolist()
                filter_category = st.multiselect(
                    "Filtrar por Categoria",
                    unique_categories
                )
            else:
                filter_category = []
        
        with col2:
            impact_options = ["Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"]
            filter_impact = st.multiselect(
                "Filtrar por Impacto",
                impact_options
            )
        
        with col3:
            if 'status' in ideas_df.columns:
                unique_status = ideas_df['status'].unique().tolist()
                # Definir valores padrão apenas se existirem nos dados
                default_status = []
                if 'proposed' in unique_status:
                    default_status.append('proposed')
                
                filter_status = st.multiselect(
                    "Filtrar por Status",
                    unique_status,
                    default=default_status if default_status else None
                )
            else:
                filter_status = []
        
        # Aplicar filtros
        filtered_df = ideas_df.copy()
        
        if filter_category and 'category' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['category'].isin(filter_category)]
        
        if filter_impact and 'expected_impact' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['expected_impact'].isin(filter_impact)]
        
        if filter_status and 'status' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['status'].isin(filter_status)]
        
        # Exibir ideias
        if len(filtered_df) > 0:
            st.write(f"Mostrando {len(filtered_df)} de {len(ideas_df)} ideias")
            
            # Cards de ideias
            for idx, idea in filtered_df.iterrows():
                # Garantir que os campos existem
                title = idea.get('title', 'Sem título')
                category = idea.get('category', 'Sem categoria')
                status = idea.get('status', 'proposed')
                
                with st.expander(f"💡 {title} - {category} ({status})"):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        description = idea.get('description', 'Sem descrição')
                        st.write(f"**Descrição:** {description}")
                        
                        if 'benefits' in idea and pd.notna(idea['benefits']) and idea['benefits']:
                            st.write(f"**Benefícios:** {idea['benefits']}")
                        
                        if 'risks' in idea and pd.notna(idea['risks']) and idea['risks']:
                            st.write(f"**Riscos:** {idea['risks']}")
                        
                        if 'responsible' in idea and pd.notna(idea['responsible']) and idea['responsible']:
                            st.write(f"**Responsável Sugerido:** {idea['responsible']}")
                    
                    with col2:
                        impact = idea.get('expected_impact', 'Não definido')
                        effort = idea.get('implementation_effort', 'Não definido')
                        
                        st.metric("Impacto", impact)
                        st.metric("Esforço", effort)
                        
                        # Score de priorização (Quick Win) - apenas se tivermos os dados
                        if impact != 'Não definido' and effort != 'Não definido':
                            impact_score = {"Muito Baixo": 1, "Baixo": 2, "Médio": 3, "Alto": 4, "Muito Alto": 5}
                            effort_score = {"Muito Baixo": 5, "Baixo": 4, "Médio": 3, "Alto": 2, "Muito Alto": 1}
                            
                            priority_score = impact_score.get(impact, 3) * effort_score.get(effort, 3)
                            
                            if priority_score >= 16:
                                st.success(f"🎯 Quick Win (Score: {priority_score})")
                            elif priority_score >= 9:
                                st.info(f"📊 Média Prioridade (Score: {priority_score})")
                            else:
                                st.warning(f"⏸️ Baixa Prioridade (Score: {priority_score})")
                    
                    with col3:
                        if 'created_at' in idea and pd.notna(idea['created_at']):
                            created_date = pd.to_datetime(idea['created_at']).strftime('%d/%m/%Y')
                            st.caption(f"Criado: {created_date}")
                        
                        # Ações - apenas se tivermos ID
                        if 'id' in idea:
                            status_options = ["proposed", "under_review", "approved", "rejected", "implemented"]
                            current_status_index = status_options.index(status) if status in status_options else 0
                            
                            new_status = st.selectbox(
                                "Status",
                                status_options,
                                index=current_status_index,
                                key=f"status_idea_{idea['id']}"
                            )
                            
                            col_btn1, col_btn2 = st.columns(2)
                            with col_btn1:
                                if st.button("💾", key=f"save_{idea['id']}", help="Atualizar status"):
                                    if update_idea_status(idea['id'], new_status):
                                        st.success("✅")
                                        st.rerun()
                            
                            with col_btn2:
                                if st.button("🗑️", key=f"delete_{idea['id']}", help="Excluir ideia"):
                                    if delete_brainstorm_idea(idea['id']):
                                        st.success("Excluído!")
                                        st.rerun()
        else:
            st.info("Nenhuma ideia encontrada com os filtros aplicados")
        
        # Exportar ideias
        if len(ideas_df) > 0:
            st.divider()
            
            # Download CSV
            csv = ideas_df.to_csv(index=False)
            st.download_button(
                label="📥 Download todas as ideias (CSV)",
                data=csv,
                file_name=f"brainstorm_{project_name}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    else:
        st.info("💡 Nenhuma ideia cadastrada ainda. Use o formulário acima para adicionar a primeira ideia!")


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

# ========================= TAB 3: PLANO DE AÇÃO (CORRIGIDO) =========================

with tab3:
    st.header("📋 Plano de Ação Detalhado")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("action_plan_form", clear_on_submit=True):
            st.subheader("Nova Ação")
            
            # Campos principais
            action_title = st.text_input("Título da Ação *")
            action_description = st.text_area("Descrição Detalhada *", height=100)
            
            col_form1, col_form2, col_form3 = st.columns(3)
            
            with col_form1:
                responsible = st.text_input("Responsável *")
                impact_level = st.selectbox(
                    "Nível de Impacto",
                    ["Baixo", "Médio", "Alto", "Crítico"],
                    index=1  # Médio como padrão
                )
            
            with col_form2:
                due_date = st.date_input(
                    "Data de Conclusão",
                    min_value=datetime.now().date(),
                    value=datetime.now().date() + timedelta(days=30)
                )
                effort_level = st.selectbox(
                    "Nível de Esforço",
                    ["Baixo", "Médio", "Alto", "Muito Alto"],
                    index=1  # Médio como padrão
                )
            
            with col_form3:
                status = st.selectbox(
                    "Status",
                    ["Não Iniciado", "Em Andamento", "Pausado", "Concluído", "Cancelado"],
                    index=0  # Não Iniciado como padrão
                )
                priority = st.number_input("Prioridade (1-10)", min_value=1, max_value=10, value=5)
            
            # Campos opcionais
            with st.expander("Campos Adicionais (Opcional)"):
                success_criteria = st.text_area("Critérios de Sucesso", height=80)
                resources_needed = st.text_area("Recursos Necessários", height=80)
            
            submitted = st.form_submit_button("➕ Adicionar Ação", type="primary")
            
            if submitted:
                if all([action_title, action_description, responsible]):
                    # Preparar dados da ação
                    action = {
                        'action_title': action_title,
                        'description': action_description,
                        'responsible': responsible,
                        'due_date': due_date.isoformat() if due_date else None,
                        'status': status,
                        'impact_level': impact_level,
                        'effort_level': effort_level,
                        'priority': priority,
                        'success_criteria': success_criteria if success_criteria else '',
                        'resources_needed': resources_needed if resources_needed else ''
                    }
                    
                    # Salvar no banco
                    if save_improvement_action(project_name, action):
                        st.success("✅ Ação adicionada com sucesso!")
                        st.balloons()
                        st.rerun()
                    else:
                        # Tentar salvar localmente como fallback
                        if 'local_actions' not in st.session_state:
                            st.session_state.local_actions = []
                        st.session_state.local_actions.append(action)
                        st.warning("⚠️ Ação salva apenas localmente")
                else:
                    st.error("❌ Preencha todos os campos obrigatórios (*)")
    
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
        
        **Status disponíveis:**
        - Não Iniciado
        - Em Andamento
        - Pausado
        - Concluído
        - Cancelado
        """)


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
