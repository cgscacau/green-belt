import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from scipy import stats
from datetime import datetime
import os
from supabase import create_client, Client

# Configuração da página
st.set_page_config(
    page_title="Analyze - Green Belt",
    page_icon="📊",
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

# Função para buscar dados do Supabase
@st.cache_data(ttl=300)  # Cache por 5 minutos
def fetch_measurements_from_db(project_name):
    """Busca medições do banco de dados"""
    if not supabase:
        return None
    
    try:
        response = supabase.table('measurements').select("*").eq('project_name', project_name).execute()
        if response.data:
            return pd.DataFrame(response.data)
        return None
    except Exception as e:
        st.error(f"Erro ao buscar dados: {str(e)}")
        return None

@st.cache_data(ttl=300)
def fetch_process_data_from_db(project_name):
    """Busca dados do processo do banco de dados"""
    if not supabase:
        return None
    
    try:
        response = supabase.table('process_data').select("*").eq('project_name', project_name).execute()
        if response.data:
            return pd.DataFrame(response.data)
        return None
    except Exception as e:
        st.error(f"Erro ao buscar dados do processo: {str(e)}")
        return None

# Função para salvar análises no Supabase
def save_analysis_to_db(project_name, analysis_type, results):
    """Salva resultados da análise no banco de dados"""
    if not supabase:
        return False
    
    try:
        data = {
            'project_name': project_name,
            'analysis_type': analysis_type,
            'results': results,
            'created_at': datetime.now().isoformat()
        }
        response = supabase.table('analyses').insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar análise: {str(e)}")
        return False

# Título e descrição
st.title("📊 Analyze — Análise Estatística e Identificação de Causas")

# Verificar projeto selecionado
if 'project_name' not in st.session_state:
    st.warning("⚠️ Nenhum projeto selecionado. Por favor, defina um projeto na página Define primeiro.")
    st.stop()

project_name = st.session_state.project_name
st.info(f"📁 Projeto: {project_name}")

# Buscar dados do banco
with st.spinner("Carregando dados do projeto..."):
    measurements_df = fetch_measurements_from_db(project_name)
    process_df = fetch_process_data_from_db(project_name)

# Verificar se há dados disponíveis
if measurements_df is None and process_df is None:
    st.warning("⚠️ Nenhum dataset carregado para análise")
    st.info("Vá para a página Measure e carregue um dataset primeiro.")
    
    # Opção de upload direto
    st.subheader("Ou faça upload de dados aqui:")
    uploaded_file = st.file_uploader("Escolha um arquivo CSV", type=['csv'])
    
    if uploaded_file is not None:
        try:
            data = pd.read_csv(uploaded_file)
            
            # Salvar no Supabase
            if supabase:
                for _, row in data.iterrows():
                    record = row.to_dict()
                    record['project_name'] = project_name
                    record['uploaded_at'] = datetime.now().isoformat()
                    supabase.table('process_data').insert(record).execute()
                
                st.success("✅ Dados salvos no banco de dados!")
                st.rerun()
            else:
                # Fallback para session_state se Supabase não estiver configurado
                st.session_state.process_data = data
                st.success("✅ Dados carregados na sessão!")
                st.rerun()
                
        except Exception as e:
            st.error(f"Erro ao carregar arquivo: {str(e)}")
    st.stop()

# Selecionar qual dataset usar
data = None
if measurements_df is not None and process_df is not None:
    data_source = st.selectbox(
        "Selecione a fonte de dados:",
        ["Medições (Measurements)", "Dados do Processo (Process Data)"]
    )
    data = measurements_df if "Medições" in data_source else process_df
elif measurements_df is not None:
    data = measurements_df
    st.info("Usando dados de medições")
else:
    data = process_df
    st.info("Usando dados do processo")

# Tabs para diferentes análises
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Ishikawa Diagram",
    "Pareto Analysis", 
    "Correlation Analysis",
    "Hypothesis Testing",
    "5 Whys Analysis"
])

