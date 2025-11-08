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

from components.visual_blocks import pareto_chart

st.set_page_config(page_title="Improve", page_icon="🛠️", layout="wide")

st.header("🛠️ Improve — Desenvolvimento e Implementação de Melhorias")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 Análise de Causas",
    "📊 Pareto",
    "📋 Plano de Ação",
    "🔮 Simulação"
])

with tab1:
    st.subheader("Diagrama de Ishikawa (Espinha de Peixe)")
    
    # Problema principal
    problem = st.text_input(
        "Problema Principal",
        placeholder="Ex: Alta turbidez na água do Rio X",
        value="Alta turbidez na água"
    )
    
    if problem:
        st.markdown(f"### Análise de Causas: {problem}")
        
        # 6M's do Ishikawa
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🧑 Mão de Obra (Man)**")
            man1 = st.text_input("Causa 1", key="man1", placeholder="Ex: Falta de treinamento")
            man2 = st.text_input("Causa 2", key="man2", placeholder="Ex: Equipe reduzida")
            
            st.markdown("**🔧 Método (Method)**")
            method1 = st.text_input("Causa 1", key="method1", placeholder="Ex: Processo inadequado")
            method2 = st.text_input("Causa 2", key="method2", placeholder="Ex: Falta de padronização")
            
            st.markdown("**📦 Material**")
            material1 = st.text_input("Causa 1", key="material1", placeholder="Ex: Qualidade dos insumos")
            material2 = st.text_input("Causa 2", key="material2", placeholder="Ex: Fornecedor não conforme")
        
        with col2:
            st.markdown("**⚙️ Máquina (Machine)**")
            machine1 = st.text_input("Causa 1", key="machine1", placeholder="Ex: Equipamento obsoleto")
            machine2 = st.text_input("Causa 2", key="machine2", placeholder="Ex: Falta de manutenção")
            
            st.markdown("**📏 Medição (Measurement)**")
            measurement1 = st.text_input("Causa 1", key="measurement1", placeholder="Ex: Calibração incorreta")
            measurement2 = st.text_input("Causa 2", key="measurement2", placeholder="Ex: Frequência inadequada")
            
            st.markdown("**🌍 Meio Ambiente (Environment)**")
            environment1 = st.text_input("Causa 1", key="environment1", placeholder="Ex: Chuvas intensas")
            environment2 = st.text_input("Causa 2", key="environment2", placeholder="Ex: Temperatura elevada")
        
        # Priorização de causas
        st.markdown("### Priorização de Causas Raiz")
        
        causes = []
        for category, items in [
            ("Mão de Obra", [man1, man2]),
            ("Método", [method1, method2]),
            ("Material", [material1, material2]),
            ("Máquina", [machine1, machine2]),
            ("Medição", [measurement1, measurement2]),
            ("Meio Ambiente", [environment1, environment2])
        ]:
            for item in items:
                if item:
                    causes.append({"Categoria": category, "Causa": item})
        
        if causes:
            priority_df = pd.DataFrame(causes)
            priority_df['Impacto (1-10)'] = 5
            priority_df['Facilidade (1-10)'] = 5
            
            edited_df = st.data_editor(
                priority_df,
                column_config={
                    "Impacto (1-10)": st.column_config.NumberColumn(
                        min_value=1,
                        max_value=10,
                        step=1
                    ),
                    "Facilidade (1-10)": st.column_config.NumberColumn(
                        min_value=1,
                        max_value=10,
                        step=1
                    )
                },
                use_container_width=True,
                key="priority_editor"
            )
            
            # Calcula score de prioridade
            edited_df['Score'] = edited_df['Impacto (1-10)'] * edited_df['Facilidade (1-10)']
            edited_df = edited_df.sort_values('Score', ascending=False)
            
            st.markdown("### Top 3 Causas Prioritárias")
            st.dataframe(
                edited_df.head(3)[['Causa', 'Score']],
                use_container_width=True
            )
            
            # Salva causas priorizadas
            st.session_state['prioritized_causes'] = edited_df

