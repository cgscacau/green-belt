import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from components.supabase_client import get_supabase_manager
import io

st.set_page_config(page_title="Control", page_icon="✅", layout="wide")

# Inicializa Supabase
db = get_supabase_manager()

st.header("✅ Control — Monitoramento e Controle Contínuo")

# Verifica projeto ativo
current_project_id = st.session_state.get('current_project_id')

if not current_project_id:
    st.warning("⚠️ Nenhum projeto selecionado")
    st.info("Por favor, selecione ou crie um projeto na página **Define** primeiro.")
    st.stop()

# Mostra projeto ativo
project = db.get_project(current_project_id)
if project:
    st.success(f"📂 Projeto: **{project['name']}**")
    
    # Calcula dias do projeto
    if project.get('start_date'):
        start_date = pd.to_datetime(project['start_date'])
        days_elapsed = (datetime.now() - start_date).days
        st.caption(f"Projeto em andamento há {days_elapsed} dias")
else:
    st.error("Projeto não encontrado")
    st.stop()

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard KPIs",
    "📈 Gráficos de Controle",
    "📋 Plano de Controle",
    "📄 Relatório Final",
    "💾 Histórico"
])

with tab1:
    st.subheader("Dashboard de Indicadores-Chave (KPIs)")
    
    # Busca KPIs salvos
    kpis_df = db.get_kpis(current_project_id)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown("### Registrar KPIs")
        
        # KPI Principal - Taxa de Defeitos
        kpi1_name = st.text_input("KPI Principal", value="Taxa de Defeitos")
        kpi1_target = st.number_input("Meta (%)", 
                                      value=float(project.get('target_value', 5.0)), 
                                      format="%.1f")
        kpi1_current = st.number_input("Valor Atual (%)", value=8.5, format="%.1f")
        
        # KPIs Secundários
        kpi2_name = st.text_input("KPI 2", value="Retrabalho")
        kpi2_target = st.number_input("Meta (%)", value=2.0, key="kpi2_target", format="%.1f")
        kpi2_current = st.number_input("Valor Atual (%)", value=3.2, key="kpi2_current", format="%.1f")
        
        kpi3_name = st.text_input("KPI 3", value="Satisfação Cliente")
        kpi3_target = st.number_input("Meta (%)", value=90.0, key="kpi3_target", format="%.1f")
        kpi3_current = st.number_input("Valor Atual (%)", value=85.0, key="kpi3_current", format="%.1f")
        
        if st.button("💾 Salvar KPIs", type="primary"):
            # Salva os 3 KPIs
            saved = 0
            for name, target, current in [
                (kpi1_name, kpi1_target, kpi1_current),
                (kpi2_name, kpi2_target, kpi2_current),
                (kpi3_name, kpi3_target, kpi3_current)
            ]:
                if db.save_kpi(current_project_id, name, target, current, "%"):
                    saved += 1
            
            if saved > 0:
                st.success(f"✅ {saved} KPIs salvos!")
                st.rerun()
    
    with col2:
        st.markdown("### 📊 Painel de KPIs")
        
        # Mostra evolução vs baseline
        baseline = project.get('baseline_value', 15.0)
        
        st.markdown(f"**Evolução do Projeto**")
        st.caption(f"Baseline: {baseline}% → Meta: {kpi1_target}% → Atual: {kpi1_current}%")
        
        # Progress bar geral
        progress = max(0, min(100, ((baseline - kpi1_current) / (baseline - kpi1_target) * 100))) if baseline != kpi1_target else 0
        st.progress(progress / 100)
        st.caption(f"Progresso para meta: {progress:.0f}%")
        
        # KPIs individuais
        kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
        
        with kpi_col1:
            delta1 = kpi1_current - kpi1_target
            improvement1 = baseline - kpi1_current
            
            st.metric(
                kpi1_name,
                f"{kpi1_current:.1f}%",
                delta=f"{improvement1:.1f}% melhoria",
                delta_color="normal"
            )
            
            # Status
            if kpi1_current <= kpi1_target:
                st.success("✅ Meta atingida!")
            elif kpi1_current < baseline:
                st.warning(f"📈 Melhorando ({improvement1/baseline*100:.0f}% redução)")
            else:
                st.error("❌ Acima do baseline")
        
        with kpi_col2:
            delta2 = kpi2_current - kpi2_target
            st.metric(
                kpi2_name,
                f"{kpi2_current:.1f}%",
                delta=f"{delta2:+.1f}% vs meta",
                delta_color="inverse" if delta2 > 0 else "normal"
            )
            
            if kpi2_current <= kpi2_target:
                st.success("✅ Meta atingida!")
            else:
                st.warning(f"⚠️ {abs(delta2):.1f}% acima da meta")
        
        with kpi_col3:
            delta3 = kpi3_current - kpi3_target
            st.metric(
                kpi3_name,
                f"{kpi3_current:.1f}%",
                delta=f"{delta3:+.1f}% vs meta",
                delta_color="normal" if delta3 >= 0 else "inverse"
            )
            
            if kpi3_current >= kpi3_target:
                st.success("✅ Meta atingida!")
            else:
                st.warning(f"⚠️ {abs(delta3):.1f}% abaixo da meta")
        
        # Status geral e nível sigma
        st.markdown("### 🎯 Status do Processo")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            kpis_ok = sum([
                kpi1_current <= kpi1_target,
                kpi2_current <= kpi2_target,
                kpi3_current >= kpi3_target
            ])
            st.metric("KPIs na Meta", f"{kpis_ok}/3")
        
        with col2:
            performance = (kpis_ok / 3) * 100
            st.metric("Performance", f"{performance:.0f}%")
        
        with col3:
            # Cálculo aproximado do nível sigma baseado na taxa de defeitos
            if kpi1_current > 0:
                dpmo = kpi1_current * 10000  # Defeitos por milhão de oportunidades
                # Aproximação do nível sigma
                if dpmo <= 3.4:
                    sigma_level = 6.0
                elif dpmo <= 233:
                    sigma_level = 5.0
                elif dpmo <= 6210:
                    sigma_level = 4.0
                elif dpmo <= 66807:
                    sigma_level = 3.0
                else:
                    sigma_level = 2.0
            else:
                sigma_level = 6.0
            
            st.metric("Nível Sigma", f"{sigma_level:.1f}σ")
        
        with col4:
            if kpis_ok == 3:
                risk = "Baixo"
                color = "🟢"
            elif kpis_ok >= 2:
                risk = "Médio"
                color = "🟡"
            else:
                risk = "Alto"
                color = "🔴"
            st.metric("Risco", f"{color} {risk}")
        
        # Gráfico de tendência dos KPIs
        if not kpis_df.empty:
            st.markdown("### 📈 Tendência dos KPIs")
            
            # Agrupa por data e KPI
            kpis_trend = kpis_df.pivot_table(
                index='measurement_date',
                columns='kpi_name',
                values='current_value',
                aggfunc='mean'
            ).reset_index()
            
            # Cria gráfico de linhas
            fig = go.Figure()
            
            for col in kpis_trend.columns[1:]:
                fig.add_trace(go.Scatter(
                    x=kpis_trend['measurement_date'],
                    y=kpis_trend[col],
                    mode='lines+markers',
                    name=col
                ))
            
            # Adiciona linha da meta principal
            if kpi1_name in kpis_trend.columns:
                fig.add_hline(y=kpi1_target, line_dash="dash", line_color="red",
                            annotation_text=f"Meta {kpi1_name}: {kpi1_target}%")
            
            fig.update_layout(
                title="Evolução dos KPIs ao Longo do Tempo",
                xaxis_title="Data",
                yaxis_title="Valor (%)",
                template="plotly_dark",
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Registre KPIs regularmente para ver a tendência")

with tab2:
    st.subheader("Gráficos de Controle Estatístico")
    
    # Busca histórico de KPIs para controle
    kpis_data = db.get_kpis(current_project_id)
    
    if not kpis_data.empty:
        # Seleciona KPI para controle
        kpi_names = kpis_data['kpi_name'].unique()
        selected_kpi = st.selectbox("Selecione o KPI para controle", kpi_names)
        
        # Filtra dados do KPI selecionado
        kpi_control = kpis_data[kpis_data['kpi_name'] == selected_kpi].sort_values('measurement_date')
        
        if len(kpi_control) >= 3:
            # Calcula limites de controle
            mean_val = kpi_control['current_value'].mean()
            std_val = kpi_control['current_value'].std()
            
            ucl = mean_val + 3 * std_val
            lcl = max(0, mean_val - 3 * std_val)
            uwl = mean_val + 2 * std_val
            lwl = max(0, mean_val - 2 * std_val)
            
            # Gráfico de controle
            fig = go.Figure()
            
            # Linha principal
            fig.add_trace(go.Scatter(
                x=kpi_control['measurement_date'],
                y=kpi_control['current_value'],
                mode='lines+markers',
                name=selected_kpi,
                line=dict(color='cyan', width=2),
                marker=dict(size=10)
            ))
            
            # Linha média
            fig.add_hline(y=mean_val, line_dash="solid", line_color="green",
                        annotation_text=f"Média: {mean_val:.2f}")
            
            # Limites de controle
            fig.add_hline(y=ucl, line_dash="dash", line_color="red",
                        annotation_text=f"UCL: {ucl:.2f}")
            fig.add_hline(y=lcl, line_dash="dash", line_color="red",
                        annotation_text=f"LCL: {lcl:.2f}")
            
            # Limites de aviso
            fig.add_hline(y=uwl, line_dash="dot", line_color="yellow",
                        annotation_text=f"UWL: {uwl:.2f}", opacity=0.5)
            fig.add_hline(y=lwl, line_dash="dot", line_color="yellow",
                        annotation_text=f"LWL: {lwl:.2f}", opacity=0.5)
            
            # Meta
            target_val = kpi_control['target_value'].iloc[0] if 'target_value' in kpi_control.columns else None
            if target_val:
                fig.add_hline(y=target_val, line_dash="dashdot", line_color="blue",
                            annotation_text=f"Meta: {target_val:.2f}")
            
            fig.update_layout(
                title=f"Gráfico de Controle - {selected_kpi}",
                xaxis_title="Data",
                yaxis_title=f"{selected_kpi} ({kpi_control['unit'].iloc[0] if 'unit' in kpi_control.columns else '%'})",
                template="plotly_dark",
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Análise de estabilidade
            st.markdown("### 📊 Análise de Estabilidade")
            
            # Verifica violações
            violations = []
            
            # Pontos fora dos limites de controle
            out_of_control = kpi_control[(kpi_control['current_value'] > ucl) | (kpi_control['current_value'] < lcl)]
            if len(out_of_control) > 0:
                violations.append(f"❌ {len(out_of_control)} pontos fora dos limites de controle")
            
            # Pontos fora dos limites de aviso
            out_of_warning = kpi_control[(kpi_control['current_value'] > uwl) | (kpi_control['current_value'] < lwl)]
            if len(out_of_warning) > 0:
                violations.append(f"⚠️ {len(out_of_warning)} pontos fora dos limites de aviso")
            
            # Tendência (7 pontos consecutivos crescentes ou decrescentes)
            if len(kpi_control) >= 7:
                diffs = kpi_control['current_value'].diff()
                for i in range(len(diffs) - 6):
                    if all(diffs.iloc[i:i+7] > 0) or all(diffs.iloc[i:i+7] < 0):
                        violations.append("📈 Tendência detectada (7+ pontos na mesma direção)")
                        break
            
            if violations:
                for v in violations:
                    st.warning(v)
            else:
                st.success("✅ Processo estatisticamente sob controle")
            
            # Capacidade do processo
            st.markdown("### 📏 Análise de Capacidade")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                lsl = st.number_input("LSL (Limite Inferior)", value=0.0, format="%.2f")
            with col2:
                usl = st.number_input("USL (Limite Superior)", 
                                     value=float(project.get('target_value', 10.0)), 
                                     format="%.2f")
            with col3:
                if st.button("Calcular Capacidade"):
                    if usl > lsl and std_val > 0:
                        # Índices de capacidade
                        cp = (usl - lsl) / (6 * std_val)
                        cpu = (usl - mean_val) / (3 * std_val)
                        cpl = (mean_val - lsl) / (3 * std_val)
                        cpk = min(cpu, cpl)
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Cp", f"{cp:.3f}")
                            st.caption("Capacidade potencial")
                        
                        with col2:
                            st.metric("Cpk", f"{cpk:.3f}")
                            if cpk >= 2.0:
                                st.caption("🌟 Nível Six Sigma")
                            elif cpk >= 1.33:
                                st.caption("✅ Processo capaz")
                            elif cpk >= 1.0:
                                st.caption("⚠️ Marginalmente capaz")
                            else:
                                st.caption("❌ Não capaz")
                        
                        with col3:
                            # PPM estimado
                            from scipy import stats
                            ppm_lsl = stats.norm.cdf(lsl, mean_val, std_val) * 1000000
                            ppm_usl = (1 - stats.norm.cdf(usl, mean_val, std_val)) * 1000000
                            ppm_total = ppm_lsl + ppm_usl
                            
                            st.metric("PPM Total", f"{ppm_total:.0f}")
                            st.caption("Defeitos por milhão")
        else:
            st.info("Registre mais medições para análise de controle (mínimo 3)")
    else:
        st.info("Registre KPIs na aba 'Dashboard KPIs' para criar gráficos de controle")

with tab3:
    st.subheader("📋 Plano de Controle")
    
    st.markdown("### ✅ Checklist de Controle")
    
    # Template de controle
    control_items = pd.DataFrame({
        'Item': [
            'Verificação de setup',
            'Inspeção de primeira peça',
            'Monitoramento de processo',
            'Análise de defeitos',
            'Calibração de instrumentos',
            'Auditoria de qualidade',
            'Treinamento de reforço',
            'Revisão de procedimentos'
        ],
        'Frequência': [
            'Cada setup',
            'Cada lote',
            'Horária',
            'Diária',
            'Mensal',
            'Semanal',
            'Mensal',
            'Trimestral'
        ],
        'Responsável': [
            'Operador',
            'Inspetor',
            'Operador',
            'Qualidade',
            'Metrologia',
            'Qualidade',
            'RH',
            'Engenharia'
        ],
        'Método': [
            'Check-list padrão',
            'Inspeção visual/dimensional',
            'Carta de controle',
            'Análise de Pareto',
            'Procedimento calibração',
            'Check-list auditoria',
            'Treinamento on-the-job',
            'Análise crítica'
        ],
        'Último Check': [
            datetime.now().date(),
            datetime.now().date(),
            datetime.now().date(),
            datetime.now().date() - timedelta(days=1),
            datetime.now().date() - timedelta(days=15),
            datetime.now().date() - timedelta(days=3),
            datetime.now().date() - timedelta(days=20),
            datetime.now().date() - timedelta(days=60)
        ],
        'Status': ['✅ OK', '✅ OK', '✅ OK', '✅ OK', '⚠️ Próximo', '✅ OK', '⚠️ Próximo', '✅ OK']
    })
    
    edited_control = st.data_editor(
        control_items,
        column_config={
            'Item': st.column_config.TextColumn('Item', width="large"),
            'Frequência': st.column_config.SelectboxColumn(
                'Frequência',
                options=['Cada setup', 'Cada lote', 'Horária', 'Diária', 'Semanal', 
                        'Quinzenal', 'Mensal', 'Trimestral', 'Semestral', 'Anual']
            ),
            'Último Check': st.column_config.DateColumn('Último Check', format="DD/MM/YYYY"),
            'Status': st.column_config.SelectboxColumn(
                'Status',
                options=['✅ OK', '⚠️ Próximo', '❌ Atrasado', '🔄 Em andamento']
            )
        },
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="control_checklist"
    )
    
    # Resumo do plano
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        ok_count = len(edited_control[edited_control['Status'] == '✅ OK'])
        st.metric("Itens OK", ok_count)
    
    with col2:
        pending = len(edited_control[edited_control['Status'].str.contains('⚠️')])
        st.metric("Próximos", pending)
    
    with col3:
        late = len(edited_control[edited_control['Status'].str.contains('❌')])
        st.metric("Atrasados", late)
    
    with col4:
        compliance = (ok_count / len(edited_control) * 100) if len(edited_control) > 0 else 0
        st.metric("Conformidade", f"{compliance:.0f}%")
    
    # Sistema de reação
    st.markdown("### 🚨 Plano de Reação")
    
    reaction_plan = pd.DataFrame({
        'Gatilho': [
            'Taxa defeitos > Meta + 2σ',
            'Taxa defeitos > Meta + 3σ',
            'Tendência crescente (3 pontos)',
            'Ponto fora de controle',
            'Reclamação cliente'
        ],
        'Ação Imediata': [
            'Verificar processo',
            'Parar produção',
            'Investigar causa',
            'Segregar produção',
            'Contenção imediata'
        ],
        'Responsável': [
            'Operador',
            'Supervisor',
            'Engenharia',
            'Qualidade',
            'Qualidade'
        ],
        'Escalonamento': [
            'Supervisor (30 min)',
            'Gerente (imediato)',
            'Engenharia (2h)',
            'Gerente (1h)',
            'Diretor (4h)'
        ]
    })
    
    st.dataframe(reaction_plan, use_container_width=True, hide_index=True)
    
    # Salvar plano
    if st.button("💾 Salvar Plano de Controle"):
        control_plan = {
            'checklist': edited_control.to_dict('records'),
            'reaction_plan': reaction_plan.to_dict('records'),
            'compliance': compliance
        }
        
        if db.save_report(current_project_id, 'CONTROL_PLAN', control_plan):
            st.success("✅ Plano de controle salvo!")

with tab4:
    st.subheader("📄 Relatório Final DMAIC")
    
    st.markdown(f"### Projeto: {project['name']}")
    
    # Coleta todas as informações do projeto
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Resumo do Projeto")
        st.write(f"**Problema:** {project.get('problem_statement', 'N/A')}")
        st.write(f"**Início:** {project.get('start_date', 'N/A')}")
        st.write(f"**Baseline:** {project.get('baseline_value', 'N/A')}{project.get('unit', '%')}")
        st.write(f"**Meta:** {project.get('target_value', 'N/A')}{project.get('unit', '%')}")
    
    with col2:
        st.markdown("### 🎯 Resultados Alcançados")
        
        # Busca último KPI registrado
        latest_kpis = db.get_kpis(current_project_id, limit=10)
        if not latest_kpis.empty:
            main_kpi = latest_kpis[latest_kpis['kpi_name'].str.contains('Defeito', case=False, na=False)]
            if not main_kpi.empty:
                current_value = main_kpi.iloc[0]['current_value']
            else:
                current_value = 8.5  # Valor default
        else:
            current_value = 8.5
        
        baseline_val = project.get('baseline_value', 15.0)
        improvement = baseline_val - current_value
        improvement_pct = (improvement / baseline_val * 100) if baseline_val > 0 else 0
        
        st.metric("Valor Atual", f"{current_value:.1f}{project.get('unit', '%')}")
        st.metric("Melhoria Absoluta", f"{improvement:.1f}{project.get('unit', '%')}")
        st.metric("Melhoria Percentual", f"{improvement_pct:.1f}%")
    
    # Análises realizadas
    st.markdown("### 📈 Análises Realizadas")
    
    # Conta análises
    reports = db.get_reports(current_project_id)
    datasets = db.list_datasets(current_project_id)
    ishikawa = db.get_ishikawa(current_project_id)
    action_plan = db.get_action_plan(current_project_id)
    
    analysis_summary = {
        'Datasets carregados': len(datasets),
        'Análises estatísticas': len([r for r in reports if 'TEST' in r['report_type'] or 'ANALYSIS' in r['report_type']]),
        'Análise Ishikawa': '✅' if ishikawa else '❌',
        'Plano de Ação': '✅' if action_plan else '❌',
        'KPIs registrados': len(db.get_kpis(current_project_id))
    }
    
    for key, value in analysis_summary.items():
        st.write(f"• **{key}:** {value}")
    
    # ROI do projeto
    st.markdown("### 💰 Retorno sobre Investimento (ROI)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        investment = st.number_input("Investimento Total (R$)", value=50000.00, format="%.2f")
    
    with col2:
        # Estima economia baseada na redução de defeitos
        production_volume = st.number_input("Volume Mensal", value=10000, format="%d")
        cost_per_defect = st.number_input("Custo por Defeito (R$)", value=50.00, format="%.2f")
    
    with col3:
        # Calcula economia
        defects_before = production_volume * (baseline_val / 100)
        defects_after = production_volume * (current_value / 100)
        monthly_savings = (defects_before - defects_after) * cost_per_defect
        annual_savings = monthly_savings * 12
        
        roi = ((annual_savings - investment) / investment * 100) if investment > 0 else 0
        payback = (investment / monthly_savings) if monthly_savings > 0 else 0
        
        st.metric("ROI Anual", f"{roi:.0f}%")
        st.metric("Payback", f"{payback:.1f} meses")
        st.metric("Economia Anual", f"R$ {annual_savings:,.2f}")
    
    # Lições aprendidas
    st.markdown("### 💡 Lições Aprendidas")
    
    lessons = st.text_area(
        "Principais aprendizados do projeto",
        value="""• A análise de dados revelou que o turno noturno tinha 2x mais defeitos
• Treinamento padronizado reduziu variabilidade entre operadores em 40%
• Implementação de inspeção na fonte preveniu 60% dos defeitos
• Controle estatístico de processo essencial para sustentabilidade
• Engajamento da equipe foi fator crítico de sucesso""",
        height=150
    )
    
    # Próximos passos
    st.markdown("### 🚀 Recomendações e Próximos Passos")
    
    recommendations = [
        "Manter monitoramento diário dos KPIs estabelecidos",
        "Expandir metodologia para outras linhas de produção",
        "Implementar sistema de gestão visual no chão de fábrica",
        "Revisar plano de controle trimestralmente",
        "Buscar certificação ISO 9001 com base nas melhorias"
    ]
    
    for i, rec in enumerate(recommendations, 1):
        st.write(f"{i}. {rec}")
    
    # Gerar relatório final
    st.markdown("### 📥 Exportar Relatório Final")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Salvar Relatório Final", type="primary", use_container_width=True):
            final_report = {
                'project': {
                    'name': project['name'],
                    'problem': project.get('problem_statement'),
                    'baseline': baseline_val,
                    'target': project.get('target_value'),
                    'current': current_value,
                    'improvement': improvement,
                    'improvement_pct': improvement_pct
                },
                'roi': {
                    'investment': investment,
                    'annual_savings': annual_savings,
                    'roi_pct': roi,
                    'payback_months': payback
                },
                'analyses': analysis_summary,
                'lessons': lessons,
                'recommendations': recommendations,
                'timestamp': datetime.now().isoformat()
            }
            
            if db.save_report(current_project_id, 'FINAL_REPORT', final_report):
                st.success("✅ Relatório Final salvo no banco de dados!")
                st.balloons()
                
                # Marca projeto como concluído se atingiu a meta
                if current_value <= project.get('target_value', 999):
                    st.success("🎉 PARABÉNS! META ATINGIDA!")
                    st.snow()
    
    with col2:
        # Gera PDF/Excel do relatório
        output = io.BytesIO()
        
        # Cria Excel com múltiplas abas
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Resumo
            summary_df = pd.DataFrame({
                'Métrica': ['Baseline', 'Meta', 'Atual', 'Melhoria', 'ROI'],
                'Valor': [
                    f"{baseline_val}{project.get('unit', '%')}",
                    f"{project.get('target_value')}{project.get('unit', '%')}",
                    f"{current_value}{project.get('unit', '%')}",
                    f"{improvement_pct:.1f}%",
                    f"{roi:.0f}%"
                ]
            })
            summary_df.to_excel(writer, sheet_name='Resumo', index=False)
            
            # KPIs
            if not kpis_df.empty:
                kpis_df.to_excel(writer, sheet_name='KPIs', index=False)
            
            # Plano de Ação
            if action_plan and isinstance(action_plan.get('actions'), list):
                pd.DataFrame(action_plan['actions']).to_excel(writer, sheet_name='Plano de Ação', index=False)
        
        st.download_button(
            label="📥 Baixar Relatório (Excel)",
            data=output.getvalue(),
            file_name=f"relatorio_final_{project['name']}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

with tab5:
    st.subheader("💾 Histórico Completo")
    
    # KPIs históricos
    with st.expander("📊 Histórico de KPIs"):
        kpis_hist = db.get_kpis(current_project_id, limit=100)
        if not kpis_hist.empty:
            st.dataframe(kpis_hist, use_container_width=True, hide_index=True)
            
            # Gráfico de evolução
            if st.checkbox("Mostrar gráfico de evolução"):
                fig = px.line(kpis_hist, x='measurement_date', y='current_value',
                            color='kpi_name', title='Evolução Histórica dos KPIs',
                            template='plotly_dark')
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhum KPI registrado ainda")
    
    # Todos os relatórios
    with st.expander("📄 Todos os Relatórios"):
        all_reports = db.get_reports(current_project_id)
        if all_reports:
            for report in all_reports:
                st.markdown(f"**{report['report_type']}** - {report['created_at'][:19]}")
                with st.expander(f"Ver conteúdo"):
                    st.json(report['content'])
        else:
            st.info("Nenhum relatório salvo ainda")
    
    # Estatísticas do projeto
    st.markdown("### 📈 Estatísticas do Projeto")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Relatórios", len(reports))
    
    with col2:
        st.metric("Datasets Salvos", len(datasets))
    
    with col3:
        st.metric("KPIs Registrados", len(kpis_df) if not kpis_df.empty else 0)
    
    with col4:
        days_active = (datetime.now() - pd.to_datetime(project['created_at'])).days
        st.metric("Dias Ativos", days_active)
