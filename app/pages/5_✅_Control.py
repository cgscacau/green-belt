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

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard KPIs",
    "📈 Gráficos de Controle",
    "📋 Plano de Controle",
    "📄 Relatório Final"
])

with tab1:
    st.subheader("Dashboard de Indicadores-Chave (KPIs)")
    
    # Configuração de KPIs
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown("### Configurar KPIs")
        
        kpi1_name = st.text_input("KPI 1", value="pH da Água")
        kpi1_target = st.number_input("Meta", value=7.0, key="kpi1_target", format="%.1f")
        kpi1_current = st.number_input("Valor Atual", value=6.8, key="kpi1_current", format="%.1f")
        
        kpi2_name = st.text_input("KPI 2", value="Turbidez")
        kpi2_target = st.number_input("Meta", value=3.0, key="kpi2_target", format="%.1f")
        kpi2_current = st.number_input("Valor Atual", value=4.2, key="kpi2_current", format="%.1f")
        
        kpi3_name = st.text_input("KPI 3", value="NO3")
        kpi3_target = st.number_input("Meta", value=1.5, key="kpi3_target", format="%.1f")
        kpi3_current = st.number_input("Valor Atual", value=2.1, key="kpi3_current", format="%.1f")
    
    with col2:
        st.markdown("### 📊 Painel de KPIs")
        
        # Linha 1 de KPIs
        kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
        
        with kpi_col1:
            delta1 = kpi1_current - kpi1_target
            # Para pH, quanto mais próximo de 7, melhor
            deviation1 = abs(kpi1_current - 7.0) - abs(kpi1_target - 7.0)
            
            st.metric(
                kpi1_name,
                f"{kpi1_current:.2f}",
                delta=f"{delta1:+.2f} vs meta",
                delta_color="inverse" if abs(delta1) > 0.5 else "normal"
            )
            
            # Progress bar
            progress1 = min(100, max(0, (1 - abs(delta1) / kpi1_target) * 100)) if kpi1_target != 0 else 0
            st.progress(progress1 / 100)
            st.caption(f"Meta: {kpi1_target:.2f} | Ideal: 7.0")
        
        with kpi_col2:
            delta2 = kpi2_current - kpi2_target
            st.metric(
                kpi2_name,
                f"{kpi2_current:.2f}",
                delta=f"{delta2:+.2f} vs meta",
                delta_color="inverse" if delta2 > 0 else "normal"
            )
            
            progress2 = min(100, max(0, (kpi2_target / kpi2_current) * 100)) if kpi2_current != 0 else 0
            st.progress(progress2 / 100)
            st.caption(f"Meta: ≤ {kpi2_target:.2f}")
        
        with kpi_col3:
            delta3 = kpi3_current - kpi3_target
            st.metric(
                kpi3_name,
                f"{kpi3_current:.2f}",
                delta=f"{delta3:+.2f} vs meta",
                delta_color="inverse" if delta3 > 0 else "normal"
            )
            
            progress3 = min(100, max(0, (kpi3_target / kpi3_current) * 100)) if kpi3_current != 0 else 0
            st.progress(progress3 / 100)
            st.caption(f"Meta: ≤ {kpi3_target:.2f}")
        
        # Status geral
        st.markdown("### 🎯 Status Geral do Processo")
        
        # Calcula quantos KPIs estão OK
        kpis_ok = sum([
            abs(delta1) <= 0.5,  # pH próximo da meta
            delta2 <= 0,         # Turbidez abaixo da meta
            delta3 <= 0          # NO3 abaixo da meta
        ])
        
        if kpis_ok == 3:
            st.success("✅ **Processo sob controle** - Todos KPIs dentro da meta")
        elif kpis_ok >= 2:
            st.warning("⚠️ **Atenção necessária** - Alguns KPIs fora da meta")
        else:
            st.error("❌ **Processo fora de controle** - Ação imediata necessária")
        
        # Indicadores visuais
        status_col1, status_col2, status_col3, status_col4 = st.columns(4)
        
        with status_col1:
            st.metric("KPIs OK", f"{kpis_ok}/3")
        with status_col2:
            performance = (kpis_ok / 3) * 100
            st.metric("Performance", f"{performance:.0f}%")
        with status_col3:
            trend = "📈" if kpis_ok >= 2 else "📉"
            st.metric("Tendência", trend)
        with status_col4:
            risk_level = "Baixo" if kpis_ok == 3 else "Médio" if kpis_ok >= 2 else "Alto"
            st.metric("Nível de Risco", risk_level)
        
        # Gráfico de tendência simulado
        st.markdown("### 📈 Tendência dos KPIs (Últimos 30 dias)")
        
        # Gera dados simulados
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        
        # Simula tendência com melhoria gradual
        np.random.seed(42)  # Para reprodutibilidade
        trend_data = pd.DataFrame({
            'Data': dates,
            kpi1_name: np.random.normal(kpi1_current, 0.2, 30).cumsum() / np.arange(1, 31) + np.linspace(7.5, kpi1_current, 30),
            kpi2_name: np.random.normal(kpi2_current, 0.5, 30).cumsum() / np.arange(1, 31) + np.linspace(5.0, kpi2_current, 30),
            kpi3_name: np.random.normal(kpi3_current, 0.3, 30).cumsum() / np.arange(1, 31) + np.linspace(2.5, kpi3_current, 30)
        })
        
        # Melt para formato long
        trend_long = trend_data.melt(id_vars='Data', var_name='KPI', value_name='Valor')
        
        try:
            fig = line_over_time(
                trend_long,
                'Data', 'Valor', color='KPI',
                title="Evolução dos KPIs"
            )
            st.plotly_chart(fig, use_container_width=True, key="kpi_trend")
        except Exception as e:
            st.error(f"Erro ao criar gráfico: {e}")

