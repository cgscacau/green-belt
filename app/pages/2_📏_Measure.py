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

# ========================= TAB 2: MSA =========================

with tab2:
    st.header("Measurement System Analysis (MSA)")
    
    st.info("Análise do Sistema de Medição - Repetibilidade e Reprodutibilidade (R&R)")
    
    uploaded_file = st.file_uploader(
        "Faça upload dos dados de MSA (CSV, Excel)",
        type=['csv', 'xlsx', 'xls'],
        key="msa_upload"
    )
    
    if uploaded_file is not None:
        try:
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            if file_extension == 'csv':
                msa_data = pd.read_csv(uploaded_file)
            elif file_extension in ['xlsx', 'xls']:
                msa_data = pd.read_excel(uploaded_file)
            else:
                st.error("❌ Formato não suportado")
                st.stop()
            
            if st.checkbox("🧹 Tentar converter colunas automaticamente para numérico", value=True, key="auto_clean_msa"):
                msa_data = auto_clean_numeric_columns(msa_data)
                st.success("✅ Conversão automática aplicada")
            
            if supabase and st.button("💾 Salvar dados MSA no projeto"):
                msa_data_clean = clean_dataframe_for_json(msa_data)
                if save_process_data(st.session_state.project_name, msa_data_clean):
                    st.success("✅ Dados salvos no projeto!")
            
            st.subheader("📊 Dados Carregados")
            st.dataframe(msa_data.head(), use_container_width=True)
            
            all_cols = msa_data.columns.tolist()
            numeric_cols = []
            
            for col in all_cols:
                try:
                    pd.to_numeric(msa_data[col], errors='coerce')
                    numeric_cols.append(col)
                except:
                    pass
            
            if len(numeric_cols) == 0:
                st.warning("⚠️ Nenhuma coluna numérica detectada automaticamente. Mostrando todas as colunas.")
                numeric_cols = all_cols
            
            if len(numeric_cols) > 0:
                analysis_col = st.selectbox("Selecione a coluna para análise:", numeric_cols)
                
                try:
                    msa_data[analysis_col] = pd.to_numeric(msa_data[analysis_col], errors='coerce')
                except:
                    st.error(f"❌ Não foi possível converter a coluna '{analysis_col}' para valores numéricos")
                    st.stop()
                
                if analysis_col:
                    data_col = pd.to_numeric(msa_data[analysis_col], errors='coerce').dropna()
                    
                    if len(data_col) == 0:
                        st.error("❌ A coluna selecionada não contém valores numéricos válidos")
                        st.stop()
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Média", f"{data_col.mean():.3f}")
                        st.metric("Desvio Padrão", f"{data_col.std():.3f}")
                    
                    with col2:
                        st.metric("Mínimo", f"{data_col.min():.3f}")
                        st.metric("Máximo", f"{data_col.max():.3f}")
                    
                    with col3:
                        st.metric("Amplitude", f"{data_col.max() - data_col.min():.3f}")
                        st.metric("CV%", f"{(data_col.std()/data_col.mean()*100):.1f}%")
                    
                    st.subheader("📈 Gráfico de Controle")
                    
                    mean = data_col.mean()
                    std = data_col.std()
                    ucl = mean + 3*std
                    lcl = mean - 3*std
                    
                    fig = go.Figure()
                    
                    fig.add_trace(go.Scatter(
                        x=list(range(len(data_col))),
                        y=data_col,
                        mode='lines+markers',
                        name='Medições',
                        line=dict(color='blue')
                    ))
                    
                    fig.add_hline(y=mean, line_dash="dash", line_color="green", 
                                 annotation_text=f"Média: {mean:.2f}")
                    fig.add_hline(y=ucl, line_dash="dash", line_color="red",
                                 annotation_text=f"UCL: {ucl:.2f}")
                    fig.add_hline(y=lcl, line_dash="dash", line_color="red",
                                 annotation_text=f"LCL: {lcl:.2f}")
                    
                    fig.update_layout(
                        title="Gráfico de Controle X-bar",
                        xaxis_title="Observação",
                        yaxis_title="Valor",
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.subheader("📊 Análise de Capacidade")
                    
                    tolerance = st.number_input("Digite a tolerância do processo:", value=0.1, format="%.4f")
                    
                    if tolerance > 0:
                        measurement_variation = std
                        percent_tolerance = (measurement_variation / tolerance) * 100
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Variação da Medição", f"{measurement_variation:.4f}")
                        with col2:
                            st.metric("% da Tolerância", f"{percent_tolerance:.1f}%")
                        
                        if percent_tolerance < 10:
                            st.success("✅ Sistema de medição EXCELENTE (< 10%)")
                        elif percent_tolerance < 30:
                            st.warning("⚠️ Sistema de medição ACEITÁVEL (10-30%)")
                        else:
                            st.error("❌ Sistema de medição PRECISA MELHORAR (> 30%)")
            
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {str(e)}")
    else:
        if supabase:
            saved_data = load_process_data(st.session_state.project_name)
            if saved_data is not None:
                st.info("📂 Dados anteriores encontrados no projeto")
                if st.button("Carregar dados salvos"):
                    st.session_state.msa_data = saved_data
                    st.rerun()

# ========================= TAB 3: PROCESS CAPABILITY =========================

with tab3:
    st.header("Process Capability Analysis")
    
    uploaded_file = st.file_uploader(
        "Faça upload dos dados do processo (CSV, Excel)",
        type=['csv', 'xlsx', 'xls'],
        key="process_upload"
    )
    
    if uploaded_file is not None:
        try:
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            if file_extension == 'csv':
                process_data = pd.read_csv(uploaded_file)
            elif file_extension in ['xlsx', 'xls']:
                process_data = pd.read_excel(uploaded_file)
            else:
                st.error("❌ Formato não suportado")
                st.stop()
            
            st.subheader("📊 Preview dos Dados Carregados")
            st.dataframe(process_data.head(10), use_container_width=True)
            
            if st.checkbox("🧹 Tentar converter colunas automaticamente para numérico", value=True, key="auto_clean_process"):
                process_data = auto_clean_numeric_columns(process_data)
                st.success("✅ Conversão automática aplicada")
            
            if supabase and st.button("💾 Salvar dados do processo", key="save_process"):
                process_data_clean = clean_dataframe_for_json(process_data)
                if save_process_data(st.session_state.project_name, process_data_clean):
                    st.success("✅ Dados salvos no projeto!")
            
            st.subheader("📊 Análise de Capacidade do Processo")
            
            all_cols = process_data.columns.tolist()
            numeric_cols = []
            
            for col in all_cols:
                try:
                    pd.to_numeric(process_data[col], errors='coerce')
                    numeric_cols.append(col)
                except:
                    pass
            
            if len(numeric_cols) == 0:
                st.warning("⚠️ Nenhuma coluna numérica detectada. Mostrando todas.")
                numeric_cols = all_cols
            
            if len(numeric_cols) > 0:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    selected_col = st.selectbox("Selecione a variável:", numeric_cols, key="cap_col")
                
                with col2:
                    col_lsl, col_usl = st.columns(2)
                    with col_lsl:
                        lsl = st.number_input("LSL", value=0.0, key="lsl")
                    with col_usl:
                        usl = st.number_input("USL", value=100.0, key="usl")
                
                if selected_col and usl > lsl:
                    try:
                        data = pd.to_numeric(process_data[selected_col], errors='coerce').dropna()
                        
                        if len(data) == 0:
                            st.error("❌ A coluna selecionada não contém valores numéricos válidos")
                            st.info("💡 Dica: Verifique se a coluna contém apenas números.")
                            st.write("**Amostra dos dados originais:**")
                            st.write(process_data[selected_col].head(10))
                            st.stop()
                        
                        original_count = len(process_data[selected_col])
                        valid_count = len(data)
                        if original_count > valid_count:
                            st.warning(f"⚠️ {original_count - valid_count} valores não numéricos foram removidos da análise")
                        
                        mean = data.mean()
                        std = data.std()
                        
                        cp = (usl - lsl) / (6 * std)
                        cpu = (usl - mean) / (3 * std)
                        cpl = (mean - lsl) / (3 * std)
                        cpk = min(cpu, cpl)
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Cp", f"{cp:.3f}")
                            if cp >= 1.33:
                                st.success("Capaz")
                            elif cp >= 1.0:
                                st.warning("Marginalmente capaz")
                            else:
                                st.error("Não capaz")
                        
                        with col2:
                            st.metric("Cpk", f"{cpk:.3f}")
                            if cpk >= 1.33:
                                st.success("Capaz")
                            elif cpk >= 1.0:
                                st.warning("Marginalmente capaz")
                            else:
                                st.error("Não capaz")
                        
                        with col3:
                            st.metric("Média", f"{mean:.3f}")
                        
                        with col4:
                            st.metric("Desvio Padrão", f"{std:.3f}")
                        
                        st.subheader("📊 Distribuição do Processo")
                        
                        fig = go.Figure()
                        
                        fig.add_trace(go.Histogram(
                            x=data,
                            name='Dados',
                            nbinsx=30,
                            histnorm='probability density',
                            marker_color='lightblue'
                        ))
                        
                        x_range = np.linspace(data.min(), data.max(), 100)
                        y_normal = norm.pdf(x_range, mean, std)
                        
                        fig.add_trace(go.Scatter(
                            x=x_range,
                            y=y_normal,
                            mode='lines',
                            name='Normal',
                            line=dict(color='red', width=2)
                        ))
                        
                        fig.add_vline(x=lsl, line_dash="dash", line_color="red",
                                     annotation_text=f"LSL: {lsl}")
                        fig.add_vline(x=usl, line_dash="dash", line_color="red",
                                     annotation_text=f"USL: {usl}")
                        fig.add_vline(x=mean, line_dash="dash", line_color="green",
                                     annotation_text=f"Média: {mean:.2f}")
                        
                        fig.update_layout(
                            title="Histograma com Limites de Especificação",
                            xaxis_title="Valor",
                            yaxis_title="Densidade",
                            height=400
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        st.subheader("📈 Previsão de Defeitos")
                        
                        prob_below_lsl = norm.cdf(lsl, mean, std)
                        prob_above_usl = 1 - norm.cdf(usl, mean, std)
                        prob_defect = prob_below_lsl + prob_above_usl
                        ppm = prob_defect * 1_000_000
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("PPM Total", f"{ppm:.0f}")
                        with col2:
                            st.metric("% Defeitos", f"{prob_defect*100:.3f}%")
                        with col3:
                            sigma_level = 3 * cpk
                            st.metric("Nível Sigma", f"{sigma_level:.1f}σ")
                    
                    except Exception as e:
                        st.error(f"❌ Erro ao processar coluna: {str(e)}")
                        st.stop()
                    
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {str(e)}")
    else:
        if supabase:
            saved_data = load_process_data(st.session_state.project_name)
            if saved_data is not None:
                st.info("📂 Dados anteriores encontrados")
                if st.button("Carregar dados salvos", key="load_process"):
                    st.session_state.process_data = saved_data
                    st.rerun()

# ========================= TAB 4: DATA VISUALIZATION =========================

with tab4:
    st.header("Data Visualization")
    
    uploaded_file = st.file_uploader(
        "Faça upload dos dados para visualização (CSV, Excel)",
        type=['csv', 'xlsx', 'xls'],
        key="viz_upload"
    )
    
    if uploaded_file is not None:
        try:
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            if file_extension == 'csv':
                viz_data = pd.read_csv(uploaded_file)
            elif file_extension in ['xlsx', 'xls']:
                viz_data = pd.read_excel(uploaded_file)
            else:
                st.error("❌ Formato não suportado")
                st.stop()
            
            st.subheader("📊 Criar Visualização")
            
            chart_type = st.selectbox(
                "Tipo de gráfico:",
                ["Linha", "Barra", "Scatter", "Box Plot", "Histograma", "Pareto"]
            )
            
            if chart_type in ["Linha", "Barra", "Scatter"]:
                col1, col2 = st.columns(2)
                with col1:
                    x_col = st.selectbox("Eixo X:", viz_data.columns)
                with col2:
                    y_col = st.selectbox("Eixo Y:", viz_data.columns)
                
                if st.button("Gerar Gráfico", type="primary"):
                    if chart_type == "Linha":
                        fig = px.line(viz_data, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
                    elif chart_type == "Barra":
                        fig = px.bar(viz_data, x=x_col, y=y_col, title=f"{y_col} por {x_col}")
                    elif chart_type == "Scatter":
                        fig = px.scatter(viz_data, x=x_col, y=y_col, title=f"{y_col} vs {x_col}",
                                       trendline="ols")
                    
                    st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Box Plot":
                numeric_cols_viz = [col for col in viz_data.columns if pd.to_numeric(viz_data[col], errors='coerce').notna().any()]
                col = st.selectbox("Selecione a variável:", numeric_cols_viz)
                if col:
                    fig = px.box(viz_data, y=col, title=f"Box Plot - {col}")
                    st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Histograma":
                numeric_cols_viz = [col for col in viz_data.columns if pd.to_numeric(viz_data[col], errors='coerce').notna().any()]
                col = st.selectbox("Selecione a variável:", numeric_cols_viz)
                bins = st.slider("Número de bins:", 10, 50, 20)
                if col:
                    fig = px.histogram(viz_data, x=col, nbins=bins, title=f"Histograma - {col}")
                    st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Pareto":
                cat_col = st.selectbox("Categoria:", viz_data.columns)
                val_col = st.selectbox("Valor (ou use contagem):", ["Contagem"] + list(viz_data.columns))
                
                if st.button("Gerar Pareto", type="primary"):
                    if val_col == "Contagem":
                        pareto_data = viz_data[cat_col].value_counts().reset_index()
                        pareto_data.columns = ['Categoria', 'Frequência']
                    else:
                        pareto_data = viz_data.groupby(cat_col)[val_col].sum().reset_index()
                        pareto_data.columns = ['Categoria', 'Valor']
                    
                    pareto_data = pareto_data.sort_values(by=pareto_data.columns[1], ascending=False)
                    pareto_data['Percentual'] = pareto_data.iloc[:, 1] / pareto_data.iloc[:, 1].sum() * 100
                    pareto_data['Acumulado'] = pareto_data['Percentual'].cumsum()
                    
                    fig = go.Figure()
                    
                    fig.add_trace(go.Bar(
                        x=pareto_data['Categoria'],
                        y=pareto_data.iloc[:, 1],
                        name='Frequência',
                        yaxis='y'
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=pareto_data['Categoria'],
                        y=pareto_data['Acumulado'],
                        name='% Acumulado',
                        yaxis='y2',
                        line=dict(color='red'),
                        mode='lines+markers'
                    ))
                    
                    fig.update_layout(
                        title="Gráfico de Pareto",
                        yaxis=dict(title="Frequência"),
                        yaxis2=dict(title="% Acumulado", overlaying='y', side='right', range=[0, 100]),
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {str(e)}")

st.divider()
st.header("📊 Resumo da Fase Measure")

if 'project_data' in st.session_state:
    project_data = st.session_state.project_data
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        plans_count = len(st.session_state.get('collection_plans', []))
        st.metric("Planos de Coleta", plans_count)
    
    with col2:
        if project_data.get('baseline_value'):
            st.metric("Baseline", f"{project_data['baseline_value']:.2f}")
    
    with col3:
        if project_data.get('target_value'):
            st.metric("Meta", f"{project_data['target_value']:.2f}")
    
    with col4:
        st.metric("Status", "Em andamento")
    
    st.subheader("✅ Checklist da Fase Measure")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Atividades Principais:**")
        checks = {
            "Plano de Coleta definido": plans_count > 0,
            "MSA realizado": 'msa_data' in st.session_state,
            "Dados do processo coletados": 'process_data' in st.session_state,
            "Capacidade calculada": False
        }
        
        for item, done in checks.items():
            if done:
                st.write(f"✅ {item}")
            else:
                st.write(f"⬜ {item}")
    
    with col2:
        st.write("**Próximos Passos:**")
        if all(checks.values()):
            st.success("Fase Measure completa! Prossiga para Analyze.")
        else:
            st.info("Complete todas as atividades antes de prosseguir.")

st.divider()
st.caption("💡 **Dica:** Garanta que o sistema de medição é confiável antes de coletar dados para análise")
