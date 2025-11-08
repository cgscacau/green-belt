import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import io
from components.supabase_client import get_supabase_manager

st.set_page_config(page_title="Measure", page_icon="📏", layout="wide")

# Inicializa Supabase
db = get_supabase_manager()

st.header("📏 Measure — Coleta, Validação e Padronização de Dados")

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

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📤 Upload", "📊 Validação", "📈 Estatísticas", "🗄️ Datasets Salvos"])

with tab1:
    st.subheader("Upload de Dados")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Opção de usar dados de exemplo
        use_sample = st.checkbox("Usar dados de exemplo")
        
        if use_sample:
            # Gera dados de exemplo de defeitos
            import numpy as np
            from datetime import datetime, timedelta
            
            np.random.seed(42)
            dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
            
            sample_data = pd.DataFrame({
                'data': dates,
                'lote': [f'L{i:04d}' for i in range(1, 101)],
                'turno': np.random.choice(['Manhã', 'Tarde', 'Noite'], 100),
                'operador': np.random.choice(['João', 'Maria', 'Pedro', 'Ana', 'Carlos'], 100),
                'producao': np.random.randint(800, 1200, 100),
                'defeitos': np.random.poisson(15, 100),  # Média de 15 defeitos
                'retrabalho': np.random.poisson(5, 100),   # Média de 5 retrabalhos
                'temperatura': np.random.normal(25, 2, 100),
                'umidade': np.random.normal(60, 5, 100),
                'velocidade_linha': np.random.normal(100, 10, 100)
            })
            
            # Calcula taxa de defeitos
            sample_data['taxa_defeitos'] = (sample_data['defeitos'] / sample_data['producao'] * 100).round(2)
            sample_data['taxa_retrabalho'] = (sample_data['retrabalho'] / sample_data['producao'] * 100).round(2)
            
            st.success("Dados de exemplo carregados!")
            st.dataframe(sample_data.head(10), use_container_width=True)
            
            dataset_name = st.text_input("Nome do dataset", value="dados_producao_exemplo")
            
            if st.button("💾 Salvar Dataset de Exemplo", type="primary"):
                dataset_id = db.save_dataset(current_project_id, dataset_name, sample_data)
                if dataset_id:
                    st.success(f"✅ Dataset salvo com sucesso! ID: {dataset_id[:8]}...")
                    st.session_state['last_dataset_id'] = dataset_id
                    st.session_state['current_df'] = sample_data
                    st.balloons()
        else:
            # Upload de arquivo real
            uploaded_file = st.file_uploader(
                "Envie arquivo CSV ou Excel",
                type=["csv", "xlsx", "xls"],
                help="Máximo 200MB"
            )
            
            if uploaded_file:
                try:
                    # Lê o arquivo
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)
                    
                    st.success(f"✅ Arquivo carregado: {uploaded_file.name}")
                    st.dataframe(df.head(10), use_container_width=True)
                    
                    dataset_name = st.text_input(
                        "Nome do dataset",
                        value=uploaded_file.name.split('.')[0]
                    )
                    
                    if st.button("💾 Salvar Dataset", type="primary"):
                        dataset_id = db.save_dataset(current_project_id, dataset_name, df)
                        if dataset_id:
                            st.success(f"✅ Dataset salvo com sucesso! ID: {dataset_id[:8]}...")
                            st.session_state['last_dataset_id'] = dataset_id
                            st.session_state['current_df'] = df
                            st.balloons()
                            
                except Exception as e:
                    st.error(f"Erro ao processar arquivo: {e}")
    
    with col2:
        st.info("""
        **Formatos aceitos:**
        - CSV (vírgula ou ponto-vírgula)
        - Excel (.xlsx, .xls)
        
        **Dados recomendados:**
        - Data/Timestamp
        - Quantidade produzida
        - Quantidade de defeitos
        - Tipo de defeito
        - Turno/Operador
        - Variáveis de processo
        """)

