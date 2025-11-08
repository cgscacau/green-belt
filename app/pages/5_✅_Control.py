import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from app.components.upload_and_store import init_catalog, load_dataset, list_datasets, RESULTS
from app.components.visual_blocks import control_chart, line_over_time
from app.components.reports import render_html_report, save_analysis_manifest
import json

st.set_page_config(page_title="Control", page_icon="✅", layout="wide")
init_catalog()

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
        kpi1_target = st.number_input("Meta", value=7.0, key="kpi1_target")
        kpi1_current = st.number_input("Valor Atual", value=6.8, key="kpi1_current")
        
        kpi2_name = st.text_input("KPI 2", value="Turbidez")
        kpi2_target = st.number_input("Meta", value=3.0, key="kpi2_target")
        kpi2_current = st.number_input("Valor Atual", value=4.2, key="kpi2_current")
        
        kpi3_name = st.text_input("KPI 3", value="NO3")
        kpi3_target = st.number_input("Meta", value=1.5, key="kpi3_target")
        kpi3_current = st.number_input("Valor Atual", value=2.1, key="kpi3_current")
    
    with col2:
        st.markdown("### Painel de KPIs")
        
        # Linha 1 de KPIs
        col1, col2, col3 = st.columns(3)
        
        with col1:
            delta1 = kpi1_current - kpi1_target
            st.metric(
                kpi1_name,
                f"{kpi1_current:.2f}",
                delta=f"{delta1:.2f} vs meta",
                delta_color="inverse" if abs(delta1) > 0.5 else "normal"
            )
            
            # Progress bar
            progress1 = min(100, max(0, (1 - abs(delta1) / kpi1_target) * 100))
            st.progress(progress1 / 100)
            st.caption(f"Meta: {kpi1_target:.2f}")
        
        with col2:
            delta2 = kpi2_current - kpi2_target
            st.metric(
                kpi2_name,
                f"{kpi2_current:.2f}",
                delta=f"{delta2:.2f} vs meta",
                delta_color="inverse" if delta2 > 0 else "normal"
            )
            
            progress2 = min(100, max(0, (1 - abs(delta2) / kpi2_target) * 100))
            st.progress(progress2 / 100)
            st.caption(f"Meta: {kpi2_target:.2f}")
        
        with col3:
            delta3 = kpi3_current - kpi3_target
            st.metric(
                kpi3_name,
                f"{kpi3_current:.2f}",
                delta=f"{delta3:.2f} vs meta",
                delta_color="inverse" if delta3 > 0 else "normal"
            )
            
            progress3 = min(100, max(0, (1 - abs(delta3) / kpi3_target) * 100))
            st.progress(progress3 / 100)
            st.caption(f"Meta: {kpi3_target:.2f}")
        
        # Status geral
        st.markdown("### Status Geral do Processo")
        
        kpis_ok = sum([
            abs(delta1) <= 0.5,
            delta2 <= 0,
            delta3 <= 0
        ])
        
        if kpis_ok == 3:
            st.success("✅ Processo sob controle - Todos KPIs dentro da meta")
        elif kpis_ok >= 2:
            st.warning("⚠️ Atenção - Alguns KPIs fora da meta")
        else:
            st.error("❌ Processo fora de controle - Ação imediata necessária")
        
        # Tendência (simulada)
        st.markdown("### Tendência (últimos 30 dias)")
        
        dates = pd.date_range(end=datetime.now(), periods=30)
        trend_data = pd.DataFrame({
            'Data': dates,
            kpi1_name: np.random.normal(kpi1_current, 0.2, 30),
            kpi2_name: np.random.normal(kpi2_current, 0.5, 30),
            kpi3_name: np.random.normal(kpi3_current, 0.3, 30)
        })
        
        trend_data[kpi1_name] = trend_data[kpi1_name].cumsum() / range(1, 31)
        trend_data[kpi2_name] = trend_data[kpi2_name].cumsum() / range(1, 31)
        trend_data[kpi3_name] = trend_data[kpi3_name].cumsum() / range(1, 31)
        
        fig = line_over_time(
            trend_data.melt(id_vars='Data', var_name='KPI', value_name='Valor'),
            'Data', 'Valor', color='KPI',
            title="Evolução dos KPIs"
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Gráficos de Controle Estatístico")
    
    # Seleção de dataset
    datasets_df = list_datasets()
    
    if not datasets_df.empty:
        selected = st.selectbox(
            "Selecione o dataset para controle",
            datasets_df['name'].unique(),
            key="control_dataset"
        )
        
        df = load_dataset(selected)
        
        if not df.empty and 'date' in df.columns:
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            
            if numeric_cols:
                selected_metric = st.selectbox("Métrica para controle", numeric_cols)
                
                # Gráfico de controle
                fig = control_chart(df, 'date', selected_metric, title=f"Gráfico de Controle - {selected_metric}")
                st.plotly_chart(fig, use_container_width=True)
                
                # Análise de capacidade
                st.markdown("### Análise de Capacidade do Processo")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    lsl = st.number_input("LSL (Limite Inferior)", value=df[selected_metric].min())
                
                with col2:
                    usl = st.number_input("USL (Limite Superior)", value=df[selected_metric].max())
                
                with col3:
                    target = st.number_input("Alvo", value=df[selected_metric].mean())
                
                if st.button("Calcular Capacidade"):
                    from app.components.stats_blocks import process_capability
                    
                    cap_result = process_capability(df[selected_metric], lsl, usl, target)
                    
                    if cap_result:
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Cp", f"{cap_result.get('cp', 0):.3f}")
                        with col2:
                            st.metric("Cpk", f"{cap_result.get('cpk', 0):.3f}")
                        with col3:
                            st.metric("PPM Total", f"{cap_result.get('ppm_total', 0):.0f}")
                        with col4:
                            capable = cap_result.get('process_capable', False)
                            st.metric("Status", "Capaz" if capable else "Não Capaz")
    else:
        st.info("Nenhum dataset disponível. Faça upload na página Measure.")

with tab3:
    st.subheader("Plano de Controle")
    
    st.markdown("### Checklist de Controle")
    
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
        'Status': ['OK', 'OK', 'Pendente', 'OK', 'OK', 'Atrasado']
    })
    
    edited_control = st.data_editor(
        control_items,
        column_config={
            'Último Check': st.column_config.DateColumn(),
            'Status': st.column_config.SelectboxColumn(
                options=['OK', 'Pendente', 'Atrasado', 'Crítico']
            )
        },
        use_container_width=True
    )
    
    # Alertas
    st.markdown("### Sistema de Alertas")
    
    alert_config = pd.DataFrame({
        'Métrica': ['pH', 'Turbidez', 'NO3'],
        'Limite Inferior': [6.0, 0.0, 0.0],
        'Limite Superior': [8.0, 5.0, 3.0],
        'Ação se Violado': [
            'Ajustar dosagem química',
            'Verificar sistema de filtragem',
            'Investigar fonte de contaminação'
        ],
        'Notificar': ['gerente@greenpeace.org', 'lab@greenpeace.org', 'todos@greenpeace.org']
    })
    
    st.dataframe(alert_config, use_container_width=True)
    
    # Documentação
    st.markdown("### Documentação de Controle")
    
    doc_list = [
        "✅ POP - Procedimento Operacional Padrão",
        "✅ Instrução de Trabalho - Coleta de Amostras",
        "✅ Formulário de Registro de Não-Conformidades",
        "✅ Plano de Resposta a Emergências",
        "✅ Matriz de Treinamento"
    ]
    
    for doc in doc_list:
        st.markdown(doc)

