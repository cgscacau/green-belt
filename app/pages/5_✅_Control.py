import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import os
from supabase import create_client, Client
from scipy import stats

# Configuração da página
st.set_page_config(
    page_title="Control - Green Belt",
    page_icon="✅",
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

# Função para salvar plano de controle
def save_control_plan(project_name, plan_data):
    """Salva plano de controle no banco"""
    if not supabase:
        return False
    
    try:
        plan_data['project_name'] = project_name
        plan_data['created_at'] = datetime.now().isoformat()
        
        response = supabase.table('control_plans').insert(plan_data).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar plano: {str(e)}")
        return False

# Função para carregar planos de controle
def load_control_plans(project_name):
    """Carrega planos de controle do projeto"""
    if not supabase:
        return None
    
    try:
        response = supabase.table('control_plans').select("*").eq('project_name', project_name).order('created_at', desc=True).execute()
        if response.data:
            return pd.DataFrame(response.data)
        return None
    except Exception as e:
        st.error(f"Erro ao carregar planos: {str(e)}")
        return None

# Função para salvar lições aprendidas
def save_lessons_learned(project_name, lesson_data):
    """Salva lições aprendidas no banco"""
    if not supabase:
        return False
    
    try:
        lesson_data['project_name'] = project_name
        lesson_data['created_at'] = datetime.now().isoformat()
        
        response = supabase.table('lessons_learned').insert(lesson_data).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar lição: {str(e)}")
        return False

# Função para carregar lições aprendidas
def load_lessons_learned(project_name):
    """Carrega lições aprendidas do projeto"""
    if not supabase:
        return None
    
    try:
        response = supabase.table('lessons_learned').select("*").eq('project_name', project_name).order('created_at', desc=True).execute()
        if response.data:
            return pd.DataFrame(response.data)
        return None
    except Exception as e:
        st.error(f"Erro ao carregar lições: {str(e)}")
        return None

# Função para carregar dados do processo
def load_process_data(project_name):
    """Carrega dados do processo para monitoramento"""
    if not supabase:
        return None
    
    try:
        response = supabase.table('process_data').select("*").eq('project_name', project_name).order('uploaded_at', desc=True).limit(1).execute()
        
        if response.data and len(response.data) > 0:
            data_json = response.data[0].get('data', None)
            if data_json:
                if isinstance(data_json, list):
                    return pd.DataFrame(data_json)
                elif isinstance(data_json, dict):
                    return pd.DataFrame(data_json)
        return None
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return None

# Função para carregar ações de melhoria
def load_improvement_actions(project_name):
    """Carrega ações de melhoria implementadas"""
    if not supabase:
        return None
    
    try:
        response = supabase.table('improvement_actions').select("*").eq('project_name', project_name).eq('status', 'Concluído').execute()
        if response.data:
            return pd.DataFrame(response.data)
        return None
    except Exception as e:
        st.error(f"Erro ao carregar ações: {str(e)}")
        return None

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
        
        # Status do projeto
        project_data = st.session_state.get('project_data', {})
        if project_data:
            st.caption(f"**Líder:** {project_data.get('project_leader', 'N/A')}")
            st.caption(f"**Métrica:** {project_data.get('primary_metric', 'N/A')}")
            
            # Progresso
            baseline = project_data.get('baseline_value', 0)
            target = project_data.get('target_value', 0)
            
            if baseline and target:
                progress = ((baseline - target) / abs(baseline)) * 100 if baseline != 0 else 0
                st.metric("Meta de Redução", f"{abs(progress):.1f}%")

# ========================= INTERFACE PRINCIPAL =========================

st.title("✅ Control — Monitoramento e Controle Contínuo")
st.markdown("Garanta que as melhorias sejam sustentadas e monitore o desempenho do processo")

# Verificar se há projeto selecionado
if 'project_name' not in st.session_state:
    st.warning("⚠️ Nenhum projeto selecionado")
    st.info("Por favor, selecione ou crie um projeto na página Define primeiro.")
    
    if supabase:
        projects = list_projects()
        if projects:
            st.subheader("📂 Projetos Disponíveis")
            df = pd.DataFrame(projects)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.info("👈 Use a barra lateral para selecionar um projeto")
    
    if st.button("📋 Ir para Define"):
        st.switch_page("pages/1_📋_Define.py")
    st.stop()

# Projeto selecionado
project_name = st.session_state.project_name
project_data = st.session_state.get('project_data', {})

st.info(f"📁 Projeto: **{project_name}**")

# Verificar se há ações implementadas
actions_df = load_improvement_actions(project_name)

if actions_df is None or len(actions_df) == 0:
    st.warning("⚠️ Nenhuma ação concluída encontrada.")
    st.info("""
    **Para iniciar a fase Control:**
    1. Complete a implementação das ações na fase **Improve**
    2. Marque as ações como 'Concluído'
    3. Volte aqui para estabelecer controles
    """)
    
    if st.button("🔧 Ir para Improve"):
        st.switch_page("pages/4_🔧_Improve.py")
else:
    st.success(f"✅ {len(actions_df)} ações implementadas encontradas")

# Tabs principais
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Plano de Controle",
    "📊 Gráficos de Controle",
    "📈 Monitoramento",
    "📚 Lições Aprendidas",
    "📑 Documentação"
])

