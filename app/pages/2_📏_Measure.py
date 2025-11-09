import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import numpy as np
from scipy.stats import norm
import os
from supabase import create_client, Client
import time

# Configuração da página
st.set_page_config(
    page_title="Measure - Green Belt",
    page_icon="📏",
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

def clean_dataframe_for_json(df):
    """Limpa DataFrame para ser compatível com JSON"""
    df_clean = df.copy()
    
    # Substituir valores problemáticos
    df_clean = df_clean.replace([np.nan, np.inf, -np.inf], None)
    
    # Converter tipos de dados problemáticos
    for col in df_clean.columns:
        if df_clean[col].dtype == 'object':
            df_clean[col] = df_clean[col].astype(str)
        elif df_clean[col].dtype in ['datetime64[ns]', 'timedelta64[ns]']:
            df_clean[col] = df_clean[col].astype(str)
    
    return df_clean

def auto_clean_numeric_columns(df):
    """Tenta limpar e converter colunas para numérico automaticamente"""
    df_clean = df.copy()
    
    for col in df_clean.columns:
        try:
            if df_clean[col].dtype == 'object':
                df_clean[col] = df_clean[col].astype(str).str.replace(',', '.').str.strip()
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        except:
            pass
    
    return df_clean

def load_project_from_db(project_name):
    """Carrega dados do projeto do banco"""
    if not supabase:
        return None
    
    try:
        response = supabase.table('projects').select("*").eq('project_name', project_name).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Erro ao carregar projeto: {str(e)}")
        return None

@st.cache_data(ttl=300)
def list_projects():
    """Lista todos os projetos disponíveis"""
    if not supabase:
        return []
    
    try:
        response = supabase.table('projects').select("project_name, project_leader, status").execute()
        if response.data:
            return response.data
        return []
    except Exception as e:
        st.error(f"Erro ao listar projetos: {str(e)}")
        return []

def save_collection_plan(project_name, plan_data):
    """Salva plano de coleta de dados no banco"""
    if not supabase:
        return False
    
    try:
        plan_data['project_name'] = project_name
        plan_data['created_at'] = datetime.now().isoformat()
        response = supabase.table('collection_plans').insert(plan_data).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar plano: {str(e)}")
        return False

def save_process_data(project_name, data_df):
    """Salva dados do processo no banco"""
    if not supabase:
        return False
    
    try:
        data_df_clean = data_df.replace([np.nan, np.inf, -np.inf], None)
        data_json = data_df_clean.to_dict('records')
        
        record = {
            'project_name': project_name,
            'data': data_json,
            'collection_date': datetime.now().date().isoformat(),
            'uploaded_at': datetime.now().isoformat()
        }
        
        response = supabase.table('process_data').insert(record).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar dados do processo: {str(e)}")
        return False

@st.cache_data(ttl=60)
def load_process_data(project_name):
    """Carrega dados do processo do banco"""
    if not supabase:
        return None
    
    try:
        response = supabase.table('process_data').select("*").eq('project_name', project_name).order('uploaded_at', desc=True).limit(1).execute()
        if response.data and len(response.data) > 0:
            data = response.data[0].get('data', [])
            if data:
                return pd.DataFrame(data)
        return None
    except Exception as e:
        st.error(f"Erro ao carregar dados do processo: {str(e)}")
        return None

############################################################################################################################################################################################################################################
# ========================= SIDEBAR =========================

with st.sidebar:
    st.header("🗂️ Seleção de Projeto")
    
    # Verificar conexão com Supabase
    if not supabase:
        st.error("⚠️ Supabase não configurado")
        st.info("""
        **Configure o Supabase:**
        1. Adicione as credenciais em `.streamlit/secrets.toml`
        2. Ou configure as variáveis de ambiente
        """)
    else:
        st.success("✅ Conectado ao Supabase")
    
    st.divider()
    
    # Listar e selecionar projetos
    if supabase:
        projects = list_projects()
        
        if projects:
            project_names = [p['project_name'] for p in projects]
            
            # Determinar índice padrão
            default_index = 0
            if 'project_name' in st.session_state and st.session_state.project_name in project_names:
                default_index = project_names.index(st.session_state.project_name) + 1
            
            selected_project = st.selectbox(
                "Selecione um projeto:",
                [""] + project_names,
                index=default_index,
                key="sidebar_project_select"
            )
            
            # Botão para carregar projeto
            if selected_project:
                if st.button("📂 Carregar Projeto", type="primary", use_container_width=True, key="load_project_btn"):
                    with st.spinner("Carregando projeto..."):
                        project_data = load_project_from_db(selected_project)
                        if project_data:
                            st.session_state.project_name = selected_project
                            st.session_state.project_data = project_data
                            st.success(f"✅ Projeto '{selected_project}' carregado!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ Erro ao carregar projeto")
        else:
            st.warning("📭 Nenhum projeto encontrado")
            st.info("Crie um projeto na página **Define** primeiro")
    
    # Mostrar projeto ativo
    if 'project_name' in st.session_state:
        st.divider()
        
        # Card do projeto ativo
        with st.container():
            st.success("📁 **Projeto Ativo:**")
            st.markdown(f"### {st.session_state.project_name}")
            
            project_data = st.session_state.get('project_data', {})
            
            if project_data:
                # Informações do projeto
                col1, col2 = st.columns(2)
                
                with col1:
                    st.caption("👤 **Líder:**")
                    st.write(project_data.get('project_leader', 'N/A'))
                
                with col2:
                    st.caption("📊 **Status:**")
                    status = project_data.get('status', 'N/A')
                    if status == 'active':
                        st.success("✅ Ativo")
                    elif status == 'completed':
                        st.info("🎯 Concluído")
                    else:
                        st.write(status)
                
                st.caption("📈 **Métrica Principal:**")
                st.write(project_data.get('primary_metric', 'N/A'))
                
                # Dados do projeto
                if project_data.get('baseline_value'):
                    st.caption("📍 **Baseline:**")
                    st.write(f"{project_data.get('baseline_value', 'N/A')}")
                
                if project_data.get('target_value'):
                    st.caption("🎯 **Meta:**")
                    st.write(f"{project_data.get('target_value', 'N/A')}")
                
                # Datas
                if project_data.get('start_date'):
                    st.caption("📅 **Início:**")
                    st.write(project_data.get('start_date', 'N/A'))
        
        st.divider()
        
        # Botão para trocar de projeto
        if st.button("🔄 Trocar Projeto", use_container_width=True, key="change_project_btn"):
            if 'project_name' in st.session_state:
                del st.session_state.project_name
            if 'project_data' in st.session_state:
                del st.session_state.project_data
            st.rerun()
    
    # Rodapé da sidebar
    st.divider()
    st.caption("📏 **Fase:** Measure")
    st.caption("🔧 **Green Belt Project**")

############################################################################################################################################################################################################################################
# ========================= INTERFACE PRINCIPAL =========================

st.title("📏 Measure — Medição e Coleta de Dados")
st.markdown("**Objetivo:** Coletar dados confiáveis para análise do processo")

st.divider()

# ============= VERIFICAÇÃO DE PROJETO =============
if 'project_name' not in st.session_state:
    st.warning("⚠️ Nenhum projeto selecionado.")
    
    col_warn1, col_warn2 = st.columns([2, 1])
    
    with col_warn1:
        st.info("""
        **Para começar:**
        1. 👈 Use a barra lateral para selecionar um projeto
        2. Ou crie um novo projeto na página **Define**
        """)
    
    with col_warn2:
        if st.button("➕ Criar Novo Projeto", type="primary", use_container_width=True):
            st.switch_page("pages/1_📋_Define.py")
    
    # Mostrar projetos disponíveis
    if supabase:
        projects = list_projects()
        if projects:
            st.divider()
            st.subheader("📂 Projetos Disponíveis")
            
            # Criar DataFrame formatado
            df = pd.DataFrame(projects)
            
            # Renomear colunas para português
            column_mapping = {
                'project_name': 'Nome do Projeto',
                'project_leader': 'Líder',
                'status': 'Status'
            }
            
            if all(col in df.columns for col in column_mapping.keys()):
                df = df.rename(columns=column_mapping)
            
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.caption("💡 **Dica:** Selecione um projeto na barra lateral para começar")
        else:
            st.info("📭 Nenhum projeto encontrado. Crie um na página Define.")
    
    st.stop()

# ============= PROJETO SELECIONADO =============
# Banner do projeto ativo
col_banner1, col_banner2, col_banner3 = st.columns([2, 1, 1])

with col_banner1:
    st.info(f"📁 **Projeto Ativo:** {st.session_state.project_name}")

with col_banner2:
    # Carregar dados do projeto se não estiver em cache
    if 'project_data' not in st.session_state:
        with st.spinner("Carregando dados do projeto..."):
            project_data = load_project_from_db(st.session_state.project_name)
            if project_data:
                st.session_state.project_data = project_data
    
    project_data = st.session_state.get('project_data', {})
    
    if project_data:
        metric = project_data.get('primary_metric', 'N/A')
        st.metric("📊 Métrica", metric)

with col_banner3:
    if project_data:
        baseline = project_data.get('baseline_value', 'N/A')
        target = project_data.get('target_value', 'N/A')
        
        if baseline != 'N/A' and target != 'N/A':
            try:
                improvement = ((float(baseline) - float(target)) / float(baseline)) * 100
                st.metric("🎯 Meta", f"{improvement:.1f}%")
            except:
                st.metric("🎯 Meta", "Definida")
        else:
            st.metric("🎯 Meta", "Não definida")

st.divider()

# ============= NAVEGAÇÃO POR TABS =============
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Data Collection Plan",
    "🔍 Measurement System Analysis (MSA)",
    "📊 Process Capability",
    "📈 Data Visualization"
])

