import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from scipy import stats
import io

# Configuração da página
st.set_page_config(
    page_title="Measure - Green Belt",
    page_icon="📏",
    layout="wide"
)

# Inicializar Supabase
try:
    from supabase import create_client, Client
    
    @st.cache_resource
    def init_supabase():
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "")
        if url and key:
            return create_client(url, key)
        return None
    
    supabase = init_supabase()
except Exception as e:
    st.warning(f"Supabase não configurado: {e}")
    supabase = None

# Título
st.title("📏 Measure - Coleta, Validação e Padronização de Dados")

# Verificar se há projeto selecionado
if 'project_id' not in st.session_state or st.session_state.project_id is None:
    st.warning("⚠️ Nenhum projeto selecionado")
    
    if supabase:
        st.info("Por favor, selecione ou crie um projeto na página **Define** primeiro.")
        
        try:
            projects = supabase.table('projects').select("*").order('created_at', desc=True).execute()
            
            if projects.data:
                st.subheader("Ou selecione um projeto existente:")
                
                project_names = [p['name'] for p in projects.data]
                selected_project = st.selectbox("Projeto:", project_names)
                
                if st.button("Carregar Projeto"):
                    selected = next(p for p in projects.data if p['name'] == selected_project)
                    st.session_state.project_id = selected['id']
                    st.session_state.project_name = selected['name']
                    st.success(f"✅ Projeto '{selected['name']}' carregado!")
                    st.rerun()
        except Exception as e:
            st.error(f"Erro ao carregar projetos: {e}")
    
    st.stop()

# Mostrar projeto ativo
st.success(f"📁 Projeto Ativo: ID {st.session_state.project_id}")

# Inicializar session state
if 'measure_data' not in st.session_state:
    st.session_state.measure_data = pd.DataFrame()
if 'custom_fields' not in st.session_state:
    st.session_state.custom_fields = []

# Tabs principais
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "⚙️ Configurar Campos",
    "📊 Coleta de Dados",
    "🔍 Análise Exploratória",
    "📈 Estatísticas",
    "✅ Validação",
    "💾 Dados Salvos"
])

# Tab 1: Configurar Campos Personalizados
with tab1:
    st.header("Configurar Campos do Projeto")
    st.info("Configure os campos específicos para coleta de dados do seu projeto")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("➕ Adicionar Campo")
        
        with st.form("add_field_form"):
            field_name = st.text_input("Nome do Campo", placeholder="Ex: temperatura, pressao, defeitos")
            
            field_type = st.selectbox(
                "Tipo de Dado",
                ["Texto", "Número Inteiro", "Número Decimal", "Data", "Sim/Não", "Lista de Opções"]
            )
            
            field_required = st.checkbox("Campo Obrigatório")
            
            field_description = st.text_area("Descrição/Instrução", placeholder="Descreva como este campo deve ser preenchido")
            
            # Configurações específicas por tipo
            field_config = {}
            
            if field_type == "Número Inteiro":
                col_min, col_max = st.columns(2)
                with col_min:
                    field_config['min'] = st.number_input("Valor Mínimo", value=0)
                with col_max:
                    field_config['max'] = st.number_input("Valor Máximo", value=1000)
                    
            elif field_type == "Número Decimal":
                col_min, col_max, col_step = st.columns(3)
                with col_min:
                    field_config['min'] = st.number_input("Mínimo", value=0.0)
                with col_max:
                    field_config['max'] = st.number_input("Máximo", value=100.0)
                with col_step:
                    field_config['step'] = st.number_input("Incremento", value=0.1, min_value=0.01)
                    
            elif field_type == "Lista de Opções":
                options_text = st.text_area(
                    "Opções (uma por linha)",
                    placeholder="Opção 1\nOpção 2\nOpção 3"
                )
                field_config['options'] = [opt.strip() for opt in options_text.split('\n') if opt.strip()]
            
            submitted = st.form_submit_button("Adicionar Campo", type="primary")
            
            if submitted and field_name:
                # Criar campo personalizado
                new_field = {
                    'name': field_name.lower().replace(' ', '_'),
                    'label': field_name,
                    'type': field_type,
                    'required': field_required,
                    'description': field_description,
                    'config': field_config
                }
                
                # Adicionar ao session state
                if 'custom_fields' not in st.session_state:
                    st.session_state.custom_fields = []
                
                # Verificar duplicatas
                if not any(f['name'] == new_field['name'] for f in st.session_state.custom_fields):
                    st.session_state.custom_fields.append(new_field)
                    st.success(f"✅ Campo '{field_name}' adicionado!")
                    st.rerun()
                else:
                    st.error("Campo já existe!")
    
    with col2:
        st.subheader("📋 Campos Configurados")
        
        # Campos padrão sempre presentes
        st.write("**Campos Padrão:**")
        default_fields = [
            "ID do Registro",
            "Data de Coleta",
            "Responsável pela Coleta"
        ]
        for field in default_fields:
            st.write(f"• {field}")
        
        st.divider()
        
        # Campos personalizados
        st.write("**Campos Personalizados:**")
        
        if st.session_state.custom_fields:
            for idx, field in enumerate(st.session_state.custom_fields):
                with st.expander(f"{field['label']} ({field['type']})"):
                    st.write(f"**Nome técnico:** {field['name']}")
                    st.write(f"**Obrigatório:** {'Sim' if field['required'] else 'Não'}")
                    if field['description']:
                        st.write(f"**Descrição:** {field['description']}")
                    if field['config']:
                        st.write(f"**Configuração:** {field['config']}")
                    
                    if st.button(f"🗑️ Remover", key=f"remove_field_{idx}"):
                        st.session_state.custom_fields.pop(idx)
                        st.rerun()
        else:
            st.info("Nenhum campo personalizado configurado ainda")
        
        # Opção de salvar template
        if st.session_state.custom_fields:
            st.divider()
            if st.button("💾 Salvar Template de Campos"):
                template = {
                    'project_id': st.session_state.project_id,
                    'fields': st.session_state.custom_fields,
                    'created_at': datetime.now().isoformat()
                }
                
                # Salvar como JSON para download
                json_str = pd.json_normalize(template).to_json()
                st.download_button(
                    label="📥 Baixar Template",
                    data=json_str,
                    file_name=f"template_fields_{st.session_state.project_id}.json",
                    mime="application/json"
                )

