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

# ========================= TAB 5: DOCUMENTAÇÃO COMPLETA =========================

with tab5:
    st.header("📑 Documentação Final do Projeto")
    
    # Função para gerar relatório HTML completo
    def generate_html_report(project_name):
        """Gera relatório HTML completo com todos os dados do projeto"""
        
        # Buscar TODOS os dados do Supabase
        project_info = load_project_from_db(project_name)
        voc_items = None
        sipoc_data = None
        measurements = None
        analyses = None
        actions = None
        control_plans = load_control_plans(project_name)
        lessons = load_lessons_learned(project_name)
        
        # Buscar dados adicionais
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
                
                # Analyses
                analyses_response = supabase.table('analyses').select("*").eq('project_name', project_name).execute()
                if analyses_response.data:
                    analyses = pd.DataFrame(analyses_response.data)
                
                # Actions
                actions_response = supabase.table('improvement_actions').select("*").eq('project_name', project_name).execute()
                if actions_response.data:
                    actions = pd.DataFrame(actions_response.data)
                
                # Brainstorm Ideas
                ideas_response = supabase.table('brainstorm_ideas').select("*").eq('project_name', project_name).execute()
                if ideas_response.data:
                    ideas = pd.DataFrame(ideas_response.data)
                else:
                    ideas = None
                    
            except Exception as e:
                st.error(f"Erro ao buscar dados: {str(e)}")
        
        # Calcular métricas
        baseline = project_info.get('baseline_value', 100) if project_info else 100
        target = project_info.get('target_value', 80) if project_info else 80
        current = baseline * 0.85  # Simulado - substituir por valor real dos measurements
        improvement = ((baseline - current) / baseline * 100) if baseline != 0 else 0
        achievement = ((baseline - current) / (baseline - target) * 100) if baseline != target else 0
        
        # Gerar gráficos como base64
        import plotly.graph_objects as go
        import base64
        from io import BytesIO
        
        # Gráfico de progresso
        fig_progress = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = achievement,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Progresso da Meta (%)"},
            delta = {'reference': 100},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkgreen" if achievement >= 90 else "orange"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 90], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig_progress.update_layout(height=300)
        
        # Converter gráfico para HTML
        progress_html = fig_progress.to_html(include_plotlyjs='cdn', div_id="progress-chart")
        
        # Gráfico de tendência
        if measurements is not None and len(measurements) > 0:
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=pd.to_datetime(measurements['measurement_date']),
                y=measurements['metric_value'],
                mode='lines+markers',
                name='Medições',
                line=dict(color='blue', width=2)
            ))
            fig_trend.add_hline(y=target, line_dash="dash", line_color="green", annotation_text=f"Meta: {target}")
            fig_trend.add_hline(y=baseline, line_dash="dash", line_color="red", annotation_text=f"Baseline: {baseline}")
            fig_trend.update_layout(
                title="Evolução do Indicador",
                xaxis_title="Data",
                yaxis_title=project_info.get('primary_metric', 'Métrica') if project_info else 'Métrica',
                height=400
            )
            trend_html = fig_trend.to_html(include_plotlyjs=False, div_id="trend-chart")
        else:
            trend_html = "<p>Dados de tendência não disponíveis</p>"
        
        # Gráfico de Pareto se houver análise
        pareto_html = ""
        if analyses is not None and len(analyses) > 0:
            pareto_analyses = analyses[analyses['analysis_type'] == 'pareto']
            if len(pareto_analyses) > 0:
                try:
                    pareto_data = pareto_analyses.iloc[0]['results']
                    if 'data' in pareto_data:
                        df_pareto = pd.DataFrame(pareto_data['data'])
                        
                        fig_pareto = go.Figure()
                        fig_pareto.add_trace(go.Bar(
                            x=df_pareto.get('Categoria', []),
                            y=df_pareto.get('Frequência', df_pareto.get('Valor', [])),
                            name='Frequência',
                            marker_color='lightblue'
                        ))
                        
                        if 'Acumulado' in df_pareto.columns:
                            fig_pareto.add_trace(go.Scatter(
                                x=df_pareto.get('Categoria', []),
                                y=df_pareto['Acumulado'],
                                name='% Acumulado',
                                yaxis='y2',
                                line=dict(color='red'),
                                mode='lines+markers'
                            ))
                            
                        fig_pareto.update_layout(
                            title="Análise de Pareto",
                            yaxis2=dict(overlaying='y', side='right', range=[0, 100]),
                            height=400
                        )
                        pareto_html = fig_pareto.to_html(include_plotlyjs=False, div_id="pareto-chart")
                except:
                    pareto_html = ""
        
        # Template HTML
        html_template = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Relatório Green Belt - {project_name}</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 20px;
                }}
                
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 15px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    overflow: hidden;
                }}
                
                header {{
                    background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
                    color: white;
                    padding: 40px;
                    text-align: center;
                }}
                
                h1 {{
                    font-size: 2.5em;
                    margin-bottom: 10px;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                }}
                
                .subtitle {{
                    font-size: 1.2em;
                    opacity: 0.9;
                }}
                
                .content {{
                    padding: 40px;
                }}
                
                .section {{
                    margin-bottom: 40px;
                    padding: 25px;
                    background: #f8f9fa;
                    border-radius: 10px;
                    border-left: 5px solid #3498db;
                }}
                
                h2 {{
                    color: #2c3e50;
                    margin-bottom: 20px;
                    padding-bottom: 10px;
                    border-bottom: 2px solid #3498db;
                }}
                
                h3 {{
                    color: #34495e;
                    margin: 20px 0 15px 0;
                }}
                
                .metrics {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin: 20px 0;
                }}
                
                .metric-card {{
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                    text-align: center;
                    transition: transform 0.3s;
                }}
                
                .metric-card:hover {{
                    transform: translateY(-5px);
                    box-shadow: 0 10px 25px rgba(0,0,0,0.15);
                }}
                
                .metric-value {{
                    font-size: 2em;
                    font-weight: bold;
                    color: #3498db;
                    margin: 10px 0;
                }}
                
                .metric-label {{
                    color: #7f8c8d;
                    font-size: 0.9em;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }}
                
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    background: white;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                
                th {{
                    background: #3498db;
                    color: white;
                    padding: 12px;
                    text-align: left;
                    font-weight: 600;
                }}
                
                td {{
                    padding: 12px;
                    border-bottom: 1px solid #ecf0f1;
                }}
                
                tr:hover {{
                    background: #f8f9fa;
                }}
                
                .success {{
                    background: #d4edda;
                    color: #155724;
                    padding: 15px;
                    border-radius: 5px;
                    border-left: 5px solid #28a745;
                    margin: 20px 0;
                }}
                
                .warning {{
                    background: #fff3cd;
                    color: #856404;
                    padding: 15px;
                    border-radius: 5px;
                    border-left: 5px solid #ffc107;
                    margin: 20px 0;
                }}
                
                .info {{
                    background: #d1ecf1;
                    color: #0c5460;
                    padding: 15px;
                    border-radius: 5px;
                    border-left: 5px solid #17a2b8;
                    margin: 20px 0;
                }}
                
                .chart-container {{
                    margin: 30px 0;
                    padding: 20px;
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                }}
                
                .timeline {{
                    position: relative;
                    padding: 20px 0;
                }}
                
                .timeline-item {{
                    padding: 20px 30px;
                    background: white;
                    border-radius: 10px;
                    margin-bottom: 20px;
                    border-left: 3px solid #3498db;
                    box-shadow: 0 3px 10px rgba(0,0,0,0.1);
                }}
                
                .badge {{
                    display: inline-block;
                    padding: 5px 10px;
                    border-radius: 20px;
                    font-size: 0.85em;
                    font-weight: bold;
                    margin-right: 10px;
                }}
                
                .badge-success {{
                    background: #28a745;
                    color: white;
                }}
                
                .badge-warning {{
                    background: #ffc107;
                    color: #333;
                }}
                
                .badge-info {{
                    background: #17a2b8;
                    color: white;
                }}
                
                .badge-danger {{
                    background: #dc3545;
                    color: white;
                }}
                
                footer {{
                    background: #2c3e50;
                    color: white;
                    text-align: center;
                    padding: 20px;
                    margin-top: 40px;
                }}
                
                @media print {{
                    body {{
                        background: white;
                        padding: 0;
                    }}
                    
                    .container {{
                        box-shadow: none;
                    }}
                    
                    .section {{
                        page-break-inside: avoid;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>🏆 Relatório Final - Projeto Green Belt</h1>
                    <div class="subtitle">{project_name}</div>
                    <div style="margin-top: 20px;">
                        <span style="margin: 0 15px;">📅 {datetime.now().strftime('%d/%m/%Y')}</span>
                        <span style="margin: 0 15px;">👤 {project_info.get('project_leader', 'N/A') if project_info else 'N/A'}</span>
                        <span style="margin: 0 15px;">🏢 {project_info.get('project_sponsor', 'N/A') if project_info else 'N/A'}</span>
                    </div>
                </header>
                
                <div class="content">
                    <!-- Resumo Executivo -->
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
                                <div class="metric-label">Atual</div>
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
                        
                        <div class="{'success' if achievement >= 90 else 'warning'}">
                            <strong>Status do Projeto:</strong> 
                            {'✅ Meta Atingida! Projeto concluído com sucesso.' if achievement >= 90 else '⏳ Projeto em andamento. Continue monitorando os resultados.'}
                        </div>
                    </div>
                    
                    <!-- DEFINE -->
                    <div class="section">
                        <h2>📋 DEFINE - Definição do Projeto</h2>
                        
                        <h3>Declaração do Problema</h3>
                        <div class="info">
                            {project_info.get('problem_statement', 'Não definido') if project_info else 'Não definido'}
                        </div>
                        
                        <h3>Declaração da Meta</h3>
                        <div class="info">
                            {project_info.get('goal_statement', 'Não definido') if project_info else 'Não definido'}
                        </div>
                        
                        <h3>Business Case</h3>
                        <p>{project_info.get('business_case', 'Não definido') if project_info else 'Não definido'}</p>
                        
                        <h3>Escopo</h3>
                        <p>{project_info.get('project_scope', 'Não definido') if project_info else 'Não definido'}</p>
                        
                        {'<h3>Voice of Customer (VOC)</h3>' if voc_items is not None else ''}
                        {f'''
                        <table>
                            <tr>
                                <th>Segmento</th>
                                <th>Necessidade</th>
                                <th>Prioridade</th>
                                <th>CSAT Atual</th>
                                <th>CSAT Meta</th>
                            </tr>
                            {''.join([f"""
                            <tr>
                                <td>{row.get('customer_segment', '')}</td>
                                <td>{row.get('customer_need', '')}</td>
                                <td><span class="badge badge-{'danger' if row.get('priority') == 'Crítica' else 'warning' if row.get('priority') == 'Alta' else 'info'}">{row.get('priority', '')}</span></td>
                                <td>{row.get('csat_score', '')}</td>
                                <td>{row.get('target_csat', '')}</td>
                            </tr>
                            """ for _, row in voc_items.iterrows()])}
                        </table>
                        ''' if voc_items is not None and len(voc_items) > 0 else '<p>Nenhum VOC cadastrado</p>'}
                        
                        {'<h3>SIPOC</h3>' if sipoc_data else ''}
                        {f'''
                        <table>
                            <tr>
                                <th>Suppliers</th>
                                <th>Inputs</th>
                                <th>Process</th>
                                <th>Outputs</th>
                                <th>Customers</th>
                            </tr>
                            <tr>
                                <td>{sipoc_data.get('suppliers', '').replace(chr(10), '<br>') if sipoc_data else ''}</td>
                                <td>{sipoc_data.get('inputs', '').replace(chr(10), '<br>') if sipoc_data else ''}</td>
                                <td>{sipoc_data.get('process', '').replace(chr(10), '<br>') if sipoc_data else ''}</td>
                                <td>{sipoc_data.get('outputs', '').replace(chr(10), '<br>') if sipoc_data else ''}</td>
                                <td>{sipoc_data.get('customers', '').replace(chr(10), '<br>') if sipoc_data else ''}</td>
                            </tr>
                        </table>
                        ''' if sipoc_data else ''}
                    </div>
                    
                    <!-- MEASURE -->
                    <div class="section">
                        <h2>📏 MEASURE - Medição e Coleta de Dados</h2>
                        
                        <div class="chart-container">
                            <h3>Tendência do Indicador</h3>
                            {trend_html}
                        </div>
                        
                        {f'''
                        <h3>Estatísticas do Processo</h3>
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
                        </div>
                        ''' if measurements is not None and len(measurements) > 0 else '<p>Dados de medição não disponíveis</p>'}
                    </div>
                    
                    <!-- ANALYZE -->
                    <div class="section">
                        <h2>📊 ANALYZE - Análise e Identificação de Causas</h2>
                        
                        {pareto_html if pareto_html else ''}
                        
                        {f'''
                        <h3>Análises Realizadas</h3>
                        <table>
                            <tr>
                                <th>Tipo de Análise</th>
                                <th>Data</th>
                                <th>Status</th>
                            </tr>
                            {''.join([f"""
                            <tr>
                                <td>{row.get('analysis_type', '')}</td>
                                <td>{pd.to_datetime(row.get('created_at', '')).strftime('%d/%m/%Y %H:%M') if row.get('created_at') else ''}</td>
                                <td><span class="badge badge-success">Concluída</span></td>
                            </tr>
                            """ for _, row in analyses.iterrows()])}
                        </table>
                        ''' if analyses is not None and len(analyses) > 0 else '<p>Nenhuma análise registrada</p>'}
                    </div>
                    
                    <!-- IMPROVE -->
                    <div class="section">
                        <h2>🔧 IMPROVE - Implementação de Melhorias</h2>
                        
                        {f'''
                        <h3>Ações Implementadas</h3>
                        <div class="timeline">
                            {''.join([f"""
                            <div class="timeline-item">
                                <h4>{row.get('action_title', '')}</h4>
                                <p>{row.get('description', '')}</p>
                                <div style="margin-top: 10px;">
                                    <span class="badge badge-{'success' if row.get('status') == 'Concluído' else 'warning' if row.get('status') == 'Em Andamento' else 'info'}">{row.get('status', '')}</span>
                                    <span class="badge badge-info">{row.get('responsible', '')}</span>
                                    <span class="badge badge-{'danger' if row.get('impact_level') == 'Crítico' else 'warning' if row.get('impact_level') == 'Alto' else 'info'}">{row.get('impact_level', '')} Impacto</span>
                                </div>
                            </div>
                            """ for _, row in actions.iterrows()])}
                        </div>
                        
                        <h3>Resumo das Ações</h3>
                        <div class="metrics">
                            <div class="metric-card">
                                <div class="metric-label">Total de Ações</div>
                                <div class="metric-value">{len(actions)}</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-label">Concluídas</div>
                                <div class="metric-value">{len(actions[actions['status'] == 'Concluído'])}</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-label">Em Andamento</div>
                                <div class="metric-value">{len(actions[actions['status'] == 'Em Andamento'])}</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-label">Taxa de Conclusão</div>
                                <div class="metric-value">{(len(actions[actions['status'] == 'Concluído']) / len(actions) * 100):.0f}%</div>
                            </div>
                        </div>
                        ''' if actions is not None and len(actions) > 0 else '<p>Nenhuma ação registrada</p>'}
                    </div>
                    
                    <!-- CONTROL -->
                    <div class="section">
                        <h2>✅ CONTROL - Controle e Sustentação</h2>
                        
                        {f'''
                        <h3>Plano de Controle</h3>
                        <table>
                            <tr>
                                <th>Item de Controle</th>
                                <th>Especificação</th>
                                <th>Método</th>
                                <th>Frequência</th>
                                <th>Responsável</th>
                                <th>Criticidade</th>
                            </tr>
                            {''.join([f"""
                            <tr>
                                <td>{row.get('control_item', '')}</td>
                                <td>{row.get('specification', '')}</td>
                                <td>{row.get('measurement_method', '')}</td>
                                <td>{row.get('frequency', '')}</td>
                                <td>{row.get('responsible', '')}</td>
                                <td><span class="badge badge-{'danger' if row.get('critical_level') == 'Crítica' else 'warning' if row.get('critical_level') == 'Alta' else 'info'}">{row.get('critical_level', '')}</span></td>
                            </tr>
                            """ for _, row in control_plans.iterrows()])}
                        </table>
                        ''' if control_plans is not None and len(control_plans) > 0 else '<p>Plano de controle não definido</p>'}
                        
                        {f'''
                        <h3>Lições Aprendidas</h3>
                        {''.join([f"""
                        <div class="timeline-item">
                            <h4>{row.get('lesson_type', '')}</h4>
                            <p><strong>Descrição:</strong> {row.get('description', '')}</p>
                            <p><strong>Recomendações:</strong> {row.get('recommendations', '')}</p>
                            <span class="badge badge-info">{row.get('impact', '')} Impacto</span>
                        </div>
                        """ for _, row in lessons.iterrows()])}
                        ''' if lessons is not None and len(lessons) > 0 else '<p>Nenhuma lição aprendida documentada</p>'}
                    </div>
                    
                    <!-- Conclusão -->
                    <div class="section">
                        <h2>🎯 Conclusão</h2>
                        
                        <div class="{'success' if achievement >= 90 else 'info'}">
                            <h3>Status Final do Projeto</h3>
                            <p>
                                O projeto <strong>{project_name}</strong> 
                                {'atingiu' if achievement >= 90 else 'está progredindo em direção à'} sua meta de reduzir 
                                o indicador de {baseline:.1f} para {target:.1f}.
                            </p>
                            <p>
                                <strong>Resultado alcançado:</strong> {current:.1f} 
                                (melhoria de {improvement:.1f}% em relação ao baseline)
                            </p>
                            {f'<p><strong>Economia realizada:</strong> R$ {project_info.get("expected_savings", 0):,.2f}</p>' if project_info and project_info.get("expected_savings") else ''}
                        </div>
                        
                        <h3>Próximos Passos</h3>
                        <ul>
                            <li>Continuar monitoramento conforme plano de controle estabelecido</li>
                            <li>Revisar indicadores mensalmente</li>
                            <li>Aplicar lições aprendidas em projetos futuros</li>
                            <li>Compartilhar resultados com a organização</li>
                            {'<li>Buscar oportunidades de replicação em outras áreas</li>' if achievement >= 90 else '<li>Implementar ações corretivas conforme necessário</li>'}
                        </ul>
                    </div>
                </div>
                
                <footer>
                    <p>Relatório gerado automaticamente pelo Sistema Green Belt</p>
                    <p>{datetime.now().strftime('%d de %B de %Y às %H:%M')}</p>
                    <p>© 2024 - Projeto Lean Six Sigma</p>
                </footer>
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    # Interface para gerar relatório
    st.info("Compile toda a documentação do projeto em um relatório profissional")
    
    # Prévia do conteúdo
    with st.expander("📋 Prévia do Conteúdo do Relatório"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Seções Incluídas:**")
            st.write("✅ Resumo Executivo com métricas")
            st.write("✅ Project Charter completo")
            st.write("✅ VOC e SIPOC")
            st.write("✅ Dados e gráficos de medição")
            st.write("✅ Análises realizadas (Pareto, etc)")
            st.write("✅ Ações de melhoria implementadas")
            st.write("✅ Plano de controle")
            st.write("✅ Lições aprendidas")
        
        with col2:
            st.write("**Elementos Visuais:**")
            st.write("📊 Gráfico de progresso (gauge)")
            st.write("📈 Gráfico de tendência")
            st.write("📊 Gráfico de Pareto")
            st.write("🎨 Design profissional")
            st.write("📱 Responsivo")
            st.write("🖨️ Pronto para impressão")
    
    st.divider()
    
    # Opções de geração
    st.subheader("🎯 Gerar Relatório Final")
    
    col1, col2 = st.columns(2)
    
    with col1:
        report_format = st.selectbox(
            "Formato do Relatório",
            ["HTML Interativo (Recomendado)", "PDF (via HTML)", "Excel Detalhado"]
        )
    
    with col2:
        include_charts = st.checkbox("Incluir gráficos interativos", value=True)
        include_timeline = st.checkbox("Incluir linha do tempo", value=True)
    
    # Botões de ação
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🌐 Gerar HTML", type="primary", use_container_width=True):
            with st.spinner("Gerando relatório completo..."):
                try:
                    html_report = generate_html_report(project_name)
                    
                    # Download
                    st.download_button(
                        label="📥 Download Relatório HTML",
                        data=html_report,
                        file_name=f"relatorio_completo_{project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                        mime="text/html",
                        use_container_width=True
                    )
                    
                    st.success("✅ Relatório HTML gerado com sucesso!")
                    
                    # Prévia
                    with st.expander("👁️ Visualizar Relatório"):
                        st.components.v1.html(html_report, height=800, scrolling=True)
                        
                except Exception as e:
                    st.error(f"Erro ao gerar relatório: {str(e)}")
    
    with col2:
        if st.button("📄 Instruções PDF", use_container_width=True):
            st.info("""
            **Para converter HTML em PDF:**
            1. Abra o arquivo HTML no navegador
            2. Pressione Ctrl+P (ou Cmd+P no Mac)
            3. Selecione "Salvar como PDF"
            4. Ajuste as configurações conforme necessário
            5. Salve o arquivo
            
            O relatório HTML foi otimizado para impressão!
            """)
    
    with col3:
        if st.button("📊 Versão Simplificada", use_container_width=True):
            # Versão simplificada em CSV
            summary_data = {
                'Métrica': ['Projeto', 'Líder', 'Baseline', 'Meta', 'Atual', 'Melhoria (%)', 'Status'],
                'Valor': [
                    project_name,
                    project_data.get('project_leader', 'N/A'),
                    baseline,
                    target,
                    current,
                    f"{improvement:.1f}",
                    'Concluído' if achievement >= 90 else 'Em andamento'
                ]
            }
            
            df_summary = pd.DataFrame(summary_data)
            csv = df_summary.to_csv(index=False)
            
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"resumo_{project_name}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )


# Footer
st.divider()
st.caption("💡 **Dica:** A fase Control garante a sustentabilidade das melhorias. Mantenha o monitoramento contínuo!")
