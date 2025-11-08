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
        st.info("💡 Avalie cada causa: **Impacto** (1-10) = quanto afeta o problema | **Facilidade** (1-10) = quão fácil é resolver")
        
        # Coleta todas as causas preenchidas
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
                if item and item.strip():  # Verifica se não está vazio
                    causes_list.append({
                        "Categoria": category, 
                        "Causa": item,
                        "Impacto (1-10)": 5,  # Valor inicial
                        "Facilidade (1-10)": 5  # Valor inicial
                    })
        
        if causes_list:
            # Cria DataFrame com as causas
            priority_df = pd.DataFrame(causes_list)
            
            # Permite edição dos valores
            st.markdown("**Avalie cada causa:**")
            edited_df = st.data_editor(
                priority_df,
                column_config={
                    "Categoria": st.column_config.TextColumn(
                        "Categoria",
                        disabled=True,  # Não permite editar categoria
                        width="small"
                    ),
                    "Causa": st.column_config.TextColumn(
                        "Causa",
                        disabled=True,  # Não permite editar o texto da causa
                        width="large"
                    ),
                    "Impacto (1-10)": st.column_config.NumberColumn(
                        "Impacto (1-10)",
                        help="Quanto esta causa impacta o problema? (1=baixo, 10=alto)",
                        min_value=1,
                        max_value=10,
                        step=1,
                        default=5
                    ),
                    "Facilidade (1-10)": st.column_config.NumberColumn(
                        "Facilidade (1-10)",
                        help="Quão fácil é resolver esta causa? (1=difícil, 10=fácil)",
                        min_value=1,
                        max_value=10,
                        step=1,
                        default=5
                    )
                },
                use_container_width=True,
                hide_index=True,
                key="priority_editor_fixed"
            )
            
            # Calcula score de prioridade
            edited_df['Score'] = edited_df['Impacto (1-10)'] * edited_df['Facilidade (1-10)']
            edited_df = edited_df.sort_values('Score', ascending=False)
            
            # Mostra ranking completo
            st.markdown("### 📊 Ranking de Priorização")
            
            # Adiciona coluna de ranking
            edited_df['Ranking'] = range(1, len(edited_df) + 1)
            
            # Mostra tabela com cores
            def highlight_top3(s):
                """Destaca as top 3 causas"""
                if s.name == 'Ranking':
                    return ['background-color: gold' if v <= 3 else '' for v in s]
                elif s.name == 'Score':
                    max_score = s.max()
                    return ['background-color: rgba(0, 255, 0, 0.3)' if v >= max_score * 0.8 
                           else 'background-color: rgba(255, 255, 0, 0.2)' if v >= max_score * 0.5
                           else '' for v in s]
                return ['' for _ in s]
            
            # Mostra tabela formatada
            st.dataframe(
                edited_df[['Ranking', 'Causa', 'Categoria', 'Impacto (1-10)', 'Facilidade (1-10)', 'Score']].style.apply(highlight_top3),
                use_container_width=True,
                hide_index=True
            )
            
            # Destaca Top 3
            st.markdown("### 🏆 Top 3 Causas Prioritárias")
            top3 = edited_df.head(3)
            
            for idx, row in top3.iterrows():
                col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
                with col1:
                    st.metric("Posição", f"#{row['Ranking']}")
                with col2:
                    st.write(f"**{row['Causa']}**")
                    st.caption(f"Categoria: {row['Categoria']}")
                with col3:
                    st.metric("Score", row['Score'])
                with col4:
                    impact_emoji = "🔴" if row['Impacto (1-10)'] >= 8 else "🟡" if row['Impacto (1-10)'] >= 5 else "🟢"
                    facility_emoji = "✅" if row['Facilidade (1-10)'] >= 7 else "⚠️" if row['Facilidade (1-10)'] >= 4 else "❌"
                    st.write(f"Impacto: {impact_emoji}")
                    st.write(f"Facilidade: {facility_emoji}")
            
            # Salva causas priorizadas
            st.session_state['prioritized_causes'] = edited_df
            
            # Botão para exportar
            if st.button("💾 Salvar Análise de Causas"):
                csv = edited_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Baixar Análise (CSV)",
                    data=csv,
                    file_name=f"analise_causas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
                st.success("✅ Análise de causas salva!")
        else:
            st.warning("⚠️ Preencha pelo menos uma causa para fazer a priorização.")

# O resto do código continua igual...