with tab2:
    st.subheader("Gráficos de Controle Estatístico")
    
    # Verifica se há dados disponíveis
    if 'analysis_df' in st.session_state:
        df = st.session_state['analysis_df']
        
        # Identifica colunas apropriadas
        if 'date' in df.columns or 'data' in df.columns:
            date_col = 'date' if 'date' in df.columns else 'data'
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            
            if numeric_cols:
                selected_metric = st.selectbox(
                    "Selecione a métrica para controle",
                    numeric_cols,
                    key="control_metric"
                )
                
                # Gráfico de controle
                try:
                    fig = control_chart(
                        df, date_col, selected_metric,
                        title=f"Gráfico de Controle - {selected_metric}"
                    )
                    st.plotly_chart(fig, use_container_width=True, key="control_chart_plot")
                except Exception as e:
                    st.error(f"Erro ao criar gráfico de controle: {e}")
                
                # Análise de capacidade
                st.markdown("### 📊 Análise de Capacidade do Processo")
                
                col1, col2, col3 = st.columns(3)
                
                series = df[selected_metric].dropna()
                mean_val = series.mean()
                std_val = series.std()
                
                with col1:
                    lsl = st.number_input(
                        "LSL (Limite Inferior)",
                        value=float(series.min()),
                        format="%.2f",
                        key="lsl"
                    )
                
                with col2:
                    usl = st.number_input(
                        "USL (Limite Superior)",
                        value=float(series.max()),
                        format="%.2f",
                        key="usl"
                    )
                
                with col3:
                    target = st.number_input(
                        "Alvo",
                        value=float(mean_val),
                        format="%.2f",
                        key="target"
                    )
                
                if st.button("📊 Calcular Capacidade"):
                    if usl > lsl and std_val > 0:
                        # Calcula índices de capacidade
                        cp = (usl - lsl) / (6 * std_val)
                        cpu = (usl - mean_val) / (3 * std_val)
                        cpl = (mean_val - lsl) / (3 * std_val)
                        cpk = min(cpu, cpl)
                        
                        # PPM defeituosos
                        from scipy import stats
                        ppm_lsl = stats.norm.cdf(lsl, mean_val, std_val) * 1000000
                        ppm_usl = (1 - stats.norm.cdf(usl, mean_val, std_val)) * 1000000
                        ppm_total = ppm_lsl + ppm_usl
                        
                        # Mostra resultados
                        res_col1, res_col2, res_col3, res_col4 = st.columns(4)
                        
                        with res_col1:
                            st.metric("Cp", f"{cp:.3f}")
                            st.caption("Capacidade potencial")
                        with res_col2:
                            st.metric("Cpk", f"{cpk:.3f}")
                            st.caption("Capacidade real")
                        with res_col3:
                            st.metric("PPM Total", f"{ppm_total:.0f}")
                            st.caption("Defeitos por milhão")
                        with res_col4:
                            capable = cpk >= 1.33
                            st.metric(
                                "Status",
                                "✅ Capaz" if capable else "❌ Não Capaz"
                            )
                            st.caption("Cpk ≥ 1.33")
                        
                        # Interpretação
                        if cpk >= 2.0:
                            st.success("🌟 **Processo de classe mundial** (Nível Six Sigma)")
                        elif cpk >= 1.33:
                            st.success("✅ **Processo capaz** - Atende especificações")
                        elif cpk >= 1.0:
                            st.warning("⚠️ **Processo marginalmente capaz** - Requer monitoramento")
                        else:
                            st.error("❌ **Processo não capaz** - Necessita melhoria urgente")
                    else:
                        st.error("Verifique os limites: USL deve ser maior que LSL")
            else:
                st.warning("Nenhuma coluna numérica disponível para controle.")
        else:
            st.warning("Dataset não possui coluna de data para gráfico de controle.")
    else:
        st.info("Nenhum dataset disponível. Processe dados na página Measure primeiro.")