# ========================= TAB 1: PLANO DE CONTROLE =========================

with tab1:
    st.header("📋 Plano de Controle do Processo")
    st.markdown("Defina como o processo será monitorado e controlado")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("control_plan_form", clear_on_submit=True):
            st.subheader("Novo Item de Controle")
            
            control_item = st.text_input("Item de Controle *")
            specification = st.text_area("Especificação/Limites *", height=80)
            
            col_form1, col_form2, col_form3 = st.columns(3)
            
            with col_form1:
                measurement_method = st.selectbox(
                    "Método de Medição",
                    ["Manual", "Automático", "Inspeção Visual", "Sistema", "Auditoria"]
                )
                sample_size = st.text_input("Tamanho da Amostra", value="5")
            
            with col_form2:
                frequency = st.selectbox(
                    "Frequência",
                    ["Horária", "Por Turno", "Diária", "Semanal", "Mensal", "Por Lote"]
                )
                responsible = st.text_input("Responsável *")
            
            with col_form3:
                control_type = st.selectbox(
                    "Tipo de Controle",
                    ["Preventivo", "Detectivo", "Corretivo"]
                )
                critical_level = st.select_slider(
                    "Criticidade",
                    options=["Baixa", "Média", "Alta", "Crítica"],
                    value="Média"
                )
            
            action_plan = st.text_area(
                "Plano de Ação (se fora dos limites)",
                height=80,
                placeholder="O que fazer se o processo sair de controle?"
            )
            
            submitted = st.form_submit_button("➕ Adicionar ao Plano", type="primary")
            
            if submitted:
                if all([control_item, specification, responsible]):
                    plan = {
                        'control_item': control_item,
                        'specification': specification,
                        'measurement_method': measurement_method,
                        'sample_size': sample_size,
                        'frequency': frequency,
                        'responsible': responsible,
                        'control_type': control_type,
                        'critical_level': critical_level,
                        'action_plan': action_plan
                    }
                    
                    if save_control_plan(project_name, plan):
                        st.success("✅ Item adicionado ao plano de controle!")
                        st.rerun()
                    else:
                        st.error("Erro ao salvar")
                else:
                    st.error("Preencha os campos obrigatórios")
    
    with col2:
        st.info("""
        **📋 Elementos do Controle:**
        
        **Tipos de Controle:**
        - **Preventivo**: Evita problemas
        - **Detectivo**: Identifica desvios
        - **Corretivo**: Corrige problemas
        
        **Frequência adequada:**
        - Baseada na variabilidade
        - Custo-benefício
        - Criticidade do processo
        
        **OCAP:**
        Out of Control Action Plan
        - Ações imediatas
        - Responsáveis definidos
        - Critérios claros
        """)
    
    # Exibir plano de controle
    plans_df = load_control_plans(project_name)
    
    if plans_df is not None and len(plans_df) > 0:
        st.divider()
        st.subheader("📊 Plano de Controle Atual")
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_type = st.multiselect(
                "Tipo de Controle",
                plans_df['control_type'].unique() if 'control_type' in plans_df.columns else []
            )
        with col2:
            filter_critical = st.multiselect(
                "Criticidade",
                plans_df['critical_level'].unique() if 'critical_level' in plans_df.columns else []
            )
        with col3:
            filter_responsible = st.multiselect(
                "Responsável",
                plans_df['responsible'].unique() if 'responsible' in plans_df.columns else []
            )
        
        # Aplicar filtros
        filtered_plans = plans_df.copy()
        if filter_type:
            filtered_plans = filtered_plans[filtered_plans['control_type'].isin(filter_type)]
        if filter_critical:
            filtered_plans = filtered_plans[filtered_plans['critical_level'].isin(filter_critical)]
        if filter_responsible:
            filtered_plans = filtered_plans[filtered_plans['responsible'].isin(filter_responsible)]
        
        # Exibir tabela
        st.dataframe(
            filtered_plans[['control_item', 'specification', 'frequency', 'responsible', 'critical_level']],
            use_container_width=True,
            hide_index=True
        )
        
        # Download do plano
        csv = filtered_plans.to_csv(index=False)
        st.download_button(
            "📥 Download Plano de Controle (CSV)",
            data=csv,
            file_name=f"plano_controle_{project_name}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

# ========================= TAB 2: GRÁFICOS DE CONTROLE =========================

with tab2:
    st.header("📊 Gráficos de Controle Estatístico")
    
    # Carregar dados do processo
    process_data = load_process_data(project_name)
    
    if process_data is not None:
        numeric_cols = process_data.select_dtypes(include=[np.number]).columns.tolist()
        
        if numeric_cols:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                selected_metric = st.selectbox("Selecione a métrica:", numeric_cols)
                
                if selected_metric:
                    data = process_data[selected_metric].dropna()
                    
                    # Calcular limites de controle
                    mean = data.mean()
                    std = data.std()
                    ucl = mean + 3 * std
                    lcl = mean - 3 * std
                    usl = st.number_input("USL (Limite Superior Especificação)", value=ucl * 1.1)
                    lsl = st.number_input("LSL (Limite Inferior Especificação)", value=lcl * 0.9)
                    
                    # Criar gráfico de controle
                    fig = go.Figure()
                    
                    # Dados
                    fig.add_trace(go.Scatter(
                        x=list(range(len(data))),
                        y=data,
                        mode='lines+markers',
                        name='Medições',
                        line=dict(color='blue', width=2),
                        marker=dict(size=6)
                    ))
                    
                    # Linha média
                    fig.add_hline(y=mean, line_dash="solid", line_color="green",
                                 annotation_text=f"Média: {mean:.2f}", line_width=2)
                    
                    # Limites de controle
                    fig.add_hline(y=ucl, line_dash="dash", line_color="orange",
                                 annotation_text=f"UCL: {ucl:.2f}")
                    fig.add_hline(y=lcl, line_dash="dash", line_color="orange",
                                 annotation_text=f"LCL: {lcl:.2f}")
                    
                    # Limites de especificação
                    fig.add_hline(y=usl, line_dash="dot", line_color="red",
                                 annotation_text=f"USL: {usl:.2f}")
                    fig.add_hline(y=lsl, line_dash="dot", line_color="red",
                                 annotation_text=f"LSL: {lsl:.2f}")
                    
                    # Destacar pontos fora de controle
                    out_of_control = data[(data > ucl) | (data < lcl)]
                    if len(out_of_control) > 0:
                        fig.add_trace(go.Scatter(
                            x=[i for i, v in enumerate(data) if v in out_of_control.values],
                            y=out_of_control,
                            mode='markers',
                            name='Fora de Controle',
                            marker=dict(color='red', size=10, symbol='x')
                        ))
                    
                    fig.update_layout(
                        title=f"Gráfico de Controle - {selected_metric}",
                        xaxis_title="Observação",
                        yaxis_title=selected_metric,
                        height=500,
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Análise de capacidade
                    st.subheader("📈 Análise de Capacidade")
                    
                    cp = (usl - lsl) / (6 * std) if std > 0 else 0
                    cpu = (usl - mean) / (3 * std) if std > 0 else 0
                    cpl = (mean - lsl) / (3 * std) if std > 0 else 0
                    cpk = min(cpu, cpl)
                    
                    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                    
                    with col_m1:
                        st.metric("Cp", f"{cp:.3f}")
                    with col_m2:
                        st.metric("Cpk", f"{cpk:.3f}")
                    with col_m3:
                        points_out = len(out_of_control)
                        st.metric("Pontos Fora", points_out)
                    with col_m4:
                        control_pct = ((len(data) - points_out) / len(data) * 100)
                        st.metric("% Sob Controle", f"{control_pct:.1f}%")
                    
                    # Interpretação
                    if cpk >= 1.33:
                        st.success("✅ Processo capaz e sob controle")
                    elif cpk >= 1.0:
                        st.warning("⚠️ Processo marginalmente capaz")
                    else:
                        st.error("❌ Processo não capaz - ação necessária")
            
            with col2:
                st.info("""
                **📊 Interpretação:**
                
                **Limites de Controle:**
                - UCL/LCL: ±3σ da média
                - Variação natural do processo
                
                **Limites de Especificação:**
                - USL/LSL: Requisitos do cliente
                - Tolerância aceitável
                
                **Regras de Nelson:**
                1. 1 ponto > 3σ da média
                2. 9 pontos mesmo lado
                3. 6 pontos crescentes/decrescentes
                4. 14 pontos alternados
                
                **Capacidade:**
                - Cpk ≥ 1.33: Capaz
                - Cpk ≥ 1.0: Marginal
                - Cpk < 1.0: Não capaz
                """)
    else:
        st.warning("Nenhum dado disponível para criar gráficos de controle")
        
        # Upload de dados
        uploaded_file = st.file_uploader("Faça upload de dados para monitoramento", type=['csv'])
        
        if uploaded_file:
            try:
                data = pd.read_csv(uploaded_file)
                
                if supabase:
                    if st.button("💾 Salvar dados para monitoramento"):
                        data_json = data.to_dict('records')
                        record = {
                            'project_name': project_name,
                            'data': data_json,
                            'data_type': 'control_monitoring',
                            'collection_date': datetime.now().date().isoformat(),
                            'uploaded_at': datetime.now().isoformat()
                        }
                        
                        response = supabase.table('process_data').insert(record).execute()
                        st.success("✅ Dados salvos!")
                        st.rerun()
            except Exception as e:
                st.error(f"Erro: {str(e)}")

# ========================= TAB 3: MONITORAMENTO =========================

with tab3:
    st.header("📈 Dashboard de Monitoramento")
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    baseline = project_data.get('baseline_value', 100)
    target = project_data.get('target_value', 80)
    current = baseline * 0.85  # Simulado - substituir por valor real
    
    with col1:
        st.metric(
            "Baseline",
            f"{baseline:.1f}",
            help="Valor inicial antes das melhorias"
        )
    
    with col2:
        st.metric(
            "Meta",
            f"{target:.1f}",
            f"{target - baseline:.1f}",
            help="Objetivo do projeto"
        )
    
    with col3:
        st.metric(
            "Atual",
            f"{current:.1f}",
            f"{current - baseline:.1f}",
            help="Valor atual do processo"
        )
    
    with col4:
        achievement = ((baseline - current) / (baseline - target) * 100) if baseline != target else 0
        st.metric(
            "Realização",
            f"{achievement:.0f}%",
            help="Percentual da meta atingido"
        )
    
    st.divider()
    
    # Tendência ao longo do tempo
    st.subheader("📊 Tendência de Desempenho")
    
    # Simular dados de tendência (substituir por dados reais)
    days = 90
    dates = pd.date_range(end=datetime.now(), periods=days)
    
    # Simular melhoria gradual
    np.random.seed(42)
    values = []
    current_val = baseline
    
    for i in range(days):
        if i < 30:  # Fase de implementação
            current_val = baseline
        elif i < 60:  # Fase de melhoria
            current_val -= (baseline - target) * 0.02
        else:  # Fase de estabilização
            current_val = target * (1 + np.random.normal(0, 0.02))
        
        values.append(current_val + np.random.normal(0, current_val * 0.05))
    
    trend_df = pd.DataFrame({
        'Data': dates,
        'Valor': values
    })
    
    # Criar gráfico de tendência
    fig = go.Figure()
    
    # Linha de tendência
    fig.add_trace(go.Scatter(
        x=trend_df['Data'],
        y=trend_df['Valor'],
        mode='lines',
        name='Desempenho',
        line=dict(color='blue', width=2)
    ))
    
    # Linha de meta
    fig.add_hline(y=target, line_dash="dash", line_color="green",
                 annotation_text=f"Meta: {target:.0f}")
    
    # Linha baseline
    fig.add_hline(y=baseline, line_dash="dash", line_color="red",
                 annotation_text=f"Baseline: {baseline:.0f}")
    
    # Adicionar fases
    fig.add_vrect(x0=dates[0], x1=dates[30],
                  fillcolor="red", opacity=0.1,
                  annotation_text="Implementação")
    fig.add_vrect(x0=dates[30], x1=dates[60],
                  fillcolor="yellow", opacity=0.1,
                  annotation_text="Melhoria")
    fig.add_vrect(x0=dates[60], x1=dates[-1],
                  fillcolor="green", opacity=0.1,
                  annotation_text="Controle")
    
    fig.update_layout(
        title="Evolução do Indicador Principal",
        xaxis_title="Data",
        yaxis_title=project_data.get('primary_metric', 'Métrica'),
        height=400,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Alertas e notificações
    st.divider()
    st.subheader("🚨 Alertas e Ações")
    
    # Verificar pontos fora de controle
    recent_values = values[-10:]
    out_of_control_count = sum(1 for v in recent_values if v > target * 1.1 or v < target * 0.9)
    
    if out_of_control_count > 0:
        st.error(f"⚠️ {out_of_control_count} pontos fora de controle nos últimos 10 dias")
        
        with st.expander("Ver Plano de Ação"):
            st.write("""
            **Ações Imediatas:**
            1. Verificar mudanças no processo
            2. Revisar procedimentos operacionais
            3. Treinar operadores se necessário
            4. Ajustar parâmetros do processo
            5. Aumentar frequência de monitoramento
            """)
    else:
        st.success("✅ Processo sob controle estatístico")

# ========================= TAB 4: LIÇÕES APRENDIDAS =========================

with tab4:
    st.header("📚 Lições Aprendidas")
    st.markdown("Documente os aprendizados para projetos futuros")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("lessons_form", clear_on_submit=True):
            st.subheader("Nova Lição Aprendida")
            
            lesson_type = st.selectbox(
                "Tipo de Lição",
                ["Sucesso", "Desafio", "Melhoria", "Erro a Evitar", "Boa Prática"]
            )
            
            description = st.text_area(
                "Descrição da Lição *",
                height=100,
                placeholder="O que foi aprendido?"
            )
            
            context = st.text_area(
                "Contexto",
                height=80,
                placeholder="Em que situação isso ocorreu?"
            )
            
            recommendations = st.text_area(
                "Recomendações *",
                height=80,
                placeholder="O que fazer em projetos futuros?"
            )
            
            impact = st.select_slider(
                "Impacto no Projeto",
                options=["Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"],
                value="Médio"
            )
            
            submitted = st.form_submit_button("💾 Salvar Lição", type="primary")
            
            if submitted:
                if description and recommendations:
                    lesson = {
                        'lesson_type': lesson_type,
                        'description': description,
                        'context': context,
                        'recommendations': recommendations,
                        'impact': impact
                    }
                    
                    if save_lessons_learned(project_name, lesson):
                        st.success("✅ Lição aprendida documentada!")
                        st.rerun()
                else:
                    st.error("Preencha os campos obrigatórios")
    
    with col2:
        st.info("""
        **📚 Importância das Lições:**
        
        **Benefícios:**
        - Evitar repetir erros
        - Replicar sucessos
        - Acelerar futuros projetos
        - Construir conhecimento
        
        **Elementos-chave:**
        - Situação específica
        - Ação tomada
        - Resultado obtido
        - Recomendação clara
        
        **Compartilhamento:**
        - Equipe do projeto
        - Outros Green Belts
        - Gestão
        """)
    
    # Exibir lições aprendidas
    lessons_df = load_lessons_learned(project_name)
    
    if lessons_df is not None and len(lessons_df) > 0:
        st.divider()
        st.subheader("📖 Lições Documentadas")
        
        # Filtro por tipo
        lesson_types = lessons_df['lesson_type'].unique() if 'lesson_type' in lessons_df.columns else []
        selected_types = st.multiselect("Filtrar por tipo:", lesson_types, default=lesson_types)
        
        if selected_types:
            filtered_lessons = lessons_df[lessons_df['lesson_type'].isin(selected_types)]
        else:
            filtered_lessons = lessons_df
        
        # Exibir lições
        for idx, lesson in filtered_lessons.iterrows():
            icon = {
                "Sucesso": "✅",
                "Desafio": "⚠️",
                "Melhoria": "💡",
                "Erro a Evitar": "❌",
                "Boa Prática": "⭐"
            }.get(lesson.get('lesson_type', ''), "📝")
            
            with st.expander(f"{icon} {lesson.get('lesson_type', 'Lição')} - {lesson.get('impact', 'N/A')} Impacto"):
                st.write(f"**Descrição:** {lesson.get('description', '')}")
                if lesson.get('context'):
                    st.write(f"**Contexto:** {lesson['context']}")
                st.write(f"**Recomendações:** {lesson.get('recommendations', '')}")
                
                if 'created_at' in lesson:
                    st.caption(f"Documentado em: {pd.to_datetime(lesson['created_at']).strftime('%d/%m/%Y')}")

# ========================= TAB 5: DOCUMENTAÇÃO (CORRIGIDA) =========================

with tab5:
    st.header("📑 Documentação Final do Projeto")
    
    st.info("Compile toda a documentação do projeto para referência futura")
    
    # Resumo executivo
    st.subheader("📊 Resumo Executivo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Informações do Projeto:**")
        st.write(f"- **Nome:** {project_name}")
        st.write(f"- **Líder:** {project_data.get('project_leader', 'N/A')}")
        st.write(f"- **Sponsor:** {project_data.get('project_sponsor', 'N/A')}")
        st.write(f"- **Início:** {project_data.get('start_date', 'N/A')}")
        st.write(f"- **Término:** {project_data.get('end_date', 'N/A')}")
    
    with col2:
        st.write("**Resultados:**")
        st.write(f"- **Baseline:** {baseline:.1f}")
        st.write(f"- **Meta:** {target:.1f}")
        st.write(f"- **Atual:** {current:.1f}")
        st.write(f"- **Melhoria:** {((baseline - current)/baseline*100):.1f}%")
        
        if project_data.get('expected_savings'):
            st.write(f"- **Economia:** R$ {project_data['expected_savings']:,.2f}")
    
    st.divider()
    
    # Gerar relatório
    st.subheader("📄 Gerar Relatório Final")
    
    report_format = st.selectbox(
        "Formato do Relatório",
        ["CSV (Simples)", "Excel (Múltiplas Abas)", "JSON (Dados Completos)"]
    )
    
    include_sections = st.multiselect(
        "Seções a incluir:",
        ["Resumo Executivo", "Project Charter", "Análises Realizadas", 
         "Ações Implementadas", "Plano de Controle", "Lições Aprendidas"],
        default=["Resumo Executivo", "Plano de Controle", "Lições Aprendidas"]
    )
    
    if st.button("📥 Gerar Relatório", type="primary"):
        try:
            if report_format == "CSV (Simples)":
                # Criar CSV consolidado
                report_data = []
                
                # Adicionar resumo
                report_data.append(['=== RESUMO EXECUTIVO ==='])
                report_data.append(['Projeto', project_name])
                report_data.append(['Líder', project_data.get('project_leader', 'N/A')])
                report_data.append(['Baseline', baseline])
                report_data.append(['Meta', target])
                report_data.append(['Atual', current])
                report_data.append(['Melhoria (%)', f"{((baseline-current)/baseline*100):.1f}"])
                report_data.append([])
                
                # Adicionar plano de controle se existir
                if "Plano de Controle" in include_sections and plans_df is not None and len(plans_df) > 0:
                    report_data.append(['=== PLANO DE CONTROLE ==='])
                    report_data.append(plans_df.columns.tolist())
                    for _, row in plans_df.iterrows():
                        report_data.append(row.tolist())
                    report_data.append([])
                
                # Adicionar lições aprendidas se existir
                if "Lições Aprendidas" in include_sections and lessons_df is not None and len(lessons_df) > 0:
                    report_data.append(['=== LIÇÕES APRENDIDAS ==='])
                    report_data.append(lessons_df.columns.tolist())
                    for _, row in lessons_df.iterrows():
                        report_data.append(row.tolist())
                
                # Converter para CSV
                import csv
                from io import StringIO
                
                output = StringIO()
                writer = csv.writer(output)
                writer.writerows(report_data)
                
                # Download
                st.download_button(
                    label="📥 Download Relatório CSV",
                    data=output.getvalue(),
                    file_name=f"relatorio_{project_name}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
                
                st.success("✅ Relatório CSV gerado com sucesso!")
            
            elif report_format == "Excel (Múltiplas Abas)":
                # Tentar usar openpyxl ou método alternativo
                try:
                    from io import BytesIO
                    import pandas as pd
                    
                    output = BytesIO()
                    
                    # Criar writer com engine openpyxl
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        # Resumo
                        summary_data = pd.DataFrame({
                            'Item': ['Projeto', 'Líder', 'Baseline', 'Meta', 'Atual', 'Melhoria (%)'],
                            'Valor': [
                                project_name, 
                                project_data.get('project_leader', 'N/A'), 
                                baseline, 
                                target, 
                                current, 
                                f"{((baseline-current)/baseline*100):.1f}"
                            ]
                        })
                        summary_data.to_excel(writer, sheet_name='Resumo', index=False)
                        
                        # Plano de Controle
                        if "Plano de Controle" in include_sections and plans_df is not None and len(plans_df) > 0:
                            plans_df.to_excel(writer, sheet_name='Plano de Controle', index=False)
                        
                        # Lições Aprendidas
                        if "Lições Aprendidas" in include_sections and lessons_df is not None and len(lessons_df) > 0:
                            lessons_df.to_excel(writer, sheet_name='Lições Aprendidas', index=False)
                        
                        # Ações Implementadas
                        if "Ações Implementadas" in include_sections and actions_df is not None and len(actions_df) > 0:
                            actions_df.to_excel(writer, sheet_name='Ações', index=False)
                    
                    # Download
                    st.download_button(
                        label="📥 Download Relatório Excel",
                        data=output.getvalue(),
                        file_name=f"relatorio_{project_name}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                    st.success("✅ Relatório Excel gerado com sucesso!")
                    
                except ImportError:
                    st.error("""
                    ❌ Biblioteca Excel não disponível.
                    
                    Para habilitar exportação Excel, adicione ao requirements.txt:
                    - openpyxl>=3.1.0
                    - ou xlsxwriter>=3.1.0
                    
                    Enquanto isso, use a opção CSV ou JSON.
                    """)
                except Exception as e:
                    st.error(f"Erro ao gerar Excel: {str(e)}")
                    st.info("Tente usar o formato CSV ou JSON como alternativa.")
            
            elif report_format == "JSON (Dados Completos)":
                # Criar JSON com todos os dados
                import json
                
                report_json = {
                    "project_info": {
                        "name": project_name,
                        "leader": project_data.get('project_leader', 'N/A'),
                        "sponsor": project_data.get('project_sponsor', 'N/A'),
                        "start_date": project_data.get('start_date', 'N/A'),
                        "end_date": project_data.get('end_date', 'N/A')
                    },
                    "results": {
                        "baseline": baseline,
                        "target": target,
                        "current": current,
                        "improvement_percentage": ((baseline-current)/baseline*100),
                        "expected_savings": project_data.get('expected_savings', 0)
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
                # Adicionar seções selecionadas
                if "Plano de Controle" in include_sections and plans_df is not None:
                    report_json["control_plans"] = plans_df.to_dict('records')
                
                if "Lições Aprendidas" in include_sections and lessons_df is not None:
                    report_json["lessons_learned"] = lessons_df.to_dict('records')
                
                if "Ações Implementadas" in include_sections and actions_df is not None:
                    report_json["implemented_actions"] = actions_df.to_dict('records')
                
                # Download
                st.download_button(
                    label="📥 Download Relatório JSON",
                    data=json.dumps(report_json, indent=2, ensure_ascii=False, default=str),
                    file_name=f"relatorio_{project_name}_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
                
                st.success("✅ Relatório JSON gerado com sucesso!")
                
        except Exception as e:
            st.error(f"Erro ao gerar relatório: {str(e)}")
            st.info("Verifique se todos os dados necessários estão disponíveis.")
    
    # Prévia do relatório
    st.divider()
    st.subheader("👁️ Prévia do Relatório")
    
    with st.expander("Ver estrutura do relatório"):
        st.write("""
        **Estrutura do Relatório Final:**
        
        1. **Capa**
           - Nome do projeto
           - Equipe
           - Período
        
        2. **Resumo Executivo**
           - Problema inicial
           - Solução implementada
           - Resultados alcançados
           - Benefícios financeiros
        
        3. **Metodologia DMAIC**
           - Define: Charter e escopo
           - Measure: Baseline e sistema de medição
           - Analyze: Causas raiz identificadas
           - Improve: Ações implementadas
           - Control: Plano de sustentação
        
        4. **Resultados e Métricas**
           - Indicadores antes/depois
           - Gráficos de tendência
           - Análise de capacidade
        
        5. **Plano de Controle**
           - Itens críticos
           - Frequência de monitoramento
           - Responsáveis
        
        6. **Lições Aprendidas**
           - Sucessos
           - Desafios
           - Recomendações
        
        7. **Anexos**
           - Dados detalhados
           - Análises estatísticas
           - Documentação de suporte
        """)


# Footer
st.divider()
st.caption("💡 **Dica:** A fase Control garante a sustentabilidade das melhorias. Mantenha o monitoramento contínuo!")
