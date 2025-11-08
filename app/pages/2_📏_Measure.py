import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import time

# Adiciona o diretório app ao path
app_dir = Path(__file__).parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

# Imports dos componentes
from components.upload_and_store import (
    init_catalog, save_upload, load_table_from_path, 
    curate_table, list_datasets, RESULTS
)
from components.stats_blocks import desc_stats, detect_outliers
from components.visual_blocks import histogram_with_stats, box_by_group
from components.reports import render_html_report, save_analysis_manifest

st.set_page_config(page_title="Measure", page_icon="📏", layout="wide")

# Inicializa catálogo
try:
    init_catalog()
except Exception as e:
    st.warning(f"Aviso ao inicializar catálogo: {e}")

st.header("📏 Measure — Coleta, Validação e Padronização de Dados")

# Tabs
tab1, tab2, tab3 = st.tabs(["📤 Upload", "📊 Validação", "📈 Estatísticas"])

with tab1:
    st.subheader("Upload de Dados")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Opção de usar dados de exemplo
        use_sample = st.checkbox("Usar dados de exemplo")
        
        if use_sample:
            sample_path = Path(__file__).parent.parent.parent / "sample_data" / "greenpeace_example.csv"
            if sample_path.exists():
                try:
                    df_sample = pd.read_csv(sample_path)
                    st.success("Dados de exemplo carregados!")
                    st.dataframe(df_sample.head(), use_container_width=True)
                    
                    if st.button("Usar estes dados"):
                        st.session_state['uploaded_df'] = df_sample
                        st.session_state['uploaded_name'] = "greenpeace_example.csv"
                        st.rerun()
                except Exception as e:
                    st.error(f"Erro ao carregar exemplo: {e}")
            else:
                st.warning("Arquivo de exemplo não encontrado.")
        else:
            file = st.file_uploader(
                "Envie arquivo CSV ou Excel",
                type=["csv", "xlsx", "xls"],
                help="Máximo 200MB"
            )
            
            if file:
                notes = st.text_input("Observações sobre o arquivo (opcional)")
                
                if st.button("💾 Processar Arquivo"):
                    try:
                        # Lê o arquivo diretamente
                        if file.name.endswith('.csv'):
                            df = pd.read_csv(file)
                        else:
                            df = pd.read_excel(file)
                        
                        st.session_state['uploaded_df'] = df
                        st.session_state['uploaded_name'] = file.name
                        st.success(f"✅ Arquivo processado: {file.name}")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Erro ao processar arquivo: {e}")
    
    with col2:
        st.info("""
        **Formatos aceitos:**
        - CSV (vírgula ou ponto-vírgula)
        - Excel (.xlsx, .xls)
        
        **Dica:** Marque "Usar dados de exemplo" 
        para testar o sistema rapidamente.
        """)

with tab2:
    st.subheader("Validação e Padronização")
    
    if 'uploaded_df' in st.session_state:
        df = st.session_state['uploaded_df']
        filename = st.session_state.get('uploaded_name', 'arquivo')
        
        st.markdown(f"**Arquivo:** {filename}")
        st.markdown(f"**Dimensões:** {df.shape[0]} linhas × {df.shape[1]} colunas")
        
        # Preview
        st.markdown("### Preview dos Dados")
        st.dataframe(df.head(10), use_container_width=True)
        
        # Validação
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de Registros", df.shape[0])
        
        with col2:
            missing = df.isnull().sum().sum()
            st.metric("Valores Ausentes", missing)
        
        with col3:
            duplicates = df.duplicated().sum()
            st.metric("Linhas Duplicadas", duplicates)
        
        # Análise de qualidade por coluna
        st.markdown("### Qualidade dos Dados por Campo")
        
        quality_df = pd.DataFrame({
            'Campo': df.columns,
            'Tipo': df.dtypes.astype(str),
            'Valores Únicos': df.nunique(),
            'Ausentes': df.isnull().sum(),
            '% Ausentes': (df.isnull().sum() / len(df) * 100).round(2)
        })
        
        st.dataframe(quality_df, use_container_width=True)
        
        # Padronização
        st.markdown("### Padronizar e Salvar")
        
        dataset_name = st.text_input(
            "Nome do dataset padronizado",
            value="dataset_medicoes",
            help="Use apenas letras, números e underscore"
        )
        
        if st.button("🔧 Padronizar e Salvar como Parquet", type="primary"):
            try:
                # Padroniza colunas
                df_copy = df.copy()
                df_copy.columns = [c.strip().lower().replace(" ", "_") for c in df_copy.columns]
                
                # Salva temporariamente em session_state
                st.session_state['padronized_df'] = df_copy
                st.session_state['padronized_name'] = dataset_name
                
                # Tenta salvar como Parquet
                timestamp = int(time.time())
                parquet_filename = f"{dataset_name}_{timestamp}.parquet"
                
                st.success(f"✅ Dataset padronizado: {dataset_name}")
                st.info(f"Dados prontos para análise na aba 'Estatísticas'")
                
                # Salva informações no session_state para uso posterior
                st.session_state['current_dataset'] = dataset_name
                st.session_state['current_df'] = df_copy
                
            except Exception as e:
                st.error(f"Erro ao padronizar: {e}")
                st.info("Os dados foram salvos temporariamente na sessão.")
    else:
        st.info("Faça upload de um arquivo na aba 'Upload' primeiro.")

