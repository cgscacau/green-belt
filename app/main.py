import streamlit as st
from pathlib import Path
import yaml
from components.supabase_client import get_supabase_manager

st.set_page_config(
    page_title="Green_Belt DMAIC", 
    page_icon="🌿", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializa Supabase
db = get_supabase_manager()

# Header principal
st.title("🌿 Green_Belt DMAIC - Sistema com Persistência")
st.caption("Sistema completo de análise DMAIC com banco de dados Supabase")

# Seletor de Projeto na Sidebar
with st.sidebar:
    st.markdown("## 🗂️ Gerenciar Projetos")
    
    # Lista projetos existentes
    projects = db.list_projects()
    
    if projects:
        project_names = ["➕ Criar Novo Projeto"] + [p['name'] for p in projects]
        selected = st.selectbox(
            "Selecione um Projeto",
            project_names,
            key="project_selector"
        )
        
        if selected == "➕ Criar Novo Projeto":
            st.session_state['current_project_id'] = None
            st.info("👈 Vá para a página **Define** para criar um novo projeto")
        else:
            # Carrega projeto selecionado
            selected_project = next(p for p in projects if p['name'] == selected)
            st.session_state['current_project_id'] = selected_project['id']
            st.session_state['current_project'] = selected_project
            
            # Mostra info do projeto
            st.success(f"✅ Projeto Ativo: **{selected_project['name']}**")
            
            with st.expander("📊 Detalhes do Projeto"):
                st.caption(f"ID: {selected_project['id']}")
                st.caption(f"Criado: {selected_project['created_at'][:10]}")
                if selected_project.get('baseline_value'):
                    st.metric("Baseline", f"{selected_project['baseline_value']}{selected_project.get('unit', '%')}")
                if selected_project.get('target_value'):
                    st.metric("Meta", f"{selected_project['target_value']}{selected_project.get('unit', '%')}")
    else:
        st.info("Nenhum projeto encontrado")
        st.markdown("👉 Vá para **Define** para criar seu primeiro projeto")
    
    st.markdown("---")
    
    # Status do projeto atual
    if 'current_project_id' in st.session_state and st.session_state['current_project_id']:
        st.markdown("### 📈 Status do Projeto")
        
        project_id = st.session_state['current_project_id']
        
        # Verifica o que já foi feito
        datasets = db.list_datasets(project_id)
        ishikawa = db.get_ishikawa(project_id)
        action_plan = db.get_action_plan(project_id)
        kpis = db.get_kpis(project_id)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Datasets", len(datasets))
            st.metric("KPIs", len(kpis) if not kpis.empty else 0)
        with col2:
            st.metric("Ishikawa", "✅" if ishikawa else "❌")
            st.metric("Plano Ação", "✅" if action_plan else "❌")

# Conteúdo principal
tab1, tab2, tab3 = st.tabs(["📋 Sobre", "🎯 Como Usar", "📊 Status Global"])

with tab1:
    st.markdown("""
    ### Sistema DMAIC com Persistência de Dados
    
    Este sistema agora utiliza **Supabase** para armazenar todos os dados permanentemente.
    
    **Benefícios:**
    - ✅ Dados persistem mesmo após reboot
    - ✅ Múltiplos projetos simultâneos
    - ✅ Histórico completo de análises
    - ✅ Compartilhamento entre usuários
    - ✅ Backup automático na nuvem
    
    ### Metodologia DMAIC
    
    - **D**efine: Definir o problema e objetivos
    - **M**easure: Medir e coletar dados
    - **A**nalyze: Analisar dados e identificar causas
    - **I**mprove: Implementar melhorias
    - **C**ontrol: Controlar e monitorar resultados
    """)

with tab2:
    st.markdown("""
    ### 🚀 Quick Start
    
    1. **Selecione ou crie um projeto** na barra lateral
    2. **Define** → Configure o projeto e defina objetivos
    3. **Measure** → Faça upload dos dados
    4. **Analyze** → Execute análises estatísticas
    5. **Improve** → Crie planos de ação
    6. **Control** → Monitore indicadores
    
    ### 💾 Persistência Automática
    
    - Todos os dados são salvos automaticamente no Supabase
    - Não é necessário fazer backup manual
    - Acesse seus projetos de qualquer lugar
    """)

with tab3:
    st.markdown("### 📊 Visão Global de Todos os Projetos")
    
    all_projects = db.list_projects()
    
    if all_projects:
        # Cria DataFrame com resumo
        import pandas as pd
        
        summary_data = []
        for proj in all_projects:
            proj_id = proj['id']
            datasets = db.list_datasets(proj_id)
            kpis = db.get_kpis(proj_id)
            
            summary_data.append({
                'Projeto': proj['name'],
                'Criado': proj['created_at'][:10],
                'Baseline': f"{proj.get('baseline_value', 'N/A')}",
                'Meta': f"{proj.get('target_value', 'N/A')}",
                'Datasets': len(datasets),
                'KPIs': len(kpis) if not kpis.empty else 0,
                'Status': '🟢 Ativo' if proj['id'] == st.session_state.get('current_project_id') else '⚪ Inativo'
            })
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
        
        # Métricas globais
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Projetos", len(all_projects))
        with col2:
            total_datasets = sum([len(db.list_datasets(p['id'])) for p in all_projects])
            st.metric("Total de Datasets", total_datasets)
        with col3:
            active_projects = sum(1 for p in all_projects if p.get('end_date') is None)
            st.metric("Projetos Ativos", active_projects)
    else:
        st.info("Nenhum projeto criado ainda. Comece criando um novo projeto na página Define.")

# Footer
st.divider()
st.markdown("""
<small>
💡 **Dica:** Todos os dados são salvos automaticamente no Supabase. 
Você pode fechar o navegador e retornar a qualquer momento sem perder nada!
</small>
""", unsafe_allow_html=True)
