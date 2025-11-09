import streamlit as st
import pandas as pd
from datetime import datetime
import os
import sys
from supabase import create_client, Client

# Configuração da página
st.set_page_config(
    page_title="Diagnóstico Supabase - Green Belt",
    page_icon="🔍",
    layout="wide"
)

# ========================= FUNÇÕES AUXILIARES =========================

# Inicializar Supabase
@st.cache_resource
def init_supabase():
    """Inicializa conexão com Supabase"""
    try:
        if "supabase" in st.secrets:
            url = st.secrets["supabase"]["url"]
            key = st.secrets["supabase"]["key"]
        else:
            url = os.environ.get("SUPABASE_URL", "")
            key = os.environ.get("SUPABASE_KEY", "")
        
        if url and key:
            return create_client(url, key)
        return None
    except Exception as e:
        st.error(f"Erro ao conectar com Supabase: {str(e)}")
        return None

supabase = init_supabase()

# ========================= INTERFACE PRINCIPAL =========================

st.title("🔍 Diagnóstico do Supabase")
st.markdown("Verifique o status da conexão e estrutura do banco de dados")

# Status da conexão
st.header("📡 Status da Conexão")

col1, col2, col3 = st.columns(3)

with col1:
    if supabase:
        st.success("✅ **Conexão Ativa**")
        st.caption("Supabase conectado com sucesso")
    else:
        st.error("❌ **Sem Conexão**")
        st.caption("Verifique as credenciais")

with col2:
    if "supabase" in st.secrets:
        st.info("🔑 **Secrets Configurados**")
        st.caption("Via st.secrets")
    elif os.environ.get("SUPABASE_URL"):
        st.info("🔑 **Env Vars Configuradas**")
        st.caption("Via variáveis de ambiente")
    else:
        st.warning("⚠️ **Credenciais Ausentes**")

with col3:
    st.metric("Timestamp", datetime.now().strftime("%H:%M:%S"))
    if st.button("🔄 Atualizar", use_container_width=True):
        st.rerun()

st.divider()

# Verificar tabelas
st.header("📊 Estrutura do Banco de Dados")

