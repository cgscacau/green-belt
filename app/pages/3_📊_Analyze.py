import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats
import plotly.express as px
import plotly.graph_objects as go
from components.supabase_client import get_supabase_manager

st.set_page_config(page_title="Analyze", page_icon="📊", layout="wide")

# Inicializa Supabase
db = get_supabase_manager()

st.header("📊 Analyze — Análise Estatística e Identificação de Causas")

# Verifica projeto ativo
current_project_id = st.session_state.get('current_project_id')

if not current_project_id:
    st.warning("⚠️ Nenhum projeto selecionado")
    st.info("Por favor, selecione ou crie um projeto na página **Define** primeiro.")
    st.stop()

# Mostra projeto ativo
project = db.get_project(current_project_id)
if project:
    st.success(f"📂 Projeto: **{project['name']}**")
else:
    st.error("Projeto não encontrado")
    st.stop()

# Verifica se há dataset para análise
if 'analysis_df' not in st.session_state:
    st.warning("⚠️ Nenhum dataset carregado para análise")
    st.info("Vá para a página **Measure** e carregue um dataset primeiro.")
    
    # Opção de carregar último dataset
    datasets = db.list_datasets(current_project_id)
    if datasets:
        if st.button("📂 Carregar Último Dataset"):
            latest_dataset = datasets[0]
            df = pd.DataFrame(latest_dataset['data'])
            st.session_state['analysis_df'] = df
            st.session_state['analysis_dataset_id'] = latest_dataset['id']
            st.rerun()
    st.stop()

# Carrega dataset
df = st.session_state['analysis_df']

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
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🔍 Exploratória",
    "📐 Normalidade",
    "🎯 Comparações",
    "🔗 Correlações",
    "📈 Regressão",
    "💾 Análises Salvas"
])

