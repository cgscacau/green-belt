import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import io
import json
from scipy import stats
from supabase import create_client, Client
import os

# Configuração da página
st.set_page_config(
    page_title="Improve - Green Belt",
    page_icon="🛠️",
    layout="wide"
)

# Configuração do Supabase
@st.cache_resource
def init_supabase():
    url = os.environ.get("SUPABASE_URL", st.secrets.get("SUPABASE_URL", ""))
    key = os.environ.get("SUPABASE_KEY", st.secrets.get("SUPABASE_KEY", ""))
    if url and key:
        return create_client(url, key)
    return None

supabase = init_supabase()

# Função para carregar dados do projeto do Supabase
@st.cache_data(ttl=300)
def load_project_data():
    """Carrega os dados do projeto do Supabase"""
    if supabase:
        try:
            # Carregar dados principais do projeto
            response = supabase.table('project_data').select("*").execute()
            if response.data:
                df = pd.DataFrame(response.data)
                # Converter colunas numéricas
                numeric_columns = ['horas_operacao', 'tempo_parada_min', 'custo', 'quantidade', 'defeitos']
                for col in numeric_columns:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                return df
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
    
    # Se não houver dados no Supabase, verificar session_state
    if 'project_df' in st.session_state:
        return st.session_state.project_df
    elif 'df' in st.session_state:
        return st.session_state.df
    
    return pd.DataFrame()

# Função para carregar análises da página Analyze
@st.cache_data(ttl=300)
def load_analyze_results():
    """Carrega resultados das análises já realizadas na página Analyze"""
    if supabase:
        try:
            response = supabase.table('analyze_results').select("*").order('created_at', desc=True).execute()
            if response.data:
                return response.data
        except:
            pass
    
    # Verificar session_state para análises
    if 'analyze_results' in st.session_state:
        return st.session_state.analyze_results
    
    return []

# Função para salvar plano de ação no Supabase
def save_action_plan(action_data):
    """Salva plano de ação no Supabase"""
    if supabase:
        try:
            response = supabase.table('action_plans').insert(action_data).execute()
            return True
        except Exception as e:
            st.error(f"Erro ao salvar plano de ação: {e}")
    return False

# Função para carregar planos de ação salvos
@st.cache_data(ttl=300)
def load_action_plans():
    """Carrega planos de ação do Supabase"""
    if supabase:
        try:
            response = supabase.table('action_plans').select("*").order('created_at', desc=True).execute()
            if response.data:
                return response.data
        except:
            pass
    return []

# Carregar dados do projeto
df_projeto = load_project_data()
analyze_results = load_analyze_results()

# Inicializar session state
if 'improvement_actions' not in st.session_state:
    st.session_state.improvement_actions = load_action_plans()
if 'ishikawa_causes' not in st.session_state:
    st.session_state.ishikawa_causes = {
        "Método": [],
        "Máquina": [],
        "Mão de Obra": [],
        "Material": [],
        "Medida": [],
        "Meio Ambiente": []
    }

# Título e descrição
st.title("🛠️ Improve - Implementação de Melhorias")
st.markdown("""
Esta fase foca na implementação de soluções para os problemas identificados.
Vamos desenvolver, testar e implementar melhorias no processo.
""")

# Verificar se há dados carregados
if df_projeto.empty:
    st.warning("⚠️ Nenhum dado do projeto foi encontrado. Por favor, complete as fases anteriores primeiro.")
    st.stop()

# Mostrar estatísticas do projeto
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Registros", len(df_projeto))
with col2:
    st.metric("Variáveis", len(df_projeto.columns))
with col3:
    if 'defeitos' in df_projeto.columns:
        st.metric("Total Defeitos", df_projeto['defeitos'].sum())
with col4:
    if 'custo' in df_projeto.columns:
        st.metric("Custo Médio", f"R$ {df_projeto['custo'].mean():.2f}")

# Tabs principais
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Análise de Causas",
    "📋 Plano de Ação",
    "🔬 Simulação",
    "📈 Resultados da Análise"
])

