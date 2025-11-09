import streamlit as st
import pandas as pd
from datetime import datetime
import os
import sys  # Adicionar esta importação
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
    
    # Criar DataFrame para mostrar status
    table_status = []
    
    for table_name in expected_tables:
        try:
            # Tentar fazer uma query simples
            response = supabase.table(table_name).select("*", count='exact').limit(0).execute()
            count = response.count if hasattr(response, 'count') else 0
            
            table_status.append({
                'Tabela': table_name,
                'Status': '✅ OK',
                'Registros': count,
                'Erro': None
            })
            
        except Exception as e:
            error_msg = str(e)
            if "not exist" in error_msg or "not found" in error_msg:
                status = '❌ Não existe'
            else:
                status = '⚠️ Erro'
            
            table_status.append({
                'Tabela': table_name,
                'Status': status,
                'Registros': 0,
                'Erro': error_msg[:50] if len(error_msg) > 50 else error_msg
            })
    
    # Mostrar em DataFrame
    df_status = pd.DataFrame(table_status)
    
    # Colorir baseado no status
    def color_status(val):
        if '✅' in str(val):
            return 'background-color: #d4edda'
        elif '❌' in str(val):
            return 'background-color: #f8d7da'
        elif '⚠️' in str(val):
            return 'background-color: #fff3cd'
        return ''
    
    styled_df = df_status.style.applymap(color_status, subset=['Status'])
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    # Resumo
    col1, col2, col3 = st.columns(3)
    with col1:
        ok_count = len([s for s in table_status if '✅' in s['Status']])
        st.metric("✅ Tabelas OK", ok_count)
    with col2:
        missing_count = len([s for s in table_status if '❌' in s['Status']])
        st.metric("❌ Tabelas Ausentes", missing_count)
    with col3:
        error_count = len([s for s in table_status if '⚠️' in s['Status']])
        st.metric("⚠️ Tabelas com Erro", error_count)
    
    st.divider()
    
    # Estatísticas gerais
    st.subheader("📈 Estatísticas Gerais")
    
    stats_data = {}
    
    # Coletar estatísticas apenas de tabelas que existem
    for item in table_status:
        if '✅' in item['Status']:
            stats_data[item['Tabela']] = item['Registros']
    
    if stats_data:
        # Mostrar principais métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Projetos", stats_data.get('projects', 0))
        with col2:
            st.metric("Análises Realizadas", stats_data.get('analyses', 0))
        with col3:
            st.metric("Ações de Melhoria", stats_data.get('improvement_actions', 0))
        with col4:
            st.metric("VOCs Coletados", stats_data.get('voc_items', 0))
        
        # Gráfico de barras com registros por tabela
        if len(stats_data) > 0:
            st.divider()
            st.subheader("📊 Registros por Tabela")
            
            import plotly.express as px
            
            df_chart = pd.DataFrame(list(stats_data.items()), columns=['Tabela', 'Registros'])
            df_chart = df_chart.sort_values('Registros', ascending=True)
            
            fig = px.bar(df_chart, x='Registros', y='Tabela', orientation='h',
                        title='Quantidade de Registros por Tabela')
            st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Scripts SQL para correção
    st.header("🛠️ Scripts de Correção")
    
    if missing_count > 0:
        st.warning(f"⚠️ {missing_count} tabela(s) precisam ser criadas")
        
        with st.expander("📝 Ver Script SQL para criar tabelas ausentes"):
            missing_tables = [item['Tabela'] for item in table_status if '❌' in item['Status']]
            
            sql_scripts = {
                'projects': """
CREATE TABLE projects (
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
);""",
                'voc_items': """
CREATE TABLE voc_items (
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
);""",
                'sipoc': """
CREATE TABLE sipoc (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_name VARCHAR(255) REFERENCES projects(project_name) ON DELETE CASCADE,
    suppliers TEXT,
    inputs TEXT,
    process TEXT,
    outputs TEXT,
    customers TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);""",
                'measurements': """
CREATE TABLE measurements (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_name VARCHAR(255) REFERENCES projects(project_name) ON DELETE CASCADE,
    metric_name VARCHAR(255),
    metric_value DECIMAL(15,6),
    unit VARCHAR(50),
    measurement_date DATE,
    operator VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);""",
                'process_data': """
CREATE TABLE process_data (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_name VARCHAR(255) REFERENCES projects(project_name) ON DELETE CASCADE,
    data JSONB,
    data_type VARCHAR(100),
    collection_date DATE,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);""",
                'analyses': """
CREATE TABLE analyses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_name VARCHAR(255) REFERENCES projects(project_name) ON DELETE CASCADE,
    analysis_type VARCHAR(100),
    results JSONB,
    conclusions TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);""",
                'improvement_actions': """
CREATE TABLE improvement_actions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_name VARCHAR(255) REFERENCES projects(project_name) ON DELETE CASCADE,
    action_title VARCHAR(255),
    description TEXT,
    responsible VARCHAR(255),
    due_date DATE,
    status VARCHAR(50) DEFAULT 'Não Iniciado',
    impact_level VARCHAR(50),
    effort_level VARCHAR(50),
    priority INTEGER,
    success_criteria TEXT,
    resources_needed TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);""",
                'brainstorm_ideas': """
CREATE TABLE brainstorm_ideas (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_name VARCHAR(255) REFERENCES projects(project_name) ON DELETE CASCADE,
    title VARCHAR(255),
    description TEXT,
    category VARCHAR(100),
    expected_impact VARCHAR(50),
    implementation_effort VARCHAR(50),
    responsible VARCHAR(255),
    benefits TEXT,
    risks TEXT,
    status VARCHAR(50) DEFAULT 'proposed',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);""",
                'control_plans': """
CREATE TABLE control_plans (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_name VARCHAR(255) REFERENCES projects(project_name) ON DELETE CASCADE,
    control_item VARCHAR(255),
    specification TEXT,
    measurement_method TEXT,
    sample_size VARCHAR(50),
    frequency VARCHAR(100),
    responsible VARCHAR(255),
    action_plan TEXT,
    control_type VARCHAR(50),
    critical_level VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);""",
                'lessons_learned': """
CREATE TABLE lessons_learned (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_name VARCHAR(255) REFERENCES projects(project_name) ON DELETE CASCADE,
    lesson_type VARCHAR(100),
    description TEXT,
    context TEXT,
    recommendations TEXT,
    impact VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);""",
                'collection_plans': """
CREATE TABLE collection_plans (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_name VARCHAR(255) REFERENCES projects(project_name) ON DELETE CASCADE,
    metric_name VARCHAR(255),
    collection_method TEXT,
    frequency VARCHAR(100),
    responsible VARCHAR(255),
    start_date DATE,
    end_date DATE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);"""
            }
            
            # Mostrar apenas scripts das tabelas que faltam
            full_script = "-- Script para criar tabelas ausentes\n\n"
            for table in missing_tables:
                if table in sql_scripts:
                    full_script += f"-- {table}\n{sql_scripts[table]}\n\n"
            
            st.code(full_script, language='sql')
            
            # Botão para copiar
            st.download_button(
                label="📥 Download Script SQL",
                data=full_script,
                file_name=f"create_missing_tables_{datetime.now().strftime('%Y%m%d')}.sql",
                mime="text/plain"
            )
    
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
                st.error(f"❌ Erro: {str(e)[:100]}")
    
    with col2:
        if st.button("📖 Teste SELECT", use_container_width=True):
            try:
                response = supabase.table('projects').select("*").limit(1).execute()
                count = len(response.data) if response.data else 0
                st.success(f"✅ SELECT OK ({count} registro)")
            except Exception as e:
                st.error(f"❌ Erro: {str(e)[:100]}")
    
    with col3:
        if st.button("✏️ Teste UPDATE", use_container_width=True):
            try:
                test_projects = supabase.table('projects').select("*").like('project_name', 'TESTE_%').limit(1).execute()
                if test_projects.data:
                    project_name = test_projects.data[0]['project_name']
                    response = supabase.table('projects').update({'status': 'updated'}).eq('project_name', project_name).execute()
                    st.success("✅ UPDATE funcionando")
                else:
                    st.warning("⚠️ Sem projeto de teste")
            except Exception as e:
                st.error(f"❌ Erro: {str(e)[:100]}")
    
    with col4:
        if st.button("🗑️ Limpar Testes", use_container_width=True):
            try:
                response = supabase.table('projects').delete().like('project_name', 'TESTE_%').execute()
                st.success("✅ DELETE funcionando")
            except Exception as e:
                st.error(f"❌ Erro: {str(e)[:100]}")
    
    # Logs e debug
    st.divider()
    st.header("🐛 Debug e Logs")
    
    with st.expander("📋 Ver Configuração Atual"):
        # CORREÇÃO: Usar sys diretamente ao invés de st.runtime.sys
        config_info = {
            "Supabase URL configurada": bool(os.environ.get("SUPABASE_URL") or ("supabase" in st.secrets)),
            "Supabase Key configurada": bool(os.environ.get("SUPABASE_KEY") or ("supabase" in st.secrets)),
            "Cliente inicializado": supabase is not None,
            "Python Version": sys.version.split()[0],  # Pega apenas a versão principal
            "Streamlit Version": st.__version__ if hasattr(st, '__version__') else "N/A",
            "Sistema Operacional": os.name
        }
        
        for key, value in config_info.items():
            if value == True:
                st.write(f"✅ **{key}:** {value}")
            elif value == False:
                st.write(f"❌ **{key}:** {value}")
            else:
                st.write(f"**{key}:** {value}")
    
    with st.expander("💾 Exportar Relatório de Diagnóstico"):
        if st.button("Gerar Relatório Completo"):
            # Criar relatório
            report = {
                'timestamp': datetime.now().isoformat(),
                'connection_status': 'connected' if supabase else 'disconnected',
                'tables': table_status,
                'statistics': stats_data if 'stats_data' in locals() else {},
                'config': config_info
            }
            
            # Exportar como JSON
            import json
            json_str = json.dumps(report, indent=2, default=str)
            
            st.download_button(
                label="📥 Download JSON",
                data=json_str,
                file_name=f"diagnostico_completo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

else:
    st.error("❌ Supabase não está conectado")
    
    st.subheader("📚 Como Configurar")
    
    tab1, tab2 = st.tabs(["Streamlit Cloud", "Local"])
    
    with tab1:
        st.markdown("""
        ### Configuração para Streamlit Cloud
        
        1. No seu app no Streamlit Cloud, vá em **Settings** → **Secrets**
        2. Adicione as seguintes linhas:
        
        ```toml
        [supabase]
        url = "sua-url-do-supabase"
        key = "sua-chave-anon-do-supabase"
        ```
        
        3. Clique em **Save** e reinicie o app
        """)
    
    with tab2:
        st.markdown("""
        ### Configuração Local
        
        1. Crie um arquivo `.streamlit/secrets.toml` no seu projeto:
        
        ```toml
        [supabase]
        url = "sua-url-do-supabase"
        key = "sua-chave-anon-do-supabase"
        ```
        
        2. Ou use variáveis de ambiente criando um arquivo `.env`:
        
        ```bash
        SUPABASE_URL=sua-url-do-supabase
        SUPABASE_KEY=sua-chave-anon-do-supabase
        ```
        """)
    
    st.divider()
    
    st.info("""
    ### 🔑 Onde encontrar as credenciais:
    
    1. Acesse [app.supabase.com](https://app.supabase.com)
    2. Selecione seu projeto
    3. Vá em **Settings** → **API**
    4. Copie:
       - **Project URL** (sua URL)
       - **anon public** (sua chave)
    """)

# Footer
st.divider()
st.caption("🔍 Diagnóstico Supabase - Green Belt System")
st.caption(f"Última verificação: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
