import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
from scipy import stats
from scipy.stats import norm

# Configuração da página
st.set_page_config(
    page_title="Measure - Green Belt Project",
    page_icon="📊",
    layout="wide"
)

# Inicializar Supabase
from supabase import create_client, Client

@st.cache_resource
def init_supabase():
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY", "")
    if url and key:
        return create_client(url, key)
    return None

supabase = init_supabase()

if not supabase:
    st.error("⚠️ Supabase não configurado!")
    st.stop()

# Verificar projeto ativo
if 'current_project_id' not in st.session_state or not st.session_state.current_project_id:
    st.warning("⚠️ Nenhum projeto selecionado. Por favor, selecione ou crie um projeto na página inicial.")
    st.stop()

# Header
st.title("📊 Measure - Coleta e Análise de Dados")
st.info(f"📁 Projeto: **{st.session_state.get('current_project_name', 'Não identificado')}**")

# Inicializar session state
if 'uploaded_data' not in st.session_state:
    st.session_state.uploaded_data = None
if 'data_columns' not in st.session_state:
    st.session_state.data_columns = []
if 'column_types' not in st.session_state:
    st.session_state.column_types = {}

# Carregar configuração de medição existente
try:
    config_response = supabase.table('measure_config').select("*").eq('project_id', st.session_state.current_project_id).execute()
    existing_config = config_response.data[0] if config_response.data else {}
except:
    existing_config = {}

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📤 Upload de Dados",
    "📊 Visualização",
    "📈 Estatísticas",
    "🎯 Capacidade do Processo",
    "✅ Validação",
    "💾 Dados Salvos"
])

