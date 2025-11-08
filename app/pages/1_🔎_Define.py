import streamlit as st
from pathlib import Path
from datetime import datetime, date
import json
from components.supabase_client import get_supabase_manager

st.set_page_config(page_title="Define", page_icon="🔎", layout="wide")

# Inicializa Supabase
db = get_supabase_manager()

st.header("🔎 Define — Definição do Projeto")

# Verifica se há projeto selecionado
current_project_id = st.session_state.get('current_project_id')
current_project = None

if current_project_id:
    current_project = db.get_project(current_project_id)
    if current_project:
        st.success(f"📂 Editando projeto: **{current_project['name']}**")
    else:
        st.error("Projeto não encontrado")
        current_project_id = None

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📋 Project Charter", "🎯 Metas SMART", "👥 Stakeholders", "📊 Projetos Salvos"])

with tab1:
    st.subheader("Project Charter")
    
    # Formulário com valores do projeto existente ou novos
    col1, col2 = st.columns(2)
    
    with col1:
        project_name = st.text_input(
            "Nome do Projeto *",
            value=current_project['name'] if current_project else "",
            placeholder="Ex: Redução de Defeitos na Linha A"
        )
        
        problem_statement = st.text_area(
            "Declaração do Problema *",
            value=current_project['problem_statement'] if current_project else "",
            placeholder="Descreva o problema atual de forma clara e específica",
            height=150
        )
        
        business_case = st.text_area(
            "Justificativa (Business Case)",
            value=current_project['business_case'] if current_project else "",
            placeholder="Por que este projeto é importante?",
            height=100
        )
    
    with col2:
        scope = st.text_area(
            "Escopo do Projeto",
            value=current_project['scope'] if current_project else "",
            placeholder="O que está incluído e excluído",
            height=100
        )
        
        # Datas
        col_date1, col_date2 = st.columns(2)
        with col_date1:
            start_date = st.date_input(
                "Data de Início",
                value=datetime.strptime(current_project['start_date'], '%Y-%m-%d').date() if current_project and current_project.get('start_date') else date.today()
            )
        with col_date2:
            end_date = st.date_input(
                "Data de Término",
                value=datetime.strptime(current_project['end_date'], '%Y-%m-%d').date() if current_project and current_project.get('end_date') else date.today()
            )
        
        # Métricas
        st.markdown("**Métricas do Projeto**")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            baseline_value = st.number_input(
                "Baseline Atual",
                value=float(current_project['baseline_value']) if current_project and current_project.get('baseline_value') else 0.0,
                format="%.2f"
            )
        with col_m2:
            target_value = st.number_input(
                "Meta",
                value=float(current_project['target_value']) if current_project and current_project.get('target_value') else 0.0,
                format="%.2f"
            )
        with col_m3:
            unit = st.text_input(
                "Unidade",
                value=current_project['unit'] if current_project and current_project.get('unit') else "%",
                placeholder="Ex: %, mg/L, pH"
            )
    
    # Botões de ação
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        if st.button("💾 Salvar Projeto", type="primary", use_container_width=True):
            if project_name and problem_statement:
                project_data = {
                    'name': project_name,
                    'problem_statement': problem_statement,
                    'business_case': business_case,
                    'scope': scope,
                    'start_date': start_date,
                    'end_date': end_date,
                    'baseline_value': baseline_value,
                    'target_value': target_value,
                    'unit': unit
                }
                
                if current_project_id:
                    # Atualiza projeto existente
                    if db.update_project(current_project_id, project_data):
                        st.success("✅ Projeto atualizado com sucesso!")
                        st.balloons()
                else:
                    # Cria novo projeto
                    project_id = db.create_project(project_data)
                    if project_id:
                        st.success(f"✅ Projeto criado com sucesso! ID: {project_id[:8]}...")
                        st.session_state['current_project_id'] = project_id
                        st.balloons()
                        st.rerun()
            else:
                st.error("Por favor, preencha ao menos o nome do projeto e a declaração do problema.")
    
    with col_btn2:
        if current_project_id and st.button("🔄 Recarregar", use_container_width=True):
            st.rerun()
    
    with col_btn3:
        if current_project_id and st.button("🗑️ Excluir Projeto", use_container_width=True):
            if st.checkbox("Confirmar exclusão"):
                # Implementar exclusão se necessário
                st.warning("Função de exclusão a ser implementada")

