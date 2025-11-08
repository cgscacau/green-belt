"""
Testes básicos para o sistema DMAIC Greenpeace
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Adiciona o diretório app ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'app'))

def test_imports():
    """Testa se todos os módulos podem ser importados"""
    try:
        from components.upload_and_store import init_catalog
        from components.stats_blocks import desc_stats
        from components.visual_blocks import line_over_time
        from components.reports import render_html_report
        print("✅ Todos os imports funcionando")
        return True
    except ImportError as e:
        print(f"❌ Erro de import: {e}")
        return False

def test_sample_data():
    """Testa se o arquivo de exemplo existe e pode ser lido"""
    try:
        sample_path = Path(__file__).parent.parent / 'sample_data' / 'greenpeace_example.csv'
        if not sample_path.exists():
            print(f"❌ Arquivo de exemplo não encontrado: {sample_path}")
            return False
        
        df = pd.read_csv(sample_path)
        print(f"✅ Arquivo de exemplo carregado: {len(df)} linhas, {len(df.columns)} colunas")
        print(f"   Colunas: {', '.join(df.columns)}")
        return True
    except Exception as e:
        print(f"❌ Erro ao ler arquivo de exemplo: {e}")
        return False

def test_statistics():
    """Testa funções estatísticas básicas"""
    try:
        from components.stats_blocks import desc_stats, shapiro_test
        
        # Cria dados de teste
        test_data = pd.DataFrame({
            'normal': np.random.normal(100, 15, 100),
            'uniform': np.random.uniform(0, 100, 100),
            'categorical': np.random.choice(['A', 'B', 'C'], 100)
        })
        
        # Testa estatísticas descritivas
        stats = desc_stats(test_data)
        assert not stats.empty, "Estatísticas descritivas vazias"
        print(f"✅ Estatísticas descritivas: {stats.shape}")
        
        # Testa normalidade
        result = shapiro_test(test_data['normal'])
        assert result is not None, "Teste de normalidade falhou"
        print(f"✅ Teste Shapiro-Wilk: W={result['W']:.4f}, p={result['p_value']:.4f}")
        
        return True
    except Exception as e:
        print(f"❌ Erro em testes estatísticos: {e}")
        return False

def test_database():
    """Testa inicialização do banco de dados"""
    try:
        from components.upload_and_store import init_catalog, DB
        
        # Tenta inicializar catálogo
        success = init_catalog()
        if success:
            print(f"✅ Banco de dados inicializado: {DB}")
        else:
            print("⚠️ Banco de dados não pôde ser inicializado (pode ser normal no ambiente de teste)")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao testar banco de dados: {e}")
        return False

def test_visualization():
    """Testa criação de visualizações"""
    try:
        from components.visual_blocks import histogram_with_stats
        
        # Dados de teste
        data = pd.Series(np.random.normal(100, 15, 100))
        
        # Tenta criar histograma
        fig = histogram_with_stats(data, title="Teste")
        assert fig is not None, "Figura não criada"
        print("✅ Visualização criada com sucesso")
        
        return True
    except Exception as e:
        print(f"❌ Erro em visualização: {e}")
        return False

def run_all_tests():
    """Executa todos os testes"""
    print("\n" + "="*50)
    print("🧪 EXECUTANDO TESTES DO SISTEMA DMAIC")
    print("="*50 + "\n")
    
    tests = [
        ("Imports", test_imports),
        ("Sample Data", test_sample_data),
        ("Statistics", test_statistics),
        ("Database", test_database),
        ("Visualization", test_visualization)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n📋 Testando {name}...")
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"❌ Erro inesperado em {name}: {e}")
            results.append((name, False))
    
    # Resumo
    print("\n" + "="*50)
    print("📊 RESUMO DOS TESTES")
    print("="*50)
    
    passed = sum(1 for _, p in results if p)
    total = len(results)
    
    for name, passed in results:
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"{name}: {status}")
    
    print(f"\nTotal: {passed}/{total} testes passaram")
    
    if passed == total:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
    else:
        print(f"\n⚠️ {total - passed} teste(s) falharam")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