with tab3:
    st.subheader("Análise Estatística Descritiva")
    
    # Verifica se há dados padronizados na sessão
    if 'current_df' in st.session_state and 'current_dataset' in st.session_state:
        df = st.session_state['current_df']
        dataset_name = st.session_state['current_dataset']
        
        st.markdown(f"**Dataset:** {dataset_name}")
        st.markdown(f"**Registros:** {len(df)}")
        
        # Estatísticas descritivas
        st.markdown("### Estatísticas Descritivas")
        
        try:
            stats_df = desc_stats(df)
            
            if not stats_df.empty:
                st.dataframe(stats_df, use_container_width=True)
                
                # Visualizações
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                
                if numeric_cols:
                    st.markdown("### Distribuições")
                    
                    selected_col = st.selectbox("Selecione a variável", numeric_cols)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        try:
                            fig = histogram_with_stats(df[selected_col], title=f"Distribuição de {selected_col}")
                            st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.error(f"Erro ao criar histograma: {e}")
                    
                    with col2:
                        try:
                            outliers = detect_outliers(df[selected_col])
                            n_outliers = outliers.sum() if not outliers.empty else 0
                            
                            st.metric("Outliers Detectados", n_outliers)
                            st.caption("Método: IQR (1.5 × Intervalo Interquartil)")
                            
                            if n_outliers > 0:
                                st.warning(f"⚠️ {n_outliers} outliers encontrados em {selected_col}")
                        except Exception as e:
                            st.error(f"Erro ao detectar outliers: {e}")
                    
                    # Botão para exportar dados
                    st.markdown("### Exportar Dados")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Exporta como CSV
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Baixar CSV",
                            data=csv,
                            file_name=f"{dataset_name}.csv",
                            mime="text/csv"
                        )
                    
                    with col2:
                        # Salva dados na sessão para outras páginas
                        if st.button("💾 Disponibilizar para Análise"):
                            st.session_state['analysis_dataset'] = dataset_name
                            st.session_state['analysis_df'] = df
                            st.success("✅ Dataset disponível para análise!")
                            st.info("Vá para a página 'Analyze' para continuar.")
                    
                else:
                    st.warning("Nenhuma coluna numérica encontrada no dataset.")
            else:
                st.warning("Não foi possível calcular estatísticas descritivas.")
                
        except Exception as e:
            st.error(f"Erro na análise estatística: {e}")
            
            # Mostra pelo menos os dados
            st.markdown("### Dados Disponíveis")
            st.dataframe(df.head(20), use_container_width=True)
    
    # Alternativa: usar dados de exemplo diretamente
    elif not st.session_state.get('current_df') is None:
        st.info("Processe os dados na aba 'Validação' primeiro.")
    else:
        st.info("Nenhum dataset disponível. Faça upload e padronize os dados primeiro.")
        
        # Botão para carregar exemplo rapidamente
        if st.button("🚀 Carregar Exemplo Rápido"):
            try:
                sample_path = Path(__file__).parent.parent.parent / "sample_data" / "greenpeace_example.csv"
                if sample_path.exists():
                    df = pd.read_csv(sample_path)
                    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
                    
                    st.session_state['current_df'] = df
                    st.session_state['current_dataset'] = "greenpeace_example"
                    st.session_state['analysis_df'] = df
                    st.session_state['analysis_dataset'] = "greenpeace_example"
                    
                    st.success("✅ Dados de exemplo carregados!")
                    st.rerun()
            except Exception as e:
                st.error(f"Erro ao carregar exemplo: {e}")
