import streamlit as st
import pandas as pd
import numpy as np  # se necessário
from pathlib import Path
from datetime import datetime  # se necessário
import sys

# Adiciona o diretório app ao path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

try:
    from components.upload_and_store import (
        init_catalog, save_upload, load_table_from_path, 
        curate_table, list_datasets, load_dataset, RESULTS
    )
    from components.stats_blocks import (
        desc_stats, detect_outliers, shapiro_test, 
        ttest_two_groups, anova_test, correlation_analysis, 
        ols_regression, levene_test, process_capability
    )
    from components.visual_blocks import (
        line_over_time, box_by_group, histogram_with_stats,
        scatter_with_regression, correlation_heatmap, 
        control_chart, pareto_chart, qq_plot
    )
    from components.data_catalog import show_catalog, dataset_selector
    from components.reports import render_html_report, save_analysis_manifest
except ImportError as e:
    st.error(f"Erro ao importar componentes: {e}")
    st.info("Verifique se todos os arquivos de componentes estão presentes.")
    st.stop()

st.set_page_config(page_title="Improve", page_icon="🛠️", layout="wide")
init_catalog()

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
        placeholder="Ex: Alta turbidez na água do Rio X"
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
                use_container_width=True
            )
            
            # Calcula score de prioridade
            edited_df['Score'] = edited_df['Impacto (1-10)'] * edited_df['Facilidade (1-10)']
            edited_df = edited_df.sort_values('Score', ascending=False)
            
            st.markdown("### Top 3 Causas Prioritárias")
            st.dataframe(
                edited_df.head(3)[['Causa', 'Score']],
                use_container_width=True
            )

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
            use_container_width=True
        )
        
        if not edited_pareto.empty:
            fig = pareto_chart(
                edited_pareto,
                'Categoria',
                'Frequência',
                title="Análise de Pareto - Causas"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Identifica causas vitais (80/20)
            edited_pareto = edited_pareto.sort_values('Frequência', ascending=False)
            edited_pareto['Cumsum'] = edited_pareto['Frequência'].cumsum()
            edited_pareto['Cumperc'] = 100 * edited_pareto['Cumsum'] / edited_pareto['Frequência'].sum()
            
            vital_causes = edited_pareto[edited_pareto['Cumperc'] <= 80]
            st.info(f"**Causas Vitais (Princípio 80/20):** {', '.join(vital_causes['Categoria'].tolist())}")
    
    else:
        datasets_df = list_datasets()
        if not datasets_df.empty:
            selected = st.selectbox("Selecione o dataset", datasets_df['name'].unique())
            df = load_dataset(selected)
            
            if not df.empty:
                cat_col = st.selectbox("Coluna de categoria", df.columns)
                val_col = st.selectbox("Coluna de valor", df.select_dtypes(include=['number']).columns)
                
                if st.button("Gerar Pareto"):
                    fig = pareto_chart(df, cat_col, val_col)
                    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Plano de Ação 5W2H")
    
    st.info("5W2H: What, Why, Where, When, Who, How, How Much")
    
    # Template de plano de ação
    action_plan = pd.DataFrame({
        'What (O quê)': ['Ação 1', 'Ação 2', 'Ação 3'],
        'Why (Por quê)': ['Razão 1', 'Razão 2', 'Razão 3'],
        'Where (Onde)': ['Local 1', 'Local 2', 'Local 3'],
        'When (Quando)': [datetime.now().date(), datetime.now().date() + timedelta(days=7), datetime.now().date() + timedelta(days=14)],
        'Who (Quem)': ['Responsável 1', 'Responsável 2', 'Responsável 3'],
        'How (Como)': ['Método 1', 'Método 2', 'Método 3'],
        'How Much (Quanto)': [1000.0, 2000.0, 1500.0],
        'Status': ['Não iniciado', 'Não iniciado', 'Não iniciado']
    })
    
    edited_plan = st.data_editor(
        action_plan,
        num_rows="dynamic",
        column_config={
            'When (Quando)': st.column_config.DateColumn(),
            'How Much (Quanto)': st.column_config.NumberColumn(
                format="R$ %.2f"
            ),
            'Status': st.column_config.SelectboxColumn(
                options=['Não iniciado', 'Em andamento', 'Concluído', 'Cancelado']
            )
        },
        use_container_width=True
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
        value="Gerente, Analista, Técnico, Consultor"
    ).split(',')
    
    if stakeholders and len(edited_plan) > 0:
        raci_matrix = pd.DataFrame(
            index=edited_plan['What (O quê)'],
            columns=[s.strip() for s in stakeholders]
        )
        
        # Preenche com valores padrão
        for col in raci_matrix.columns:
            raci_matrix[col] = 'I'
        
        edited_raci = st.data_editor(
            raci_matrix,
            column_config={
                col: st.column_config.SelectboxColumn(
                    options=['R', 'A', 'C', 'I', '-']
                ) for col in raci_matrix.columns
            },
            use_container_width=True
        )
    
    # Salvar plano
    if st.button("💾 Salvar Plano de Ação", type="primary"):
        plan_path = RESULTS / f"action_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        with pd.ExcelWriter(plan_path) as writer:
            edited_plan.to_excel(writer, sheet_name='5W2H', index=False)
            if 'edited_raci' in locals():
                edited_raci.to_excel(writer, sheet_name='RACI')
        
        st.success(f"✅ Plano de ação salvo: {plan_path.name}")
        
        # Salva manifesto
        manifest_id, _ = save_analysis_manifest(
            phase="improve",
            dataset_id="action_plan",
            parameters={"total_actions": total_actions, "total_cost": float(total_cost)},
            results={"plan_path": str(plan_path)}
        )

with tab4:
    st.subheader("Simulação What-If")
    
    st.info("Simule cenários de melhoria baseados nos modelos da fase Analyze")
    
    # Simulação simples baseada em regressão
    st.markdown("### Simulador de Impacto")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Variáveis de Entrada**")
        
        # Sliders para variáveis
        var1_baseline = st.number_input("pH - Baseline", value=6.8, step=0.1)
        var1_new = st.slider("pH - Novo", 5.0, 9.0, var1_baseline, 0.1)
        
        var2_baseline = st.number_input("Turbidez - Baseline", value=4.2, step=0.1)
        var2_new = st.slider("Turbidez - Nova", 0.0, 10.0, var2_baseline, 0.1)
        
        var3_baseline = st.number_input("NO3 - Baseline", value=2.1, step=0.1)
        var3_new = st.slider("NO3 - Novo", 0.0, 5.0, var3_baseline, 0.1)
    
    with col2:
        st.markdown("**Impacto Estimado**")
        
        # Cálculo simples de impacto (exemplo)
        # Em produção, usaria o modelo de regressão da fase Analyze
        
        impact_ph = (var1_new - var1_baseline) / var1_baseline * 100
        impact_turb = (var2_new - var2_baseline) / var2_baseline * 100
        impact_no3 = (var3_new - var3_baseline) / var3_baseline * 100
        
        # Score de qualidade (exemplo simplificado)
        quality_baseline = 100 - abs(var1_baseline - 7.0) * 10 - var2_baseline * 5 - var3_baseline * 10
        quality_new = 100 - abs(var1_new - 7.0) * 10 - var2_new * 5 - var3_new * 10
        
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
        if quality_new > quality_baseline:
            st.success(f"✅ Cenário de melhoria viável! Ganho estimado: {quality_new - quality_baseline:.1f} pontos")
        else:
            st.warning(f"⚠️ Cenário não apresenta melhoria significativa")
