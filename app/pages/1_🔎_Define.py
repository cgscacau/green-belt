import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import json

# Configuração da página
st.set_page_config(
    page_title="Define - Green Belt Project",
    page_icon="🎯",
    layout="wide"
)

# Inicializar Supabase
from supabase import create_client, Client

@st.cache_resource
def init_supabase():
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY", "")
    if url and key:
        return create_client(url, key)
    return None

supabase = init_supabase()

if not supabase:
    st.error("⚠️ Supabase não configurado!")
    st.stop()

# Verificar projeto ativo
if 'current_project_id' not in st.session_state or not st.session_state.current_project_id:
    st.warning("⚠️ Nenhum projeto selecionado. Por favor, selecione ou crie um projeto na página inicial.")
    st.stop()

# Header
st.title("🎯 Define - Definição do Projeto")
st.info(f"📁 Projeto: **{st.session_state.get('current_project_name', 'Não identificado')}**")

# Carregar dados existentes do charter
try:
    charter_response = supabase.table('project_charter').select("*").eq('project_id', st.session_state.current_project_id).execute()
    existing_charter = charter_response.data[0] if charter_response.data else {}
except Exception as e:
    st.error(f"Erro ao carregar charter: {e}")
    existing_charter = {}

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋 Project Charter",
    "🎯 Metas & Métricas",
    "🔄 SIPOC",
    "👥 Stakeholders",
    "🗣️ VOC & CTQ",
    "⚠️ Riscos"
])

