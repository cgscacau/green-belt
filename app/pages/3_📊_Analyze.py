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
    
    # Primeiro, tentar carregar dados do Supabase
    data = None
    data_source = None
    
    # Buscar dados salvos no projeto
    if supabase:
        try:
            # Buscar dados do processo salvos
            response = supabase.table('process_data').select("*").eq('project_name', project_name).order('uploaded_at', desc=True).limit(1).execute()
            
            if response.data and len(response.data) > 0:
                st.info("📂 Dados encontrados no projeto")
                
                # Extrair o JSON data
                data_json = response.data[0].get('data', None)
                
                if data_json:
                    # Converter JSON para DataFrame
                    if isinstance(data_json, list):
                        data = pd.DataFrame(data_json)
                        data_source = "Supabase"
                        st.success(f"✅ Dados carregados do banco: {len(data)} registros")
                    elif isinstance(data_json, dict):
                        data = pd.DataFrame(data_json)
                        data_source = "Supabase"
                        st.success(f"✅ Dados carregados do banco")
                    
                    # Mostrar preview dos dados
                    with st.expander("Ver dados carregados"):
                        st.dataframe(data.head(), use_container_width=True)
        
        except Exception as e:
            st.error(f"Erro ao buscar dados: {str(e)}")
    
    # Opção de upload se não houver dados ou usuário quiser substituir
    st.subheader("📤 Upload de Dados")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        uploaded_file = st.file_uploader(
            "Faça upload de um arquivo CSV (opcional - sobrescreve dados existentes)",
            type=['csv'],
            key="pareto_upload"
        )
    
    with col2:
        if data is not None:
            st.metric("Fonte Atual", data_source)
            st.metric("Registros", len(data))
    
    # Se fez upload, usar os novos dados
    if uploaded_file is not None:
        try:
            new_data = pd.read_csv(uploaded_file)
            
            # Perguntar se quer salvar no Supabase
            if supabase:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Salvar no projeto", type="primary"):
                        # Salvar no process_data
                        data_json = new_data.to_dict('records')
                        record = {
                            'project_name': project_name,
                            'data': data_json,
                            'data_type': 'pareto_analysis',
                            'collection_date': datetime.now().date().isoformat(),
                            'uploaded_at': datetime.now().isoformat()
                        }
                        
                        try:
                            response = supabase.table('process_data').insert(record).execute()
                            st.success("✅ Dados salvos no projeto!")
                            data = new_data
                            data_source = "Upload + Supabase"
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar: {str(e)}")
                
                with col2:
                    if st.button("📊 Usar sem salvar"):
                        data = new_data
                        data_source = "Upload temporário"
            else:
                data = new_data
                data_source = "Upload local"
                
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {str(e)}")
    
    # Análise de Pareto se houver dados
    if data is not None and len(data.columns) > 0:
        st.divider()
        st.subheader("📊 Configurar Análise de Pareto")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Seleção de colunas
            category_col = st.selectbox(
                "Selecione a coluna de categorias:",
                data.columns,
                key="pareto_category"
            )
            
            value_col = st.selectbox(
                "Selecione a coluna de valores (ou use Contagem):",
                ["Contagem"] + list(data.columns),
                index=0,
                key="pareto_value"
            )
            
            # Filtros opcionais
            with st.expander("⚙️ Filtros Avançados"):
                # Permitir filtrar dados antes da análise
                filter_col = st.selectbox(
                    "Filtrar por coluna (opcional):",
                    ["Nenhum"] + list(data.columns)
                )
                
                if filter_col != "Nenhum" and filter_col in data.columns:
                    unique_vals = data[filter_col].unique()
                    selected_vals = st.multiselect(
                        f"Valores de {filter_col}:",
                        unique_vals,
                        default=unique_vals[:5] if len(unique_vals) > 5 else unique_vals
                    )
                    if selected_vals:
                        data = data[data[filter_col].isin(selected_vals)]
                        st.info(f"Dados filtrados: {len(data)} registros")
        
        with col2:
            st.info("""
            **📚 Princípio de Pareto:**
            - 80% dos efeitos vêm de 20% das causas
            - Identifica os "poucos vitais"
            - Prioriza ações de melhoria
            
            **Como usar:**
            1. Selecione a categoria a analisar
            2. Escolha o valor ou use contagem
            3. Analise o gráfico gerado
            """)
        
        # Botão para gerar análise
        if st.button("🎯 Gerar Análise de Pareto", type="primary", use_container_width=True):
            
            # Preparar dados para Pareto
            if value_col == "Contagem":
                pareto_data = data[category_col].value_counts().reset_index()
                pareto_data.columns = ['Categoria', 'Frequência']
                value_column = 'Frequência'
            else:
                pareto_data = data.groupby(category_col)[value_col].sum().reset_index()
                pareto_data.columns = ['Categoria', 'Valor']
                value_column = 'Valor'
            
            # Ordenar por valor decrescente
            pareto_data = pareto_data.sort_values(by=value_column, ascending=False)
            
            # Calcular percentual e acumulado
            total = pareto_data[value_column].sum()
            pareto_data['Percentual'] = (pareto_data[value_column] / total) * 100
            pareto_data['Acumulado'] = pareto_data['Percentual'].cumsum()
            
            # Identificar os "vital few" (80%)
            vital_few_index = (pareto_data['Acumulado'] <= 80).sum()
            if vital_few_index == 0:
                vital_few_index = 1
            
            # Criar gráfico de Pareto
            fig = go.Figure()
            
            # Barras
            colors = ['red' if i < vital_few_index else 'lightblue' 
                     for i in range(len(pareto_data))]
            
            fig.add_trace(go.Bar(
                x=pareto_data['Categoria'],
                y=pareto_data[value_column],
                name=value_column,
                marker_color=colors,
                yaxis='y',
                text=pareto_data[value_column],
                texttemplate='%{text:.0f}',
                textposition='outside'
            ))
            
            # Linha acumulada
            fig.add_trace(go.Scatter(
                x=pareto_data['Categoria'],
                y=pareto_data['Acumulado'],
                name='% Acumulado',
                mode='lines+markers+text',
                line=dict(color='darkgreen', width=2),
                marker=dict(size=8),
                yaxis='y2',
                text=pareto_data['Acumulado'].round(1),
                texttemplate='%{text:.1f}%',
                textposition='top center'
            ))
            
            # Linha de referência 80%
            fig.add_hline(
                y=80,
                line_dash="dash",
                line_color="orange",
                line_width=2,
                annotation_text="80% (Vital Few)",
                annotation_position="right",
                yref='y2'
            )
            
            # Layout
            fig.update_layout(
                title=f"Gráfico de Pareto - {category_col}",
                xaxis=dict(
                    title="Categorias",
                    tickangle=-45
                ),
                yaxis=dict(
                    title=value_column,
                    side='left'
                ),
                yaxis2=dict(
                    title="% Acumulado",
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
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Análise dos resultados
            st.divider()
            st.subheader("📋 Análise dos Resultados")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Total de Categorias",
                    len(pareto_data)
                )
            
            with col2:
                st.metric(
                    "Vital Few (80%)",
                    f"{vital_few_index} categorias",
                    f"{(vital_few_index/len(pareto_data)*100):.1f}% do total"
                )
            
            with col3:
                st.metric(
                    "Maior Contribuidor",
                    pareto_data.iloc[0]['Categoria'],
                    f"{pareto_data.iloc[0]['Percentual']:.1f}%"
                )
            
            # Tabela com os Vital Few
            st.subheader("🎯 Categorias Prioritárias (Vital Few)")
            vital_few_data = pareto_data.iloc[:vital_few_index].copy()
            vital_few_data['Percentual'] = vital_few_data['Percentual'].round(2)
            vital_few_data['Acumulado'] = vital_few_data['Acumulado'].round(2)
            
            st.dataframe(
                vital_few_data,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Categoria": st.column_config.TextColumn("Categoria", width="medium"),
                    value_column: st.column_config.NumberColumn(value_column, format="%.0f"),
                    "Percentual": st.column_config.NumberColumn("% Individual", format="%.2f%%"),
                    "Acumulado": st.column_config.NumberColumn("% Acumulado", format="%.2f%%")
                }
            )
            
            # Recomendações
            st.subheader("💡 Recomendações")
            st.success(f"""
            **Foque nas {vital_few_index} categorias principais:**
            - Elas representam {vital_few_data['Acumulado'].iloc[-1]:.1f}% do problema
            - Priorize ações de melhoria nestas categorias
            - Maior impacto com menor esforço
            """)
            
            # Salvar análise no banco
            if save_analysis_to_db(project_name, "pareto", {
                "data": pareto_data.to_dict(),
                "vital_few": vital_few_index,
                "category_column": category_col,
                "value_column": value_col,
                "timestamp": datetime.now().isoformat()
            }):
                st.success("✅ Análise salva no banco de dados!")
            
            # Opção de download
            csv = pareto_data.to_csv(index=False)
            st.download_button(
                label="📥 Download Análise CSV",
                data=csv,
                file_name=f"pareto_{project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    elif data is None:
        st.warning("⚠️ Nenhum dado disponível para análise")
        st.info("""
        **Para realizar a análise de Pareto:**
        1. Faça upload de um arquivo CSV com seus dados, ou
        2. Carregue dados salvos anteriormente na fase Measure
        """)
        
        # Botão para ir para a página Measure
        if st.button("📏 Ir para página Measure"):
            st.switch_page("pages/2_📏_Measure.py")


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