with tab2:
    st.subheader("Análise de Pareto")
    
    # Permite entrada manual ou uso de dataset
    data_source = st.radio(
        "Fonte de dados",
        ["Entrada Manual", "Dataset Existente"]
    )
    
    if data_source == "Entrada Manual":
        st.markdown("### Entrada de Dados para Pareto")
        
        # Tabela editável
        pareto_data = pd.DataFrame({
            'Categoria': ['Causa A', 'Causa B', 'Causa C', 'Causa D', 'Causa E'],
            'Frequência': [45, 30, 15, 7, 3]
        })
        
        edited_pareto = st.data_editor(
            pareto_data,
            num_rows="dynamic",
            use_container_width=True,
            key="pareto_editor"
        )
        
        if not edited_pareto.empty and edited_pareto['Frequência'].sum() > 0:
            try:
                fig = pareto_chart(
                    edited_pareto,
                    'Categoria',
                    'Frequência',
                    title="Análise de Pareto - Causas"
                )
                st.plotly_chart(fig, use_container_width=True, key="pareto_plot")
                
                # Identifica causas vitais (80/20)
                edited_pareto = edited_pareto.sort_values('Frequência', ascending=False)
                edited_pareto['Cumsum'] = edited_pareto['Frequência'].cumsum()
                edited_pareto['Cumperc'] = 100 * edited_pareto['Cumsum'] / edited_pareto['Frequência'].sum()
                
                vital_causes = edited_pareto[edited_pareto['Cumperc'] <= 80]
                st.info(f"**Causas Vitais (Princípio 80/20):** {', '.join(vital_causes['Categoria'].tolist())}")
            except Exception as e:
                st.error(f"Erro ao criar gráfico de Pareto: {e}")
    
    else:
        if 'analysis_df' in st.session_state:
            df = st.session_state['analysis_df']
            
            cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            num_cols = df.select_dtypes(include=['number']).columns.tolist()
            
            if cat_cols and num_cols:
                cat_col = st.selectbox("Coluna de categoria", cat_cols, key="pareto_cat")
                val_col = st.selectbox("Coluna de valor", num_cols, key="pareto_val")
                
                if st.button("Gerar Pareto"):
                    try:
                        fig = pareto_chart(df, cat_col, val_col)
                        st.plotly_chart(fig, use_container_width=True, key="pareto_dataset_plot")
                    except Exception as e:
                        st.error(f"Erro ao gerar Pareto: {e}")
            else:
                st.warning("Dataset não possui colunas adequadas para análise de Pareto.")
        else:
            st.info("Nenhum dataset disponível. Processe dados na página Measure primeiro.")

with tab3:
    st.subheader("Plano de Ação 5W2H")
    
    st.info("5W2H: What, Why, Where, When, Who, How, How Much")
    
    # Template de plano de ação com dados válidos
    current_date = datetime.now().date()
    action_plan = pd.DataFrame({
        'What (O quê)': ['Treinar equipe', 'Calibrar equipamentos', 'Revisar processos'],
        'Why (Por quê)': ['Reduzir erros', 'Melhorar precisão', 'Padronizar operação'],
        'Where (Onde)': ['Sala de treinamento', 'Laboratório', 'Área de produção'],
        'When (Quando)': [
            current_date,
            current_date + timedelta(days=7),
            current_date + timedelta(days=14)
        ],
        'Who (Quem)': ['João Silva', 'Maria Santos', 'Pedro Costa'],
        'How (Como)': ['Workshop presencial', 'Procedimento técnico', 'Reunião de alinhamento'],
        'How Much (Quanto)': [1000.0, 2000.0, 1500.0],
        'Status': ['Não iniciado', 'Não iniciado', 'Não iniciado']
    })
    
    edited_plan = st.data_editor(
        action_plan,
        num_rows="dynamic",
        column_config={
            'When (Quando)': st.column_config.DateColumn(
                "When (Quando)",
                format="DD/MM/YYYY",
            ),
            'How Much (Quanto)': st.column_config.NumberColumn(
                "How Much (Quanto)",
                format="R$ %.2f"
            ),
            'Status': st.column_config.SelectboxColumn(
                "Status",
                options=['Não iniciado', 'Em andamento', 'Concluído', 'Cancelado']
            )
        },
        use_container_width=True,
        key="action_plan_editor"
    )
    
    # Resumo do plano
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_actions = len(edited_plan)
        st.metric("Total de Ações", total_actions)
    
    with col2:
        total_cost = edited_plan['How Much (Quanto)'].sum()
        st.metric("Custo Total", f"R$ {total_cost:,.2f}")
    
    with col3:
        completed = len(edited_plan[edited_plan['Status'] == 'Concluído'])
        st.metric("Ações Concluídas", f"{completed}/{total_actions}")
    
    # Matriz RACI
    st.markdown("### Matriz RACI")
    st.caption("R: Responsible, A: Accountable, C: Consulted, I: Informed")
    
    stakeholders = st.text_input(
        "Stakeholders (separados por vírgula)",
        value="Gerente, Analista, Técnico, Consultor",
        key="stakeholders_input"
    ).split(',')
    
    if stakeholders and len(edited_plan) > 0:
        raci_matrix = pd.DataFrame(
            index=edited_plan['What (O quê)'],
            columns=[s.strip() for s in stakeholders if s.strip()]
        )
        
        # Preenche com valores padrão
        for col in raci_matrix.columns:
            raci_matrix[col] = 'I'
        
        edited_raci = st.data_editor(
            raci_matrix,
            column_config={
                col: st.column_config.SelectboxColumn(
                    col,
                    options=['R', 'A', 'C', 'I', '-']
                ) for col in raci_matrix.columns
            },
            use_container_width=True,
            key="raci_editor"
        )
    
    # Salvar plano
    if st.button("💾 Salvar Plano de Ação", type="primary"):
        try:
            # Salva em JSON na sessão
            plan_data = {
                "timestamp": datetime.now().isoformat(),
                "actions": edited_plan.to_dict('records'),
                "total_cost": float(total_cost),
                "total_actions": total_actions
            }
            
            if 'edited_raci' in locals():
                plan_data["raci"] = edited_raci.to_dict()
            
            st.session_state['action_plan'] = plan_data
            
            # Download como CSV
            csv = edited_plan.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Baixar Plano (CSV)",
                data=csv,
                file_name=f"action_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
            st.success("✅ Plano de ação salvo com sucesso!")
            
        except Exception as e:
            st.error(f"Erro ao salvar plano: {e}")