# Tab 1: Análise de Causas (Ishikawa)
with tab1:
    st.header("Análise de Causas Raiz")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Diagrama de Ishikawa (Espinha de Peixe)")
        st.info("Adicione as causas identificadas na fase Analyze para cada categoria")
        
        # Input para causas
        for categoria in st.session_state.ishikawa_causes:
            with st.expander(f"📌 {categoria}"):
                # Campo para adicionar nova causa
                nova_causa = st.text_input(
                    f"Adicionar causa em {categoria}",
                    key=f"nova_causa_{categoria}"
                )
                if st.button(f"Adicionar", key=f"add_{categoria}"):
                    if nova_causa and nova_causa not in st.session_state.ishikawa_causes[categoria]:
                        st.session_state.ishikawa_causes[categoria].append(nova_causa)
                        st.success(f"Causa adicionada em {categoria}")
                        st.rerun()
                
                # Listar causas existentes
                if st.session_state.ishikawa_causes[categoria]:
                    st.write("**Causas cadastradas:**")
                    for i, causa in enumerate(st.session_state.ishikawa_causes[categoria]):
                        col_causa, col_remove = st.columns([4, 1])
                        with col_causa:
                            st.write(f"{i+1}. {causa}")
                        with col_remove:
                            if st.button("🗑️", key=f"del_{categoria}_{i}"):
                                st.session_state.ishikawa_causes[categoria].pop(i)
                                st.rerun()
    
    with col2:
        st.subheader("Priorização de Causas")
        
        # Coletar todas as causas para priorização
        todas_causas = []
        for cat, causas_list in st.session_state.ishikawa_causes.items():
            for causa in causas_list:
                todas_causas.append({
                    "Categoria": cat,
                    "Causa": causa,
                    "Impacto": 5,
                    "Facilidade": 5,
                    "Custo": 5
                })
        
        if todas_causas:
            st.write("Avalie cada causa (1-10):")
            
            # Editor de dados para priorização
            df_causas = pd.DataFrame(todas_causas)
            
            df_editado = st.data_editor(
                df_causas,
                column_config={
                    "Impacto": st.column_config.NumberColumn(
                        "Impacto (1-10)",
                        min_value=1,
                        max_value=10,
                        default=5
                    ),
                    "Facilidade": st.column_config.NumberColumn(
                        "Facilidade (1-10)",
                        min_value=1,
                        max_value=10,
                        default=5
                    ),
                    "Custo": st.column_config.NumberColumn(
                        "Custo (1-10)",
                        min_value=1,
                        max_value=10,
                        default=5
                    )
                },
                hide_index=True,
                key="causas_editor"
            )
            
            # Calcular score
            df_editado["Score"] = (
                df_editado["Impacto"] * 0.5 +
                df_editado["Facilidade"] * 0.3 +
                (11 - df_editado["Custo"]) * 0.2
            ) * 10
            
            # Ordenar por score
            df_editado = df_editado.sort_values("Score", ascending=False)
            
            # Mostrar top 3
            if len(df_editado) > 0:
                st.subheader("🏆 Top 3 Causas Prioritárias")
                for idx, row in df_editado.head(3).iterrows():
                    st.write(f"**#{idx+1}**")
                    st.write(f"{row['Causa']}")
                    st.write(f"*Categoria: {row['Categoria']}*")
                    st.metric("Score", f"{row['Score']:.0f}")
                    if row['Score'] >= 70:
                        st.success("✅ Alta Prioridade")
                    st.markdown("---")
        else:
            st.info("Adicione causas no diagrama de Ishikawa para realizar a priorização")