############################################################################################################################################################################################################################################
# ========================= TAB 1: DATA COLLECTION PLAN =========================

# ========================= TAB 1: DATA COLLECTION PLAN =========================

with tab1:
    st.header("📋 Plano de Coleta de Dados")
    st.markdown("Defina **como**, **quando** e **quem** coletará os dados do processo")
    
    st.divider()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("collection_plan_form", clear_on_submit=True):
            st.subheader("➕ Adicionar Novo Plano")
            
            col_form1, col_form2 = st.columns(2)
            
            with col_form1:
                metric = st.text_input(
                    "Métrica a ser coletada *", 
                    value=st.session_state.get('project_data', {}).get('primary_metric', ''),
                    placeholder="Ex: Tempo de ciclo, Defeitos, Temperatura..."
                )
                
                collection_method = st.selectbox(
                    "Método de coleta *",
                    ["Manual", "Automático", "Sistema", "Inspeção", "Amostragem", "Sensor"],
                    help="Como os dados serão coletados"
                )
                
                frequency = st.selectbox(
                    "Frequência *",
                    ["Horária", "Diária", "Semanal", "Mensal", "Por lote", "Contínua", "Sob demanda"],
                    help="Com que frequência os dados serão coletados"
                )
            
            with col_form2:
                responsible = st.text_input(
                    "Responsável pela coleta *",
                    placeholder="Nome do responsável"
                )
                
                col_date1, col_date2 = st.columns(2)
                with col_date1:
                    start_date = st.date_input(
                        "Data início *", 
                        value=datetime.now(),
                        help="Quando a coleta começará"
                    )
                with col_date2:
                    end_date = st.date_input(
                        "Data fim",
                        help="Quando a coleta terminará (opcional)"
                    )
                
                sample_size = st.number_input(
                    "Tamanho da amostra",
                    min_value=1,
                    value=30,
                    help="Quantidade de medições por coleta"
                )
            
            notes = st.text_area(
                "Observações / Instruções",
                height=100,
                placeholder="Adicione instruções especiais, cuidados, equipamentos necessários..."
            )
            
            submitted = st.form_submit_button("💾 Adicionar Plano", type="primary", use_container_width=True)
            
            if submitted:
                if metric and responsible:
                    plan = {
                        'metric_name': metric,
                        'collection_method': collection_method,
                        'frequency': frequency,
                        'responsible': responsible,
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat() if end_date else None,
                        'sample_size': sample_size,
                        'notes': notes,
                        'created_at': datetime.now().isoformat()
                    }
                    
                    # Inicializar lista se não existir
                    if 'collection_plans' not in st.session_state:
                        st.session_state.collection_plans = []
                    
                    st.session_state.collection_plans.append(plan)
                    
                    # Salvar no banco
                    if supabase:
                        if save_collection_plan(st.session_state.project_name, plan):
                            st.success("✅ Plano adicionado e salvo no banco de dados!")
                            st.balloons()
                        else:
                            st.warning("⚠️ Plano salvo localmente (erro ao salvar no banco)")
                    else:
                        st.success("✅ Plano adicionado localmente!")
                    
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ Preencha todos os campos obrigatórios (*)")
    
    with col2:
        st.info("""
        **📚 Guia de Coleta de Dados**
        
        **Métodos de Coleta:**
        - **Manual:** Registro em papel/planilha
        - **Automático:** Sistema integrado
        - **Sistema:** Software específico
        - **Inspeção:** Verificação visual/medição
        - **Amostragem:** Coleta de amostras
        - **Sensor:** Dispositivos automáticos
        
        **Frequências Recomendadas:**
        - **Processo estável:** Semanal/Mensal
        - **Processo variável:** Diária/Horária
        - **Alta criticidade:** Contínua
        
        **💡 Dicas:**
        - Defina tamanho de amostra adequado
        - Documente o procedimento
        - Treine os coletadores
        - Valide o sistema de medição
        """)
        
        st.divider()
        
        # Estatísticas rápidas
        if 'collection_plans' in st.session_state and st.session_state.collection_plans:
            st.metric("📊 Planos Cadastrados", len(st.session_state.collection_plans))
            
            # Contar métodos
            methods = [p['collection_method'] for p in st.session_state.collection_plans]
            most_common = max(set(methods), key=methods.count) if methods else "N/A"
            st.caption(f"**Método mais usado:** {most_common}")
    
    # ============= PLANOS CADASTRADOS =============
    if 'collection_plans' in st.session_state and st.session_state.collection_plans:
        st.divider()
        st.subheader("📋 Planos de Coleta Cadastrados")
        
        # Métricas resumo
        col_metric1, col_metric2, col_metric3, col_metric4 = st.columns(4)
        
        with col_metric1:
            st.metric("Total de Planos", len(st.session_state.collection_plans))
        
        with col_metric2:
            unique_metrics = len(set([p['metric_name'] for p in st.session_state.collection_plans]))
            st.metric("Métricas Únicas", unique_metrics)
        
        with col_metric3:
            unique_responsible = len(set([p['responsible'] for p in st.session_state.collection_plans]))
            st.metric("Responsáveis", unique_responsible)
        
        with col_metric4:
            # Calcular total de amostras esperadas
            total_samples = sum([p.get('sample_size', 0) for p in st.session_state.collection_plans])
            st.metric("Amostras Totais", total_samples)
        
        st.divider()
        
        # Tabela de planos
        plans_df = pd.DataFrame(st.session_state.collection_plans)
        
        # Selecionar colunas para exibição
        display_columns = ['metric_name', 'collection_method', 'frequency', 'responsible', 'start_date', 'sample_size']
        available_columns = [col for col in display_columns if col in plans_df.columns]
        
        # Renomear colunas para português
        column_names = {
            'metric_name': 'Métrica',
            'collection_method': 'Método',
            'frequency': 'Frequência',
            'responsible': 'Responsável',
            'start_date': 'Data Início',
            'sample_size': 'Amostra'
        }
        
        display_df = plans_df[available_columns].copy()
        display_df = display_df.rename(columns=column_names)
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Detalhes expandíveis
        st.subheader("🔍 Detalhes dos Planos")
        
        for idx, plan in enumerate(st.session_state.collection_plans):
            with st.expander(f"📌 {plan['metric_name']} - {plan['responsible']}"):
                col_detail1, col_detail2 = st.columns(2)
                
                with col_detail1:
                    st.write(f"**Método:** {plan['collection_method']}")
                    st.write(f"**Frequência:** {plan['frequency']}")
                    st.write(f"**Responsável:** {plan['responsible']}")
                    st.write(f"**Tamanho da Amostra:** {plan.get('sample_size', 'N/A')}")
                
                with col_detail2:
                    st.write(f"**Data Início:** {plan['start_date']}")
                    if plan.get('end_date'):
                        st.write(f"**Data Fim:** {plan['end_date']}")
                    else:
                        st.write(f"**Data Fim:** Não definida")
                    
                    if plan.get('created_at'):
                        created = datetime.fromisoformat(plan['created_at']).strftime('%d/%m/%Y %H:%M')
                        st.caption(f"Criado em: {created}")
                
                if plan.get('notes'):
                    st.markdown("**📝 Observações:**")
                    st.info(plan['notes'])
                
                # Botão para remover
                if st.button(f"🗑️ Remover Plano", key=f"remove_plan_{idx}"):
                    st.session_state.collection_plans.pop(idx)
                    st.success("Plano removido!")
                    st.rerun()
        
        # Exportar planos
        st.divider()
        
        col_export1, col_export2 = st.columns(2)
        
        with col_export1:
            # Download CSV
            csv = plans_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Planos (CSV)",
                data=csv,
                file_name=f"planos_coleta_{st.session_state.project_name}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col_export2:
            # Limpar todos os planos
            if st.button("🗑️ Limpar Todos os Planos", type="secondary", use_container_width=True):
                if st.session_state.get('confirm_clear_plans', False):
                    st.session_state.collection_plans = []
                    st.session_state.confirm_clear_plans = False
                    st.success("Todos os planos foram removidos!")
                    st.rerun()
                else:
                    st.session_state.confirm_clear_plans = True
                    st.warning("⚠️ Clique novamente para confirmar")
    
    else:
        st.info("📭 Nenhum plano de coleta cadastrado ainda. Use o formulário acima para adicionar o primeiro plano.")


