"""
Configuração de paths para o sistema DMAIC
"""
import sys
from pathlib import Path

# Adiciona o diretório app ao path
APP_DIR = Path(__file__).parent
sys.path.insert(0, str(APP_DIR))

# Paths importantes
DB_PATH = APP_DIR / "db" / "catalog.duckdb"
FILES_PATH = APP_DIR / "db" / "files"
CURATED_PATH = APP_DIR / "data_container" / "curated"
RESULTS_PATH = APP_DIR / "data_container" / "results"

# Cria diretórios se não existirem
for path in [FILES_PATH, CURATED_PATH, RESULTS_PATH]:
    path.mkdir(parents=True, exist_ok=True)
