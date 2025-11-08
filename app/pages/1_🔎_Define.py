import streamlit as st
from pathlib import Path
from datetime import datetime
import json
import sys

# Adiciona o diretório app ao path de forma mais robusta
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

try:
    from components.upload_and_store import init_catalog, save_upload, RESULTS
    from components.reports import render_html_report
except ImportError as e:
    st.error(f"Erro ao importar componentes: {e}")
    st.stop()

st.set_page_config(page_title="Define", page_icon="🔎", layout="wide")
init_catalog()

st.header("🔎 Define — Definição do Projeto")
st.markdown("Estabeleça o escopo, objetivos e metas do projeto DMAIC.")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📋 Project Charter", "🎯 Metas SMART", "👥 Stakeholders", "📄 Documentos"])

with tab1:
    st.subheader("Project Charter")
    
    col1, col2 = st.columns(2)
    
    with col1:
        project_name = st.text_input(
            "Nome do Projeto",
            placeholder="Ex: Redução de Poluição Rio X"
        )
        
        problem_statement = st.text_area(
            "Declaração do Problema",
            placeholder="Descreva o problema atual de forma clara e específica",
            height=150
        )
        
        business_case = st.text_area(
            "Justificativa (Business Case)",
            placeholder="Por que este projeto é importante?",
            height=100
        )
    
    with col2:
        project_scope = st.text_area(
            "Escopo do Projeto",
            placeholder="O que está incluído e excluído",
            height=100
        )
        
        # CTQs (Critical to Quality)
        st.markdown("**CTQs - Critical to Quality**")
        ctq1 = st.text_input("CTQ 1", placeholder="Ex: pH da água")
        ctq2 = st.text_input("CTQ 2", placeholder="Ex: Nível de turbidez")
        ctq3 = st.text_input("CTQ 3", placeholder="Ex: Concentração de NO3")
    
    # Timeline
    st.subheader("Cronograma")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        start_date = st.date_input("Data de Início")
    with col2:
        end_date = st.date_input("Data de Término")
    with col3:
        current_phase = st.selectbox(
            "Fase Atual",
            ["Define", "Measure", "Analyze", "Improve", "Control"]
        )

with tab2:
    st.subheader("Metas SMART")
    st.info("Specific, Measurable, Achievable, Relevant, Time-bound")
    
    col1, col2 = st.columns(2)
    
    with col1:
        specific = st.text_area(
            "Específica (Specific)",
            placeholder="O que exatamente queremos alcançar?"
        )
        
        measurable = st.text_area(
            "Mensurável (Measurable)",
            placeholder="Como mediremos o sucesso?"
        )
        
        achievable = st.text_area(
            "Alcançável (Achievable)",
            placeholder="É realista com os recursos disponíveis?"
        )
    
    with col2:
        relevant = st.text_area(
            "Relevante (Relevant)",
            placeholder="Por que isso importa para a organização?"
        )
        
        time_bound = st.text_area(
            "Temporal (Time-bound)",
            placeholder="Qual o prazo para alcançar?"
        )
        
        # Meta quantitativa
        st.markdown("**Meta Quantitativa**")
        metric_baseline = st.number_input("Baseline Atual", value=0.0)
        metric_target = st.number_input("Meta", value=0.0)
        metric_unit = st.text_input("Unidade", placeholder="Ex: mg/L, %, pH")

with tab3:
    st.subheader("Mapa de Stakeholders")
    
    # RACI Matrix simplificada
    st.markdown("**Matriz RACI**")
    
    stakeholder_data = []
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown("**Stakeholder**")
        sh1 = st.text_input("", key="sh1", placeholder="Nome/Cargo", label_visibility="collapsed")
        sh2 = st.text_input("", key="sh2", placeholder="Nome/Cargo", label_visibility="collapsed")
        sh3 = st.text_input("", key="sh3", placeholder="Nome/Cargo", label_visibility="collapsed")
    
    with col2:
        st.markdown("**R**esponsible")
        r1 = st.checkbox("", key="r1", label_visibility="collapsed")
        r2 = st.checkbox("", key="r2", label_visibility="collapsed")
        r3 = st.checkbox("", key="r3", label_visibility="collapsed")
    
    with col3:
        st.markdown("**A**ccountable")
        a1 = st.checkbox("", key="a1", label_visibility="collapsed")
        a2 = st.checkbox("", key="a2", label_visibility="collapsed")
        a3 = st.checkbox("", key="a3", label_visibility="collapsed")
    
    with col4:
        st.markdown("**C**onsulted")
        c1 = st.checkbox("", key="c1", label_visibility="collapsed")
        c2 = st.checkbox("", key="c2", label_visibility="collapsed")
        c3 = st.checkbox("", key="c3", label_visibility="collapsed")
    
    with col5:
        st.markdown("**I**nformed")
        i1 = st.checkbox("", key="i1", label_visibility="collapsed")
        i2 = st.checkbox("", key="i2", label_visibility="collapsed")
        i3 = st.checkbox("", key="i3", label_visibility="collapsed")

with tab4:
    st.subheader("Documentos de Referência")
    
    uploaded_file = st.file_uploader(
        "Upload de documentos relacionados",
        type=["pdf", "docx", "xlsx", "csv"],
        accept_multiple_files=True
    )
    
    if uploaded_file:
        for file in uploaded_file:
            if st.button(f"Salvar {file.name}"):
                fid, stored = save_upload(file, notes="Documento de referência - Define")
                st.success(f"Documento salvo: {file.name}")

# Botão para gerar Charter
st.divider()

if st.button("💾 Gerar Project Charter", type="primary"):
    if project_name and problem_statement:
        # Prepara dados
        charter_data = {
            "project_name": project_name,
            "problem_statement": problem_statement,
            "business_case": business_case,
            "scope": project_scope,
            "ctqs": [ctq1, ctq2, ctq3],
            "start_date": str(start_date),
            "end_date": str(end_date),
            "current_phase": current_phase,
            "smart_goals": {
                "specific": specific,
                "measurable": measurable,
                "achievable": achievable,
                "relevant": relevant,
                "time_bound": time_bound
            },
            "metrics": {
                "baseline": metric_baseline,
                "target": metric_target,
                "unit": metric_unit
            }
        }
        
        # Salva charter como JSON
        charter_path = RESULTS / f"charter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        charter_path.write_text(json.dumps(charter_data, indent=2))
        
        # Gera relatório HTML
        html_path = RESULTS / f"charter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        metrics = [
            {"label": "Baseline", "value": f"{metric_baseline} {metric_unit}"},
            {"label": "Meta", "value": f"{metric_target} {metric_unit}"},
            {"label": "Melhoria Esperada", "value": f"{abs(metric_target - metric_baseline):.1f} {metric_unit}"}
        ]
        
        recommendations = [
            f"Completar fase de Measure até {end_date}",
            "Engajar stakeholders identificados",
            "Validar CTQs com equipe técnica"
        ]
        
        html = render_html_report(
            title="Project Charter - " + project_name,
            project=project_name,
            summary=problem_statement,
            metrics=metrics,
            conclusions=business_case,
            recommendations=recommendations,
            out_html=html_path
        )
        
        st.success("✅ Project Charter salvo com sucesso!")
        st.balloons()
        
        # Mostra preview
        with st.expander("📄 Preview do Charter"):
            st.markdown(html, unsafe_allow_html=True)
    else:
        st.error("Por favor, preencha ao menos o nome do projeto e a declaração do problema.")