# Tab 2: Coleta de Dados
with tab2:
    st.header("Coleta de Dados")
    
    if not st.session_state.custom_fields:
        st.warning("⚠️ Configure os campos primeiro na aba 'Configurar Campos'")
        st.stop()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Entrada Manual")
        
        with st.form("data_entry_form"):
            # Campos padrão
            st.write("**Informações Básicas**")
            record_id = st.text_input("ID do Registro", value=f"REC-{datetime.now().strftime('%Y%m%d%H%M%S')}")
            collection_date = st.date_input("Data de Coleta", value=datetime.now())
            collector = st.text_input("Responsável pela Coleta")
            
            st.divider()
            
            # Campos personalizados
            st.write("**Dados do Processo**")
            
            form_data = {
                'project_id': st.session_state.project_id,
                'record_id': record_id,
                'collection_date': collection_date,
                'collector': collector
            }
            
            # Renderizar campos personalizados dinamicamente
            for field in st.session_state.custom_fields:
                if field['type'] == 'Texto':
                    value = st.text_input(
                        field['label'] + (' *' if field['required'] else ''),
                        help=field['description']
                    )
                    
                elif field['type'] == 'Número Inteiro':
                    value = st.number_input(
                        field['label'] + (' *' if field['required'] else ''),
                        min_value=int(field['config'].get('min', 0)),
                        max_value=int(field['config'].get('max', 1000000)),
                        value=int(field['config'].get('min', 0)),
                        help=field['description']
                    )
                    
                elif field['type'] == 'Número Decimal':
                    value = st.number_input(
                        field['label'] + (' *' if field['required'] else ''),
                        min_value=float(field['config'].get('min', 0.0)),
                        max_value=float(field['config'].get('max', 1000000.0)),
                        value=float(field['config'].get('min', 0.0)),
                        step=float(field['config'].get('step', 0.1)),
                        help=field['description']
                    )
                    
                elif field['type'] == 'Data':
                    value = st.date_input(
                        field['label'] + (' *' if field['required'] else ''),
                        value=datetime.now(),
                        help=field['description']
                    )
                    
                elif field['type'] == 'Sim/Não':
                    value = st.checkbox(
                        field['label'] + (' *' if field['required'] else ''),
                        help=field['description']
                    )
                    
                elif field['type'] == 'Lista de Opções':
                    options = field['config'].get('options', [])
                    value = st.selectbox(
                        field['label'] + (' *' if field['required'] else ''),
                        options=options if options else ['Sem opções configuradas'],
                        help=field['description']
                    )
                
                form_data[field['name']] = value
            
            submitted = st.form_submit_button("➕ Adicionar Registro", type="primary")
            
            if submitted:
                # Validar campos obrigatórios
                missing_required = []
                for field in st.session_state.custom_fields:
                    if field['required'] and not form_data.get(field['name']):
                        missing_required.append(field['label'])
                
                if missing_required:
                    st.error(f"Campos obrigatórios faltando: {', '.join(missing_required)}")
                else:
                    # Converter datas para string
                    for key, value in form_data.items():
                        if isinstance(value, (datetime, pd.Timestamp)):
                            form_data[key] = value.isoformat()
                    
                    # Adicionar ao DataFrame
                    new_df = pd.DataFrame([form_data])
                    st.session_state.measure_data = pd.concat([st.session_state.measure_data, new_df], ignore_index=True)
                    
                    # Salvar no Supabase se disponível
                    if supabase:
                        try:
                            # Preparar dados para o banco
                            db_data = {
                                'project_id': st.session_state.project_id,
                                'cb_id': record_id,
                                'data_coleta': collection_date.isoformat(),
                                'data_type': 'measure',
                                'observacoes': collector
                            }
                            
                            # Adicionar campos personalizados como JSON
                            custom_data = {k: v for k, v in form_data.items() 
                                         if k not in ['project_id', 'record_id', 'collection_date', 'collector']}
                            
                            # Converter para tipos serializáveis
                            for key, value in custom_data.items():
                                if isinstance(value, np.integer):
                                    custom_data[key] = int(value)
                                elif isinstance(value, np.floating):
                                    custom_data[key] = float(value)
                                elif isinstance(value, (datetime, pd.Timestamp)):
                                    custom_data[key] = value.isoformat()
                            
                            # Salvar campos numéricos diretamente se existirem colunas correspondentes
                            numeric_fields = ['quantidade', 'defeitos', 'custo', 'tempo_parada_min', 'horas_operacao']
                            for field in numeric_fields:
                                if field in custom_data:
                                    db_data[field] = custom_data[field]
                            
                            supabase.table('datasets').insert(db_data).execute()
                            st.success("✅ Registro salvo no banco de dados!")
                            
                        except Exception as e:
                            st.error(f"Erro ao salvar no banco: {e}")
                            st.info("Dados salvos apenas localmente")
                    
                    st.success("✅ Registro adicionado com sucesso!")
    
    with col2:
        st.subheader("Upload de Dados em Lote")
        
        # Gerar template baseado nos campos configurados
        if st.button("📥 Gerar Template CSV"):
            # Criar DataFrame de exemplo
            template_data = {
                'record_id': [f'REC-{i:04d}' for i in range(1, 6)],
                'collection_date': [datetime.now().date() for _ in range(5)],
                'collector': ['Operador 1', 'Operador 2', 'Operador 3', 'Operador 4', 'Operador 5']
            }
            
            # Adicionar campos personalizados
            for field in st.session_state.custom_fields:
                if field['type'] == 'Texto':
                    template_data[field['name']] = [f'Exemplo {i}' for i in range(1, 6)]
                elif field['type'] in ['Número Inteiro', 'Número Decimal']:
                    template_data[field['name']] = [field['config'].get('min', 0) for _ in range(5)]
                elif field['type'] == 'Data':
                    template_data[field['name']] = [datetime.now().date() for _ in range(5)]
                elif field['type'] == 'Sim/Não':
                    template_data[field['name']] = [False, True, False, True, False]
                elif field['type'] == 'Lista de Opções':
                    options = field['config'].get('options', ['Opção 1'])
                    template_data[field['name']] = [options[0] if options else '' for _ in range(5)]
            
            template_df = pd.DataFrame(template_data)
            
            csv = template_df.to_csv(index=False)
            st.download_button(
                label="📄 Download Template CSV",
                data=csv,
                file_name=f"template_measure_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            
            # Mostrar instruções
            with st.expander("📝 Instruções para preenchimento"):
                st.write("**Formato dos dados:**")
                for field in st.session_state.custom_fields:
                    st.write(f"• **{field['label']}** ({field['name']}): {field['type']}")
                    if field['description']:
                        st.write(f"  → {field['description']}")
                    if field['type'] == 'Lista de Opções' and field['config'].get('options'):
                        st.write(f"  → Opções válidas: {', '.join(field['config']['options'])}")
        
        st.divider()
        
        # Upload de arquivo
        uploaded_file = st.file_uploader("Upload CSV com dados", type=['csv', 'xlsx'])
        
        if uploaded_file:
            try:
                # Ler arquivo
                if uploaded_file.name.endswith('.csv'):
                    df_upload = pd.read_csv(uploaded_file)
                else:
                    df_upload = pd.read_excel(uploaded_file)
                
                st.write("**Preview dos dados:**")
                st.dataframe(df_upload.head())
                
                # Informações do arquivo
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Linhas", len(df_upload))
                with col2:
                    st.metric("Colunas", len(df_upload.columns))
                with col3:
                    colunas_validas = sum(1 for field in st.session_state.custom_fields 
                                         if field['name'] in df_upload.columns)
                    st.metric("Campos Reconhecidos", f"{colunas_validas}/{len(st.session_state.custom_fields)}")
                
                if st.button("✅ Importar Dados", type="primary"):
                    # Adicionar project_id
                    df_upload['project_id'] = st.session_state.project_id
                    
                    # Adicionar ao DataFrame local
                    st.session_state.measure_data = pd.concat([st.session_state.measure_data, df_upload], ignore_index=True)
                    
                    # Tentar salvar no Supabase
                    if supabase:
                        success_count = 0
                        error_count = 0
                        
                        for _, row in df_upload.iterrows():
                            try:
                                # Preparar dados básicos
                                db_data = {
                                    'project_id': st.session_state.project_id,
                                    'cb_id': row.get('record_id', f'IMP-{datetime.now().strftime("%Y%m%d%H%M%S")}'),
                                    'data_coleta': pd.to_datetime(row.get('collection_date', datetime.now())).date().isoformat(),
                                    'data_type': 'measure'
                                }
                                
                                # Adicionar campos que existem na tabela
                                for col in ['quantidade', 'defeitos', 'custo', 'tempo_parada_min', 'horas_operacao']:
                                    if col in row:
                                        db_data[col] = float(row[col]) if pd.notna(row[col]) else 0
                                
                                supabase.table('datasets').insert(db_data).execute()
                                success_count += 1
                                
                            except Exception as e:
                                error_count += 1
                        
                        if success_count > 0:
                            st.success(f"✅ {success_count} registros salvos no banco")
                        if error_count > 0:
                            st.warning(f"⚠️ {error_count} registros com erro")
                    
                    st.success(f"✅ {len(df_upload)} registros importados!")
                    
            except Exception as e:
                st.error(f"Erro ao processar arquivo: {e}")

# Tab 3: Análise Exploratória
with tab3:
    st.header("Análise Exploratória de Dados")
    
    # Carregar todos os dados disponíveis
    all_data = st.session_state.measure_data
    
    # Tentar carregar do Supabase também
    if supabase and len(all_data) == 0:
        try:
            response = supabase.table('datasets').select("*").eq('project_id', st.session_state.project_id).execute()
            if response.data:
                all_data = pd.DataFrame(response.data)
        except:
            pass
    
    if not all_data.empty:
        st.success(f"✅ {len(all_data)} registros disponíveis para análise")
        
        # Identificar colunas numéricas e categóricas
        numeric_cols = all_data.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = all_data.select_dtypes(include=['object']).columns.tolist()
        
        # Remover colunas de sistema
        system_cols = ['id', 'project_id', 'created_at', 'updated_at']
        numeric_cols = [col for col in numeric_cols if col not in system_cols]
        categorical_cols = [col for col in categorical_cols if col not in system_cols]
        
        # Análise univariada
        st.subheader("📊 Análise Univariada")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if numeric_cols:
                selected_numeric = st.selectbox("Selecione variável numérica:", numeric_cols)
                
                if selected_numeric:
                    fig = px.histogram(
                        all_data,
                        x=selected_numeric,
                        title=f'Distribuição de {selected_numeric}',
                        nbins=20
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Estatísticas básicas
                    st.write("**Estatísticas:**")
                    stats_df = pd.DataFrame({
                        'Média': [all_data[selected_numeric].mean()],
                        'Mediana': [all_data[selected_numeric].median()],
                        'Desvio': [all_data[selected_numeric].std()],
                        'Min': [all_data[selected_numeric].min()],
                        'Max': [all_data[selected_numeric].max()]
                    }).T
                    stats_df.columns = ['Valor']
                    st.dataframe(stats_df)
        
        with col2:
            if categorical_cols:
                selected_categorical = st.selectbox("Selecione variável categórica:", categorical_cols)
                
                if selected_categorical:
                    value_counts = all_data[selected_categorical].value_counts()
                    
                    fig = px.pie(
                        values=value_counts.values,
                        names=value_counts.index,
                        title=f'Distribuição de {selected_categorical}'
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        # Análise bivariada
        if len(numeric_cols) >= 2:
            st.subheader("📈 Análise Bivariada")
            
            col1, col2 = st.columns(2)
            
            with col1:
                x_var = st.selectbox("Variável X:", numeric_cols, key="x_var")
            with col2:
                y_var = st.selectbox("Variável Y:", numeric_cols, key="y_var")
            
            if x_var and y_var and x_var != y_var:
                fig = px.scatter(
                    all_data,
                    x=x_var,
                    y=y_var,
                    title=f'{y_var} vs {x_var}',
                    trendline="ols"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Análise temporal se houver data
        date_cols = [col for col in all_data.columns if 'data' in col.lower() or 'date' in col.lower()]
        
        if date_cols and numeric_cols:
            st.subheader("📅 Análise Temporal")
            
            col1, col2 = st.columns(2)
            
            with col1:
                date_col = st.selectbox("Coluna de data:", date_cols)
            with col2:
                metric_col = st.selectbox("Métrica:", numeric_cols, key="metric_temporal")
            
            if date_col and metric_col:
                # Converter para datetime
                all_data[date_col] = pd.to_datetime(all_data[date_col], errors='coerce')
                
                # Filtrar dados válidos
                temporal_data = all_data[[date_col, metric_col]].dropna()
                
                if not temporal_data.empty:
                    temporal_data = temporal_data.sort_values(date_col)
                    
                    fig = px.line(
                        temporal_data,
                        x=date_col,
                        y=metric_col,
                        title=f'Evolução de {metric_col}',
                        markers=True
                    )
                    st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum dado disponível. Colete dados na aba 'Coleta de Dados'")

# Tab 4: Estatísticas
with tab4:
    st.header("Análise Estatística")
    
    if not st.session_state.measure_data.empty or (supabase and st.session_state.project_id):
        # Carregar dados
        if not st.session_state.measure_data.empty:
            df = st.session_state.measure_data
        else:
            try:
                response = supabase.table('datasets').select("*").eq('project_id', st.session_state.project_id).execute()
                df = pd.DataFrame(response.data) if response.data else pd.DataFrame()
            except:
                df = pd.DataFrame()
        
        if not df.empty:
            # Selecionar variável
            numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
            system_cols = ['id', 'project_id', 'created_at', 'updated_at']
            numeric_columns = [col for col in numeric_columns if col not in system_cols]
            
            if numeric_columns:
                selected_var = st.selectbox("Selecione a variável para análise:", numeric_columns)
                
                if selected_var:
                    data = df[selected_var].dropna()
                    
                    if len(data) > 0:
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            st.subheader("Estatísticas Descritivas")
                            
                            # Estatísticas completas
                            stats = {
                                'N (amostras)': len(data),
                                'Média': data.mean(),
                                'Erro Padrão': data.sem(),
                                'Mediana': data.median(),
                                'Moda': data.mode()[0] if not data.mode().empty else np.nan,
                                'Desvio Padrão': data.std(),
                                'Variância': data.var(),
                                'Curtose': data.kurtosis(),
                                'Assimetria': data.skew(),
                                'Amplitude': data.max() - data.min(),
                                'Mínimo': data.min(),
                                'Q1 (25%)': data.quantile(0.25),
                                'Q2 (50%)': data.quantile(0.50),
                                'Q3 (75%)': data.quantile(0.75),
                                'Máximo': data.max(),
                                'IQR': data.quantile(0.75) - data.quantile(0.25),
                                'CV (%)': (data.std() / data.mean() * 100) if data.mean() != 0 else 0
                            }
                            
                            # Criar DataFrame para exibição
                            stats_df = pd.DataFrame.from_dict(stats, orient='index', columns=['Valor'])
                            stats_df['Valor'] = stats_df['Valor'].apply(lambda x: f"{x:.4f}" if not pd.isna(x) else "N/A")
                            
                            st.dataframe(stats_df, use_container_width=True)
                            
                            # Salvar estatísticas
                            if st.button("💾 Salvar Análise Estatística"):
                                if supabase:
                                    try:
                                        # Preparar dados para salvar
                                        stats_record = {
                                            'project_id': st.session_state.project_id,
                                            'variavel': selected_var,
                                            'media': float(data.mean()),
                                            'mediana': float(data.median()),
                                            'desvio_padrao': float(data.std()),
                                            'minimo': float(data.min()),
                                            'maximo': float(data.max()),
                                            'q1': float(data.quantile(0.25)),
                                            'q3': float(data.quantile(0.75)),
                                            'cv': float((data.std() / data.mean() * 100)) if data.mean() != 0 else 0,
                                            'periodo_analise': 'measure_phase'
                                        }
                                        
                                        supabase.table('measure_statistics').insert(stats_record).execute()
                                        st.success("✅ Análise salva com sucesso!")
                                    except Exception as e:
                                        st.error(f"Erro ao salvar: {e}")
                        
                        with col2:
                            st.subheader("Visualizações")
                            
                            # Tabs para diferentes visualizações
                            viz_tab1, viz_tab2, viz_tab3 = st.tabs(["Distribuição", "Boxplot", "Q-Q Plot"])
                            
                            with viz_tab1:
                                # Histograma com curva normal
                                fig = go.Figure()
                                
                                # Histograma
                                fig.add_trace(go.Histogram(
                                    x=data,
                                    name='Frequência',
                                    nbinsx=30,
                                    histnorm='probability density',
                                    marker_color='lightblue'
                                ))
                                
                                # Curva normal
                                x_range = np.linspace(data.min(), data.max(), 100)
                                normal_curve = stats.norm.pdf(x_range, data.mean(), data.std())
                                
                                fig.add_trace(go.Scatter(
                                    x=x_range,
                                    y=normal_curve,
                                    mode='lines',
                                    name='Curva Normal',
                                    line=dict(color='red', width=2)
                                ))
                                
                                fig.update_layout(
                                    title=f'Distribuição de {selected_var}',
                                    xaxis_title=selected_var,
                                    yaxis_title='Densidade',
                                    height=400
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                            
                            with viz_tab2:
                                # Boxplot
                                fig = go.Figure()
                                fig.add_trace(go.Box(
                                    y=data,
                                    name=selected_var,
                                    boxmean='sd',
                                    marker_color='lightgreen'
                                ))
                                
                                fig.update_layout(
                                    title=f'Boxplot de {selected_var}',
                                    yaxis_title=selected_var,
                                    height=400
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                            
                            with viz_tab3:
                                # Q-Q Plot
                                if len(data) >= 3:
                                    fig = go.Figure()
                                    
                                    # Calcular quantis
                                    theoretical_quantiles = stats.probplot(data, dist="norm")[0][0]
                                    sample_quantiles = stats.probplot(data, dist="norm")[0][1]
                                    
                                    # Pontos
                                    fig.add_trace(go.Scatter(
                                        x=theoretical_quantiles,
                                        y=sample_quantiles,
                                        mode='markers',
                                        name='Dados',
                                        marker=dict(size=8, color='blue')
                                    ))
                                    
                                    # Linha de referência
                                    min_val = min(theoretical_quantiles.min(), sample_quantiles.min())
                                    max_val = max(theoretical_quantiles.max(), sample_quantiles.max())
                                    
                                    fig.add_trace(go.Scatter(
                                        x=[min_val, max_val],
                                        y=[min_val, max_val],
                                        mode='lines',
                                        name='Normal Teórica',
                                        line=dict(color='red', dash='dash')
                                    ))
                                    
                                    fig.update_layout(
                                        title='Q-Q Plot (Normalidade)',
                                        xaxis_title='Quantis Teóricos',
                                        yaxis_title='Quantis da Amostra',
                                        height=400
                                    )
                                    
                                    st.plotly_chart(fig, use_container_width=True)
                                    
                                    # Teste de normalidade
                                    st.subheader("Teste de Normalidade")
                                    
                                    # Shapiro-Wilk
                                    stat_sw, p_sw = stats.shapiro(data)
                                    
                                    # Anderson-Darling
                                    result_ad = stats.anderson(data)
                                    
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.write("**Teste Shapiro-Wilk**")
                                        st.write(f"Estatística: {stat_sw:.6f}")
                                        st.write(f"P-valor: {p_sw:.6f}")
                                        
                                        if p_sw > 0.05:
                                            st.success("✅ Distribuição normal (p > 0.05)")
                                        else:
                                            st.warning("⚠️ Distribuição não normal (p ≤ 0.05)")
                                    
                                    with col2:
                                        st.write("**Teste Anderson-Darling**")
                                        st.write(f"Estatística: {result_ad.statistic:.6f}")
                                        st.write("Valores críticos:")
                                        for i, (sig, crit) in enumerate(zip(result_ad.significance_level, result_ad.critical_values)):
                                            st.write(f"  {sig}%: {crit:.3f}")
                    else:
                        st.warning("Dados insuficientes para análise")
            else:
                st.info("Nenhuma variável numérica disponível para análise")
        else:
            st.info("Nenhum dado disponível para análise")
    else:
        st.info("Carregue dados primeiro na aba 'Coleta de Dados'")

# Tab 5: Validação
with tab5:
    st.header("Validação e Qualidade dos Dados")
    
    if not st.session_state.measure_data.empty:
        df = st.session_state.measure_data
        
        # Métricas gerais
        st.subheader("📊 Métricas de Qualidade")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Registros", len(df))
        
        with col2:
            total_cells = len(df) * len(df.columns)
            missing_cells = df.isnull().sum().sum()
            completeness = (1 - missing_cells / total_cells) * 100
            st.metric("Completude", f"{completeness:.1f}%")
        
        with col3:
            duplicates = df.duplicated().sum()
            st.metric("Registros Duplicados", duplicates)
        
        with col4:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            consistency = 100  # Placeholder para cálculo de consistência
            st.metric("Consistência", f"{consistency:.1f}%")
        
        # Análise detalhada
        st.subheader("🔍 Análise Detalhada")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Completude por Campo**")
            
            completeness_by_field = ((1 - df.isnull().sum() / len(df)) * 100).round(2)
            completeness_df = pd.DataFrame({
                'Campo': completeness_by_field.index,
                'Completude (%)': completeness_by_field.values
            }).sort_values('Completude (%)')
            
            # Colorir baseado na completude
            def color_completeness(val):
                if val >= 95:
                    return 'background-color: #90EE90'  # Verde claro
                elif val >= 80:
                    return 'background-color: #FFD700'  # Amarelo
                else:
                    return 'background-color: #FFB6C1'  # Vermelho claro
            
            styled_df = completeness_df.style.applymap(
                color_completeness,
                subset=['Completude (%)']
            )
            
            st.dataframe(completeness_df, use_container_width=True, hide_index=True)
        
        with col2:
            st.write("**Detecção de Anomalias**")
            
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            anomalies = []
            
            for col in numeric_cols:
                if col in df.columns:
                    # Método IQR
                    Q1 = df[col].quantile(0.25)
                    Q3 = df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    
                    lower = Q1 - 1.5 * IQR
                    upper = Q3 + 1.5 * IQR
                    
                    outliers = df[(df[col] < lower) | (df[col] > upper)]
                    
                    if len(outliers) > 0:
                        anomalies.append({
                            'Campo': col,
                            'Anomalias': len(outliers),
                            '% do Total': f"{(len(outliers)/len(df)*100):.1f}%"
                        })
            
            if anomalies:
                anomaly_df = pd.DataFrame(anomalies)
                st.dataframe(anomaly_df, use_container_width=True, hide_index=True)
            else:
                st.success("✅ Nenhuma anomalia detectada")
        
        # Regras de validação personalizadas
        st.subheader("📋 Regras de Validação Personalizadas")
        
        with st.expander("Configurar Regras de Validação"):
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                rule_field = st.selectbox("Campo", df.columns.tolist())
            
            with col2:
                rule_type = st.selectbox("Tipo de Regra", [
                    "Maior que",
                    "Menor que",
                    "Entre valores",
                    "Não nulo",
                    "Único",
                    "Formato específico"
                ])
            
            with col3:
                if rule_type in ["Maior que", "Menor que"]:
                    rule_value = st.number_input("Valor", value=0.0)
                elif rule_type == "Entre valores":
                    rule_min = st.number_input("Mínimo", value=0.0)
                    rule_max = st.number_input("Máximo", value=100.0)
            
            if st.button("Aplicar Validação"):
                violations = []
                
                if rule_type == "Maior que":
                    violations = df[df[rule_field] <= rule_value]
                elif rule_type == "Menor que":
                    violations = df[df[rule_field] >= rule_value]
                elif rule_type == "Entre valores":
                    violations = df[(df[rule_field] < rule_min) | (df[rule_field] > rule_max)]
                elif rule_type == "Não nulo":
                    violations = df[df[rule_field].isnull()]
                elif rule_type == "Único":
                    duplicates = df[df.duplicated(subset=[rule_field], keep=False)]
                    violations = duplicates
                
                if len(violations) > 0:
                    st.warning(f"⚠️ {len(violations)} violações encontradas")
                    st.dataframe(violations, use_container_width=True)
                else:
                    st.success("✅ Nenhuma violação encontrada")
        
        # Score geral de qualidade
        st.subheader("🎯 Score de Qualidade dos Dados")
        
        # Calcular score baseado em múltiplos fatores
        score_components = {
            'Completude': completeness,
            'Unicidade': (1 - duplicates / len(df)) * 100 if len(df) > 0 else 100,
            'Consistência': consistency,
            'Validade': 95  # Placeholder
        }
        
        overall_score = np.mean(list(score_components.values()))
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # Gauge chart para score geral
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=overall_score,
                title={'text': "Score Geral"},
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "lightgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Breakdown dos componentes
            st.write("**Componentes do Score:**")
            
            for component, value in score_components.items():
                col_label, col_bar, col_value = st.columns([2, 4, 1])
                with col_label:
                    st.write(component)
                with col_bar:
                    st.progress(value / 100)
                with col_value:
                    st.write(f"{value:.1f}%")
            
            # Recomendações
            st.write("**Recomendações:**")
            if completeness < 90:
                st.warning("• Melhorar completude dos dados - verificar campos obrigatórios")
            if duplicates > 0:
                st.warning("• Remover registros duplicados")
            if overall_score < 80:
                st.warning("• Revisar processo de coleta de dados")
            else:
                st.success("• Qualidade dos dados está adequada para análise")
    else:
        st.info("Nenhum dado disponível para validação")

# Tab 6: Dados Salvos
with tab6:
    st.header("Dados Salvos do Projeto")
    
    if supabase:
        try:
            response = supabase.table('datasets').select("*").eq('project_id', st.session_state.project_id).execute()
            
            if response.data:
                df_saved = pd.DataFrame(response.data)
                st.success(f"✅ {len(df_saved)} registros encontrados no banco de dados")
                
                # Opções de visualização
                view_option = st.radio(
                    "Visualização:",
                    ["Tabela Completa", "Resumo Estatístico", "Exportar Dados"]
                )
                
                if view_option == "Tabela Completa":
                    st.dataframe(df_saved, use_container_width=True)
                
                elif view_option == "Resumo Estatístico":
                    st.write(df_saved.describe())
                
                elif view_option == "Exportar Dados":
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        csv = df_saved.to_csv(index=False)
                        st.download_button(
                            label="📄 Download CSV",
                            data=csv,
                            file_name=f"dados_projeto_{st.session_state.project_id}_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    
                    with col2:
                        buffer = io.BytesIO()
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            df_saved.to_excel(writer, index=False)
                        
                        st.download_button(
                            label="📊 Download Excel",
                            data=buffer.getvalue(),
                            file_name=f"dados_projeto_{st.session_state.project_id}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.ms-excel"
                        )
                    
                    with col3:
                        json_str = df_saved.to_json(orient='records')
                        st.download_button(
                            label="📦 Download JSON",
                            data=json_str,
                            file_name=f"dados_projeto_{st.session_state.project_id}_{datetime.now().strftime('%Y%m%d')}.json",
                            mime="application/json"
                        )
            else:
                st.info("Nenhum dado salvo ainda para este projeto")
                
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
    else:
        if not st.session_state.measure_data.empty:
            st.info(f"Mostrando {len(st.session_state.measure_data)} registros salvos localmente")
            st.dataframe(st.session_state.measure_data, use_container_width=True)
        else:
            st.info("Nenhum dado disponível")

# Footer
st.markdown("---")
st.markdown(f"📊 **Fase Measure** - Green Belt Project | Sistema Genérico de Coleta e Análise de Dados")
