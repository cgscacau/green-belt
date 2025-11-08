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
            operador = st.text_input("Operador")
            
            st.write("**Dados do Processo**")
            caminhao_id = st.text_input("ID do Caminhão", value="CAM001")
            unidade = st.selectbox("Unidade", ["Unidade A", "Unidade B", "Unidade C"])
            
            st.write("**Medições de Diesel**")
            pressao_diesel = st.number_input("Pressão Diesel (bar)", min_value=0.0, max_value=10.0, value=4.5, step=0.1)
            temperatura_diesel = st.number_input("Temperatura (°C)", min_value=0.0, max_value=100.0, value=25.0)
            teor_agua = st.number_input("Teor de Água (%)", min_value=0.0, max_value=100.0, value=0.5, step=0.1)
            contaminacao_biologica = st.checkbox("Contaminação Biológica Detectada")
            
            st.write("**Operação**")
            horas_operacao = st.number_input("Horas de Operação", min_value=0.0, value=8.0, step=0.5)
            tempo_parada_min = st.number_input("Tempo de Parada (min)", min_value=0.0, value=0.0)
            
            st.write("**Defeitos e Custos**")
            defeito = st.selectbox("Tipo de Defeito", [
                "Sem defeito",
                "Combustível com alto teor de água",
                "Filtro saturado",
                "Processo inadequado",
                "Falta de drenagem",
                "Contaminação biológica",
                "Baixa pressão de alimentação"
            ])
            quantidade = st.number_input("Quantidade Produzida", min_value=0, value=100)
            defeitos = st.number_input("Quantidade de Defeitos", min_value=0, value=0)
            custo = st.number_input("Custo da Ocorrência (R$)", min_value=0.0, value=0.0)
            
            observacoes = st.text_area("Observações")
            
            submitted = st.form_submit_button("➕ Adicionar Registro")
            
            if submitted:
                # Criar registro
                novo_registro = {
                    'project_id': st.session_state.project_id,
                    'cb_id': cb_id,
                    'data_coleta': data_coleta.isoformat(),
                    'turno': turno,
                    'operador': operador,
                    'caminhao_id': caminhao_id,
                    'unidade': unidade,
                    'pressao_diesel': pressao_diesel,
                    'temperatura_diesel': temperatura_diesel,
                    'teor_agua': teor_agua,
                    'contaminacao_biologica': contaminacao_biologica,
                    'horas_operacao': horas_operacao,
                    'tempo_parada_min': tempo_parada_min,
                    'defeito': defeito,
                    'quantidade': quantidade,
                    'defeitos': defeitos,
                    'custo': custo,
                    'observacoes': observacoes,
                    'data_type': 'baseline'
                }
                
                # Salvar no Supabase
                if supabase:
                    try:
                        supabase.table('datasets').insert(novo_registro).execute()
                        st.success("✅ Registro salvo no banco de dados!")
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")
                
                # Adicionar ao DataFrame local
                new_df = pd.DataFrame([novo_registro])
                st.session_state.measure_data = pd.concat([st.session_state.measure_data, new_df], ignore_index=True)
                st.success("✅ Registro adicionado!")
    
    with col2:
        st.subheader("Upload de Dados em Lote")
        
        # Template para download
        if st.button("📥 Baixar Template CSV"):
            template = pd.DataFrame({
                'caminhao_id': ['CAM001', 'CAM002'],
                'data_coleta': [datetime.now().date(), datetime.now().date()],
                'turno': ['Manhã', 'Tarde'],
                'unidade': ['Unidade A', 'Unidade B'],
                'pressao_diesel': [4.5, 4.2],
                'temperatura_diesel': [25.0, 26.0],
                'teor_agua': [0.5, 0.8],
                'contaminacao_biologica': [False, False],
                'horas_operacao': [8.0, 7.5],
                'tempo_parada_min': [0, 30],
                'defeito': ['Sem defeito', 'Filtro saturado'],
                'quantidade': [100, 95],
                'defeitos': [0, 2],
                'custo': [0.0, 150.0]
            })
            
            csv = template.to_csv(index=False)
            st.download_button(
                label="Download Template",
                data=csv,
                file_name=f"template_measure_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        
        # Upload de arquivo
        uploaded_file = st.file_uploader("Upload CSV", type=['csv'])
        
        if uploaded_file:
            try:
                df_upload = pd.read_csv(uploaded_file)
                st.write("Preview dos dados:")
                st.dataframe(df_upload.head())
                
                if st.button("✅ Confirmar e Importar"):
                    # Adicionar project_id
                    df_upload['project_id'] = st.session_state.project_id
                    df_upload['data_type'] = 'baseline'
                    
                    # Salvar no Supabase
                    if supabase:
                        try:
                            # Converter DataFrame para lista de dicts
                            records = df_upload.to_dict('records')
                            
                            # Inserir em lote
                            for record in records:
                                # Converter tipos se necessário
                                if 'data_coleta' in record:
                                    record['data_coleta'] = pd.to_datetime(record['data_coleta']).date().isoformat()
                                
                                supabase.table('datasets').insert(record).execute()
                            
                            st.success(f"✅ {len(records)} registros salvos no banco de dados!")
                        except Exception as e:
                            st.error(f"Erro ao salvar: {e}")
                    
                    # Adicionar ao DataFrame local
                    st.session_state.measure_data = pd.concat([st.session_state.measure_data, df_upload], ignore_index=True)
                    st.success(f"✅ {len(df_upload)} registros importados!")
                    
            except Exception as e:
                st.error(f"Erro ao processar arquivo: {e}")

# Tab 2: Análise Exploratória
with tab2:
    st.header("Análise Exploratória de Dados")
    
    # Carregar dados do projeto
    if supabase:
        try:
            data_response = supabase.table('datasets').select("*").eq('project_id', st.session_state.project_id).execute()
            
            if data_response.data:
                df = pd.DataFrame(data_response.data)
                
                # Converter tipos
                if 'data_coleta' in df.columns:
                    df['data_coleta'] = pd.to_datetime(df['data_coleta'])
                
                numeric_cols = ['pressao_diesel', 'temperatura_diesel', 'teor_agua', 'horas_operacao', 
                               'tempo_parada_min', 'quantidade', 'defeitos', 'custo']
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                st.session_state.measure_data = df
                
                st.success(f"✅ {len(df)} registros carregados do projeto")
                
                # Métricas resumidas
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total de Registros", len(df))
                
                with col2:
                    if 'defeitos' in df.columns:
                        st.metric("Total de Defeitos", int(df['defeitos'].sum()))
                
                with col3:
                    if 'pressao_diesel' in df.columns:
                        baixa_pressao = len(df[df['pressao_diesel'] < 3.5])
                        st.metric("Ocorrências Baixa Pressão", baixa_pressao)
                
                with col4:
                    if 'custo' in df.columns:
                        st.metric("Custo Total", f"R$ {df['custo'].sum():,.2f}")
                
                # Gráficos exploratórios
                st.subheader("Visualizações")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if 'pressao_diesel' in df.columns:
                        fig = px.histogram(df, x='pressao_diesel', 
                                         title='Distribuição de Pressão de Diesel',
                                         nbins=20)
                        fig.add_vline(x=3.5, line_dash="dash", line_color="red",
                                    annotation_text="Limite Mínimo")
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    if 'defeito' in df.columns:
                        defeitos_count = df['defeito'].value_counts()
                        fig = px.pie(values=defeitos_count.values, 
                                   names=defeitos_count.index,
                                   title='Distribuição de Defeitos')
                        st.plotly_chart(fig, use_container_width=True)
                
                # Série temporal
                if 'data_coleta' in df.columns and 'pressao_diesel' in df.columns:
                    df_sorted = df.sort_values('data_coleta')
                    fig = px.line(df_sorted, x='data_coleta', y='pressao_diesel',
                                title='Pressão de Diesel ao Longo do Tempo',
                                markers=True)
                    fig.add_hline(y=3.5, line_dash="dash", line_color="red",
                                annotation_text="Limite Mínimo")
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
    st.header("Análise Estatística")
    
    if not st.session_state.measure_data.empty:
        df = st.session_state.measure_data
        
        # Selecionar variável para análise
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if numeric_columns:
            selected_var = st.selectbox("Selecione a variável para análise:", numeric_columns)
            
            if selected_var:
                data = df[selected_var].dropna()
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.subheader("Estatísticas Descritivas")
                    
                    stats_dict = {
                        'Média': data.mean(),
                        'Mediana': data.median(),
                        'Desvio Padrão': data.std(),
                        'Mínimo': data.min(),
                        'Q1': data.quantile(0.25),
                        'Q3': data.quantile(0.75),
                        'Máximo': data.max(),
                        'CV (%)': (data.std() / data.mean() * 100) if data.mean() != 0 else 0
                    }
                    
                    for stat, value in stats_dict.items():
                        st.metric(stat, f"{value:.2f}")
                    
                    # Salvar estatísticas no banco
                    if st.button("💾 Salvar Estatísticas"):
                        if supabase:
                            try:
                                stats_record = {
                                    'project_id': st.session_state.project_id,
                                    'variavel': selected_var,
                                    'media': float(stats_dict['Média']),
                                    'mediana': float(stats_dict['Mediana']),
                                    'desvio_padrao': float(stats_dict['Desvio Padrão']),
                                    'minimo': float(stats_dict['Mínimo']),
                                    'q1': float(stats_dict['Q1']),
                                    'q3': float(stats_dict['Q3']),
                                    'maximo': float(stats_dict['Máximo']),
                                    'cv': float(stats_dict['CV (%)']),
                                    'periodo_analise': 'baseline'
                                }
                                
                                supabase.table('measure_statistics').insert(stats_record).execute()
                                st.success("✅ Estatísticas salvas!")
                            except Exception as e:
                                st.error(f"Erro ao salvar: {e}")
                
                with col2:
                    st.subheader("Visualizações")
                    
                    # Boxplot
                    fig = go.Figure()
                    fig.add_trace(go.Box(y=data, name=selected_var))
                    fig.update_layout(title=f'Boxplot - {selected_var}')
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Teste de normalidade
                    st.subheader("Teste de Normalidade")
                    
                    if len(data) >= 3:
                        # Shapiro-Wilk
                        stat, p_value = stats.shapiro(data)
                        
                        st.write(f"**Teste Shapiro-Wilk**")
                        st.write(f"Estatística W: {stat:.4f}")
                        st.write(f"P-valor: {p_value:.4f}")
                        
                        if p_value > 0.05:
                            st.success("✅ Os dados seguem uma distribuição normal (p > 0.05)")
                        else:
                            st.warning("⚠️ Os dados NÃO seguem uma distribuição normal (p ≤ 0.05)")
                        
                        # Q-Q Plot
                        fig = go.Figure()
                        
                        # Calcular quantis teóricos
                        theoretical_quantiles = stats.norm.ppf(np.linspace(0.01, 0.99, len(data)))
                        sample_quantiles = np.sort(data)
                        
                        fig.add_trace(go.Scatter(
                            x=theoretical_quantiles,
                            y=sample_quantiles,
                            mode='markers',
                            name='Dados'
                        ))
                        
                        # Linha de referência
                        fig.add_trace(go.Scatter(
                            x=theoretical_quantiles,
                            y=theoretical_quantiles * data.std() + data.mean(),
                            mode='lines',
                            name='Normal Teórica',
                            line=dict(color='red', dash='dash')
                        ))
                        
                        fig.update_layout(
                            title='Q-Q Plot',
                            xaxis_title='Quantis Teóricos',
                            yaxis_title='Quantis da Amostra'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Carregue dados primeiro na aba 'Coleta de Dados'")

# Tab 4: Validação
with tab4:
    st.header("Validação de Dados")
    
    if not st.session_state.measure_data.empty:
        df = st.session_state.measure_data
        
        st.subheader("Verificação de Qualidade dos Dados")
        
        # Análise de missing values
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Valores Faltantes**")
            missing = df.isnull().sum()
            missing_pct = (missing / len(df) * 100).round(2)
            
            missing_df = pd.DataFrame({
                'Coluna': missing.index,
                'Valores Faltantes': missing.values,
                'Percentual (%)': missing_pct.values
            })
            
            missing_df = missing_df[missing_df['Valores Faltantes'] > 0]
            
            if not missing_df.empty:
                st.dataframe(missing_df)
            else:
                st.success("✅ Nenhum valor faltante encontrado!")
        
        with col2:
            st.write("**Outliers (Método IQR)**")
            
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            outliers_info = []
            
            for col in numeric_cols:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
                
                if len(outliers) > 0:
                    outliers_info.append({
                        'Variável': col,
                        'Outliers': len(outliers),
                        'Percentual (%)': round(len(outliers) / len(df) * 100, 2)
                    })
            
            if outliers_info:
                outliers_df = pd.DataFrame(outliers_info)
                st.dataframe(outliers_df)
            else:
                st.success("✅ Nenhum outlier detectado!")
        
        # Validações específicas do processo
        st.subheader("Validações Específicas do Processo")
        
        validations = []
        
        # Validação 1: Pressão de diesel
        if 'pressao_diesel' in df.columns:
            baixa_pressao = df[df['pressao_diesel'] < 3.5]
            if len(baixa_pressao) > 0:
                validations.append({
                    'Regra': 'Pressão < 3.5 bar',
                    'Violações': len(baixa_pressao),
                    'Severidade': 'Alta',
                    'Ação': 'Verificar sistema de alimentação'
                })
        
        # Validação 2: Teor de água
        if 'teor_agua' in df.columns:
            alto_teor_agua = df[df['teor_agua'] > 1.0]
            if len(alto_teor_agua) > 0:
                validations.append({
                    'Regra': 'Teor de água > 1%',
                    'Violações': len(alto_teor_agua),
                    'Severidade': 'Alta',
                    'Ação': 'Drenar tanques e verificar armazenamento'
                })
        
        # Validação 3: Tempo de parada excessivo
        if 'tempo_parada_min' in df.columns:
            parada_excessiva = df[df['tempo_parada_min'] > 60]
            if len(parada_excessiva) > 0:
                validations.append({
                    'Regra': 'Parada > 60 min',
                    'Violações': len(parada_excessiva),
                    'Severidade': 'Média',
                    'Ação': 'Revisar processo de manutenção'
                })
        
        if validations:
            val_df = pd.DataFrame(validations)
            st.dataframe(val_df)
        else:
            st.success("✅ Todos os dados estão dentro dos parâmetros esperados!")

# Tab 5: Dados Salvos
with tab5:
    st.header("Dados Salvos do Projeto")
    
    if supabase:
        try:
            # Carregar todos os dados do projeto
            data_response = supabase.table('datasets').select("*").eq('project_id', st.session_state.project_id).order('data_coleta', desc=True).execute()
            
            if data_response.data:
                df_saved = pd.DataFrame(data_response.data)
                
                st.success(f"✅ {len(df_saved)} registros encontrados")
                
                # Filtros
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if 'unidade' in df_saved.columns:
                        unidades = ['Todas'] + df_saved['unidade'].unique().tolist()
                        selected_unidade = st.selectbox("Filtrar por Unidade:", unidades)
                
                with col2:
                    if 'turno' in df_saved.columns:
                        turnos = ['Todos'] + df_saved['turno'].unique().tolist()
                        selected_turno = st.selectbox("Filtrar por Turno:", turnos)
                
                with col3:
                    if 'defeito' in df_saved.columns:
                        defeitos = ['Todos'] + df_saved['defeito'].unique().tolist()
                        selected_defeito = st.selectbox("Filtrar por Defeito:", defeitos)
                
                # Aplicar filtros
                df_filtered = df_saved.copy()
                
                if selected_unidade != 'Todas':
                    df_filtered = df_filtered[df_filtered['unidade'] == selected_unidade]
                
                if selected_turno != 'Todos':
                    df_filtered = df_filtered[df_filtered['turno'] == selected_turno]
                
                if selected_defeito != 'Todos':
                    df_filtered = df_filtered[df_filtered['defeito'] == selected_defeito]
                
                # Mostrar dados
                st.dataframe(df_filtered)
                
                # Download
                csv = df_filtered.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"dados_measure_projeto_{st.session_state.project_id}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
                
            else:
                st.info("Nenhum dado salvo ainda para este projeto.")
                
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
    else:
        st.warning("Configure o Supabase para ver os dados salvos")

# Footer
st.markdown("---")
st.markdown(f"📊 **Fase Measure** - Projeto ID: {st.session_state.project_id}")
