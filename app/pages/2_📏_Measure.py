import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Adiciona o diretório app ao path - CORRIGIDO
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
from components.data_catalog import show_catalog
from components.reports import render_html_report, save_analysis_manifest

st.set_page_config(page_title="Measure", page_icon="📏", layout="wide")
init_catalog()

st.header("📏 Measure — Coleta, Validação e Padronização de Dados")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📤 Upload", "📊 Validação", "📈 Estatísticas", "📁 Catálogo"])

with tab1:
    st.subheader("Upload de Dados")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        file = st.file_uploader(
            "Envie arquivo CSV ou Excel",
            type=["csv", "xlsx", "xls"],
            help="Máximo 200MB"
        )
        
        if file:
            notes = st.text_input("Observações sobre o arquivo (opcional)")
            
            if st.button("💾 Salvar no Catálogo"):
                fid, stored = save_upload(file, notes=notes)
                if fid:
                    st.success(f"✅ Arquivo salvo! ID: {fid}")
                    st.session_state['last_upload'] = stored
    
    with col2:
        st.info("""
        **Formatos aceitos:**
        - CSV (vírgula ou ponto-vírgula)
        - Excel (.xlsx, .xls)
        
        **Dica:** Use o arquivo exemplo em 
        `sample_data/greenpeace_example.csv`
        """)

with tab2:
    st.subheader("Validação e Padronização")
    
    if 'last_upload' in st.session_state:
        stored_path = Path(st.session_state['last_upload'])
        
        if stored_path.suffix.lower() in ['.csv', '.xlsx', '.xls']:
            df = load_table_from_path(stored_path)
            
            if not df.empty:
                st.markdown(f"**Arquivo:** {stored_path.name}")
                st.markdown(f"**Dimensões:** {df.shape[0]} linhas × {df.shape[1]} colunas")
                
                st.markdown("### Preview dos Dados")
                st.dataframe(df.head(10), use_container_width=True)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total de Registros", df.shape[0])
                
                with col2:
                    missing = df.isnull().sum().sum()
                    st.metric("Valores Ausentes", missing)
                
                with col3:
                    duplicates = df.duplicated().sum()
                    st.metric("Linhas Duplicadas", duplicates)
                
                st.markdown("### Qualidade dos Dados por Campo")
                
                quality_df = pd.DataFrame({
                    'Campo': df.columns,
                    'Tipo': df.dtypes.astype(str),
                    'Valores Únicos': df.nunique(),
                    'Ausentes': df.isnull().sum(),
                    '% Ausentes': (df.isnull().sum() / len(df) * 100).round(2)
                })
                
                st.dataframe(quality_df, use_container_width=True)
                
                st.markdown("### Padronizar e Salvar")
                
                dataset_name = st.text_input(
                    "Nome do dataset padronizado",
                    value="dataset_medicoes",
                    help="Use apenas letras, números e underscore"
                )
                
                if st.button("🔧 Padronizar e Salvar como Parquet", type="primary"):
                    out_path = curate_table(df, dataset_name)
                    if out_path:
                        st.success(f"✅ Dataset padronizado salvo: {out_path.name}")
                        st.session_state['current_dataset'] = dataset_name
                        
                        manifest_id, _ = save_analysis_manifest(
                            phase="measure",
                            dataset_id=dataset_name,
                            parameters={"original_file": stored_path.name},
                            results={"parquet_path": str(out_path)}
                        )
                        st.caption(f"Manifesto: {manifest_id}")
    else:
        st.info("Faça upload de um arquivo na aba 'Upload' primeiro.")

with tab3:
    st.subheader("Análise Estatística Descritiva")
    
    datasets_df = list_datasets()
    
    if not datasets_df.empty:
        selected = st.selectbox(
            "Selecione o dataset",
            datasets_df['name'].unique()
        )
        
        if selected:
            df = pd.read_parquet(
                datasets_df[datasets_df['name'] == selected].iloc[0]['parquet_path']
            )
            
            st.markdown(f"**Dataset:** {selected}")
            st.markdown(f"**Registros:** {len(df)}")
            
            st.markdown("### Estatísticas Descritivas")
            stats_df = desc_stats(df)
            
            if not stats_df.empty:
                st.dataframe(stats_df, use_container_width=True)
                
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                
                if numeric_cols:
                    st.markdown("### Distribuições")
                    
                    selected_col = st.selectbox("Selecione a variável", numeric_cols)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig = histogram_with_stats(df[selected_col], title=f"Distribuição de {selected_col}")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        outliers = detect_outliers(df[selected_col])
                        n_outliers = outliers.sum()
                        
                        st.metric("Outliers Detectados", n_outliers)
                        st.caption("Método: IQR (1.5 × Intervalo Interquartil)")
                        
                        if n_outliers > 0:
                            st.warning(f"⚠️ {n_outliers} outliers encontrados em {selected_col}")
                
                if st.button("📄 Gerar Relatório de Medição"):
                    html_path = RESULTS / f"measure_report_{selected}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.html"
                    
                    quality_df = pd.DataFrame({
                        'Campo': df.columns,
                        'Tipo': df.dtypes.astype(str),
                        'Valores Únicos': df.nunique(),
                        'Ausentes': df.isnull().sum(),
                        '% Ausentes': (df.isnull().sum() / len(df) * 100).round(2)
                    })
                    
                    metrics = [
                        {"label": "Total de Registros", "value": str(len(df))},
                        {"label": "Campos Numéricos", "value": str(len(numeric_cols))},
                        {"label": "Qualidade dos Dados", "value": f"{100 - (df.isnull().sum().sum() / df.size * 100):.1f}%"}
                    ]
                    
                    tables = [
                        {"title": "Estatísticas Descritivas", "df": stats_df.reset_index()},
                        {"title": "Qualidade por Campo", "df": quality_df}
                    ]
                    
                    html = render_html_report(
                        title=f"Relatório de Medição - {selected}",
                        project="DMAIC Greenpeace",
                        summary=f"Análise descritiva do dataset {selected} com {len(df)} registros.",
                        metrics=metrics,
                        tables=tables,
                        conclusions="Dados coletados e validados com sucesso. Pronto para fase de análise.",
                        out_html=html_path
                    )
                    
                    st.success("✅ Relatório gerado com sucesso!")
    else:
        st.info("Nenhum dataset disponível. Faça upload e padronize os dados primeiro.")

with tab4:
    st.subheader("Catálogo de Dados")
    show_catalog()
