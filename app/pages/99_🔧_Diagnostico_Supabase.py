import streamlit as st
import pandas as pd
from supabase import create_client, Client
import json
from datetime import datetime
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="Diagnóstico Supabase - Green Belt",
    page_icon="🔧",
    layout="wide"
)

st.title("🔧 Diagnóstico e Configuração do Supabase")
st.markdown("Verificando e configurando as tabelas do projeto Green Belt")

# Inicializar Supabase
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "")
        if url and key:
            return create_client(url, key)
        return None
    except Exception as e:
        st.error(f"Erro ao conectar: {e}")
        return None

supabase = init_supabase()

if not supabase:
    st.error("❌ Supabase não está configurado corretamente")
    st.info("""
    Para configurar o Supabase no Streamlit Cloud:
    1. Vá em Settings > Secrets no seu app
    2. Adicione:
    ```
    SUPABASE_URL = "sua-url-aqui"
    SUPABASE_KEY = "sua-key-aqui"
    ```
    """)
    st.stop()

st.success("✅ Conectado ao Supabase")

# Verificação rápida
st.header("📊 Status das Tabelas")

tabelas = ['projects', 'action_plans', 'datasets', 'ishikawa_analysis', 'kpis', 'reports']

for tabela in tabelas:
    col1, col2, col3 = st.columns([2, 2, 3])
    
    with col1:
        st.write(f"**{tabela}**")
    
    with col2:
        try:
            response = supabase.table(tabela).select("*", count='exact', head=True).execute()
            count = response.count if hasattr(response, 'count') else 0
            
            if count > 0:
                st.success(f"✅ {count} registros")
            else:
                st.warning("⚠️ Vazia")
        except Exception as e:
            if "relation" in str(e).lower() and "does not exist" in str(e).lower():
                st.error("❌ Não existe")
            else:
                st.error(f"❌ Erro")
    
    with col3:
        if st.button(f"Ver amostra", key=f"view_{tabela}"):
            try:
                data = supabase.table(tabela).select("*").limit(3).execute()
                if data.data:
                    with st.expander(f"Dados de {tabela}"):
                        st.json(data.data)
            except:
                st.error("Não foi possível carregar")

st.markdown("---")

# Criar tabelas via Dashboard
st.header("🛠️ Criar Estrutura das Tabelas")

st.warning("""
⚠️ **As tabelas precisam ser criadas no Dashboard do Supabase**

1. Acesse seu projeto em [supabase.com](https://supabase.com)
2. Vá em **SQL Editor**
3. Cole e execute cada script abaixo
""")

# SQL Scripts
sql_scripts = {
    "1. Tabela projects": """
-- Tabela de projetos
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    charter TEXT,
    smart_goals JSONB,
    stakeholders JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Desabilitar RLS temporariamente para testes
ALTER TABLE projects DISABLE ROW LEVEL SECURITY;
""",
    
    "2. Tabela datasets": """
-- Tabela de dados coletados
CREATE TABLE IF NOT EXISTS datasets (
    id SERIAL PRIMARY KEY,
    project_id INTEGER,
    cb_id VARCHAR(50),
    unidade VARCHAR(100),
    categoria VARCHAR(100),
    defeito TEXT,
    horas_operacao FLOAT,
    tempo_parada_min FLOAT,
    custo FLOAT,
    quantidade INTEGER,
    defeitos INTEGER,
    turno VARCHAR(50),
    pressao_diesel FLOAT,
    caminhao_id VARCHAR(50),
    data_coleta DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

ALTER TABLE datasets DISABLE ROW LEVEL SECURITY;
""",
    
    "3. Tabela action_plans": """
-- Tabela de planos de ação
CREATE TABLE IF NOT EXISTS action_plans (
    id SERIAL PRIMARY KEY,
    project_id INTEGER,
    what TEXT NOT NULL,
    why TEXT,
    where_location VARCHAR(255),
    when_date DATE,
    who VARCHAR(255),
    how TEXT,
    how_much FLOAT,
    priority VARCHAR(20),
    status VARCHAR(50) DEFAULT 'Pendente',
    created_at TIMESTAMP DEFAULT NOW()
);

ALTER TABLE action_plans DISABLE ROW LEVEL SECURITY;
""",
    
    "4. Tabela ishikawa_analysis": """
-- Tabela de análise Ishikawa
CREATE TABLE IF NOT EXISTS ishikawa_analysis (
    id SERIAL PRIMARY KEY,
    project_id INTEGER,
    categoria VARCHAR(50),
    causa TEXT,
    impacto INTEGER,
    facilidade INTEGER,
    custo INTEGER,
    score FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

ALTER TABLE ishikawa_analysis DISABLE ROW LEVEL SECURITY;
""",
    
    "5. Tabelas kpis e reports": """
-- Tabela de KPIs
CREATE TABLE IF NOT EXISTS kpis (
    id SERIAL PRIMARY KEY,
    project_id INTEGER,
    nome VARCHAR(100),
    valor_atual FLOAT,
    valor_meta FLOAT,
    unidade VARCHAR(50),
    tipo VARCHAR(50),
    data_medicao DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabela de relatórios
CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    project_id INTEGER,
    tipo VARCHAR(50),
    titulo VARCHAR(255),
    conteudo JSONB,
    graficos JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

ALTER TABLE kpis DISABLE ROW LEVEL SECURITY;
ALTER TABLE reports DISABLE ROW LEVEL SECURITY;
"""
}

