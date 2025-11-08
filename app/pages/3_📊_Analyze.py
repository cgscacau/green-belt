import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Adiciona o diretório app ao path
app_dir = Path(__file__).parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from components.stats_blocks import (
    shapiro_test, ttest_two_groups, anova_test, 
    correlation_analysis, ols_regression, levene_test
)
from components.visual_blocks import (
    scatter_with_regression, correlation_heatmap, 
    box_by_group, qq_plot, line_over_time
)

st.set_page_config(page_title="Analyze", page_icon="📊", layout="wide")

st.header("📊 Analyze — Análise Estatística e Identificação de Causas")

# Verifica se há dados disponíveis na sessão
if 'analysis_df' not in st.session_state:
    st.warning("⚠️ Nenhum dataset disponível.")
    st.info("Por favor, faça upload e processe os dados na página **Measure** primeiro.")
    
    # Botão para carregar dados de exemplo
    if st.button("🚀 Carregar Dados de Exemplo"):
        try:
            sample_path = Path(__file__).parent.parent.parent / "sample_data" / "greenpeace_example.csv"
            if sample_path.exists():
                df = pd.read_csv(sample_path)
                df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
                st.session_state['analysis_df'] = df
                st.session_state['analysis_dataset'] = "greenpeace_example"
                st.success("✅ Dados de exemplo carregados!")
                st.rerun()
            else:
                st.error("Arquivo de exemplo não encontrado.")
        except Exception as e:
            st.error(f"Erro ao carregar exemplo: {e}")
    st.stop()

# Carrega dados da sessão
df = st.session_state['analysis_df']
dataset_name = st.session_state.get('analysis_dataset', 'dataset')

# Info do dataset
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Registros", len(df))
with col2:
    st.metric("Variáveis", len(df.columns))
with col3:
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    st.metric("Numéricas", len(numeric_cols))
with col4:
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    st.metric("Categóricas", len(categorical_cols))

# Tabs de análise
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 Exploratória", 
    "📐 Normalidade", 
    "🎯 Comparações", 
    "🔗 Correlações", 
    "📈 Regressão"
])

with tab1:
    st.subheader("Análise Exploratória")
    
    if numeric_cols:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            selected_var = st.selectbox("Variável para análise", numeric_cols)
            
            if selected_var:
                st.markdown("**Estatísticas**")
                try:
                    mean_val = df[selected_var].mean()
                    median_val = df[selected_var].median()
                    std_val = df[selected_var].std()
                    min_val = df[selected_var].min()
                    max_val = df[selected_var].max()
                    cv_val = (std_val / mean_val * 100) if mean_val != 0 else 0
                    
                    st.metric("Média", f"{mean_val:.2f}")
                    st.metric("Mediana", f"{median_val:.2f}")
                    st.metric("Desvio Padrão", f"{std_val:.2f}")
                    st.metric("Mínimo", f"{min_val:.2f}")
                    st.metric("Máximo", f"{max_val:.2f}")
                    st.metric("CV%", f"{cv_val:.2f}")
                except Exception as e:
                    st.error(f"Erro ao calcular estatísticas: {e}")
        
        with col2:
            # Visualizações
            if 'date' in df.columns or 'data' in df.columns:
                date_col = 'date' if 'date' in df.columns else 'data'
                try:
                    fig = line_over_time(df, date_col, selected_var, title=f"{selected_var} ao longo do tempo")
                    st.plotly_chart(fig, use_container_width=True, key="line_plot")
                except Exception as e:
                    st.info(f"Não foi possível criar gráfico temporal")
            
            if categorical_cols:
                group_var = st.selectbox("Agrupar por", categorical_cols)
                if group_var:
                    try:
                        fig = box_by_group(df, selected_var, group_var)
                        st.plotly_chart(fig, use_container_width=True, key="box_plot")
                    except Exception as e:
                        st.error(f"Erro ao criar boxplot: {e}")
    else:
        st.warning("Nenhuma variável numérica encontrada no dataset.")

with tab2:
    st.subheader("Testes de Normalidade")
    
    if numeric_cols:
        col1, col2 = st.columns(2)
        
        with col1:
            var_to_test = st.selectbox("Variável para teste", numeric_cols, key="norm_var")
            
            if st.button("🧪 Executar Teste de Normalidade"):
                try:
                    shapiro_result = shapiro_test(df[var_to_test])
                    
                    if shapiro_result:
                        st.markdown("### Teste Shapiro-Wilk")
                        st.metric("Estatística W", f"{shapiro_result['W']:.4f}")
                        st.metric("p-valor", f"{shapiro_result['p_value']:.4f}")
                        
                        if shapiro_result['normal']:
                            st.success(f"✅ Distribuição normal (p > 0.05)")
                        else:
                            st.warning(f"⚠️ Distribuição não-normal (p ≤ 0.05)")
                        
                        st.session_state['last_normality_test'] = shapiro_result
                    else:
                        st.warning("Não foi possível executar o teste. Verifique se há dados suficientes.")
                except Exception as e:
                    st.error(f"Erro no teste de normalidade: {e}")
        
        with col2:
            if var_to_test:
                st.markdown("### Q-Q Plot")
                try:
                    fig = qq_plot(df[var_to_test], title=f"Q-Q Plot - {var_to_test}")
                    st.plotly_chart(fig, use_container_width=True, key="qq_plot")
                except Exception as e:
                    st.info("Q-Q Plot não disponível")
    else:
        st.warning("Nenhuma variável numérica disponível para teste.")

