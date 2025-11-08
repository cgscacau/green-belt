import streamlit as st
from supabase import create_client, Client
import pandas as pd
import json
from datetime import datetime, date
from typing import Optional, Dict, List, Any
import uuid

class SupabaseManager:
    def __init__(self):
        """Inicializa conexão com Supabase"""
        self.client = self._init_supabase()
        
    @st.cache_resource
    def _init_supabase(_self) -> Client:
        """Cria cliente Supabase com cache"""
        try:
            url = st.secrets["SUPABASE_URL"]
            key = st.secrets["SUPABASE_KEY"]
            return create_client(url, key)
        except Exception as e:
            st.error(f"Erro ao conectar com Supabase: {e}")
            st.info("Configure SUPABASE_URL e SUPABASE_KEY em Settings → Secrets")
            st.stop()
    
    # ========== PROJETOS ==========
    
    def create_project(self, project_data: Dict) -> Optional[str]:
        """Cria novo projeto"""
        try:
            # Converte dates para string
            if 'start_date' in project_data:
                project_data['start_date'] = str(project_data['start_date'])
            if 'end_date' in project_data:
                project_data['end_date'] = str(project_data['end_date'])
            
            response = self.client.table('projects').insert(project_data).execute()
            
            if response.data:
                project_id = response.data[0]['id']
                st.session_state['current_project_id'] = project_id
                return project_id
            return None
            
        except Exception as e:
            st.error(f"Erro ao criar projeto: {e}")
            return None
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """Busca projeto por ID"""
        try:
            response = self.client.table('projects').select("*").eq('id', project_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            st.error(f"Erro ao buscar projeto: {e}")
            return None
    
    def list_projects(self) -> List[Dict]:
        """Lista todos os projetos"""
        try:
            response = self.client.table('projects').select("*").order('created_at', desc=True).execute()
            return response.data
        except Exception as e:
            st.error(f"Erro ao listar projetos: {e}")
            return []
    
    def update_project(self, project_id: str, updates: Dict) -> bool:
        """Atualiza projeto"""
        try:
            # Converte dates para string
            if 'start_date' in updates:
                updates['start_date'] = str(updates['start_date'])
            if 'end_date' in updates:
                updates['end_date'] = str(updates['end_date'])
            
            updates['updated_at'] = datetime.now().isoformat()
            
            response = self.client.table('projects').update(updates).eq('id', project_id).execute()
            return bool(response.data)
        except Exception as e:
            st.error(f"Erro ao atualizar projeto: {e}")
            return False
    
    # ========== DATASETS ==========
    
    def save_dataset(self, project_id: str, name: str, df: pd.DataFrame) -> Optional[str]:
        """Salva dataset"""
        try:
            dataset_data = {
                'project_id': project_id,
                'name': name,
                'data': df.to_dict('records'),
                'columns_info': {
                    'columns': df.columns.tolist(),
                    'dtypes': df.dtypes.astype(str).to_dict()
                },
                'row_count': len(df)
            }
            
            response = self.client.table('datasets').insert(dataset_data).execute()
            return response.data[0]['id'] if response.data else None
            
        except Exception as e:
            st.error(f"Erro ao salvar dataset: {e}")
            return None
    
    def get_dataset(self, dataset_id: str) -> Optional[pd.DataFrame]:
        """Recupera dataset"""
        try:
            response = self.client.table('datasets').select("*").eq('id', dataset_id).execute()
            
            if response.data:
                data = response.data[0]['data']
                return pd.DataFrame(data)
            return None
            
        except Exception as e:
            st.error(f"Erro ao recuperar dataset: {e}")
            return None
    
    def list_datasets(self, project_id: str) -> List[Dict]:
        """Lista datasets do projeto"""
        try:
            response = self.client.table('datasets').select("*").eq('project_id', project_id).order('created_at', desc=True).execute()
            return response.data
        except Exception as e:
            st.error(f"Erro ao listar datasets: {e}")
            return []
    
    # ========== ANÁLISE ISHIKAWA ==========
    
    def save_ishikawa(self, project_id: str, causes: Dict, prioritization: pd.DataFrame) -> bool:
        """Salva análise Ishikawa"""
        try:
            data = {
                'project_id': project_id,
                'causes': causes,
                'prioritization': prioritization.to_dict('records') if isinstance(prioritization, pd.DataFrame) else prioritization
            }
            
            # Verifica se já existe
            existing = self.client.table('ishikawa_analysis').select("id").eq('project_id', project_id).execute()
            
            if existing.data:
                # Atualiza
                response = self.client.table('ishikawa_analysis').update(data).eq('project_id', project_id).execute()
            else:
                # Insere
                response = self.client.table('ishikawa_analysis').insert(data).execute()
            
            return bool(response.data)
            
        except Exception as e:
            st.error(f"Erro ao salvar Ishikawa: {e}")
            return False
    
    def get_ishikawa(self, project_id: str) -> Optional[Dict]:
        """Recupera análise Ishikawa"""
        try:
            response = self.client.table('ishikawa_analysis').select("*").eq('project_id', project_id).execute()
            
            if response.data:
                data = response.data[0]
                if 'prioritization' in data and data['prioritization']:
                    data['prioritization'] = pd.DataFrame(data['prioritization'])
                return data
            return None
            
        except Exception as e:
            st.error(f"Erro ao recuperar Ishikawa: {e}")
            return None
    
    # ========== PLANO DE AÇÃO ==========
    
    def save_action_plan(self, project_id: str, actions: pd.DataFrame, raci_matrix: pd.DataFrame = None, total_cost: float = 0) -> bool:
        """Salva plano de ação"""
        try:
            data = {
                'project_id': project_id,
                'actions': actions.to_dict('records') if isinstance(actions, pd.DataFrame) else actions,
                'raci_matrix': raci_matrix.to_dict() if isinstance(raci_matrix, pd.DataFrame) else raci_matrix,
                'total_cost': total_cost
            }
            
            # Verifica se já existe
            existing = self.client.table('action_plans').select("id").eq('project_id', project_id).execute()
            
            if existing.data:
                response = self.client.table('action_plans').update(data).eq('project_id', project_id).execute()
            else:
                response = self.client.table('action_plans').insert(data).execute()
            
            return bool(response.data)
            
        except Exception as e:
            st.error(f"Erro ao salvar plano de ação: {e}")
            return False
    
    def get_action_plan(self, project_id: str) -> Optional[Dict]:
        """Recupera plano de ação"""
        try:
            response = self.client.table('action_plans').select("*").eq('project_id', project_id).execute()
            
            if response.data:
                data = response.data[0]
                if 'actions' in data and data['actions']:
                    data['actions'] = pd.DataFrame(data['actions'])
                if 'raci_matrix' in data and data['raci_matrix']:
                    data['raci_matrix'] = pd.DataFrame(data['raci_matrix'])
                return data
            return None
            
        except Exception as e:
            st.error(f"Erro ao recuperar plano de ação: {e}")
            return None
    
    # ========== KPIs ==========
    
    def save_kpi(self, project_id: str, kpi_name: str, target: float, current: float, unit: str = "%") -> bool:
        """Salva KPI"""
        try:
            data = {
                'project_id': project_id,
                'kpi_name': kpi_name,
                'target_value': target,
                'current_value': current,
                'unit': unit,
                'measurement_date': date.today().isoformat()
            }
            
            response = self.client.table('kpis').insert(data).execute()
            return bool(response.data)
            
        except Exception as e:
            st.error(f"Erro ao salvar KPI: {e}")
            return False
    
    def get_kpis(self, project_id: str, limit: int = 100) -> pd.DataFrame:
        """Recupera histórico de KPIs"""
        try:
            response = self.client.table('kpis').select("*").eq('project_id', project_id).order('measurement_date', desc=True).limit(limit).execute()
            
            if response.data:
                return pd.DataFrame(response.data)
            return pd.DataFrame()
            
        except Exception as e:
            st.error(f"Erro ao recuperar KPIs: {e}")
            return pd.DataFrame()
    
    # ========== RELATÓRIOS ==========
    
    def save_report(self, project_id: str, report_type: str, content: Dict) -> bool:
        """Salva relatório"""
        try:
            data = {
                'project_id': project_id,
                'report_type': report_type,
                'content': content
            }
            
            response = self.client.table('reports').insert(data).execute()
            return bool(response.data)
            
        except Exception as e:
            st.error(f"Erro ao salvar relatório: {e}")
            return False
    
    def get_reports(self, project_id: str) -> List[Dict]:
        """Lista relatórios do projeto"""
        try:
            response = self.client.table('reports').select("*").eq('project_id', project_id).order('created_at', desc=True).execute()
            return response.data
        except Exception as e:
            st.error(f"Erro ao listar relatórios: {e}")
            return []

# Instância global
@st.cache_resource
def get_supabase_manager():
    """Retorna instância única do manager"""
    return SupabaseManager()