with tab3:
    st.subheader("Plano de Controle")
    
    st.markdown("### ✅ Checklist de Controle")
    
    # Checklist editável
    control_items = pd.DataFrame({
        'Item': [
            'Monitoramento diário de pH',
            'Análise semanal de turbidez',
            'Teste mensal de NO3',
            'Calibração de equipamentos',
            'Revisão trimestral de processos',
            'Treinamento semestral da equipe'
        ],
        'Frequência': [
            'Diária',
            'Semanal',
            'Mensal',
            'Quinzenal',
            'Trimestral',
            'Semestral'
        ],
        'Responsável': [
            'Técnico A',
            'Analista B',
            'Lab. Externo',
            'Manutenção',
            'Gerência',
            'RH'
        ],
        'Último Check': [
            datetime.now().date(),
            datetime.now().date() - timedelta(days=3),
            datetime.now().date() - timedelta(days=15),
            datetime.now().date() - timedelta(days=7),
            datetime.now().date() - timedelta(days=45),
            datetime.now().date() - timedelta(days=90)
        ],
        'Status': ['✅ OK', '✅ OK', '⚠️ Pendente', '✅ OK', '✅ OK', '❌ Atrasado']
    })
    
    edited_control = st.data_editor(
        control_items,
        column_config={
            'Item': st.column_config.TextColumn('Item', width="large"),
            'Frequência': st.column_config.SelectboxColumn(
                'Frequência',
                options=['Diária', 'Semanal', 'Quinzenal', 'Mensal', 'Trimestral', 'Semestral', 'Anual']
            ),
            'Responsável': st.column_config.TextColumn('Responsável'),
            'Último Check': st.column_config.DateColumn('Último Check', format="DD/MM/YYYY"),
            'Status': st.column_config.SelectboxColumn(
                'Status',
                options=['✅ OK', '⚠️ Pendente', '❌ Atrasado', '🔄 Em andamento']
            )
        },
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        key="control_checklist"
    )
    
    # Resumo do status
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        ok_count = len(edited_control[edited_control['Status'] == '✅ OK'])
        st.metric("Itens OK", ok_count)
    
    with col2:
        pending_count = len(edited_control[edited_control['Status'] == '⚠️ Pendente'])
        st.metric("Pendentes", pending_count)
    
    with col3:
        late_count = len(edited_control[edited_control['Status'] == '❌ Atrasado'])
        st.metric("Atrasados", late_count)
    
    with col4:
        compliance = (ok_count / len(edited_control)) * 100 if len(edited_control) > 0 else 0
        st.metric("Conformidade", f"{compliance:.0f}%")
    
    # Sistema de Alertas
    st.markdown("### 🚨 Sistema de Alertas")
    
    alert_config = pd.DataFrame({
        'Métrica': ['pH', 'Turbidez', 'NO3', 'Temperatura', 'Oxigênio Dissolvido'],
        'Limite Inferior': [6.0, 0.0, 0.0, 15.0, 5.0],
        'Limite Superior': [8.0, 5.0, 3.0, 30.0, 10.0],
        'Ação se Violado': [
            'Ajustar dosagem química',
            'Verificar sistema de filtragem',
            'Investigar fonte de contaminação',
            'Acionar sistema de refrigeração',
            'Aumentar aeração'
        ],
        'Notificar': [
            'gerente@greenpeace.org',
            'lab@greenpeace.org',
            'todos@greenpeace.org',
            'manutencao@greenpeace.org',
            'operacao@greenpeace.org'
        ]
    })
    
    st.dataframe(alert_config, use_container_width=True, hide_index=True)
    
    # Documentação
    st.markdown("### 📚 Documentação de Controle")
    
    doc_list = [
        {"Documento": "POP - Procedimento Operacional Padrão", "Status": "✅ Atualizado", "Versão": "2.1"},
        {"Documento": "Instrução de Trabalho - Coleta de Amostras", "Status": "✅ Atualizado", "Versão": "1.5"},
        {"Documento": "Formulário de Registro de Não-Conformidades", "Status": "⚠️ Em revisão", "Versão": "1.2"},
        {"Documento": "Plano de Resposta a Emergências", "Status": "✅ Atualizado", "Versão": "3.0"},
        {"Documento": "Matriz de Treinamento", "Status": "✅ Atualizado", "Versão": "2.0"}
    ]
    
    doc_df = pd.DataFrame(doc_list)
    st.dataframe(doc_df, use_container_width=True, hide_index=True)