# Tab 1: Project Charter
with tab1:
    st.header("Project Charter")
    
    with st.form("charter_form"):
        st.subheader("1. Declaração do Problema")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            problem_statement = st.text_area(
                "Problem Statement*",
                value=existing_charter.get('problem_statement', ''),
                height=150,
                help="Descreva o problema de forma clara e específica. Use dados quando possível."
            )
            
            problem_impact = st.text_area(
                "Impacto do Problema",
                value=existing_charter.get('problem_impact', ''),
                height=100,
                help="Qual o impacto deste problema no negócio, clientes, colaboradores?"
            )
        
        with col2:
            problem_frequency = st.text_input(
                "Frequência do Problema",
                value=existing_charter.get('problem_frequency', ''),
                placeholder="Ex: 10 vezes por dia"
            )
            
            # Adicionar evidências do problema
            st.write("**Evidências do Problema:**")
            evidence_type = st.selectbox(
                "Tipo de Evidência",
                ["Dados históricos", "Reclamações de clientes", "Relatórios", "Auditorias", "Observações"]
            )
            evidence_description = st.text_input("Descrição da evidência")
        
        st.divider()
        
        st.subheader("2. Declaração da Meta")
        
        goal_statement = st.text_area(
            "Goal Statement*",
            value=existing_charter.get('goal_statement', ''),
            height=100,
            help="Defina claramente o que o projeto pretende alcançar"
        )
        
        st.divider()
        
        st.subheader("3. Caso de Negócio")
        
        col1, col2 = st.columns(2)
        
        with col1:
            business_case = st.text_area(
                "Business Case*",
                value=existing_charter.get('business_case', ''),
                height=100,
                help="Por que este projeto é importante para o negócio?"
            )
        
        with col2:
            strategic_alignment = st.text_area(
                "Alinhamento Estratégico",
                value=existing_charter.get('strategic_alignment', ''),
                height=100,
                help="Como este projeto se alinha com os objetivos estratégicos?"
            )
        
        st.divider()
        
        st.subheader("4. Escopo do Projeto")
        
        col1, col2 = st.columns(2)
        
        with col1:
            in_scope = st.text_area(
                "Dentro do Escopo*",
                value=existing_charter.get('in_scope', ''),
                height=150,
                placeholder="• Processo X\n• Departamento Y\n• Produto Z",
                help="O que ESTÁ incluído no projeto"
            )
        
        with col2:
            out_scope = st.text_area(
                "Fora do Escopo*",
                value=existing_charter.get('out_scope', ''),
                height=150,
                placeholder="• Sistema legado\n• Fornecedores externos\n• Outros departamentos",
                help="O que NÃO está incluído no projeto"
            )
        
        col1, col2 = st.columns(2)
        
        with col1:
            constraints = st.text_area(
                "Restrições",
                value=existing_charter.get('constraints', ''),
                height=100,
                help="Limitações de tempo, recursos, tecnologia, etc."
            )
        
        with col2:
            assumptions = st.text_area(
                "Premissas",
                value=existing_charter.get('assumptions', ''),
                height=100,
                help="Suposições consideradas verdadeiras para o projeto"
            )
        
        st.divider()
        
        st.subheader("5. Aprovação")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            approved_by = st.text_input(
                "Aprovado por",
                value=existing_charter.get('approved_by', '')
            )
        
        with col2:
            approval_date = st.date_input(
                "Data de Aprovação",
                value=datetime.strptime(existing_charter.get('approval_date', datetime.now().isoformat()), '%Y-%m-%d').date() if existing_charter.get('approval_date') else datetime.now().date()
            )
        
        with col3:
            approval_notes = st.text_input(
                "Observações da Aprovação",
                value=existing_charter.get('approval_notes', '')
            )
        
        submitted = st.form_submit_button("💾 Salvar Project Charter", type="primary")
        
        if submitted:
            # Preparar dados
            charter_data = {
                'project_id': st.session_state.current_project_id,
                'problem_statement': problem_statement,
                'problem_impact': problem_impact,
                'problem_frequency': problem_frequency,
                'goal_statement': goal_statement,
                'business_case': business_case,
                'strategic_alignment': strategic_alignment,
                'in_scope': in_scope,
                'out_scope': out_scope,
                'constraints': constraints,
                'assumptions': assumptions,
                'approved_by': approved_by,
                'approval_date': approval_date.isoformat(),
                'approval_notes': approval_notes
            }
            
            try:
                if existing_charter:
                    # Atualizar
                    response = supabase.table('project_charter').update(charter_data).eq('project_id', st.session_state.current_project_id).execute()
                else:
                    # Inserir
                    response = supabase.table('project_charter').insert(charter_data).execute()
                
                st.success("✅ Project Charter salvo com sucesso!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

# Tab 2: Metas e Métricas
with tab2:
    st.header("Metas e Métricas do Projeto")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Métrica Principal")
        
        with st.form("primary_metric_form"):
            metric_name = st.text_input(
                "Nome da Métrica*",
                value=existing_charter.get('primary_metric', ''),
                placeholder="Ex: Taxa de Defeitos, Tempo de Ciclo, Satisfação do Cliente"
            )
            
            col1_1, col2_1, col3_1 = st.columns(3)
            
            with col1_1:
                metric_current = st.number_input(
                    "Valor Atual (Baseline)",
                    value=float(existing_charter.get('primary_metric_current', 0)),
                    step=0.01
                )
            
            with col2_1:
                metric_target = st.number_input(
                    "Valor Meta",
                    value=float(existing_charter.get('primary_metric_target', 0)),
                    step=0.01
                )
            
            with col3_1:
                metric_unit = st.text_input(
                    "Unidade",
                    value=existing_charter.get('primary_metric_unit', ''),
                    placeholder="%, min, unidades, R$"
                )
            
            # Cálculo de melhoria
            if metric_current > 0:
                improvement = ((metric_target - metric_current) / metric_current) * 100
                if improvement < 0:
                    st.success(f"🎯 Meta de Redução: {abs(improvement):.1f}%")
                else:
                    st.success(f"🎯 Meta de Aumento: {improvement:.1f}%")
            
            save_metric = st.form_submit_button("Salvar Métrica Principal")
            
            if save_metric:
                try:
                    update_data = {
                        'primary_metric': metric_name,
                        'primary_metric_current': metric_current,
                        'primary_metric_target': metric_target,
                        'primary_metric_unit': metric_unit
                    }
                    
                    supabase.table('project_charter').update(update_data).eq('project_id', st.session_state.current_project_id).execute()
                    st.success("✅ Métrica principal atualizada!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Erro ao salvar métrica: {e}")
    
    with col2:
        st.subheader("Visualização da Meta")
        
        if existing_charter.get('primary_metric_current') and existing_charter.get('primary_metric_target'):
            current = float(existing_charter.get('primary_metric_current', 0))
            target = float(existing_charter.get('primary_metric_target', 0))
            
            # Gauge chart
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = current,
                delta = {'reference': target, 'relative': True},
                title = {'text': existing_charter.get('primary_metric', 'Métrica')},
                domain = {'x': [0, 1], 'y': [0, 1]},
                gauge = {
                    'axis': {'range': [None, max(current, target) * 1.2]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, target], 'color': "lightgray"},
                        {'range': [target, max(current, target) * 1.2], 'color': "gray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': target
                    }
                }
            ))
            
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    # Métricas Secundárias
    st.divider()
    st.subheader("Métricas Secundárias")
    
    # Carregar métricas secundárias existentes
    secondary_metrics = existing_charter.get('secondary_metrics', []) if existing_charter else []
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        with st.expander("➕ Adicionar Métrica Secundária", expanded=len(secondary_metrics) == 0):
            with st.form("secondary_metric_form"):
                sec_name = st.text_input("Nome da Métrica")
                
                col1_s, col2_s, col3_s = st.columns(3)
                
                with col1_s:
                    sec_current = st.number_input("Valor Atual", step=0.01)
                with col2_s:
                    sec_target = st.number_input("Valor Meta", step=0.01)
                with col3_s:
                    sec_unit = st.text_input("Unidade")
                
                add_secondary = st.form_submit_button("Adicionar")
                
                if add_secondary and sec_name:
                    new_metric = {
                        'name': sec_name,
                        'current': sec_current,
                        'target': sec_target,
                        'unit': sec_unit
                    }
                    
                    if not isinstance(secondary_metrics, list):
                        secondary_metrics = []
                    
                    secondary_metrics.append(new_metric)
                    
                    try:
                        supabase.table('project_charter').update({
                            'secondary_metrics': secondary_metrics
                        }).eq('project_id', st.session_state.current_project_id).execute()
                        
                        st.success(f"✅ Métrica '{sec_name}' adicionada!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Erro ao adicionar métrica: {e}")
    
    with col2:
        if secondary_metrics:
            st.write("**Métricas Cadastradas:**")
            for i, metric in enumerate(secondary_metrics):
                st.write(f"{i+1}. {metric['name']}")
                st.caption(f"   {metric['current']} → {metric['target']} {metric['unit']}")

