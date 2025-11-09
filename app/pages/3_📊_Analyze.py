import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from scipy import stats
from scipy.stats import normaltest, shapiro, kstest, anderson
from scipy.stats import f_oneway, kruskal, mannwhitneyu, wilcoxon
from scipy.stats import chi2_contingency, fisher_exact
from datetime import datetime
import os
import json
from supabase import create_client, Client
import seaborn as sns
import matplotlib.pyplot as plt
import textwrap # Importe no início do seu script


# Configuração da página
st.set_page_config(
    page_title="Analyze - Green Belt",
    page_icon="📊",
    layout="wide"
)

# ========================= CONFIGURAÇÃO E FUNÇÕES =========================

# Inicializar Supabase
@st.cache_resource
def init_supabase():
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
        st.error(f"Erro ao conectar: {str(e)}")
        return None

supabase = init_supabase()

# IMPORTANTE: Usar session_state para manter a tab selecionada
if 'selected_tab' not in st.session_state:
    st.session_state.selected_tab = 0

# Funções de dados
@st.cache_data(ttl=300)
def fetch_process_data_from_db(project_name):
    if not supabase:
        return None
    
    try:
        response = supabase.table('process_data').select("*").eq('project_name', project_name).order('uploaded_at', desc=True).limit(1).execute()
        
        if response.data and len(response.data) > 0:
            data_json = response.data[0].get('data', None)
            if data_json:
                if isinstance(data_json, list):
                    return pd.DataFrame(data_json)
                elif isinstance(data_json, dict):
                    if 'data' in data_json and 'columns' in data_json:
                        return pd.DataFrame(data_json['data'], columns=data_json['columns'])
                    else:
                        return pd.DataFrame(data_json)
        return None
    except Exception as e:
        st.error(f"Erro ao buscar dados: {str(e)}")
        return None

