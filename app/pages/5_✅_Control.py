import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys
import json

# Adiciona o diretório app ao path
app_dir = Path(__file__).parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from components.visual_blocks import control_chart, line_over_time

st.set_page_config(page_title="Control", page_icon="✅", layout="wide")

st.header("✅ Control — Monitoramento e Controle Contínuo")

# Verifica se há dados do projeto
project_data = st.session_state.get('project_charter', {})
project_name = project_data.get('project_name', 'Redução de Defeitos')

# Info do projeto atual
st.info(f"📋 **Projeto Atual:** {project_name}")

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard KPIs",
    "📈 Gráficos de Controle", 
    "🎯 Análise de Ishikawa",
    "📋 Plano de Controle",
    "📄 Relatório Final"
])

with tab1:
    st.subheader("Dashboard de Indicadores-Chave (KPIs)")
    
    # Recupera dados do projeto
    if 'project_charter' in st.session_state:
        charter = st.session_state['project_charter']
        baseline = charter.get('metrics', {}).get('baseline', 15.0)
        target = charter.get('metrics', {}).get('target', 5.0)
        unit = charter.get('metrics', {}).get('unit', '%')
        
        # KPIs baseados no projeto de DEFEITOS
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown("### Configurar KPIs")
            
            # KPI Principal - Taxa de Defeitos
            kpi1_name = st.text_input("KPI Principal", value="Taxa de Defeitos")
            kpi1_target = st.number_input("Meta (%)", value=target, key="kpi1_target", format="%.1f")
            kpi1_current = st.number_input("Valor Atual (%)", value=8.5, key="kpi1_current", format="%.1f")
            
            # KPIs Secundários relacionados a defeitos
            kpi2_name = st.text_input("KPI 2", value="Retrabalho")
            kpi2_target = st.number_input("Meta (%)", value=2.0, key="kpi2_target", format="%.1f")
            kpi2_current = st.number_input("Valor Atual (%)", value=3.2, key="kpi2_current", format="%.1f")
            
            kpi3_name = st.text_input("KPI 3", value="PPM (Defeitos/Milhão)")
            kpi3_target = st.number_input("Meta (PPM)", value=1000.0, key="kpi3_target", format="%.0f")
            kpi3_current = st.number_input("Valor Atual (PPM)", value=1500.0, key="kpi3_current", format="%.0f")
        
        with col2:
            st.markdown("### 📊 Painel de KPIs do Projeto")
            
            # Mostra baseline vs atual
            st.markdown(f"**Baseline inicial:** {baseline}{unit} → **Meta:** {target}{unit}")
            
            # KPIs
            kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
            
            with kpi_col1:
                delta1 = kpi1_current - kpi1_target
                improvement1 = baseline - kpi1_current  # Melhoria desde o baseline
                
                st.metric(
                    kpi1_name,
                    f"{kpi1_current:.1f}%",
                    delta=f"{improvement1:.1f}% vs baseline",
                    delta_color="normal"
                )
                
                # Progress bar (invertido - menor é melhor)
                progress1 = max(0, min(100, (1 - kpi1_current/baseline) * 100)) if baseline > 0 else 0
                st.progress(progress1 / 100)
                st.caption(f"Meta: ≤ {kpi1_target:.1f}% | Redução: {((baseline-kpi1_current)/baseline*100):.1f}%")
            
            with kpi_col2:
                delta2 = kpi2_current - kpi2_target
                st.metric(
                    kpi2_name,
                    f"{kpi2_current:.1f}%",
                    delta=f"{delta2:+.1f}% vs meta",
                    delta_color="inverse" if delta2 > 0 else "normal"
                )
                
                progress2 = max(0, min(100, (kpi2_target/kpi2_current) * 100)) if kpi2_current > 0 else 100
                st.progress(progress2 / 100)
                st.caption(f"Meta: ≤ {kpi2_target:.1f}%")
            
            with kpi_col3:
                delta3 = kpi3_current - kpi3_target
                st.metric(
                    kpi3_name,
                    f"{kpi3_current:.0f}",
                    delta=f"{delta3:+.0f} vs meta",
                    delta_color="inverse" if delta3 > 0 else "normal"
                )
                
                progress3 = max(0, min(100, (kpi3_target/kpi3_current) * 100)) if kpi3_current > 0 else 100
                st.progress(progress3 / 100)
                st.caption(f"Meta: ≤ {kpi3_target:.0f} PPM")
            
            # Status geral
            st.markdown("### 🎯 Status Geral do Processo")
            
            # Calcula quantos KPIs estão OK
            kpis_ok = sum([
                kpi1_current <= kpi1_target,
                kpi2_current <= kpi2_target,
                kpi3_current <= kpi3_target
            ])
            
            if kpis_ok == 3:
                st.success("✅ **Processo sob controle** - Todos KPIs dentro da meta")
            elif kpis_ok >= 2:
                st.warning("⚠️ **Atenção necessária** - Alguns KPIs fora da meta")
            else:
                st.error("❌ **Processo fora de controle** - Ação imediata necessária")
            
            # Indicadores
            status_col1, status_col2, status_col3, status_col4 = st.columns(4)
            
            with status_col1:
                st.metric("KPIs OK", f"{kpis_ok}/3")
            with status_col2:
                performance = (kpis_ok / 3) * 100
                st.metric("Performance", f"{performance:.0f}%")
            with status_col3:
                sigma_level = 3 + (1 - kpi1_current/100) * 3  # Aproximação do nível sigma
                st.metric("Nível Sigma", f"{sigma_level:.1f}σ")
            with status_col4:
                risk_level = "Baixo" if kpis_ok == 3 else "Médio" if kpis_ok >= 2 else "Alto"
                st.metric("Nível de Risco", risk_level)
    else:
        st.warning("Configure o Project Charter na página Define primeiro.")

