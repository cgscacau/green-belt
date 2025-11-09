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
    
    if st.button("🛠️ Ir para Improve"):
        st.switch_page("pages/4_🛠️_Improve.py")
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

# ========================= TAB 5: DOCUMENTAÇÃO COMPLETA (VERSÃO PREMIUM) =========================

with tab5:
    st.header("📑 Documentação Final do Projeto")
    
    # Função para gerar relatório HTML COMPLETO E PROFISSIONAL
    def generate_premium_html_report(project_name):
        """Gera relatório HTML premium com TODAS as análises salvas"""
        
        # ==================== BUSCAR TODOS OS DADOS ====================
        project_info = load_project_from_db(project_name)
        
        # Inicializar variáveis
        voc_items = None
        sipoc_data = None
        measurements = None
        all_analyses = {}
        actions = None
        control_plans = load_control_plans(project_name)
        lessons = load_lessons_learned(project_name)
        brainstorm_ideas = None
        
        if supabase:
            try:
                # VOC Items
                voc_response = supabase.table('voc_items').select("*").eq('project_name', project_name).execute()
                if voc_response.data:
                    voc_items = pd.DataFrame(voc_response.data)
                
                # SIPOC
                sipoc_response = supabase.table('sipoc').select("*").eq('project_name', project_name).execute()
                if sipoc_response.data and len(sipoc_response.data) > 0:
                    sipoc_data = sipoc_response.data[0]
                
                # Measurements
                meas_response = supabase.table('measurements').select("*").eq('project_name', project_name).execute()
                if meas_response.data:
                    measurements = pd.DataFrame(meas_response.data)
                
                # TODAS AS ANÁLISES (organizar por tipo)
                analyses_response = supabase.table('analyses').select("*").eq('project_name', project_name).execute()
                if analyses_response.data:
                    for analysis in analyses_response.data:
                        analysis_type = analysis.get('analysis_type', 'unknown')
                        if analysis_type not in all_analyses:
                            all_analyses[analysis_type] = []
                        all_analyses[analysis_type].append(analysis)
                
                # Actions
                actions_response = supabase.table('improvement_actions').select("*").eq('project_name', project_name).execute()
                if actions_response.data:
                    actions = pd.DataFrame(actions_response.data)
                
                # Brainstorm Ideas
                ideas_response = supabase.table('brainstorm_ideas').select("*").eq('project_name', project_name).execute()
                if ideas_response.data:
                    brainstorm_ideas = pd.DataFrame(ideas_response.data)
                    
            except Exception as e:
                st.error(f"Erro ao buscar dados: {str(e)}")
        
        # ==================== CALCULAR MÉTRICAS ====================
        baseline = project_info.get('baseline_value', 100) if project_info else 100
        target = project_info.get('target_value', 80) if project_info else 80
        
        # Calcular valor atual a partir das medições
        if measurements is not None and len(measurements) > 0:
            current = measurements['metric_value'].iloc[-1]
        else:
            current = baseline * 0.85  # Simulado
        
        improvement = ((baseline - current) / baseline * 100) if baseline != 0 else 0
        achievement = ((baseline - current) / (baseline - target) * 100) if baseline != target else 0
        
        # ==================== GERAR GRÁFICOS ====================
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        # 1. GRÁFICO DE PROGRESSO (GAUGE)
        fig_progress = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = achievement,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Progresso da Meta (%)", 'font': {'size': 24}},
            delta = {'reference': 100, 'increasing': {'color': "green"}},
            gauge = {
                'axis': {'range': [None, 120], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "darkgreen" if achievement >= 90 else "orange" if achievement >= 50 else "red"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 50], 'color': '#ffcccc'},
                    {'range': [50, 90], 'color': '#ffffcc'},
                    {'range': [90, 120], 'color': '#ccffcc'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 100
                }
            }
        ))
        fig_progress.update_layout(height=400, font={'size': 16})
        progress_html = fig_progress.to_html(include_plotlyjs='cdn', div_id="progress-chart")
        
        # 2. GRÁFICO DE TENDÊNCIA
        if measurements is not None and len(measurements) > 0:
            fig_trend = go.Figure()
            
            # Linha de medições
            fig_trend.add_trace(go.Scatter(
                x=pd.to_datetime(measurements['measurement_date']),
                y=measurements['metric_value'],
                mode='lines+markers',
                name='Medições',
                line=dict(color='#3498db', width=3),
                marker=dict(size=8)
            ))
            
            # Linhas de referência
            fig_trend.add_hline(y=target, line_dash="dash", line_color="green", 
                               annotation_text=f"Meta: {target}", line_width=2)
            fig_trend.add_hline(y=baseline, line_dash="dash", line_color="red", 
                               annotation_text=f"Baseline: {baseline}", line_width=2)
            
            # Área de melhoria
            fig_trend.add_hrect(y0=target, y1=baseline, fillcolor="yellow", opacity=0.1, 
                               annotation_text="Zona de Melhoria", annotation_position="top left")
            
            fig_trend.update_layout(
                title="Evolução do Indicador ao Longo do Tempo",
                xaxis_title="Data",
                yaxis_title=project_info.get('primary_metric', 'Métrica') if project_info else 'Métrica',
                height=500,
                hovermode='x unified'
            )
            trend_html = fig_trend.to_html(include_plotlyjs=False, div_id="trend-chart")
        else:
            trend_html = "<p class='warning'>Dados de tendência não disponíveis</p>"
        
        # 3. DASHBOARD DE ANÁLISES (quantas análises de cada tipo)
        analysis_summary = {k: len(v) for k, v in all_analyses.items()}
        
        if analysis_summary:
            fig_analyses = go.Figure(data=[
                go.Bar(
                    x=list(analysis_summary.keys()),
                    y=list(analysis_summary.values()),
                    marker_color=['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#34495e'][:len(analysis_summary)],
                    text=list(analysis_summary.values()),
                    textposition='auto',
                )
            ])
            fig_analyses.update_layout(
                title="Análises Realizadas por Tipo",
                xaxis_title="Tipo de Análise",
                yaxis_title="Quantidade",
                height=400
            )
            analyses_dashboard_html = fig_analyses.to_html(include_plotlyjs=False, div_id="analyses-dashboard")
        else:
            analyses_dashboard_html = ""
        
        # 4. GRÁFICO DE PARETO (se existir)
        pareto_html = ""
        if 'pareto' in all_analyses:
            try:
                pareto_data = all_analyses['pareto'][0].get('results') or all_analyses['pareto'][0].get('data')
                # DEPOIS (código corrigido):
                if pareto_data and 'data' in pareto_data:
                    df_pareto = pd.DataFrame(pareto_data['data'])
                    
                    # CORREÇÃO 1: Ordenar por frequência/valor decrescente
                    freq_col = 'Frequência' if 'Frequência' in df_pareto.columns else 'Valor'
                    df_pareto = df_pareto.sort_values(by=freq_col, ascending=False)
                    
                    # Recalcular acumulado após ordenação
                    df_pareto['Acumulado'] = (df_pareto[freq_col].cumsum() / df_pareto[freq_col].sum() * 100)
                    
                    fig_pareto = make_subplots(specs=[[{"secondary_y": True}]])

                    
                    fig_pareto.add_trace(
                        go.Bar(x=df_pareto.get('Categoria', []), 
                              y=df_pareto.get('Frequência', df_pareto.get('Valor', [])),
                              name='Frequência',
                              marker_color='lightblue'),
                        secondary_y=False
                    )
                    
                    if 'Acumulado' in df_pareto.columns:
                        fig_pareto.add_trace(
                            go.Scatter(x=df_pareto.get('Categoria', []), 
                                      y=df_pareto['Acumulado'],
                                      name='% Acumulado',
                                      line=dict(color='red', width=3),
                                      mode='lines+markers'),
                            secondary_y=True
                        )
                    
                    fig_pareto.update_layout(title="Análise de Pareto - Principais Causas", height=500)
                    fig_pareto.update_yaxes(title_text="Frequência", secondary_y=False)
                    fig_pareto.update_yaxes(title_text="% Acumulado", range=[0, 100], secondary_y=True)
                    
                    pareto_html = fig_pareto.to_html(include_plotlyjs=False, div_id="pareto-chart")
            except:
                pass
        
        # 5. GRÁFICO DE REGRESSÃO (se existir)
        regression_html = ""
        if 'regression' in all_analyses:
            try:
                reg_data = all_analyses['regression'][0].get('results') or all_analyses['regression'][0].get('data')
                if reg_data:
                    fig_reg = go.Figure()
                    
                    # Scatter plot
                    fig_reg.add_trace(go.Scatter(
                        x=reg_data['x_values'],
                        y=reg_data['y_values'],
                        mode='markers',
                        name='Dados',
                        marker=dict(size=8, color='blue', opacity=0.6)
                    ))
                    
                    # Linha de regressão
                    fig_reg.add_trace(go.Scatter(
                        x=reg_data['x_values'],
                        y=reg_data['y_pred'],
                        mode='lines',
                        name='Regressão',
                        line=dict(color='red', width=3)
                    ))
                    
                    fig_reg.update_layout(
                        title=f"Regressão Linear: {reg_data.get('y_var', 'Y')} vs {reg_data.get('x_var', 'X')}",
                        xaxis_title=reg_data.get('x_var', 'X'),
                        yaxis_title=reg_data.get('y_var', 'Y'),
                        height=500
                    )
                    
                    regression_html = f"""
                    <div class="chart-container">
                        {fig_reg.to_html(include_plotlyjs=False, div_id="regression-chart")}
                        <div class="info">
                            <strong>Equação:</strong> {reg_data.get('equation', 'N/A')}<br>
                            <strong>R²:</strong> {reg_data.get('r2', 0):.4f} | 
                            <strong>RMSE:</strong> {reg_data.get('rmse', 0):.4f}
                        </div>
                    </div>
                    """
            except:
                pass
        
        # 6. GRÁFICO ISHIKAWA (Resumo visual)
        ishikawa_html = ""
        if '5_whys' in all_analyses or 'ishikawa' in all_analyses:
            analysis_key = '5_whys' if '5_whys' in all_analyses else 'ishikawa'
            try:
                ishikawa_data = all_analyses[analysis_key][0].get('results') or all_analyses[analysis_key][0].get('data')
                if ishikawa_data:
                    ishikawa_html = f"""
                    <div class="section-ishikawa">
                        <h3>🐟 Análise de Causa Raiz (Ishikawa / 5 Porquês)</h3>
                        <div class="ishikawa-summary">
                            <p><strong>Problema:</strong> {ishikawa_data.get('problem', 'N/A')}</p>
                            <p><strong>Causa Raiz Identificada:</strong> {ishikawa_data.get('root_cause', 'N/A')}</p>
                        </div>
                    </div>
                    """
            except:
                pass
        
        # 7. GRÁFICO FMEA (Top riscos)
        fmea_html = ""
        if 'fmea' in all_analyses:
            try:
                fmea_data = all_analyses['fmea'][0].get('results') or all_analyses['fmea'][0].get('data')
                if fmea_data and 'fmea_items' in fmea_data:
                    fmea_items = fmea_data['fmea_items']
                    df_fmea = pd.DataFrame(fmea_items)
                    df_fmea_top = df_fmea.nlargest(10, 'rpn')
                    
                    # DEPOIS (código corrigido):
                    # CORREÇÃO 2: Quebrar texto longo e aumentar altura
                    df_fmea_top['process_short'] = df_fmea_top['process_step'].apply(
                        lambda x: '<br>'.join(textwrap.wrap(str(x), width=15)) if len(str(x)) > 15 else str(x)
                    )
                    
                    fig_fmea = go.Figure(data=[
                        go.Bar(
                            x=df_fmea_top['process_short'],
                            y=df_fmea_top['rpn'],
                            marker_color=['red' if r >= 100 else 'orange' if r >= 50 else 'green' for r in df_fmea_top['rpn']],
                            text=df_fmea_top['rpn'],
                            textposition='auto',
                            hovertemplate='<b>%{x}</b><br>RPN: %{y}<extra></extra>'
                        )
                    ])
                    fig_fmea.update_layout(
                        title="FMEA - Top 10 Riscos por RPN",
                        xaxis_title="Processo",
                        yaxis_title="RPN",
                        height=500,  # Aumentado de 400 para 500
                        xaxis={'tickangle': -45},  # Rotacionar labels para melhor leitura
                        margin=dict(b=150)  # Mais margem embaixo para os textos
                    )

                    fmea_html = fig_fmea.to_html(include_plotlyjs=False, div_id="fmea-chart")
            except:
                pass
        
        # ==================== TEMPLATE HTML PREMIUM ====================
        html_template = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Relatório Green Belt Premium - {project_name}</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
                
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Inter', 'Segoe UI', sans-serif;
                    line-height: 1.6;
                    color: #2c3e50;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 20px;
                }}
                
                .container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 20px;
                    box-shadow: 0 25px 70px rgba(0,0,0,0.4);
                    overflow: hidden;
                }}
                
                header {{
                    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                    color: white;
                    padding: 60px 40px;
                    text-align: center;
                    position: relative;
                    overflow: hidden;
                }}
                
                header::before {{
                    content: '';
                    position: absolute;
                    top: -50%;
                    left: -50%;
                    width: 200%;
                    height: 200%;
                    background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
                    animation: pulse 15s ease-in-out infinite;
                }}
                
                @keyframes pulse {{
                    0%, 100% {{ transform: scale(1); }}
                    50% {{ transform: scale(1.1); }}
                }}
                
                h1 {{
                    font-size: 3em;
                    margin-bottom: 15px;
                    text-shadow: 2px 2px 8px rgba(0,0,0,0.3);
                    font-weight: 700;
                    position: relative;
                    z-index: 1;
                }}
                
                .subtitle {{
                    font-size: 1.4em;
                    opacity: 0.95;
                    font-weight: 300;
                    position: relative;
                    z-index: 1;
                }}
                
                .header-meta {{
                    margin-top: 30px;
                    display: flex;
                    justify-content: center;
                    gap: 40px;
                    flex-wrap: wrap;
                    position: relative;
                    z-index: 1;
                }}
                
                .header-meta span {{
                    background: rgba(255,255,255,0.2);
                    padding: 10px 20px;
                    border-radius: 25px;
                    backdrop-filter: blur(10px);
                }}
                
                .content {{
                    padding: 50px;
                }}
                
                .section {{
                    margin-bottom: 50px;
                    padding: 35px;
                    background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
                    border-radius: 15px;
                    border-left: 6px solid #3498db;
                    box-shadow: 0 5px 20px rgba(0,0,0,0.08);
                    transition: transform 0.3s, box-shadow 0.3s;
                }}
                
                .section:hover {{
                    transform: translateY(-5px);
                    box-shadow: 0 10px 30px rgba(0,0,0,0.15);
                }}
                
                h2 {{
                    color: #1e3c72;
                    margin-bottom: 25px;
                    padding-bottom: 15px;
                    border-bottom: 3px solid #3498db;
                    font-size: 2em;
                    font-weight: 700;
                }}
                
                h3 {{
                    color: #2c3e50;
                    margin: 30px 0 20px 0;
                    font-size: 1.5em;
                    font-weight: 600;
                }}
                
                .metrics {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                    gap: 25px;
                    margin: 30px 0;
                }}
                
                .metric-card {{
                    background: white;
                    padding: 25px;
                    border-radius: 15px;
                    box-shadow: 0 8px 20px rgba(0,0,0,0.1);
                    text-align: center;
                    transition: transform 0.3s, box-shadow 0.3s;
                    border-top: 4px solid #3498db;
                }}
                
                .metric-card:hover {{
                    transform: translateY(-8px) scale(1.02);
                    box-shadow: 0 15px 35px rgba(0,0,0,0.2);
                }}
                
                .metric-value {{
                    font-size: 2.5em;
                    font-weight: 700;
                    color: #3498db;
                    margin: 15px 0;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
                }}
                
                .metric-label {{
                    color: #7f8c8d;
                    font-size: 0.95em;
                    text-transform: uppercase;
                    letter-spacing: 1.5px;
                    font-weight: 600;
                }}
                
                .chart-container {{
                    margin: 35px 0;
                    padding: 25px;
                    background: white;
                    border-radius: 15px;
                    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
                }}
                
                table {{
                    width: 100%;
                    border-collapse: separate;
                    border-spacing: 0;
                    margin: 25px 0;
                    background: white;
                    border-radius: 12px;
                    overflow: hidden;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                }}
                
                th {{
                    background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
                    color: white;
                    padding: 15px;
                    text-align: left;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    font-size: 0.9em;
                }}
                
                td {{
                    padding: 15px;
                    border-bottom: 1px solid #ecf0f1;
                }}
                
                tr:hover {{
                    background: #f8f9fa;
                }}
                
                tr:last-child td {{
                    border-bottom: none;
                }}
                
                .success {{
                    background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
                    color: #155724;
                    padding: 20px;
                    border-radius: 10px;
                    border-left: 6px solid #28a745;
                    margin: 25px 0;
                    box-shadow: 0 3px 10px rgba(40, 167, 69, 0.2);
                }}
                
                .warning {{
                    background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
                    color: #856404;
                    padding: 20px;
                    border-radius: 10px;
                    border-left: 6px solid #ffc107;
                    margin: 25px 0;
                    box-shadow: 0 3px 10px rgba(255, 193, 7, 0.2);
                }}
                
                .info {{
                    background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
                    color: #0c5460;
                    padding: 20px;
                    border-radius: 10px;
                    border-left: 6px solid #17a2b8;
                    margin: 25px 0;
                    box-shadow: 0 3px 10px rgba(23, 162, 184, 0.2);
                }}
                
                .timeline {{
                    position: relative;
                    padding: 25px 0;
                }}
                
                .timeline-item {{
                    padding: 25px 35px;
                    background: white;
                    border-radius: 12px;
                    margin-bottom: 25px;
                    border-left: 4px solid #3498db;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                    transition: transform 0.3s;
                }}
                
                .timeline-item:hover {{
                    transform: translateX(10px);
                    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
                }}
                
                .badge {{
                    display: inline-block;
                    padding: 6px 14px;
                    border-radius: 25px;
                    font-size: 0.85em;
                    font-weight: 600;
                    margin-right: 10px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                
                .badge-success {{ background: #28a745; color: white; }}
                .badge-warning {{ background: #ffc107; color: #333; }}
                .badge-info {{ background: #17a2b8; color: white; }}
                .badge-danger {{ background: #dc3545; color: white; }}
                
                footer {{
                    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
                    color: white;
                    text-align: center;
                    padding: 30px;
                    margin-top: 50px;
                }}
                
                .dashboard-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                    gap: 30px;
                    margin: 30px 0;
                }}
                
                @media print {{
                    body {{ background: white; padding: 0; }}
                    .container {{ box-shadow: none; }}
                    .section {{ page-break-inside: avoid; }}
                    .metric-card {{ box-shadow: none; border: 1px solid #ddd; }}
                }}
                
                @media (max-width: 768px) {{
                    .metrics {{ grid-template-columns: 1fr; }}
                    .dashboard-grid {{ grid-template-columns: 1fr; }}
                    h1 {{ font-size: 2em; }}
                    .content {{ padding: 25px; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>🏆 Relatório Final - Projeto Green Belt</h1>
                    <div class="subtitle">{project_name}</div>
                    <div class="header-meta">
                        <span>📅 {datetime.now().strftime('%d/%m/%Y')}</span>
                        <span>👤 {project_info.get('project_leader', 'N/A') if project_info else 'N/A'}</span>
                        <span>🏢 {project_info.get('project_sponsor', 'N/A') if project_info else 'N/A'}</span>
                        <span>📊 {len(all_analyses)} Análises Realizadas</span>
                    </div>
                </header>
                
                <div class="content">

                    <!-- ==================== RESUMO EXECUTIVO ==================== -->
                    <div class="section">
                        <h2>📊 Resumo Executivo</h2>
                        
                        <div class="metrics">
                            <div class="metric-card">
                                <div class="metric-label">Baseline</div>
                                <div class="metric-value">{baseline:.1f}</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-label">Meta</div>
                                <div class="metric-value">{target:.1f}</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-label">Valor Atual</div>
                                <div class="metric-value">{current:.1f}</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-label">Melhoria</div>
                                <div class="metric-value">{improvement:.1f}%</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-label">Economia</div>
                                <div class="metric-value">R$ {project_info.get('expected_savings', 0):,.0f}</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-label">Progresso</div>
                                <div class="metric-value">{achievement:.0f}%</div>
                            </div>
                        </div>
                        
                        <div class="chart-container">
                            {progress_html}
                        </div>
                        
                        <div class="{'success' if achievement >= 90 else 'warning' if achievement >= 50 else 'info'}">
                            <h3>🎯 Status do Projeto</h3>
                            <p>
                                O projeto <strong>{project_name}</strong> 
                                {'<strong>ATINGIU</strong>' if achievement >= 90 else '<strong>está progredindo</strong> em direção à'} 
                                sua meta de {'reduzir' if baseline > target else 'aumentar'} 
                                o indicador de <strong>{baseline:.1f}</strong> para <strong>{target:.1f}</strong>.
                            </p>
                            <p style="margin-top: 15px;">
                                <strong>Resultado alcançado:</strong> {current:.1f} 
                                (melhoria de <strong>{improvement:.1f}%</strong> em relação ao baseline)
                            </p>
                            {f'<p style="margin-top: 10px;"><strong>💰 Economia realizada:</strong> R$ {project_info.get("expected_savings", 0):,.2f}</p>' if project_info and project_info.get("expected_savings") else ''}
                        </div>
                    </div>
                    
                    <!-- ==================== DASHBOARD DE ANÁLISES ==================== -->
                    {f'''
                    <div class="section">
                        <h2>📈 Dashboard de Análises Realizadas</h2>
                        <div class="chart-container">
                            {analyses_dashboard_html}
                        </div>
                        
                        <div class="info">
                            <strong>Total de análises realizadas:</strong> {sum(analysis_summary.values())}<br>
                            <strong>Ferramentas utilizadas:</strong> {', '.join(analysis_summary.keys())}
                        </div>
                    </div>
                    ''' if analysis_summary else ''}
                    
                    <!-- ==================== DEFINE ==================== -->
                    <div class="section">
                        <h2>🔎 DEFINE - Definição do Projeto</h2>
                        
                        <h3>📋 Project Charter</h3>
                        
                        <div class="info">
                            <h4>Declaração do Problema</h4>
                            <p>{project_info.get('problem_statement', 'Não definido') if project_info else 'Não definido'}</p>
                        </div>
                        
                        <div class="success">
                            <h4>Declaração da Meta</h4>
                            <p>{project_info.get('goal_statement', 'Não definido') if project_info else 'Não definido'}</p>
                        </div>
                        
                        <h4>Business Case</h4>
                        <p style="margin: 15px 0;">{project_info.get('business_case', 'Não definido') if project_info else 'Não definido'}</p>
                        
                        <h4>Escopo do Projeto</h4>
                        <p style="margin: 15px 0;">{project_info.get('project_scope', 'Não definido') if project_info else 'Não definido'}</p>
                        
                        <div class="dashboard-grid">
                            <div>
                                <h4>✅ Dentro do Escopo</h4>
                                <ul style="margin: 10px 0 0 20px;">
                                    {('<li>' + project_info.get('in_scope', '').replace(chr(10), '</li><li>') + '</li>') if project_info and project_info.get('in_scope') else '<li>Não definido</li>'}
                                </ul>
                            </div>
                            <div>
                                <h4>❌ Fora do Escopo</h4>
                                <ul style="margin: 10px 0 0 20px;">
                                    {('<li>' + project_info.get('out_scope', '').replace(chr(10), '</li><li>') + '</li>') if project_info and project_info.get('out_scope') else '<li>Não definido</li>'}
                                </ul>
                            </div>
                        </div>
                        
                        <!-- VOC -->
                        {f'''
                        <h3>🗣️ Voice of Customer (VOC)</h3>
                        <table>
                            <thead>
                                <tr>
                                    <th>Segmento</th>
                                    <th>Necessidade do Cliente</th>
                                    <th>Prioridade</th>
                                    <th>CSAT Atual</th>
                                    <th>CSAT Meta</th>
                                </tr>
                            </thead>
                            <tbody>
                                {''.join([f"""
                                <tr>
                                    <td><strong>{row.get('customer_segment', '')}</strong></td>
                                    <td>{row.get('customer_need', '')}</td>
                                    <td><span class="badge badge-{'danger' if row.get('priority') == 'Crítica' else 'warning' if row.get('priority') == 'Alta' else 'info'}">{row.get('priority', '')}</span></td>
                                    <td>{row.get('csat_score', 'N/A')}</td>
                                    <td>{row.get('target_csat', 'N/A')}</td>
                                </tr>
                                """ for _, row in voc_items.iterrows()])}
                            </tbody>
                        </table>
                        ''' if voc_items is not None and len(voc_items) > 0 else '<div class="warning">Nenhum VOC cadastrado</div>'}
                        
                        <!-- SIPOC -->
                        {f'''
                        <h3>🔄 SIPOC - Visão Geral do Processo</h3>
                        <table>
                            <thead>
                                <tr>
                                    <th>Suppliers<br>(Fornecedores)</th>
                                    <th>Inputs<br>(Entradas)</th>
                                    <th>Process<br>(Processo)</th>
                                    <th>Outputs<br>(Saídas)</th>
                                    <th>Customers<br>(Clientes)</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>{sipoc_data.get('suppliers', '').replace(chr(10), '<br>') if sipoc_data else ''}</td>
                                    <td>{sipoc_data.get('inputs', '').replace(chr(10), '<br>') if sipoc_data else ''}</td>
                                    <td>{sipoc_data.get('process', '').replace(chr(10), '<br>') if sipoc_data else ''}</td>
                                    <td>{sipoc_data.get('outputs', '').replace(chr(10), '<br>') if sipoc_data else ''}</td>
                                    <td>{sipoc_data.get('customers', '').replace(chr(10), '<br>') if sipoc_data else ''}</td>
                                </tr>
                            </tbody>
                        </table>
                        ''' if sipoc_data else '<div class="warning">SIPOC não definido</div>'}
                    </div>
                    
                    <!-- ==================== MEASURE ==================== -->
                    <div class="section">
                        <h2>📏 MEASURE - Medição e Coleta de Dados</h2>
                        
                        <div class="chart-container">
                            <h3>📈 Evolução do Indicador Principal</h3>
                            {trend_html}
                        </div>
                        
                        {f'''
                        <h3>📊 Estatísticas do Processo</h3>
                        <div class="metrics">
                            <div class="metric-card">
                                <div class="metric-label">Média</div>
                                <div class="metric-value">{measurements['metric_value'].mean():.2f}</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-label">Desvio Padrão</div>
                                <div class="metric-value">{measurements['metric_value'].std():.2f}</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-label">Mínimo</div>
                                <div class="metric-value">{measurements['metric_value'].min():.2f}</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-label">Máximo</div>
                                <div class="metric-value">{measurements['metric_value'].max():.2f}</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-label">Mediana</div>
                                <div class="metric-value">{measurements['metric_value'].median():.2f}</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-label">Total de Medições</div>
                                <div class="metric-value">{len(measurements)}</div>
                            </div>
                        </div>
                        ''' if measurements is not None and len(measurements) > 0 else '<div class="warning">Dados de medição não disponíveis</div>'}
                    </div>
                    
                    <!-- ==================== ANALYZE ==================== -->
                    <div class="section">
                        <h2>🔍 ANALYZE - Análise e Identificação de Causas</h2>
                        
                        <!-- Gráfico de Pareto -->
                        {f'''
                        <div class="chart-container">
                            {pareto_html}
                        </div>
                        ''' if pareto_html else ''}
                        
                        <!-- Regressão -->
                        {regression_html if regression_html else ''}
                        
                        <!-- Ishikawa / 5 Porquês -->
                        {ishikawa_html if ishikawa_html else ''}
                        
                        <!-- FMEA -->
                        {f'''
                        <div class="chart-container">
                            <h3>⚠️ FMEA - Análise de Riscos</h3>
                            {fmea_html}
                        </div>
                        ''' if fmea_html else ''}
                        
                        <!-- Resumo de todas as análises -->
                        <h3>📋 Resumo de Análises Realizadas</h3>
                        <table>
                            <thead>
                                <tr>
                                    <th>Tipo de Análise</th>
                                    <th>Quantidade</th>
                                    <th>Última Atualização</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {''.join([f"""
                                <tr>
                                    <td><strong>{analysis_type}</strong></td>
                                    <td>{len(items)}</td>
                                    <td>{pd.to_datetime(items[0].get('created_at', '')).strftime('%d/%m/%Y') if items[0].get('created_at') else 'N/A'}</td>
                                    <td><span class="badge badge-success">✅ Concluída</span></td>
                                </tr>
                                """ for analysis_type, items in all_analyses.items()])}
                            </tbody>
                        </table>
                        
                        {f'''
                        <div class="info">
                            <h4>💡 Insights Principais</h4>
                            <ul style="margin: 10px 0 0 20px;">
                                <li><strong>{len(all_analyses)}</strong> tipos diferentes de análises foram realizadas</li>
                                <li><strong>{sum(len(items) for items in all_analyses.values())}</strong> análises totais registradas</li>
                                <li>Ferramentas estatísticas e qualitativas combinadas para análise robusta</li>
                            </ul>
                        </div>
                        ''' if all_analyses else ''}
                    </div>
                    
                    <!-- ==================== IMPROVE ==================== -->
                    <div class="section">
                        <h2>🔧 IMPROVE - Implementação de Melhorias</h2>
                        
                        {f'''
                        <h3>🎯 Ações de Melhoria Implementadas</h3>
                        
                        <div class="metrics">
                            <div class="metric-card">
                                <div class="metric-label">Total de Ações</div>
                                <div class="metric-value">{len(actions)}</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-label">Concluídas</div>
                                <div class="metric-value" style="color: #28a745;">{len(actions[actions['status'] == 'Concluído'])}</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-label">Em Andamento</div>
                                <div class="metric-value" style="color: #ffc107;">{len(actions[actions['status'] == 'Em Andamento'])}</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-label">Taxa de Conclusão</div>
                                <div class="metric-value" style="color: #17a2b8;">{(len(actions[actions['status'] == 'Concluído']) / len(actions) * 100):.0f}%</div>
                            </div>
                        </div>
                        
                        <h3>📝 Detalhamento das Ações</h3>
                        <div class="timeline">
                            {''.join([f"""
                            <div class="timeline-item">
                                <h4>🎯 {row.get('action_title', 'Sem título')}</h4>
                                <p style="margin: 10px 0;">{row.get('description', 'Sem descrição')}</p>
                                <div style="margin-top: 15px;">
                                    <span class="badge badge-{'success' if row.get('status') == 'Concluído' else 'warning' if row.get('status') == 'Em Andamento' else 'info'}">{row.get('status', 'Planejado')}</span>
                                    <span class="badge badge-info">👤 {row.get('responsible', 'N/A')}</span>
                                    <span class="badge badge-{'danger' if row.get('impact_level') == 'Crítico' else 'warning' if row.get('impact_level') == 'Alto' else 'info'}">📊 {row.get('impact_level', 'Médio')} Impacto</span>
                                    {f'<span class="badge badge-success">💰 R$ {row.get("expected_savings", 0):,.0f}</span>' if row.get('expected_savings') else ''}
                                </div>
                            </div>
                            """ for _, row in actions.iterrows()])}
                        </div>
                        ''' if actions is not None and len(actions) > 0 else '<div class="warning">⚠️ Nenhuma ação de melhoria registrada</div>'}
                        
                        <!-- Brainstorm Ideas -->
                        {f'''
                        <h3>💡 Ideias Geradas (Brainstorm)</h3>
                        <table>
                            <thead>
                                <tr>
                                    <th>Ideia</th>
                                    <th>Categoria</th>
                                    <th>Impacto</th>
                                    <th>Viabilidade</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {''.join([f"""
                                <tr>
                                    <td>{row.get('idea', '')}</td>
                                    <td><span class="badge badge-info">{row.get('category', 'N/A')}</span></td>
                                    <td><span class="badge badge-{'success' if row.get('impact') == 'Alto' else 'warning' if row.get('impact') == 'Médio' else 'info'}">{row.get('impact', 'N/A')}</span></td>
                                    <td><span class="badge badge-{'success' if row.get('feasibility') == 'Alta' else 'warning' if row.get('feasibility') == 'Média' else 'danger'}">{row.get('feasibility', 'N/A')}</span></td>
                                    <td><span class="badge badge-{'success' if row.get('status') == 'Implementada' else 'warning'}">{row.get('status', 'Pendente')}</span></td>
                                </tr>
                                """ for _, row in brainstorm_ideas.iterrows()])}
                            </tbody>
                        </table>
                        ''' if brainstorm_ideas is not None and len(brainstorm_ideas) > 0 else ''}
                    </div>
                    
                    <!-- ==================== CONTROL ==================== -->
                    <div class="section">
                        <h2>✅ CONTROL - Controle e Sustentação</h2>
                        
                        {f'''
                        <h3>📋 Plano de Controle</h3>
                        <table>
                            <thead>
                                <tr>
                                    <th>Item de Controle</th>
                                    <th>Especificação</th>
                                    <th>Método de Medição</th>
                                    <th>Frequência</th>
                                    <th>Responsável</th>
                                    <th>Criticidade</th>
                                </tr>
                            </thead>
                            <tbody>
                                {''.join([f"""
                                <tr>
                                    <td><strong>{row.get('control_item', '')}</strong></td>
                                    <td>{row.get('specification', '')}</td>
                                    <td>{row.get('measurement_method', '')}</td>
                                    <td><span class="badge badge-info">{row.get('frequency', '')}</span></td>
                                    <td>{row.get('responsible', '')}</td>
                                    <td><span class="badge badge-{'danger' if row.get('critical_level') == 'Crítica' else 'warning' if row.get('critical_level') == 'Alta' else 'success'}">{row.get('critical_level', '')}</span></td>
                                </tr>
                                """ for _, row in control_plans.iterrows()])}
                            </tbody>
                        </table>
                        ''' if control_plans is not None and len(control_plans) > 0 else '<div class="warning">⚠️ Plano de controle não definido</div>'}
                        
                        {f'''
                        <h3>📚 Lições Aprendidas</h3>
                        <div class="timeline">
                            {''.join([f"""
                            <div class="timeline-item">
                                <h4>💡 {row.get('lesson_type', 'Lição Aprendida')}</h4>
                                <p><strong>Descrição:</strong> {row.get('description', '')}</p>
                                <p><strong>Recomendações Futuras:</strong> {row.get('recommendations', '')}</p>
                                <div style="margin-top: 10px;">
                                    <span class="badge badge-{'success' if row.get('impact') == 'Alto' else 'warning' if row.get('impact') == 'Médio' else 'info'}">{row.get('impact', 'Médio')} Impacto</span>
                                </div>
                            </div>
                            """ for _, row in lessons.iterrows()])}
                        </div>
                        ''' if lessons is not None and len(lessons) > 0 else '<div class="warning">⚠️ Nenhuma lição aprendida documentada</div>'}
                    </div>
                    
                    <!-- ==================== CONCLUSÃO E PRÓXIMOS PASSOS ==================== -->
                    <div class="section">
                        <h2>🎯 Conclusão e Próximos Passos</h2>
                        
                        <div class="{'success' if achievement >= 90 else 'info'}">
                            <h3>📊 Resultados Finais</h3>
                            <ul style="margin: 15px 0 0 20px; line-height: 2;">
                                <li><strong>Status:</strong> {'✅ Meta Atingida!' if achievement >= 90 else '⏳ Em Progresso'}</li>
                                <li><strong>Baseline:</strong> {baseline:.1f} → <strong>Atual:</strong> {current:.1f} (Melhoria: {improvement:.1f}%)</li>
                                <li><strong>Meta:</strong> {target:.1f} (Progresso: {achievement:.0f}%)</li>
                                {f'<li><strong>Economia Realizada:</strong> R$ {project_info.get("expected_savings", 0):,.2f}</li>' if project_info and project_info.get("expected_savings") else ''}
                                <li><strong>Análises Realizadas:</strong> {sum(len(items) for items in all_analyses.values())} análises em {len(all_analyses)} ferramentas</li>
                                {f'<li><strong>Ações Implementadas:</strong> {len(actions[actions["status"] == "Concluído"])} de {len(actions)} concluídas</li>' if actions is not None and len(actions) > 0 else ''}
                            </ul>
                        </div>
                        
                        <h3>🚀 Próximos Passos</h3>
                        <div class="timeline">
                            <div class="timeline-item">
                                <h4>1. Monitoramento Contínuo</h4>
                                <p>Seguir o plano de controle estabelecido e revisar indicadores conforme frequência definida</p>
                            </div>
                            <div class="timeline-item">
                                <h4>2. Validação de Resultados</h4>
                                <p>Confirmar sustentação dos ganhos nos próximos 3-6 meses</p>
                            </div>
                            <div class="timeline-item">
                                <h4>3. Replicação</h4>
                                <p>Identificar oportunidades de aplicar as melhorias em outras áreas/processos</p>
                            </div>
                            <div class="timeline-item">
                                <h4>4. Compartilhamento</h4>
                                <p>Apresentar resultados e lições aprendidas para a organização</p>
                            </div>
                            {'<div class="timeline-item"><h4>5. Ações Corretivas</h4><p>Implementar ajustes conforme necessário para atingir a meta</p></div>' if achievement < 90 else '<div class="timeline-item"><h4>5. Padronização</h4><p>Documentar e padronizar as melhorias implementadas</p></div>'}
                        </div>
                        
                        <div class="success" style="margin-top: 30px;">
                            <h3>🏆 Reconhecimentos</h3>
                            <p>Este projeto foi realizado com dedicação e trabalho em equipe, aplicando metodologia Lean Six Sigma para gerar resultados mensuráveis e sustentáveis.</p>
                            <p style="margin-top: 10px;"><strong>Equipe do Projeto:</strong></p>
                            <ul style="margin: 10px 0 0 20px;">
                                <li><strong>Green Belt:</strong> {project_info.get('project_leader', 'N/A') if project_info else 'N/A'}</li>
                                <li><strong>Sponsor:</strong> {project_info.get('project_sponsor', 'N/A') if project_info else 'N/A'}</li>
                                <li><strong>Departamento:</strong> {project_info.get('department', 'N/A') if project_info else 'N/A'}</li>
                            </ul>
                        </div>
                    </div>
                    
                    <!-- ==================== ANEXOS ==================== -->
                    <div class="section">
                        <h2>📎 Anexos e Documentos Complementares</h2>
                        
                        <h3>📊 Dados Estatísticos Detalhados</h3>
                        {f'''
                        <table>
                            <thead>
                                <tr>
                                    <th>Data</th>
                                    <th>Valor Medido</th>
                                    <th>Observações</th>
                                </tr>
                            </thead>
                            <tbody>
                                {''.join([f"""
                                <tr>
                                    <td>{pd.to_datetime(row.get('measurement_date', '')).strftime('%d/%m/%Y') if row.get('measurement_date') else 'N/A'}</td>
                                    <td><strong>{row.get('metric_value', 'N/A')}</strong></td>
                                    <td>{row.get('notes', '-')}</td>
                                </tr>
                                """ for _, row in measurements.tail(20).iterrows()])}
                            </tbody>
                        </table>
                        ''' if measurements is not None and len(measurements) > 0 else '<p>Dados não disponíveis</p>'}
                        
                        <div class="info" style="margin-top: 30px;">
                            <h4>📄 Documentos Gerados</h4>
                            <ul style="margin: 10px 0 0 20px;">
                                <li>✅ Relatório HTML Interativo</li>
                                <li>✅ Project Charter</li>
                                <li>✅ Análises Estatísticas Completas</li>
                                <li>✅ Plano de Controle</li>
                                <li>✅ Lições Aprendidas</li>
                            </ul>
                        </div>
                    </div>
                </div>
                
                <footer>
                    <div style="margin-bottom: 15px;">
                        <h3 style="color: white; margin-bottom: 10px;">📊 Relatório Gerado Automaticamente</h3>
                        <p>Sistema Green Belt - Metodologia Lean Six Sigma</p>
                    </div>
                    <p style="opacity: 0.8;">{datetime.now().strftime('%d de %B de %Y às %H:%M')}</p>
                    <p style="margin-top: 15px; opacity: 0.7;">© 2024-2025 - Projeto {project_name}</p>
                    <p style="margin-top: 10px; font-size: 0.9em; opacity: 0.6;">
                        Relatório confidencial - Para uso interno apenas
                    </p>
                </footer>
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    # ==================== INTERFACE DA TAB ====================
    st.info("📊 Compile toda a documentação do projeto em um relatório profissional completo com gráficos interativos e análises detalhadas")
    
    # Estatísticas do projeto
    if supabase and project_name:
        try:
            # Contar análises
            analyses_count = supabase.table('analyses').select('analysis_type', count='exact').eq('project_name', project_name).execute()
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("📊 Análises", analyses_count.count if analyses_count else 0)
            
            # Contar ações
            actions_count = supabase.table('improvement_actions').select('*', count='exact').eq('project_name', project_name).execute()
            col2.metric("🎯 Ações", actions_count.count if actions_count else 0)
            
            # Contar medições
            measurements_count = supabase.table('measurements').select('*', count='exact').eq('project_name', project_name).execute()
            col3.metric("📏 Medições", measurements_count.count if measurements_count else 0)
            
            # Controles
            controls_count = supabase.table('control_plans').select('*', count='exact').eq('project_name', project_name).execute()
            col4.metric("✅ Controles", controls_count.count if controls_count else 0)
            
        except:
            pass
    
    st.divider()
    
    # Prévia do conteúdo
    with st.expander("📋 Prévia do Conteúdo do Relatório Premium", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **📑 Seções Incluídas:**
            - ✅ Resumo Executivo com métricas-chave
            - ✅ Dashboard de análises realizadas
            - ✅ Project Charter completo
            - ✅ VOC (Voice of Customer) detalhado
            - ✅ SIPOC do processo
            - ✅ Dados e estatísticas de medição
            - ✅ Gráfico de tendência temporal
            - ✅ **Análise de Pareto** (se disponível)
            - ✅ **Análise de Regressão** (se disponível)
            - ✅ **Ishikawa/5 Porquês** (se disponível)
            - ✅ **FMEA com gráfico de riscos** (se disponível)
            - ✅ **ANOVA** (se disponível)
            - ✅ **Testes de Hipóteses** (se disponível)
            - ✅ Ações de melhoria implementadas
            - ✅ Ideias do brainstorm
            - ✅ Plano de controle
            - ✅ Lições aprendidas
            - ✅ Conclusões e próximos passos
            - ✅ Anexos com dados detalhados
            """)
        
        with col2:
            st.markdown("""
            **🎨 Elementos Visuais e Recursos:**
            - 📊 Gráfico de progresso (gauge interativo)
            - 📈 Gráfico de tendência temporal
            - 📊 Dashboard de análises realizadas
            - 📊 Gráfico de Pareto interativo
            - 📉 Gráfico de regressão
            - ⚠️ Gráfico FMEA de riscos
            - 🎨 Design moderno e profissional
            - 📱 Layout responsivo
            - 🖨️ Otimizado para impressão
            - ⚡ Gráficos interativos com Plotly
            - 🎯 Badges e indicadores visuais
            - 📋 Tabelas estilizadas
            - 🌈 Gradientes e animações sutis
            - 📊 Métricas em cards destacados
            - ⏱️ Timeline de ações e lições
            """)
    
    st.divider()
    
    # Opções de geração
    st.subheader("🎯 Gerar Relatório Final")
    
    col_opt1, col_opt2 = st.columns(2)
    
    with col_opt1:
        include_charts = st.checkbox("📊 Incluir todos os gráficos interativos", value=True)
    
    with col_opt2:
        include_raw_data = st.checkbox("📋 Incluir dados brutos (últimas 20 medições)", value=True)
    
    # Botões de ação
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🌐 Gerar Relatório HTML Premium", type="primary", use_container_width=True):
            with st.spinner("🔄 Gerando relatório completo com todos os gráficos e análises..."):
                try:
                    html_report = generate_premium_html_report(project_name)
                    
                    # Download
                    st.download_button(
                        label="📥 Download Relatório HTML Premium",
                        data=html_report,
                        file_name=f"relatorio_premium_{project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                        mime="text/html",
                        use_container_width=True,
                        type="primary"
                    )
                    
                    st.success("✅ Relatório HTML Premium gerado com sucesso!")
                    
                    # Prévia
                    with st.expander("👁️ Visualizar Relatório no Navegador"):
                        st.components.v1.html(html_report, height=800, scrolling=True)
                        
                except Exception as e:
                    st.error(f"❌ Erro ao gerar relatório: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
    
    with col2:
        if st.button("📄 Instruções para PDF", use_container_width=True):
            st.info("""
            **📄 Como Converter HTML em PDF:**
            
            1. 📥 Baixe o relatório HTML
            2. 🌐 Abra o arquivo no navegador (Chrome, Edge, Firefox)
            3. ⌨️ Pressione **Ctrl+P** (Windows) ou **Cmd+P** (Mac)
            4. 🖨️ Selecione **"Salvar como PDF"** como destino
            5. ⚙️ Ajuste as configurações:
               - Orientação: Retrato
               - Margens: Padrão
               - Gráficos em segundo plano: Ativado
            6. 💾 Salve o arquivo PDF
            
            💡 **Dica:** O relatório foi otimizado para impressão profissional!
            """)
    
    with col3:
        if st.button("📊 Exportar Excel Detalhado", use_container_width=True):
            with st.spinner("Gerando arquivo Excel..."):
                try:
                    # Criar arquivo Excel com múltiplas abas
                    from io import BytesIO
                    
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        # Aba 1: Resumo
                        project_info_dict = project_info if project_info else {}
                        summary_data = {
                            'Métrica': ['Projeto', 'Líder', 'Sponsor', 'Departamento', 'Baseline', 'Meta', 'Atual', 'Melhoria (%)', 'Progresso (%)', 'Status'],
                            'Valor': [
                                project_name,
                                project_info_dict.get('project_leader', 'N/A'),
                                project_info_dict.get('project_sponsor', 'N/A'),
                                project_info_dict.get('department', 'N/A'),
                                baseline,
                                target,
                                current,
                                f"{improvement:.1f}",
                                f"{achievement:.0f}",
                                'Concluído' if achievement >= 90 else 'Em andamento'
                            ]
                        }
                        df_summary = pd.DataFrame(summary_data)
                        df_summary.to_excel(writer, sheet_name='Resumo', index=False)
                                                
                        # Aba 2: Medições (se disponível)
                        if measurements is not None and len(measurements) > 0:
                            measurements.to_excel(writer, sheet_name='Medições', index=False)
                        
                        # Aba 3: Ações (se disponível)
                        if actions is not None and len(actions) > 0:
                            actions.to_excel(writer, sheet_name='Ações', index=False)
                        
                        # Aba 4: Controles (se disponível)
                        if control_plans is not None and len(control_plans) > 0:
                            control_plans.to_excel(writer, sheet_name='Controles', index=False)
                        
                        # Aba 5: VOC (se disponível)
                        if voc_items is not None and len(voc_items) > 0:
                            voc_items.to_excel(writer, sheet_name='VOC', index=False)
                    
                    output.seek(0)
                    
                    st.download_button(
                        label="📥 Download Excel Completo",
                        data=output.getvalue(),
                        file_name=f"relatorio_excel_{project_name}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    
                    st.success("✅ Arquivo Excel gerado com sucesso!")
                    
                except Exception as e:
                    st.error(f"❌ Erro ao gerar Excel: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())

               

# Footer
st.divider()
st.caption("💡 **Dica:** A fase Control garante a sustentabilidade das melhorias. Mantenha o monitoramento contínuo!")