############################################################################################################################################################################################################################################

# ========================= TAB 2: MSA (MEASUREMENT SYSTEM ANALYSIS) =========================

with tab2:
    st.header("🔍 Measurement System Analysis (MSA)")
    st.markdown("**Objetivo:** Avaliar a **Repetibilidade** e **Reprodutibilidade** do sistema de medição")
    
    st.divider()
    
    # Informações sobre MSA
    with st.expander("ℹ️ O que é MSA?"):
        st.markdown("""
        **MSA (Measurement System Analysis)** avalia se o sistema de medição é adequado para o uso pretendido.
        
        **Principais componentes:**
        - **Repetibilidade:** Variação quando a mesma pessoa mede a mesma peça várias vezes
        - **Reprodutibilidade:** Variação entre diferentes operadores medindo a mesma peça
        - **Estabilidade:** Variação ao longo do tempo
        - **Linearidade:** Precisão em toda a faixa de medição
        
        **Critérios de aceitação:**
        - < 10% da tolerância: Sistema **EXCELENTE**
        - 10-30% da tolerância: Sistema **ACEITÁVEL**
        - > 30% da tolerância: Sistema **PRECISA MELHORAR**
        """)
    
    st.divider()
    
    # Upload de arquivo
    col_upload1, col_upload2 = st.columns([2, 1])
    
    with col_upload1:
        uploaded_file = st.file_uploader(
            "📤 Faça upload dos dados de MSA (CSV, Excel)",
            type=['csv', 'xlsx', 'xls'],
            help="Arquivo deve conter as medições realizadas",
            key="msa_upload"
        )
    
    with col_upload2:
        st.info("""
        **Formato esperado:**
        - Colunas com medições
        - Valores numéricos
        - Sem células vazias
        """)
    
    if uploaded_file is not None:
        try:
            # Detectar extensão
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            st.info(f"📄 Arquivo: **{uploaded_file.name}**")
            
            # Ler arquivo
            with st.spinner("Lendo arquivo..."):
                if file_extension == 'csv':
                    try:
                        msa_data = pd.read_csv(uploaded_file, encoding='utf-8')
                    except UnicodeDecodeError:
                        uploaded_file.seek(0)
                        msa_data = pd.read_csv(uploaded_file, encoding='latin-1')
                        st.warning("⚠️ Arquivo lido com encoding latin-1")
                
                elif file_extension in ['xlsx', 'xls']:
                    msa_data = pd.read_excel(uploaded_file)
                
                else:
                    st.error("❌ Formato não suportado")
                    st.stop()
            
            st.success(f"✅ Arquivo carregado: {len(msa_data)} linhas, {len(msa_data.columns)} colunas")
            
            # Opção de conversão automática
            if st.checkbox("🧹 Converter colunas automaticamente para numérico", value=True, key="auto_clean_msa"):
                with st.spinner("Convertendo..."):
                    msa_data = auto_clean_numeric_columns(msa_data)
                st.success("✅ Conversão automática aplicada")
            
            # Botão salvar
            if supabase:
                if st.button("💾 Salvar dados MSA no projeto", key="save_msa_btn"):
                    with st.spinner("Salvando..."):
                        msa_data_clean = clean_dataframe_for_json(msa_data)
                        if save_process_data(st.session_state.project_name, msa_data_clean):
                            st.success("✅ Dados MSA salvos no projeto!")
                            st.balloons()
                        else:
                            st.error("❌ Erro ao salvar")
            
            st.divider()
            
            # Preview dos dados
            st.subheader("📊 Preview dos Dados")
            
            col_prev1, col_prev2 = st.columns([3, 1])
            
            with col_prev1:
                num_rows_preview = st.slider("Linhas para visualizar:", 5, 50, 10, key="msa_preview")
            
            with col_prev2:
                st.metric("Total de Linhas", len(msa_data))
            
            st.dataframe(msa_data.head(num_rows_preview), use_container_width=True)
            
            st.divider()
            
            # Detectar colunas numéricas
            all_cols = msa_data.columns.tolist()
            numeric_cols = []
            
            for col in all_cols:
                try:
                    test_numeric = pd.to_numeric(msa_data[col], errors='coerce')
                    if test_numeric.notna().sum() > 0:
                        numeric_cols.append(col)
                except:
                    pass
            
            if len(numeric_cols) == 0:
                st.warning("⚠️ Nenhuma coluna numérica detectada. Mostrando todas as colunas.")
                numeric_cols = all_cols
            
            st.info(f"📊 Colunas numéricas detectadas: **{len(numeric_cols)}**")
            
            # Seleção de coluna para análise
            if len(numeric_cols) > 0:
                
                col_select1, col_select2 = st.columns([2, 1])
                
                with col_select1:
                    analysis_col = st.selectbox(
                        "📌 Selecione a coluna para análise MSA:",
                        numeric_cols,
                        key="msa_col_select"
                    )
                
                with col_select2:
                    # Mostrar info da coluna
                    non_null = msa_data[analysis_col].notna().sum()
                    st.metric("Valores Válidos", non_null)
                
                # Converter e limpar dados
                try:
                    msa_data[analysis_col] = pd.to_numeric(msa_data[analysis_col], errors='coerce')
                    data_col = msa_data[analysis_col].dropna()
                    
                    if len(data_col) == 0:
                        st.error("❌ A coluna selecionada não contém valores numéricos válidos")
                        st.stop()
                    
                    st.success(f"✅ {len(data_col)} medições válidas encontradas")
                    
                    st.divider()
                    
                    # ============= ESTATÍSTICAS DESCRITIVAS =============
                    st.subheader("📊 Estatísticas Descritivas")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Média", f"{data_col.mean():.4f}")
                        st.metric("Mediana", f"{data_col.median():.4f}")
                    
                    with col2:
                        st.metric("Desvio Padrão", f"{data_col.std():.4f}")
                        st.metric("Variância", f"{data_col.var():.4f}")
                    
                    with col3:
                        st.metric("Mínimo", f"{data_col.min():.4f}")
                        st.metric("Máximo", f"{data_col.max():.4f}")
                    
                    with col4:
                        amplitude = data_col.max() - data_col.min()
                        st.metric("Amplitude", f"{amplitude:.4f}")
                        cv = (data_col.std() / data_col.mean() * 100) if data_col.mean() != 0 else 0
                        st.metric("CV%", f"{cv:.2f}%")
                    
                    st.divider()
                    
                    # ============= GRÁFICO DE CONTROLE =============
                    st.subheader("📈 Gráfico de Controle (X-bar)")
                    
                    mean = data_col.mean()
                    std = data_col.std()
                    ucl = mean + 3 * std
                    lcl = mean - 3 * std
                    
                    fig = go.Figure()
                    
                    # Pontos das medições
                    fig.add_trace(go.Scatter(
                        x=list(range(1, len(data_col) + 1)),
                        y=data_col,
                        mode='lines+markers',
                        name='Medições',
                        line=dict(color='#3498DB', width=2),
                        marker=dict(size=6, color='#3498DB')
                    ))
                    
                    # Linha média
                    fig.add_hline(
                        y=mean, 
                        line_dash="solid", 
                        line_color="#2ECC71",
                        line_width=2,
                        annotation_text=f"Média: {mean:.3f}",
                        annotation_position="right"
                    )
                    
                    # Limites de controle
                    fig.add_hline(
                        y=ucl, 
                        line_dash="dash", 
                        line_color="#E74C3C",
                        line_width=2,
                        annotation_text=f"UCL: {ucl:.3f}",
                        annotation_position="right"
                    )
                    
                    fig.add_hline(
                        y=lcl, 
                        line_dash="dash", 
                        line_color="#E74C3C",
                        line_width=2,
                        annotation_text=f"LCL: {lcl:.3f}",
                        annotation_position="right"
                    )
                    
                    # Destacar pontos fora de controle
                    out_of_control = data_col[(data_col > ucl) | (data_col < lcl)]
                    if len(out_of_control) > 0:
                        out_indices = out_of_control.index.tolist()
                        fig.add_trace(go.Scatter(
                            x=[i+1 for i in out_indices],
                            y=out_of_control.values,
                            mode='markers',
                            name='Fora de Controle',
                            marker=dict(size=10, color='red', symbol='x')
                        ))
                    
                    fig.update_layout(
                        title="Gráfico de Controle X-bar (Médias)",
                        xaxis_title="Número da Observação",
                        yaxis_title=f"Valor de {analysis_col}",
                        height=500,
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Alertas de pontos fora de controle
                    if len(out_of_control) > 0:
                        st.warning(f"⚠️ **{len(out_of_control)} pontos fora dos limites de controle!**")
                        st.write("Pontos fora de controle:", out_indices)
                    else:
                        st.success("✅ Todos os pontos estão dentro dos limites de controle")
                    
                    st.divider()
                    
                    # ============= ANÁLISE DE CAPACIDADE DO SISTEMA =============
                    st.subheader("📊 Análise de Capacidade do Sistema de Medição")
                    
                    col_tol1, col_tol2 = st.columns([2, 1])
                    
                    with col_tol1:
                        tolerance = st.number_input(
                            "Digite a tolerância do processo (range de especificação):",
                            min_value=0.0001,
                            value=0.1,
                            format="%.4f",
                            help="Diferença entre LSL e USL do processo",
                            key="msa_tolerance"
                        )
                    
                    with col_tol2:
                        st.info("""
                        **Tolerância =**
                        USL - LSL
                        """)
                    
                    if tolerance > 0:
                        # Cálculos
                        measurement_variation = std
                        percent_tolerance = (measurement_variation / tolerance) * 100
                        
                        # GRR (Gage R&R)
                        grr_percent = (std * 5.15 / tolerance) * 100
                        
                        col_result1, col_result2, col_result3 = st.columns(3)
                        
                        with col_result1:
                            st.metric(
                                "Variação da Medição (σ)", 
                                f"{measurement_variation:.4f}",
                                help="Desvio padrão das medições"
                            )
                        
                        with col_result2:
                            st.metric(
                                "% da Tolerância", 
                                f"{percent_tolerance:.1f}%",
                                help="Variação como % da tolerância"
                            )
                        
                        with col_result3:
                            st.metric(
                                "GRR (%)", 
                                f"{grr_percent:.1f}%",
                                help="Gage R&R como % da tolerância"
                            )
                        
                        st.divider()
                        
                        # Interpretação
                        st.subheader("💡 Interpretação dos Resultados")
                        
                        if percent_tolerance < 10:
                            st.success("""
                            ✅ **Sistema de Medição EXCELENTE**
                            
                            - Variação < 10% da tolerância
                            - Sistema adequado para uso
                            - Baixo impacto nas decisões
                            """)
                        elif percent_tolerance < 30:
                            st.warning("""
                            ⚠️ **Sistema de Medição ACEITÁVEL**
                            
                            - Variação entre 10-30% da tolerância
                            - Pode ser usado com cautela
                            - Considere melhorias se possível
                            """)
                        else:
                            st.error("""
                            ❌ **Sistema de Medição PRECISA MELHORAR**
                            
                            - Variação > 30% da tolerância
                            - Sistema inadequado para uso crítico
                            - **Ações necessárias:**
                              - Calibrar equipamento
                              - Treinar operadores
                              - Melhorar procedimento
                              - Considerar novo equipamento
                            """)
                        
                        # Tabela de classificação
                        st.divider()
                        st.subheader("📋 Tabela de Classificação GRR")
                        
                        classification_df = pd.DataFrame({
                            'GRR (%)': ['< 10%', '10% - 30%', '> 30%'],
                            'Classificação': ['Excelente', 'Aceitável', 'Inaceitável'],
                            'Ação': ['Sistema adequado', 'Usar com cautela', 'Melhorar sistema']
                        })
                        
                        st.dataframe(classification_df, use_container_width=True, hide_index=True)
                        
                        # Distribuição das medições
                        st.divider()
                        st.subheader("📊 Distribuição das Medições")
                        
                        fig_hist = go.Figure()
                        
                        fig_hist.add_trace(go.Histogram(
                            x=data_col,
                            nbinsx=30,
                            name='Medições',
                            marker_color='#3498DB',
                            opacity=0.7
                        ))
                        
                        fig_hist.add_vline(
                            x=mean,
                            line_dash="dash",
                            line_color="red",
                            annotation_text=f"Média: {mean:.3f}"
                        )
                        
                        fig_hist.update_layout(
                            title="Histograma das Medições",
                            xaxis_title="Valor",
                            yaxis_title="Frequência",
                            height=400
                        )
                        
                        st.plotly_chart(fig_hist, use_container_width=True)
                    
                    # Exportar resultados
                    st.divider()
                    
                    if st.button("📥 Exportar Relatório MSA", use_container_width=True):
                        report = f"""
RELATÓRIO MSA - MEASUREMENT SYSTEM ANALYSIS
============================================

Projeto: {st.session_state.project_name}
Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}
Variável Analisada: {analysis_col}

ESTATÍSTICAS DESCRITIVAS:
- Número de Medições: {len(data_col)}
- Média: {mean:.4f}
- Desvio Padrão: {std:.4f}
- Mínimo: {data_col.min():.4f}
- Máximo: {data_col.max():.4f}
- Amplitude: {amplitude:.4f}

LIMITES DE CONTROLE:
- UCL: {ucl:.4f}
- Média: {mean:.4f}
- LCL: {lcl:.4f}
- Pontos Fora de Controle: {len(out_of_control)}

ANÁLISE DE CAPACIDADE:
- Tolerância do Processo: {tolerance:.4f}
- Variação da Medição: {measurement_variation:.4f}
- % da Tolerância: {percent_tolerance:.2f}%
- GRR: {grr_percent:.2f}%

CONCLUSÃO:
"""
                        if percent_tolerance < 10:
                            report += "Sistema de Medição EXCELENTE - Adequado para uso"
                        elif percent_tolerance < 30:
                            report += "Sistema de Medição ACEITÁVEL - Usar com cautela"
                        else:
                            report += "Sistema de Medição INADEQUADO - Requer melhorias"
                        
                        st.download_button(
                            label="📄 Download Relatório (TXT)",
                            data=report.encode('utf-8'),
                            file_name=f"relatorio_msa_{analysis_col}_{datetime.now().strftime('%Y%m%d')}.txt",
                            mime="text/plain"
                        )
                
                except Exception as e:
                    st.error(f"❌ Erro ao processar coluna: {str(e)}")
                    st.write("**Detalhes:**", type(e).__name__)
        
        except Exception as e:
            st.error(f"❌ Erro ao processar arquivo: {str(e)}")
            
            with st.expander("🐛 Detalhes do Erro"):
                st.write("**Tipo:**", type(e).__name__)
                st.write("**Mensagem:**", str(e))
    
    else:
        # Tentar carregar dados salvos
        st.info("📤 Nenhum arquivo carregado. Faça upload dos dados de MSA.")
        
        if supabase:
            saved_data = load_process_data(st.session_state.project_name)
            if saved_data is not None:
                st.divider()
                st.success("📂 Dados anteriores encontrados no projeto")
                
                col_load1, col_load2 = st.columns([1, 2])
                
                with col_load1:
                    if st.button("📥 Carregar dados salvos", use_container_width=True):
                        st.session_state.msa_data = saved_data
                        st.rerun()
                
                with col_load2:
                    st.caption(f"Dados salvos: {len(saved_data)} linhas, {len(saved_data.columns)} colunas")


############################################################################################################################################################################################################################################

# ========================= TAB 3: PROCESS CAPABILITY =========================

with tab3:
    st.header("📊 Process Capability Analysis")
    st.markdown("**Objetivo:** Avaliar se o processo é capaz de atender às especificações")
    
    st.divider()
    
    # Informações sobre Capacidade
    with st.expander("ℹ️ O que é Análise de Capacidade?"):
        st.markdown("""
        **Análise de Capacidade** avalia se o processo consegue produzir dentro das especificações.
        
        **Índices Principais:**
        - **Cp:** Capacidade potencial (ignora centralização)
        - **Cpk:** Capacidade real (considera centralização)
        - **Pp/Ppk:** Performance do processo
        
        **Critérios de Aceitação:**
        - **Cpk ≥ 1.33:** Processo **CAPAZ**
        - **1.0 ≤ Cpk < 1.33:** **MARGINALMENTE CAPAZ**
        - **Cpk < 1.0:** Processo **NÃO CAPAZ**
        
        **PPM (Parts Per Million):** Quantidade esperada de defeitos por milhão
        
        **Nível Sigma:** Medida de qualidade (6σ = 3.4 PPM)
        """)
    
    st.divider()
    
    # Upload de arquivo
    col_upload1, col_upload2 = st.columns([2, 1])
    
    with col_upload1:
        uploaded_file = st.file_uploader(
            "📤 Faça upload dos dados do processo (CSV, Excel)",
            type=['csv', 'xlsx', 'xls'],
            help="Arquivo com dados de medições do processo",
            key="process_upload"
        )
    
    with col_upload2:
        st.info("""
        **Dados necessários:**
        - Medições do processo
        - Valores numéricos
        - Mínimo 30 amostras
        """)
    
    if uploaded_file is not None:
        try:
            # Detectar extensão
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            st.info(f"📄 Arquivo: **{uploaded_file.name}**")
            
            # Ler arquivo
            with st.spinner("Lendo arquivo..."):
                if file_extension == 'csv':
                    try:
                        process_data = pd.read_csv(uploaded_file, encoding='utf-8')
                    except UnicodeDecodeError:
                        uploaded_file.seek(0)
                        process_data = pd.read_csv(uploaded_file, encoding='latin-1')
                        st.warning("⚠️ Arquivo lido com encoding latin-1")
                
                elif file_extension in ['xlsx', 'xls']:
                    process_data = pd.read_excel(uploaded_file)
                
                else:
                    st.error("❌ Formato não suportado")
                    st.stop()
            
            st.success(f"✅ Arquivo carregado: {len(process_data)} linhas, {len(process_data.columns)} colunas")
            
            # Preview dos dados
            st.subheader("📊 Preview dos Dados")
            
            col_prev1, col_prev2 = st.columns([3, 1])
            
            with col_prev1:
                num_rows = st.slider("Linhas para visualizar:", 5, 50, 10, key="process_preview")
            
            with col_prev2:
                st.metric("Total de Linhas", len(process_data))
            
            st.dataframe(process_data.head(num_rows), use_container_width=True)
            
            # Opção de conversão
            if st.checkbox("🧹 Converter colunas automaticamente para numérico", value=True, key="auto_clean_process"):
                with st.spinner("Convertendo..."):
                    process_data = auto_clean_numeric_columns(process_data)
                st.success("✅ Conversão automática aplicada")
            
            # Salvar dados
            if supabase:
                if st.button("💾 Salvar dados do processo", key="save_process"):
                    with st.spinner("Salvando..."):
                        process_data_clean = clean_dataframe_for_json(process_data)
                        if save_process_data(st.session_state.project_name, process_data_clean):
                            st.success("✅ Dados salvos no projeto!")
                            st.balloons()
                        else:
                            st.error("❌ Erro ao salvar")
            
            st.divider()
            
            # Detectar colunas numéricas
            all_cols = process_data.columns.tolist()
            numeric_cols = []
            
            for col in all_cols:
                try:
                    test_numeric = pd.to_numeric(process_data[col], errors='coerce')
                    if test_numeric.notna().sum() > 0:
                        numeric_cols.append(col)
                except:
                    pass
            
            if len(numeric_cols) == 0:
                st.warning("⚠️ Nenhuma coluna numérica detectada. Mostrando todas.")
                numeric_cols = all_cols
            
            st.info(f"📊 Colunas numéricas detectadas: **{len(numeric_cols)}**")
            
            # ============= ANÁLISE DE CAPACIDADE =============
            if len(numeric_cols) > 0:
                st.subheader("📊 Configuração da Análise")
                
                col_config1, col_config2 = st.columns([3, 2])
                
                with col_config1:
                    selected_col = st.selectbox(
                        "📌 Selecione a variável do processo:",
                        numeric_cols,
                        key="cap_col"
                    )
                
                with col_config2:
                    # Info da coluna
                    non_null = process_data[selected_col].notna().sum()
                    st.metric("Valores Válidos", non_null)
                    
                    if non_null < 30:
                        st.warning("⚠️ Recomendado: mínimo 30 amostras")
                
                # Especificações
                st.markdown("**Limites de Especificação:**")
                
                col_spec1, col_spec2, col_spec3 = st.columns(3)
                
                with col_spec1:
                    lsl = st.number_input(
                        "LSL (Lower Spec Limit)",
                        value=0.0,
                        format="%.4f",
                        help="Limite Inferior de Especificação",
                        key="lsl"
                    )
                
                with col_spec2:
                    target = st.number_input(
                        "Target (Valor Alvo)",
                        value=50.0,
                        format="%.4f",
                        help="Valor ideal do processo",
                        key="target"
                    )
                
                with col_spec3:
                    usl = st.number_input(
                        "USL (Upper Spec Limit)",
                        value=100.0,
                        format="%.4f",
                        help="Limite Superior de Especificação",
                        key="usl"
                    )
                
                # Validação
                if lsl >= usl:
                    st.error("❌ O LSL deve ser menor que o USL!")
                    st.stop()
                
                if not (lsl <= target <= usl):
                    st.warning("⚠️ O Target deve estar entre LSL e USL!")
                
                st.divider()
                
                # Botão para calcular
                if st.button("🔄 Calcular Capacidade do Processo", type="primary", use_container_width=True):
                    
                    with st.spinner("Calculando índices de capacidade..."):
                        try:
                            # Converter e limpar dados
                            data = pd.to_numeric(process_data[selected_col], errors='coerce').dropna()
                            
                            if len(data) == 0:
                                st.error("❌ A coluna selecionada não contém valores numéricos válidos")
                                st.info("💡 **Dica:** Verifique se a coluna contém apenas números.")
                                
                                with st.expander("🔍 Ver dados originais"):
                                    st.dataframe(process_data[selected_col].head(20))
                                
                                st.stop()
                            
                            # Avisar sobre dados removidos
                            original_count = len(process_data[selected_col])
                            valid_count = len(data)
                            
                            if original_count > valid_count:
                                st.warning(f"⚠️ {original_count - valid_count} valores não numéricos foram removidos")
                            
                            st.success(f"✅ Analisando {valid_count} medições válidas")
                            
                            # ============= CÁLCULOS =============
                            mean = data.mean()
                            std = data.std()
                            median = data.median()
                            
                            # Índices de Capacidade
                            cp = (usl - lsl) / (6 * std)
                            cpu = (usl - mean) / (3 * std)
                            cpl = (mean - lsl) / (3 * std)
                            cpk = min(cpu, cpl)
                            
                            # Índices de Performance
                            pp = (usl - lsl) / (6 * data.std(ddof=1))
                            ppu = (usl - mean) / (3 * data.std(ddof=1))
                            ppl = (mean - lsl) / (3 * data.std(ddof=1))
                            ppk = min(ppu, ppl)
                            
                            # Cpm (considera target)
                            tau = np.sqrt(std**2 + (mean - target)**2)
                            cpm = (usl - lsl) / (6 * tau)
                            
                            # PPM e Sigma
                            prob_below_lsl = norm.cdf(lsl, mean, std)
                            prob_above_usl = 1 - norm.cdf(usl, mean, std)
                            prob_defect = prob_below_lsl + prob_above_usl
                            ppm = prob_defect * 1_000_000
                            sigma_level = 3 * cpk
                            
                            # Yield
                            yield_pct = (1 - prob_defect) * 100
                            
                            # Contagem real
                            below_lsl = len(data[data < lsl])
                            above_usl = len(data[data > usl])
                            total_out = below_lsl + above_usl
                            
                            st.divider()
                            
                            # ============= RESULTADOS =============
                            st.subheader("📊 Índices de Capacidade")
                            
                            col1, col2, col3, col4, col5 = st.columns(5)
                            
                            with col1:
                                st.metric("Cp", f"{cp:.3f}")
                                if cp >= 1.33:
                                    st.success("✅ Capaz")
                                elif cp >= 1.0:
                                    st.warning("⚠️ Marginal")
                                else:
                                    st.error("❌ Não capaz")
                            
                            with col2:
                                st.metric("Cpk", f"{cpk:.3f}")
                                if cpk >= 1.33:
                                    st.success("✅ Capaz")
                                elif cpk >= 1.0:
                                    st.warning("⚠️ Marginal")
                                else:
                                    st.error("❌ Não capaz")
                            
                            with col3:
                                st.metric("Pp", f"{pp:.3f}")
                            
                            with col4:
                                st.metric("Ppk", f"{ppk:.3f}")
                            
                            with col5:
                                st.metric("Cpm", f"{cpm:.3f}")
                            
                            st.divider()
                            
                            # ============= PERFORMANCE =============
                            st.subheader("📈 Performance do Processo")
                            
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("Nível Sigma", f"{sigma_level:.2f}σ")
                            
                            with col2:
                                st.metric("Yield", f"{yield_pct:.2f}%")
                            
                            with col3:
                                st.metric("PPM Esperado", f"{ppm:.0f}")
                            
                            with col4:
                                st.metric("Fora de Spec", f"{total_out}")
                            
                            # Detalhes de não-conformidades
                            if total_out > 0:
                                st.divider()
                                st.subheader("🔍 Análise de Não-Conformidades")
                                
                                col_nc1, col_nc2 = st.columns(2)
                                
                                with col_nc1:
                                    st.metric("Abaixo do LSL", below_lsl)
                                    st.caption(f"PPM: {prob_below_lsl * 1_000_000:.0f}")
                                
                                with col_nc2:
                                    st.metric("Acima do USL", above_usl)
                                    st.caption(f"PPM: {prob_above_usl * 1_000_000:.0f}")
                            
                            st.divider()
                            
                            # ============= ESTATÍSTICAS =============
                            st.subheader("📊 Estatísticas Descritivas")
                            
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("Média", f"{mean:.4f}")
                            
                            with col2:
                                st.metric("Mediana", f"{median:.4f}")
                            
                            with col3:
                                st.metric("Desvio Padrão", f"{std:.4f}")
                            
                            with col4:
                                st.metric("Amostras", valid_count)
                            
                            st.divider()
                            
                            # ============= GRÁFICO DE DISTRIBUIÇÃO =============
                            st.subheader("📊 Distribuição do Processo vs Especificações")
                            
                            fig = go.Figure()
                            
                            # Histograma
                            fig.add_trace(go.Histogram(
                                x=data,
                                name='Dados',
                                nbinsx=30,
                                histnorm='probability density',
                                marker_color='lightblue',
                                opacity=0.7
                            ))
                            
                            # Curva normal
                            x_range = np.linspace(data.min() - std, data.max() + std, 200)
                            y_normal = norm.pdf(x_range, mean, std)
                            
                            fig.add_trace(go.Scatter(
                                x=x_range,
                                y=y_normal,
                                mode='lines',
                                name='Distribuição Normal',
                                line=dict(color='red', width=3)
                            ))
                            
                            # Limites de especificação
                            max_y = max(y_normal) * 1.1
                            
                            # Área de especificação
                            fig.add_shape(
                                type="rect",
                                x0=lsl, x1=usl,
                                y0=0, y1=max_y,
                                fillcolor="green",
                                opacity=0.1,
                                line_width=0
                            )
                            
                            # Linhas LSL, USL, Target, Média
                            fig.add_vline(
                                x=lsl,
                                line_dash="dash",
                                line_color="red",
                                line_width=2,
                                annotation_text=f"LSL: {lsl:.2f}"
                            )
                            
                            fig.add_vline(
                                x=usl,
                                line_dash="dash",
                                line_color="red",
                                line_width=2,
                                annotation_text=f"USL: {usl:.2f}"
                            )
                            
                            fig.add_vline(
                                x=target,
                                line_dash="dot",
                                line_color="blue",
                                line_width=2,
                                annotation_text=f"Target: {target:.2f}"
                            )
                            
                            fig.add_vline(
                                x=mean,
                                line_dash="solid",
                                line_color="green",
                                line_width=2,
                                annotation_text=f"Média: {mean:.2f}"
                            )
                            
                            fig.update_layout(
                                title="Histograma com Limites de Especificação",
                                xaxis_title="Valor",
                                yaxis_title="Densidade de Probabilidade",
                                height=500,
                                showlegend=True
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            st.divider()
                            
                            # ============= INTERPRETAÇÃO =============
                            st.subheader("💡 Interpretação dos Resultados")
                            
                            if cpk >= 1.33:
                                st.success("""
                                ✅ **PROCESSO CAPAZ**
                                
                                - Cpk ≥ 1.33: Processo atende aos requisitos
                                - Baixa probabilidade de defeitos
                                - Continue monitorando o processo
                                """)
                            elif cpk >= 1.0:
                                st.warning("""
                                ⚠️ **PROCESSO MARGINALMENTE CAPAZ**
                                
                                - 1.0 ≤ Cpk < 1.33: Processo no limite
                                - Monitore de perto
                                - Considere melhorias
                                """)
                            else:
                                st.error("""
                                ❌ **PROCESSO NÃO CAPAZ**
                                
                                - Cpk < 1.0: Processo inadequado
                                - Alta probabilidade de defeitos
                                - **Ações necessárias:**
                                  - Reduzir variação
                                  - Centralizar processo
                                  - Revisar especificações
                                """)
                            
                            # Centralização
                            process_center = (lsl + usl) / 2
                            offset = mean - process_center
                            offset_pct = (offset / ((usl - lsl) / 2)) * 100
                            
                            if abs(offset_pct) > 10:
                                st.warning(f"⚠️ **Processo descentrado em {abs(offset_pct):.1f}%**")
                            
                            # Exportar relatório
                            st.divider()
                            
                            if st.button("📥 Exportar Relatório Completo", use_container_width=True):
                                report = f"""
RELATÓRIO DE CAPACIDADE DO PROCESSO
====================================

Projeto: {st.session_state.project_name}
Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}
Variável: {selected_col}

ESPECIFICAÇÕES:
- LSL: {lsl:.4f}
- Target: {target:.4f}
- USL: {usl:.4f}
- Tolerância: {usl - lsl:.4f}

ESTATÍSTICAS:
- N: {valid_count}
- Média: {mean:.4f}
- Mediana: {median:.4f}
- Desvio Padrão: {std:.4f}

ÍNDICES DE CAPACIDADE:
- Cp: {cp:.3f}
- Cpk: {cpk:.3f}
- Pp: {pp:.3f}
- Ppk: {ppk:.3f}
- Cpm: {cpm:.3f}

PERFORMANCE:
- Nível Sigma: {sigma_level:.2f}σ
- Yield: {yield_pct:.2f}%
- PPM Total: {ppm:.0f}
- Abaixo LSL: {below_lsl}
- Acima USL: {above_usl}

CONCLUSÃO:
"""
                                if cpk >= 1.33:
                                    report += "Processo CAPAZ - Atende aos requisitos"
                                elif cpk >= 1.0:
                                    report += "Processo MARGINALMENTE CAPAZ - Monitorar"
                                else:
                                    report += "Processo NÃO CAPAZ - Requer melhorias"
                                
                                st.download_button(
                                    label="📄 Download Relatório (TXT)",
                                    data=report.encode('utf-8'),
                                    file_name=f"capacidade_{selected_col}_{datetime.now().strftime('%Y%m%d')}.txt",
                                    mime="text/plain"
                                )
                        
                        except Exception as e:
                            st.error(f"❌ Erro ao calcular capacidade: {str(e)}")
                            
                            with st.expander("🐛 Detalhes do Erro"):
                                st.write("**Tipo:**", type(e).__name__)
                                st.write("**Mensagem:**", str(e))
        
        except Exception as e:
            st.error(f"❌ Erro ao processar arquivo: {str(e)}")
            
            with st.expander("🐛 Detalhes do Erro"):
                st.write("**Tipo:**", type(e).__name__)
                st.write("**Mensagem:**", str(e))
    
    else:
        # Tentar carregar dados salvos
        st.info("📤 Nenhum arquivo carregado. Faça upload dos dados do processo.")
        
        if supabase:
            saved_data = load_process_data(st.session_state.project_name)
            if saved_data is not None:
                st.divider()
                st.success("📂 Dados anteriores encontrados no projeto")
                
                col_load1, col_load2 = st.columns([1, 2])
                
                with col_load1:
                    if st.button("📥 Carregar dados salvos", use_container_width=True, key="load_process"):
                        st.session_state.process_data = saved_data
                        st.rerun()
                
                with col_load2:
                    st.caption(f"Dados salvos: {len(saved_data)} linhas, {len(saved_data.columns)} colunas")



############################################################################################################################################################################################################################################

# ========================= TAB 4: DATA VISUALIZATION =========================

with tab4:
    st.header("📈 Data Visualization")
    st.markdown("**Objetivo:** Criar visualizações interativas para explorar os dados")
    
    st.divider()
    
    # Upload de arquivo
    col_upload1, col_upload2 = st.columns([2, 1])
    
    with col_upload1:
        uploaded_file = st.file_uploader(
            "📤 Faça upload dos dados para visualização (CSV, Excel)",
            type=['csv', 'xlsx', 'xls'],
            help="Arquivo com dados para criar gráficos",
            key="viz_upload"
        )
    
    with col_upload2:
        st.info("""
        **Tipos de gráficos:**
        - Linha
        - Barra
        - Scatter
        - Box Plot
        - Histograma
        - Pareto
        """)
    
    if uploaded_file is not None:
        try:
            # Detectar extensão
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            st.info(f"📄 Arquivo: **{uploaded_file.name}**")
            
            # Ler arquivo
            with st.spinner("Lendo arquivo..."):
                if file_extension == 'csv':
                    try:
                        viz_data = pd.read_csv(uploaded_file, encoding='utf-8')
                    except UnicodeDecodeError:
                        uploaded_file.seek(0)
                        viz_data = pd.read_csv(uploaded_file, encoding='latin-1')
                        st.warning("⚠️ Arquivo lido com encoding latin-1")
                
                elif file_extension in ['xlsx', 'xls']:
                    viz_data = pd.read_excel(uploaded_file)
                
                else:
                    st.error("❌ Formato não suportado")
                    st.stop()
            
            st.success(f"✅ Arquivo carregado: {len(viz_data)} linhas, {len(viz_data.columns)} colunas")
            
            # Preview dos dados
            with st.expander("👀 Preview dos Dados"):
                st.dataframe(viz_data.head(10), use_container_width=True)
            
            st.divider()
            
            # ============= SELEÇÃO DE TIPO DE GRÁFICO =============
            st.subheader("📊 Criar Visualização")
            
            col_chart1, col_chart2 = st.columns([2, 1])
            
            with col_chart1:
                chart_type = st.selectbox(
                    "📌 Selecione o tipo de gráfico:",
                    ["Linha", "Barra", "Scatter", "Box Plot", "Histograma", "Pareto"],
                    key="chart_type_select"
                )
            
            with col_chart2:
                # Info sobre o tipo selecionado
                chart_info = {
                    "Linha": "Tendências ao longo do tempo",
                    "Barra": "Comparação entre categorias",
                    "Scatter": "Relação entre variáveis",
                    "Box Plot": "Distribuição e outliers",
                    "Histograma": "Distribuição de frequência",
                    "Pareto": "Análise 80/20"
                }
                st.info(f"**Uso:** {chart_info[chart_type]}")
            
            st.divider()
            
            # ============= GRÁFICOS DE LINHA, BARRA, SCATTER =============
            if chart_type in ["Linha", "Barra", "Scatter"]:
                
                col_axis1, col_axis2 = st.columns(2)
                
                with col_axis1:
                    x_col = st.selectbox("📊 Eixo X:", viz_data.columns, key="x_axis")
                
                with col_axis2:
                    y_col = st.selectbox("📊 Eixo Y:", viz_data.columns, key="y_axis")
                
                # Opções adicionais
                with st.expander("⚙️ Opções Avançadas"):
                    col_opt1, col_opt2 = st.columns(2)
                    
                    with col_opt1:
                        color_col = st.selectbox(
                            "Colorir por (opcional):",
                            ["Nenhum"] + list(viz_data.columns),
                            key="color_by"
                        )
                    
                    with col_opt2:
                        if chart_type == "Scatter":
                            show_trendline = st.checkbox("Mostrar linha de tendência", value=True)
                
                # Botão gerar
                if st.button("🎨 Gerar Gráfico", type="primary", use_container_width=True, key="gen_chart_1"):
                    try:
                        color_param = None if color_col == "Nenhum" else color_col
                        
                        if chart_type == "Linha":
                            fig = px.line(
                                viz_data, 
                                x=x_col, 
                                y=y_col, 
                                color=color_param,
                                title=f"Gráfico de Linha: {y_col} vs {x_col}"
                            )
                        
                        elif chart_type == "Barra":
                            fig = px.bar(
                                viz_data, 
                                x=x_col, 
                                y=y_col, 
                                color=color_param,
                                title=f"Gráfico de Barras: {y_col} por {x_col}"
                            )
                        
                        elif chart_type == "Scatter":
                            trendline_param = "ols" if show_trendline else None
                            fig = px.scatter(
                                viz_data, 
                                x=x_col, 
                                y=y_col, 
                                color=color_param,
                                trendline=trendline_param,
                                title=f"Gráfico de Dispersão: {y_col} vs {x_col}"
                            )
                        
                        fig.update_layout(height=500)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        st.success("✅ Gráfico gerado com sucesso!")
                    
                    except Exception as e:
                        st.error(f"❌ Erro ao gerar gráfico: {str(e)}")
            
            # ============= BOX PLOT =============
            elif chart_type == "Box Plot":
                
                # Detectar colunas numéricas
                numeric_cols_viz = [
                    col for col in viz_data.columns 
                    if pd.to_numeric(viz_data[col], errors='coerce').notna().any()
                ]
                
                if not numeric_cols_viz:
                    st.warning("⚠️ Nenhuma coluna numérica encontrada")
                    st.stop()
                
                col_box1, col_box2 = st.columns(2)
                
                with col_box1:
                    selected_col = st.selectbox(
                        "📊 Selecione a variável:",
                        numeric_cols_viz,
                        key="box_col"
                    )
                
                with col_box2:
                    group_by = st.selectbox(
                        "Agrupar por (opcional):",
                        ["Nenhum"] + list(viz_data.columns),
                        key="box_group"
                    )
                
                if st.button("🎨 Gerar Box Plot", type="primary", use_container_width=True, key="gen_box"):
                    try:
                        if group_by == "Nenhum":
                            fig = px.box(
                                viz_data, 
                                y=selected_col, 
                                title=f"Box Plot - {selected_col}"
                            )
                        else:
                            fig = px.box(
                                viz_data, 
                                x=group_by,
                                y=selected_col, 
                                title=f"Box Plot - {selected_col} por {group_by}"
                            )
                        
                        fig.update_layout(height=500)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Estatísticas
                        st.subheader("📊 Estatísticas")
                        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                        
                        data_col = pd.to_numeric(viz_data[selected_col], errors='coerce').dropna()
                        
                        with col_stat1:
                            st.metric("Mediana", f"{data_col.median():.2f}")
                        with col_stat2:
                            st.metric("Q1 (25%)", f"{data_col.quantile(0.25):.2f}")
                        with col_stat3:
                            st.metric("Q3 (75%)", f"{data_col.quantile(0.75):.2f}")
                        with col_stat4:
                            iqr = data_col.quantile(0.75) - data_col.quantile(0.25)
                            st.metric("IQR", f"{iqr:.2f}")
                        
                        st.success("✅ Box Plot gerado com sucesso!")
                    
                    except Exception as e:
                        st.error(f"❌ Erro ao gerar Box Plot: {str(e)}")
            
            # ============= HISTOGRAMA =============
            elif chart_type == "Histograma":
                
                # Detectar colunas numéricas
                numeric_cols_viz = [
                    col for col in viz_data.columns 
                    if pd.to_numeric(viz_data[col], errors='coerce').notna().any()
                ]
                
                if not numeric_cols_viz:
                    st.warning("⚠️ Nenhuma coluna numérica encontrada")
                    st.stop()
                
                col_hist1, col_hist2 = st.columns(2)
                
                with col_hist1:
                    selected_col = st.selectbox(
                        "📊 Selecione a variável:",
                        numeric_cols_viz,
                        key="hist_col"
                    )
                
                with col_hist2:
                    bins = st.slider(
                        "Número de bins:",
                        min_value=5,
                        max_value=100,
                        value=20,
                        key="hist_bins"
                    )
                
                if st.button("🎨 Gerar Histograma", type="primary", use_container_width=True, key="gen_hist"):
                    try:
                        fig = px.histogram(
                            viz_data, 
                            x=selected_col, 
                            nbins=bins,
                            title=f"Histograma - {selected_col}"
                        )
                        
                        fig.update_layout(height=500)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Estatísticas
                        st.subheader("📊 Estatísticas")
                        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                        
                        data_col = pd.to_numeric(viz_data[selected_col], errors='coerce').dropna()
                        
                        with col_stat1:
                            st.metric("Média", f"{data_col.mean():.2f}")
                        with col_stat2:
                            st.metric("Mediana", f"{data_col.median():.2f}")
                        with col_stat3:
                            st.metric("Desvio Padrão", f"{data_col.std():.2f}")
                        with col_stat4:
                            st.metric("Assimetria", f"{data_col.skew():.2f}")
                        
                        st.success("✅ Histograma gerado com sucesso!")
                    
                    except Exception as e:
                        st.error(f"❌ Erro ao gerar Histograma: {str(e)}")
            
            # ============= PARETO =============
            elif chart_type == "Pareto":
                
                col_pareto1, col_pareto2 = st.columns(2)
                
                with col_pareto1:
                    cat_col = st.selectbox(
                        "📊 Coluna de Categoria:",
                        viz_data.columns,
                        key="pareto_cat"
                    )
                
                with col_pareto2:
                    val_col = st.selectbox(
                        "📊 Coluna de Valor:",
                        ["Contagem"] + list(viz_data.columns),
                        key="pareto_val"
                    )
                
                if st.button("🎨 Gerar Pareto", type="primary", use_container_width=True, key="gen_pareto_viz"):
                    try:
                        # Processar dados
                        if val_col == "Contagem":
                            pareto_data = viz_data[cat_col].value_counts().reset_index()
                            pareto_data.columns = ['Categoria', 'Frequência']
                            value_column = 'Frequência'
                        else:
                            pareto_data = viz_data.groupby(cat_col)[val_col].sum().reset_index()
                            pareto_data.columns = ['Categoria', 'Valor']
                            value_column = 'Valor'
                        
                        pareto_data = pareto_data.sort_values(by=value_column, ascending=False)
                        total = pareto_data[value_column].sum()
                        pareto_data['Percentual'] = (pareto_data[value_column] / total) * 100
                        pareto_data['Acumulado'] = pareto_data['Percentual'].cumsum()
                        
                        # Criar gráfico
                        fig = go.Figure()
                        
                        fig.add_trace(go.Bar(
                            x=pareto_data['Categoria'],
                            y=pareto_data[value_column],
                            name=value_column,
                            marker_color='lightblue',
                            yaxis='y'
                        ))
                        
                        fig.add_trace(go.Scatter(
                            x=pareto_data['Categoria'],
                            y=pareto_data['Acumulado'],
                            name='% Acumulado',
                            yaxis='y2',
                            line=dict(color='red', width=2),
                            mode='lines+markers'
                        ))
                        
                        fig.add_hline(
                            y=80,
                            line_dash="dash",
                            line_color="orange",
                            yref='y2',
                            annotation_text="80%"
                        )
                        
                        fig.update_layout(
                            title="Gráfico de Pareto",
                            xaxis=dict(title="Categorias"),
                            yaxis=dict(title=value_column),
                            yaxis2=dict(
                                title="% Acumulado",
                                overlaying='y',
                                side='right',
                                range=[0, 105]
                            ),
                            height=500
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        st.success("✅ Gráfico de Pareto gerado com sucesso!")
                    
                    except Exception as e:
                        st.error(f"❌ Erro ao gerar Pareto: {str(e)}")
        
        except Exception as e:
            st.error(f"❌ Erro ao processar arquivo: {str(e)}")
            
            with st.expander("🐛 Detalhes do Erro"):
                st.write("**Tipo:**", type(e).__name__)
                st.write("**Mensagem:**", str(e))
    
    else:
        st.info("📤 Nenhum arquivo carregado. Faça upload para criar visualizações.")
        
        # Exemplo de uso
        with st.expander("💡 Como usar esta ferramenta"):
            st.markdown("""
            **Passo a passo:**
            
            1. **Upload:** Carregue um arquivo CSV ou Excel
            2. **Escolha:** Selecione o tipo de gráfico desejado
            3. **Configure:** Escolha as colunas e opções
            4. **Gere:** Clique no botão para criar o gráfico
            
            **Tipos de gráficos disponíveis:**
            - **Linha:** Para tendências temporais
            - **Barra:** Para comparações entre categorias
            - **Scatter:** Para correlações entre variáveis
            - **Box Plot:** Para análise de distribuição
            - **Histograma:** Para frequência de valores
            - **Pareto:** Para análise 80/20
            """)

# ========================= RESUMO E FOOTER =========================

st.divider()
st.header("📊 Resumo da Fase Measure")

if 'project_data' in st.session_state:
    project_data = st.session_state.project_data
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        plans_count = len(st.session_state.get('collection_plans', []))
        st.metric("Planos de Coleta", plans_count)
    
    with col2:
        if project_data.get('baseline_value'):
            baseline = project_data['baseline_value']
            st.metric("Baseline", f"{baseline:.2f}")
        else:
            st.metric("Baseline", "Não definido")
    
    with col3:
        if project_data.get('target_value'):
            target = project_data['target_value']
            st.metric("Meta", f"{target:.2f}")
        else:
            st.metric("Meta", "Não definida")
    
    with col4:
        status = "Em andamento"
        st.metric("Status", status)
    
    st.divider()
    
    # Checklist
    st.subheader("✅ Checklist da Fase Measure")
    
    col_check1, col_check2 = st.columns(2)
    
    with col_check1:
        st.markdown("**Atividades Principais:**")
        
        # Verificar se há dados salvos no banco
        msa_saved = False
        process_saved = False
        capability_saved = False
        
        if supabase and st.session_state.get('project_name'):
            try:
                # Verificar se há dados do processo salvos
                saved_data = load_process_data(st.session_state.project_name)
                if saved_data is not None and len(saved_data) > 0:
                    process_saved = True
                    msa_saved = True  # Se tem dados, assume que MSA foi feito
            except:
                pass
        
        checks = {
            "Plano de Coleta definido": plans_count > 0,
            "MSA realizado": msa_saved or 'msa_data' in st.session_state,
            "Dados do processo coletados": process_saved or 'process_data' in st.session_state or 'uploaded_data' in st.session_state,
            "Capacidade calculada": 'capability_results' in st.session_state
        }

        
        for item, done in checks.items():
            if done:
                st.success(f"✅ {item}")
            else:
                st.info(f"⬜ {item}")
    
    with col_check2:
        st.markdown("**Próximos Passos:**")
        
        completed = sum(checks.values())
        total = len(checks)
        progress = completed / total
        
        st.progress(progress, text=f"Progresso: {completed}/{total} ({progress*100:.0f}%)")
        
        if all(checks.values()):
            st.success("🎉 **Fase Measure completa!** Prossiga para Analyze.")
            
            if st.button("➡️ Ir para Analyze", type="primary", use_container_width=True):
                st.switch_page("pages/3_📊_Analyze.py")
        else:
            st.warning("⚠️ Complete todas as atividades antes de prosseguir.")
            
            # Mostrar o que falta
            pending = [item for item, done in checks.items() if not done]
            if pending:
                st.write("**Pendente:**")
                for item in pending:
                    st.write(f"- {item}")

else:
    st.info("Selecione um projeto para ver o resumo.")

# Footer
st.divider()
st.caption("💡 **Dica:** Garanta que o sistema de medição é confiável antes de coletar dados para análise")
st.caption("📏 Fase Measure | Green Belt Project Management System")


############################################################################################################################################################################################################################################