with tab2:
    st.subheader("Gráficos de Controle Estatístico")
    
    # Simula dados de defeitos ao longo do tempo
    st.markdown("### Controle de Taxa de Defeitos")
    
    # Gera dados simulados de defeitos
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    
    # Simula melhoria gradual na taxa de defeitos
    np.random.seed(42)
    baseline_rate = 15.0  # Taxa inicial de defeitos
    current_rate = 8.5    # Taxa atual
    
    # Cria tendência de melhoria
    defeitos = np.linspace(baseline_rate, current_rate, 30) + np.random.normal(0, 1, 30)
    defeitos = np.maximum(0, defeitos)  # Não pode ser negativo
    
    control_df = pd.DataFrame({
        'Data': dates,
        'Taxa_Defeitos_%': defeitos
    })
    
    # Calcula limites de controle
    mean_rate = defeitos.mean()
    std_rate = defeitos.std()
    ucl = mean_rate + 3 * std_rate
    lcl = max(0, mean_rate - 3 * std_rate)
    
    # Gráfico de controle
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    # Linha principal
    fig.add_trace(go.Scatter(
        x=control_df['Data'],
        y=control_df['Taxa_Defeitos_%'],
        mode='lines+markers',
        name='Taxa de Defeitos',
        line=dict(color='cyan', width=2),
        marker=dict(size=8)
    ))
    
    # Linha média
    fig.add_hline(y=mean_rate, line_dash="solid", line_color="green",
                  annotation_text=f"Média: {mean_rate:.1f}%")
    
    # Limites de controle
    fig.add_hline(y=ucl, line_dash="dash", line_color="red",
                  annotation_text=f"UCL: {ucl:.1f}%")
    fig.add_hline(y=lcl, line_dash="dash", line_color="red",
                  annotation_text=f"LCL: {lcl:.1f}%")
    
    # Meta
    if 'project_charter' in st.session_state:
        target = st.session_state['project_charter'].get('metrics', {}).get('target', 5.0)
        fig.add_hline(y=target, line_dash="dot", line_color="yellow",
                      annotation_text=f"Meta: {target}%", opacity=0.7)
    
    fig.update_layout(
        title="Gráfico de Controle - Taxa de Defeitos",
        xaxis_title="Data",
        yaxis_title="Taxa de Defeitos (%)",
        template="plotly_dark",
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Análise de capacidade
    st.markdown("### 📊 Análise de Capacidade do Processo")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Calcula capacidade (simplificado)
    lsl = 0  # Limite inferior (0% defeitos)
    usl = 10  # Limite superior aceitável (10% defeitos)
    
    if std_rate > 0:
        cp = (usl - lsl) / (6 * std_rate)
        cpk = min((usl - mean_rate) / (3 * std_rate), (mean_rate - lsl) / (3 * std_rate))
    else:
        cp = cpk = 0
    
    with col1:
        st.metric("Cp", f"{cp:.2f}")
        st.caption("Capacidade potencial")
    with col2:
        st.metric("Cpk", f"{cpk:.2f}")
        st.caption("Capacidade real")
    with col3:
        st.metric("Média", f"{mean_rate:.1f}%")
        st.caption("Taxa média defeitos")
    with col4:
        capable = cpk >= 1.33
        st.metric("Status", "✅ Capaz" if capable else "⚠️ Marginal" if cpk >= 1.0 else "❌ Não Capaz")

with tab3:
    st.subheader("🎯 Análise de Ishikawa Salva")
    
    if 'prioritized_causes' in st.session_state:
        st.success("✅ Análise de Ishikawa encontrada!")
        
        # Recupera dados salvos
        causes_df = st.session_state['prioritized_causes']
        
        # Mostra tabela completa
        st.markdown("### Todas as Causas Priorizadas")
        st.dataframe(causes_df, use_container_width=True, hide_index=True)
        
        # Top 3 causas
        st.markdown("### 🏆 Top 3 Causas para Ação")
        top3 = causes_df.head(3)
        
        for idx, row in top3.iterrows():
            with st.expander(f"**{row['Causa']}** (Score: {row['Score']})"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Categoria", row['Categoria'])
                with col2:
                    st.metric("Impacto", f"{row['Impacto (1-10)']}/10")
                with col3:
                    st.metric("Facilidade", f"{row['Facilidade (1-10)']}/10")
                
                # Ação sugerida baseada na categoria
                actions = {
                    "Método": "Revisar e padronizar procedimentos",
                    "Máquina": "Manutenção preventiva/calibração",
                    "Mão de Obra": "Treinamento e capacitação",
                    "Material": "Qualificar fornecedores",
                    "Medição": "Calibrar instrumentos",
                    "Meio Ambiente": "Controlar condições ambientais"
                }
                
                st.info(f"💡 **Ação sugerida:** {actions.get(row['Categoria'], 'Investigar causa raiz')}")
        
        # Download da análise
        csv = causes_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Análise de Ishikawa",
            data=csv,
            file_name=f"ishikawa_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.warning("⚠️ Nenhuma análise de Ishikawa encontrada.")
        st.info("Vá para a página **Improve** e complete a análise de causas primeiro.")

with tab4:
    st.subheader("📋 Plano de Controle")
    
    # Plano específico para controle de defeitos
    st.markdown("### ✅ Checklist de Controle de Defeitos")
    
    control_items = pd.DataFrame({
        'Item': [
            'Inspeção de qualidade na entrada',
            'Verificação de setup de máquina',
            'Auditoria de processo',
            'Análise de defeitos (Pareto)',
            'Calibração de instrumentos',
            'Treinamento de operadores',
            'Revisão de procedimentos',
            'Análise de capabilidade'
        ],
        'Frequência': [
            'Cada lote',
            'Cada setup',
            'Diária',
            'Semanal',
            'Mensal',
            'Mensal',
            'Trimestral',
            'Mensal'
        ],
        'Responsável': [
            'Inspetor QA',
            'Operador',
            'Supervisor',
            'Eng. Qualidade',
            'Metrologia',
            'RH/Qualidade',
            'Eng. Processo',
            'Eng. Qualidade'
        ],
        'Método': [
            'Checklist padrão',
            'Setup sheet',
            'Formulário audit',
            'Software análise',
            'Procedimento calibração',
            'Matriz competências',
            'Revisão documental',
            'Estudo Cpk'
        ],
        'Status': ['✅ OK', '✅ OK', '⚠️ Pendente', '✅ OK', '✅ OK', '⚠️ Pendente', '✅ OK', '🔄 Em andamento']
    })
    
    edited_control = st.data_editor(
        control_items,
        column_config={
            'Item': st.column_config.TextColumn('Item', width="large"),
            'Frequência': st.column_config.SelectboxColumn(
                'Frequência',
                options=['Cada lote', 'Cada setup', 'Diária', 'Semanal', 'Quinzenal', 'Mensal', 'Trimestral', 'Anual']
            ),
            'Status': st.column_config.SelectboxColumn(
                'Status',
                options=['✅ OK', '⚠️ Pendente', '❌ Atrasado', '🔄 Em andamento']
            )
        },
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic"
    )
    
    # Sistema de reação para defeitos
    st.markdown("### 🚨 Plano de Reação")
    
    reaction_plan = pd.DataFrame({
        'Situação': [
            'Taxa defeitos > 10%',
            'Taxa defeitos > 15%',
            'Defeito crítico',
            'Reclamação cliente',
            'Tendência crescente (3 pontos)'
        ],
        'Ação Imediata': [
            'Alertar supervisor',
            'Parar produção',
            'Segregar lote',
            'Abrir NC urgente',
            'Investigar causa'
        ],
        'Responsável': [
            'Operador',
            'Supervisor',
            'Qualidade',
            'Qualidade',
            'Eng. Processo'
        ],
        'Prazo': [
            '30 min',
            'Imediato',
            'Imediato',
            '2 horas',
            '4 horas'
        ]
    })
    
    st.dataframe(reaction_plan, use_container_width=True, hide_index=True)

with tab5:
    st.subheader("📄 Relatório Final DMAIC")
    
    # Recupera dados do projeto
    if 'project_charter' in st.session_state:
        charter = st.session_state['project_charter']
        
        st.markdown(f"### Projeto: {charter.get('project_name', 'Redução de Defeitos')}")
        
        # Resumo executivo
        st.markdown("### 📝 Resumo Executivo")
        
        executive_summary = st.text_area(
            "Resumo do Projeto",
            value=f"""Projeto DMAIC para {charter.get('project_name', 'redução de defeitos')} concluído com sucesso.

**Problema inicial:** {charter.get('problem_statement', 'Alta taxa de defeitos no processo')}

**Resultados alcançados:**
• Redução de {charter.get('metrics', {}).get('baseline', 15)}% para 8.5% na taxa de defeitos
• Economia estimada de R$ 250.000/ano
• Melhoria na satisfação do cliente de 72% para 89%
• Implementação de controles estatísticos de processo

**Principais ações implementadas:**
• Padronização de procedimentos operacionais
• Treinamento de 100% da equipe
• Implementação de inspeção na fonte
• Sistema de monitoramento em tempo real""",
            height=300
        )
        
        # Métricas do projeto
        st.markdown("### 📊 Resultados do Projeto")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🔴 Baseline (Início)**")
            st.metric("Taxa de Defeitos", f"{charter.get('metrics', {}).get('baseline', 15.0)}%")
            st.metric("PPM", "15,000")
            st.metric("Custo da Qualidade", "R$ 500k/ano")
            st.metric("Satisfação Cliente", "72%")
        
        with col2:
            st.markdown("**🟢 Atual (Após DMAIC)**")
            st.metric("Taxa de Defeitos", "8.5%", delta="-6.5%")
            st.metric("PPM", "8,500", delta="-6,500")
            st.metric("Custo da Qualidade", "R$ 250k/ano", delta="-R$ 250k")
            st.metric("Satisfação Cliente", "89%", delta="+17%")
        
        # Salvar relatório
        if st.button("💾 Salvar Relatório Final", type="primary"):
            report_data = {
                "project": charter,
                "results": {
                    "baseline": charter.get('metrics', {}).get('baseline', 15.0),
                    "current": 8.5,
                    "improvement": 6.5,
                    "savings": 250000
                },
                "ishikawa": st.session_state.get('prioritized_causes', pd.DataFrame()).to_dict() if 'prioritized_causes' in st.session_state else {},
                "action_plan": st.session_state.get('action_plan', {}),
                "executive_summary": executive_summary
            }
            
            st.session_state['final_report'] = report_data
            
            # Download JSON
            st.download_button(
                label="📥 Baixar Relatório (JSON)",
                data=json.dumps(report_data, indent=2, default=str),
                file_name=f"dmaic_final_report_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
            
            st.success("✅ Relatório Final salvo com sucesso!")
            st.balloons()
    else:
        st.warning("Configure o projeto na página Define primeiro.")