with tab4:
    st.subheader("📄 Relatório Final DMAIC")
    
    st.info("Consolidação de todas as fases do projeto DMAIC")
    
    # Resumo do projeto
    st.markdown("### 📝 Resumo Executivo")
    
    executive_summary = st.text_area(
        "Resumo do Projeto",
        value="""Este projeto DMAIC foi conduzido para melhorar a qualidade da água no Rio X, 
focando na redução de turbidez e controle de pH. Através de análises estatísticas 
rigorosas e implementação de melhorias no processo, conseguimos atingir as metas estabelecidas.

Principais conquistas:
• Redução de 20% na turbidez média
• Estabilização do pH dentro da faixa ideal
• Implementação de sistema de monitoramento contínuo
• Treinamento de toda equipe operacional""",
        height=200,
        key="executive_summary"
    )
    
    # Resultados alcançados
    st.markdown("### 📊 Resultados Alcançados")
    
    results_col1, results_col2 = st.columns(2)
    
    with results_col1:
        st.markdown("**🔴 Antes (Baseline)**")
        before_metrics = {
            "pH": 6.5,
            "Turbidez (NTU)": 5.3,
            "NO3 (mg/L)": 2.4,
            "Defeitos (%)": 15.2,
            "Satisfação Cliente": "72%"
        }
        for metric, value in before_metrics.items():
            st.metric(metric, value)
    
    with results_col2:
        st.markdown("**🟢 Depois (Atual)**")
        after_metrics = {
            "pH": (6.8, "+0.3"),
            "Turbidez (NTU)": (4.2, "-1.1"),
            "NO3 (mg/L)": (2.1, "-0.3"),
            "Defeitos (%)": (8.5, "-6.7"),
            "Satisfação Cliente": ("89%", "+17%")
        }
        for metric, (value, delta) in after_metrics.items():
            st.metric(metric, value, delta=delta)
    
    # ROI do Projeto
    st.markdown("### 💰 Retorno sobre Investimento (ROI)")
    
    roi_col1, roi_col2, roi_col3 = st.columns(3)
    
    with roi_col1:
        investment = st.number_input("Investimento Total (R$)", value=50000.00, format="%.2f")
    
    with roi_col2:
        savings = st.number_input("Economia Anual (R$)", value=125000.00, format="%.2f")
    
    with roi_col3:
        roi = ((savings - investment) / investment * 100) if investment > 0 else 0
        st.metric("ROI", f"{roi:.1f}%")
        payback = investment / savings * 12 if savings > 0 else 0
        st.metric("Payback", f"{payback:.1f} meses")
    
    # Lições aprendidas
    st.markdown("### 💡 Lições Aprendidas")
    
    lessons = st.text_area(
        "Principais aprendizados",
        value="""1. A padronização dos processos de coleta foi fundamental para reduzir variabilidade
2. O treinamento da equipe teve impacto direto e mensurável nos resultados
3. O monitoramento contínuo é essencial para sustentabilidade das melhorias
4. A análise de dados históricos revelou padrões não percebidos anteriormente
5. O engajamento da liderança foi crucial para o sucesso do projeto""",
        height=150,
        key="lessons_learned"
    )
    
    # Próximos passos
    st.markdown("### 🚀 Próximos Passos")
    
    next_steps = [
        "Expandir o programa para outros rios da região Norte",
        "Implementar sistema automatizado de monitoramento IoT",
        "Buscar certificação ISO 14001 para o processo",
        "Desenvolver dashboard em tempo real para stakeholders",
        "Treinar multiplicadores internos na metodologia DMAIC"
    ]
    
    for i, step in enumerate(next_steps, 1):
        st.markdown(f"{i}. {step}")
    
    # Gerar relatório final
    st.markdown("### 📥 Gerar Documentação Final")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Gerar Relatório Final Completo", type="primary", use_container_width=True):
            # Prepara dados para o relatório
            report_data = {
                "project_name": "Melhoria da Qualidade da Água - Rio X",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "executive_summary": executive_summary,
                "results": after_metrics,
                "roi": roi,
                "lessons": lessons,
                "next_steps": next_steps
            }
            
            # Salva na sessão
            st.session_state['final_report'] = report_data
            
            st.success("✅ Relatório Final DMAIC preparado com sucesso!")
            st.balloons()
            
            # Mostra preview do JSON
            with st.expander("📋 Preview dos Dados do Relatório"):
                st.json(report_data)
    
    with col2:
        if st.button("📊 Exportar Apresentação Executiva", type="secondary", use_container_width=True):
            # Cria resumo executivo
            exec_summary = f"""
# PROJETO DMAIC - RELATÓRIO EXECUTIVO

## Projeto: Melhoria da Qualidade da Água - Rio X
## Data: {datetime.now().strftime("%d/%m/%Y")}

### RESULTADOS ALCANÇADOS
- Redução de 20.8% na turbidez
- Melhoria de 4.6% no pH
- Redução de 12.5% no NO3
- ROI: {roi:.1f}%

### PRÓXIMAS AÇÕES
{chr(10).join([f"- {step}" for step in next_steps])}

### STATUS: ✅ PROJETO CONCLUÍDO COM SUCESSO
            """
            
            # Download como texto
            st.download_button(
                label="📥 Baixar Resumo Executivo",
                data=exec_summary,
                file_name=f"resumo_executivo_dmaic_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )
    
    # Certificação do projeto
    st.markdown("### 🏆 Certificação do Projeto")
    
    cert_col1, cert_col2, cert_col3 = st.columns(3)
    
    with cert_col1:
        st.info("📋 **Conformidade**\n\nTodos os requisitos DMAIC foram atendidos")
    
    with cert_col2:
        st.success("✅ **Validação**\n\nResultados validados pela equipe técnica")
    
    with cert_col3:
        st.success("🎯 **Metas Atingidas**\n\n100% das metas do projeto foram alcançadas")
    
    # Assinatura digital
    st.markdown("### ✍️ Aprovações")
    
    approvals = pd.DataFrame({
        'Papel': ['Sponsor do Projeto', 'Gerente de Qualidade', 'Black Belt', 'Champion'],
        'Nome': ['João Silva', 'Maria Santos', 'Pedro Costa', 'Ana Lima'],
        'Data': [datetime.now().date()] * 4,
        'Status': ['✅ Aprovado'] * 4
    })
    
    st.dataframe(approvals, use_container_width=True, hide_index=True)
    
    # Mensagem final
    st.success("""
    ### 🎉 Parabéns! Projeto DMAIC Concluído com Sucesso!
    
    O projeto demonstrou melhorias significativas em todos os KPIs monitorados, 
    com ROI positivo e sustentabilidade garantida através do plano de controle implementado.
    """)
