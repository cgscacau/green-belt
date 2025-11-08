import streamlit as st
import pandas as pd
from pathlib import Path
import duckdb
import sys

# Adiciona o diretório app ao path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from components.upload_and_store import DB, init_catalog

def show_catalog():
    """Exibe catálogo de dados"""
    init_catalog()
    
    try:
        con = duckdb.connect(str(DB))
        
        # Arquivos enviados
        st.subheader("📁 Arquivos Enviados")
        try:
            files_df = con.execute("""
                SELECT filename, orig_ext, uploaded_at, notes 
                FROM files_catalog 
                ORDER BY uploaded_at DESC
            """).df()
            
            if not files_df.empty:
                st.dataframe(files_df, use_container_width=True)
            else:
                st.info("Nenhum arquivo enviado ainda.")
        except:
            st.info("Nenhum arquivo enviado ainda.")
        
        # Datasets processados
        st.subheader("📊 Datasets Processados")
        try:
            datasets_df = con.execute("""
                SELECT name, version, created_at, row_count, col_count 
                FROM datasets 
                ORDER BY created_at DESC
            """).df()
            
            if not datasets_df.empty:
                st.dataframe(datasets_df, use_container_width=True)
            else:
                st.info("Nenhum dataset processado ainda.")
        except:
            st.info("Nenhum dataset processado ainda.")
        
        con.close()
    except Exception as e:
        st.error(f"Erro ao acessar catálogo: {e}")

def get_dataset_info(dataset_name: str):
    """Retorna informações sobre um dataset"""
    try:
        con = duckdb.connect(str(DB))
        info = con.execute("""
            SELECT * FROM datasets 
            WHERE name = ? 
            ORDER BY version DESC 
            LIMIT 1
        """, [dataset_name]).df()
        con.close()
        return info
    except:
        return pd.DataFrame()

def dataset_selector():
    """Widget para selecionar dataset"""
    try:
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
    except:
        st.warning("Nenhum dataset disponível. Faça upload na página Measure.")
        return None