if supabase:
    # Lista de tabelas esperadas
    expected_tables = [
        'projects',
        'voc_items',
        'sipoc',
        'measurements',
        'process_data',
        'analyses',
        'improvement_actions',
        'brainstorm_ideas',
        'control_plans',
        'lessons_learned',
        'collection_plans'
    ]
    
    st.subheader("🗂️ Verificação de Tabelas")
    
    # Criar grid de status
    cols = st.columns(3)
    
    for i, table_name in enumerate(expected_tables):
        with cols[i % 3]:
            try:
                # Tentar fazer uma query simples
                response = supabase.table(table_name).select("*").limit(1).execute()
                
                # Contar registros
                count_response = supabase.table(table_name).select("*", count='exact').execute()
                count = len(count_response.data) if count_response.data else 0
                
                st.success(f"✅ **{table_name}**")
                st.caption(f"{count} registros")
                
            except Exception as e:
                if "not exist" in str(e) or "not found" in str(e):
                    st.error(f"❌ **{table_name}**")
                    st.caption("Tabela não existe")
                else:
                    st.warning(f"⚠️ **{table_name}**")
                    st.caption("Erro ao acessar")
    
    st.divider()
    
    # Estatísticas gerais
    st.subheader("📈 Estatísticas Gerais")
    
    try:
        # Buscar estatísticas
        projects_count = len(supabase.table('projects').select("*").execute().data or [])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Projetos", projects_count)
        
        with col2:
            analyses_count = len(supabase.table('analyses').select("*").execute().data or [])
            st.metric("Análises Realizadas", analyses_count)
        
        with col3:
            actions_count = len(supabase.table('improvement_actions').select("*").execute().data or [])
            st.metric("Ações de Melhoria", actions_count)
        
        with col4:
            voc_count = len(supabase.table('voc_items').select("*").execute().data or [])
            st.metric("VOCs Coletados", voc_count)
            
    except Exception as e:
        st.error(f"Erro ao buscar estatísticas: {str(e)}")
    
    st.divider()
    
    # Scripts SQL para correção
    st.header("🛠️ Scripts de Correção")
    
    with st.expander("📝 Ver Script SQL para criar tabelas ausentes"):
        st.code("""
-- Script para criar todas as tabelas necessárias

-- 1. Projects
CREATE TABLE IF NOT EXISTS projects (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_name VARCHAR(255) UNIQUE NOT NULL,
    problem_statement TEXT,
    business_case TEXT,
    project_scope TEXT,
    goal_statement TEXT,
    start_date DATE,
    end_date DATE,
    team_members TEXT,
    project_sponsor VARCHAR(255),
    project_leader VARCHAR(255),
    primary_metric VARCHAR(255),
    baseline_value DECIMAL(10,2),
    target_value DECIMAL(10,2),
    expected_savings DECIMAL(10,2),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. VOC Items
CREATE TABLE IF NOT EXISTS voc_items (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_name VARCHAR(255) REFERENCES projects(project_name) ON DELETE CASCADE,
    customer_segment VARCHAR(255),
    customer_need TEXT,
    current_performance TEXT,
    priority VARCHAR(50),
    csat_score INTEGER,
    target_csat INTEGER,
    ctq TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. SIPOC
CREATE TABLE IF NOT EXISTS sipoc (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_name VARCHAR(255) REFERENCES projects(project_name) ON DELETE CASCADE,
    suppliers TEXT,
    inputs TEXT,
    process TEXT,
    outputs TEXT,
    customers TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Continue com as outras tabelas...
        """, language='sql')
    
    # Teste de operações CRUD
    st.divider()
    st.header("🧪 Teste de Operações")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("➕ Teste INSERT", use_container_width=True):
            try:
                test_data = {
                    'project_name': f'TESTE_{datetime.now().strftime("%H%M%S")}',
                    'project_leader': 'Sistema',
                    'problem_statement': 'Teste de inserção',
                    'goal_statement': 'Verificar funcionamento'
                }
                response = supabase.table('projects').insert(test_data).execute()
                st.success("✅ INSERT funcionando")
            except Exception as e:
                st.error(f"❌ Erro: {str(e)}")
    
    with col2:
        if st.button("📖 Teste SELECT", use_container_width=True):
            try:
                response = supabase.table('projects').select("*").limit(1).execute()
                st.success(f"✅ SELECT funcionando ({len(response.data)} registro)")
            except Exception as e:
                st.error(f"❌ Erro: {str(e)}")
    
    with col3:
        if st.button("✏️ Teste UPDATE", use_container_width=True):
            try:
                # Buscar um projeto de teste
                test_projects = supabase.table('projects').select("*").like('project_name', 'TESTE_%').limit(1).execute()
                if test_projects.data:
                    project_name = test_projects.data[0]['project_name']
                    response = supabase.table('projects').update({'status': 'test_updated'}).eq('project_name', project_name).execute()
                    st.success("✅ UPDATE funcionando")
                else:
                    st.warning("⚠️ Nenhum projeto de teste para atualizar")
            except Exception as e:
                st.error(f"❌ Erro: {str(e)}")
    
    with col4:
        if st.button("🗑️ Limpar Testes", use_container_width=True):
            try:
                response = supabase.table('projects').delete().like('project_name', 'TESTE_%').execute()
                st.success("✅ DELETE funcionando")
            except Exception as e:
                st.error(f"❌ Erro: {str(e)}")
    
    # Logs e debug
    st.divider()
    st.header("🐛 Debug e Logs")
    
    with st.expander("📋 Ver Configuração Atual"):
        config_info = {
            "Supabase URL configurada": bool(os.environ.get("SUPABASE_URL") or ("supabase" in st.secrets)),
            "Supabase Key configurada": bool(os.environ.get("SUPABASE_KEY") or ("supabase" in st.secrets)),
            "Cliente inicializado": supabase is not None,
            "Python Version": st.runtime.sys.version,
            "Streamlit Version": st.__version__
        }
        
        for key, value in config_info.items():
            st.write(f"**{key}:** {value}")
    
    with st.expander("💾 Exportar Estrutura do Banco"):
        if st.button("Gerar Relatório de Estrutura"):
            report = []
            for table in expected_tables:
                try:
                    response = supabase.table(table).select("*", count='exact').execute()
                    report.append({
                        'Tabela': table,
                        'Status': 'OK',
                        'Registros': len(response.data) if response.data else 0
                    })
                except:
                    report.append({
                        'Tabela': table,
                        'Status': 'ERRO',
                        'Registros': 0
                    })
            
            df_report = pd.DataFrame(report)
            csv = df_report.to_csv(index=False)
            
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"diagnostico_supabase_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

else:
    st.error("❌ Supabase não está conectado")
    
    st.subheader("📚 Como Configurar")
    
    st.markdown("""
    ### Opção 1: Usando Streamlit Secrets (Recomendado para Streamlit Cloud)
    
    1. Crie um arquivo `.streamlit/secrets.toml` no seu projeto:
    ```toml
    [supabase]
    url = "sua-url-do-supabase"
    key = "sua-chave-anon-do-supabase"
    ```
    
    ### Opção 2: Usando Variáveis de Ambiente
    
    1. Crie um arquivo `.env`:
    ```
    SUPABASE_URL=sua-url-do-supabase
    SUPABASE_KEY=sua-chave-anon-do-supabase
    ```
    
    ### Onde encontrar as credenciais:
    
    1. Acesse [Supabase Dashboard](https://app.supabase.com)
    2. Selecione seu projeto
    3. Vá em **Settings** → **API**
    4. Copie:
       - **Project URL** → sua URL
       - **anon public** → sua chave
    """)

# Footer
st.divider()
st.caption("🔍 Diagnóstico Supabase - Green Belt System")
st.caption(f"Última verificação: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