def save_analysis_to_db(project_name, analysis_type, results, analysis_subtype=None):
    if not supabase:
        return False
    
    try:
        def convert_to_serializable(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, pd.DataFrame):
                return obj.to_dict('records')
            elif isinstance(obj, pd.Series):
                return obj.to_dict()
            elif isinstance(obj, dict):
                return {key: convert_to_serializable(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(item) for item in obj]
            elif pd.isna(obj):
                return None
            else:
                return obj
        
        serializable_results = convert_to_serializable(results)
        
        # Salvar na tabela principal
        data = {
            'project_name': project_name,
            'analysis_type': analysis_type,
            'results': serializable_results,
            'created_at': datetime.now().isoformat()
        }
        
        response = supabase.table('analyses').insert(data).execute()
        
        # Salvar também na tabela de análises estatísticas se for o caso
        if analysis_subtype:
            stat_data = {
                'project_name': project_name,
                'analysis_type': analysis_type,
                'analysis_subtype': analysis_subtype,
                'results': serializable_results,
                'created_at': datetime.now().isoformat()
            }
            supabase.table('statistical_analyses').insert(stat_data).execute()
        
        return True
        
    except Exception as e:
        st.error(f"Erro ao salvar: {str(e)}")
        return False

# ========================= INTERFACE PRINCIPAL =========================

st.title("📊 Analyze — Análise Estatística Completa")

# Verificar projeto
if 'project_name' not in st.session_state:
    st.warning("⚠️ Selecione um projeto primeiro")
    st.stop()

project_name = st.session_state.project_name
st.info(f"📁 Projeto: **{project_name}**")

# Buscar dados
with st.spinner("Carregando dados..."):
    data = fetch_process_data_from_db(project_name)

if data is None:
    st.warning("⚠️ Nenhum dado encontrado. Faça upload primeiro.")
    uploaded_file = st.file_uploader("Upload CSV", type=['csv'])
    
    if uploaded_file:
        data = pd.read_csv(uploaded_file)
        if st.button("💾 Salvar no projeto"):
            # Salvar dados
            pass
else:
    st.success(f"✅ Dados carregados: {len(data)} registros")

# TABS COM SESSION STATE PARA NÃO RESETAR
tab_list = [
    "📊 Estatística Descritiva",
    "📈 Pareto",
    "🎯 Ishikawa",
    "📉 Análise de Regressão",
    "🔍 Testes de Hipóteses",
    "📐 Análise de Normalidade",
    "🔗 Correlação",
    "📊 Box Plot & Outliers",
    "⚙️ Análise de Capacidade",
    "🎲 ANOVA",
    "❓ 5 Porquês",
    "📋 FMEA"
]

# Criar tabs
tabs = st.tabs(tab_list)

# ========================= TAB 1: ESTATÍSTICA DESCRITIVA =========================
with tabs[0]:
    st.header("📊 Estatística Descritiva Completa")
    
    if data is not None:
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        
        if numeric_cols:
            selected_cols = st.multiselect(
                "Selecione as variáveis para análise:",
                numeric_cols,
                default=numeric_cols[:3] if len(numeric_cols) > 3 else numeric_cols,
                key="desc_stats_cols"
            )
            
            if selected_cols:
                # Estatísticas básicas
                st.subheader("📈 Medidas de Tendência Central e Dispersão")
                
                stats_df = pd.DataFrame()
                for col in selected_cols:
                    stats_dict = {
                        'Variável': col,
                        'Contagem': data[col].count(),
                        'Média': data[col].mean(),
                        'Mediana': data[col].median(),
                        'Moda': data[col].mode()[0] if not data[col].mode().empty else np.nan,
                        'Desvio Padrão': data[col].std(),
                        'Variância': data[col].var(),
                        'Mínimo': data[col].min(),
                        'Q1 (25%)': data[col].quantile(0.25),
                        'Q2 (50%)': data[col].quantile(0.50),
                        'Q3 (75%)': data[col].quantile(0.75),
                        'Máximo': data[col].max(),
                        'Amplitude': data[col].max() - data[col].min(),
                        'IQR': data[col].quantile(0.75) - data[col].quantile(0.25),
                        'CV%': (data[col].std() / data[col].mean() * 100) if data[col].mean() != 0 else 0,
                        'Assimetria': data[col].skew(),
                        'Curtose': data[col].kurtosis()
                    }
                    stats_df = pd.concat([stats_df, pd.DataFrame([stats_dict])], ignore_index=True)
                
                # Formatar e exibir
                st.dataframe(
                    stats_df.style.format({
                        'Contagem': '{:.0f}',
                        'Média': '{:.3f}',
                        'Mediana': '{:.3f}',
                        'Moda': '{:.3f}',
                        'Desvio Padrão': '{:.3f}',
                        'Variância': '{:.3f}',
                        'Mínimo': '{:.3f}',
                        'Q1 (25%)': '{:.3f}',
                        'Q2 (50%)': '{:.3f}',
                        'Q3 (75%)': '{:.3f}',
                        'Máximo': '{:.3f}',
                        'Amplitude': '{:.3f}',
                        'IQR': '{:.3f}',
                        'CV%': '{:.2f}%',
                        'Assimetria': '{:.3f}',
                        'Curtose': '{:.3f}'
                    }),
                    use_container_width=True
                )
                
                # Interpretação
                st.subheader("💡 Interpretação")
                for _, row in stats_df.iterrows():
                    with st.expander(f"Análise de {row['Variável']}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Assimetria
                            if abs(row['Assimetria']) < 0.5:
                                st.success(f"✅ Distribuição aproximadamente simétrica ({row['Assimetria']:.3f})")
                            elif row['Assimetria'] > 0.5:
                                st.warning(f"⚠️ Assimetria positiva (cauda à direita) ({row['Assimetria']:.3f})")
                            else:
                                st.warning(f"⚠️ Assimetria negativa (cauda à esquerda) ({row['Assimetria']:.3f})")
                        
                        with col2:
                            # Curtose
                            if abs(row['Curtose']) < 0.5:
                                st.success(f"✅ Curtose normal (mesocúrtica) ({row['Curtose']:.3f})")
                            elif row['Curtose'] > 0.5:
                                st.info(f"📊 Distribuição leptocúrtica (pico alto) ({row['Curtose']:.3f})")
                            else:
                                st.info(f"📊 Distribuição platicúrtica (achatada) ({row['Curtose']:.3f})")
                        
                        # CV
                        if row['CV%'] < 15:
                            st.success(f"✅ Baixa variabilidade (CV = {row['CV%']:.2f}%)")
                        elif row['CV%'] < 30:
                            st.warning(f"⚠️ Variabilidade moderada (CV = {row['CV%']:.2f}%)")
                        else:
                            st.error(f"❌ Alta variabilidade (CV = {row['CV%']:.2f}%)")
                
                # Salvar análise
                if st.button("💾 Salvar Estatísticas Descritivas", key="save_desc_stats"):
                    if save_analysis_to_db(project_name, "descriptive_statistics", stats_df.to_dict(), "full_descriptive"):
                        st.success("✅ Análise salva!")

# ========================= TAB 2: PARETO (CORRIGIDO) =========================
with tabs[1]:
    st.header("📈 Análise de Pareto")
    
    if data is not None and len(data.columns) > 0:
        # Usar container para evitar reset
        pareto_container = st.container()
        
        with pareto_container:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Use keys únicos e session_state
                if 'pareto_category' not in st.session_state:
                    st.session_state.pareto_category = data.columns[0]
                
                category_col = st.selectbox(
                    "Coluna de categorias:",
                    data.columns,
                    index=list(data.columns).index(st.session_state.pareto_category) if st.session_state.pareto_category in data.columns else 0,
                    key="pareto_cat_select"
                )
                st.session_state.pareto_category = category_col
                
                value_col = st.selectbox(
                    "Coluna de valores:",
                    ["Contagem"] + list(data.columns),
                    key="pareto_val_select"
                )
            
            with col2:
                st.info("""
                **Princípio 80/20:**
                80% dos efeitos vêm de 20% das causas
                """)
            
            # Botão para gerar
            if st.button("🎯 Gerar Pareto", type="primary", key="gen_pareto"):
                try:
                    # Processar dados com tratamento de erros
                    if value_col == "Contagem":
                        pareto_data = data[category_col].value_counts().reset_index()
                        pareto_data.columns = ['Categoria', 'Frequência']
                        value_column = 'Frequência'
                    else:
                        # Verificar se a coluna de valor é numérica
                        if data[value_col].dtype not in ['int64', 'float64']:
                            st.error(f"❌ A coluna '{value_col}' não é numérica. Selecione uma coluna numérica ou use 'Contagem'.")
                            st.stop()
                        
                        # Agrupar e somar, removendo NaN
                        pareto_data = data.groupby(category_col)[value_col].sum().reset_index()
                        pareto_data.columns = ['Categoria', 'Valor']
                        value_column = 'Valor'
                        
                        # Remover valores NaN ou negativos
                        pareto_data = pareto_data.dropna()
                        pareto_data = pareto_data[pareto_data[value_column] > 0]
                    
                    # Verificar se há dados após limpeza
                    if len(pareto_data) == 0:
                        st.error("❌ Nenhum dado válido para criar o gráfico de Pareto")
                        st.stop()
                    
                    # Ordenar por valor decrescente
                    pareto_data = pareto_data.sort_values(by=value_column, ascending=False)
                    
                    # Calcular total com verificação
                    total = pareto_data[value_column].sum()
                    
                    if total == 0 or pd.isna(total):
                        st.error("❌ A soma total dos valores é zero ou inválida. Verifique seus dados.")
                        st.stop()
                    
                    # Calcular percentuais com segurança
                    pareto_data['Percentual'] = (pareto_data[value_column].astype(float) / float(total)) * 100
                    pareto_data['Acumulado'] = pareto_data['Percentual'].cumsum()
                    
                    # Identificar Vital Few
                    vital_few = pareto_data[pareto_data['Acumulado'] <= 80]
                    if len(vital_few) == 0:
                        vital_few = pareto_data.head(1)  # Pelo menos um item
                    
                    # Criar gráfico
                    fig = go.Figure()
                    
                    # Barras com cores diferentes para vital few
                    colors = ['red' if i < len(vital_few) else 'lightblue' for i in range(len(pareto_data))]
                    
                    fig.add_trace(go.Bar(
                        x=pareto_data['Categoria'].astype(str),
                        y=pareto_data[value_column],
                        name=value_column,
                        marker_color=colors,
                        yaxis='y',
                        text=pareto_data[value_column].round(2),
                        textposition='outside'
                    ))
                    
                    # Linha acumulada
                    fig.add_trace(go.Scatter(
                        x=pareto_data['Categoria'].astype(str),
                        y=pareto_data['Acumulado'],
                        name='% Acumulado',
                        mode='lines+markers',
                        line=dict(color='green', width=2),
                        marker=dict(size=8),
                        yaxis='y2',
                        text=pareto_data['Acumulado'].round(1),
                        texttemplate='%{text}%',
                        textposition='top center'
                    ))
                    
                    # Linha 80%
                    fig.add_hline(
                        y=80, 
                        line_dash="dash", 
                        line_color="orange",
                        annotation_text="80%", 
                        yref='y2'
                    )
                    
                    fig.update_layout(
                        title=f"Gráfico de Pareto: {category_col}",
                        xaxis=dict(title="Categorias", tickangle=-45),
                        yaxis=dict(title=value_column, side='left'),
                        yaxis2=dict(
                            title='% Acumulado', 
                            overlaying='y', 
                            side='right', 
                            range=[0, 105]
                        ),
                        height=500,
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Métricas
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total de Categorias", len(pareto_data))
                    with col2:
                        st.metric("Vital Few (80%)", len(vital_few))
                    with col3:
                        vital_percentage = (len(vital_few)/len(pareto_data)*100)
                        st.metric("% dos Vital Few", f"{vital_percentage:.1f}%")
                    
                    # Tabela detalhada
                    st.subheader("📊 Detalhamento")
                    
                    # Formatar a tabela para exibição
                    display_df = pareto_data.copy()
                    display_df['Percentual'] = display_df['Percentual'].round(2).astype(str) + '%'
                    display_df['Acumulado'] = display_df['Acumulado'].round(2).astype(str) + '%'
                    display_df[value_column] = display_df[value_column].round(2)
                    
                    # Destacar vital few
                    def highlight_vital(row):
                        if row.name < len(vital_few):
                            return ['background-color: #ffcccc'] * len(row)
                        return [''] * len(row)
                    
                    styled_df = display_df.style.apply(highlight_vital, axis=1)
                    st.dataframe(styled_df, use_container_width=True, hide_index=True)
                    
                    # Insights
                    st.subheader("💡 Insights")
                    
                    top_category = pareto_data.iloc[0]['Categoria']
                    top_value = pareto_data.iloc[0][value_column]
                    top_percent = pareto_data.iloc[0]['Percentual']
                    
                    st.success(f"""
                    **Análise de Pareto:**
                    - A categoria **"{top_category}"** é a mais significativa com {top_value:.2f} ({top_percent:.1f}% do total)
                    - **{len(vital_few)} categorias** representam 80% do impacto total
                    - Isso corresponde a **{vital_percentage:.1f}%** das categorias
                    - **Recomendação:** Foque nas {len(vital_few)} categorias principais para máximo impacto
                    """)
                    
                    # Salvar análise
                    if st.button("💾 Salvar Análise Pareto", key="save_pareto"):
                        analysis_data = {
                            'data': pareto_data.to_dict('records'),
                            'vital_few_count': int(len(vital_few)),
                            'total_categories': int(len(pareto_data)),
                            'category_column': str(category_col),
                            'value_column': str(value_col),
                            'total_value': float(total),
                            'vital_few_percentage': float(vital_percentage),
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        if save_analysis_to_db(project_name, "pareto", analysis_data, "pareto_analysis"):
                            st.success("✅ Análise salva com sucesso!")
                        else:
                            st.error("❌ Erro ao salvar análise")
                    
                    # Download CSV
                    csv = pareto_data.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"pareto_{category_col}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                    
                except Exception as e:
                    st.error(f"❌ Erro ao gerar análise de Pareto: {str(e)}")
                    st.info("Verifique se os dados estão corretos e tente novamente")
                    
                    # Debug info
                    with st.expander("🐛 Informações de Debug"):
                        st.write("Tipo de erro:", type(e).__name__)
                        st.write("Mensagem:", str(e))
                        if value_col != "Contagem":
                            st.write(f"Tipo da coluna {value_col}:", data[value_col].dtype)
                            st.write(f"Primeiros valores de {value_col}:", data[value_col].head())
                            st.write(f"Valores únicos em {category_col}:", data[category_col].nunique())
    else:
        st.warning("⚠️ Nenhum dado disponível para análise de Pareto")

########################################################################################################################################################################################################################################


# ==============================================================================
# ========================= TAB 3: ISHIKAWA (VERSÃO FINAL COM LOAD) =========================
# ==============================================================================

import streamlit as st
import plotly.graph_objects as go
import textwrap
import pandas as pd
from datetime import datetime

# ==============================================================================
# FUNÇÃO DE CRIAÇÃO DO DIAGRAMA
# ==============================================================================
def create_definitive_ishikawa(problem, categories_filled):
    """
    Cria um diagrama de Ishikawa com design final, usando um layout de posição fixo
    para até 5 causas por categoria, garantindo zero sobreposição.
    """

    def wrap_text(text, width):
        return '<br>'.join(textwrap.wrap(text, width=width, break_long_words=False, replace_whitespace=False))

    fig = go.Figure()

    fig.update_layout(
        title={
            'text': "<b>Diagrama de Ishikawa - Análise de Causa e Efeito</b>",
            'x': 0.5, 'xanchor': 'center', 'font': {'size': 26, 'color': '#FFFFFF'}
        },
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, visible=False, range=[-5, 13]),
        yaxis=dict(showgrid=False, zeroline=False, visible=False, range=[-8, 13]),
        height=900,
        margin=dict(l=10, r=10, t=90, b=10),
        plot_bgcolor='#0E1117',
        paper_bgcolor='#0E1117',
    )

    fig.add_trace(go.Scatter(
        x=[0, 9.3], y=[3, 3], mode='lines',
        line=dict(color='#FFFFFF', width=4), hoverinfo='skip'
    ))

    category_colors = {
        "Método": '#E74C3C', "Máquina": '#3498DB', "Mão de obra": '#2ECC71',
        "Material": '#F39C12', "Medida": '#9B59B6', "Meio ambiente": '#1ABC9C'
    }

    category_positions = {
        "Método": (1.5, 8, True), "Máquina": (4.5, 8, True), "Mão de obra": (7.5, 8, True),
        "Material": (1.5, -2, False), "Medida": (4.5, -2, False), "Meio ambiente": (7.5, -2, False)
    }
    
    cause_positions = [
        {'x': 2.0, 'y': 1.2, 'align': 'left'},
        {'x': -2.0, 'y': 1.2, 'align': 'right'},
        {'x': 2.8, 'y': 2.6, 'align': 'left'},
        {'x': -2.8, 'y': 2.6, 'align': 'right'},
        {'x': 0, 'y': 2.4, 'align': 'center'},
    ]

    for category, causes in categories_filled.items():
        if category in category_positions:
            x_pos, y_pos, is_top = category_positions[category]
            color = category_colors.get(category, '#7F8C8D')

            fig.add_trace(go.Scatter(
                x=[x_pos, x_pos], y=[y_pos, 3], mode='lines',
                line=dict(color=color, width=3), hoverinfo='skip'
            ))

            fig.add_annotation(
                x=x_pos + 0.05, y=y_pos - 0.05, text=f"<b>{category.upper()}</b>", showarrow=False,
                font=dict(size=15, color='black'), bgcolor='black', opacity=0.4, borderpad=10, borderwidth=2, bordercolor='black'
            )
            fig.add_annotation(
                x=x_pos, y=y_pos, text=f"<b>{category.upper()}</b>", showarrow=False,
                font=dict(size=15, color='#FFFFFF'), bgcolor=color, bordercolor='#FFFFFF', borderwidth=2, borderpad=10
            )

            for j, cause in enumerate(causes[:5]):
                pos_data = cause_positions[j]
                x_offset, y_offset, text_align = pos_data['x'], pos_data['y'], pos_data['align']
                
                cause_x = x_pos + x_offset
                cause_y = y_pos + (y_offset if is_top else -y_offset)
                
                fig.add_trace(go.Scatter(
                    x=[x_pos, cause_x], y=[y_pos, cause_y], mode='lines',
                    line=dict(color=color, width=1.5, dash='dot'), opacity=0.7, hoverinfo='skip'
                ))
                
                wrapped_cause = wrap_text(cause, width=28)
                
                fig.add_annotation(
                    x=cause_x + 0.05, y=cause_y - 0.05, text=wrapped_cause, align=text_align, showarrow=False,
                    font=dict(size=12, color='black'), bgcolor='black', opacity=0.3, borderpad=8, borderwidth=2, bordercolor='black'
                )
                fig.add_annotation(
                    x=cause_x, y=cause_y, text=wrapped_cause, align=text_align, showarrow=False,
                    font=dict(size=12, color='#FFFFFF'), bgcolor='rgba(45, 52, 54, 0.9)', bordercolor=color, borderwidth=2, borderpad=8
                )

    wrapped_problem = wrap_text(problem, width=25)
    fig.add_annotation(
        x=10.5 + 0.05, y=3 - 0.05, text=f"<b>PROBLEMA</b><br>{wrapped_problem}", showarrow=False,
        font=dict(size=13, color='black'), align='center', bgcolor='black', opacity=0.4, borderpad=12, borderwidth=2, bordercolor='black'
    )
    fig.add_annotation(
        x=10.5, y=3, text=f"<b>PROBLEMA</b><br>{wrapped_problem}", showarrow=False,
        font=dict(size=13, color='#FFFFFF'), align='center', bgcolor='#E74C3C', bordercolor='#FFFFFF', borderwidth=2, borderpad=12
    )

    fig.add_annotation(
        x=9.5, y=3, ax=9.3, ay=3, showarrow=True, arrowhead=3,
        arrowsize=1.5, arrowwidth=3, arrowcolor='#FFFFFF'
    )

    return fig

# ==============================================================================
# FUNÇÃO PARA CARREGAR DADOS DO SUPABASE
# ==============================================================================
def load_ishikawa_from_supabase(project_name):
    """Carrega análise Ishikawa salva do Supabase"""
    if not supabase:
        return None
    
    try:
        response = supabase.table('analyses').select('*').eq('project_name', project_name).eq('analysis_type', 'ishikawa').order('created_at', desc=True).limit(1).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]['results']
        return None
        
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return None


# ==============================================================================
# INÍCIO DA LÓGICA DA TAB 3
# ==============================================================================
with tabs[2]:
    st.header("🎯 Diagrama de Ishikawa (Espinha de Peixe)")
    
    # Verificar se há projeto selecionado
    project_name = st.session_state.get('project_name', None)
    
    if not project_name:
        st.warning("⚠️ Nenhum projeto selecionado. Por favor, selecione ou crie um projeto primeiro.")
        st.stop()
    
    # Botão para carregar dados salvos
    col_load, col_new = st.columns([1, 1])
    
    with col_load:
        if st.button("📂 Carregar Análise Salva", use_container_width=True, type="secondary"):
            loaded_data = load_ishikawa_from_supabase(project_name)
            if loaded_data:
                # Reconstruir a estrutura de dados
                st.session_state.ishikawa_data = {
                    'problem': loaded_data.get('problem', ''),
                    'categories': {}
                }
                
                # Reconstruir categorias
                for cat_name in ["Método", "Máquina", "Mão de obra", "Material", "Medida", "Meio ambiente"]:
                    causes_list = loaded_data.get('categories', {}).get(cat_name, [])
                    causes_dict = {i: cause for i, cause in enumerate(causes_list)}
                    st.session_state.ishikawa_data['categories'][cat_name] = {
                        'num_causes': max(3, len(causes_list)),
                        'causes': causes_dict
                    }
                
                st.success("✅ Análise carregada com sucesso!")
                st.rerun()
            else:
                st.info("ℹ️ Nenhuma análise salva encontrada para este projeto.")
    
    with col_new:
        if st.button("🆕 Nova Análise", use_container_width=True):
            st.session_state.ishikawa_data = {
                'problem': '',
                'categories': {
                    "Método": {'num_causes': 3, 'causes': {}}, "Máquina": {'num_causes': 3, 'causes': {}},
                    "Mão de obra": {'num_causes': 3, 'causes': {}}, "Material": {'num_causes': 3, 'causes': {}},
                    "Medida": {'num_causes': 3, 'causes': {}}, "Meio ambiente": {'num_causes': 3, 'causes': {}}
                }
            }
            st.rerun()
    
    st.divider()
    
    # Inicializar dados se não existirem
    if 'ishikawa_data' not in st.session_state:
        st.session_state.ishikawa_data = {
            'problem': '',
            'categories': {
                "Método": {'num_causes': 3, 'causes': {}}, "Máquina": {'num_causes': 3, 'causes': {}},
                "Mão de obra": {'num_causes': 3, 'causes': {}}, "Material": {'num_causes': 3, 'causes': {}},
                "Medida": {'num_causes': 3, 'causes': {}}, "Meio ambiente": {'num_causes': 3, 'causes': {}}
            }
        }
    
    problem = st.text_input(
        "Defina o problema central:", 
        value=st.session_state.ishikawa_data.get('problem', ''),
        key="ishikawa_problem_input"
    )
    st.session_state.ishikawa_data['problem'] = problem
    
    with st.container(border=True):
        st.subheader("📝 Adicionar Causas por Categoria")
        view_mode = st.radio("Modo de visualização:", ["Todas as Categorias", "Uma por Vez"], horizontal=True, key="ishikawa_view_mode")
        
        categories_to_show = list(st.session_state.ishikawa_data['categories'].keys())
        if view_mode == "Uma por Vez":
            selected_category = st.selectbox("Selecione a categoria:", categories_to_show, key="ishikawa_selected_cat")
            categories_to_show = [selected_category]
        
        for category in categories_to_show:
            with st.expander(f"📌 {category}", expanded=(view_mode == "Uma por Vez")):
                col1, col2, col3 = st.columns([2, 1, 1])
                current_num = st.session_state.ishikawa_data['categories'][category]['num_causes']
                col1.write(f"**Campos de causa: {current_num}**")
                if col2.button("➕", key=f"add_btn_{category}", help="Adicionar campo"):
                    st.session_state.ishikawa_data['categories'][category]['num_causes'] = min(10, current_num + 1)
                    st.rerun()
                if col3.button("➖", key=f"rem_btn_{category}", help="Remover campo"):
                    st.session_state.ishikawa_data['categories'][category]['num_causes'] = max(1, current_num - 1)
                    st.rerun()
                
                for i in range(st.session_state.ishikawa_data['categories'][category]['num_causes']):
                    saved_value = st.session_state.ishikawa_data['categories'][category]['causes'].get(i, '')
                    cause = st.text_input(f"Causa {i+1}:", value=saved_value, key=f"ishikawa_cause_{category}_{i}", placeholder=f"Descreva a causa {i+1} para '{category}'")
                    st.session_state.ishikawa_data['categories'][category]['causes'][i] = cause
        
        with st.expander("⚡ Entrada Rápida - Colar Lista de Causas"):
            col1, col2 = st.columns([1, 2])
            quick_category = col1.selectbox("Adicionar à Categoria:", list(st.session_state.ishikawa_data['categories'].keys()), key="quick_cat_select")
            quick_input = col2.text_area("Cole as causas (uma por linha):", height=120, key="quick_causes_input")
            if st.button("➕ Adicionar da Lista", key="add_quick_list"):
                if quick_input and quick_category:
                    lines = [line.strip() for line in quick_input.split('\n') if line.strip()]
                    cat_data = st.session_state.ishikawa_data['categories'][quick_category]
                    non_empty_causes = {k: v for k, v in cat_data['causes'].items() if v}
                    start_index = len(non_empty_causes)
                    for i, line in enumerate(lines):
                        if start_index + i < 10:
                            cat_data['causes'][start_index + i] = line
                    cat_data['num_causes'] = max(cat_data['num_causes'], len(cat_data['causes']))
                    st.success(f"{len(lines)} causa(s) adicionada(s) a '{quick_category}'.")
                    st.rerun()

    st.divider()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🎨 Gerar Diagrama", type="primary", use_container_width=True):
            st.session_state.show_ishikawa_diagram = True
    with col2:
        if st.button("💾 Salvar Análise", use_container_width=True):
            st.session_state.save_ishikawa = True
    with col3:
        if st.button("📥 Exportar CSV", use_container_width=True):
            st.session_state.export_ishikawa = True
    with col4:
        if st.button("🗑️ Limpar Tudo", use_container_width=True):
            st.session_state.ishikawa_data = {'problem': '', 'categories': {"Método": {'num_causes': 3, 'causes': {}}, "Máquina": {'num_causes': 3, 'causes': {}}, "Mão de obra": {'num_causes': 3, 'causes': {}}, "Material": {'num_causes': 3, 'causes': {}}, "Medida": {'num_causes': 3, 'causes': {}}, "Meio ambiente": {'num_causes': 3, 'causes': {}}}}
            st.session_state.show_ishikawa_diagram = False
            st.rerun()

    diagram_container = st.container()

    if st.session_state.get('show_ishikawa_diagram', False):
        with diagram_container:
            problem_text = st.session_state.ishikawa_data.get('problem', '')
            categories_filled = {cat_name: [v for v in cat_data['causes'].values() if v] for cat_name, cat_data in st.session_state.ishikawa_data['categories'].items() if any(v for v in cat_data['causes'].values())}

            if not problem_text:
                st.warning("⚠️ Por favor, defina o problema central antes de gerar o diagrama.")
                st.info("💡 **Dica:** Você pode carregar uma análise salva usando o botão '📂 Carregar Análise Salva' no topo da página.")
            elif not categories_filled:
                st.warning("⚠️ Adicione pelo menos uma causa em qualquer categoria.")
                st.info("💡 **Dica:** Use a 'Entrada Rápida' para adicionar múltiplas causas de uma vez.")
            else:
                fig = create_definitive_ishikawa(problem_text, categories_filled)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("---")
                st.subheader("📊 Estatísticas da Análise")
                total_causes = sum(len(c) for c in categories_filled.values())
                stat_cols = st.columns(3)
                stat_cols[0].metric("Total de Causas", total_causes)
                stat_cols[1].metric("Categorias Utilizadas", len(categories_filled))
                if categories_filled:
                    max_cat = max(categories_filled, key=lambda k: len(categories_filled[k]))
                    stat_cols[2].metric("Categoria Principal", max_cat)
    
    # Lógica de salvamento
    if st.session_state.get('save_ishikawa', False):
        problem_text = st.session_state.ishikawa_data.get('problem', '')
        categories_filled = {
            cat_name: [v for v in cat_data['causes'].values() if v]
            for cat_name, cat_data in st.session_state.ishikawa_data['categories'].items()
            if any(v for v in cat_data['causes'].values())
        }
        
        if categories_filled and problem_text:
            analysis_data = {
                'problem': problem_text,
                'categories': categories_filled,
                'total_causes': sum(len(c) for c in categories_filled.values()),
                'timestamp': datetime.now().isoformat()
            }
            
            if save_analysis_to_db(project_name, "ishikawa", analysis_data):
                st.success("✅ Análise Ishikawa salva com sucesso no Supabase!")
            else:
                st.error("❌ Falha ao salvar a análise no Supabase.")
        else:
            st.warning("⚠️ Nada para salvar. Preencha o problema e pelo menos uma causa.")
        
        st.session_state.save_ishikawa = False

    if st.session_state.get('export_ishikawa', False):
        export_data = []
        for cat, data in st.session_state.ishikawa_data['categories'].items():
            for i, cause_text in data['causes'].items():
                if cause_text:
                    export_data.append({'Categoria': cat, 'Causa': cause_text})
        
        if export_data:
            df_export = pd.DataFrame(export_data)
            csv = df_export.to_csv(index=False).encode('utf-8')
            st.download_button("Clique para Baixar o CSV", csv, f"ishikawa_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
        else:
            st.warning("Não há dados para exportar.")
        st.session_state.export_ishikawa = False







#########################################################################################################################################################################################################################################



# ========================= TAB 4: REGRESSÃO (COM SALVAMENTO) =========================
with tabs[3]:
    st.header("📉 Análise de Regressão")
    
    # Verificar se há projeto selecionado
    project_name = st.session_state.get('project_name', None)
    
    if not project_name:
        st.warning("⚠️ Nenhum projeto selecionado. Por favor, selecione ou crie um projeto primeiro.")
        st.stop()
    
    # Botões de carregar e nova análise
    col_load, col_new = st.columns([1, 1])
    
    with col_load:
        if st.button("📂 Carregar Análise Salva", use_container_width=True, type="secondary", key="load_regression"):
            if not supabase:
                st.error("❌ Conexão com Supabase não disponível.")
            else:
                try:
                    response = supabase.table('analyses').select('*').eq('project_name', project_name).eq('analysis_type', 'regression').order('created_at', desc=True).limit(1).execute()
                    
                    if response.data and len(response.data) > 0:
                        loaded_data = response.data[0]['results']
                        st.session_state.regression_results = loaded_data
                        st.success("✅ Análise de regressão carregada com sucesso!")
                        st.rerun()
                    else:
                        st.info("ℹ️ Nenhuma análise de regressão salva encontrada para este projeto.")
                except Exception as e:
                    st.error(f"Erro ao carregar dados: {str(e)}")
    
    with col_new:
        if st.button("🆕 Nova Análise", use_container_width=True, key="new_regression"):
            if 'regression_results' in st.session_state:
                del st.session_state.regression_results
            st.rerun()
    
    st.divider()
    
    if data is not None:
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) >= 2:
            col1, col2 = st.columns(2)
            
            with col1:
                x_var = st.selectbox("Variável Independente (X):", numeric_cols, key="reg_x")
            with col2:
                y_var = st.selectbox("Variável Dependente (Y):", 
                                   [c for c in numeric_cols if c != x_var], key="reg_y")
            
            # Botões de ação
            col_exec, col_save, col_export = st.columns([1, 1, 1])
            
            with col_exec:
                execute_regression = st.button("🔄 Executar Regressão", key="run_regression", use_container_width=True, type="primary")
            
            with col_save:
                save_regression = st.button("💾 Salvar Análise", key="save_regression", use_container_width=True)
            
            with col_export:
                export_regression = st.button("📥 Exportar Resultados", key="export_regression", use_container_width=True)
            
            # Executar regressão
            if execute_regression or 'regression_results' in st.session_state:
                
                if execute_regression:
                    from sklearn.linear_model import LinearRegression
                    from sklearn.metrics import r2_score, mean_squared_error
                    
                    # Preparar dados
                    X = data[[x_var]].dropna()
                    y = data[y_var].dropna()
                    
                    # Alinhar índices
                    common_idx = X.index.intersection(y.index)
                    X = X.loc[common_idx]
                    y = y.loc[common_idx]
                    
                    # Regressão
                    model = LinearRegression()
                    model.fit(X, y)
                    y_pred = model.predict(X)
                    
                    # Métricas
                    r2 = r2_score(y, y_pred)
                    rmse = np.sqrt(mean_squared_error(y, y_pred))
                    
                    # Calcular intervalo de confiança (simplificado)
                    n = len(y)
                    dof = n - 2  # graus de liberdade
                    
                    # Salvar resultados no session_state
                    st.session_state.regression_results = {
                        'x_var': x_var,
                        'y_var': y_var,
                        'coefficient': float(model.coef_[0]),
                        'intercept': float(model.intercept_),
                        'r2': float(r2),
                        'rmse': float(rmse),
                        'n_samples': int(n),
                        'x_values': X.iloc[:, 0].tolist(),
                        'y_values': y.tolist(),
                        'y_pred': y_pred.tolist(),
                        'residuals': (y - y_pred).tolist(),
                        'equation': f"y = {model.coef_[0]:.4f}x + {model.intercept_:.4f}"
                    }
                
                # Recuperar resultados (seja de execução nova ou carregados)
                results = st.session_state.get('regression_results', None)
                
                if results:
                    # Gráfico de regressão
                    fig = go.Figure()
                    
                    # Scatter plot
                    fig.add_trace(go.Scatter(
                        x=results['x_values'], 
                        y=results['y_values'],
                        mode='markers',
                        name='Dados Observados',
                        marker=dict(size=8, color='blue', opacity=0.6)
                    ))
                    
                    # Linha de regressão
                    fig.add_trace(go.Scatter(
                        x=results['x_values'], 
                        y=results['y_pred'],
                        mode='lines',
                        name='Regressão',
                        line=dict(color='red', width=3)
                    ))
                    
                    # Equação e R²
                    fig.add_annotation(
                        x=max(results['x_values']), 
                        y=max(results['y_values']),
                        text=f"<b>{results['equation']}</b><br>R² = {results['r2']:.4f}",
                        showarrow=False,
                        bgcolor='rgba(255, 255, 255, 0.8)',
                        bordercolor='black',
                        borderwidth=1,
                        borderpad=10,
                        font=dict(size=12)
                    )
                    
                    fig.update_layout(
                        title=f"<b>Regressão Linear: {results['y_var']} vs {results['x_var']}</b>",
                        xaxis_title=results['x_var'],
                        yaxis_title=results['y_var'],
                        hovermode='closest',
                        height=500
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Métricas
                    st.subheader("📊 Métricas da Regressão")
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    with col1:
                        st.metric("R²", f"{results['r2']:.4f}")
                    with col2:
                        st.metric("RMSE", f"{results['rmse']:.4f}")
                    with col3:
                        st.metric("Coeficiente", f"{results['coefficient']:.4f}")
                    with col4:
                        st.metric("Intercepto", f"{results['intercept']:.4f}")
                    with col5:
                        st.metric("N° Amostras", results['n_samples'])
                    
                    # Análise de resíduos
                    st.subheader("📉 Análise de Resíduos")
                    
                    col_res1, col_res2 = st.columns(2)
                    
                    with col_res1:
                        # Gráfico de resíduos vs valores preditos
                        fig_res = go.Figure()
                        fig_res.add_trace(go.Scatter(
                            x=results['y_pred'], 
                            y=results['residuals'],
                            mode='markers',
                            marker=dict(size=8, color='purple', opacity=0.6)
                        ))
                        fig_res.add_hline(y=0, line_dash="dash", line_color="red", line_width=2)
                        fig_res.update_layout(
                            title="Resíduos vs Valores Preditos",
                            xaxis_title="Valores Preditos",
                            yaxis_title="Resíduos",
                            height=400
                        )
                        st.plotly_chart(fig_res, use_container_width=True)
                    
                    with col_res2:
                        # Histograma dos resíduos
                        fig_hist = go.Figure()
                        fig_hist.add_trace(go.Histogram(
                            x=results['residuals'],
                            nbinsx=20,
                            marker=dict(color='green', opacity=0.7)
                        ))
                        fig_hist.update_layout(
                            title="Distribuição dos Resíduos",
                            xaxis_title="Resíduos",
                            yaxis_title="Frequência",
                            height=400
                        )
                        st.plotly_chart(fig_hist, use_container_width=True)
                    
                    # Interpretação
                    st.subheader("💡 Interpretação")
                    
                    interpretation = f"""
                    **Equação da Regressão:** `{results['equation']}`
                    
                    **Coeficiente de Determinação (R²):** {results['r2']:.4f}
                    - O modelo explica **{results['r2']*100:.2f}%** da variabilidade em {results['y_var']}.
                    {'- ✅ Bom ajuste (R² > 0.7)' if results['r2'] > 0.7 else '- ⚠️ Ajuste moderado (0.5 < R² < 0.7)' if results['r2'] > 0.5 else '- ❌ Ajuste fraco (R² < 0.5)'}
                    
                    **Interpretação do Coeficiente:**
                    - Para cada unidade de aumento em **{results['x_var']}**, espera-se que **{results['y_var']}** {'aumente' if results['coefficient'] > 0 else 'diminua'} em **{abs(results['coefficient']):.4f}** unidades.
                    
                    **RMSE (Erro Médio Quadrático):** {results['rmse']:.4f}
                    - Em média, as previsões do modelo desviam **{results['rmse']:.4f}** unidades do valor real.
                    """
                    
                    st.markdown(interpretation)
            
            # Salvar análise
            if save_regression:
                results = st.session_state.get('regression_results', None)
                if results:
                    if save_analysis_to_db(project_name, "regression", results):
                        st.success("✅ Análise de regressão salva com sucesso no Supabase!")
                    else:
                        st.error("❌ Falha ao salvar a análise.")
                else:
                    st.warning("⚠️ Execute a regressão antes de salvar.")
            
            # Exportar resultados
            if export_regression:
                results = st.session_state.get('regression_results', None)
                if results:
                    # Criar DataFrame com resultados
                    export_df = pd.DataFrame({
                        results['x_var']: results['x_values'],
                        results['y_var']: results['y_values'],
                        'Valores_Preditos': results['y_pred'],
                        'Residuos': results['residuals']
                    })
                    
                    # Adicionar métricas como metadados
                    metrics_text = f"""
ANÁLISE DE REGRESSÃO LINEAR
============================
Variável Independente (X): {results['x_var']}
Variável Dependente (Y): {results['y_var']}

EQUAÇÃO: {results['equation']}

MÉTRICAS:
- R²: {results['r2']:.4f}
- RMSE: {results['rmse']:.4f}
- Coeficiente: {results['coefficient']:.4f}
- Intercepto: {results['intercept']:.4f}
- Número de Amostras: {results['n_samples']}

DADOS:
"""
                    
                    csv = metrics_text + "\n" + export_df.to_csv(index=False)
                    
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv.encode('utf-8'),
                        file_name=f"regressao_{results['x_var']}_vs_{results['y_var']}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("⚠️ Execute a regressão antes de exportar.")
        
        else:
            st.warning("⚠️ São necessárias pelo menos 2 variáveis numéricas para realizar a regressão.")
    else:
        st.info("📊 Carregue dados primeiro para realizar análise de regressão.")


#############################################################################################################################################################################################################################################################

# ========================= TAB 5: TESTES DE HIPÓTESES (COMPLETO) =========================
with tabs[4]:
    st.header("🔍 Testes de Hipóteses")
    
    # Verificar se há projeto selecionado
    project_name = st.session_state.get('project_name', None)
    
    if not project_name:
        st.warning("⚠️ Nenhum projeto selecionado. Por favor, selecione ou crie um projeto primeiro.")
        st.stop()
    
    # Botões de carregar e nova análise
    col_load, col_new = st.columns([1, 1])
    
    with col_load:
        if st.button("📂 Carregar Análise Salva", use_container_width=True, type="secondary", key="load_hypothesis"):
            if not supabase:
                st.error("❌ Conexão com Supabase não disponível.")
            else:
                try:
                    response = supabase.table('analyses').select('*').eq('project_name', project_name).eq('analysis_type', 'hypothesis_test').order('created_at', desc=True).limit(1).execute()
                    
                    if response.data and len(response.data) > 0:
                        loaded_data = response.data[0]['results']
                        st.session_state.hypothesis_results = loaded_data
                        st.success("✅ Teste de hipóteses carregado com sucesso!")
                        st.rerun()
                    else:
                        st.info("ℹ️ Nenhum teste de hipóteses salvo encontrado para este projeto.")
                except Exception as e:
                    st.error(f"Erro ao carregar dados: {str(e)}")
    
    with col_new:
        if st.button("🆕 Nova Análise", use_container_width=True, key="new_hypothesis"):
            if 'hypothesis_results' in st.session_state:
                del st.session_state.hypothesis_results
            st.rerun()
    
    st.divider()
    
    test_type = st.selectbox(
        "Tipo de Teste:",
        ["Teste t (1 amostra)", "Teste t (2 amostras)", "Teste t pareado",
         "Mann-Whitney U", "Wilcoxon", "Qui-Quadrado", "Fisher Exact"],
        key="test_type_select"
    )
    
    if data is not None:
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = data.select_dtypes(include=['object']).columns.tolist()
        
        # ============= TESTE T (1 AMOSTRA) =============
        if test_type == "Teste t (1 amostra)":
            st.info("**Teste t de 1 amostra:** Compara a média de uma amostra com um valor hipotético (μ₀)")
            
            if numeric_cols:
                value_col = st.selectbox("Variável numérica:", numeric_cols, key="t1_value_col")
                mu0 = st.number_input("Valor hipotético da média (μ₀):", value=0.0, key="t1_mu0")
                alpha = st.slider("Nível de significância (α):", 0.01, 0.10, 0.05, key="t1_alpha")
                
                col_exec, col_save, col_export = st.columns([1, 1, 1])
                
                with col_exec:
                    execute_test = st.button("🔄 Executar Teste", key="run_t1", use_container_width=True, type="primary")
                
                with col_save:
                    save_test = st.button("💾 Salvar", key="save_t1", use_container_width=True)
                
                with col_export:
                    export_test = st.button("📥 Exportar", key="export_t1", use_container_width=True)
                
                current_results = st.session_state.get('hypothesis_results') or {}
                if execute_test or (current_results.get('test_type') == test_type):
                    if execute_test:
                        sample_data = data[value_col].dropna()
                        t_stat, p_value = stats.ttest_1samp(sample_data, mu0)
                        
                        st.session_state.hypothesis_results = {
                            'test_type': test_type,
                            'value_col': value_col,
                            'mu0': float(mu0),
                            'alpha': float(alpha),
                            't_statistic': float(t_stat),
                            'p_value': float(p_value),
                            'sample_mean': float(sample_data.mean()),
                            'sample_std': float(sample_data.std()),
                            'n': int(len(sample_data)),
                            'data': sample_data.tolist(),
                            'conclusion': 'reject_h0' if p_value < alpha else 'fail_to_reject_h0'
                        }
                    
                    results = st.session_state.hypothesis_results
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Estatística t", f"{results['t_statistic']:.4f}")
                    col2.metric("Valor p", f"{results['p_value']:.4f}")
                    col3.metric("Média Amostral", f"{results['sample_mean']:.3f}")
                    
                    if results['conclusion'] == 'reject_h0':
                        st.error(f"**❌ Rejeitar H₀:** A média é significativamente diferente de {results['mu0']} (p={results['p_value']:.4f})")
                    else:
                        st.success(f"**✅ Não Rejeitar H₀:** Não há evidência de diferença significativa de {results['mu0']} (p={results['p_value']:.4f})")
                    
                    fig = go.Figure()
                    fig.add_trace(go.Histogram(x=results['data'], name='Dados', nbinsx=30))
                    fig.add_vline(x=results['sample_mean'], line_dash="dash", line_color="red", annotation_text="Média Amostral")
                    fig.add_vline(x=results['mu0'], line_dash="dot", line_color="blue", annotation_text="μ₀")
                    fig.update_layout(title="Distribuição dos Dados")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    if save_test:
                        if save_analysis_to_db(project_name, "hypothesis_test", results):
                            st.success("✅ Análise salva!")
                    
                    if export_test:
                        csv = f"Teste t (1 amostra)\nμ₀={results['mu0']}\nt={results['t_statistic']:.4f}\np={results['p_value']:.4f}\n\nDados:\n"
                        csv += pd.DataFrame({'Valores': results['data']}).to_csv(index=False)
                        st.download_button("📥 Download CSV", csv.encode('utf-8'), f"teste_t1_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
            else:
                st.warning("⚠️ Nenhuma variável numérica disponível.")
        
        # ============= TESTE T (2 AMOSTRAS) =============
        elif test_type == "Teste t (2 amostras)":
            st.info("**Teste t de 2 amostras independentes:** Compara as médias de dois grupos diferentes")
            
            if numeric_cols and categorical_cols:
                value_col = st.selectbox("Variável numérica:", numeric_cols, key="t2_value_col")
                group_col = st.selectbox("Variável de grupo:", categorical_cols, key="t2_group_col")
                
                groups = data[group_col].unique()
                if len(groups) >= 2:
                    group1 = st.selectbox("Grupo 1:", groups, key="t2_group1")
                    group2 = st.selectbox("Grupo 2:", [g for g in groups if g != group1], key="t2_group2")
                    alpha = st.slider("Nível de significância (α):", 0.01, 0.10, 0.05, key="t2_alpha")
                    
                    col_exec, col_save, col_export = st.columns([1, 1, 1])
                    
                    with col_exec:
                        execute_test = st.button("🔄 Executar Teste", key="run_t2", use_container_width=True, type="primary")
                    with col_save:
                        save_test = st.button("💾 Salvar", key="save_t2", use_container_width=True)
                    with col_export:
                        export_test = st.button("📥 Exportar", key="export_t2", use_container_width=True)
                    
                    current_results = st.session_state.get('hypothesis_results') or {}
                    if execute_test or (current_results.get('test_type') == test_type):
                        if execute_test:
                            data1 = data[data[group_col] == group1][value_col].dropna()
                            data2 = data[data[group_col] == group2][value_col].dropna()
                            
                            t_stat, p_value = stats.ttest_ind(data1, data2)
                            levene_stat, levene_p = stats.levene(data1, data2)
                            
                            pooled_std = np.sqrt(((len(data1)-1)*data1.std()**2 + (len(data2)-1)*data2.std()**2) / (len(data1)+len(data2)-2))
                            cohens_d = (data1.mean() - data2.mean()) / pooled_std
                            
                            st.session_state.hypothesis_results = {
                                'test_type': test_type,
                                'value_col': value_col,
                                'group_col': group_col,
                                'group1': str(group1),
                                'group2': str(group2),
                                'alpha': float(alpha),
                                't_statistic': float(t_stat),
                                'p_value': float(p_value),
                                'mean_group1': float(data1.mean()),
                                'mean_group2': float(data2.mean()),
                                'std_group1': float(data1.std()),
                                'std_group2': float(data2.std()),
                                'n_group1': int(len(data1)),
                                'n_group2': int(len(data2)),
                                'mean_difference': float(data1.mean() - data2.mean()),
                                'levene_p_value': float(levene_p),
                                'cohens_d': float(cohens_d),
                                'data1': data1.tolist(),
                                'data2': data2.tolist(),
                                'conclusion': 'reject_h0' if p_value < alpha else 'fail_to_reject_h0'
                            }
                        
                        results = st.session_state.hypothesis_results
                        
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Estatística t", f"{results['t_statistic']:.4f}")
                        col2.metric("Valor p", f"{results['p_value']:.4f}")
                        col3.metric("Diferença", f"{results['mean_difference']:.3f}")
                        col4.metric("Cohen's d", f"{results['cohens_d']:.3f}")
                        
                        if results['conclusion'] == 'reject_h0':
                            st.error(f"**❌ Rejeitar H₀:** Diferença significativa (p={results['p_value']:.4f})")
                        else:
                            st.success(f"**✅ Não Rejeitar H₀:** Sem diferença significativa (p={results['p_value']:.4f})")
                        
                        fig = go.Figure()
                        fig.add_trace(go.Box(y=results['data1'], name=results['group1'], boxmean='sd'))
                        fig.add_trace(go.Box(y=results['data2'], name=results['group2'], boxmean='sd'))
                        fig.update_layout(title=f"Comparação: {results['group1']} vs {results['group2']}")
                        st.plotly_chart(fig, use_container_width=True)
                        
                        if save_test:
                            if save_analysis_to_db(project_name, "hypothesis_test", results):
                                st.success("✅ Análise salva!")
                        
                        if export_test:
                            csv = f"Teste t (2 amostras)\nGrupo 1: {results['group1']}\nGrupo 2: {results['group2']}\nt={results['t_statistic']:.4f}\np={results['p_value']:.4f}\n\n"
                            max_len = max(len(results['data1']), len(results['data2']))
                            df = pd.DataFrame({
                                results['group1']: results['data1'] + [None]*(max_len-len(results['data1'])),
                                results['group2']: results['data2'] + [None]*(max_len-len(results['data2']))
                            })
                            csv += df.to_csv(index=False)
                            st.download_button("📥 Download CSV", csv.encode('utf-8'), f"teste_t2_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
                else:
                    st.warning("⚠️ São necessários pelo menos 2 grupos.")
            else:
                st.warning("⚠️ São necessárias variáveis numéricas e categóricas.")
        
        # ============= TESTE T PAREADO =============
        elif test_type == "Teste t pareado":
            st.info("**Teste t pareado:** Compara duas medidas do mesmo grupo (antes/depois, pré/pós)")
            
            if len(numeric_cols) >= 2:
                col1_select = st.selectbox("Primeira medida (ex: Antes):", numeric_cols, key="tp_col1")
                col2_select = st.selectbox("Segunda medida (ex: Depois):", [c for c in numeric_cols if c != col1_select], key="tp_col2")
                alpha = st.slider("Nível de significância (α):", 0.01, 0.10, 0.05, key="tp_alpha")
                
                col_exec, col_save, col_export = st.columns([1, 1, 1])
                
                with col_exec:
                    execute_test = st.button("🔄 Executar Teste", key="run_tp", use_container_width=True, type="primary")
                with col_save:
                    save_test = st.button("💾 Salvar", key="save_tp", use_container_width=True)
                with col_export:
                    export_test = st.button("📥 Exportar", key="export_tp", use_container_width=True)
                
                current_results = st.session_state.get('hypothesis_results') or {}
                if execute_test or (current_results.get('test_type') == test_type):
                    if execute_test:
                        paired_data = data[[col1_select, col2_select]].dropna()
                        data1 = paired_data[col1_select]
                        data2 = paired_data[col2_select]
                        
                        t_stat, p_value = stats.ttest_rel(data1, data2)
                        differences = data2 - data1
                        
                        st.session_state.hypothesis_results = {
                            'test_type': test_type,
                            'col1': col1_select,
                            'col2': col2_select,
                            'alpha': float(alpha),
                            't_statistic': float(t_stat),
                            'p_value': float(p_value),
                            'mean_col1': float(data1.mean()),
                            'mean_col2': float(data2.mean()),
                            'mean_difference': float(differences.mean()),
                            'std_difference': float(differences.std()),
                            'n': int(len(data1)),
                            'data1': data1.tolist(),
                            'data2': data2.tolist(),
                            'differences': differences.tolist(),
                            'conclusion': 'reject_h0' if p_value < alpha else 'fail_to_reject_h0'
                        }
                    
                    results = st.session_state.hypothesis_results
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Estatística t", f"{results['t_statistic']:.4f}")
                    col2.metric("Valor p", f"{results['p_value']:.4f}")
                    col3.metric("Diferença Média", f"{results['mean_difference']:.3f}")
                    
                    if results['conclusion'] == 'reject_h0':
                        st.error(f"**❌ Rejeitar H₀:** Há diferença significativa entre as medidas (p={results['p_value']:.4f})")
                    else:
                        st.success(f"**✅ Não Rejeitar H₀:** Não há diferença significativa (p={results['p_value']:.4f})")
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=list(range(len(results['data1']))), y=results['data1'], mode='markers+lines', name=results['col1']))
                    fig.add_trace(go.Scatter(x=list(range(len(results['data2']))), y=results['data2'], mode='markers+lines', name=results['col2']))
                    fig.update_layout(title="Comparação Pareada", xaxis_title="Observação", yaxis_title="Valor")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    if save_test:
                        if save_analysis_to_db(project_name, "hypothesis_test", results):
                            st.success("✅ Análise salva!")
                    
                    if export_test:
                        csv = f"Teste t Pareado\n{results['col1']} vs {results['col2']}\nt={results['t_statistic']:.4f}\np={results['p_value']:.4f}\n\n"
                        df = pd.DataFrame({
                            results['col1']: results['data1'],
                            results['col2']: results['data2'],
                            'Diferença': results['differences']
                        })
                        csv += df.to_csv(index=False)
                        st.download_button("📥 Download CSV", csv.encode('utf-8'), f"teste_pareado_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
            else:
                st.warning("⚠️ São necessárias pelo menos 2 variáveis numéricas.")
        
        # ============= MANN-WHITNEY U =============
        elif test_type == "Mann-Whitney U":
            st.info("**Teste de Mann-Whitney U:** Alternativa não-paramétrica ao teste t de 2 amostras")
            
            if numeric_cols and categorical_cols:
                value_col = st.selectbox("Variável numérica:", numeric_cols, key="mw_value_col")
                group_col = st.selectbox("Variável de grupo:", categorical_cols, key="mw_group_col")
                
                groups = data[group_col].unique()
                if len(groups) >= 2:
                    group1 = st.selectbox("Grupo 1:", groups, key="mw_group1")
                    group2 = st.selectbox("Grupo 2:", [g for g in groups if g != group1], key="mw_group2")
                    alpha = st.slider("Nível de significância (α):", 0.01, 0.10, 0.05, key="mw_alpha")
                    
                    col_exec, col_save, col_export = st.columns([1, 1, 1])
                    
                    with col_exec:
                        execute_test = st.button("🔄 Executar Teste", key="run_mw", use_container_width=True, type="primary")
                    with col_save:
                        save_test = st.button("💾 Salvar", key="save_mw", use_container_width=True)
                    with col_export:
                        export_test = st.button("📥 Exportar", key="export_mw", use_container_width=True)
                    
                    current_results = st.session_state.get('hypothesis_results') or {}
                    if execute_test or (current_results.get('test_type') == test_type):
                        if execute_test:
                            data1 = data[data[group_col] == group1][value_col].dropna()
                            data2 = data[data[group_col] == group2][value_col].dropna()
                            
                            u_stat, p_value = stats.mannwhitneyu(data1, data2, alternative='two-sided')
                            
                            st.session_state.hypothesis_results = {
                                'test_type': test_type,
                                'value_col': value_col,
                                'group_col': group_col,
                                'group1': str(group1),
                                'group2': str(group2),
                                'alpha': float(alpha),
                                'u_statistic': float(u_stat),
                                'p_value': float(p_value),
                                'median_group1': float(data1.median()),
                                'median_group2': float(data2.median()),
                                'n_group1': int(len(data1)),
                                'n_group2': int(len(data2)),
                                'data1': data1.tolist(),
                                'data2': data2.tolist(),
                                'conclusion': 'reject_h0' if p_value < alpha else 'fail_to_reject_h0'
                            }
                        
                        results = st.session_state.hypothesis_results
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Estatística U", f"{results['u_statistic']:.0f}")
                        col2.metric("Valor p", f"{results['p_value']:.4f}")
                        col3.metric("Diferença Medianas", f"{results['median_group1'] - results['median_group2']:.3f}")
                        
                        if results['conclusion'] == 'reject_h0':
                            st.error(f"**❌ Rejeitar H₀:** Distribuições são diferentes (p={results['p_value']:.4f})")
                        else:
                            st.success(f"**✅ Não Rejeitar H₀:** Distribuições não diferem significativamente (p={results['p_value']:.4f})")
                        
                        fig = go.Figure()
                        fig.add_trace(go.Box(y=results['data1'], name=results['group1']))
                        fig.add_trace(go.Box(y=results['data2'], name=results['group2']))
                        fig.update_layout(title="Teste de Mann-Whitney U")
                        st.plotly_chart(fig, use_container_width=True)
                        
                        if save_test:
                            if save_analysis_to_db(project_name, "hypothesis_test", results):
                                st.success("✅ Análise salva!")
                        
                        if export_test:
                            csv = f"Mann-Whitney U\nU={results['u_statistic']:.0f}\np={results['p_value']:.4f}\n\n"
                            max_len = max(len(results['data1']), len(results['data2']))
                            df = pd.DataFrame({
                                results['group1']: results['data1'] + [None]*(max_len-len(results['data1'])),
                                results['group2']: results['data2'] + [None]*(max_len-len(results['data2']))
                            })
                            csv += df.to_csv(index=False)
                            st.download_button("📥 Download CSV", csv.encode('utf-8'), f"mann_whitney_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
        
        # ============= WILCOXON =============
        elif test_type == "Wilcoxon":
            st.info("**Teste de Wilcoxon:** Alternativa não-paramétrica ao teste t pareado")
            
            if len(numeric_cols) >= 2:
                col1_select = st.selectbox("Primeira medida:", numeric_cols, key="w_col1")
                col2_select = st.selectbox("Segunda medida:", [c for c in numeric_cols if c != col1_select], key="w_col2")
                alpha = st.slider("Nível de significância (α):", 0.01, 0.10, 0.05, key="w_alpha")
                
                col_exec, col_save, col_export = st.columns([1, 1, 1])
                
                with col_exec:
                    execute_test = st.button("🔄 Executar Teste", key="run_w", use_container_width=True, type="primary")
                with col_save:
                    save_test = st.button("💾 Salvar", key="save_w", use_container_width=True)
                with col_export:
                    export_test = st.button("📥 Exportar", key="export_w", use_container_width=True)
                
                current_results = st.session_state.get('hypothesis_results') or {}
                if execute_test or (current_results.get('test_type') == test_type):
                    if execute_test:
                        paired_data = data[[col1_select, col2_select]].dropna()
                        data1 = paired_data[col1_select]
                        data2 = paired_data[col2_select]
                        
                        w_stat, p_value = stats.wilcoxon(data1, data2)
                        
                        st.session_state.hypothesis_results = {
                            'test_type': test_type,
                            'col1': col1_select,
                            'col2': col2_select,
                            'alpha': float(alpha),
                            'w_statistic': float(w_stat),
                            'p_value': float(p_value),
                            'median_col1': float(data1.median()),
                            'median_col2': float(data2.median()),
                            'n': int(len(data1)),
                            'data1': data1.tolist(),
                            'data2': data2.tolist(),
                            'conclusion': 'reject_h0' if p_value < alpha else 'fail_to_reject_h0'
                        }
                    
                    results = st.session_state.hypothesis_results
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Estatística W", f"{results['w_statistic']:.0f}")
                    col2.metric("Valor p", f"{results['p_value']:.4f}")
                    col3.metric("Diferença Medianas", f"{results['median_col2'] - results['median_col1']:.3f}")
                    
                    if results['conclusion'] == 'reject_h0':
                        st.error(f"**❌ Rejeitar H₀:** Há diferença significativa (p={results['p_value']:.4f})")
                    else:
                        st.success(f"**✅ Não Rejeitar H₀:** Não há diferença significativa (p={results['p_value']:.4f})")
                    
                    fig = go.Figure()
                    fig.add_trace(go.Box(y=results['data1'], name=results['col1']))
                    fig.add_trace(go.Box(y=results['data2'], name=results['col2']))
                    fig.update_layout(title="Teste de Wilcoxon")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    if save_test:
                        if save_analysis_to_db(project_name, "hypothesis_test", results):
                            st.success("✅ Análise salva!")
                    
                    if export_test:
                        csv = f"Wilcoxon\nW={results['w_statistic']:.0f}\np={results['p_value']:.4f}\n\n"
                        df = pd.DataFrame({
                            results['col1']: results['data1'],
                            results['col2']: results['data2']
                        })
                        csv += df.to_csv(index=False)
                        st.download_button("📥 Download CSV", csv.encode('utf-8'), f"wilcoxon_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
        
        # ============= QUI-QUADRADO =============
        elif test_type == "Qui-Quadrado":
            st.info("**Teste Qui-Quadrado:** Testa independência entre duas variáveis categóricas")
            
            if len(categorical_cols) >= 2:
                cat1 = st.selectbox("Primeira variável categórica:", categorical_cols, key="chi_cat1")
                cat2 = st.selectbox("Segunda variável categórica:", [c for c in categorical_cols if c != cat1], key="chi_cat2")
                alpha = st.slider("Nível de significância (α):", 0.01, 0.10, 0.05, key="chi_alpha")
                
                col_exec, col_save, col_export = st.columns([1, 1, 1])
                
                with col_exec:
                    execute_test = st.button("🔄 Executar Teste", key="run_chi", use_container_width=True, type="primary")
                with col_save:
                    save_test = st.button("💾 Salvar", key="save_chi", use_container_width=True)
                with col_export:
                    export_test = st.button("📥 Exportar", key="export_chi", use_container_width=True)
                
                current_results = st.session_state.get('hypothesis_results') or {}
                if execute_test or (current_results.get('test_type') == test_type):
                    if execute_test:
                        contingency_table = pd.crosstab(data[cat1], data[cat2])
                        chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)
                        
                        st.session_state.hypothesis_results = {
                            'test_type': test_type,
                            'cat1': cat1,
                            'cat2': cat2,
                            'alpha': float(alpha),
                            'chi2_statistic': float(chi2),
                            'p_value': float(p_value),
                            'degrees_of_freedom': int(dof),
                            'contingency_table': contingency_table.to_dict(),
                            'conclusion': 'reject_h0' if p_value < alpha else 'fail_to_reject_h0'
                        }
                    
                    results = st.session_state.hypothesis_results
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("χ²", f"{results['chi2_statistic']:.4f}")
                    col2.metric("Valor p", f"{results['p_value']:.4f}")
                    col3.metric("Graus de Liberdade", results['degrees_of_freedom'])
                    
                    if results['conclusion'] == 'reject_h0':
                        st.error(f"**❌ Rejeitar H₀:** As variáveis são dependentes (p={results['p_value']:.4f})")
                    else:
                        st.success(f"**✅ Não Rejeitar H₀:** As variáveis são independentes (p={results['p_value']:.4f})")
                    
                    st.subheader("Tabela de Contingência")
                    contingency_df = pd.DataFrame(results['contingency_table'])
                    st.dataframe(contingency_df)
                    
                    if save_test:
                        if save_analysis_to_db(project_name, "hypothesis_test", results):
                            st.success("✅ Análise salva!")
                    
                    if export_test:
                        csv = f"Qui-Quadrado\nχ²={results['chi2_statistic']:.4f}\np={results['p_value']:.4f}\n\nTabela de Contingência:\n"
                        csv += contingency_df.to_csv()
                        st.download_button("📥 Download CSV", csv.encode('utf-8'), f"qui_quadrado_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
            else:
                st.warning("⚠️ São necessárias pelo menos 2 variáveis categóricas.")
        
        # ============= FISHER EXACT =============
        elif test_type == "Fisher Exact":
            st.info("**Teste Exato de Fisher:** Alternativa ao Qui-Quadrado para amostras pequenas (tabelas 2x2)")
            
            if len(categorical_cols) >= 2:
                cat1 = st.selectbox("Primeira variável categórica:", categorical_cols, key="f_cat1")
                cat2 = st.selectbox("Segunda variável categórica:", [c for c in categorical_cols if c != cat1], key="f_cat2")
                alpha = st.slider("Nível de significância (α):", 0.01, 0.10, 0.05, key="f_alpha")
                
                col_exec, col_save, col_export = st.columns([1, 1, 1])
                
                with col_exec:
                    execute_test = st.button("🔄 Executar Teste", key="run_f", use_container_width=True, type="primary")
                with col_save:
                    save_test = st.button("💾 Salvar", key="save_f", use_container_width=True)
                with col_export:
                    export_test = st.button("📥 Exportar", key="export_f", use_container_width=True)
                
                current_results = st.session_state.get('hypothesis_results') or {}
                if execute_test or (current_results.get('test_type') == test_type):
                    if execute_test:
                        contingency_table = pd.crosstab(data[cat1], data[cat2])
                        
                        if contingency_table.shape == (2, 2):
                            table_array = contingency_table.values
                            oddsratio, p_value = stats.fisher_exact(table_array)
                            
                            st.session_state.hypothesis_results = {
                                'test_type': test_type,
                                'cat1': cat1,
                                'cat2': cat2,
                                'alpha': float(alpha),
                                'odds_ratio': float(oddsratio),
                                'p_value': float(p_value),
                                'contingency_table': contingency_table.to_dict(),
                                'conclusion': 'reject_h0' if p_value < alpha else 'fail_to_reject_h0'
                            }
                        else:
                            st.error("⚠️ O teste exato de Fisher requer uma tabela 2x2. Use Qui-Quadrado para tabelas maiores.")
                            st.session_state.hypothesis_results = None
                    
                    results = st.session_state.get('hypothesis_results')
                    
                    if results:
                        col1, col2 = st.columns(2)
                        col1.metric("Odds Ratio", f"{results['odds_ratio']:.4f}")
                        col2.metric("Valor p", f"{results['p_value']:.4f}")
                        
                        if results['conclusion'] == 'reject_h0':
                            st.error(f"**❌ Rejeitar H₀:** Há associação significativa (p={results['p_value']:.4f})")
                        else:
                            st.success(f"**✅ Não Rejeitar H₀:** Não há associação significativa (p={results['p_value']:.4f})")
                        
                        st.subheader("Tabela de Contingência 2x2")
                        contingency_df = pd.DataFrame(results['contingency_table'])
                        st.dataframe(contingency_df)
                        
                        if save_test:
                            if save_analysis_to_db(project_name, "hypothesis_test", results):
                                st.success("✅ Análise salva!")
                        
                        if export_test:
                            csv = f"Fisher Exact\nOdds Ratio={results['odds_ratio']:.4f}\np={results['p_value']:.4f}\n\nTabela:\n"
                            csv += contingency_df.to_csv()
                            st.download_button("📥 Download CSV", csv.encode('utf-8'), f"fisher_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
            else:
                st.warning("⚠️ São necessárias pelo menos 2 variáveis categóricas.")
    
    else:
        st.info("📊 Carregue dados primeiro para realizar testes de hipóteses.")



#######################################################################################################################################################################################################################################################################

# ========================= TAB 6: NORMALIDADE =========================
with tabs[5]:
    st.header("📐 Testes de Normalidade")
    
    if data is not None:
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        
        if numeric_cols:
            selected_col = st.selectbox("Selecione a variável:", numeric_cols, key="norm_col")
            
            if st.button("Executar Testes de Normalidade", key="run_normality"):
                test_data = data[selected_col].dropna()
                
                # Múltiplos testes
                tests_results = {}
                
                # Shapiro-Wilk
                if len(test_data) <= 5000:
                    stat_sw, p_sw = shapiro(test_data)
                    tests_results['Shapiro-Wilk'] = {'statistic': stat_sw, 'p_value': p_sw}
                
                # Kolmogorov-Smirnov
                stat_ks, p_ks = kstest(test_data, 'norm', args=(test_data.mean(), test_data.std()))
                tests_results['Kolmogorov-Smirnov'] = {'statistic': stat_ks, 'p_value': p_ks}
                
                # Anderson-Darling
                result_ad = anderson(test_data, dist='norm')
                tests_results['Anderson-Darling'] = {
                    'statistic': result_ad.statistic,
                    'critical_values': dict(zip(result_ad.significance_level, result_ad.critical_values))
                }
                
                # D'Agostino-Pearson
                stat_dp, p_dp = normaltest(test_data)
                tests_results["D'Agostino-Pearson"] = {'statistic': stat_dp, 'p_value': p_dp}
                
                # Exibir resultados
                st.subheader("📊 Resultados dos Testes")
                
                for test_name, results in tests_results.items():
                    with st.expander(f"{test_name}"):
                        if 'p_value' in results:
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Estatística", f"{results['statistic']:.4f}")
                            with col2:
                                st.metric("Valor p", f"{results['p_value']:.4f}")
                            
                            if results['p_value'] > 0.05:
                                st.success("✅ Dados seguem distribuição normal (p > 0.05)")
                            else:
                                st.warning("⚠️ Dados NÃO seguem distribuição normal (p ≤ 0.05)")
                        else:
                            st.write(f"Estatística: {results['statistic']:.4f}")
                            st.write("Valores Críticos:", results['critical_values'])
                
                # Visualizações
                col1, col2 = st.columns(2)
                
                with col1:
                    # Histograma com curva normal
                    fig = go.Figure()
                    fig.add_trace(go.Histogram(x=test_data, nbinsx=30, name='Dados',
                                              histnorm='probability density'))
                    
                    # Curva normal teórica
                    x_range = np.linspace(test_data.min(), test_data.max(), 100)
                    y_normal = stats.norm.pdf(x_range, test_data.mean(), test_data.std())
                    fig.add_trace(go.Scatter(x=x_range, y=y_normal, mode='lines',
                                            name='Normal Teórica', line=dict(color='red')))
                    
                    fig.update_layout(title="Histograma vs Normal")
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Q-Q Plot
                    theoretical_quantiles = stats.norm.ppf(np.linspace(0.01, 0.99, len(test_data)))
                    sample_quantiles = np.sort(test_data)
                    
                    fig_qq = go.Figure()
                    fig_qq.add_trace(go.Scatter(x=theoretical_quantiles, y=sample_quantiles,
                                               mode='markers', name='Dados'))
                    fig_qq.add_trace(go.Scatter(x=[theoretical_quantiles.min(), theoretical_quantiles.max()],
                                               y=[theoretical_quantiles.min(), theoretical_quantiles.max()],
                                               mode='lines', name='Linha de Referência',
                                               line=dict(color='red', dash='dash')))
                    
                    fig_qq.update_layout(title="Q-Q Plot",
                                        xaxis_title="Quantis Teóricos",
                                        yaxis_title="Quantis Amostrais")
                    st.plotly_chart(fig_qq, use_container_width=True)

# ========================= TAB 7: CORRELAÇÃO =========================
with tabs[6]:
    st.header("🔗 Análise de Correlação")
    
    if data is not None:
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) >= 2:
            selected_cols = st.multiselect(
                "Selecione as variáveis:",
                numeric_cols,
                default=numeric_cols[:5] if len(numeric_cols) > 5 else numeric_cols,
                key="corr_cols"
            )
            
            if len(selected_cols) >= 2:
                # Métodos de correlação
                corr_method = st.selectbox(
                    "Método de Correlação:",
                    ["Pearson", "Spearman", "Kendall"]
                )
                
                if st.button("Calcular Correlação", key="calc_corr"):
                    # Calcular matriz
                    if corr_method == "Pearson":
                        corr_matrix = data[selected_cols].corr(method='pearson')
                    elif corr_method == "Spearman":
                        corr_matrix = data[selected_cols].corr(method='spearman')
                    else:
                        corr_matrix = data[selected_cols].corr(method='kendall')
                    
                    # Heatmap
                    fig = px.imshow(corr_matrix,
                                   labels=dict(color="Correlação"),
                                   x=selected_cols,
                                   y=selected_cols,
                                   color_continuous_scale='RdBu',
                                   zmin=-1, zmax=1)
                    
                    fig.update_layout(title=f"Matriz de Correlação ({corr_method})")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Correlações significativas
                    st.subheader("📊 Correlações Significativas")
                    threshold = st.slider("Threshold:", 0.0, 1.0, 0.7)
                    
                    strong_corr = []
                    for i in range(len(corr_matrix.columns)):
                        for j in range(i+1, len(corr_matrix.columns)):
                            if abs(corr_matrix.iloc[i, j]) >= threshold:
                                strong_corr.append({
                                    'Var 1': corr_matrix.columns[i],
                                    'Var 2': corr_matrix.columns[j],
                                    'Correlação': corr_matrix.iloc[i, j],
                                    'Força': 'Forte' if abs(corr_matrix.iloc[i, j]) >= 0.7 else 'Moderada'
                                })
                    
                    if strong_corr:
                        st.dataframe(pd.DataFrame(strong_corr), use_container_width=True)

# ========================= TAB 8: BOX PLOT & OUTLIERS =========================
with tabs[7]:
    st.header("📊 Box Plot e Análise de Outliers")
    
    if data is not None:
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        
        if numeric_cols:
            selected_cols = st.multiselect(
                "Selecione as variáveis:",
                numeric_cols,
                default=numeric_cols[:3] if len(numeric_cols) > 3 else numeric_cols,
                key="box_cols"
            )
            
            if selected_cols and st.button("Gerar Box Plots", key="gen_box"):
                # Box plots
                fig = go.Figure()
                
                outliers_summary = []
                
                for col in selected_cols:
                    col_data = data[col].dropna()
                    
                    # Calcular outliers usando IQR
                    Q1 = col_data.quantile(0.25)
                    Q3 = col_data.quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    
                    outliers = col_data[(col_data < lower_bound) | (col_data > upper_bound)]
                    
                    fig.add_trace(go.Box(y=col_data, name=col))
                    
                    outliers_summary.append({
                        'Variável': col,
                        'Q1': Q1,
                        'Q3': Q3,
                        'IQR': IQR,
                        'Limite Inferior': lower_bound,
                        'Limite Superior': upper_bound,
                        'Outliers': len(outliers),
                        '% Outliers': (len(outliers) / len(col_data) * 100)
                    })
                
                fig.update_layout(title="Box Plots - Análise de Outliers", height=500)
                st.plotly_chart(fig, use_container_width=True)
                
                # Resumo de outliers
                st.subheader("📋 Resumo de Outliers")
                outliers_df = pd.DataFrame(outliers_summary)
                st.dataframe(outliers_df, use_container_width=True)
                
                # Tratamento de outliers
                st.subheader("🔧 Tratamento de Outliers")
                treatment = st.selectbox(
                    "Método de tratamento:",
                    ["Nenhum", "Remover", "Capping (Limitar)", "Transformação Log", "Z-Score"]
                )
                
                if treatment != "Nenhum" and st.button("Aplicar Tratamento"):
                    treated_data = data.copy()
                    
                    for col in selected_cols:
                        if treatment == "Remover":
                            Q1 = treated_data[col].quantile(0.25)
                            Q3 = treated_data[col].quantile(0.75)
                            IQR = Q3 - Q1
                            treated_data = treated_data[
                                (treated_data[col] >= Q1 - 1.5 * IQR) &
                                (treated_data[col] <= Q3 + 1.5 * IQR)
                            ]
                        elif treatment == "Capping":
                            Q1 = treated_data[col].quantile(0.25)
                            Q3 = treated_data[col].quantile(0.75)
                            IQR = Q3 - Q1
                            lower = Q1 - 1.5 * IQR
                            upper = Q3 + 1.5 * IQR
                            treated_data[col] = treated_data[col].clip(lower=lower, upper=upper)
                        elif treatment == "Transformação Log":
                            treated_data[col] = np.log1p(treated_data[col])
                        elif treatment == "Z-Score":
                            z_scores = np.abs(stats.zscore(treated_data[col].dropna()))
                            treated_data = treated_data[z_scores < 3]
                    
                    st.success(f"✅ Tratamento '{treatment}' aplicado!")
                    st.session_state.treated_data = treated_data

# ========================= TAB 9: CAPACIDADE =========================
with tabs[8]:
    st.header("⚙️ Análise de Capacidade do Processo")
    
    if data is not None:
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        
        if numeric_cols:
            selected_col = st.selectbox("Variável do processo:", numeric_cols, key="cap_col")
            
            col1, col2 = st.columns(2)
            with col1:
                lsl = st.number_input("LSL (Limite Inferior):", value=0.0)
            with col2:
                usl = st.number_input("USL (Limite Superior):", value=100.0)
            
            if st.button("Calcular Capacidade", key="calc_cap") and usl > lsl:
                process_data = data[selected_col].dropna()
                
                # Cálculos
                mean = process_data.mean()
                std = process_data.std()
                
                # Índices de capacidade
                cp = (usl - lsl) / (6 * std)
                cpu = (usl - mean) / (3 * std)
                cpl = (mean - lsl) / (3 * std)
                cpk = min(cpu, cpl)
                
                # Índices de performance
                pp = (usl - lsl) / (6 * process_data.std(ddof=1))
                ppu = (usl - mean) / (3 * process_data.std(ddof=1))
                ppl = (mean - lsl) / (3 * process_data.std(ddof=1))
                ppk = min(ppu, ppl)
                
                # PPM
                prob_below_lsl = stats.norm.cdf(lsl, mean, std)
                prob_above_usl = 1 - stats.norm.cdf(usl, mean, std)
                ppm_total = (prob_below_lsl + prob_above_usl) * 1_000_000
                
                # Nível sigma
                sigma_level = 3 * cpk
                
                # Métricas
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Cp", f"{cp:.3f}")
                    st.metric("Pp", f"{pp:.3f}")
                
                with col2:
                    st.metric("Cpk", f"{cpk:.3f}")
                    st.metric("Ppk", f"{ppk:.3f}")
                
                with col3:
                    st.metric("PPM Total", f"{ppm_total:.0f}")
                    st.metric("Nível Sigma", f"{sigma_level:.1f}σ")
                
                with col4:
                    # Interpretação
                    if cpk >= 1.33:
                        st.success("✅ Processo Capaz")
                    elif cpk >= 1.0:
                        st.warning("⚠️ Marginalmente Capaz")
                    else:
                        st.error("❌ Não Capaz")
                
                # Gráfico
                fig = go.Figure()
                
                # Histograma
                fig.add_trace(go.Histogram(x=process_data, nbinsx=30, name='Dados',
                                          histnorm='probability density'))
                
                # Curva normal
                x_range = np.linspace(process_data.min(), process_data.max(), 100)
                y_normal = stats.norm.pdf(x_range, mean, std)
                fig.add_trace(go.Scatter(x=x_range, y=y_normal, mode='lines',
                                        name='Distribuição Normal', line=dict(color='red')))
                
                # Limites
                fig.add_vline(x=lsl, line_dash="dash", line_color="red", annotation_text=f"LSL: {lsl}")
                fig.add_vline(x=usl, line_dash="dash", line_color="red", annotation_text=f"USL: {usl}")
                fig.add_vline(x=mean, line_dash="dash", line_color="green", annotation_text=f"Média: {mean:.2f}")
                
                fig.update_layout(title="Análise de Capacidade do Processo", height=500)
                st.plotly_chart(fig, use_container_width=True)

# ========================= TAB 10: ANOVA =========================
with tabs[9]:
    st.header("🎲 ANOVA - Análise de Variância")
    
    if data is not None:
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = data.select_dtypes(include=['object']).columns.tolist()
        
        if numeric_cols and categorical_cols:
            response_var = st.selectbox("Variável resposta:", numeric_cols, key="anova_resp")
            factor_var = st.selectbox("Fator:", categorical_cols, key="anova_factor")
            
            if st.button("Executar ANOVA", key="run_anova"):
                # Preparar dados
                groups = []
                labels = []
                
                for group in data[factor_var].unique():
                    group_data = data[data[factor_var] == group][response_var].dropna()
                    if len(group_data) > 0:
                        groups.append(group_data)
                        labels.append(group)
                
                if len(groups) >= 2:
                    # ANOVA
                    f_stat, p_value = f_oneway(*groups)
                    
                    # Tabela ANOVA
                    total_mean = data[response_var].mean()
                    sst = sum([(x - total_mean)**2 for group in groups for x in group])
                    ssb = sum([len(group) * (group.mean() - total_mean)**2 for group in groups])
                    ssw = sst - ssb
                    
                    df_between = len(groups) - 1
                    df_within = sum([len(g) - 1 for g in groups])
                    df_total = df_between + df_within
                    
                    msb = ssb / df_between
                    msw = ssw / df_within
                    
                    # Resultados
                    st.subheader("📊 Tabela ANOVA")
                    
                    anova_table = pd.DataFrame({
                        'Fonte': ['Entre Grupos', 'Dentro dos Grupos', 'Total'],
                        'SQ': [ssb, ssw, sst],
                        'GL': [df_between, df_within, df_total],
                        'QM': [msb, msw, '-'],
                        'F': [f_stat, '-', '-'],
                        'p-valor': [p_value, '-', '-']
                    })
                    
                    st.dataframe(anova_table, use_container_width=True)
                    
                    # Interpretação
                    alpha = 0.05
                    if p_value < alpha:
                        st.error(f"Rejeitar H₀: Existe diferença significativa entre os grupos (p={p_value:.4f} < {alpha})")
                    else:
                        st.success(f"Não rejeitar H₀: Não há diferença significativa (p={p_value:.4f} ≥ {alpha})")
                    
                    # Box plots
                    fig = go.Figure()
                    for group_data, label in zip(groups, labels):
                        fig.add_trace(go.Box(y=group_data, name=label))
                    
                    fig.update_layout(title=f"ANOVA: {response_var} por {factor_var}")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Post-hoc (Tukey)
                    if p_value < alpha and st.checkbox("Executar teste Post-hoc (Tukey)"):
                        from scipy.stats import tukey_hsd
                        
                        result = tukey_hsd(*groups)
                        st.subheader("Teste de Tukey HSD")
                        st.dataframe(pd.DataFrame(result), use_container_width=True)

# ========================= TAB 11: 5 PORQUÊS =========================
with tabs[10]:
    st.header("❓ Análise dos 5 Porquês")
    
    problem = st.text_area("Problema:", height=100)
    
    whys = []
    for i in range(5):
        why = st.text_area(f"Por quê {i+1}?", key=f"why_{i}", height=80)
        whys.append(why)
    
    root_cause = st.text_area("Causa Raiz Identificada:", height=100)
    action_plan = st.text_area("Plano de Ação:", height=100)
    
    if st.button("💾 Salvar 5 Porquês", key="save_5why"):
        analysis = {
            "problem": problem,
            "whys": whys,
            "root_cause": root_cause,
            "action_plan": action_plan
        }
        
        if save_analysis_to_db(project_name, "5_whys", analysis):
            st.success("✅ Análise salva!")

# ========================= TAB 12: FMEA =========================
with tabs[11]:
    st.header("📋 FMEA - Análise de Modo e Efeito de Falha")
    
    with st.form("fmea_form"):
        st.subheader("Adicionar Modo de Falha")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            process_step = st.text_input("Etapa do Processo")
            failure_mode = st.text_input("Modo de Falha")
            failure_effect = st.text_area("Efeito da Falha")
        
        with col2:
            severity = st.slider("Severidade (1-10)", 1, 10, 5)
            occurrence = st.slider("Ocorrência (1-10)", 1, 10, 5)
            detection = st.slider("Detecção (1-10)", 1, 10, 5)
        
        with col3:
            cause = st.text_area("Causa Potencial")
            current_controls = st.text_area("Controles Atuais")
            recommended_actions = st.text_area("Ações Recomendadas")
        
        submitted = st.form_submit_button("Adicionar")
        
        if submitted:
            rpn = severity * occurrence * detection
            
            if 'fmea_items' not in st.session_state:
                st.session_state.fmea_items = []
            
            st.session_state.fmea_items.append({
                'process_step': process_step,
                'failure_mode': failure_mode,
                'failure_effect': failure_effect,
                'severity': severity,
                'occurrence': occurrence,
                'detection': detection,
                'rpn': rpn,
                'cause': cause,
                'current_controls': current_controls,
                'recommended_actions': recommended_actions
            })
            
            st.success(f"✅ Adicionado! RPN = {rpn}")
    
    # Exibir FMEA
    if 'fmea_items' in st.session_state and st.session_state.fmea_items:
        st.subheader("📊 Tabela FMEA")
        
        fmea_df = pd.DataFrame(st.session_state.fmea_items)
        fmea_df = fmea_df.sort_values('rpn', ascending=False)
        
        # Colorir por RPN
        def color_rpn(val):
            if val >= 100:
                return 'background-color: #ff4444'
            elif val >= 50:
                return 'background-color: #ffaa00'
            else:
                return 'background-color: #44ff44'
        
        styled_df = fmea_df.style.applymap(color_rpn, subset=['rpn'])
        st.dataframe(styled_df, use_container_width=True)
        
        # Gráfico de Pareto dos RPNs
        fig = px.bar(fmea_df.head(10), x='failure_mode', y='rpn',
                    title='Top 10 Modos de Falha por RPN')
        st.plotly_chart(fig, use_container_width=True)

# Footer
st.divider()
st.caption("💡 Complete todas as análises antes de prosseguir para Improve")
