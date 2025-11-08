import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import io
import json
from scipy import stats

# Configuração da página
st.set_page_config(
    page_title="Improve - Green Belt",
    page_icon="🛠️",
    layout="wide"
)

# Função para converter tipos numpy para Python nativos
def convert_to_native_types(obj):
    """Converte tipos numpy/pandas para tipos Python nativos"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Series):
        return obj.tolist()
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict('records')
    elif isinstance(obj, dict):
        return {key: convert_to_native_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_native_types(item) for item in item]
    return obj

# Função para carregar dados existentes
@st.cache_data
def load_existing_data():
    """Carrega dados do projeto já existentes no sistema"""
    # Tentar carregar dados do session_state global ou de outras páginas
    if 'df' in st.session_state:
        return st.session_state.df
    elif 'data' in st.session_state:
        return st.session_state.data
    else:
        # Criar dados de exemplo baseados no contexto do projeto
        np.random.seed(42)
        n_records = 121  # Número de registros mostrado na imagem
        
        data = {
            'id': range(1, n_records + 1),
            'data': pd.date_range(start='2024-01-01', periods=n_records, freq='D'),
            'unidade': np.random.choice(['Unidade A', 'Unidade B', 'Unidade C'], n_records),
            'categoria': np.random.choice(['Material', 'Mão de Obra', 'Método'], n_records, 
                                        p=[0.5, 0.3, 0.2]),
            'defeito': np.random.choice([
                'Combustível com alto teor de água',
                'Falta de treinamento',
                'Processo de abastecimento inadequado',
                'Checklist incompleto',
                'Filtro saturado',
                'Tanque com contaminação',
                'Drenagem não realizada'
            ], n_records, p=[0.3, 0.2, 0.15, 0.1, 0.1, 0.1, 0.05]),
            'horas_operacao': np.random.normal(67.97, 4.59, n_records),
            'tempo_parada_min': np.random.exponential(30, n_records),
            'custo': np.random.exponential(100, n_records),
            'quantidade': np.random.poisson(5, n_records),
            'defeitos': np.random.poisson(3, n_records),
            'turno': np.random.choice(['Manhã', 'Tarde', 'Noite'], n_records),
            'linha': np.random.choice(['Linha 1', 'Linha 2', 'Linha 3'], n_records)
        }
        
        df = pd.DataFrame(data)
        df['horas_operacao'] = df['horas_operacao'].clip(lower=0)
        df['tempo_parada_min'] = df['tempo_parada_min'].clip(lower=0, upper=480)
        
        return df

# Inicializar session state
if 'improve_df' not in st.session_state:
    st.session_state.improve_df = load_existing_data()
if 'improve_analyses' not in st.session_state:
    st.session_state.improve_analyses = []
if 'improvement_actions' not in st.session_state:
    st.session_state.improvement_actions = []

# Calcular métricas atuais baseadas nos dados
if not st.session_state.improve_df.empty:
    df_metrics = st.session_state.improve_df
    current_defect_rate = (df_metrics['defeitos'].sum() / len(df_metrics) * 100) if 'defeitos' in df_metrics.columns else 5.0
    current_cycle_time = df_metrics['tempo_parada_min'].mean() if 'tempo_parada_min' in df_metrics.columns else 15
    current_cost = df_metrics['custo'].mean() if 'custo' in df_metrics.columns else 25.0
    current_productivity = len(df_metrics) / df_metrics['horas_operacao'].sum() * 60 if 'horas_operacao' in df_metrics.columns else 50
else:
    current_defect_rate = 5.0
    current_cycle_time = 15
    current_cost = 25.0
    current_productivity = 50

# Título e descrição
st.title("🛠️ Improve - Implementação de Melhorias")
st.markdown("""
Esta fase foca na implementação de soluções para os problemas identificados.
Vamos desenvolver, testar e implementar melhorias no processo.
""")

# Tabs principais
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Análise de Causas",
    "🎯 Pareto",
    "📋 Plano de Ação",
    "🔬 Simulação",
    "💾 Análises Salvas"
])

# Tab 1: Análise de Causas
with tab1:
    st.header("Análise de Causas Raiz")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Diagrama de Ishikawa (Espinha de Peixe)")
        
        # Categorias do Ishikawa
        categorias = {
            "Método": [],
            "Máquina": [],
            "Mão de Obra": [],
            "Material": [],
            "Medida": [],
            "Meio Ambiente": []
        }
        
        # Input para causas
        st.write("Adicione causas para cada categoria:")
        
        for categoria in categorias:
            with st.expander(f"📌 {categoria}"):
                num_causas = st.number_input(
                    f"Número de causas para {categoria}",
                    min_value=0,
                    max_value=5,
                    value=1,
                    key=f"num_{categoria}"
                )
                
                for i in range(int(num_causas)):
                    causa = st.text_input(
                        f"Causa {i+1}",
                        key=f"causa_{categoria}_{i}"
                    )
                    if causa:
                        if causa not in categorias[categoria]:
                            categorias[categoria].append(causa)
    
    with col2:
        st.subheader("Priorização de Causas")
        
        # Top 3 causas prioritárias (baseadas nos dados mostrados na imagem)
        st.subheader("🏆 Top 3 Causas Prioritárias")
        
        causas_prioritarias = [
            {
                "posicao": "#1",
                "causa": "Combustível com alto teor de água e contaminação biológica (bactérias/fungos).",
                "categoria": "Material",
                "score": 80,
                "prioridade": "Alta Prioridade"
            },
            {
                "posicao": "#2",
                "causa": "Falta de treinamento específico para inspeção e drenagem diária dos tanques de combustível.",
                "categoria": "Mão de Obra",
                "score": 72,
                "prioridade": "Alta Prioridade"
            },
            {
                "posicao": "#3",
                "causa": "Processo de abastecimento e armazenamento do diesel não padronizado (ausência de checklist e rotina de filtragem).",
                "categoria": "Método",
                "score": 72,
                "prioridade": "Alta Prioridade"
            }
        ]
        
        for causa in causas_prioritarias:
            with st.container():
                st.write(f"**Posição**")
                st.write(f"## {causa['posicao']}")
                st.write(causa['causa'])
                st.write(f"*Categoria: {causa['categoria']}*")
                col_score, col_prio = st.columns(2)
                with col_score:
                    st.metric("Score", causa['score'])
                with col_prio:
                    if causa['prioridade'] == "Alta Prioridade":
                        st.success(f"✅ {causa['prioridade']}")
                st.markdown("---")

# Tab 2: Análise de Pareto
with tab2:
    st.header("Análise de Pareto")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Configuração")
        
        # Usar dados carregados
        if not st.session_state.improve_df.empty:
            st.success(f"✅ {len(st.session_state.improve_df)} registros carregados")
            
            # Seleção de colunas
            cat_columns = st.session_state.improve_df.select_dtypes(include=['object']).columns.tolist()
            num_columns = st.session_state.improve_df.select_dtypes(include=[np.number]).columns.tolist()
            
            cat_col = st.selectbox(
                "Categoria (eixo X)",
                options=cat_columns,
                index=cat_columns.index('defeito') if 'defeito' in cat_columns else 0,
                key="pareto_cat"
            )
            
            val_col = st.selectbox(
                "Valor (eixo Y)",
                options=num_columns,
                index=num_columns.index('tempo_parada_min') if 'tempo_parada_min' in num_columns else 0,
                key="pareto_val"
            )
        else:
            st.warning("Nenhum dado carregado")
            
            # Upload de dados
            uploaded_file = st.file_uploader(
                "Upload de dados (CSV/Excel)",
                type=['csv', 'xlsx'],
                key="pareto_upload"
            )
            
            if uploaded_file:
                try:
                    if uploaded_file.name.endswith('.csv'):
                        st.session_state.improve_df = pd.read_csv(uploaded_file)
                    else:
                        st.session_state.improve_df = pd.read_excel(uploaded_file)
                    st.success("✅ Dados carregados com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao carregar arquivo: {e}")
    
    with col2:
        if not st.session_state.improve_df.empty and 'cat_col' in locals() and 'val_col' in locals():
            st.subheader("Pareto de Defeitos/Problemas")
            
            # Mostrar campos selecionados
            st.write(f"**Categoria (eixo X):** {cat_col}")
            st.write(f"**Valor (eixo Y):** {val_col}")
            
            def create_pareto_chart(df, category_col, value_col):
                """Cria gráfico de Pareto com tipos nativos"""
                try:
                    # Validar e limpar dados
                    df = df.copy()
                    df = df[df[value_col].notna()]
                    df = df[~df[value_col].isin([np.inf, -np.inf])]
                    df[value_col] = pd.to_numeric(df[value_col], errors='coerce')
                    df = df.dropna(subset=[value_col])
                    
                    # Agregar dados
                    pareto_data = df.groupby(category_col)[value_col].sum().sort_values(ascending=False).head(10)
                    
                    # Converter para tipos nativos imediatamente
                    categories = list(pareto_data.index)
                    values = [float(v) for v in pareto_data.values]
                    
                    # Calcular percentual acumulado
                    total = sum(values)
                    cumsum = []
                    cumulative = 0
                    for v in values:
                        cumulative += v
                        cumsum.append(cumulative)
                    
                    cumperc = [100.0 * c / total for c in cumsum]
                    
                    # Criar figura
                    fig = go.Figure()
                    
                    # Adicionar barras
                    fig.add_trace(go.Bar(
                        x=categories,
                        y=values,
                        name='Frequência',
                        marker_color='lightblue',
                        yaxis='y',
                        text=[f'{v:.0f}' for v in values],
                        textposition='auto'
                    ))
                    
                    # Adicionar linha de percentual acumulado
                    fig.add_trace(go.Scatter(
                        x=categories,
                        y=cumperc,
                        name='% Acumulado',
                        marker_color='red',
                        yaxis='y2',
                        mode='lines+markers',
                        line=dict(width=2),
                        text=[f'{p:.1f}%' for p in cumperc],
                        textposition='top center'
                    ))
                    
                    # Adicionar linha de referência em 80%
                    fig.add_hline(
                        y=80,
                        line_dash="dash",
                        line_color="green",
                        line_width=2,
                        yref='y2',
                        annotation_text="80%",
                        annotation_position="right"
                    )
                    
                    # Configurar layout
                    fig.update_layout(
                        title=f'Análise de Pareto - {category_col} vs {value_col}',
                        xaxis=dict(
                            title=category_col,
                            tickangle=45
                        ),
                        yaxis=dict(
                            title=value_col,
                            side='left'
                        ),
                        yaxis2=dict(
                            title='% Acumulado',
                            overlaying='y',
                            side='right',
                            range=[0, 105],
                            tickformat='.0f',
                            ticksuffix='%'
                        ),
                        hovermode='x unified',
                        height=500,
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        )
                    )
                    
                    # Retornar dados convertidos
                    pareto_dict = {
                        'categories': categories,
                        'values': values,
                        'cumulative_percent': cumperc
                    }
                    
                    return fig, pareto_dict
                    
                except Exception as e:
                    st.error(f"Erro ao criar gráfico: {e}")
                    return None, None
            
            # Gerar Pareto
            if st.button("📊 Gerar Pareto", key="gen_pareto"):
                fig, pareto_data = create_pareto_chart(
                    st.session_state.improve_df,
                    cat_col,
                    val_col
                )
                
                if fig and pareto_data:
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Insights do Pareto
                    st.info("📊 **Insights do Pareto:**")
                    
                    # Encontrar ponto 80/20
                    items_80 = 0
                    for i, perc in enumerate(pareto_data['cumulative_percent']):
                        if perc >= 80:
                            items_80 = i + 1
                            break
                    
                    total_items = len(pareto_data['categories'])
                    perc_items = (items_80 / total_items) * 100
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(
                            "Items para 80%",
                            f"{items_80} de {total_items}",
                            f"{perc_items:.1f}% dos items"
                        )
                    with col2:
                        st.metric(
                            "Top Categoria",
                            pareto_data['categories'][0] if pareto_data['categories'] else "N/A",
                            f"{pareto_data['cumulative_percent'][0]:.1f}% do total" if pareto_data['cumulative_percent'] else "N/A"
                        )
                    with col3:
                        total_value = sum(pareto_data['values'])
                        st.metric(
                            "Total Analisado",
                            f"{total_value:.0f}",
                            f"{len(st.session_state.improve_df)} registros"
                        )
                    
                    # Salvar análise
                    if st.button("💾 Salvar Análise", key="save_pareto"):
                        try:
                            output = io.StringIO()
                            fig.write_html(output)
                            
                            analysis_data = {
                                'type': 'pareto',
                                'timestamp': datetime.now().isoformat(),
                                'category': cat_col,
                                'value': val_col,
                                'data': pareto_data,
                                'insights': {
                                    'items_for_80': int(items_80),
                                    'total_items': int(total_items),
                                    'percent_items': float(perc_items),
                                    'top_category': str(pareto_data['categories'][0]) if pareto_data['categories'] else "N/A",
                                    'top_percent': float(pareto_data['cumulative_percent'][0]) if pareto_data['cumulative_percent'] else 0
                                },
                                'figure_html': output.getvalue()
                            }
                            
                            st.session_state.improve_analyses.append(analysis_data)
                            st.success("✅ Análise salva com sucesso!")
                            
                        except Exception as e:
                            st.error(f"Erro ao salvar: {e}")

# Tab 3: Plano de Ação
with tab3:
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
                    'id': len(st.session_state.improvement_actions) + 1,
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
                
                st.session_state.improvement_actions.append(action)
                st.success("✅ Ação adicionada ao plano!")
                st.rerun()
    
    # Visualização do Plano de Ação
    if st.session_state.improvement_actions:
        st.subheader("📋 Plano de Ação Atual")
        
        # Converter para DataFrame
        df_actions = pd.DataFrame(st.session_state.improvement_actions)
        
        # Estatísticas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_actions = len(df_actions)
            st.metric("Total de Ações", total_actions)
        with col2:
            pending = len(df_actions[df_actions['status'] == 'Pendente'])
            st.metric("Pendentes", pending)
        with col3:
            total_cost = df_actions['how_much'].sum()
            st.metric("Custo Total", f"R$ {total_cost:,.2f}")
        with col4:
            high_priority = len(df_actions[df_actions['priority'] == 'Alta'])
            st.metric("Alta Prioridade", high_priority)
        
        # Tabela de ações
        st.dataframe(
            df_actions[['id', 'what', 'who', 'when', 'priority', 'status', 'how_much']],
            use_container_width=True,
            hide_index=True
        )
        
        # Gráfico de Gantt
        if len(df_actions) > 0:
            st.subheader("📊 Cronograma (Gantt)")
            
            # Preparar dados para Gantt
            df_gantt = df_actions.copy()
            df_gantt['start'] = pd.to_datetime(df_gantt['when'])
            df_gantt['end'] = df_gantt['start'] + pd.Timedelta(days=7)
            
            fig_gantt = px.timeline(
                df_gantt,
                x_start='start',
                x_end='end',
                y='what',
                color='priority',
                title='Cronograma de Implementação',
                color_discrete_map={
                    'Alta': 'red',
                    'Média': 'yellow',
                    'Baixa': 'green'
                }
            )
            
            fig_gantt.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_gantt, use_container_width=True)

# Tab 4: Simulação
with tab4:
    st.header("Simulação de Melhorias")
    
    st.markdown("""
    Simule o impacto das melhorias propostas nos indicadores do processo.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Parâmetros Atuais 📊")
        st.info("Valores baseados nos dados carregados do sistema")
        
        # Mostrar valores calculados dos dados reais
        st.write(f"**Taxa de Defeitos Atual:** {current_defect_rate:.2f}%")
        defect_slider_current = st.slider(
            "Ajustar Taxa de Defeitos Atual (%)",
            min_value=0.0,
            max_value=20.0,
            value=float(current_defect_rate),
            step=0.1,
            key="current_defect",
            disabled=True
        )
        
        st.write(f"**Tempo de Ciclo Atual:** {current_cycle_time:.2f} min")
        cycle_slider_current = st.slider(
            "Ajustar Tempo de Ciclo Atual (min)",
            min_value=1,
            max_value=60,
            value=int(current_cycle_time),
            key="current_cycle",
            disabled=True
        )
        
        st.write(f"**Custo por Unidade Atual:** R$ {current_cost:.2f}")
        cost_slider_current = st.slider(
            "Ajustar Custo por Unidade Atual (R$)",
            min_value=1.0,
            max_value=100.0,
            value=float(current_cost),
            step=0.5,
            key="current_cost",
            disabled=True
        )
        
        st.write(f"**Produtividade Atual:** {current_productivity:.2f} un/hora")
        prod_slider_current = st.slider(
            "Ajustar Produtividade Atual (un/hora)",
            min_value=10,
            max_value=200,
            value=int(current_productivity),
            key="current_prod",
            disabled=True
        )
    
    with col2:
        st.subheader("Parâmetros Esperados (Após Melhorias)")
        
        expected_defect_rate = st.slider(
            "Taxa de Defeitos Esperada (%)",
            min_value=0.0,
            max_value=20.0,
            value=2.0,
            step=0.1,
            key="expected_defect"
        )
        
        expected_cycle_time = st.slider(
            "Tempo de Ciclo Esperado (min)",
            min_value=1,
            max_value=60,
            value=10,
            key="expected_cycle"
        )
        
        expected_cost = st.slider(
            "Custo por Unidade Esperado (R$)",
            min_value=1.0,
            max_value=100.0,
            value=20.0,
            step=0.5,
            key="expected_cost"
        )
        
        expected_productivity = st.slider(
            "Produtividade Esperada (un/hora)",
            min_value=10,
            max_value=200,
            value=75,
            key="expected_prod"
        )
    
    # Calcular impactos
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
    
    # Gráficos comparativos
    st.subheader("Comparação Visual")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de barras comparativo
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
        # Gráfico de radar
        categories = ['Taxa Defeitos', 'Tempo Ciclo', 'Custo', 'Produtividade']
        
        # Normalizar valores para escala 0-100 (invertendo onde menor é melhor)
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
            r=atual_norm,
            theta=categories,
            fill='toself',
            name='Atual',
            line_color='blue'
        ))
        
        fig_radar.add_trace(go.Scatterpolar(
            r=esperado_norm,
            theta=categories,
            fill='toself',
            name='Esperado',
            line_color='green'
        ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=True,
            title="Análise Radar de Desempenho",
            height=400
        )
        
        st.plotly_chart(fig_radar, use_container_width=True)
    
    # ROI Estimado
    st.subheader("💰 Retorno sobre Investimento (ROI)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        production_volume = st.number_input(
            "Volume de Produção Mensal",
            min_value=100,
            max_value=100000,
            value=10000,
            step=100
        )
    
    with col2:
        investment = st.number_input(
            "Investimento Total (R$)",
            min_value=1000.0,
            max_value=1000000.0,
            value=50000.0,
            step=1000.0
        )
    
    with col3:
        months = st.number_input(
            "Período de Análise (meses)",
            min_value=1,
            max_value=36,
            value=12
        )
    
    # Calcular ROI
    monthly_savings = production_volume * (current_cost - expected_cost)
    total_savings = monthly_savings * months
    roi = ((total_savings - investment) / investment) * 100 if investment > 0 else 0
    payback = investment / monthly_savings if monthly_savings > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Economia Mensal", f"R$ {monthly_savings:,.2f}")
    with col2:
        st.metric("Economia Total", f"R$ {total_savings:,.2f}")
    with col3:
        st.metric("ROI", f"{roi:.1f}%")
    with col4:
        st.metric("Payback", f"{payback:.1f} meses" if payback > 0 else "N/A")

# Tab 5: Análises Salvas
with tab5:
    st.header("💾 Análises Salvas")
    
    if st.session_state.improve_analyses:
        st.success(f"Total de análises salvas: {len(st.session_state.improve_analyses)}")
        
        for idx, analysis in enumerate(st.session_state.improve_analyses):
            with st.expander(f"Análise {idx + 1} - {analysis['type']} - {analysis['timestamp'][:10]}"):
                if analysis['type'] == 'pareto':
                    st.write("**Tipo:** Análise de Pareto")
                    st.write(f"**Categoria:** {analysis.get('category', 'N/A')}")
                    st.write(f"**Valor:** {analysis.get('value', 'N/A')}")
                    
                    if 'insights' in analysis:
                        st.write("**Insights:**")
                        insights = analysis['insights']
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Items para 80%", f"{insights['items_for_80']} de {insights['total_items']}")
                        with col2:
                            st.metric("Top Categoria", insights['top_category'])
                    
                    if 'data' in analysis:
                        st.write("**Dados:**")
                        st.json(analysis['data'])
                
                # Botão para remover análise
                if st.button(f"🗑️ Remover", key=f"remove_{idx}"):
                    st.session_state.improve_analyses.pop(idx)
                    st.rerun()
        
        # Exportar todas as análises
        if st.button("📥 Exportar Todas as Análises"):
            try:
                # Converter para JSON
                json_str = json.dumps(st.session_state.improve_analyses, indent=2, default=str)
                
                # Download
                st.download_button(
                    label="Download JSON",
                    data=json_str,
                    file_name=f"improve_analyses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            except Exception as e:
                st.error(f"Erro ao exportar: {e}")
    else:
        st.info("Nenhuma análise salva ainda. Complete as análises nas outras abas e salve os resultados.")

# Footer
st.markdown("---")
st.markdown("🎯 **Fase Improve** - Green Belt Project | Implementação de Melhorias")