with tab4:
    st.subheader("Relatório Final DMAIC")
    
    st.info("Consolidação de todas as fases do projeto DMAIC")
    
    # Resumo do projeto
    st.markdown("### Resumo Executivo")
    
    executive_summary = st.text_area(
        "Resumo do Projeto",
        value="""Este projeto DMAIC foi conduzido para melhorar a qualidade da água no Rio X, 
focando na redução de turbidez e controle de pH. Através de análises estatísticas 
rigorosas e implementação de melhorias no processo, conseguimos atingir as metas estabelecidas.""",
        height=150
    )
    
    # Resultados alcançados
    st.markdown("### Resultados Alcançados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Antes (Baseline)**")
        st.metric("pH", "6.5")
        st.metric("Turbidez", "5.3 NTU")
        st.metric("NO3", "2.4 mg/L")
    
    with col2:
        st.markdown("**Depois (Atual)**")
        st.metric("pH", "6.8", delta="0.3")
        st.metric("Turbidez", "4.2 NTU", delta="-1.1")
        st.metric("NO3", "2.1 mg/L", delta="-0.3")
    
    # Lições aprendidas
    st.markdown("### Lições Aprendidas")
    
    lessons = st.text_area(
        "Principais aprendizados",
        value="""1. A padronização dos processos de coleta foi fundamental
2. O treinamento da equipe teve impacto direto nos resultados
3. O monitoramento contínuo é essencial para sustentabilidade""",
        height=100
    )
    
    # Próximos passos
    st.markdown("### Próximos Passos")
    
    next_steps = [
        "Expandir o programa para outros rios da região",
        "Implementar sistema automatizado de monitoramento",
        "Certificação ISO 14001",
        "Treinamento avançado para equipe técnica"
    ]
    
    for i, step in enumerate(next_steps, 1):
        st.markdown(f"{i}. {step}")
    
    # Gerar relatório final
    if st.button("📄 Gerar Relatório Final Completo", type="primary"):
        
        # Coleta todos os arquivos de relatórios anteriores
        report_files = list(RESULTS.glob("*.html"))
        
        # Prepara dados para o relatório
        metrics = [
            {"label": "Redução de Turbidez", "value": "20.8%"},
            {"label": "Melhoria no pH", "value": "4.6%"},
            {"label": "Redução de NO3", "value": "12.5%"},
            {"label": "ROI do Projeto", "value": "250%"}
        ]
        
        recommendations = [
            "Manter monitoramento contínuo dos KPIs estabelecidos",
            "Realizar auditorias trimestrais de processo",
            "Atualizar plano de controle conforme necessário",
            "Documentar e compartilhar melhores práticas"
        ]
        
        # Gera relatório
        final_report_path = RESULTS / f"final_dmaic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        html = render_html_report(
            title="Relatório Final DMAIC - Qualidade da Água Rio X",
            project="Melhoria da Qualidade da Água - Greenpeace",
            summary=executive_summary,
            metrics=metrics,
            conclusions=lessons,
            recommendations=recommendations,
            out_html=final_report_path
        )
        
        st.success("✅ Relatório Final DMAIC gerado com sucesso!")
        st.balloons()
        
        # Mostra preview
        with st.expander("📄 Preview do Relatório Final"):
            st.markdown(html, unsafe_allow_html=True)
        
        # Salva manifesto final
        manifest_id, _ = save_analysis_manifest(
            phase="control",
            dataset_id="final_report",
            parameters={
                "phases_completed": ["Define", "Measure", "Analyze", "Improve", "Control"],
                "total_reports": len(report_files)
            },
            results={"final_report": str(final_report_path)}
        )
        
        st.caption(f"Projeto DMAIC concluído. ID: {manifest_id}")
