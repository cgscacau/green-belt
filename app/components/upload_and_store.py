import hashlib
import time
from pathlib import Path
import pandas as pd
import duckdb
import streamlit as st

# Paths configuráveis para cloud/local
ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "db" / "catalog.duckdb"
FILES = ROOT / "db" / "files"
CURATED = ROOT / "data_container" / "curated"
RESULTS = ROOT / "data_container" / "results"

# Cria diretórios se não existirem
for p in (FILES, CURATED, RESULTS):
    p.mkdir(parents=True, exist_ok=True)

def _hash_bytes(b: bytes) -> str:
    """Gera hash único para arquivo"""
    return hashlib.sha256(b).hexdigest()[:16]

def init_catalog():
    """Inicializa banco de dados DuckDB"""
    try:
        con = duckdb.connect(str(DB))
        
        # Tabela de arquivos
        con.execute("""
        CREATE TABLE IF NOT EXISTS files_catalog(
            id TEXT PRIMARY KEY,
            filename TEXT,
            stored_path TEXT,
            orig_ext TEXT,
            uploaded_at TIMESTAMP,
            notes TEXT
        );
        """)
        
        # Tabela de datasets
        con.execute("""
        CREATE TABLE IF NOT EXISTS datasets(
            id TEXT,
            version INT,
            name TEXT,
            parquet_path TEXT,
            created_at TIMESTAMP,
            row_count INT,
            col_count INT,
            PRIMARY KEY (id, version)
        );
        """)
        
        # Tabela de análises
        con.execute("""
        CREATE TABLE IF NOT EXISTS analysis_runs(
            run_id TEXT PRIMARY KEY,
            phase TEXT,
            dataset_id TEXT,
            parameters TEXT,
            results_path TEXT,
            created_at TIMESTAMP
        );
        """)
        
        con.close()
        return True
    except Exception as e:
        st.error(f"Erro ao inicializar catálogo: {e}")
        return False

def save_upload(file, notes=""):
    """Salva arquivo no repositório"""
    try:
        data = file.read()
        fid = _hash_bytes(data)
        ext = Path(file.name).suffix.lower()
        ts = int(time.time())
        dest = FILES / f"{fid}_{ts}{ext}"
        dest.write_bytes(data)
        
        con = duckdb.connect(str(DB))
        con.execute(
            "INSERT OR REPLACE INTO files_catalog VALUES (?, ?, ?, ?, now(), ?)",
            [fid, file.name, str(dest), ext, notes]
        )
        con.close()
        return fid, dest
    except Exception as e:
        st.error(f"Erro ao salvar arquivo: {e}")
        return None, None

def load_table_from_path(p: Path) -> pd.DataFrame:
    """Carrega tabela de CSV ou Excel"""
    try:
        if p.suffix.lower() in [".csv"]:
            return pd.read_csv(p)
        elif p.suffix.lower() in [".xlsx", ".xls"]:
            return pd.read_excel(p)
        else:
            raise ValueError("Formato não suportado. Use CSV ou Excel.")
    except Exception as e:
        st.error(f"Erro ao carregar arquivo: {e}")
        return pd.DataFrame()

def curate_table(df: pd.DataFrame, name: str) -> Path:
    """Padroniza e salva tabela como Parquet"""
    try:
        # Padronização de colunas
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        
        # Remove linhas completamente vazias
        df = df.dropna(how='all')
        
        # Gera versão única
        ver = int(time.time())
        out = CURATED / f"{name}_{ver}.parquet"
        
        # Salva como Parquet
        df.to_parquet(out, index=False)
        
        # Registra no catálogo
        con = duckdb.connect(str(DB))
        con.execute(
            "INSERT INTO datasets VALUES (?, ?, ?, ?, now(), ?, ?)",
            [name, ver, name, str(out), len(df), len(df.columns)]
        )
        con.close()
        
        return out
    except Exception as e:
        st.error(f"Erro ao padronizar dados: {e}")
        return None

def list_datasets():
    """Lista datasets disponíveis"""
    try:
        con = duckdb.connect(str(DB))
        df = con.execute("""
            SELECT name, version, created_at, row_count, col_count 
            FROM datasets 
            ORDER BY created_at DESC
        """).df()
        con.close()
        return df
    except:
        return pd.DataFrame()

def load_dataset(name: str, version: int = None) -> pd.DataFrame:
    """Carrega dataset do catálogo"""
    try:
        con = duckdb.connect(str(DB))
        
        if version is None:
            # Pega versão mais recente
            result = con.execute("""
                SELECT parquet_path FROM datasets 
                WHERE id = ? 
                ORDER BY version DESC 
                LIMIT 1
            """, [name]).fetchone()
        else:
            result = con.execute("""
                SELECT parquet_path FROM datasets 
                WHERE id = ? AND version = ?
            """, [name, version]).fetchone()
        
        con.close()
        
        if result:
            return pd.read_parquet(result[0])
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar dataset: {e}")
        return pd.DataFrame()