with tab2:
    st.subheader("Validação e Análise de Qualidade")
    
    # Lista datasets do projeto
    datasets = db.list_datasets(current_project_id)
    
    if datasets:
        # Seletor de dataset
        dataset_names = [f"{ds['name']} ({ds['created_at'][:10]})" for ds in datasets]
        selected_idx = st.selectbox("Selecione o dataset", range(len(datasets)), format_func=lambda x: dataset_names[x])
        selected_dataset = datasets[selected_idx]
        
        # Carrega dataset
        df = pd.DataFrame(selected_dataset['data'])
        
        if not df.empty:
            st.markdown(f"**Dataset:** {selected_dataset['name']}")
            st.markdown(f"**Registros:** {len(df)} | **Colunas:** {len(df.columns)}")
            
            # Validação
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total de Registros", len(df))
            
            with col2:
                missing = df.isnull().sum().sum()
                st.metric("Valores Ausentes", missing)
            
            with col3:
                duplicates = df.duplicated().sum()
                st.metric("Linhas Duplicadas", duplicates)
            
            with col4:
                completeness = (1 - missing / df.size) * 100
                st.metric("Completude", f"{completeness:.1f}%")
            
            # Análise de qualidade por coluna
            st.markdown("### 📊 Qualidade dos Dados por Campo")
            
            quality_df = pd.DataFrame({
                'Campo': df.columns,
                'Tipo': df.dtypes.astype(str),
                'Valores Únicos': df.nunique(),
                'Ausentes': df.isnull().sum(),
                '% Ausentes': (df.isnull().sum() / len(df) * 100).round(2),
                'Exemplo': [str(df[col].dropna().iloc[0]) if not df[col].dropna().empty else 'N/A' for col in df.columns]
            })
            
            st.dataframe(quality_df, use_container_width=True, hide_index=True)
            
            # Identificação de outliers
            st.markdown("### 🔍 Detecção de Outliers")
            
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            
            if numeric_cols:
                selected_col = st.selectbox("Selecione a coluna para análise de outliers", numeric_cols)
                
                if selected_col:
                    from scipy import stats
                    import numpy as np
                    
                    # Método IQR
                    Q1 = df[selected_col].quantile(0.25)
                    Q3 = df[selected_col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    
                    outliers = df[(df[selected_col] < lower_bound) | (df[selected_col] > upper_bound)]
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Outliers Detectados", len(outliers))
                        st.caption(f"Método: IQR (1.5×)")
                    
                    with col2:
                        st.metric("% Outliers", f"{len(outliers)/len(df)*100:.2f}%")
                        st.caption(f"Limite inferior: {lower_bound:.2f}")
                    
                    with col3:
                        z_scores = np.abs(stats.zscore(df[selected_col].dropna()))
                        outliers_z = len(z_scores[z_scores > 3])
                        st.metric("Outliers (Z-score > 3)", outliers_z)
                        st.caption(f"Limite superior: {upper_bound:.2f}")
                    
                    if len(outliers) > 0:
                        with st.expander(f"Ver {len(outliers)} outliers"):
                            st.dataframe(outliers, use_container_width=True)
            
            # Salvar dataset validado
            if st.button("✅ Aprovar Dataset para Análise", type="primary"):
                st.session_state['analysis_dataset_id'] = selected_dataset['id']
                st.session_state['analysis_df'] = df
                st.success("Dataset aprovado e disponível para análise!")
    else:
        st.info("Nenhum dataset encontrado. Faça upload na aba 'Upload'.")

with tab3:
    st.subheader("Análise Estatística Descritiva")
    
    # Verifica se há dataset para análise
    if 'analysis_df' in st.session_state:
        df = st.session_state['analysis_df']
        
        st.markdown(f"**Analisando:** {len(df)} registros")
        
        # Estatísticas descritivas
        numeric_df = df.select_dtypes(include=['number'])
        
        if not numeric_df.empty:
            st.markdown("### 📊 Estatísticas Descritivas")
            
            stats_df = numeric_df.describe().T
            stats_df['CV%'] = (numeric_df.std() / numeric_df.mean() * 100).round(2)
            stats_df['IQR'] = numeric_df.quantile(0.75) - numeric_df.quantile(0.25)
            
            st.dataframe(stats_df, use_container_width=True)
            
            # Análise específica de defeitos
            if 'taxa_defeitos' in df.columns:
                st.markdown("### 🎯 Análise de Defeitos")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Taxa Média de Defeitos", f"{df['taxa_defeitos'].mean():.2f}%")
                    st.caption(f"Desvio: {df['taxa_defeitos'].std():.2f}%")
                
                with col2:
                    st.metric("Taxa Máxima", f"{df['taxa_defeitos'].max():.2f}%")
                    st.caption(f"Data: {df.loc[df['taxa_defeitos'].idxmax(), 'data'] if 'data' in df.columns else 'N/A'}")
                
                with col3:
                    st.metric("Taxa Mínima", f"{df['taxa_defeitos'].min():.2f}%")
                    st.caption(f"Data: {df.loc[df['taxa_defeitos'].idxmin(), 'data'] if 'data' in df.columns else 'N/A'}")
                
                with col4:
                    capability = (df['taxa_defeitos'] <= project['target_value']).mean() * 100 if project.get('target_value') else 0
                    st.metric("% Dentro da Meta", f"{capability:.1f}%")
                    st.caption(f"Meta: ≤ {project.get('target_value', 'N/A')}%")
            
            # Análise por categoria
            categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
            
            if categorical_cols and numeric_cols:
                st.markdown("### 📈 Análise por Categoria")
                
                cat_col = st.selectbox("Agrupar por", categorical_cols)
                metric_col = st.selectbox("Métrica", numeric_cols)
                
                if cat_col and metric_col:
                    grouped = df.groupby(cat_col)[metric_col].agg(['mean', 'std', 'count']).round(2)
                    grouped.columns = ['Média', 'Desvio Padrão', 'Quantidade']
                    grouped = grouped.sort_values('Média', ascending=False)
                    
                    st.dataframe(grouped, use_container_width=True)
                    
                    # Gráfico de barras
                    import plotly.express as px
                    
                    fig = px.bar(
                        grouped.reset_index(),
                        x=cat_col,
                        y='Média',
                        error_y='Desvio Padrão',
                        title=f'Média de {metric_col} por {cat_col}',
                        template='plotly_dark'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # Salvar análise
            if st.button("💾 Salvar Análise Descritiva"):
                analysis_report = {
                    'statistics': stats_df.to_dict(),
                    'summary': {
                        'total_records': len(df),
                        'numeric_columns': len(numeric_cols),
                        'categorical_columns': len(categorical_cols),
                        'missing_values': df.isnull().sum().sum(),
                        'completeness': (1 - df.isnull().sum().sum() / df.size) * 100
                    }
                }
                
                if 'taxa_defeitos' in df.columns:
                    analysis_report['defects_analysis'] = {
                        'mean_rate': df['taxa_defeitos'].mean(),
                        'std_rate': df['taxa_defeitos'].std(),
                        'max_rate': df['taxa_defeitos'].max(),
                        'min_rate': df['taxa_defeitos'].min(),
                        'within_target': capability if 'capability' in locals() else None
                    }
                
                if db.save_report(current_project_id, 'DESCRIPTIVE_ANALYSIS', analysis_report):
                    st.success("✅ Análise descritiva salva no banco de dados!")
    else:
        st.info("Aprove um dataset na aba 'Validação' primeiro.")

with tab4:
    st.subheader("🗄️ Datasets Salvos no Projeto")
    
    datasets = db.list_datasets(current_project_id)
    
    if datasets:
        # Cria DataFrame para visualização
        datasets_info = []
        for ds in datasets:
            datasets_info.append({
                'Nome': ds['name'],
                'Registros': ds['row_count'],
                'Criado em': ds['created_at'][:19],
                'ID': ds['id'][:8] + '...'
            })
        
        datasets_df = pd.DataFrame(datasets_info)
        
        # Mostra tabela com seleção
        selected_row = st.dataframe(
            datasets_df,
            use_container_width=True,
            hide_index=True,
            selection_mode="single-row",
            on_select="rerun"
        )
        
        # Ações com dataset selecionado
        if selected_row and selected_row.selection.rows:
            selected_idx = selected_row.selection.rows[0]
            selected_dataset = datasets[selected_idx]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📂 Carregar Dataset", type="primary", use_container_width=True):
                    df = pd.DataFrame(selected_dataset['data'])
                    st.session_state['analysis_df'] = df
                    st.session_state['analysis_dataset_id'] = selected_dataset['id']
                    st.success(f"Dataset '{selected_dataset['name']}' carregado!")
                    st.rerun()
            
            with col2:
                if st.button("📥 Baixar CSV", use_container_width=True):
                    df = pd.DataFrame(selected_dataset['data'])
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"{selected_dataset['name']}.csv",
                        mime="text/csv"
                    )
            
            with col3:
                if st.button("👁️ Visualizar", use_container_width=True):
                    with st.expander("Dados do Dataset"):
                        df = pd.DataFrame(selected_dataset['data'])
                        st.dataframe(df, use_container_width=True)
        
        # Estatísticas gerais
        st.markdown("### 📈 Estatísticas dos Datasets")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de Datasets", len(datasets))
        
        with col2:
            total_records = sum(ds['row_count'] for ds in datasets)
            st.metric("Total de Registros", f"{total_records:,}")
        
        with col3:
            latest_date = max(ds['created_at'] for ds in datasets)
            st.metric("Última Atualização", latest_date[:10])
    else:
        st.info("Nenhum dataset salvo ainda. Faça upload na aba 'Upload'.")