# Tab 2: Plano de Ação
with tab2:
    st.header("Plano de Ação 5W2H")
    
    st.markdown("""
    Desenvolva um plano de ação detalhado usando a metodologia 5W2H:
    - **What** (O quê): O que será feito?
    - **Why** (Por quê): Por que será feito?
    - **Where** (Onde): Onde será feito?
    - **When** (Quando): Quando será feito?
    - **Who** (Quem): Quem fará?
    - **How** (Como): Como será feito?
    - **How Much** (Quanto): Quanto custará?
    """)
    
    # Formulário de nova ação
    with st.expander("➕ Adicionar Nova Ação", expanded=True):
        with st.form("action_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                what = st.text_area("O QUÊ será feito?", height=100)
                why = st.text_area("POR QUÊ será feito?", height=100)
                where = st.text_input("ONDE será feito?")
                when = st.date_input("QUANDO será feito?")
            
            with col2:
                who = st.text_input("QUEM fará?")
                how = st.text_area("COMO será feito?", height=100)
                how_much = st.number_input("QUANTO custará? (R$)", min_value=0.0, step=100.0)
                priority = st.selectbox("Prioridade", ["Alta", "Média", "Baixa"])
            
            submitted = st.form_submit_button("Adicionar Ação")
            
            if submitted and what and why:
                action = {
                    'what': what,
                    'why': why,
                    'where': where,
                    'when': when.isoformat(),
                    'who': who,
                    'how': how,
                    'how_much': float(how_much),
                    'priority': priority,
                    'status': 'Pendente',
                    'created_at': datetime.now().isoformat()
                }
                
                # Salvar no Supabase
                if save_action_plan(action):
                    st.session_state.improvement_actions.append(action)
                    st.success("✅ Ação adicionada e salva no banco de dados!")
                    st.rerun()
                else:
                    st.session_state.improvement_actions.append(action)
                    st.warning("Ação adicionada localmente (não foi possível salvar no banco)")
    
    # Visualização do Plano de Ação
    if st.session_state.improvement_actions:
        st.subheader("📋 Plano de Ação Atual")
        
        # Converter para DataFrame
        df_actions = pd.DataFrame(st.session_state.improvement_actions)
        
        # Estatísticas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total de Ações", len(df_actions))
        with col2:
            pending = len(df_actions[df_actions['status'] == 'Pendente'])
            st.metric("Pendentes", pending)
        with col3:
            if 'how_much' in df_actions.columns:
                total_cost = df_actions['how_much'].sum()
                st.metric("Custo Total", f"R$ {total_cost:,.2f}")
        with col4:
            high_priority = len(df_actions[df_actions['priority'] == 'Alta'])
            st.metric("Alta Prioridade", high_priority)
        
        # Tabela de ações
        display_cols = ['what', 'who', 'when', 'priority', 'status']
        if 'how_much' in df_actions.columns:
            display_cols.append('how_much')
        
        st.dataframe(
            df_actions[display_cols],
            use_container_width=True,
            hide_index=True
        )

# Tab 3: Simulação baseada em dados reais
with tab3:
    st.header("Simulação de Melhorias")
    st.markdown("Simule o impacto das melhorias propostas nos indicadores do processo.")
    
    # Calcular métricas atuais dos dados reais do projeto
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Parâmetros Atuais 📊")
        st.info("Valores calculados dos dados reais do projeto")
        
        # Calcular métricas dos dados
        if 'defeitos' in df_projeto.columns:
            current_defect_rate = (df_projeto['defeitos'].sum() / len(df_projeto)) * 100
        else:
            current_defect_rate = 5.0
            
        if 'tempo_parada_min' in df_projeto.columns:
            current_cycle_time = df_projeto['tempo_parada_min'].mean()
        else:
            current_cycle_time = 15.0
            
        if 'custo' in df_projeto.columns:
            current_cost = df_projeto['custo'].mean()
        else:
            current_cost = 25.0
            
        if 'horas_operacao' in df_projeto.columns:
            current_productivity = len(df_projeto) / df_projeto['horas_operacao'].sum() * 60
        else:
            current_productivity = 50.0
        
        st.metric("Taxa de Defeitos Atual", f"{current_defect_rate:.2f}%")
        st.metric("Tempo de Ciclo Atual", f"{current_cycle_time:.2f} min")
        st.metric("Custo por Unidade Atual", f"R$ {current_cost:.2f}")
        st.metric("Produtividade Atual", f"{current_productivity:.2f} un/hora")
    
    with col2:
        st.subheader("Parâmetros Esperados (Após Melhorias)")
        
        expected_defect_rate = st.slider(
            "Taxa de Defeitos Esperada (%)",
            min_value=0.0,
            max_value=current_defect_rate,
            value=current_defect_rate * 0.4,
            step=0.1
        )
        
        expected_cycle_time = st.slider(
            "Tempo de Ciclo Esperado (min)",
            min_value=1.0,
            max_value=current_cycle_time,
            value=current_cycle_time * 0.67,
            step=0.5
        )
        
        expected_cost = st.slider(
            "Custo por Unidade Esperado (R$)",
            min_value=1.0,
            max_value=current_cost,
            value=current_cost * 0.8,
            step=0.5
        )
        
        expected_productivity = st.slider(
            "Produtividade Esperada (un/hora)",
            min_value=current_productivity,
            max_value=current_productivity * 2,
            value=current_productivity * 1.5,
            step=1.0
        )
    
    # Análise de Impacto
    st.subheader("📊 Análise de Impacto")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        defect_reduction = ((current_defect_rate - expected_defect_rate) / current_defect_rate) * 100 if current_defect_rate > 0 else 0
        st.metric(
            "Redução de Defeitos",
            f"{defect_reduction:.1f}%",
            f"↑ {current_defect_rate - expected_defect_rate:.1f} pp"
        )
    
    with col2:
        cycle_improvement = ((current_cycle_time - expected_cycle_time) / current_cycle_time) * 100 if current_cycle_time > 0 else 0
        st.metric(
            "Redução Tempo Ciclo",
            f"{cycle_improvement:.1f}%",
            f"↓ {current_cycle_time - expected_cycle_time:.1f} min"
        )
    
    with col3:
        cost_reduction = ((current_cost - expected_cost) / current_cost) * 100 if current_cost > 0 else 0
        st.metric(
            "Redução de Custo",
            f"{cost_reduction:.1f}%",
            f"↓ R$ {current_cost - expected_cost:.2f}"
        )
    
    with col4:
        productivity_gain = ((expected_productivity - current_productivity) / current_productivity) * 100 if current_productivity > 0 else 0
        st.metric(
            "Ganho Produtividade",
            f"{productivity_gain:.1f}%",
            f"↑ +{expected_productivity - current_productivity:.0f} un/h"
        )
    
    # Comparação Visual
    st.subheader("Comparação Visual")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de barras
        comparison_data = pd.DataFrame({
            'Indicador': ['Taxa Defeitos (%)', 'Tempo Ciclo (min)', 'Custo (R$)', 'Produtividade (un/h)'],
            'Atual': [current_defect_rate, current_cycle_time, current_cost, current_productivity],
            'Esperado': [expected_defect_rate, expected_cycle_time, expected_cost, expected_productivity]
        })
        
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(name='Atual', x=comparison_data['Indicador'], y=comparison_data['Atual']))
        fig_bar.add_trace(go.Bar(name='Esperado', x=comparison_data['Indicador'], y=comparison_data['Esperado']))
        fig_bar.update_layout(
            title='Comparação de Indicadores',
            barmode='group',
            height=400
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        # Gráfico radar
        categories = ['Taxa Defeitos', 'Tempo Ciclo', 'Custo', 'Produtividade']
        
        atual_norm = [
            100 - (current_defect_rate * 5) if current_defect_rate <= 20 else 0,
            100 - (current_cycle_time * 1.67) if current_cycle_time <= 60 else 0,
            100 - current_cost if current_cost <= 100 else 0,
            current_productivity / 2 if current_productivity <= 200 else 100
        ]
        
        esperado_norm = [
            100 - (expected_defect_rate * 5),
            100 - (expected_cycle_time * 1.67),
            100 - expected_cost,
            expected_productivity / 2
        ]
        
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=atual_norm, theta=categories, fill='toself', name='Atual'
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=esperado_norm, theta=categories, fill='toself', name='Esperado'
        ))
        fig_radar.update_layout(
            title="Análise Radar de Desempenho",
            height=400
        )
        st.plotly_chart(fig_radar, use_container_width=True)

