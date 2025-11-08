import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from components.supabase_client import get_supabase_manager

st.set_page_config(page_title="Improve", page_icon="🛠️", layout="wide")

# Inicializa Supabase
db = get_supabase_manager()

st.header("🛠️ Improve — Desenvolvimento e Implementação de Melhorias")

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
    st.caption(f"Meta: Reduzir de {project.get('baseline_value', 'N/A')}{project.get('unit', '%')} para {project.get('target_value', 'N/A')}{project.get('unit', '%')}")
else:
    st.error("Projeto não encontrado")
    st.stop()

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎯 Análise de Causas",
    "📊 Pareto",
    "📋 Plano de Ação",
    "🔮 Simulação",
    "💾 Análises Salvas"
])

with tab1:
    st.subheader("Diagrama de Ishikawa (Espinha de Peixe)")
    
    # Verifica se já existe análise salva
    existing_ishikawa = db.get_ishikawa(current_project_id)
    
    if existing_ishikawa:
        st.info("📌 Análise de Ishikawa existente encontrada. Você pode editar ou criar nova.")
        if st.button("📂 Carregar Análise Existente"):
            st.session_state['ishikawa_causes'] = existing_ishikawa.get('causes', {})
            if isinstance(existing_ishikawa.get('prioritization'), list):
                st.session_state['prioritized_causes'] = pd.DataFrame(existing_ishikawa['prioritization'])
            st.rerun()
    
    # Problema principal
    problem = st.text_input(
        "Problema Principal",
        value=project.get('problem_statement', 'Alta taxa de defeitos'),
        placeholder="Ex: Alta taxa de defeitos no processo"
    )
    
    if problem:
        st.markdown(f"### Análise de Causas: {problem}")
        
        # Recupera causas salvas ou usa novas
        saved_causes = st.session_state.get('ishikawa_causes', {})
        
        # 6M's do Ishikawa
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🧑 Mão de Obra (Man)**")
            man1 = st.text_input("Causa 1", key="man1", 
                               value=saved_causes.get('man', {}).get('causa1', ''),
                               placeholder="Ex: Falta de treinamento")
            man2 = st.text_input("Causa 2", key="man2",
                               value=saved_causes.get('man', {}).get('causa2', ''),
                               placeholder="Ex: Equipe reduzida")
            
            st.markdown("**🔧 Método (Method)**")
            method1 = st.text_input("Causa 1", key="method1",
                                  value=saved_causes.get('method', {}).get('causa1', ''),
                                  placeholder="Ex: Processo não padronizado")
            method2 = st.text_input("Causa 2", key="method2",
                                  value=saved_causes.get('method', {}).get('causa2', ''),
                                  placeholder="Ex: Falta de procedimentos")
            
            st.markdown("**📦 Material**")
            material1 = st.text_input("Causa 1", key="material1",
                                    value=saved_causes.get('material', {}).get('causa1', ''),
                                    placeholder="Ex: Matéria-prima fora de especificação")
            material2 = st.text_input("Causa 2", key="material2",
                                    value=saved_causes.get('material', {}).get('causa2', ''),
                                    placeholder="Ex: Fornecedor não qualificado")
        
        with col2:
            st.markdown("**⚙️ Máquina (Machine)**")
            machine1 = st.text_input("Causa 1", key="machine1",
                                   value=saved_causes.get('machine', {}).get('causa1', ''),
                                   placeholder="Ex: Equipamento descalibrado")
            machine2 = st.text_input("Causa 2", key="machine2",
                                   value=saved_causes.get('machine', {}).get('causa2', ''),
                                   placeholder="Ex: Manutenção inadequada")
            
            st.markdown("**📏 Medição (Measurement)**")
            measurement1 = st.text_input("Causa 1", key="measurement1",
                                       value=saved_causes.get('measurement', {}).get('causa1', ''),
                                       placeholder="Ex: Instrumento descalibrado")
            measurement2 = st.text_input("Causa 2", key="measurement2",
                                       value=saved_causes.get('measurement', {}).get('causa2', ''),
                                       placeholder="Ex: Método de medição inadequado")
            
            st.markdown("**🌍 Meio Ambiente (Environment)**")
            environment1 = st.text_input("Causa 1", key="environment1",
                                       value=saved_causes.get('environment', {}).get('causa1', ''),
                                       placeholder="Ex: Temperatura fora de controle")
            environment2 = st.text_input("Causa 2", key="environment2",
                                       value=saved_causes.get('environment', {}).get('causa2', ''),
                                       placeholder="Ex: Umidade excessiva")
        
        # Priorização de causas
        st.markdown("### Priorização de Causas Raiz")
        st.info("💡 Avalie cada causa: **Impacto** (1-10) = quanto afeta o problema | **Facilidade** (1-10) = quão fácil é resolver")
        
        # Coleta todas as causas preenchidas
        causes_dict = {
            'man': {'causa1': man1, 'causa2': man2},
            'method': {'causa1': method1, 'causa2': method2},
            'material': {'causa1': material1, 'causa2': material2},
            'machine': {'causa1': machine1, 'causa2': machine2},
            'measurement': {'causa1': measurement1, 'causa2': measurement2},
            'environment': {'causa1': environment1, 'causa2': environment2}
        }
        
        causes_list = []
        for category, items in [
            ("Mão de Obra", [man1, man2]),
            ("Método", [method1, method2]),
            ("Material", [material1, material2]),
            ("Máquina", [machine1, machine2]),
            ("Medição", [measurement1, measurement2]),
            ("Meio Ambiente", [environment1, environment2])
        ]:
            for item in items:
                if item and item.strip():
                    causes_list.append({
                        "Categoria": category,
                        "Causa": item,
                        "Impacto (1-10)": 5,
                        "Facilidade (1-10)": 5
                    })
        
        if causes_list:
            # Verifica se já existe priorização salva
            if 'prioritized_causes' in st.session_state and isinstance(st.session_state['prioritized_causes'], pd.DataFrame):
                priority_df = st.session_state['prioritized_causes']
                st.info("📌 Usando priorização salva. Edite conforme necessário.")
            else:
                priority_df = pd.DataFrame(causes_list)
            
            st.markdown("**Avalie cada causa:**")
            edited_df = st.data_editor(
                priority_df,
                column_config={
                    "Categoria": st.column_config.TextColumn("Categoria", disabled=True),
                    "Causa": st.column_config.TextColumn("Causa", disabled=True, width="large"),
                    "Impacto (1-10)": st.column_config.NumberColumn(
                        "Impacto (1-10)",
                        help="Quanto esta causa impacta o problema?",
                        min_value=1, max_value=10, step=1
                    ),
                    "Facilidade (1-10)": st.column_config.NumberColumn(
                        "Facilidade (1-10)",
                        help="Quão fácil é resolver esta causa?",
                        min_value=1, max_value=10, step=1
                    )
                },
                use_container_width=True,
                hide_index=True,
                key="priority_editor"
            )
            
            # Calcula score
            edited_df['Score'] = edited_df['Impacto (1-10)'] * edited_df['Facilidade (1-10)']
            edited_df = edited_df.sort_values('Score', ascending=False)
            
            # Mostra ranking
            st.markdown("### 📊 Ranking de Priorização")
            
            # Gráfico de bolhas
            fig = px.scatter(edited_df, 
                           x='Facilidade (1-10)', 
                           y='Impacto (1-10)',
                           size='Score',
                           color='Categoria',
                           hover_data=['Causa'],
                           title='Matriz de Priorização (Impacto vs Facilidade)',
                           template='plotly_dark')
            
            # Adiciona quadrantes
            fig.add_hline(y=5, line_dash="dash", line_color="gray", opacity=0.5)
            fig.add_vline(x=5, line_dash="dash", line_color="gray", opacity=0.5)
            
            # Adiciona anotações dos quadrantes
            fig.add_annotation(x=8, y=8, text="Quick Wins", showarrow=False, font=dict(size=12, color="green"))
            fig.add_annotation(x=2, y=8, text="Difícil mas Importante", showarrow=False, font=dict(size=12, color="orange"))
            fig.add_annotation(x=8, y=2, text="Baixa Prioridade", showarrow=False, font=dict(size=12, color="gray"))
            fig.add_annotation(x=2, y=2, text="Evitar", showarrow=False, font=dict(size=12, color="red"))
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Top 3 causas
            st.markdown("### 🏆 Top 3 Causas Prioritárias")
            top3 = edited_df.head(3)
            
            for idx, (_, row) in enumerate(top3.iterrows(), 1):
                col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
                with col1:
                    st.metric("Posição", f"#{idx}")
                with col2:
                    st.write(f"**{row['Causa']}**")
                    st.caption(f"Categoria: {row['Categoria']}")
                with col3:
                    st.metric("Score", row['Score'])
                with col4:
                    if row['Score'] >= 64:
                        st.success("🎯 Alta Prioridade")
                    elif row['Score'] >= 36:
                        st.warning("⚠️ Média Prioridade")
                    else:
                        st.info("ℹ️ Baixa Prioridade")
            
            # Salvar análise
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("💾 Salvar Análise de Ishikawa", type="primary", use_container_width=True):
                    # Salva no Supabase
                    if db.save_ishikawa(current_project_id, causes_dict, edited_df):
                        st.success("✅ Análise de Ishikawa salva no banco de dados!")
                        st.session_state['ishikawa_causes'] = causes_dict
                        st.session_state['prioritized_causes'] = edited_df
                        st.balloons()
            
            with col2:
                # Download CSV
                csv = edited_df.to_csv(index=False)
                st.download_button(
                    label="📥 Baixar Análise (CSV)",
                    data=csv,
                    file_name=f"ishikawa_{project['name']}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.warning("⚠️ Preencha pelo menos uma causa para fazer a priorização.")

with tab2:
    st.subheader("Análise de Pareto")
    
    # Verifica se há dados para análise
    if 'analysis_df' in st.session_state:
        df = st.session_state['analysis_df']
        
        st.markdown("### Pareto de Defeitos/Problemas")
        
        # Identifica colunas relevantes
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if categorical_cols and numeric_cols:
            cat_col = st.selectbox("Categoria (eixo X)", categorical_cols, key="pareto_cat")
            val_col = st.selectbox("Valor (eixo Y)", numeric_cols, key="pareto_val")
            
            if st.button("📊 Gerar Pareto"):
                # Agrupa dados
                pareto_data = df.groupby(cat_col)[val_col].sum().reset_index()
                pareto_data = pareto_data.sort_values(val_col, ascending=False)
                
                # Calcula percentual acumulado
                pareto_data['Percentual'] = (pareto_data[val_col] / pareto_data[val_col].sum() * 100).round(2)
                pareto_data['Acumulado'] = pareto_data['Percentual'].cumsum()
                
                # Cria gráfico de Pareto
                fig = go.Figure()
                
                # Barras
                fig.add_trace(go.Bar(
                    x=pareto_data[cat_col],
                    y=pareto_data[val_col],
                    name='Frequência',
                    marker_color='lightblue',
                    yaxis='y'
                ))
                
                # Linha acumulada
                fig.add_trace(go.Scatter(
                    x=pareto_data[cat_col],
                    y=pareto_data['Acumulado'],
                    name='% Acumulado',
                    line=dict(color='red', width=2),
                    marker=dict(size=8),
                    yaxis='y2'
                ))
                
                # Linha 80%
                fig.add_hline(y=80, line_dash="dash", line_color="green",
                            annotation_text="80%", yaxis='y2')
                
                # Layout
                fig.update_layout(
                    title=f'Análise de Pareto - {val_col} por {cat_col}',
                    template='plotly_dark',
                    yaxis=dict(title=val_col, side='left'),
                    yaxis2=dict(title='% Acumulado', side='right', overlaying='y', range=[0, 105]),
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Identifica causas vitais (80/20)
                vital_idx = pareto_data[pareto_data['Acumulado'] <= 80].index
                vital_causes = pareto_data.loc[vital_idx, cat_col].tolist()
                
                if not vital_causes and len(pareto_data) > 0:
                    vital_causes = [pareto_data.iloc[0][cat_col]]
                
                st.success(f"**Causas Vitais (Princípio 80/20):** {', '.join(map(str, vital_causes))}")
                st.info(f"Foque em {len(vital_causes)} de {len(pareto_data)} categorias para resolver 80% do problema")
                
                # Mostra tabela
                st.dataframe(pareto_data, use_container_width=True, hide_index=True)
                
                # Salvar análise
                if st.button("💾 Salvar Análise de Pareto"):
                    pareto_report = {
                        'category': cat_col,
                        'value': val_col,
                        'data': pareto_data.to_dict('records'),
                        'vital_causes': vital_causes
                    }
                    
                    if db.save_report(current_project_id, 'PARETO_ANALYSIS', pareto_report):
                        st.success("✅ Análise de Pareto salva!")
    else:
        st.info("Carregue dados na página Measure primeiro para análise de Pareto.")

with tab3:
    st.subheader("Plano de Ação 5W2H")
    
    st.info("5W2H: What, Why, Where, When, Who, How, How Much")
    
    # Verifica se já existe plano salvo
    existing_plan = db.get_action_plan(current_project_id)
    
    if existing_plan and isinstance(existing_plan.get('actions'), pd.DataFrame):
        st.info("📌 Plano de ação existente encontrado.")
        action_plan = existing_plan['actions']
    else:
        # Template de plano de ação baseado nas causas prioritárias
        if 'prioritized_causes' in st.session_state and isinstance(st.session_state['prioritized_causes'], pd.DataFrame):
            top_causes = st.session_state['prioritized_causes'].head(3)
            actions = []
            for _, cause in top_causes.iterrows():
                actions.append({
                    'What (O quê)': f"Eliminar: {cause['Causa']}",
                    'Why (Por quê)': f"Score de prioridade: {cause['Score']}",
                    'Where (Onde)': 'Linha de produção',
                    'When (Quando)': datetime.now().date() + timedelta(days=7),
                    'Who (Quem)': 'A definir',
                    'How (Como)': 'A definir',
                    'How Much (Quanto)': 0.0,
                    'Status': 'Não iniciado'
                })
            action_plan = pd.DataFrame(actions)
        else:
            # Template padrão
            action_plan = pd.DataFrame({
                'What (O quê)': ['Treinar equipe', 'Calibrar equipamentos', 'Revisar processos'],
                'Why (Por quê)': ['Reduzir erros humanos', 'Melhorar precisão', 'Padronizar operação'],
                'Where (Onde)': ['Sala de treinamento', 'Laboratório', 'Área de produção'],
                'When (Quando)': [
                    datetime.now().date() + timedelta(days=7),
                    datetime.now().date() + timedelta(days=14),
                    datetime.now().date() + timedelta(days=21)
                ],
                'Who (Quem)': ['RH', 'Manutenção', 'Engenharia'],
                'How (Como)': ['Workshop', 'Procedimento técnico', 'Kaizen'],
                'How Much (Quanto)': [5000.0, 2000.0, 1500.0],
                'Status': ['Não iniciado', 'Não iniciado', 'Não iniciado']
            })
    
    # Editor do plano
    edited_plan = st.data_editor(
        action_plan,
        column_config={
            'What (O quê)': st.column_config.TextColumn('What (O quê)', width="large"),
            'Why (Por quê)': st.column_config.TextColumn('Why (Por quê)', width="medium"),
            'When (Quando)': st.column_config.DateColumn('When (Quando)', format="DD/MM/YYYY"),
            'How Much (Quanto)': st.column_config.NumberColumn('How Much (Quanto)', format="R$ %.2f"),
            'Status': st.column_config.SelectboxColumn(
                'Status',
                options=['Não iniciado', 'Em andamento', 'Concluído', 'Cancelado']
            )
        },
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="action_plan_editor"
    )
    
    # Resumo do plano
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_actions = len(edited_plan)
        st.metric("Total de Ações", total_actions)
    
    with col2:
        total_cost = edited_plan['How Much (Quanto)'].sum()
        st.metric("Custo Total", f"R$ {total_cost:,.2f}")
    
    with col3:
        completed = len(edited_plan[edited_plan['Status'] == 'Concluído'])
        st.metric("Concluídas", f"{completed}/{total_actions}")
    
    with col4:
        progress = (completed / total_actions * 100) if total_actions > 0 else 0
        st.metric("Progresso", f"{progress:.0f}%")
    
    # Cronograma visual
    if 'When (Quando)' in edited_plan.columns and len(edited_plan) > 0:
        st.markdown("### 📅 Cronograma Visual")
        
        # Prepara dados para Gantt
        gantt_data = edited_plan.copy()
        gantt_data['Start'] = pd.to_datetime(gantt_data['When (Quando)'])
        gantt_data['Finish'] = gantt_data['Start'] + timedelta(days=7)  # Assume 1 semana por ação
        
        fig = px.timeline(
            gantt_data,
            x_start="Start",
            x_end="Finish",
            y="What (O quê)",
            color="Status",
            title="Cronograma de Ações",
            template="plotly_dark"
        )
        fig.update_yaxes(categoryorder="total ascending")
        st.plotly_chart(fig, use_container_width=True)
    
    # Matriz RACI
    st.markdown("### Matriz RACI")
    st.caption("R: Responsible, A: Accountable, C: Consulted, I: Informed")
    
    stakeholders = st.text_input(
        "Stakeholders (separados por vírgula)",
        value="Gerente, Supervisor, Operador, Qualidade",
        key="stakeholders_raci"
    ).split(',')
    
    if stakeholders and len(edited_plan) > 0:
        raci_matrix = pd.DataFrame(
            index=edited_plan['What (O quê)'],
            columns=[s.strip() for s in stakeholders if s.strip()]
        )
        raci_matrix = raci_matrix.fillna('I')  # Default: Informed
        
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
    else:
        edited_raci = None
    
    # Salvar plano
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Salvar Plano de Ação", type="primary", use_container_width=True):
            if db.save_action_plan(current_project_id, edited_plan, edited_raci, float(total_cost)):
                st.success("✅ Plano de ação salvo no banco de dados!")
                st.balloons()
    
    with col2:
        # Download Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            edited_plan.to_excel(writer, sheet_name='5W2H', index=False)
            if edited_raci is not None:
                edited_raci.to_excel(writer, sheet_name='RACI')
        
        st.download_button(
            label="📥 Baixar Plano (Excel)",
            data=output.getvalue(),
            file_name=f"plano_acao_{project['name']}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

with tab4:
    st.subheader("🔮 Simulação What-If")
    
    st.info("Simule o impacto das melhorias propostas")
    
    # Simulação baseada nos dados do projeto
    baseline = project.get('baseline_value', 15.0)
    target = project.get('target_value', 5.0)
    unit = project.get('unit', '%')
    
    st.markdown(f"### Simulador de Redução de Defeitos")
    st.caption(f"Baseline: {baseline}{unit} | Meta: {target}{unit}")
    
    # Fatores de melhoria
    st.markdown("**Ajuste os fatores de melhoria:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        training_impact = st.slider(
            "Impacto do Treinamento (%)",
            0, 50, 20,
            help="Redução esperada por melhor capacitação"
        )
        
        equipment_impact = st.slider(
            "Impacto da Calibração (%)",
            0, 50, 15,
            help="Redução esperada por equipamentos calibrados"
        )
        
        process_impact = st.slider(
            "Impacto da Padronização (%)",
            0, 50, 25,
            help="Redução esperada por processos padronizados"
        )
    
    with col2:
        material_impact = st.slider(
            "Impacto do Controle de Material (%)",
            0, 50, 10,
            help="Redução esperada por melhor controle de material"
        )
        
        environment_impact = st.slider(
            "Impacto do Controle Ambiental (%)",
            0, 50, 5,
            help="Redução esperada por controle ambiental"
        )
        
        synergy_factor = st.slider(
            "Fator de Sinergia (%)",
            -20, 20, 10,
            help="Efeito combinado das melhorias"
        )
    
    # Calcula impacto total
    total_reduction = training_impact + equipment_impact + process_impact + material_impact + environment_impact
    total_reduction = total_reduction * (1 + synergy_factor/100)
    
    # Novo valor simulado
    new_value = baseline * (1 - total_reduction/100)
    new_value = max(0, new_value)  # Não pode ser negativo
    
    # Mostra resultados
    st.markdown("### 📊 Resultados da Simulação")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Baseline", f"{baseline:.1f}{unit}")
    
    with col2:
        st.metric(
            "Valor Simulado",
            f"{new_value:.1f}{unit}",
            delta=f"{new_value - baseline:.1f}{unit}"
        )
    
    with col3:
        st.metric("Meta", f"{target:.1f}{unit}")
    
    with col4:
        achievement = ((baseline - new_value) / (baseline - target) * 100) if baseline != target else 0
        st.metric("Atingimento da Meta", f"{achievement:.0f}%")
    
    # Gráfico de barras comparativo
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=['Baseline', 'Simulado', 'Meta'],
        y=[baseline, new_value, target],
        marker_color=['red', 'yellow' if new_value > target else 'green', 'green'],
        text=[f'{baseline:.1f}{unit}', f'{new_value:.1f}{unit}', f'{target:.1f}{unit}'],
        textposition='outside'
    ))
    
    fig.update_layout(
        title='Comparação: Baseline vs Simulado vs Meta',
        yaxis_title=f'Taxa de Defeitos ({unit})',
        template='plotly_dark',
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Análise de viabilidade
    st.markdown("### 🎯 Análise de Viabilidade")
    
    if new_value <= target:
        st.success(f"✅ **Meta atingível!** Com as melhorias propostas, é possível reduzir de {baseline:.1f}{unit} para {new_value:.1f}{unit}, superando a meta de {target:.1f}{unit}.")
    elif new_value < baseline * 0.7:
        st.warning(f"⚠️ **Progresso significativo!** Redução de {baseline:.1f}{unit} para {new_value:.1f}{unit}, mas ainda acima da meta de {target:.1f}{unit}. Considere ações adicionais.")
    else:
        st.error(f"❌ **Melhorias insuficientes!** Redução de apenas {(baseline-new_value)/baseline*100:.1f}%. Revise o plano de ação.")
    
    # Breakdown do impacto
    st.markdown("### 📈 Contribuição de Cada Fator")
    
    factors_df = pd.DataFrame({
        'Fator': ['Treinamento', 'Calibração', 'Padronização', 'Material', 'Ambiente'],
        'Impacto (%)': [training_impact, equipment_impact, process_impact, material_impact, environment_impact],
        'Redução Absoluta': [
            baseline * training_impact/100,
            baseline * equipment_impact/100,
            baseline * process_impact/100,
            baseline * material_impact/100,
            baseline * environment_impact/100
        ]
    }).sort_values('Impacto (%)', ascending=False)
    
    fig = px.bar(factors_df, x='Fator', y='Impacto (%)',
                title='Contribuição de Cada Fator para Redução',
                template='plotly_dark',
                color='Impacto (%)',
                color_continuous_scale='Viridis')
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Salvar simulação
    if st.button("💾 Salvar Simulação"):
        simulation_data = {
            'baseline': baseline,
            'target': target,
            'simulated': new_value,
            'factors': {
                'training': training_impact,
                'equipment': equipment_impact,
                'process': process_impact,
                'material': material_impact,
                'environment': environment_impact,
                'synergy': synergy_factor
            },
            'total_reduction': total_reduction,
            'achievement': achievement
        }
        
        if db.save_report(current_project_id, 'SIMULATION', simulation_data):
            st.success("✅ Simulação salva!")
            st.session_state['last_simulation'] = simulation_data

with tab5:
    st.subheader("💾 Análises Salvas")
    
    # Busca análises de melhoria
    reports = db.get_reports(current_project_id)
    
    # Ishikawa
    ishikawa = db.get_ishikawa(current_project_id)
    if ishikawa:
        with st.expander("🎯 Análise de Ishikawa"):
            if isinstance(ishikawa.get('prioritization'), pd.DataFrame):
                st.dataframe(ishikawa['prioritization'], use_container_width=True)
            elif isinstance(ishikawa.get('prioritization'), list):
                st.dataframe(pd.DataFrame(ishikawa['prioritization']), use_container_width=True)
            st.caption(f"Salvo em: {ishikawa.get('created_at', 'N/A')}")
    
    # Plano de Ação
    action_plan = db.get_action_plan(current_project_id)
    if action_plan:
        with st.expander("📋 Plano de Ação 5W2H"):
            if isinstance(action_plan.get('actions'), pd.DataFrame):
                st.dataframe(action_plan['actions'], use_container_width=True)
            elif isinstance(action_plan.get('actions'), list):
                st.dataframe(pd.DataFrame(action_plan['actions']), use_container_width=True)
            st.metric("Custo Total", f"R$ {action_plan.get('total_cost', 0):,.2f}")
            st.caption(f"Salvo em: {action_plan.get('created_at', 'N/A')}")
    
    # Outras análises
    if reports:
        improvement_reports = [r for r in reports if r['report_type'] in ['PARETO_ANALYSIS', 'SIMULATION']]
        
        if improvement_reports:
            for report in improvement_reports:
                with st.expander(f"{report['report_type'].replace('_', ' ').title()} - {report['created_at'][:10]}"):
                    st.json(report['content'])
