import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from app.components.upload_and_store import init_catalog, load_dataset, list_datasets, RESULTS
from app.components.stats_blocks import (
    shapiro_test, ttest_two_groups, anova_test, 
    correlation_analysis, ols_regression, levene_test
)
from app.components.visual_blocks import (
    scatter_with_regression, correlation_heatmap, 
    box_by_group, qq_plot, line_over_time
)
from app.components.reports import render_html_report, save_analysis_manifest

st.set_page_config(page_title="Analyze", page_icon="📊", layout="wide")
init_catalog()

st.header("📊 Analyze — Análise Estatística e Identificação de Causas")

# Seleção de dataset
datasets_df = list_datasets()

if datasets_df.empty:
    st.warning("⚠️ Nenhum dataset disponível. Por favor, faça upload na página Measure primeiro.")
    st.stop()

selected_dataset = st.selectbox(
    "Selecione o dataset para análise",
    datasets_df['name'].unique(),
    help="Escolha o dataset que foi padronizado na fase Measure"
)

df = load_dataset(selected_dataset)

if df.empty:
    st.error("Erro ao carregar dataset.")
    st.stop()

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
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
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
                # Estatísticas básicas
                st.markdown("**Estatísticas**")
                stats_dict = {
                    "Média": df[selected_var].mean(),
                    "Mediana": df[selected_var].median(),
                    "Desvio Padrão": df[selected_var].std(),
                    "Mínimo": df[selected_var].min(),
                    "Máximo": df[selected_var].max(),
                    "CV%": (df[selected_var].std() / df[selected_var].mean() * 100)
                }
                
                for key, value in stats_dict.items():
                    st.metric(key, f"{value:.2f}")
        
        with col2:
            # Visualizações
            if 'date' in df.columns:
                fig = line_over_time(df, 'date', selected_var, title=f"{selected_var} ao longo do tempo")
                st.plotly_chart(fig, use_container_width=True)
            
            if categorical_cols:
                group_var = st.selectbox("Agrupar por", categorical_cols)
                if group_var:
                    fig = box_by_group(df, selected_var, group_var)
                    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Testes de Normalidade")
    
    if numeric_cols:
        col1, col2 = st.columns(2)
        
        with col1:
            var_to_test = st.selectbox("Variável para teste", numeric_cols, key="norm_var")
            
            if st.button("🧪 Executar Teste de Normalidade"):
                # Shapiro-Wilk
                shapiro_result = shapiro_test(df[var_to_test])
                
                if shapiro_result:
                    st.markdown("### Teste Shapiro-Wilk")
                    st.metric("Estatística W", f"{shapiro_result['W']:.4f}")
                    st.metric("p-valor", f"{shapiro_result['p_value']:.4f}")
                    
                    if shapiro_result['normal']:
                        st.success(f"✅ Distribuição normal (p > 0.05)")
                    else:
                        st.warning(f"⚠️ Distribuição não-normal (p ≤ 0.05)")
                    
                    # Salva resultado
                    st.session_state['last_normality_test'] = shapiro_result
        
        with col2:
            if var_to_test:
                # Q-Q Plot
                st.markdown("### Q-Q Plot")
                fig = qq_plot(df[var_to_test], title=f"Q-Q Plot - {var_to_test}")
                st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Testes de Comparação")
    
    if numeric_cols and categorical_cols:
        col1, col2 = st.columns(2)
        
        with col1:
            value_col = st.selectbox("Variável dependente", numeric_cols, key="comp_value")
            group_col = st.selectbox("Variável de grupo", categorical_cols, key="comp_group")
            
            if value_col and group_col:
                unique_groups = df[group_col].unique()
                n_groups = len(unique_groups)
                
                st.info(f"Grupos encontrados: {n_groups}")
                
                if n_groups == 2:
                    # Teste t
                    if st.button("🎯 Executar Teste t"):
                        # Teste de Levene primeiro
                        levene_result = levene_test(df, value_col, group_col)
                        
                        st.markdown("### Teste de Levene (Homogeneidade)")
                        if levene_result:
                            st.metric("p-valor", f"{levene_result['p_value']:.4f}")
                            st.caption(levene_result['interpretation'])
                        
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
                                st.metric("Cohen's d", f"{result['cohens_d']:.4f}")
                            
                            if result['significant']:
                                st.success(f"✅ {result['interpretation']}")
                            else:
                                st.info(f"ℹ️ {result['interpretation']}")
                            
                            st.session_state['last_ttest'] = result
                
                elif n_groups > 2:
                    # ANOVA
                    if st.button("📊 Executar ANOVA"):
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
                                
                                # Mostra Tukey post-hoc
                                if result['tukey']:
                                    st.markdown("### Teste Post-Hoc (Tukey HSD)")
                                    st.text(result['tukey'])
                            else:
                                st.info(f"ℹ️ {result['interpretation']}")
                            
                            st.session_state['last_anova'] = result
        
        with col2:
            if value_col and group_col:
                # Visualização
                fig = box_by_group(df, value_col, group_col)
                st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("Análise de Correlação")
    
    if len(numeric_cols) >= 2:
        method = st.selectbox(
            "Método de correlação",
            ["pearson", "spearman", "kendall"],
            help="Pearson: linear, Spearman: monotônica, Kendall: ordinal"
        )
        
        if st.button("🔗 Calcular Correlações"):
            result = correlation_analysis(df, method=method)
            
            if result:
                st.markdown(f"### Matriz de Correlação ({method.capitalize()})")
                
                # Heatmap
                fig = correlation_heatmap(
                    result['correlation_matrix'],
                    title=f"Correlação {method.capitalize()}"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Correlações significativas
                st.markdown("### Correlações Significativas (p < 0.05)")
                
                corr_matrix = result['correlation_matrix']
                p_values = result['p_values']
                
                significant_corrs = []
                for i in range(len(corr_matrix.columns)):
                    for j in range(i+1, len(corr_matrix.columns)):
                        if p_values.iloc[i, j] < 0.05:
                            significant_corrs.append({
                                'Var1': corr_matrix.columns[i],
                                'Var2': corr_matrix.columns[j],
                                'Correlação': corr_matrix.iloc[i, j],
                                'p-valor': p_values.iloc[i, j]
                            })
                
                if significant_corrs:
                    sig_df = pd.DataFrame(significant_corrs)
                    sig_df = sig_df.sort_values('Correlação', key=abs, ascending=False)
                    st.dataframe(sig_df, use_container_width=True)
                else:
                    st.info("Nenhuma correlação significativa encontrada.")
                
                st.session_state['last_correlation'] = result

with tab5:
    st.subheader("Análise de Regressão")
    
    if len(numeric_cols) >= 2:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            y_var = st.selectbox("Variável dependente (Y)", numeric_cols)
            x_vars = st.multiselect(
                "Variáveis independentes (X)",
                [col for col in numeric_cols if col != y_var]
            )
            
            if y_var and x_vars:
                if st.button("📈 Executar Regressão"):
                    result = ols_regression(df, y_var, x_vars)
                    
                    if result and result['model']:
                        st.markdown("### Resultados da Regressão")
                        
                        # Métricas principais
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("R²", f"{result['r_squared']:.4f}")
                        with col2:
                            st.metric("R² Ajustado", f"{result['adj_r_squared']:.4f}")
                        with col3:
                            st.metric("p-valor (modelo)", f"{result['p_value']:.4f}")
                        
                        # Coeficientes
                        st.markdown("### Coeficientes")
                        coef_df = pd.DataFrame({
                            'Variável': list(result['coefficients'].keys()),
                            'Coeficiente': list(result['coefficients'].values()),
                            'p-valor': list(result['p_values_coef'].values())
                        })
                        
                        # Destaca significativos
                        def highlight_significant(val):
                            if isinstance(val, float) and val < 0.05:
                                return 'background-color: #2e7d32'
                            return ''
                        
                        styled_df = coef_df.style.applymap(
                            highlight_significant,
                            subset=['p-valor']
                        )
                        st.dataframe(styled_df, use_container_width=True)
                        
                        # Diagnósticos
                        st.markdown("### Diagnósticos")
                        if result['residuals_normal']:
                            st.success("✅ Resíduos normalmente distribuídos")
                        else:
                            st.warning("⚠️ Resíduos não-normais")
                        
                        st.metric(
                            "Durbin-Watson",
                            f"{result['durbin_watson']:.4f}",
                            help="Valores próximos a 2 indicam ausência de autocorrelação"
                        )
                        
                        # Sumário completo
                        with st.expander("Sumário Completo do Modelo"):
                            st.text(str(result['model'].summary()))
                        
                        st.session_state['last_regression'] = result
        
        with col2:
            if y_var and len(x_vars) == 1:
                # Scatter plot para regressão simples
                fig = scatter_with_regression(
                    df, x_vars[0], y_var,
                    title=f"Regressão: {y_var} ~ {x_vars[0]}"
                )
                st.plotly_chart(fig, use_container_width=True)

# Botão para gerar relatório
st.divider()

if st.button("📄 Gerar Relatório de Análise", type="primary"):
    # Coleta resultados salvos
    results_summary = []
    
    if 'last_normality_test' in st.session_state:
        results_summary.append(
            f"Teste de Normalidade: {'Normal' if st.session_state['last_normality_test']['normal'] else 'Não-normal'}"
        )
    
    if 'last_ttest' in st.session_state:
        results_summary.append(
            f"Teste t: {'Significativo' if st.session_state['last_ttest']['significant'] else 'Não significativo'}"
        )
    
    if 'last_anova' in st.session_state:
        results_summary.append(
            f"ANOVA: {'Significativo' if st.session_state['last_anova']['significant'] else 'Não significativo'}"
        )
    
    # Gera relatório
    html_path = RESULTS / f"analyze_report_{selected_dataset}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.html"
    
    metrics = [
        {"label": "Dataset", "value": selected_dataset},
        {"label": "Registros Analisados", "value": str(len(df))},
        {"label": "Testes Executados", "value": str(len(results_summary))}
    ]
    
    html = render_html_report(
        title=f"Relatório de Análise - {selected_dataset}",
        project="DMAIC Greenpeace",
        summary="Análise estatística completa incluindo testes de normalidade, comparações e correlações.",
        metrics=metrics,
        conclusions="\n".join(results_summary) if results_summary else "Análises em andamento.",
        recommendations=[
            "Verificar pressupostos estatísticos antes de conclusões",
            "Considerar transformações se dados não-normais",
            "Validar resultados com conhecimento do domínio"
        ],
        out_html=html_path
    )
    
    st.success("✅ Relatório de análise gerado com sucesso!")
    
    # Salva manifesto
    manifest_id, _ = save_analysis_manifest(
        phase="analyze",
        dataset_id=selected_dataset,
        parameters={"tests_executed": results_summary},
        results={"report_path": str(html_path)}
    )