# Tab 1: Diagrama de Ishikawa
with tab1:
    st.header("Diagrama de Ishikawa (Espinha de Peixe)")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        problem = st.text_input("Defina o problema:", value=st.session_state.get('problem_statement', ''))
        
        categories = {
            "Método": [],
            "Máquina": [],
            "Mão de obra": [],
            "Material": [],
            "Medida": [],
            "Meio ambiente": []
        }
        
        st.subheader("Adicione causas para cada categoria:")
        
        for category in categories:
            with st.expander(f"📌 {category}"):
                num_causes = st.number_input(
                    f"Número de causas para {category}",
                    min_value=0,
                    max_value=5,
                    value=1,
                    key=f"num_{category}"
                )
                
                for i in range(int(num_causes)):
                    cause = st.text_input(
                        f"Causa {i+1}:",
                        key=f"{category}_cause_{i}"
                    )
                    if cause:
                        categories[category].append(cause)
        
        if st.button("Gerar Diagrama", type="primary"):
            fig = go.Figure()
            
            # Linha principal (espinha)
            fig.add_trace(go.Scatter(
                x=[0, 10],
                y=[5, 5],
                mode='lines',
                line=dict(color='black', width=3),
                showlegend=False
            ))
            
            # Adicionar categorias e causas
            positions = [(2, 7), (4, 7), (6, 7), (2, 3), (4, 3), (6, 3)]
            
            for i, (category, causes) in enumerate(categories.items()):
                if i < len(positions):
                    x_pos, y_pos = positions[i]
                    
                    # Linha da categoria
                    fig.add_trace(go.Scatter(
                        x=[x_pos, x_pos],
                        y=[5, y_pos],
                        mode='lines+text',
                        line=dict(color='gray', width=2),
                        text=[None, category],
                        textposition='top center',
                        showlegend=False
                    ))
                    
                    # Adicionar causas
                    for j, cause in enumerate(causes):
                        cause_y = y_pos + (0.3 if y_pos > 5 else -0.3) * (j + 1)
                        fig.add_annotation(
                            x=x_pos,
                            y=cause_y,
                            text=cause,
                            showarrow=False,
                            font=dict(size=10)
                        )
            
            # Adicionar problema
            fig.add_annotation(
                x=10.5,
                y=5,
                text=f"PROBLEMA:<br>{problem}",
                showarrow=False,
                font=dict(size=12, color='red'),
                bgcolor='yellow'
            )
            
            fig.update_layout(
                title="Diagrama de Ishikawa",
                showlegend=False,
                xaxis=dict(showgrid=False, zeroline=False, visible=False),
                yaxis=dict(showgrid=False, zeroline=False, visible=False),
                height=600
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Salvar análise no banco
            if save_analysis_to_db(project_name, "ishikawa", {"problem": problem, "categories": categories}):
                st.success("✅ Análise salva no banco de dados!")
    
    with col2:
        st.info("""
        **Como usar o Diagrama de Ishikawa:**
        1. Defina claramente o problema
        2. Identifique causas potenciais em cada categoria
        3. Use brainstorming com a equipe
        4. Priorize as causas mais prováveis
        5. Valide com dados
        """)

# Tab 2: Análise de Pareto
with tab2:
    st.header("Análise de Pareto")
    
    if len(data.columns) > 0:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Seleção de colunas
            category_col = st.selectbox("Selecione a coluna de categorias:", data.columns)
            
            value_col = st.selectbox(
                "Selecione a coluna de valores (ou deixe vazio para contagem):",
                ["Contagem"] + list(data.columns),
                index=0
            )
            
            if st.button("Gerar Gráfico de Pareto", type="primary"):
                # Preparar dados
                if value_col == "Contagem":
                    pareto_data = data[category_col].value_counts().reset_index()
                    pareto_data.columns = ['Category', 'Count']
                    pareto_data = pareto_data.sort_values('Count', ascending=False)
                else:
                    pareto_data = data.groupby(category_col)[value_col].sum().reset_index()
                    pareto_data.columns = ['Category', 'Value']
                    pareto_data = pareto_data.sort_values('Value', ascending=False)
                
                # Calcular percentual acumulado
                pareto_data['Percentage'] = (pareto_data.iloc[:, 1] / pareto_data.iloc[:, 1].sum()) * 100
                pareto_data['Cumulative'] = pareto_data['Percentage'].cumsum()
                
                # Criar gráfico
                fig = go.Figure()
                
                # Barras
                fig.add_trace(go.Bar(
                    x=pareto_data['Category'],
                    y=pareto_data.iloc[:, 1],
                    name='Frequência',
                    marker_color='lightblue',
                    yaxis='y'
                ))
                
                # Linha acumulada
                fig.add_trace(go.Scatter(
                    x=pareto_data['Category'],
                    y=pareto_data['Cumulative'],
                    name='% Acumulado',
                    marker_color='red',
                    mode='lines+markers',
                    yaxis='y2'
                ))
                
                # Linha de 80%
                fig.add_hline(
                    y=80,
                    line_dash="dash",
                    line_color="green",
                    annotation_text="80%",
                    yref='y2'
                )
                
                fig.update_layout(
                    title="Gráfico de Pareto",
                    xaxis=dict(title="Categorias"),
                    yaxis=dict(title="Frequência", side='left'),
                    yaxis2=dict(title="% Acumulado", overlaying='y', side='right', range=[0, 100]),
                    hovermode='x'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Análise
                vital_few = pareto_data[pareto_data['Cumulative'] <= 80]
                st.success(f"✅ {len(vital_few)} categorias representam 80% do problema (Vital Few)")
                st.dataframe(pareto_data)
                
                # Salvar análise
                save_analysis_to_db(project_name, "pareto", pareto_data.to_dict())
        
        with col2:
            st.info("""
            **Princípio de Pareto (80/20):**
            - 80% dos problemas vêm de 20% das causas
            - Foque nos "Vital Few" vs "Trivial Many"
            - Priorize ações nas categorias principais
            """)

# Tab 3: Análise de Correlação
with tab3:
    st.header("Análise de Correlação")
    
    numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
    
    if len(numeric_cols) >= 2:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Matriz de correlação
            st.subheader("Matriz de Correlação")
            
            selected_cols = st.multiselect(
                "Selecione as variáveis para análise:",
                numeric_cols,
                default=numeric_cols[:5] if len(numeric_cols) > 5 else numeric_cols
            )
            
            if len(selected_cols) >= 2:
                corr_matrix = data[selected_cols].corr()
                
                fig = px.imshow(
                    corr_matrix,
                    labels=dict(x="Variáveis", y="Variáveis", color="Correlação"),
                    x=selected_cols,
                    y=selected_cols,
                    color_continuous_scale='RdBu',
                    zmin=-1,
                    zmax=1
                )
                
                fig.update_layout(title="Matriz de Correlação")
                st.plotly_chart(fig, use_container_width=True)
                
                # Análise de correlações fortes
                st.subheader("Correlações Significativas")
                threshold = st.slider("Threshold de correlação:", 0.0, 1.0, 0.7)
                
                strong_corr = []
                for i in range(len(corr_matrix.columns)):
                    for j in range(i+1, len(corr_matrix.columns)):
                        if abs(corr_matrix.iloc[i, j]) >= threshold:
                            strong_corr.append({
                                'Variável 1': corr_matrix.columns[i],
                                'Variável 2': corr_matrix.columns[j],
                                'Correlação': round(corr_matrix.iloc[i, j], 3)
                            })
                
                if strong_corr:
                    st.dataframe(pd.DataFrame(strong_corr))
                else:
                    st.info(f"Nenhuma correlação acima de {threshold}")
                
                # Scatter plot
                st.subheader("Gráfico de Dispersão")
                x_var = st.selectbox("Variável X:", selected_cols)
                y_var = st.selectbox("Variável Y:", [c for c in selected_cols if c != x_var])
                
                if x_var and y_var:
                    fig = px.scatter(
                        data,
                        x=x_var,
                        y=y_var,
                        trendline="ols",
                        title=f"Correlação: {x_var} vs {y_var}"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Calcular R²
                    correlation = data[x_var].corr(data[y_var])
                    r_squared = correlation ** 2
                    st.metric("R²", f"{r_squared:.3f}")
                    st.metric("Correlação", f"{correlation:.3f}")
                
                # Salvar análise
                if st.button("Salvar Análise de Correlação"):
                    save_analysis_to_db(project_name, "correlation", {
                        "correlation_matrix": corr_matrix.to_dict(),
                        "strong_correlations": strong_corr
                    })
                    st.success("✅ Análise salva!")
        
        with col2:
            st.info("""
            **Interpretação de Correlação:**
            - **1.0**: Correlação positiva perfeita
            - **0.7 a 0.9**: Correlação forte
            - **0.4 a 0.6**: Correlação moderada
            - **0.1 a 0.3**: Correlação fraca
            - **0**: Sem correlação
            - **-1.0**: Correlação negativa perfeita
            """)
    else:
        st.warning("É necessário pelo menos 2 variáveis numéricas para análise de correlação")

# Tab 4: Testes de Hipótese
with tab4:
    st.header("Testes de Hipótese")
    
    test_type = st.selectbox(
        "Selecione o tipo de teste:",
        ["Teste t (2 amostras)", "ANOVA (múltiplas amostras)", "Teste de Normalidade", "Teste Qui-Quadrado"]
    )
    
    if test_type == "Teste t (2 amostras)":
        st.subheader("Teste t de Student")
        
        col1, col2 = st.columns(2)
        
        with col1:
            numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_cols:
                value_col = st.selectbox("Variável de interesse:", numeric_cols)
                
                categorical_cols = data.select_dtypes(include=['object']).columns.tolist()
                if categorical_cols:
                    group_col = st.selectbox("Variável de agrupamento:", categorical_cols)
                    
                    unique_groups = data[group_col].unique()
                    if len(unique_groups) >= 2:
                        group1 = st.selectbox("Grupo 1:", unique_groups)
                        group2 = st.selectbox("Grupo 2:", [g for g in unique_groups if g != group1])
                        
                        alpha = st.slider("Nível de significância (α):", 0.01, 0.10, 0.05)
                        
                        if st.button("Executar Teste t", type="primary"):
                            # Preparar dados
                            data1 = data[data[group_col] == group1][value_col].dropna()
                            data2 = data[data[group_col] == group2][value_col].dropna()
                            
                            # Executar teste
                            t_stat, p_value = stats.ttest_ind(data1, data2)
                            
                            # Resultados
                            st.write("### Resultados do Teste t")
                            col_res1, col_res2 = st.columns(2)
                            
                            with col_res1:
                                st.metric("Estatística t", f"{t_stat:.4f}")
                                st.metric("Valor p", f"{p_value:.4f}")
                            
                            with col_res2:
                                st.metric(f"Média {group1}", f"{data1.mean():.2f}")
                                st.metric(f"Média {group2}", f"{data2.mean():.2f}")
                            
                            # Interpretação
                            if p_value < alpha:
                                st.error(f"""
                                **Rejeitar H₀**: Existe diferença significativa entre os grupos 
                                (p-value = {p_value:.4f} < α = {alpha})
                                """)
                            else:
                                st.success(f"""
                                **Não rejeitar H₀**: Não há diferença significativa entre os grupos
                                (p-value = {p_value:.4f} ≥ α = {alpha})
                                """)
                            
                            # Visualização
                            fig = go.Figure()
                            fig.add_trace(go.Box(y=data1, name=group1))
                            fig.add_trace(go.Box(y=data2, name=group2))
                            fig.update_layout(title=f"Comparação: {group1} vs {group2}")
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Salvar resultado
                            save_analysis_to_db(project_name, "t_test", {
                                "groups": [group1, group2],
                                "t_statistic": t_stat,
                                "p_value": p_value,
                                "alpha": alpha,
                                "conclusion": "reject" if p_value < alpha else "fail_to_reject"
                            })
        
        with col2:
            st.info("""
            **Teste t de Student:**
            - **H₀**: As médias dos grupos são iguais
            - **H₁**: As médias dos grupos são diferentes
            - **Premissas**:
                - Dados normalmente distribuídos
                - Variâncias homogêneas
                - Amostras independentes
            """)
    
    elif test_type == "ANOVA (múltiplas amostras)":
        st.subheader("Análise de Variância (ANOVA)")
        
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            value_col = st.selectbox("Variável dependente:", numeric_cols)
            
            categorical_cols = data.select_dtypes(include=['object']).columns.tolist()
            if categorical_cols:
                group_col = st.selectbox("Fator (variável categórica):", categorical_cols)
                
                if st.button("Executar ANOVA", type="primary"):
                    # Preparar dados
                    groups = []
                    labels = []
                    for group in data[group_col].unique():
                        group_data = data[data[group_col] == group][value_col].dropna()
                        if len(group_data) > 0:
                            groups.append(group_data)
                            labels.append(group)
                    
                    # Executar ANOVA
                    f_stat, p_value = stats.f_oneway(*groups)
                    
                    # Resultados
                    st.write("### Resultados da ANOVA")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Estatística F", f"{f_stat:.4f}")
                        st.metric("Valor p", f"{p_value:.4f}")
                    
                    alpha = 0.05
                    if p_value < alpha:
                        st.error(f"""
                        **Rejeitar H₀**: Existe diferença significativa entre pelo menos um par de grupos
                        (p-value = {p_value:.4f} < α = {alpha})
                        """)
                    else:
                        st.success(f"""
                        **Não rejeitar H₀**: Não há diferença significativa entre os grupos
                        (p-value = {p_value:.4f} ≥ α = {alpha})
                        """)
                    
                    # Visualização
                    fig = go.Figure()
                    for group_data, label in zip(groups, labels):
                        fig.add_trace(go.Box(y=group_data, name=label))
                    fig.update_layout(title=f"ANOVA: {value_col} por {group_col}")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Tabela de médias
                    summary = data.groupby(group_col)[value_col].agg(['mean', 'std', 'count'])
                    st.write("### Resumo por Grupo")
                    st.dataframe(summary)
                    
                    # Salvar resultado
                    save_analysis_to_db(project_name, "anova", {
                        "f_statistic": f_stat,
                        "p_value": p_value,
                        "groups": labels,
                        "summary": summary.to_dict()
                    })
    
    elif test_type == "Teste de Normalidade":
        st.subheader("Teste de Normalidade (Shapiro-Wilk)")
        
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            test_col = st.selectbox("Selecione a variável:", numeric_cols)
            
            if st.button("Executar Teste", type="primary"):
                # Preparar dados
                test_data = data[test_col].dropna()
                
                # Executar teste
                stat, p_value = stats.shapiro(test_data)
                
                # Resultados
                st.write("### Resultados do Teste de Normalidade")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Estatística W", f"{stat:.4f}")
                    st.metric("Valor p", f"{p_value:.4f}")
                
                alpha = 0.05
                if p_value > alpha:
                    st.success(f"""
                    **Dados seguem distribuição normal**
                    (p-value = {p_value:.4f} > α = {alpha})
                    """)
                else:
                    st.warning(f"""
                    **Dados NÃO seguem distribuição normal**
                    (p-value = {p_value:.4f} ≤ α = {alpha})
                    """)
                
                # Visualização
                fig = go.Figure()
                
                # Histograma
                fig.add_trace(go.Histogram(
                    x=test_data,
                    name='Dados',
                    nbinsx=30,
                    histnorm='probability density'
                ))
                
                # Curva normal teórica
                x_range = np.linspace(test_data.min(), test_data.max(), 100)
                y_normal = stats.norm.pdf(x_range, test_data.mean(), test_data.std())
                fig.add_trace(go.Scatter(
                    x=x_range,
                    y=y_normal,
                    mode='lines',
                    name='Normal Teórica',
                    line=dict(color='red')
                ))
                
                fig.update_layout(title=f"Teste de Normalidade: {test_col}")
                st.plotly_chart(fig, use_container_width=True)
                
                # Q-Q Plot
                st.write("### Q-Q Plot")
                theoretical_quantiles = stats.norm.ppf(np.linspace(0.01, 0.99, len(test_data)))
                sample_quantiles = np.sort(test_data)
                
                fig_qq = go.Figure()
                fig_qq.add_trace(go.Scatter(
                    x=theoretical_quantiles,
                    y=sample_quantiles,
                    mode='markers',
                    name='Dados'
                ))
                fig_qq.add_trace(go.Scatter(
                    x=[theoretical_quantiles.min(), theoretical_quantiles.max()],
                    y=[theoretical_quantiles.min(), theoretical_quantiles.max()],
                    mode='lines',
                    name='Linha de Referência',
                    line=dict(color='red', dash='dash')
                ))
                fig_qq.update_layout(
                    title="Q-Q Plot",
                    xaxis_title="Quantis Teóricos",
                    yaxis_title="Quantis Amostrais"
                )
                st.plotly_chart(fig_qq, use_container_width=True)

# Tab 5: Análise dos 5 Porquês
with tab5:
    st.header("Análise dos 5 Porquês")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        problem_5why = st.text_area(
            "Descreva o problema:",
            value=st.session_state.get('problem_statement', ''),
            height=100
        )
        
        st.subheader("Sequência dos Porquês")
        
        whys = []
        for i in range(5):
            why = st.text_area(
                f"Por quê {i+1}?",
                key=f"why_{i+1}",
                height=80,
                help=f"Responda: Por que {'o problema ocorre' if i == 0 else f'a resposta {i} acontece'}?"
            )
            whys.append(why)
            
            if why and i < 4:
                st.write(f"↓")
        
        root_cause = st.text_area(
            "Causa Raiz Identificada:",
            height=100,
            help="Baseado na análise dos 5 porquês, qual é a causa raiz?"
        )
        
        action_plan = st.text_area(
            "Plano de Ação Proposto:",
            height=100,
            help="Que ações podem ser tomadas para eliminar a causa raiz?"
        )
        
        if st.button("Salvar Análise dos 5 Porquês", type="primary"):
            analysis_5why = {
                "problem": problem_5why,
                "whys": whys,
                "root_cause": root_cause,
                "action_plan": action_plan,
                "timestamp": datetime.now().isoformat()
            }
            
            if save_analysis_to_db(project_name, "5_whys", analysis_5why):
                st.success("✅ Análise dos 5 Porquês salva com sucesso!")
                
                # Visualização em formato de árvore
                st.write("### Visualização da Análise")
                for i, why in enumerate(whys):
                    if why:
                        st.write(f"{'  ' * i}↳ **Por quê {i+1}?** {why}")
                
                if root_cause:
                    st.write(f"\n🎯 **Causa Raiz:** {root_cause}")
                
                if action_plan:
                    st.write(f"\n📋 **Plano de Ação:** {action_plan}")
    
    with col2:
        st.info("""
        **Técnica dos 5 Porquês:**
        1. Defina claramente o problema
        2. Pergunte "Por quê?" 5 vezes
        3. Cada resposta se torna a base para a próxima pergunta
        4. Continue até encontrar a causa raiz
        5. Desenvolva ações para eliminar a causa raiz
        
        **Dicas:**
        - Seja específico em cada resposta
        - Base-se em fatos, não suposições
        - Pode ser necessário mais ou menos que 5 porquês
        - Valide a causa raiz com dados
        """)

# Resumo das Análises
st.divider()
st.header("📊 Resumo das Análises Realizadas")

if supabase:
    try:
        analyses = supabase.table('analyses').select("*").eq('project_name', project_name).execute()
        if analyses.data:
            analyses_df = pd.DataFrame(analyses.data)
            
            # Agrupar por tipo de análise
            analysis_counts = analyses_df['analysis_type'].value_counts()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Análises", len(analyses_df))
            with col2:
                st.metric("Tipos Diferentes", len(analysis_counts))
            with col3:
                if len(analyses_df) > 0:
                    last_analysis = pd.to_datetime(analyses_df['created_at']).max()
                    st.metric("Última Análise", last_analysis.strftime("%d/%m/%Y %H:%M"))
            
            # Tabela de análises
            st.subheader("Histórico de Análises")
            display_df = analyses_df[['analysis_type', 'created_at']].copy()
            display_df['created_at'] = pd.to_datetime(display_df['created_at']).dt.strftime("%d/%m/%Y %H:%M")
            st.dataframe(display_df, use_container_width=True)
            
            # Download de relatório
            if st.button("📥 Baixar Relatório de Análises"):
                report = {
                    "project_name": project_name,
                    "total_analyses": len(analyses_df),
                    "analysis_types": analysis_counts.to_dict(),
                    "analyses": analyses_df.to_dict('records')
                }
                
                st.download_button(
                    label="Download JSON",
                    data=pd.DataFrame(report).to_json(),
                    file_name=f"analises_{project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        else:
            st.info("Nenhuma análise realizada ainda para este projeto.")
    except Exception as e:
        st.error(f"Erro ao buscar histórico de análises: {str(e)}")
else:
    st.warning("Supabase não configurado. Histórico de análises não disponível.")

# Footer
st.divider()
st.caption("💡 **Dica:** Complete todas as análises antes de prosseguir para a fase Improve")
