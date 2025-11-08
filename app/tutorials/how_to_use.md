# Como Usar o Sistema DMAIC Greenpeace

## 🚀 Início Rápido

### Passo 1: Define (Definir Projeto)
1. Acesse a página **🔎 Define** no menu lateral
2. Preencha o **Project Charter**:
   - Nome do projeto
   - Declaração do problema
   - Justificativa (por que é importante?)
   - Escopo (o que está incluído/excluído)
3. Defina as **Metas SMART**
4. Identifique **Stakeholders** e crie matriz RACI
5. Clique em **"Gerar Project Charter"**

### Passo 2: Measure (Coletar Dados)
1. Vá para **📏 Measure**
2. Na aba **Upload**:
   - Faça upload do arquivo CSV ou Excel
   - Adicione observações (opcional)
   - Clique em **"Salvar no Catálogo"**
3. Na aba **Validação**:
   - Revise a qualidade dos dados
   - Nomeie o dataset
   - Clique em **"Padronizar e Salvar como Parquet"**
4. Na aba **Estatísticas**:
   - Visualize estatísticas descritivas
   - Identifique outliers
   - Gere relatório de medição

### Passo 3: Analyze (Analisar Dados)
1. Acesse **📊 Analyze**
2. Selecione o dataset padronizado
3. Execute análises:
   - **Exploratória:** Visualize tendências e distribuições
   - **Normalidade:** Teste Shapiro-Wilk e Q-Q Plot
   - **Comparações:** Teste t ou ANOVA
   - **Correlações:** Matriz de correlação
   - **Regressão:** Modelagem preditiva
4. Gere **Relatório de Análise**

### Passo 4: Improve (Implementar Melhorias)
1. Navegue para **🛠️ Improve**
2. Na aba **Análise de Causas**:
   - Preencha diagrama de Ishikawa
   - Priorize causas por impacto × facilidade
3. Na aba **Pareto**:
   - Identifique causas vitais (80/20)
4. Na aba **Plano de Ação**:
   - Crie plano 5W2H
   - Defina matriz RACI
   - Salve plano de ação
5. Na aba **Simulação**:
   - Teste cenários what-if

### Passo 5: Control (Monitorar Resultados)
1. Acesse **✅ Control**
2. Configure **Dashboard de KPIs**:
   - Defina métricas e metas
   - Monitore tendências
3. Crie **Gráficos de Controle**
4. Estabeleça **Plano de Controle**:
   - Checklist de atividades
   - Sistema de alertas
5. Gere **Relatório Final DMAIC**

## 📁 Trabalhando com Dados

### Formatos Aceitos
- **CSV:** Separado por vírgula ou ponto-vírgula
- **Excel:** .xlsx ou .xls
- **PDF:** Para documentação de referência

### Dataset de Exemplo
Use `sample_data/greenpeace_example.csv` para testar o sistema:
- Contém dados de qualidade de água
- Métricas: pH, Turbidez, NO3
- Múltiplos sites e datas

### Padronização Automática
O sistema automaticamente:
- Converte nomes de colunas (lowercase, underscore)
- Remove espaços extras
- Identifica tipos de dados
- Salva em formato Parquet otimizado

## 📊 Interpretando Resultados

### Testes Estatísticos
- **p-valor < 0.05:** Resultado estatisticamente significativo
- **p-valor ≥ 0.05:** Sem evidência estatística suficiente

### Gráficos de Controle
- **Dentro dos limites:** Processo sob controle
- **Fora dos limites:** Investigar causa especial
- **Tendências:** 7+ pontos crescentes/decrescentes

### Capacidade do Processo
- **Cpk < 1.00:** Processo precisa melhoria urgente
- **Cpk ≥ 1.33:** Processo capaz
- **Cpk ≥ 2.00:** Excelência (nível Six Sigma)

## 💡 Dicas e Boas Práticas

### Qualidade dos Dados
✅ **Faça:**
- Valide dados antes de análises
- Documente fonte e data de coleta
- Trate valores ausentes adequadamente

❌ **Evite:**
- Ignorar outliers sem investigação
- Misturar dados de períodos muito diferentes
- Assumir normalidade sem testar

### Análises Estatísticas
✅ **Faça:**
- Verifique pressupostos dos testes
- Use visualizações para explorar dados
- Documente decisões e interpretações

❌ **Evite:**
- P-hacking (testar até achar significância)
- Ignorar tamanho de efeito
- Confundir correlação com causalidade

### Relatórios
✅ **Faça:**
- Seja claro e objetivo
- Use visualizações apropriadas
- Inclua contexto e interpretações

❌ **Evite:**
- Jargão técnico excessivo
- Gráficos sem legendas/títulos
- Conclusões sem suporte dos dados

## 🆘 Troubleshooting

### Problema: Upload falha
**Soluções:**
- Verifique tamanho do arquivo (< 200MB)
- Confirme formato (CSV/Excel)
- Remova caracteres especiais do nome

### Problema: Teste estatístico não executa
**Soluções:**
- Verifique se há dados suficientes (n ≥ 3)
- Confirme que variáveis são numéricas
- Remova ou trate valores ausentes

### Problema: Gráfico não aparece
**Soluções:**
- Recarregue a página (F5)
- Verifique seleção de variáveis
- Confirme que dados existem para período

## 📚 Recursos Adicionais

### Documentação
- [Metodologia DMAIC](dmaic_overview.md)
- [Conceitos Estatísticos](stats_concepts.md)

### Suporte
- Email: suporte@greenpeace.org
- Wiki interno: wiki.greenpeace.org/dmaic

### Treinamentos
- DMAIC Básico: 1º segunda-feira do mês
- Estatística Aplicada: 3º quinta-feira do mês
- Workshops práticos: Sob demanda

## 🎯 Checklist de Projeto

### Início
- [ ] Project Charter definido
- [ ] Equipe formada
- [ ] Cronograma aprovado

### Durante
- [ ] Dados coletados e validados
- [ ] Análises documentadas
- [ ] Stakeholders informados

### Conclusão
- [ ] Melhorias implementadas
- [ ] Controles estabelecidos
- [ ] Relatório final gerado
- [ ] Lições aprendidas documentadas

## 🌟 Casos de Sucesso

### Projeto Rio Limpo
- **Redução de 35%** na turbidez
- **ROI de 450%** em 6 meses
- **3 prêmios** de sustentabilidade

### Projeto Ar Puro
- **Diminuição de 28%** em emissões
- **Economia de R$ 2.3M** anuais
- **Modelo replicado** em 5 unidades

---

💚 **Juntos pela sustentabilidade!** 

*Sistema DMAIC Greenpeace - Versão 1.0*