with tab4:
    st.subheader("Simulação What-If")
    
    st.info("Simule cenários de melhoria baseados em variações de parâmetros")
    
    # Simulação simples
    st.markdown("### Simulador de Impacto")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Variáveis de Entrada**")
        
        # Sliders para variáveis
        var1_baseline = st.number_input("pH - Baseline", value=6.8, step=0.1, format="%.1f")
        var1_new = st.slider("pH - Novo", 5.0, 9.0, var1_baseline, 0.1, key="ph_slider")
        
        var2_baseline = st.number_input("Turbidez - Baseline", value=4.2, step=0.1, format="%.1f")
        var2_new = st.slider("Turbidez - Nova", 0.0, 10.0, var2_baseline, 0.1, key="turb_slider")
        
        var3_baseline = st.number_input("NO3 - Baseline", value=2.1, step=0.1, format="%.1f")
        var3_new = st.slider("NO3 - Novo", 0.0, 5.0, var3_baseline, 0.1, key="no3_slider")
    
    with col2:
        st.markdown("**Impacto Estimado**")
        
        # Cálculo simples de impacto
        impact_ph = ((var1_new - var1_baseline) / var1_baseline * 100) if var1_baseline != 0 else 0
        impact_turb = ((var2_new - var2_baseline) / var2_baseline * 100) if var2_baseline != 0 else 0
        impact_no3 = ((var3_new - var3_baseline) / var3_baseline * 100) if var3_baseline != 0 else 0
        
        # Score de qualidade (exemplo simplificado)
        # pH ideal = 7.0, menor turbidez = melhor, menor NO3 = melhor
        quality_baseline = max(0, 100 - abs(var1_baseline - 7.0) * 10 - var2_baseline * 5 - var3_baseline * 10)
        quality_new = max(0, 100 - abs(var1_new - 7.0) * 10 - var2_new * 5 - var3_new * 10)
        
        st.metric("Qualidade da Água - Baseline", f"{quality_baseline:.1f}")
        st.metric(
            "Qualidade da Água - Simulada",
            f"{quality_new:.1f}",
            delta=f"{quality_new - quality_baseline:.1f}"
        )
        
        st.markdown("**Variações**")
        st.metric("pH", f"{impact_ph:.1f}%", delta=f"{var1_new - var1_baseline:.2f}")
        st.metric("Turbidez", f"{impact_turb:.1f}%", delta=f"{var2_new - var2_baseline:.2f}")
        st.metric("NO3", f"{impact_no3:.1f}%", delta=f"{var3_new - var3_baseline:.2f}")
        
        # Recomendação baseada na simulação
        st.markdown("### Recomendação")
        if quality_new > quality_baseline + 5:
            st.success(f"✅ Cenário de melhoria significativa! Ganho estimado: {quality_new - quality_baseline:.1f} pontos")
        elif quality_new > quality_baseline:
            st.info(f"📊 Melhoria marginal. Ganho: {quality_new - quality_baseline:.1f} pontos")
        else:
            st.warning(f"⚠️ Cenário não apresenta melhoria. Perda: {abs(quality_new - quality_baseline):.1f} pontos")
        
        # Salvar simulação
        if st.button("💾 Salvar Simulação"):
            simulation_data = {
                "timestamp": datetime.now().isoformat(),
                "baseline": {
                    "pH": var1_baseline,
                    "turbidez": var2_baseline,
                    "NO3": var3_baseline,
                    "quality_score": quality_baseline
                },
                "simulated": {
                    "pH": var1_new,
                    "turbidez": var2_new,
                    "NO3": var3_new,
                    "quality_score": quality_new
                },
                "improvement": quality_new - quality_baseline
            }
            
            st.session_state['simulation'] = simulation_data
            st.success("✅ Simulação salva!")
            
            # Mostra JSON da simulação
            with st.expander("Ver dados da simulação"):
                st.json(simulation_data)