# Tab 4: Resultados da Análise
with tab4:
    st.header("📈 Resultados da Fase Analyze")
    
    if analyze_results:
        st.success(f"Encontradas {len(analyze_results)} análises realizadas")
        
        # Mostrar resumo das análises
        for result in analyze_results:
            with st.expander(f"Análise: {result.get('type', 'N/A')} - {result.get('date', 'N/A')}"):
                st.json(result)
    else:
        st.info("Nenhuma análise da fase Analyze foi encontrada. Complete a fase Analyze primeiro.")
    
    # Mostrar gráficos e resultados importantes da fase Analyze
    if not df_projeto.empty:
        st.subheader("Principais Indicadores do Projeto")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'defeito' in df_projeto.columns:
                # Pareto de defeitos
                defeitos_count = df_projeto['defeito'].value_counts().head(10)
                fig = px.bar(
                    x=defeitos_count.index,
                    y=defeitos_count.values,
                    title="Top 10 Defeitos",
                    labels={'x': 'Defeito', 'y': 'Frequência'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if 'horas_operacao' in df_projeto.columns:
                # Histograma de horas de operação
                fig = px.histogram(
                    df_projeto,
                    x='horas_operacao',
                    title="Distribuição de Horas de Operação",
                    nbins=20
                )
                st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("🎯 **Fase Improve** - Green Belt Project | Implementação de Melhorias")