for titulo, sql in sql_scripts.items():
    with st.expander(titulo):
        st.code(sql, language='sql')
        if st.button(f"📋 Copiar", key=f"copy_{titulo}"):
            st.info("Cole este código no SQL Editor do Supabase")

st.markdown("---")

# Carregar dados de teste
st.header("📥 Carregar Dados de Teste")

if st.button("🚀 Carregar Dados do Projeto Green Belt", type="primary"):
    
    progress = st.progress(0)
    status = st.empty()
    
    try:
        # 1. Criar projeto
        status.text("Criando projeto...")
        progress.progress(20)
        
        projeto = {
            'name': 'Redução de Paradas de Caminhões Por Baixa Pressão de Diesel',
            'description': 'Projeto Green Belt para reduzir paradas por baixa pressão em 60%',
            'smart_goals': {
                'specific': 'Reduzir paradas por baixa pressão',
                'measurable': 'De 15 para 6 paradas/mês',
                'achievable': 'Com treinamento e manutenção',
                'relevant': 'Impacta disponibilidade da frota',
                'time_bound': '3 meses'
            },
            'stakeholders': ['Manutenção', 'Operação', 'Qualidade']
        }
        
        # Verificar se já existe
        existing = supabase.table('projects').select("*").eq('name', projeto['name']).execute()
        
        if existing.data:
            project_id = existing.data[0]['id']
            st.info(f"Projeto já existe (ID: {project_id})")
        else:
            response = supabase.table('projects').insert(projeto).execute()
            project_id = response.data[0]['id']
            st.success(f"✅ Projeto criado (ID: {project_id})")
        
        # 2. Criar dados de medição
        status.text("Criando dados de medição...")
        progress.progress(40)
        
        np.random.seed(42)
        dados_criados = 0
        
        for i in range(20):  # 20 registros de exemplo
            data = {
                'project_id': project_id,
                'cb_id': f'CB-{i+1:03d}',
                'unidade': np.random.choice(['Unidade A', 'Unidade B', 'Unidade C']),
                'categoria': np.random.choice(['Material', 'Mão de Obra', 'Método']),
                'defeito': np.random.choice([
                    'Combustível com alto teor de água',
                    'Falta de treinamento',
                    'Processo inadequado',
                    'Filtro saturado'
                ]),
                'horas_operacao': float(np.random.normal(67.97, 4.59)),
                'tempo_parada_min': float(np.random.exponential(30)),
                'custo': float(np.random.exponential(100)),
                'quantidade': int(np.random.poisson(5)),
                'defeitos': int(np.random.poisson(3)),
                'turno': np.random.choice(['Manhã', 'Tarde', 'Noite']),
                'pressao_diesel': float(np.random.normal(4.5, 0.5)),
                'caminhao_id': f'CAM{np.random.randint(1, 21):03d}',
                'data_coleta': datetime.now().date().isoformat()
            }
            
            try:
                supabase.table('datasets').insert(data).execute()
                dados_criados += 1
            except:
                pass
        
        if dados_criados > 0:
            st.success(f"✅ {dados_criados} registros de dados criados")
        
        # 3. Criar planos de ação
        status.text("Criando planos de ação...")
        progress.progress(60)
        
        acoes = [
            {
                'project_id': project_id,
                'what': 'Implementar análise de qualidade do combustível',
                'why': 'Reduzir contaminação por água',
                'where_location': 'Todos os tanques',
                'when_date': datetime.now().date().isoformat(),
                'who': 'Equipe Manutenção',
                'how': 'Análise semanal com kit de teste',
                'how_much': 5000.00,
                'priority': 'Alta',
                'status': 'Pendente'
            },
            {
                'project_id': project_id,
                'what': 'Programa de treinamento',
                'why': 'Capacitar operadores',
                'where_location': 'Sala de treinamento',
                'when_date': datetime.now().date().isoformat(),
                'who': 'RH + Consultoria',
                'how': 'Curso teórico e prático 16h',
                'how_much': 8000.00,
                'priority': 'Alta',
                'status': 'Pendente'
            },
            {
                'project_id': project_id,
                'what': 'Criar checklist de abastecimento',
                'why': 'Padronizar processo',
                'where_location': 'Todos os pontos',
                'when_date': datetime.now().date().isoformat(),
                'who': 'Engenharia',
                'how': 'Desenvolver e implementar POP',
                'how_much': 3000.00,
                'priority': 'Média',
                'status': 'Pendente'
            }
        ]
        
        acoes_criadas = 0
        for acao in acoes:
            try:
                supabase.table('action_plans').insert(acao).execute()
                acoes_criadas += 1
            except:
                pass
        
        if acoes_criadas > 0:
            st.success(f"✅ {acoes_criadas} planos de ação criados")
        
        # 4. Criar análise Ishikawa
        status.text("Criando análise Ishikawa...")
        progress.progress(80)
        
        causas = [
            ('Material', 'Combustível com alto teor de água', 9, 5, 3),
            ('Material', 'Contaminação biológica', 8, 4, 4),
            ('Mão de Obra', 'Falta de treinamento específico', 8, 7, 2),
            ('Mão de Obra', 'Não realização de drenagem', 7, 8, 1),
            ('Método', 'Processo não padronizado', 8, 8, 3),
            ('Método', 'Ausência de checklist', 7, 9, 2),
            ('Máquina', 'Filtros saturados', 6, 6, 5),
            ('Máquina', 'Bombas desgastadas', 5, 4, 7)
        ]
        
        causas_criadas = 0
        for cat, causa, imp, fac, custo in causas:
            ishikawa = {
                'project_id': project_id,
                'categoria': cat,
                'causa': causa,
                'impacto': imp,
                'facilidade': fac,
                'custo': custo,
                'score': float((imp * 0.5 + fac * 0.3 + (11-custo) * 0.2) * 10)
            }
            try:
                supabase.table('ishikawa_analysis').insert(ishikawa).execute()
                causas_criadas += 1
            except:
                pass
        
        if causas_criadas > 0:
            st.success(f"✅ {causas_criadas} causas Ishikawa criadas")
        
        progress.progress(100)
        status.text("Concluído!")
        
        st.balloons()
        st.success("🎉 Dados de exemplo carregados com sucesso!")
        
        # Mostrar resumo
        st.info(f"""
        **Resumo do carregamento:**
        - 1 Projeto criado/verificado
        - {dados_criados} Registros de dados
        - {acoes_criadas} Planos de ação
        - {causas_criadas} Análises Ishikawa
        """)
        
    except Exception as e:
        st.error(f"Erro durante o carregamento: {e}")
        st.info("Verifique se as tabelas foram criadas no Supabase")

# Limpar dados (opcional)
st.markdown("---")
st.header("🗑️ Limpar Dados (Cuidado!)")

with st.expander("Opções de limpeza"):
    st.warning("⚠️ Estas ações são irreversíveis!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Limpar datasets", type="secondary"):
            if st.checkbox("Confirmo que quero limpar"):
                try:
                    supabase.table('datasets').delete().neq('id', 0).execute()
                    st.success("Tabela datasets limpa")
                except Exception as e:
                    st.error(f"Erro: {e}")
    
    with col2:
        if st.button("Limpar TUDO", type="secondary"):
            if st.checkbox("Confirmo que quero limpar TUDO"):
                try:
                    for tabela in tabelas:
                        supabase.table(tabela).delete().neq('id', 0).execute()
                    st.success("Todas as tabelas limpas")
                except Exception as e:
                    st.error(f"Erro: {e}")

st.markdown("---")
st.caption("🔧 Página de Diagnóstico - Remova após configurar o Supabase")