with tab2:
    st.subheader("Metas SMART")
    
    if current_project_id:
        st.info("Specific, Measurable, Achievable, Relevant, Time-bound")
        
        col1, col2 = st.columns(2)
        
        with col1:
            specific = st.text_area(
                "Específica (Specific)",
                placeholder="O que exatamente queremos alcançar?",
                key="smart_s"
            )
            
            measurable = st.text_area(
                "Mensurável (Measurable)",
                placeholder="Como mediremos o sucesso?",
                key="smart_m"
            )
            
            achievable = st.text_area(
                "Alcançável (Achievable)",
                placeholder="É realista com os recursos disponíveis?",
                key="smart_a"
            )
        
        with col2:
            relevant = st.text_area(
                "Relevante (Relevant)",
                placeholder="Por que isso importa para a organização?",
                key="smart_r"
            )
            
            time_bound = st.text_area(
                "Temporal (Time-bound)",
                placeholder="Qual o prazo para alcançar?",
                key="smart_t"
            )
        
        if st.button("💾 Salvar Metas SMART"):
            # Salva como parte do projeto ou em tabela separada
            smart_data = {
                'specific': specific,
                'measurable': measurable,
                'achievable': achievable,
                'relevant': relevant,
                'time_bound': time_bound
            }
            
            # Pode salvar como relatório
            if db.save_report(current_project_id, 'SMART_GOALS', smart_data):
                st.success("✅ Metas SMART salvas!")
    else:
        st.warning("Crie ou selecione um projeto primeiro")

with tab3:
    st.subheader("Mapa de Stakeholders")
    
    if current_project_id:
        st.markdown("**Matriz RACI**")
        st.caption("R: Responsible, A: Accountable, C: Consulted, I: Informed")
        
        # Template de stakeholders
        stakeholders_df = st.data_editor(
            pd.DataFrame({
                'Stakeholder': ['Gerente de Produção', 'Eng. Qualidade', 'Operador', 'Cliente'],
                'Papel': ['Sponsor', 'Líder', 'Executor', 'Beneficiário'],
                'RACI': ['A', 'R', 'R', 'I'],
                'Contato': ['gerente@empresa.com', 'eng@empresa.com', 'operador@empresa.com', 'cliente@empresa.com']
            }),
            num_rows="dynamic",
            use_container_width=True
        )
        
        if st.button("💾 Salvar Stakeholders"):
            if db.save_report(current_project_id, 'STAKEHOLDERS', stakeholders_df.to_dict()):
                st.success("✅ Stakeholders salvos!")
    else:
        st.warning("Crie ou selecione um projeto primeiro")

with tab4:
    st.subheader("📊 Projetos Salvos no Banco de Dados")
    
    # Lista todos os projetos
    projects = db.list_projects()
    
    if projects:
        import pandas as pd
        
        # Cria DataFrame para visualização
        projects_df = pd.DataFrame(projects)
        
        # Formata colunas
        display_columns = ['name', 'baseline_value', 'target_value', 'unit', 'created_at']
        projects_df = projects_df[display_columns]
        projects_df.columns = ['Nome', 'Baseline', 'Meta', 'Unidade', 'Criado em']
        projects_df['Criado em'] = pd.to_datetime(projects_df['Criado em']).dt.strftime('%Y-%m-%d %H:%M')
        
        # Mostra tabela
        selected_row = st.dataframe(
            projects_df,
            use_container_width=True,
            hide_index=True,
            selection_mode="single-row",
            on_select="rerun"
        )
        
        # Se uma linha foi selecionada
        if selected_row and selected_row.selection.rows:
            selected_idx = selected_row.selection.rows[0]
            selected_project = projects[selected_idx]
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📂 Abrir Projeto Selecionado", type="primary", use_container_width=True):
                    st.session_state['current_project_id'] = selected_project['id']
                    st.rerun()
            
            with col2:
                if st.button("📋 Ver Detalhes", use_container_width=True):
                    with st.expander("Detalhes do Projeto"):
                        st.json(selected_project)
        
        # Estatísticas
        st.markdown("### 📈 Estatísticas Gerais")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de Projetos", len(projects))
        with col2:
            active_count = sum(1 for p in projects if p.get('end_date') is None or datetime.strptime(p['end_date'], '%Y-%m-%d').date() >= date.today())
            st.metric("Projetos Ativos", active_count)
        with col3:
            avg_improvement = sum((p.get('baseline_value', 0) - p.get('target_value', 0)) for p in projects) / len(projects) if projects else 0
            st.metric("Melhoria Média Esperada", f"{avg_improvement:.1f}{projects[0].get('unit', '%') if projects else '%'}")
    else:
        st.info("Nenhum projeto salvo ainda. Crie seu primeiro projeto na aba 'Project Charter'.")