# Tab 1: Upload de Dados
with tab1:
    st.header("Upload e Configuração de Dados")
    
    # Opções de entrada de dados
    data_input_method = st.radio(
        "Método de entrada de dados:",
        ["📤 Upload de arquivo (CSV/Excel)", "📝 Entrada manual", "🔄 Usar dados salvos"]
    )
    
    if "📤 Upload" in data_input_method:
        st.subheader("Upload de Arquivo")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded_file = st.file_uploader(
                "Escolha um arquivo CSV ou Excel",
                type=['csv', 'xlsx', 'xls'],
                help="O sistema detectará automaticamente as colunas do seu arquivo"
            )
            
            if uploaded_file is not None:
                try:
                    # Ler arquivo
                    if uploaded_file.name.endswith('.csv'):
                        # Tentar diferentes encodings
                        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
                        df = None
                        for encoding in encodings:
                            try:
                                uploaded_file.seek(0)
                                df = pd.read_csv(uploaded_file, encoding=encoding)
                                st.success(f"✅ Arquivo lido com sucesso (encoding: {encoding})")
                                break
                            except:
                                continue
                        
                        if df is None:
                            uploaded_file.seek(0)
                            df = pd.read_csv(uploaded_file, encoding='utf-8', errors='ignore')
                    else:
                        df = pd.read_excel(uploaded_file)
                    
                    st.session_state.uploaded_data = df
                    st.session_state.data_columns = df.columns.tolist()
                    
                    # Mostrar preview
                    st.success(f"✅ Arquivo carregado com sucesso! {len(df)} linhas e {len(df.columns)} colunas")
                    
                    # Informações do arquivo
                    col1_1, col2_1, col3_1, col4_1 = st.columns(4)
                    with col1_1:
                        st.metric("Total de Linhas", len(df))
                    with col2_1:
                        st.metric("Total de Colunas", len(df.columns))
                    with col3_1:
                        missing = df.isnull().sum().sum()
                        st.metric("Valores Faltantes", missing)
                    with col4_1:
                        memory = df.memory_usage(deep=True).sum() / 1024 / 1024
                        st.metric("Tamanho", f"{memory:.2f} MB")
                    
                    # Preview dos dados
                    st.subheader("Preview dos Dados")
                    
                    # Opção de visualização
                    view_option = st.radio(
                        "Visualizar:",
                        ["Primeiras linhas", "Últimas linhas", "Amostra aleatória", "Dados completos"],
                        horizontal=True
                    )
                    
                    if view_option == "Primeiras linhas":
                        n_rows = st.slider("Número de linhas", 5, 50, 10)
                        st.dataframe(df.head(n_rows), use_container_width=True)
                    elif view_option == "Últimas linhas":
                        n_rows = st.slider("Número de linhas", 5, 50, 10)
                        st.dataframe(df.tail(n_rows), use_container_width=True)
                    elif view_option == "Amostra aleatória":
                        n_rows = st.slider("Número de linhas", 5, 50, 10)
                        st.dataframe(df.sample(min(n_rows, len(df))), use_container_width=True)
                    else:
                        st.dataframe(df, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"Erro ao ler arquivo: {e}")
        
        with col2:
            if st.session_state.uploaded_data is not None:
                st.subheader("Colunas Detectadas")
                
                df = st.session_state.uploaded_data
                
                # Análise automática de tipos
                st.write("**Análise Automática dos Tipos:**")
                
                column_info = []
                for col in df.columns:
                    # Detectar tipo
                    if df[col].dtype in ['int64', 'float64']:
                        tipo = "Numérico"
                        icon = "🔢"
                    elif df[col].dtype == 'object':
                        # Verificar se é data
                        try:
                            pd.to_datetime(df[col], errors='coerce')
                            if df[col].str.match(r'\d{4}-\d{2}-\d{2}').any():
                                tipo = "Data"
                                icon = "📅"
                            else:
                                tipo = "Texto"
                                icon = "📝"
                        except:
                            tipo = "Texto"
                            icon = "📝"
                    elif df[col].dtype == 'bool':
                        tipo = "Booleano"
                        icon = "✓✗"
                    elif pd.api.types.is_datetime64_any_dtype(df[col]):
                        tipo = "Data/Hora"
                        icon = "📅"
                    else:
                        tipo = "Outro"
                        icon = "❓"
                    
                    # Estatísticas básicas
                    non_null = df[col].notna().sum()
                    null_count = df[col].isna().sum()
                    unique = df[col].nunique()
                    
                    column_info.append({
                        'Coluna': f"{icon} {col}",
                        'Tipo': tipo,
                        'Não-Nulos': non_null,
                        'Nulos': null_count,
                        'Únicos': unique
                    })
                
                info_df = pd.DataFrame(column_info)
                st.dataframe(info_df, use_container_width=True, hide_index=True)
    
    # Configuração de colunas
    if st.session_state.uploaded_data is not None:
        st.divider()
        st.subheader("⚙️ Configuração das Colunas")
        
        df = st.session_state.uploaded_data
        
        with st.expander("Configurar tipos e papéis das colunas", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            # Configuração de colunas especiais
            with col1:
                st.write("**Identificação:**")
                
                date_columns = [col for col in df.columns if 'data' in col.lower() or 'date' in col.lower()]
                date_col = st.selectbox(
                    "Coluna de Data",
                    options=['Nenhuma'] + df.columns.tolist(),
                    index=1 if date_columns else 0,
                    help="Selecione a coluna que contém as datas"
                )
                
                id_col = st.selectbox(
                    "Coluna de ID/Código",
                    options=['Nenhuma'] + df.columns.tolist(),
                    help="Coluna com identificador único"
                )
            
            with col2:
                st.write("**Categorização:**")
                
                text_columns = df.select_dtypes(include=['object']).columns.tolist()
                
                category_cols = st.multiselect(
                    "Colunas Categóricas",
                    options=text_columns,
                    help="Colunas para agrupamento e filtros"
                )
                
                group_col = st.selectbox(
                    "Coluna de Agrupamento Principal",
                    options=['Nenhuma'] + text_columns,
                    help="Coluna principal para análises agrupadas"
                )
            
            with col3:
                st.write("**Medições:**")
                
                numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
                
                metric_cols = st.multiselect(
                    "Colunas de Métricas",
                    options=numeric_columns,
                    default=numeric_columns[:5] if len(numeric_columns) > 5 else numeric_columns,
                    help="Colunas numéricas para análise"
                )
                
                target_col = st.selectbox(
                    "Variável Principal (Y)",
                    options=['Nenhuma'] + numeric_columns,
                    help="Variável principal do estudo"
                )
        
        # Transformações básicas
        with st.expander("🔄 Transformações de Dados (Opcional)"):
            st.write("**Aplicar transformações aos dados:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Tratamento de valores faltantes
                st.write("**Valores Faltantes:**")
                missing_strategy = st.selectbox(
                    "Estratégia para valores faltantes",
                    ["Manter como está", "Remover linhas", "Preencher com média", 
                     "Preencher com mediana", "Preencher com zero", "Preencher com anterior"]
                )
                
                if missing_strategy != "Manter como está":
                    if st.button("Aplicar tratamento"):
                        if missing_strategy == "Remover linhas":
                            df = df.dropna()
                        elif missing_strategy == "Preencher com média":
                            df = df.fillna(df.mean())
                        elif missing_strategy == "Preencher com mediana":
                            df = df.fillna(df.median())
                        elif missing_strategy == "Preencher com zero":
                            df = df.fillna(0)
                        elif missing_strategy == "Preencher com anterior":
                            df = df.fillna(method='ffill')
                        
                        st.session_state.uploaded_data = df
                        st.success(f"✅ Tratamento aplicado: {missing_strategy}")
                        st.rerun()
            
            with col2:
                # Filtros
                st.write("**Filtros:**")
                
                if date_col != 'Nenhuma' and date_col in df.columns:
                    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                    
                    date_range = st.date_input(
                        "Filtrar por período",
                        value=(df[date_col].min(), df[date_col].max()),
                        key="date_filter"
                    )
                    
                    if st.button("Aplicar filtro de data"):
                        mask = (df[date_col] >= pd.to_datetime(date_range[0])) & \
                               (df[date_col] <= pd.to_datetime(date_range[1]))
                        df = df[mask]
                        st.session_state.uploaded_data = df
                        st.success(f"✅ Filtro aplicado: {len(df)} linhas mantidas")
                        st.rerun()
        
        # Salvar dados no banco
        st.divider()
        st.subheader("💾 Salvar Dados no Projeto")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            data_description = st.text_area(
                "Descrição dos dados",
                placeholder="Descreva brevemente o que estes dados representam",
                help="Esta descrição ajudará a identificar os dados posteriormente"
            )
            
            data_source = st.text_input(
                "Fonte dos dados",
                placeholder="Ex: Sistema ERP, Planilha de controle, Sensor IoT"
            )
            
            collection_period = st.text_input(
                "Período de coleta",
                placeholder="Ex: Janeiro 2024 - Março 2024"
            )
        
        with col2:
            st.write("**Resumo para salvar:**")
            st.metric("Registros", len(df))
            st.metric("Colunas", len(df.columns))
            st.metric("Tamanho", f"{df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
        
        if st.button("💾 Salvar Dados no Banco", type="primary"):
            try:
                # Preparar configuração
                config_data = {
                    'project_id': st.session_state.current_project_id,
                    'data_collection_plan': {
                        'description': data_description,
                        'source': data_source,
                        'period': collection_period,
                        'columns': df.columns.tolist(),
                        'shape': {'rows': len(df), 'columns': len(df.columns)},
                        'date_column': date_col if date_col != 'Nenhuma' else None,
                        'id_column': id_col if id_col != 'Nenhuma' else None,
                        'category_columns': category_cols,
                        'metric_columns': metric_cols,
                        'target_column': target_col if target_col != 'Nenhuma' else None
                    }
                }
                
                # Salvar configuração
                if existing_config:
                    supabase.table('measure_config').update(config_data).eq('project_id', st.session_state.current_project_id).execute()
                else:
                    supabase.table('measure_config').insert(config_data).execute()
                
                # Salvar dados em lote
                success_count = 0
                error_count = 0
                batch_size = 100  # Inserir em lotes de 100
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i in range(0, len(df), batch_size):
                    batch = df.iloc[i:i+batch_size]
                    
                    for _, row in batch.iterrows():
                        try:
                            # Preparar dados para inserção
                            measurement_data = {
                                'project_id': st.session_state.current_project_id,
                                'measurement_date': datetime.now().date().isoformat(),
                                'metrics': row.to_dict(),  # Salvar todos os dados como JSON
                                'data_source': data_source
                            }
                            
                            # Adicionar campos especiais se configurados
                            if date_col != 'Nenhuma' and date_col in row:
                                measurement_data['measurement_date'] = pd.to_datetime(row[date_col]).date().isoformat()
                            
                            if group_col != 'Nenhuma' and group_col in row:
                                measurement_data['category'] = str(row[group_col])
                            
                            supabase.table('measurements').insert(measurement_data).execute()
                            success_count += 1
                            
                        except Exception as e:
                            error_count += 1
                    
                    # Atualizar progresso
                    progress = (i + batch_size) / len(df)
                    progress_bar.progress(min(progress, 1.0))
                    status_text.text(f"Salvando: {min(i + batch_size, len(df))}/{len(df)} registros")
                
                progress_bar.empty()
                status_text.empty()
                
                if success_count > 0:
                    st.success(f"✅ {success_count} registros salvos com sucesso!")
                if error_count > 0:
                    st.warning(f"⚠️ {error_count} registros com erro")
                
                # Atualizar fase do projeto
                supabase.table('projects').update({
                    'current_phase': 'Measure',
                    'progress_percentage': 40
                }).eq('id', st.session_state.current_project_id).execute()
                
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")
    
    elif "📝 Entrada manual" in data_input_method:
        st.subheader("Entrada Manual de Dados")
        
        # Verificar se há configuração salva
        if existing_config and 'data_collection_plan' in existing_config:
            plan = existing_config['data_collection_plan']
            if 'columns' in plan:
                st.info(f"Usando estrutura salva: {len(plan['columns'])} colunas")
                
                # Criar formulário baseado nas colunas salvas
                with st.form("manual_entry_form"):
                    st.write("**Preencha os dados:**")
                    
                    form_data = {}
                    
                    # Criar campos dinamicamente
                    cols = st.columns(3)
                    for i, col_name in enumerate(plan['columns']):
                        with cols[i % 3]:
                            # Determinar tipo de input baseado no nome/tipo
                            if 'date' in col_name.lower() or 'data' in col_name.lower():
                                form_data[col_name] = st.date_input(col_name)
                            elif col_name in plan.get('metric_columns', []):
                                form_data[col_name] = st.number_input(col_name, step=0.01)
                            elif col_name in plan.get('category_columns', []):
                                form_data[col_name] = st.text_input(col_name)
                            else:
                                form_data[col_name] = st.text_input(col_name)
                    
                    submitted = st.form_submit_button("Adicionar Registro")
                    
                    if submitted:
                        try:
                            # Salvar no banco
                            measurement_data = {
                                'project_id': st.session_state.current_project_id,
                                'measurement_date': datetime.now().date().isoformat(),
                                'metrics': form_data,
                                'data_source': 'Manual Entry'
                            }
                            
                            supabase.table('measurements').insert(measurement_data).execute()
                            st.success("✅ Registro adicionado com sucesso!")
                            
                        except Exception as e:
                            st.error(f"Erro ao salvar: {e}")
        else:
            st.warning("Configure primeiro a estrutura dos dados fazendo upload de um arquivo exemplo.")
    
    else:  # Usar dados salvos
        st.subheader("Dados Salvos do Projeto")
        
        try:
            # Carregar dados salvos
            measurements = supabase.table('measurements').select("*").eq('project_id', st.session_state.current_project_id).execute()
            
            if measurements.data:
                st.success(f"✅ {len(measurements.data)} registros encontrados")
                
                # Converter para DataFrame
                data_list = []
                for m in measurements.data:
                    if 'metrics' in m and m['metrics']:
                        record = m['metrics']
                        record['_measurement_date'] = m.get('measurement_date')
                        record['_id'] = m.get('id')
                        data_list.append(record)
                
                if data_list:
                    df = pd.DataFrame(data_list)
                    st.session_state.uploaded_data = df
                    
                    # Preview
                    st.dataframe(df.head(10), use_container_width=True)
                else:
                    st.warning("Dados salvos não contêm métricas")
            else:
                st.info("Nenhum dado salvo encontrado para este projeto")
                
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")

# Tab 2: Visualização
with tab2:
    st.header("Visualização dos Dados")
    
    if st.session_state.uploaded_data is not None:
        df = st.session_state.uploaded_data
        
        # Identificar colunas numéricas e categóricas
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        # Tipo de gráfico
        chart_type = st.selectbox(
            "Tipo de Visualização",
            ["Histograma", "Boxplot", "Scatter", "Linha", "Barras", "Pizza", "Heatmap", "Pareto"]
        )
        
        col1, col2 = st.columns([2, 1])
        
        with col2:
            st.write("**Configuração do Gráfico:**")
            
            if chart_type == "Histograma":
                x_col = st.selectbox("Variável", numeric_cols)
                bins = st.slider("Número de bins", 10, 100, 30)
                
                if st.button("Gerar Gráfico"):
                    fig = px.histogram(df, x=x_col, nbins=bins, title=f"Histograma de {x_col}")
                    col1.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Boxplot":
                y_col = st.selectbox("Variável", numeric_cols)
                x_col = st.selectbox("Agrupar por (opcional)", ['Nenhum'] + categorical_cols)
                
                if st.button("Gerar Gráfico"):
                    if x_col == 'Nenhum':
                        fig = px.box(df, y=y_col, title=f"Boxplot de {y_col}")
                    else:
                        fig = px.box(df, x=x_col, y=y_col, title=f"Boxplot de {y_col} por {x_col}")
                    col1.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Scatter":
                x_col = st.selectbox("Eixo X", numeric_cols)
                y_col = st.selectbox("Eixo Y", numeric_cols)
                color_col = st.selectbox("Cor (opcional)", ['Nenhum'] + categorical_cols)
                size_col = st.selectbox("Tamanho (opcional)", ['Nenhum'] + numeric_cols)
                
                if st.button("Gerar Gráfico"):
                    fig_params = {'x': x_col, 'y': y_col, 'title': f"{y_col} vs {x_col}"}
                    if color_col != 'Nenhum':
                        fig_params['color'] = color_col
                    if size_col != 'Nenhum':
                        fig_params['size'] = size_col
                    
                    fig = px.scatter(df, **fig_params, trendline="ols")
                    col1.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Linha":
                # Tentar identificar coluna de tempo
                time_cols = [col for col in df.columns if 'date' in col.lower() or 'data' in col.lower() or 'time' in col.lower()]
                
                if time_cols:
                    x_col = st.selectbox("Eixo X (tempo)", time_cols)
                else:
                    x_col = st.selectbox("Eixo X", df.columns.tolist())
                
                y_cols = st.multiselect("Variáveis Y", numeric_cols)
                
                if st.button("Gerar Gráfico"):
                    if y_cols:
                        fig = go.Figure()
                        for y_col in y_cols:
                            fig.add_trace(go.Scatter(x=df[x_col], y=df[y_col], mode='lines+markers', name=y_col))
                        fig.update_layout(title="Gráfico de Linha", xaxis_title=x_col, yaxis_title="Valor")
                        col1.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Barras":
                x_col = st.selectbox("Categoria", categorical_cols) if categorical_cols else None
                y_col = st.selectbox("Valor", numeric_cols) if numeric_cols else None
                agg_func = st.selectbox("Agregação", ["sum", "mean", "count", "max", "min"])
                
                if st.button("Gerar Gráfico") and x_col and y_col:
                    agg_data = df.groupby(x_col)[y_col].agg(agg_func).reset_index()
                    fig = px.bar(agg_data, x=x_col, y=y_col, title=f"{agg_func} de {y_col} por {x_col}")
                    col1.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Pizza":
                cat_col = st.selectbox("Categoria", categorical_cols) if categorical_cols else None
                
                if st.button("Gerar Gráfico") and cat_col:
                    value_counts = df[cat_col].value_counts()
                    fig = px.pie(values=value_counts.values, names=value_counts.index, title=f"Distribuição de {cat_col}")
                    col1.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Heatmap":
                if st.button("Gerar Gráfico"):
                    corr_matrix = df[numeric_cols].corr()
                    fig = px.imshow(corr_matrix, text_auto=True, title="Matriz de Correlação")
                    col1.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Pareto":
                cat_col = st.selectbox("Categoria", categorical_cols) if categorical_cols else None
                val_col = st.selectbox("Valor", numeric_cols) if numeric_cols else None
                
                if st.button("Gerar Gráfico") and cat_col and val_col:
                    # Agregar dados
                    pareto_data = df.groupby(cat_col)[val_col].sum().sort_values(ascending=False)
                    
                    # Calcular percentual acumulado
                    cumsum = pareto_data.cumsum()
                    cumperc = 100 * cumsum / pareto_data.sum()
                    
                    # Criar gráfico
                    fig = go.Figure()
                    
                    fig.add_trace(go.Bar(
                        x=pareto_data.index,
                        y=pareto_data.values,
                        name='Frequência',
                        yaxis='y'
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=pareto_data.index,
                        y=cumperc.values,
                        name='% Acumulado',
                        yaxis='y2',
                        mode='lines+markers',
                        marker=dict(color='red')
                    ))
                    
                    fig.update_layout(
                        title=f'Diagrama de Pareto - {cat_col}',
                        yaxis=dict(title=val_col),
                        yaxis2=dict(title='% Acumulado', overlaying='y', side='right', range=[0, 105]),
                        xaxis=dict(tickangle=45)
                    )
                    
                    col1.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Carregue dados na aba 'Upload de Dados' para visualizar")

# Tab 3: Estatísticas
with tab3:
    st.header("Análise Estatística")
    
    if st.session_state.uploaded_data is not None:
        df = st.session_state.uploaded_data
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        
        if numeric_cols:
            selected_cols = st.multiselect(
                "Selecione as variáveis para análise:",
                numeric_cols,
                default=numeric_cols[:5] if len(numeric_cols) > 5 else numeric_cols
            )
            
            if selected_cols:
                # Estatísticas descritivas
                st.subheader("Estatísticas Descritivas")
                stats_df = df[selected_cols].describe().T
                stats_df['CV%'] = (df[selected_cols].std() / df[selected_cols].mean() * 100).round(2)
                stats_df['IQR'] = df[selected_cols].quantile(0.75) - df[selected_cols].quantile(0.25)
                
                st.dataframe(stats_df, use_container_width=True)
                
                # Download das estatísticas
                csv = stats_df.to_csv()
                st.download_button(
                    label="📥 Download Estatísticas (CSV)",
                    data=csv,
                    file_name=f"estatisticas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
                
                # Teste de normalidade
                st.subheader("Teste de Normalidade (Shapiro-Wilk)")
                
                normality_results = []
                for col in selected_cols:
                    data = df[col].dropna()
                    if len(data) >= 3:
                        stat, p_value = stats.shapiro(data)
                        normality_results.append({
                            'Variável': col,
                            'Estatística W': round(stat, 6),
                            'P-valor': round(p_value, 6),
                            'Normal (α=0.05)': '✅ Sim' if p_value > 0.05 else '❌ Não'
                        })
                
                if normality_results:
                    norm_df = pd.DataFrame(normality_results)
                    st.dataframe(norm_df, use_container_width=True, hide_index=True)
        else:
            st.warning("Nenhuma coluna numérica encontrada nos dados")
    else:
        st.info("Carregue dados na aba 'Upload de Dados' para análise estatística")

# Tab 4: Capacidade do Processo
with tab4:
    st.header("Análise de Capacidade do Processo")
    
    if st.session_state.uploaded_data is not None:
        df = st.session_state.uploaded_data
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        
        if numeric_cols:
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.subheader("Configuração")
                
                process_var = st.selectbox("Variável do Processo", numeric_cols)
                
                st.write("**Limites de Especificação:**")
                
                lsl = st.number_input("LSL (Lower Spec Limit)", value=None)
                usl = st.number_input("USL (Upper Spec Limit)", value=None)
                target = st.number_input("Target (Alvo)", value=None)
                
                if st.button("Calcular Capacidade", type="primary"):
                    if lsl is not None and usl is not None:
                        data = df[process_var].dropna()
                        
                        # Cálculos
                        mean = data.mean()
                        std = data.std()
                        
                        # Índices de capacidade
                        cp = (usl - lsl) / (6 * std)
                        cpu = (usl - mean) / (3 * std)
                        cpl = (mean - lsl) / (3 * std)
                        cpk = min(cpu, cpl)
                        
                        # Pp e Ppk (performance)
                        pp = (usl - lsl) / (6 * data.std())
                        ppu = (usl - mean) / (3 * data.std())
                        ppl = (mean - lsl) / (3 * data.std())
                        ppk = min(ppu, ppl)
                        
                        # Nível sigma
                        sigma_level = 3 * cpk
                        
                        # DPMO
                        z_usl = (usl - mean) / std
                        z_lsl = (lsl - mean) / std
                        
                        from scipy.stats import norm
                        p_above_usl = 1 - norm.cdf(z_usl)
                        p_below_lsl = norm.cdf(z_lsl)
                        total_defects = p_above_usl + p_below_lsl
                        dpmo = total_defects * 1000000
                        
                        # Mostrar resultados
                        st.subheader("Resultados")
                        
                        col1_r, col2_r = st.columns(2)
                        
                        with col1_r:
                            st.metric("Cp", f"{cp:.3f}")
                            st.metric("Cpk", f"{cpk:.3f}")
                            st.metric("Pp", f"{pp:.3f}")
                            st.metric("Ppk", f"{ppk:.3f}")
                        
                        with col2_r:
                            st.metric("Nível Sigma", f"{sigma_level:.2f}σ")
                            st.metric("DPMO", f"{dpmo:.0f}")
                            st.metric("Yield", f"{(1-total_defects)*100:.2f}%")
                        
                        # Interpretação
                        st.write("**Interpretação:**")
                        
                        if cpk >= 1.33:
                            st.success("✅ Processo capaz (Cpk ≥ 1.33)")
                        elif cpk >= 1.0:
                            st.warning("⚠️ Processo marginalmente capaz (1.0 ≤ Cpk < 1.33)")
                        else:
                            st.error("❌ Processo não capaz (Cpk < 1.0)")
            
            with col2:
                if lsl is not None and usl is not None and process_var:
                    st.subheader("Gráfico de Capacidade")
                    
                    data = df[process_var].dropna()
                    
                    # Criar histograma com curva normal e limites
                    fig = go.Figure()
                    
                    # Histograma
                    fig.add_trace(go.Histogram(
                        x=data,
                        name='Dados',
                        nbinsx=30,
                        histnorm='probability density'
                    ))
                    
                    # Curva normal
                    x_range = np.linspace(data.min(), data.max(), 100)
                    y_normal = norm.pdf(x_range, data.mean(), data.std())
                    
                    fig.add_trace(go.Scatter(
                        x=x_range,
                        y=y_normal,
                        mode='lines',
                        name='Normal',
                        line=dict(color='red', width=2)
                    ))
                    
                    # Adicionar linhas de especificação
                    fig.add_vline(x=lsl, line_dash="dash", line_color="red", annotation_text="LSL")
                    fig.add_vline(x=usl, line_dash="dash", line_color="red", annotation_text="USL")
                    if target:
                        fig.add_vline(x=target, line_dash="dash", line_color="green", annotation_text="Target")
                    fig.add_vline(x=data.mean(), line_dash="solid", line_color="blue", annotation_text="Mean")
                    
                    fig.update_layout(
                        title=f"Capacidade do Processo - {process_var}",
                        xaxis_title=process_var,
                        yaxis_title="Densidade"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Nenhuma coluna numérica encontrada nos dados")
    else:
        st.info("Carregue dados na aba 'Upload de Dados' para análise de capacidade")

# Tab 5: Validação
with tab5:
    st.header("Validação de Dados")
    
    if st.session_state.uploaded_data is not None:
        df = st.session_state.uploaded_data
        
        # Relatório de qualidade
        st.subheader("Relatório de Qualidade dos Dados")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_cells = len(df) * len(df.columns)
            missing_cells = df.isnull().sum().sum()
            completeness = (1 - missing_cells / total_cells) * 100
            st.metric("Completude", f"{completeness:.1f}%")
        
        with col2:
            duplicates = df.duplicated().sum()
            uniqueness = (1 - duplicates / len(df)) * 100
            st.metric("Unicidade", f"{uniqueness:.1f}%")
        
        with col3:
            st.metric("Registros Duplicados", duplicates)
        
        with col4:
            st.metric("Valores Faltantes", missing_cells)
        
        # Detalhamento por coluna
        st.subheader("Análise Detalhada por Coluna")
        
        column_analysis = []
        for col in df.columns:
            analysis = {
                'Coluna': col,
                'Tipo': str(df[col].dtype),
                'Não-Nulos': df[col].notna().sum(),
                'Nulos': df[col].isna().sum(),
                '% Completo': f"{(df[col].notna().sum() / len(df) * 100):.1f}%",
                'Únicos': df[col].nunique(),
                'Duplicados': len(df) - df[col].nunique()
            }
            
            # Adicionar análise de outliers para colunas numéricas
            if df[col].dtype in ['int64', 'float64']:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                outliers = ((df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))).sum()
                analysis['Outliers'] = outliers
            else:
                analysis['Outliers'] = 'N/A'
            
            column_analysis.append(analysis)
        
        analysis_df = pd.DataFrame(column_analysis)
        st.dataframe(analysis_df, use_container_width=True, hide_index=True)
        
        # MSA - Measurement System Analysis (se aplicável)
        st.subheader("MSA - Análise do Sistema de Medição")
        
        st.info("""
        Para realizar uma análise completa do sistema de medição (MSA), você precisará de:
        - Dados de repetibilidade (mesma peça, mesmo operador)
        - Dados de reprodutibilidade (mesma peça, operadores diferentes)
        - Padrão de referência conhecido
        """)
        
        if st.checkbox("Tenho dados para MSA"):
            st.write("Configuração MSA em desenvolvimento...")
    else:
        st.info("Carregue dados na aba 'Upload de Dados' para validação")

# Tab 6: Dados Salvos
with tab6:
    st.header("Dados Salvos do Projeto")
    
    try:
        # Carregar dados salvos
        measurements = supabase.table('measurements').select("*").eq('project_id', st.session_state.current_project_id).order('created_at', desc=True).execute()
        
        if measurements.data:
            st.success(f"✅ {len(measurements.data)} registros salvos encontrados")
            
            # Opções de visualização
            view_option = st.radio(
                "Visualizar:",
                ["Resumo", "Dados Completos", "Exportar"],
                horizontal=True
            )
            
            if view_option == "Resumo":
                # Mostrar resumo
                st.subheader("Resumo dos Dados Salvos")
                
                # Estatísticas gerais
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total de Registros", len(measurements.data))
                
                with col2:
                    dates = [m['measurement_date'] for m in measurements.data if 'measurement_date' in m]
                    if dates:
                        st.metric("Período", f"{min(dates)} a {max(dates)}")
                
                with col3:
                    sources = set([m.get('data_source', 'Unknown') for m in measurements.data])
                    st.metric("Fontes de Dados", len(sources))
                
                with col4:
                    # Contar colunas únicas
                    all_keys = set()
                    for m in measurements.data:
                        if 'metrics' in m and m['metrics']:
                            all_keys.update(m['metrics'].keys())
                    st.metric("Variáveis", len(all_keys))
            
            elif view_option == "Dados Completos":
                # Converter para DataFrame
                data_list = []
                for m in measurements.data:
                    if 'metrics' in m and m['metrics']:
                        record = m['metrics']
                        record['_measurement_date'] = m.get('measurement_date')
                        record['_data_source'] = m.get('data_source')
                        record['_created_at'] = m.get('created_at')
                        data_list.append(record)
                
                if data_list:
                    df_saved = pd.DataFrame(data_list)
                    st.dataframe(df_saved, use_container_width=True)
            
            else:  # Exportar
                st.subheader("Exportar Dados")
                
                # Preparar dados para exportação
                data_list = []
                for m in measurements.data:
                    if 'metrics' in m and m['metrics']:
                        record = m['metrics']
                        record['measurement_date'] = m.get('measurement_date')
                        record['data_source'] = m.get('data_source')
                        data_list.append(record)
                
                if data_list:
                    df_export = pd.DataFrame(data_list)
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # CSV
                        csv = df_export.to_csv(index=False)
                        st.download_button(
                            label="📄 Download CSV",
                            data=csv,
                            file_name=f"measure_data_{st.session_state.current_project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    
                    with col2:
                        # Excel
                        buffer = io.BytesIO()
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            df_export.to_excel(writer, sheet_name='Measurements', index=False)
                        
                        st.download_button(
                            label="📊 Download Excel",
                            data=buffer.getvalue(),
                            file_name=f"measure_data_{st.session_state.current_project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    
                    with col3:
                        # JSON
                        json_str = df_export.to_json(orient='records', date_format='iso')
                        st.download_button(
                            label="📦 Download JSON",
                            data=json_str,
                            file_name=f"measure_data_{st.session_state.current_project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
        else:
            st.info("Nenhum dado salvo encontrado para este projeto")
            
    except Exception as e:
        st.error(f"Erro ao carregar dados salvos: {e}")

# Resumo e próximos passos
st.divider()
st.header("📊 Resumo da Fase Measure")

if st.session_state.uploaded_data is not None:
    df = st.session_state.uploaded_data
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Registros Carregados", len(df))
    
    with col2:
        st.metric("Variáveis", len(df.columns))
    
    with col3:
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        st.metric("Variáveis Numéricas", len(numeric_cols))
    
    with col4:
        completeness = (1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        st.metric("Completude", f"{completeness:.1f}%")
    
    if completeness >= 70:
        st.success("✅ Dados prontos para análise! Você pode prosseguir para a fase Analyze.")
        
        if st.button("➡️ Avançar para Fase Analyze"):
            try:
                supabase.table('projects').update({
                    'current_phase': 'Analyze',
                    'progress_percentage': 50
                }).eq('id', st.session_state.current_project_id).execute()
                
                st.success("Projeto avançado para fase Analyze!")
                st.info("Acesse a página Analyze no menu lateral.")
                
            except Exception as e:
                st.error(f"Erro ao atualizar fase: {e}")
    else:
        st.warning(f"⚠️ Recomenda-se ter pelo menos 70% de completude dos dados para prosseguir (atual: {completeness:.1f}%)")
else:
    st.info("Carregue dados para começar a fase Measure")

# Footer
st.markdown("---")
st.caption("📊 Fase Measure - Green Belt Project Management System")
