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
        
        # Opção de selecionar projeto existente
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
    else:
        st.info("Configure o Supabase para salvar dados do projeto.")
    
    st.stop()

# Mostrar projeto ativo
st.success(f"📁 Projeto Ativo: ID {st.session_state.project_id}")

# Inicializar session state para dados
if 'measure_data' not in st.session_state:
    st.session_state.measure_data = pd.DataFrame()

# Lista de colunas válidas no banco de dados
VALID_DB_COLUMNS = [
    'project_id', 'cb_id', 'data_coleta', 'turno', 'operador',
    'unidade', 'categoria', 'defeito', 'horas_operacao',
    'tempo_parada_min', 'custo', 'quantidade', 'defeitos',
    'pressao_diesel', 'temperatura_diesel', 'teor_agua',
    'contaminacao_biologica', 'caminhao_id', 'tanque_id',
    'data_type', 'observacoes', 'viscosidade'
]

# Tabs principais
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Coleta de Dados",
    "🔍 Análise Exploratória",
    "📈 Estatísticas",
    "✅ Validação",
    "💾 Dados Salvos"
])

# Tab 1: Coleta de Dados
with tab1:
    st.header("Coleta de Dados")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Entrada Manual")
        
        with st.form("data_entry_form"):
            st.write("**Identificação**")
            cb_id = st.text_input("ID do Registro", value=f"CB-{datetime.now().strftime('%Y%m%d%H%M')}")
            data_coleta = st.date_input("Data da Coleta", value=datetime.now())
            turno = st.selectbox("Turno", ["Manhã", "Tarde", "Noite"])
            operador = st.text_input("Operador", value="")
            
            st.write("**Dados do Processo**")
            caminhao_id = st.text_input("ID do Caminhão", value="CAM001")
            tanque_id = st.text_input("ID do Tanque", value="TQ01")
            unidade = st.selectbox("Unidade", ["Unidade A", "Unidade B", "Unidade C"])
            categoria = st.selectbox("Categoria", ["Material", "Método", "Mão de Obra", "Máquina", "Medida", "Meio Ambiente"])
            
            st.write("**Medições de Diesel**")
            pressao_diesel = st.number_input("Pressão Diesel (bar)", min_value=0.0, max_value=10.0, value=4.5, step=0.1)
            temperatura_diesel = st.number_input("Temperatura (°C)", min_value=0.0, max_value=100.0, value=25.0, step=0.5)
            teor_agua = st.number_input("Teor de Água (%)", min_value=0.0, max_value=100.0, value=0.5, step=0.1)
            viscosidade = st.number_input("Viscosidade (cSt)", min_value=0.0, max_value=100.0, value=3.5, step=0.1)
            contaminacao_biologica = st.checkbox("Contaminação Biológica Detectada")
            
            st.write("**Operação**")
            horas_operacao = st.number_input("Horas de Operação", min_value=0.0, value=8.0, step=0.5)
            tempo_parada_min = st.number_input("Tempo de Parada (min)", min_value=0.0, value=0.0, step=1.0)
            
            st.write("**Defeitos e Custos**")
            defeito = st.selectbox("Tipo de Defeito", [
                "Sem defeito",
                "Combustível com alto teor de água",
                "Filtro saturado",
                "Processo inadequado",
                "Falta de drenagem",
                "Contaminação biológica",
                "Baixa pressão de alimentação",
                "Viscosidade fora do padrão"
            ])
            quantidade = st.number_input("Quantidade Produzida", min_value=0, value=100)
            defeitos = st.number_input("Quantidade de Defeitos", min_value=0, value=0)
            custo = st.number_input("Custo da Ocorrência (R$)", min_value=0.0, value=0.0, step=10.0)
            
            observacoes = st.text_area("Observações", value="")
            
            submitted = st.form_submit_button("➕ Adicionar Registro", type="primary")
            
            if submitted:
                # Criar registro
                novo_registro = {
                    'project_id': st.session_state.project_id,
                    'cb_id': cb_id,
                    'data_coleta': data_coleta.isoformat(),
                    'turno': turno,
                    'operador': operador if operador else None,
                    'caminhao_id': caminhao_id,
                    'tanque_id': tanque_id,
                    'unidade': unidade,
                    'categoria': categoria,
                    'pressao_diesel': float(pressao_diesel),
                    'temperatura_diesel': float(temperatura_diesel),
                    'teor_agua': float(teor_agua),
                    'viscosidade': float(viscosidade),
                    'contaminacao_biologica': contaminacao_biologica,
                    'horas_operacao': float(horas_operacao),
                    'tempo_parada_min': float(tempo_parada_min),
                    'defeito': defeito,
                    'quantidade': int(quantidade),
                    'defeitos': int(defeitos),
                    'custo': float(custo),
                    'observacoes': observacoes if observacoes else None,
                    'data_type': 'baseline'
                }
                
                # Salvar no Supabase
                if supabase:
                    try:
                        # Filtrar apenas colunas válidas
                        clean_record = {k: v for k, v in novo_registro.items() if k in VALID_DB_COLUMNS and v is not None}
                        response = supabase.table('datasets').insert(clean_record).execute()
                        st.success("✅ Registro salvo no banco de dados!")
                        
                        # Adicionar ao DataFrame local
                        new_df = pd.DataFrame([novo_registro])
                        st.session_state.measure_data = pd.concat([st.session_state.measure_data, new_df], ignore_index=True)
                        
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")
                else:
                    # Adicionar apenas ao DataFrame local
                    new_df = pd.DataFrame([novo_registro])
                    st.session_state.measure_data = pd.concat([st.session_state.measure_data, new_df], ignore_index=True)
                    st.success("✅ Registro adicionado localmente!")
    
    with col2:
        st.subheader("Upload de Dados em Lote")
        
        # Template para download
        if st.button("📥 Baixar Template CSV"):
            template = pd.DataFrame({
                'caminhao_id': ['CAM001', 'CAM002', 'CAM003', 'CAM004', 'CAM005'],
                'data_coleta': [
                    (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') 
                    for i in range(5)
                ],
                'turno': ['Manhã', 'Tarde', 'Noite', 'Manhã', 'Tarde'],
                'operador': ['João Silva', 'Maria Santos', 'Pedro Costa', 'Ana Lima', 'Carlos Souza'],
                'unidade': ['Unidade A', 'Unidade B', 'Unidade C', 'Unidade A', 'Unidade B'],
                'categoria': ['Material', 'Método', 'Mão de Obra', 'Máquina', 'Material'],
                'defeito': [
                    'Sem defeito', 
                    'Filtro saturado', 
                    'Combustível com alto teor de água',
                    'Baixa pressão de alimentação',
                    'Contaminação biológica'
                ],
                'pressao_diesel': [4.5, 4.2, 3.8, 3.4, 4.1],
                'temperatura_diesel': [25.0, 26.0, 27.0, 25.5, 26.5],
                'teor_agua': [0.5, 0.8, 1.2, 0.6, 1.5],
                'viscosidade': [3.5, 3.4, 3.6, 3.3, 3.7],
                'contaminacao_biologica': [False, False, True, False, True],
                'horas_operacao': [8.0, 7.5, 8.0, 6.0, 8.0],
                'tempo_parada_min': [0, 30, 45, 60, 15],
                'quantidade': [100, 95, 90, 80, 98],
                'defeitos': [0, 2, 3, 5, 1],
                'custo': [0.0, 150.0, 250.0, 380.0, 75.0],
                'tanque_id': ['TQ01', 'TQ01', 'TQ02', 'TQ02', 'TQ01'],
                'observacoes': [
                    'Operação normal', 
                    'Filtro substituído', 
                    'Drenagem realizada',
                    'Manutenção corretiva',
                    'Análise de qualidade solicitada'
                ]
            })
            
            csv = template.to_csv(index=False)
            st.download_button(
                label="Download Template CSV",
                data=csv,
                file_name=f"template_measure_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            
            st.info("""
            📝 **Instruções para o template:**
            - Data no formato: YYYY-MM-DD
            - Pressão em bar (ex: 4.5)
            - Temperatura em °C
            - Teor de água em percentual (ex: 0.5 para 0.5%)
            - Viscosidade em cSt
            - Contaminação biológica: True ou False
            - Custos em R$
            """)
        
        # Upload de arquivo
        st.divider()
        uploaded_file = st.file_uploader("Upload CSV com dados", type=['csv'])
        
        if uploaded_file:
            try:
                df_upload = pd.read_csv(uploaded_file)
                
                # Mostrar preview
                st.write("**Preview dos dados carregados:**")
                st.dataframe(df_upload.head(10))
                
                # Informações do arquivo
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Linhas", len(df_upload))
                with col2:
                    st.metric("Colunas", len(df_upload.columns))
                with col3:
                    st.metric("Tamanho", f"{uploaded_file.size / 1024:.1f} KB")
                
                # Validação de colunas
                required_columns = ['caminhao_id', 'data_coleta']
                missing_columns = [col for col in required_columns if col not in df_upload.columns]
                
                if missing_columns:
                    st.error(f"❌ Colunas obrigatórias faltando: {', '.join(missing_columns)}")
                else:
                    st.success("✅ Arquivo válido para importação")
                    
                    if st.button("✅ Confirmar e Importar", type="primary"):
                        with st.spinner("Importando dados..."):
                            # Adicionar project_id e data_type
                            df_upload['project_id'] = st.session_state.project_id
                            df_upload['data_type'] = 'baseline'
                            
                            # Converter tipos de dados
                            if 'data_coleta' in df_upload.columns:
                                df_upload['data_coleta'] = pd.to_datetime(df_upload['data_coleta'])
                            
                            # Converter booleanos
                            if 'contaminacao_biologica' in df_upload.columns:
                                df_upload['contaminacao_biologica'] = df_upload['contaminacao_biologica'].astype(bool)
                            
                            # Converter numéricos
                            numeric_columns = [
                                'pressao_diesel', 'temperatura_diesel', 'teor_agua', 'viscosidade',
                                'horas_operacao', 'tempo_parada_min', 'quantidade', 'defeitos', 'custo'
                            ]
                            
                            for col in numeric_columns:
                                if col in df_upload.columns:
                                    df_upload[col] = pd.to_numeric(df_upload[col], errors='coerce')
                            
                            if supabase:
                                # Salvar no Supabase
                                success_count = 0
                                error_count = 0
                                errors = []
                                
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                
                                records = df_upload.to_dict('records')
                                total_records = len(records)
                                
                                for i, record in enumerate(records):
                                    try:
                                        # Limpar registro - manter apenas colunas válidas
                                        clean_record = {}
                                        for key, value in record.items():
                                            if key in VALID_DB_COLUMNS:
                                                # Tratar valores NaN
                                                if pd.isna(value):
                                                    clean_record[key] = None
                                                elif key == 'data_coleta':
                                                    # Converter data
                                                    clean_record[key] = pd.to_datetime(value).date().isoformat()
                                                else:
                                                    clean_record[key] = value
                                        
                                        # Inserir no banco
                                        supabase.table('datasets').insert(clean_record).execute()
                                        success_count += 1
                                        
                                    except Exception as e:
                                        error_count += 1
                                        errors.append(f"Linha {i+2}: {str(e)[:100]}")
                                    
                                    # Atualizar progresso
                                    progress = (i + 1) / total_records
                                    progress_bar.progress(progress)
                                    status_text.text(f"Processando: {i+1}/{total_records}")
                                
                                progress_bar.empty()
                                status_text.empty()
                                
                                # Mostrar resultado
                                if success_count > 0:
                                    st.success(f"✅ {success_count} registros importados com sucesso!")
                                
                                if error_count > 0:
                                    st.warning(f"⚠️ {error_count} registros com erro")
                                    with st.expander("Ver detalhes dos erros"):
                                        for error in errors[:20]:  # Mostrar até 20 erros
                                            st.text(error)
                            else:
                                # Salvar apenas localmente
                                st.session_state.measure_data = pd.concat(
                                    [st.session_state.measure_data, df_upload], 
                                    ignore_index=True
                                )
                                st.success(f"✅ {len(df_upload)} registros importados localmente!")
                
            except Exception as e:
                st.error(f"Erro ao processar arquivo: {e}")

# Tab 2: Análise Exploratória
with tab2:
    st.header("Análise Exploratória de Dados")
    
    # Carregar dados do projeto
    if supabase:
        try:
            with st.spinner("Carregando dados..."):
                data_response = supabase.table('datasets').select("*").eq('project_id', st.session_state.project_id).execute()
                
                if data_response.data:
                    df = pd.DataFrame(data_response.data)
                    
                    # Converter tipos
                    if 'data_coleta' in df.columns:
                        df['data_coleta'] = pd.to_datetime(df['data_coleta'])
                    
                    numeric_cols = [
                        'pressao_diesel', 'temperatura_diesel', 'teor_agua', 'viscosidade',
                        'horas_operacao', 'tempo_parada_min', 'quantidade', 'defeitos', 'custo'
                    ]
                    
                    for col in numeric_cols:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    st.session_state.measure_data = df
                    
                    # Métricas resumidas
                    st.success(f"✅ {len(df)} registros carregados")
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    with col1:
                        st.metric("Total de Registros", len(df))
                    
                    with col2:
                        if 'defeitos' in df.columns:
                            total_defeitos = df['defeitos'].sum()
                            st.metric("Total de Defeitos", int(total_defeitos))
                    
                    with col3:
                        if 'pressao_diesel' in df.columns:
                            baixa_pressao = len(df[df['pressao_diesel'] < 3.5])
                            st.metric("Baixa Pressão", baixa_pressao)
                    
                    with col4:
                        if 'contaminacao_biologica' in df.columns:
                            contaminados = df['contaminacao_biologica'].sum()
                            st.metric("Contaminação Bio", int(contaminados))
                    
                    with col5:
                        if 'custo' in df.columns:
                            custo_total = df['custo'].sum()
                            st.metric("Custo Total", f"R$ {custo_total:,.0f}")
                    
                    # Gráficos
                    st.subheader("Visualizações")
                    
                    # Linha 1 de gráficos
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if 'pressao_diesel' in df.columns:
                            fig = px.histogram(
                                df, 
                                x='pressao_diesel',
                                title='Distribuição de Pressão de Diesel',
                                nbins=20,
                                labels={'pressao_diesel': 'Pressão (bar)', 'count': 'Frequência'}
                            )
                            fig.add_vline(x=3.5, line_dash="dash", line_color="red", annotation_text="Limite Mínimo")
                            fig.update_layout(height=400)
                            st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        if 'defeito' in df.columns:
                            defeitos_count = df[df['defeito'] != 'Sem defeito']['defeito'].value_counts()
                            if not defeitos_count.empty:
                                fig = px.pie(
                                    values=defeitos_count.values,
                                    names=defeitos_count.index,
                                    title='Distribuição de Defeitos',
                                    hole=0.4
                                )
                                fig.update_layout(height=400)
                                st.plotly_chart(fig, use_container_width=True)
                    
                    # Linha 2 de gráficos
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if 'teor_agua' in df.columns:
                            fig = px.box(
                                df,
                                y='teor_agua',
                                x='unidade' if 'unidade' in df.columns else None,
                                title='Teor de Água por Unidade',
                                labels={'teor_agua': 'Teor de Água (%)', 'unidade': 'Unidade'}
                            )
                            fig.add_hline(y=1.0, line_dash="dash", line_color="orange", annotation_text="Limite")
                            fig.update_layout(height=400)
                            st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        if 'tempo_parada_min' in df.columns and 'turno' in df.columns:
                            paradas_turno = df.groupby('turno')['tempo_parada_min'].sum().reset_index()
                            fig = px.bar(
                                paradas_turno,
                                x='turno',
                                y='tempo_parada_min',
                                title='Tempo de Parada por Turno',
                                labels={'tempo_parada_min': 'Tempo Total (min)', 'turno': 'Turno'}
                            )
                            fig.update_layout(height=400)
                            st.plotly_chart(fig, use_container_width=True)
                    
                    # Série temporal
                    if 'data_coleta' in df.columns and 'pressao_diesel' in df.columns:
                        df_sorted = df.sort_values('data_coleta')
                        
                        fig = go.Figure()
                        
                        # Adicionar linha de pressão
                        fig.add_trace(go.Scatter(
                            x=df_sorted['data_coleta'],
                            y=df_sorted['pressao_diesel'],
                            mode='lines+markers',
                            name='Pressão Diesel',
                            line=dict(color='blue', width=2),
                            marker=dict(size=6)
                        ))
                        
                        # Adicionar linha de limite
                        fig.add_hline(y=3.5, line_dash="dash", line_color="red", annotation_text="Limite Mínimo")
                        
                        # Destacar pontos abaixo do limite
                        baixa_pressao_df = df_sorted[df_sorted['pressao_diesel'] < 3.5]
                        if not baixa_pressao_df.empty:
                            fig.add_trace(go.Scatter(
                                x=baixa_pressao_df['data_coleta'],
                                y=baixa_pressao_df['pressao_diesel'],
                                mode='markers',
                                name='Baixa Pressão',
                                marker=dict(color='red', size=10, symbol='x')
                            ))
                        
                        fig.update_layout(
                            title='Evolução da Pressão de Diesel ao Longo do Tempo',
                            xaxis_title='Data',
                            yaxis_title='Pressão (bar)',
                            height=400,
                            hovermode='x unified'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                else:
                    st.info("Nenhum dado encontrado para este projeto. Adicione dados na aba 'Coleta de Dados'.")
                    
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
    else:
        if not st.session_state.measure_data.empty:
            df = st.session_state.measure_data
            st.info(f"Mostrando {len(df)} registros salvos localmente")

# Tab 3: Estatísticas
with tab3:
    st.header("Análise Estatística Detalhada")
    
    if not st.session_state.measure_data.empty:
        df = st.session_state.measure_data
        
        # Selecionar variável
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if numeric_columns:
            col1, col2 = st.columns([1, 3])
            
            with col1:
                selected_var = st.selectbox(
                    "Selecione a variável:",
                    numeric_columns,
                    index=numeric_columns.index('pressao_diesel') if 'pressao_diesel' in numeric_columns else 0
                )
                
                if selected_var:
                    data = df[selected_var].dropna()
                    
                    st.subheader("Estatísticas Descritivas")
                    
                    # Calcular estatísticas
                    stats_dict = {
                        'N (amostras)': len(data),
                        'Média': data.mean(),
                        'Mediana': data.median(),
                        'Moda': data.mode()[0] if not data.mode().empty else np.nan,
                        'Desvio Padrão': data.std(),
                        'Variância': data.var(),
                        'Mínimo': data.min(),
                        'Q1 (25%)': data.quantile(0.25),
                        'Q3 (75%)': data.quantile(0.75),
                        'Máximo': data.max(),
                        'Amplitude': data.max() - data.min(),
                        'IQR': data.quantile(0.75) - data.quantile(0.25),
                        'CV (%)': (data.std() / data.mean() * 100) if data.mean() != 0 else 0,
                        'Assimetria': data.skew(),
                        'Curtose': data.kurtosis()
                    }
                    
                    # Mostrar estatísticas
                    for stat, value in stats_dict.items():
                        if stat == 'N (amostras)':
                            st.metric(stat, f"{int(value)}")
                        else:
                            st.metric(stat, f"{value:.3f}")
                    
                    # Botão para salvar
                    if st.button("💾 Salvar Estatísticas no Banco"):
                        if supabase:
                            try:
                                # Teste de normalidade
                                if len(data) >= 3:
                                    shapiro_stat, shapiro_p = stats.shapiro(data)
                                else:
                                    shapiro_stat, shapiro_p = None, None
                                
                                stats_record = {
                                    'project_id': st.session_state.project_id,
                                    'variavel': selected_var,
                                    'media': float(stats_dict['Média']),
                                    'mediana': float(stats_dict['Mediana']),
                                    'desvio_padrao': float(stats_dict['Desvio Padrão']),
                                    'minimo': float(stats_dict['Mínimo']),
                                    'q1': float(stats_dict['Q1 (25%)']),
                                    'q3': float(stats_dict['Q3 (75%)']),
                                    'maximo': float(stats_dict['Máximo']),
                                    'cv': float(stats_dict['CV (%)']),
                                    'shapiro_w': float(shapiro_stat) if shapiro_stat else None,
                                    'shapiro_p': float(shapiro_p) if shapiro_p else None,
                                    'periodo_analise': 'baseline'
                                }
                                
                                # Remover None values
                                stats_record = {k: v for k, v in stats_record.items() if v is not None}
                                
                                supabase.table('measure_statistics').insert(stats_record).execute()
                                st.success("✅ Estatísticas salvas com sucesso!")
                            except Exception as e:
                                st.error(f"Erro ao salvar: {e}")
            
            with col2:
                if selected_var:
                    data = df[selected_var].dropna()
                    
                    # Criar subplots
                    st.subheader("Visualizações Estatísticas")
                    
                    # Histograma com curva normal
                    col_hist, col_box = st.columns(2)
                    
                    with col_hist:
                        fig = go.Figure()
                        
                        # Histograma
                        fig.add_trace(go.Histogram(
                            x=data,
                            name='Frequência',
                            nbinsx=20,
                            histnorm='probability density'
                        ))
                        
                        # Curva normal teórica
                        x_range = np.linspace(data.min(), data.max(), 100)
                        normal_curve = stats.norm.pdf(x_range, data.mean(), data.std())
                        
                        fig.add_trace(go.Scatter(
                            x=x_range,
                            y=normal_curve,
                            mode='lines',
                            name='Normal Teórica',
                            line=dict(color='red', width=2)
                        ))
                        
                        fig.update_layout(
                            title=f'Histograma - {selected_var}',
                            xaxis_title=selected_var,
                            yaxis_title='Densidade',
                            height=400
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col_box:
                        # Boxplot
                        fig = go.Figure()
                        fig.add_trace(go.Box(
                            y=data,
                            name=selected_var,
                            boxmean='sd'
                        ))
                        
                        fig.update_layout(
                            title=f'Boxplot - {selected_var}',
                            yaxis_title=selected_var,
                            height=400
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Teste de Normalidade
                    st.subheader("Testes de Normalidade")
                    
                    if len(data) >= 3:
                        col_test1, col_test2 = st.columns(2)
                        
                        with col_test1:
                            # Shapiro-Wilk
                            stat, p_value = stats.shapiro(data)
                            
                            st.write("**Teste Shapiro-Wilk**")
                            st.write(f"W-statistic: {stat:.6f}")
                            st.write(f"P-valor: {p_value:.6f}")
                            
                            if p_value > 0.05:
                                st.success("✅ Distribuição normal (p > 0.05)")
                            else:
                                st.warning("⚠️ Distribuição NÃO normal (p ≤ 0.05)")
                        
                        with col_test2:
                            # Q-Q Plot
                            fig = go.Figure()
                            
                            # Calcular quantis
                            theoretical_quantiles = stats.probplot(data, dist="norm")[0][0]
                            sample_quantiles = stats.probplot(data, dist="norm")[0][1]
                            
                            # Pontos do Q-Q plot
                            fig.add_trace(go.Scatter(
                                x=theoretical_quantiles,
                                y=sample_quantiles,
                                mode='markers',
                                name='Dados',
                                marker=dict(size=8)
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
                                title='Q-Q Plot',
                                xaxis_title='Quantis Teóricos',
                                yaxis_title='Quantis da Amostra',
                                height=400
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Dados insuficientes para teste de normalidade (mínimo 3 amostras)")
        else:
            st.warning("Nenhuma coluna numérica disponível para análise")
    else:
        st.info("Carregue dados primeiro na aba 'Coleta de Dados'")

# Tab 4: Validação
with tab4:
    st.header("Validação e Qualidade dos Dados")
    
    if not st.session_state.measure_data.empty:
        df = st.session_state.measure_data
        
        # Análise geral de qualidade
        st.subheader("📊 Análise Geral de Qualidade")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_rows = len(df)
            st.metric("Total de Registros", total_rows)
        
        with col2:
            total_missing = df.isnull().sum().sum()
            missing_pct = (total_missing / (total_rows * len(df.columns)) * 100)
            st.metric("Dados Faltantes", f"{missing_pct:.1f}%")
        
        with col3:
            duplicates = df.duplicated().sum()
            st.metric("Linhas Duplicadas", duplicates)
        
        with col4:
            completeness = 100 - missing_pct
            st.metric("Completude", f"{completeness:.1f}%")
        
        # Detalhamento de valores faltantes
        st.subheader("🔍 Análise Detalhada")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Valores Faltantes por Coluna**")
            
            missing = df.isnull().sum()
            missing_pct = (missing / len(df) * 100).round(2)
            
            missing_df = pd.DataFrame({
                'Coluna': missing.index,
                'Faltantes': missing.values,
                'Percentual': [f"{pct}%" for pct in missing_pct.values]
            })
            
            missing_df = missing_df[missing_df['Faltantes'] > 0].sort_values('Faltantes', ascending=False)
            
            if not missing_df.empty:
                st.dataframe(missing_df, use_container_width=True, hide_index=True)
            else:
                st.success("✅ Nenhum valor faltante!")
        
        with col2:
            st.write("**Outliers Detectados (IQR)**")
            
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            outliers_summary = []
            
            for col in numeric_cols:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                
                lower = Q1 - 1.5 * IQR
                upper = Q3 + 1.5 * IQR
                
                outliers = df[(df[col] < lower) | (df[col] > upper)]
                
                if len(outliers) > 0:
                    outliers_summary.append({
                        'Variável': col,
                        'Outliers': len(outliers),
                        'Percentual': f"{len(outliers)/len(df)*100:.1f}%",
                        'Limites': f"[{lower:.2f}, {upper:.2f}]"
                    })
            
            if outliers_summary:
                outliers_df = pd.DataFrame(outliers_summary)
                st.dataframe(outliers_df, use_container_width=True, hide_index=True)
            else:
                st.success("✅ Nenhum outlier detectado!")
        
        # Validações específicas do negócio
        st.subheader("⚠️ Validações Específicas do Processo")
        
        validations = []
        
        # Validação 1: Pressão baixa
        if 'pressao_diesel' in df.columns:
            baixa_pressao = df[df['pressao_diesel'] < 3.5]
            if len(baixa_pressao) > 0:
                validations.append({
                    '❌ Regra': 'Pressão < 3.5 bar',
                    'Violações': len(baixa_pressao),
                    '% Total': f"{len(baixa_pressao)/len(df)*100:.1f}%",
                    'Severidade': '🔴 Alta',
                    'Ação Recomendada': 'Verificar sistema de alimentação urgente'
                })
        
        # Validação 2: Alto teor de água
        if 'teor_agua' in df.columns:
            alto_teor = df[df['teor_agua'] > 1.0]
            if len(alto_teor) > 0:
                validations.append({
                    '❌ Regra': 'Teor de água > 1%',
                    'Violações': len(alto_teor),
                    '% Total': f"{len(alto_teor)/len(df)*100:.1f}%",
                    'Severidade': '🔴 Alta',
                    'Ação Recomendada': 'Drenar tanques e verificar vedação'
                })
        
        # Validação 3: Contaminação biológica
        if 'contaminacao_biologica' in df.columns:
            contaminados = df[df['contaminacao_biologica'] == True]
            if len(contaminados) > 0:
                validations.append({
                    '❌ Regra': 'Contaminação biológica presente',
                    'Violações': len(contaminados),
                    '% Total': f"{len(contaminados)/len(df)*100:.1f}%",
                    'Severidade': '🟡 Média',
                    'Ação Recomendada': 'Aplicar biocida e limpar tanques'
                })
        
        # Validação 4: Tempo de parada excessivo
        if 'tempo_parada_min' in df.columns:
            parada_longa = df[df['tempo_parada_min'] > 60]
            if len(parada_longa) > 0:
                validations.append({
                    '❌ Regra': 'Parada > 60 minutos',
                    'Violações': len(parada_longa),
                    '% Total': f"{len(parada_longa)/len(df)*100:.1f}%",
                    'Severidade': '🟡 Média',
                    'Ação Recomendada': 'Revisar procedimento de manutenção'
                })
        
        # Validação 5: Viscosidade fora do padrão
        if 'viscosidade' in df.columns:
            visc_fora = df[(df['viscosidade'] < 2.0) | (df['viscosidade'] > 4.5)]
            if len(visc_fora) > 0:
                validations.append({
                    '❌ Regra': 'Viscosidade fora do padrão (2.0-4.5 cSt)',
                    'Violações': len(visc_fora),
                    '% Total': f"{len(visc_fora)/len(df)*100:.1f}%",
                    'Severidade': '🟡 Média',
                    'Ação Recomendada': 'Verificar qualidade do diesel'
                })
        
        if validations:
            val_df = pd.DataFrame(validations)
            st.dataframe(val_df, use_container_width=True, hide_index=True)
            
            # Resumo de severidade
            alta_count = len([v for v in validations if '🔴' in v['Severidade']])
            media_count = len([v for v in validations if '🟡' in v['Severidade']])
            
            if alta_count > 0:
                st.error(f"⚠️ {alta_count} validações de ALTA severidade requerem ação imediata!")
            if media_count > 0:
                st.warning(f"⚠️ {media_count} validações de MÉDIA severidade requerem atenção")
        else:
            st.success("✅ Todos os dados estão dentro dos parâmetros aceitáveis!")
        
        # Relatório de qualidade
        st.subheader("📋 Relatório de Qualidade")
        
        quality_score = completeness * 0.4  # 40% peso para completude
        
        if validations:
            violation_penalty = len(validations) * 5  # -5% por validação violada
            quality_score -= violation_penalty
        
        quality_score = max(0, min(100, quality_score))  # Limitar entre 0 e 100
        
        if quality_score >= 80:
            st.success(f"🟢 Score de Qualidade: {quality_score:.1f}% - EXCELENTE")
        elif quality_score >= 60:
            st.warning(f"🟡 Score de Qualidade: {quality_score:.1f}% - BOM")
        else:
            st.error(f"🔴 Score de Qualidade: {quality_score:.1f}% - NECESSITA MELHORIA")
        
    else:
        st.info("Carregue dados primeiro na aba 'Coleta de Dados'")

# Tab 5: Dados Salvos
with tab5:
    st.header("Dados Salvos do Projeto")
    
    if supabase:
        try:
            # Carregar dados
            with st.spinner("Carregando dados salvos..."):
                data_response = supabase.table('datasets').select("*").eq('project_id', st.session_state.project_id).order('created_at', desc=True).execute()
                
                if data_response.data:
                    df_saved = pd.DataFrame(data_response.data)
                    
                    st.success(f"✅ {len(df_saved)} registros encontrados")
                    
                    # Filtros
                    st.subheader("🔍 Filtros")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        if 'unidade' in df_saved.columns:
                            unidades = ['Todas'] + sorted(df_saved['unidade'].dropna().unique().tolist())
                            selected_unidade = st.selectbox("Unidade:", unidades)
                    
                    with col2:
                        if 'turno' in df_saved.columns:
                            turnos = ['Todos'] + sorted(df_saved['turno'].dropna().unique().tolist())
                            selected_turno = st.selectbox("Turno:", turnos)
                    
                    with col3:
                        if 'defeito' in df_saved.columns:
                            defeitos = ['Todos'] + sorted(df_saved['defeito'].dropna().unique().tolist())
                            selected_defeito = st.selectbox("Defeito:", defeitos)
                    
                    with col4:
                        if 'data_coleta' in df_saved.columns:
                            df_saved['data_coleta'] = pd.to_datetime(df_saved['data_coleta'])
                            date_range = st.date_input(
                                "Período:",
                                value=(df_saved['data_coleta'].min(), df_saved['data_coleta'].max()),
                                key="date_filter"
                            )
                    
                    # Aplicar filtros
                    df_filtered = df_saved.copy()
                    
                    if 'selected_unidade' in locals() and selected_unidade != 'Todas':
                        df_filtered = df_filtered[df_filtered['unidade'] == selected_unidade]
                    
                    if 'selected_turno' in locals() and selected_turno != 'Todos':
                        df_filtered = df_filtered[df_filtered['turno'] == selected_turno]
                    
                    if 'selected_defeito' in locals() and selected_defeito != 'Todos':
                        df_filtered = df_filtered[df_filtered['defeito'] == selected_defeito]
                    
                    if 'date_range' in locals() and len(date_range) == 2:
                        df_filtered = df_filtered[
                            (df_filtered['data_coleta'] >= pd.to_datetime(date_range[0])) &
                            (df_filtered['data_coleta'] <= pd.to_datetime(date_range[1]))
                        ]
                    
                    # Mostrar dados filtrados
                    st.subheader(f"📊 Dados ({len(df_filtered)} registros)")
                    
                    # Selecionar colunas para exibir
                    display_columns = [
                        'cb_id', 'data_coleta', 'caminhao_id', 'unidade', 'turno',
                        'pressao_diesel', 'temperatura_diesel', 'teor_agua',
                        'defeito', 'tempo_parada_min', 'custo'
                    ]
                    
                    # Filtrar apenas colunas que existem
                    display_columns = [col for col in display_columns if col in df_filtered.columns]
                    
                    # Mostrar dataframe
                    st.dataframe(
                        df_filtered[display_columns],
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Opções de exportação
                    st.subheader("📥 Exportar Dados")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # CSV
                        csv = df_filtered.to_csv(index=False)
                        st.download_button(
                            label="📄 Download CSV",
                            data=csv,
                            file_name=f"dados_measure_{st.session_state.project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    
                    with col2:
                        # Excel
                        buffer = io.BytesIO()
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            df_filtered.to_excel(writer, sheet_name='Dados', index=False)
                        
                        st.download_button(
                            label="📊 Download Excel",
                            data=buffer.getvalue(),
                            file_name=f"dados_measure_{st.session_state.project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    
                    with col3:
                        # JSON
                        json_str = df_filtered.to_json(orient='records', date_format='iso')
                        st.download_button(
                            label="📦 Download JSON",
                            data=json_str,
                            file_name=f"dados_measure_{st.session_state.project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                    
                else:
                    st.info("Nenhum dado salvo ainda para este projeto. Adicione dados na aba 'Coleta de Dados'.")
                    
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
            st.info("Verifique se a tabela 'datasets' existe no Supabase com as colunas corretas.")
    else:
        st.warning("Configure o Supabase para ver os dados salvos")

# Footer
st.markdown("---")
st.markdown(f"📊 **Fase Measure** - Projeto ID: {st.session_state.project_id} | Green Belt Project")