# Tab 3: SIPOC
with tab3:
    st.header("Diagrama SIPOC")
    st.info("SIPOC: Suppliers → Inputs → Process → Outputs → Customers")
    
    with st.form("sipoc_form"):
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.subheader("Suppliers")
            suppliers = st.text_area(
                "Fornecedores",
                value='\n'.join(existing_charter.get('suppliers', [])) if existing_charter else '',
                height=300,
                placeholder="• Fornecedor 1\n• Fornecedor 2\n• Departamento X",
                help="Quem fornece as entradas para o processo?"
            )
        
        with col2:
            st.subheader("Inputs")
            inputs = st.text_area(
                "Entradas",
                value='\n'.join(existing_charter.get('inputs', [])) if existing_charter else '',
                height=300,
                placeholder="• Matéria-prima\n• Informações\n• Requisições",
                help="O que entra no processo?"
            )
        
        with col3:
            st.subheader("Process")
            process_steps = st.text_area(
                "Processo",
                value='\n'.join(existing_charter.get('process_steps', [])) if existing_charter else '',
                height=300,
                placeholder="1. Receber pedido\n2. Processar\n3. Validar\n4. Entregar",
                help="Principais etapas do processo (alto nível)"
            )
        
        with col4:
            st.subheader("Outputs")
            outputs = st.text_area(
                "Saídas",
                value='\n'.join(existing_charter.get('outputs', [])) if existing_charter else '',
                height=300,
                placeholder="• Produto final\n• Relatórios\n• Serviço entregue",
                help="O que sai do processo?"
            )
        
        with col5:
            st.subheader("Customers")
            customers = st.text_area(
                "Clientes",
                value='\n'.join(existing_charter.get('customers', [])) if existing_charter else '',
                height=300,
                placeholder="• Cliente final\n• Próximo processo\n• Departamento Y",
                help="Quem recebe as saídas do processo?"
            )
        
        save_sipoc = st.form_submit_button("💾 Salvar SIPOC", type="primary")
        
        if save_sipoc:
            sipoc_data = {
                'suppliers': [s.strip() for s in suppliers.split('\n') if s.strip()],
                'inputs': [i.strip() for i in inputs.split('\n') if i.strip()],
                'process_steps': [p.strip() for p in process_steps.split('\n') if p.strip()],
                'outputs': [o.strip() for o in outputs.split('\n') if o.strip()],
                'customers': [c.strip() for c in customers.split('\n') if c.strip()]
            }
            
            try:
                supabase.table('project_charter').update(sipoc_data).eq('project_id', st.session_state.current_project_id).execute()
                st.success("✅ SIPOC salvo com sucesso!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Erro ao salvar SIPOC: {e}")
    
    # Visualização do SIPOC
    if existing_charter and any([existing_charter.get('suppliers'), existing_charter.get('inputs'), 
                                  existing_charter.get('process_steps'), existing_charter.get('outputs'), 
                                  existing_charter.get('customers')]):
        
        st.divider()
        st.subheader("Visualização do Fluxo SIPOC")
        
        # Criar visualização simples
        sipoc_df = pd.DataFrame({
            'Suppliers': [', '.join(existing_charter.get('suppliers', [])[:3])],
            'Inputs': [', '.join(existing_charter.get('inputs', [])[:3])],
            'Process': [', '.join(existing_charter.get('process_steps', [])[:3])],
            'Outputs': [', '.join(existing_charter.get('outputs', [])[:3])],
            'Customers': [', '.join(existing_charter.get('customers', [])[:3])]
        })
        
        st.dataframe(sipoc_df, use_container_width=True, hide_index=True)