with tab3:
    st.subheader("Testes de Comparação")
    
    if numeric_cols and categorical_cols:
        col1, col2 = st.columns(2)
        
        with col1:
            value_col = st.selectbox("Variável dependente", numeric_cols, key="comp_value")
            group_col = st.selectbox("Variável de grupo", categorical_cols, key="comp_group")
            
            if value_col and group_col:
                try:
                    unique_groups = df[group_col].dropna().unique()
                    n_groups = len(unique_groups)
                    
                    st.info(f"Grupos encontrados: {n_groups}")
                    
                    if n_groups == 2:
                        if st.button("🎯 Executar Teste t"):
                            try:
                                # Teste t
                                result = ttest_two_groups(
                                    df, value_col, group_col, 
                                    unique_groups[0], unique_groups[1]
                                )
                                
                                if result:
                                    st.markdown("### Teste t de Student")
                                    
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Estatística t", f"{result['t']:.4f}")
                                    with col2:
                                        st.metric("p-valor", f"{result['p_value']:.4f}")
                                    with col3:
                                        st.metric("Cohen's d", f"{result.get('cohens_d', 0):.4f}")
                                    
                                    if result['significant']:
                                        st.success(f"✅ {result['interpretation']}")
                                    else:
                                        st.info(f"ℹ️ {result['interpretation']}")
                                    
                                    st.session_state['last_ttest'] = result
                                else:
                                    st.warning("Não foi possível executar o teste t.")
                            except Exception as e:
                                st.error(f"Erro no teste t: {e}")
                    
                    elif n_groups > 2:
                        if st.button("📊 Executar ANOVA"):
                            try:
                                result = anova_test(df, value_col, group_col)
                                
                                if result:
                                    st.markdown("### ANOVA One-Way")
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.metric("Estatística F", f"{result['F']:.4f}")
                                    with col2:
                                        st.metric("p-valor", f"{result['p_value']:.4f}")
                                    
                                    if result['significant']:
                                        st.success(f"✅ {result['interpretation']}")
                                        
                                        if result.get('tukey'):
                                            st.markdown("### Teste Post-Hoc (Tukey HSD)")
                                            st.text(result['tukey'])
                                    else:
                                        st.info(f"ℹ️ {result['interpretation']}")
                                    
                                    st.session_state['last_anova'] = result
                                else:
                                    st.warning("Não foi possível executar ANOVA.")
                            except Exception as e:
                                st.error(f"Erro na ANOVA: {e}")
                    else:
                        st.warning("Necessário pelo menos 2 grupos para comparação.")
                except Exception as e:
                    st.error(f"Erro ao processar grupos: {e}")
        
        with col2:
            if value_col and group_col:
                try:
                    fig = box_by_group(df, value_col, group_col)
                    st.plotly_chart(fig, use_container_width=True, key="comp_box_plot")
                except Exception as e:
                    st.info("Visualização não disponível")
    else:
        if not numeric_cols:
            st.warning("Nenhuma variável numérica disponível.")
        if not categorical_cols:
            st.warning("Nenhuma variável categórica disponível.")

with tab4:
    st.subheader("Análise de Correlação")
    
    if len(numeric_cols) >= 2:
        method = st.selectbox(
            "Método de correlação",
            ["pearson", "spearman", "kendall"],
            help="Pearson: linear, Spearman: monotônica, Kendall: ordinal"
        )
        
        if st.button("🔗 Calcular Correlações"):
            try:
                result = correlation_analysis(df, method=method)
                
                if result:
                    st.markdown(f"### Matriz de Correlação ({method.capitalize()})")
                    
                    # Heatmap
                    fig = correlation_heatmap(
                        result['correlation_matrix'],
                        title=f"Correlação {method.capitalize()}"
                    )
                    st.plotly_chart(fig, use_container_width=True, key="corr_heatmap")
                    
                    # Mostra matriz
                    with st.expander("Ver matriz de correlação"):
                        st.dataframe(result['correlation_matrix'].round(3))
                    
                    st.session_state['last_correlation'] = result
                else:
                    st.warning("Não foi possível calcular correlações.")
            except Exception as e:
                st.error(f"Erro na análise de correlação: {e}")
    else:
        st.warning("São necessárias pelo menos 2 variáveis numéricas para análise de correlação.")

with tab5:
    st.subheader("Análise de Regressão")
    
    if len(numeric_cols) >= 2:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            y_var = st.selectbox("Variável dependente (Y)", numeric_cols, key="reg_y")
            available_x = [col for col in numeric_cols if col != y_var]
            x_vars = st.multiselect("Variáveis independentes (X)", available_x, key="reg_x")
            
            if y_var and x_vars:
                if st.button("📈 Executar Regressão"):
                    try:
                        result = ols_regression(df, y_var, x_vars)
                        
                        if result and result.get('model'):
                            st.markdown("### Resultados da Regressão")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("R²", f"{result['r_squared']:.4f}")
                            with col2:
                                st.metric("R² Ajustado", f"{result['adj_r_squared']:.4f}")
                            with col3:
                                st.metric("p-valor", f"{result['p_value']:.4f}")
                            
                            st.session_state['last_regression'] = result
                        else:
                            st.warning("Não foi possível executar a regressão.")
                    except Exception as e:
                        st.error(f"Erro na regressão: {e}")
        
        with col2:
            if y_var and len(x_vars) == 1:
                try:
                    fig = scatter_with_regression(
                        df, x_vars[0], y_var,
                        title=f"Regressão: {y_var} ~ {x_vars[0]}"
                    )
                    st.plotly_chart(fig, use_container_width=True, key="reg_scatter")
                except Exception as e:
                    st.info("Gráfico de regressão não disponível")
    else:
        st.warning("São necessárias pelo menos 2 variáveis numéricas para regressão.")