with tab1:
    st.subheader("Análise Exploratória")
    
    if numeric_cols:
        selected_var = st.selectbox("Selecione a variável para análise", numeric_cols)
        
        if selected_var:
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown("### 📊 Estatísticas")
                
                mean_val = df[selected_var].mean()
                median_val = df[selected_var].median()
                std_val = df[selected_var].std()
                min_val = df[selected_var].min()
                max_val = df[selected_var].max()
                
                st.metric("Média", f"{mean_val:.2f}")
                st.metric("Mediana", f"{median_val:.2f}")
                st.metric("Desvio Padrão", f"{std_val:.2f}")
                st.metric("Mínimo", f"{min_val:.2f}")
                st.metric("Máximo", f"{max_val:.2f}")
                
                # Teste contra meta do projeto
                if 'taxa_defeitos' in selected_var.lower() and project.get('target_value'):
                    target = project['target_value']
                    if mean_val <= target:
                        st.success(f"✅ Média ({mean_val:.2f}) dentro da meta ({target})")
                    else:
                        st.warning(f"⚠️ Média ({mean_val:.2f}) acima da meta ({target})")
            
            with col2:
                # Histograma
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=df[selected_var],
                    nbinsx=30,
                    name='Frequência',
                    marker_color='cyan'
                ))
                
                # Adiciona linha da média
                fig.add_vline(x=mean_val, line_dash="dash", line_color="yellow",
                            annotation_text=f"Média: {mean_val:.2f}")
                
                # Adiciona meta se aplicável
                if 'taxa_defeitos' in selected_var.lower() and project.get('target_value'):
                    fig.add_vline(x=project['target_value'], line_dash="dot", line_color="red",
                                annotation_text=f"Meta: {project['target_value']}")
                
                fig.update_layout(
                    title=f"Distribuição de {selected_var}",
                    template="plotly_dark",
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Boxplot por categoria
                if categorical_cols:
                    cat_var = st.selectbox("Agrupar por", categorical_cols)
                    if cat_var:
                        fig = px.box(df, x=cat_var, y=selected_var,
                                    title=f"{selected_var} por {cat_var}",
                                    template="plotly_dark")
                        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Testes de Normalidade")
    
    if numeric_cols:
        var_to_test = st.selectbox("Variável para teste de normalidade", numeric_cols, key="norm_test")
        
        if st.button("🧪 Executar Teste de Normalidade"):
            # Remove NaN
            data = df[var_to_test].dropna()
            
            if len(data) >= 3:
                # Shapiro-Wilk
                stat_sw, p_sw = stats.shapiro(data)
                
                # Anderson-Darling
                result_ad = stats.anderson(data)
                
                # Kolmogorov-Smirnov
                stat_ks, p_ks = stats.kstest(data, 'norm', args=(data.mean(), data.std()))
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("### Shapiro-Wilk")
                    st.metric("Estatística W", f"{stat_sw:.4f}")
                    st.metric("p-valor", f"{p_sw:.4f}")
                    if p_sw > 0.05:
                        st.success("✅ Normal (p > 0.05)")
                    else:
                        st.warning("⚠️ Não-normal (p ≤ 0.05)")
                
                with col2:
                    st.markdown("### Anderson-Darling")
                    st.metric("Estatística", f"{result_ad.statistic:.4f}")
                    st.metric("Valor Crítico (5%)", f"{result_ad.critical_values[2]:.4f}")
                    if result_ad.statistic < result_ad.critical_values[2]:
                        st.success("✅ Normal")
                    else:
                        st.warning("⚠️ Não-normal")
                
                with col3:
                    st.markdown("### Kolmogorov-Smirnov")
                    st.metric("Estatística D", f"{stat_ks:.4f}")
                    st.metric("p-valor", f"{p_ks:.4f}")
                    if p_ks > 0.05:
                        st.success("✅ Normal (p > 0.05)")
                    else:
                        st.warning("⚠️ Não-normal (p ≤ 0.05)")
                
                # Q-Q Plot
                st.markdown("### Q-Q Plot")
                
                from scipy.stats import probplot
                
                fig = go.Figure()
                
                qq = probplot(data, dist="norm")
                x = qq[0][0]
                y = qq[0][1]
                
                fig.add_trace(go.Scatter(x=x, y=y, mode='markers', name='Dados',
                                        marker=dict(color='cyan')))
                
                # Linha de referência
                fig.add_trace(go.Scatter(x=x, y=x*qq[1][0] + qq[1][1],
                                        mode='lines', name='Normal Teórica',
                                        line=dict(color='red', dash='dash')))
                
                fig.update_layout(
                    title=f"Q-Q Plot - {var_to_test}",
                    xaxis_title="Quantis Teóricos",
                    yaxis_title="Quantis Amostrais",
                    template="plotly_dark"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Salvar resultado
                normality_result = {
                    'variable': var_to_test,
                    'shapiro_w': stat_sw,
                    'shapiro_p': p_sw,
                    'anderson_stat': result_ad.statistic,
                    'ks_stat': stat_ks,
                    'ks_p': p_ks,
                    'is_normal': p_sw > 0.05
                }
                
                st.session_state['last_normality_test'] = normality_result
                
                if st.button("💾 Salvar Teste de Normalidade"):
                    if db.save_report(current_project_id, 'NORMALITY_TEST', normality_result):
                        st.success("✅ Teste de normalidade salvo!")
            else:
                st.error("Dados insuficientes para teste (mínimo 3 observações)")

with tab3:
    st.subheader("Testes de Comparação")
    
    if numeric_cols and categorical_cols:
        value_col = st.selectbox("Variável dependente", numeric_cols, key="comp_val")
        group_col = st.selectbox("Variável de grupo", categorical_cols, key="comp_group")
        
        if value_col and group_col:
            groups = df[group_col].unique()
            n_groups = len(groups)
            
            st.info(f"Grupos encontrados: {n_groups} - {', '.join(map(str, groups))}")
            
            if n_groups >= 2:
                if st.button("🎯 Executar Teste de Comparação"):
                    # Prepara dados por grupo
                    group_data = [df[df[group_col] == g][value_col].dropna() for g in groups]
                    
                    # Remove grupos vazios
                    group_data = [g for g in group_data if len(g) > 0]
                    groups = [groups[i] for i, g in enumerate(group_data) if len(g) > 0]
                    
                    if len(group_data) >= 2:
                        if len(group_data) == 2:
                            # Teste t
                            st.markdown("### Teste t de Student")
                            
                            # Teste de Levene para variâncias
                            stat_levene, p_levene = stats.levene(*group_data)
                            
                            # Teste t
                            stat_t, p_t = stats.ttest_ind(group_data[0], group_data[1],
                                                         equal_var=(p_levene > 0.05))
                            
                            # Effect size (Cohen's d)
                            pooled_std = np.sqrt((group_data[0].var() + group_data[1].var()) / 2)
                            cohens_d = (group_data[0].mean() - group_data[1].mean()) / pooled_std
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("Estatística t", f"{stat_t:.4f}")
                                st.metric("p-valor", f"{p_t:.4f}")
                            
                            with col2:
                                st.metric("Cohen's d", f"{cohens_d:.4f}")
                                if abs(cohens_d) < 0.2:
                                    st.caption("Efeito pequeno")
                                elif abs(cohens_d) < 0.5:
                                    st.caption("Efeito médio")
                                else:
                                    st.caption("Efeito grande")
                            
                            with col3:
                                st.metric("Levene p-valor", f"{p_levene:.4f}")
                                st.caption("Variâncias " + ("iguais" if p_levene > 0.05 else "diferentes"))
                            
                            if p_t < 0.05:
                                st.success(f"✅ Diferença significativa entre grupos (p = {p_t:.4f})")
                            else:
                                st.info(f"ℹ️ Sem diferença significativa (p = {p_t:.4f})")
                            
                            # Salvar resultado
                            test_result = {
                                'test_type': 't-test',
                                'variable': value_col,
                                'groups': group_col,
                                't_statistic': stat_t,
                                'p_value': p_t,
                                'cohens_d': cohens_d,
                                'significant': p_t < 0.05
                            }
                        
                        else:
                            # ANOVA
                            st.markdown("### ANOVA One-Way")
                            
                            stat_f, p_f = stats.f_oneway(*group_data)
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.metric("Estatística F", f"{stat_f:.4f}")
                            with col2:
                                st.metric("p-valor", f"{p_f:.4f}")
                            
                            if p_f < 0.05:
                                st.success(f"✅ Diferença significativa entre grupos (p = {p_f:.4f})")
                                
                                # Post-hoc Tukey
                                from statsmodels.stats.multicomp import pairwise_tukeyhsd
                                
                                # Prepara dados para Tukey
                                data_for_tukey = pd.concat([
                                    pd.DataFrame({
                                        'value': group_data[i],
                                        'group': groups[i]
                                    }) for i in range(len(groups))
                                ])
                                
                                tukey = pairwise_tukeyhsd(data_for_tukey['value'],
                                                         data_for_tukey['group'],
                                                         alpha=0.05)
                                
                                st.markdown("### Teste Post-Hoc (Tukey HSD)")
                                st.text(str(tukey))
                                
                                # Salvar resultado
                                test_result = {
                                    'test_type': 'ANOVA',
                                    'variable': value_col,
                                    'groups': group_col,
                                    'f_statistic': stat_f,
                                    'p_value': p_f,
                                    'significant': p_f < 0.05,
                                    'tukey': str(tukey)
                                }
                            else:
                                st.info(f"ℹ️ Sem diferença significativa (p = {p_f:.4f})")
                                
                                test_result = {
                                    'test_type': 'ANOVA',
                                    'variable': value_col,
                                    'groups': group_col,
                                    'f_statistic': stat_f,
                                    'p_value': p_f,
                                    'significant': p_f < 0.05
                                }
                        
                        # Visualização
                        fig = px.box(df, x=group_col, y=value_col,
                                    title=f"{value_col} por {group_col}",
                                    template="plotly_dark",
                                    points="all")
                        st.plotly_chart(fig, use_container_width=True)
                        
                        if st.button("💾 Salvar Teste de Comparação"):
                            if db.save_report(current_project_id, 'COMPARISON_TEST', test_result):
                                st.success("✅ Teste de comparação salvo!")
                    else:
                        st.error("Dados insuficientes nos grupos")

with tab4:
    st.subheader("Análise de Correlação")
    
    if len(numeric_cols) >= 2:
        method = st.selectbox("Método", ["pearson", "spearman", "kendall"])
        
        if st.button("🔗 Calcular Correlações"):
            # Calcula matriz de correlação
            if method == 'pearson':
                corr_matrix = df[numeric_cols].corr(method='pearson')
            elif method == 'spearman':
                corr_matrix = df[numeric_cols].corr(method='spearman')
            else:
                corr_matrix = df[numeric_cols].corr(method='kendall')
            
            # Heatmap
            fig = px.imshow(corr_matrix,
                          labels=dict(color="Correlação"),
                          x=corr_matrix.columns,
                          y=corr_matrix.columns,
                          color_continuous_scale='RdBu',
                          zmin=-1, zmax=1,
                          title=f"Matriz de Correlação ({method.capitalize()})",
                          template="plotly_dark",
                          text_auto='.2f')
            
            fig.update_layout(width=800, height=800)
            st.plotly_chart(fig, use_container_width=True)
            
            # Correlações significativas
            st.markdown("### Correlações Mais Fortes")
            
            # Extrai correlações únicas (triangular superior)
            corr_list = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_list.append({
                        'Var1': corr_matrix.columns[i],
                        'Var2': corr_matrix.columns[j],
                        'Correlação': corr_matrix.iloc[i, j]
                    })
            
            corr_df = pd.DataFrame(corr_list)
            corr_df['Abs_Corr'] = corr_df['Correlação'].abs()
            corr_df = corr_df.sort_values('Abs_Corr', ascending=False)
            
            # Top 10 correlações
            st.dataframe(corr_df.head(10)[['Var1', 'Var2', 'Correlação']],
                        use_container_width=True,
                        hide_index=True)
            
            if st.button("💾 Salvar Análise de Correlação"):
                correlation_result = {
                    'method': method,
                    'matrix': corr_matrix.to_dict(),
                    'top_correlations': corr_df.head(10).to_dict('records')
                }
                
                if db.save_report(current_project_id, 'CORRELATION_ANALYSIS', correlation_result):
                    st.success("✅ Análise de correlação salva!")

with tab5:
    st.subheader("Análise de Regressão")
    
    if len(numeric_cols) >= 2:
        y_var = st.selectbox("Variável dependente (Y)", numeric_cols, key="reg_y")
        x_vars = st.multiselect("Variáveis independentes (X)",
                               [c for c in numeric_cols if c != y_var],
                               key="reg_x")
        
        if y_var and x_vars:
            if st.button("📈 Executar Regressão"):
                from sklearn.linear_model import LinearRegression
                from sklearn.metrics import r2_score, mean_squared_error
                
                # Prepara dados
                X = df[x_vars].dropna()
                y = df.loc[X.index, y_var]
                
                # Remove NaN de y
                valid_idx = ~y.isna()
                X = X[valid_idx]
                y = y[valid_idx]
                
                if len(X) > len(x_vars):
                    # Fit modelo
                    model = LinearRegression()
                    model.fit(X, y)
                    
                    # Predições
                    y_pred = model.predict(X)
                    
                    # Métricas
                    r2 = r2_score(y, y_pred)
                    rmse = np.sqrt(mean_squared_error(y, y_pred))
                    
                    # Coeficientes
                    coef_df = pd.DataFrame({
                        'Variável': x_vars,
                        'Coeficiente': model.coef_,
                        'Abs_Coef': np.abs(model.coef_)
                    }).sort_values('Abs_Coef', ascending=False)
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("R²", f"{r2:.4f}")
                        st.caption("Variância explicada")
                    
                    with col2:
                        st.metric("RMSE", f"{rmse:.4f}")
                        st.caption("Erro quadrático médio")
                    
                    with col3:
                        st.metric("Intercepto", f"{model.intercept_:.4f}")
                        st.caption("β₀")
                    
                    # Coeficientes
                    st.markdown("### Coeficientes")
                    st.dataframe(coef_df[['Variável', 'Coeficiente']],
                               use_container_width=True,
                               hide_index=True)
                    
                    # Gráfico de resíduos
                    residuals = y - y_pred
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=y_pred,
                        y=residuals,
                        mode='markers',
                        marker=dict(color='cyan'),
                        name='Resíduos'
                    ))
                    fig.add_hline(y=0, line_dash="dash", line_color="red")
                    fig.update_layout(
                        title="Gráfico de Resíduos",
                        xaxis_title="Valores Preditos",
                        yaxis_title="Resíduos",
                        template="plotly_dark"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    if st.button("💾 Salvar Modelo de Regressão"):
                        regression_result = {
                            'y_variable': y_var,
                            'x_variables': x_vars,
                            'r2': r2,
                            'rmse': rmse,
                            'intercept': model.intercept_,
                            'coefficients': coef_df.to_dict('records'),
                            'n_observations': len(X)
                        }
                        
                        if db.save_report(current_project_id, 'REGRESSION_MODEL', regression_result):
                            st.success("✅ Modelo de regressão salvo!")
                            st.session_state['regression_model'] = model
                else:
                    st.error("Dados insuficientes para regressão")

with tab6:
    st.subheader("💾 Análises Salvas")
    
    # Busca relatórios salvos
    reports = db.get_reports(current_project_id)
    
    if reports:
        # Filtra apenas análises estatísticas
        analysis_reports = [r for r in reports if r['report_type'] in 
                          ['NORMALITY_TEST', 'COMPARISON_TEST', 'CORRELATION_ANALYSIS', 
                           'REGRESSION_MODEL', 'DESCRIPTIVE_ANALYSIS']]
        
        if analysis_reports:
            st.markdown(f"### Total de análises salvas: {len(analysis_reports)}")
            
            # Agrupa por tipo
            report_types = {}
            for report in analysis_reports:
                report_type = report['report_type']
                if report_type not in report_types:
                    report_types[report_type] = []
                report_types[report_type].append(report)
            
            # Mostra cada tipo
            for report_type, reports_list in report_types.items():
                with st.expander(f"{report_type.replace('_', ' ').title()} ({len(reports_list)} análises)"):
                    for report in reports_list:
                        st.markdown(f"**Data:** {report['created_at'][:19]}")
                        st.json(report['content'])
                        st.markdown("---")
        else:
            st.info("Nenhuma análise estatística salva ainda.")
    else:
        st.info("Nenhum relatório encontrado para este projeto.")