# Tab 4: Stakeholders
with tab4:
    st.header("Análise de Stakeholders")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Adicionar Stakeholder")
        
        with st.form("stakeholder_form"):
            stake_name = st.text_input("Nome/Departamento*")
            stake_role = st.text_input("Papel no Projeto")
            
            stake_influence = st.select_slider(
                "Influência",
                options=["Muito Baixa", "Baixa", "Média", "Alta", "Muito Alta"],
                value="Média"
            )
            
            stake_interest = st.select_slider(
                "Interesse",
                options=["Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"],
                value="Médio"
            )
            
            stake_strategy = st.text_area(
                "Estratégia de Engajamento",
                placeholder="Como engajar este stakeholder?"
            )
            
            add_stakeholder = st.form_submit_button("Adicionar Stakeholder")
            
            if add_stakeholder and stake_name:
                new_stakeholder = {
                    'name': stake_name,
                    'role': stake_role,
                    'influence': stake_influence,
                    'interest': stake_interest,
                    'strategy': stake_strategy
                }
                
                # Carregar stakeholders existentes
                stakeholders = existing_charter.get('stakeholders', []) if existing_charter else []
                if not isinstance(stakeholders, list):
                    stakeholders = []
                
                stakeholders.append(new_stakeholder)
                
                try:
                    supabase.table('project_charter').update({
                        'stakeholders': stakeholders
                    }).eq('project_id', st.session_state.current_project_id).execute()
                    
                    st.success(f"✅ Stakeholder '{stake_name}' adicionado!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Erro ao adicionar stakeholder: {e}")
    
    with col2:
        st.subheader("Matriz de Stakeholders")
        
        stakeholders = existing_charter.get('stakeholders', []) if existing_charter else []
        
        if stakeholders:
            # Criar matriz de influência x interesse
            influence_map = {"Muito Baixa": 1, "Baixa": 2, "Média": 3, "Alta": 4, "Muito Alta": 5}
            interest_map = {"Muito Baixo": 1, "Baixo": 2, "Médio": 3, "Alto": 4, "Muito Alto": 5}
            
            fig = go.Figure()
            
            for stakeholder in stakeholders:
                x = interest_map.get(stakeholder.get('interest', 'Médio'), 3)
                y = influence_map.get(stakeholder.get('influence', 'Média'), 3)
                
                fig.add_trace(go.Scatter(
                    x=[x],
                    y=[y],
                    mode='markers+text',
                    name=stakeholder['name'],
                    text=[stakeholder['name']],
                    textposition="top center",
                    marker=dict(size=15)
                ))
            
            # Adicionar quadrantes
            fig.add_shape(type="line", x0=3, y0=0, x1=3, y1=6, line=dict(color="Gray", width=1, dash="dash"))
            fig.add_shape(type="line", x0=0, y0=3, x1=6, y1=3, line=dict(color="Gray", width=1, dash="dash"))
            
            # Adicionar anotações dos quadrantes
            fig.add_annotation(x=1.5, y=4.5, text="Manter Satisfeito", showarrow=False, bgcolor="yellow", opacity=0.5)
            fig.add_annotation(x=4.5, y=4.5, text="Gerenciar de Perto", showarrow=False, bgcolor="red", opacity=0.5)
            fig.add_annotation(x=1.5, y=1.5, text="Monitorar", showarrow=False, bgcolor="lightblue", opacity=0.5)
            fig.add_annotation(x=4.5, y=1.5, text="Manter Informado", showarrow=False, bgcolor="lightgreen", opacity=0.5)
            
            fig.update_layout(
                title="Matriz de Stakeholders (Influência x Interesse)",
                xaxis_title="Interesse →",
                yaxis_title="Influência →",
                xaxis=dict(range=[0, 6], tickvals=[1,2,3,4,5], ticktext=["Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"]),
                yaxis=dict(range=[0, 6], tickvals=[1,2,3,4,5], ticktext=["Muito Baixa", "Baixa", "Média", "Alta", "Muito Alta"]),
                showlegend=True,
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Lista de stakeholders
            st.divider()
            st.subheader("Lista de Stakeholders")
            
            for i, stakeholder in enumerate(stakeholders):
                with st.expander(f"{i+1}. {stakeholder['name']}"):
                    col1_s, col2_s = st.columns(2)
                    with col1_s:
                        st.write(f"**Papel:** {stakeholder.get('role', 'N/A')}")
                        st.write(f"**Influência:** {stakeholder.get('influence', 'N/A')}")
                        st.write(f"**Interesse:** {stakeholder.get('interest', 'N/A')}")
                    with col2_s:
                        st.write(f"**Estratégia:** {stakeholder.get('strategy', 'N/A')}")
                    
                    if st.button(f"🗑️ Remover", key=f"remove_stake_{i}"):
                        stakeholders.pop(i)
                        try:
                            supabase.table('project_charter').update({
                                'stakeholders': stakeholders
                            }).eq('project_id', st.session_state.current_project_id).execute()
                            st.success("Stakeholder removido!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")
        else:
            st.info("Nenhum stakeholder cadastrado ainda.")

# Tab 5: VOC e CTQ
with tab5:
    st.header("Voz do Cliente (VOC) e Características Críticas para a Qualidade (CTQ)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🗣️ Voz do Cliente (VOC)")
        
        with st.form("voc_form"):
            voc_source = st.selectbox(
                "Fonte",
                ["Pesquisa", "Reclamação", "Feedback", "Entrevista", "Observação", "Dados históricos"]
            )
            
            voc_requirement = st.text_area(
                "Requisito/Necessidade do Cliente",
                placeholder="O que o cliente disse ou precisa?"
            )
            
            voc_priority = st.select_slider(
                "Prioridade",
                options=["Baixa", "Média", "Alta", "Crítica"]
            )
            
            voc_date = st.date_input("Data da Coleta")
            
            add_voc = st.form_submit_button("Adicionar VOC")
            
            if add_voc and voc_requirement:
                new_voc = {
                    'source': voc_source,
                    'requirement': voc_requirement,
                    'priority': voc_priority,
                    'date': voc_date.isoformat()
                }
                
                voc_data = existing_charter.get('voc_data', []) if existing_charter else []
                if not isinstance(voc_data, list):
                    voc_data = []
                
                voc_data.append(new_voc)
                
                try:
                    supabase.table('project_charter').update({
                        'voc_data': voc_data
                    }).eq('project_id', st.session_state.current_project_id).execute()
                    
                    st.success("✅ VOC adicionado!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Erro: {e}")
        
        # Listar VOCs
        voc_data = existing_charter.get('voc_data', []) if existing_charter else []
        
        if voc_data:
            st.divider()
            st.write("**VOCs Coletados:**")
            
            for i, voc in enumerate(voc_data):
                with st.expander(f"{voc['source']} - {voc['priority']}"):
                    st.write(f"**Requisito:** {voc['requirement']}")
                    st.write(f"**Data:** {voc['date']}")
                    
                    if st.button(f"🗑️ Remover", key=f"remove_voc_{i}"):
                        voc_data.pop(i)
                        try:
                            supabase.table('project_charter').update({
                                'voc_data': voc_data
                            }).eq('project_id', st.session_state.current_project_id).execute()
                            st.rerun()
                        except:
                            pass
    
    with col2:
        st.subheader("📊 Características Críticas para a Qualidade (CTQ)")
        
        with st.form("ctq_form"):
            ctq_characteristic = st.text_input(
                "Característica CTQ",
                placeholder="Ex: Tempo de resposta < 2 segundos"
            )
            
            ctq_metric = st.text_input(
                "Como medir?",
                placeholder="Ex: Tempo em segundos do clique até a resposta"
            )
            
            ctq_target = st.text_input(
                "Meta/Especificação",
                placeholder="Ex: < 2 segundos em 95% dos casos"
            )
            
            ctq_related_voc = st.text_input(
                "VOC Relacionado",
                placeholder="Qual necessidade do cliente isso atende?"
            )
            
            add_ctq = st.form_submit_button("Adicionar CTQ")
            
            if add_ctq and ctq_characteristic:
                new_ctq = {
                    'characteristic': ctq_characteristic,
                    'metric': ctq_metric,
                    'target': ctq_target,
                    'related_voc': ctq_related_voc
                }
                
                ctq_characteristics = existing_charter.get('ctq_characteristics', []) if existing_charter else []
                if not isinstance(ctq_characteristics, list):
                    ctq_characteristics = []
                
                ctq_characteristics.append(new_ctq)
                
                try:
                    supabase.table('project_charter').update({
                        'ctq_characteristics': ctq_characteristics
                    }).eq('project_id', st.session_state.current_project_id).execute()
                    
                    st.success("✅ CTQ adicionado!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Erro: {e}")
        
        # Listar CTQs
        ctq_characteristics = existing_charter.get('ctq_characteristics', []) if existing_charter else []
        
        if ctq_characteristics:
            st.divider()
            st.write("**CTQs Definidos:**")
            
            for i, ctq in enumerate(ctq_characteristics):
                with st.expander(f"CTQ {i+1}: {ctq['characteristic']}"):
                    st.write(f"**Métrica:** {ctq.get('metric', 'N/A')}")
                    st.write(f"**Meta:** {ctq.get('target', 'N/A')}")
                    st.write(f"**VOC Relacionado:** {ctq.get('related_voc', 'N/A')}")
                    
                    if st.button(f"🗑️ Remover", key=f"remove_ctq_{i}"):
                        ctq_characteristics.pop(i)
                        try:
                            supabase.table('project_charter').update({
                                'ctq_characteristics': ctq_characteristics
                            }).eq('project_id', st.session_state.current_project_id).execute()
                            st.rerun()
                        except:
                            pass

# Tab 6: Riscos
with tab6:
    st.header("Análise de Riscos do Projeto")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Adicionar Risco")
        
        with st.form("risk_form"):
            risk_description = st.text_area(
                "Descrição do Risco*",
                placeholder="Descreva o risco potencial"
            )
            
            risk_probability = st.select_slider(
                "Probabilidade",
                options=["Muito Baixa", "Baixa", "Média", "Alta", "Muito Alta"],
                value="Média"
            )
            
            risk_impact = st.select_slider(
                "Impacto",
                options=["Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"],
                value="Médio"
            )
            
            risk_mitigation = st.text_area(
                "Plano de Mitigação",
                placeholder="Como prevenir ou reduzir este risco?"
            )
            
            risk_owner = st.text_input("Responsável pelo Risco")
            
            add_risk = st.form_submit_button("Adicionar Risco")
            
            if add_risk and risk_description:
                # Calcular score do risco
                prob_score = {"Muito Baixa": 1, "Baixa": 2, "Média": 3, "Alta": 4, "Muito Alta": 5}
                impact_score = {"Muito Baixo": 1, "Baixo": 2, "Médio": 3, "Alto": 4, "Muito Alto": 5}
                
                risk_score = prob_score[risk_probability] * impact_score[risk_impact]
                
                new_risk = {
                    'risk': risk_description,
                    'probability': risk_probability,
                    'impact': risk_impact,
                    'score': risk_score,
                    'mitigation': risk_mitigation,
                    'owner': risk_owner
                }
                
                risks = existing_charter.get('risks', []) if existing_charter else []
                if not isinstance(risks, list):
                    risks = []
                
                risks.append(new_risk)
                
                try:
                    supabase.table('project_charter').update({
                        'risks': risks
                    }).eq('project_id', st.session_state.current_project_id).execute()
                    
                    st.success("✅ Risco adicionado!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Erro: {e}")
    
    with col2:
        st.subheader("Matriz de Riscos")
        
        risks = existing_charter.get('risks', []) if existing_charter else []
        
        if risks:
            # Criar matriz de riscos
            prob_map = {"Muito Baixa": 1, "Baixa": 2, "Média": 3, "Alta": 4, "Muito Alta": 5}
            impact_map = {"Muito Baixo": 1, "Baixo": 2, "Médio": 3, "Alto": 4, "Muito Alto": 5}
            
            fig = go.Figure()
            
            for i, risk in enumerate(risks):
                x = impact_map.get(risk.get('impact', 'Médio'), 3)
                y = prob_map.get(risk.get('probability', 'Média'), 3)
                
                # Cor baseada no score
                score = risk.get('score', 9)
                if score <= 6:
                    color = 'green'
                elif score <= 12:
                    color = 'yellow'
                else:
                    color = 'red'
                
                fig.add_trace(go.Scatter(
                    x=[x],
                    y=[y],
                    mode='markers+text',
                    name=f"Risco {i+1}",
                    text=[f"R{i+1}"],
                    textposition="middle center",
                    marker=dict(size=30, color=color),
                    hovertext=risk['risk'][:50]
                ))
            
            # Adicionar zonas de risco
            fig.add_shape(type="rect", x0=0, y0=0, x1=2, y1=2, fillcolor="lightgreen", opacity=0.2)
            fig.add_shape(type="rect", x0=2, y0=0, x1=4, y1=2, fillcolor="yellow", opacity=0.2)
            fig.add_shape(type="rect", x0=4, y0=0, x1=6, y1=2, fillcolor="orange", opacity=0.2)
            fig.add_shape(type="rect", x0=0, y0=2, x1=2, y1=4, fillcolor="yellow", opacity=0.2)
            fig.add_shape(type="rect", x0=2, y0=2, x1=4, y1=4, fillcolor="orange", opacity=0.2)
            fig.add_shape(type="rect", x0=4, y0=2, x1=6, y1=4, fillcolor="red", opacity=0.2)
            fig.add_shape(type="rect", x0=0, y0=4, x1=2, y1=6, fillcolor="orange", opacity=0.2)
            fig.add_shape(type="rect", x0=2, y0=4, x1=4, y1=6, fillcolor="red", opacity=0.2)
            fig.add_shape(type="rect", x0=4, y0=4, x1=6, y1=6, fillcolor="darkred", opacity=0.2)
            
            fig.update_layout(
                title="Matriz de Riscos (Probabilidade x Impacto)",
                xaxis_title="Impacto →",
                yaxis_title="Probabilidade →",
                xaxis=dict(range=[0, 6], tickvals=[1,2,3,4,5], ticktext=["Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"]),
                yaxis=dict(range=[0, 6], tickvals=[1,2,3,4,5], ticktext=["Muito Baixa", "Baixa", "Média", "Alta", "Muito Alta"]),
                showlegend=False,
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Lista de riscos
            st.divider()
            st.subheader("Lista de Riscos")
            
            # Ordenar por score
            sorted_risks = sorted(risks, key=lambda x: x.get('score', 0), reverse=True)
            
            for i, risk in enumerate(sorted_risks):
                score = risk.get('score', 0)
                
                if score <= 6:
                    color = "🟢"
                elif score <= 12:
                    color = "🟡"
                else:
                    color = "🔴"
                
                with st.expander(f"{color} Risco {i+1} (Score: {score})"):
                    st.write(f"**Descrição:** {risk['risk']}")
                    st.write(f"**Probabilidade:** {risk.get('probability', 'N/A')}")
                    st.write(f"**Impacto:** {risk.get('impact', 'N/A')}")
                    st.write(f"**Mitigação:** {risk.get('mitigation', 'N/A')}")
                    st.write(f"**Responsável:** {risk.get('owner', 'N/A')}")
        else:
            st.info("Nenhum risco identificado ainda.")

# Resumo e Status
st.divider()
st.header("📊 Resumo da Fase Define")

if existing_charter:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        completeness = 0
        if existing_charter.get('problem_statement'): completeness += 20
        if existing_charter.get('goal_statement'): completeness += 20
        if existing_charter.get('in_scope'): completeness += 15
        if existing_charter.get('primary_metric'): completeness += 15
        if existing_charter.get('stakeholders'): completeness += 15
        if existing_charter.get('risks'): completeness += 15
        
        st.metric("Completude", f"{completeness}%")
        st.progress(completeness / 100)
    
    with col2:
        stakeholder_count = len(existing_charter.get('stakeholders', []))
        st.metric("Stakeholders", stakeholder_count)
    
    with col3:
        risk_count = len(existing_charter.get('risks', []))
        st.metric("Riscos Identificados", risk_count)
    
    with col4:
        voc_count = len(existing_charter.get('voc_data', []))
        st.metric("VOCs Coletados", voc_count)
    
    # Atualizar fase do projeto se Define estiver completo
    if completeness >= 80:
        st.success("✅ Fase Define está substancialmente completa! Você pode prosseguir para a fase Measure.")
        
        if st.button("➡️ Avançar para Fase Measure"):
            try:
                supabase.table('projects').update({
                    'current_phase': 'Measure',
                    'progress_percentage': 20
                }).eq('id', st.session_state.current_project_id).execute()
                
                st.success("Projeto avançado para fase Measure!")
                st.info("Acesse a página Measure no menu lateral.")
                
            except Exception as e:
                st.error(f"Erro ao atualizar fase: {e}")
    else:
        st.warning(f"⚠️ Complete pelo menos 80% da fase Define para prosseguir (atual: {completeness}%)")
else:
    st.info("Preencha o Project Charter para começar.")

# Footer
st.markdown("---")
st.caption("🎯 Fase Define - Green Belt Project Management System")
