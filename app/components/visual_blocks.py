import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import streamlit as st

def line_over_time(df, time_col, value_col, color=None, title=None):
    """Gráfico de linha temporal"""
    fig = px.line(
        df, 
        x=time_col, 
        y=value_col, 
        color=color,
        title=title or f"{value_col} ao longo do tempo",
        markers=True
    )
    
    fig.update_layout(
        template="plotly_dark",
        hovermode='x unified',
        showlegend=True
    )
    
    return fig

def box_by_group(df, value_col, group_col, title=None):
    """Boxplot por grupo"""
    fig = px.box(
        df, 
        x=group_col, 
        y=value_col,
        title=title or f"Distribuição de {value_col} por {group_col}",
        points="all",
        notched=True
    )
    
    fig.update_layout(template="plotly_dark")
    return fig

def histogram_with_stats(series, bins=30, title=None):
    """Histograma com estatísticas"""
    series = series.dropna()
    
    fig = go.Figure()
    
    # Histograma
    fig.add_trace(go.Histogram(
        x=series,
        nbinsx=bins,
        name='Frequência',
        marker_color='cyan',
        opacity=0.7
    ))
    
    # Linha de média
    mean_val = series.mean()
    fig.add_vline(
        x=mean_val,
        line_dash="dash",
        line_color="yellow",
        annotation_text=f"Média: {mean_val:.2f}"
    )
    
    # Linha de mediana
    median_val = series.median()
    fig.add_vline(
        x=median_val,
        line_dash="dot",
        line_color="orange",
        annotation_text=f"Mediana: {median_val:.2f}"
    )
    
    fig.update_layout(
        title=title or "Distribuição",
        template="plotly_dark",
        showlegend=True
    )
    
    return fig

def scatter_with_regression(df, x_col, y_col, color=None, title=None):
    """Scatter plot com linha de regressão"""
    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        color=color,
        title=title or f"{y_col} vs {x_col}",
        trendline="ols",
        trendline_color_override="red"
    )
    
    fig.update_layout(template="plotly_dark")
    return fig

def correlation_heatmap(corr_matrix, title=None):
    """Heatmap de correlação"""
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        colorscale='RdBu',
        zmid=0,
        text=corr_matrix.values.round(2),
        texttemplate='%{text}',
        textfont={"size": 10},
        colorbar=dict(title="Correlação")
    ))
    
    fig.update_layout(
        title=title or "Matriz de Correlação",
        template="plotly_dark",
        width=700,
        height=700
    )
    
    return fig

def control_chart(df, time_col, value_col, title=None):
    """Gráfico de controle com limites"""
    df = df.sort_values(time_col)
    series = df[value_col]
    
    mean = series.mean()
    std = series.std()
    
    # Limites de controle (3 sigma)
    ucl = mean + 3 * std
    lcl = mean - 3 * std
    
    # Limites de aviso (2 sigma)
    uwl = mean + 2 * std
    lwl = mean - 2 * std
    
    fig = go.Figure()
    
    # Linha principal
    fig.add_trace(go.Scatter(
        x=df[time_col],
        y=series,
        mode='lines+markers',
        name='Valor',
        line=dict(color='cyan', width=2),
        marker=dict(size=8)
    ))
    
    # Linha média
    fig.add_hline(
        y=mean,
        line_dash="solid",
        line_color="green",
        annotation_text=f"Média: {mean:.2f}"
    )
    
    # Limites de controle
    fig.add_hline(
        y=ucl,
        line_dash="dash",
        line_color="red",
        annotation_text=f"UCL: {ucl:.2f}"
    )
    
    fig.add_hline(
        y=lcl,
        line_dash="dash",
        line_color="red",
        annotation_text=f"LCL: {lcl:.2f}"
    )
    
    # Limites de aviso
    fig.add_hline(
        y=uwl,
        line_dash="dot",
        line_color="yellow",
        opacity=0.5
    )
    
    fig.add_hline(
        y=lwl,
        line_dash="dot",
        line_color="yellow",
        opacity=0.5
    )
    
    fig.update_layout(
        title=title or "Gráfico de Controle",
        template="plotly_dark",
        hovermode='x unified'
    )
    
    return fig

def pareto_chart(df, category_col, value_col, title=None):
    """Gráfico de Pareto"""
    # Agrupa e ordena
    pareto_df = df.groupby(category_col)[value_col].sum().reset_index()
    pareto_df = pareto_df.sort_values(value_col, ascending=False)
    
    # Calcula percentual acumulado
    pareto_df['cumsum'] = pareto_df[value_col].cumsum()
    pareto_df['cumperc'] = 100 * pareto_df['cumsum'] / pareto_df[value_col].sum()
    
    fig = make_subplots(
        specs=[[{"secondary_y": True}]],
        subplot_titles=[title or "Análise de Pareto"]
    )
    
    # Barras
    fig.add_trace(
        go.Bar(
            x=pareto_df[category_col],
            y=pareto_df[value_col],
            name='Frequência',
            marker_color='lightblue'
        ),
        secondary_y=False
    )
    
    # Linha acumulada
    fig.add_trace(
        go.Scatter(
            x=pareto_df[category_col],
            y=pareto_df['cumperc'],
            name='% Acumulado',
            line=dict(color='red', width=2),
            marker=dict(size=8)
        ),
        secondary_y=True
    )
    
    # Linha 80%
    fig.add_hline(
        y=80,
        line_dash="dash",
        line_color="green",
        secondary_y=True,
        annotation_text="80%"
    )
    
    fig.update_xaxes(title_text=category_col)
    fig.update_yaxes(title_text="Frequência", secondary_y=False)
    fig.update_yaxes(title_text="% Acumulado", secondary_y=True)
    
    fig.update_layout(
        template="plotly_dark",
        hovermode='x unified'
    )
    
    return fig

def qq_plot(series, title=None):
    """Q-Q Plot para normalidade"""
    import scipy.stats as stats
    
    series = series.dropna()
    
    fig = go.Figure()
    
    # Calcula quantis
    theoretical_quantiles = stats.norm.ppf(np.linspace(0.01, 0.99, len(series)))
    sample_quantiles = np.sort(series)
    
    # Pontos
    fig.add_trace(go.Scatter(
        x=theoretical_quantiles,
        y=sample_quantiles,
        mode='markers',
        name='Dados',
        marker=dict(color='cyan')
    ))
    
    # Linha de referência
    fig.add_trace(go.Scatter(
        x=theoretical_quantiles,
        y=theoretical_quantiles * series.std() + series.mean(),
        mode='lines',
        name='Normal teórica',
        line=dict(color='red', dash='dash')
    ))
    
    fig.update_layout(
        title=title or "Q-Q Plot",
        xaxis_title="Quantis Teóricos",
        yaxis_title="Quantis Amostrais",
        template="plotly_dark"
    )
    
    return fig
