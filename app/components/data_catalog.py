import streamlit as st
import pandas as pd
from pathlib import Path
import duckdb
from app.components.upload_and_store import DB, init_catalog

def show_catalog():
    """Exibe catálogo de dados"""
    init_catalog()
    
    con = duckdb.connect(str(DB))
    
    # Arquivos enviados
    st.subheader("📁 Arquivos Enviados")
    files_df = con.execute("""
        SELECT filename, orig_ext, uploaded_at, notes 
        FROM files_catalog 
        ORDER BY uploaded_at DESC
    """).df()
    
    if not files_df.empty:
        st.dataframe(files_df, use_container_width=True)
    else:
        st.info("Nenhum arquivo enviado ainda.")
    
    # Datasets processados
    st.subheader("📊 Datasets Processados")
    datasets_df = con.execute("""
        SELECT name, version, created_at, row_count, col_count 
        FROM datasets 
        ORDER BY created_at DESC
    """).df()
    
    if not datasets_df.empty:
        st.dataframe(datasets_df, use_container_width=True)
    else:
        st.info("Nenhum dataset processado ainda.")
    
    con.close()

def get_dataset_info(dataset_name: str):
    """Retorna informações sobre um dataset"""
    con = duckdb.connect(str(DB))
    info = con.execute("""
        SELECT * FROM datasets 
        WHERE name = ? 
        ORDER BY version DESC 
        LIMIT 1
    """, [dataset_name]).df()
    con.close()
    return info

def dataset_selector():
    """Widget para selecionar dataset"""
    con = duckdb.connect(str(DB))
    datasets = con.execute("""
        SELECT DISTINCT name FROM datasets ORDER BY name
    """).df()
    con.close()
    
    if datasets.empty:
        st.warning("Nenhum dataset disponível. Faça upload na página Measure.")
        return None
    
    selected = st.selectbox(
        "Selecione o dataset",
        datasets['name'].tolist()
    )
    
    return selected
