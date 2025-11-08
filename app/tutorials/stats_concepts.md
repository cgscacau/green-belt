# Conceitos Estatísticos para DMAIC

## 📊 Estatística Descritiva

### Medidas de Tendência Central
- **Média:** Valor médio dos dados
- **Mediana:** Valor central quando dados ordenados
- **Moda:** Valor mais frequente

### Medidas de Dispersão
- **Desvio Padrão (σ):** Variabilidade em torno da média
- **Variância (σ²):** Quadrado do desvio padrão
- **Amplitude:** Diferença entre máximo e mínimo
- **IQR:** Intervalo interquartil (Q3 - Q1)
- **CV%:** Coeficiente de variação (σ/μ × 100)

## 🔬 Testes de Hipóteses

### O que é p-valor?
O p-valor representa a probabilidade de obter resultados tão extremos quanto os observados, assumindo que a hipótese nula é verdadeira.

- **p < 0.05:** Rejeita H₀ (resultado significativo)
- **p ≥ 0.05:** Não rejeita H₀ (sem evidência suficiente)

### Hipóteses
- **H₀ (Nula):** Não há diferença/efeito
- **H₁ (Alternativa):** Existe diferença/efeito

## 📐 Teste de Normalidade

### Teste Shapiro-Wilk
Verifica se os dados seguem distribuição normal.

**Interpretação:**
- p > 0.05: Dados normais
- p ≤ 0.05: Dados não-normais

**Quando usar:** Amostras pequenas (n < 50)

### Teste Anderson-Darling
Alternativa ao Shapiro-Wilk para amostras maiores.

### Q-Q Plot
Gráfico visual para avaliar normalidade. Pontos próximos à linha diagonal indicam normalidade.

## 🎯 Testes de Comparação

### Teste t de Student
Compara médias de dois grupos.

**Pressupostos:**
1. Dados normais
2. Variâncias iguais (teste de Levene)
3. Observações independentes

**Tipos:**
- **Independente:** Grupos diferentes
- **Pareado:** Mesmas unidades, momentos diferentes

### ANOVA (Analysis of Variance)
Compara médias de três ou mais grupos.

**Pressupostos:**
1. Normalidade em cada grupo
2. Homogeneidade de variâncias
3. Independência

**Post-hoc:** Se ANOVA significativa, use Tukey HSD para comparações múltiplas.

### Teste de Levene
Verifica homogeneidade de variâncias entre grupos.
- p > 0.05: Variâncias iguais
- p ≤ 0.05: Variâncias diferentes

## 🔗 Análise de Correlação

### Coeficiente de Pearson (r)
Mede correlação **linear** entre variáveis.

**Interpretação:**
- r = 1: Correlação positiva perfeita
- r = 0: Sem correlação linear
- r = -1: Correlação negativa perfeita

**Força:**
- |r| < 0.3: Fraca
- 0.3 ≤ |r| < 0.7: Moderada
- |r| ≥ 0.7: Forte

### Coeficiente de Spearman (ρ)
Correlação de **postos**, não assume linearidade.

**Quando usar:**
- Dados ordinais
- Relação monotônica não-linear
- Presença de outliers

## 📈 Regressão Linear

### Regressão Simples
Y = β₀ + β₁X + ε

- **β₀:** Intercepto
- **β₁:** Coeficiente angular
- **ε:** Erro

### Regressão Múltipla
Y = β₀ + β₁X₁ + β₂X₂ + ... + ε

### Métricas de Avaliação
- **R²:** Proporção da variância explicada (0 a 1)
- **R² Ajustado:** R² penalizado pelo número de variáveis
- **RMSE:** Erro quadrático médio

### Pressupostos
1. Linearidade
2. Independência dos erros
3. Homocedasticidade
4. Normalidade dos resíduos
5. Ausência de multicolinearidade

## 📊 Controle Estatístico de Processo

### Gráficos de Controle
Monitoram a estabilidade do processo ao longo do tempo.

**Limites:**
- **UCL:** Limite Superior de Controle (μ + 3σ)
- **LCL:** Limite Inferior de Controle (μ - 3σ)
- **Linha Central:** Média do processo

**Regras de Western Electric:**
1. 1 ponto além de 3σ
2. 2 de 3 pontos além de 2σ
3. 4 de 5 pontos além de 1σ
4. 8 pontos consecutivos do mesmo lado

### Capacidade do Processo

**Cp (Capacidade Potencial):**
Cp = (USL - LSL) / 6σ

**Cpk (Capacidade Real):**
Cpk = min[(USL - μ) / 3σ, (μ - LSL) / 3σ]

**Interpretação:**
- Cpk < 1.00: Processo incapaz
- 1.00 ≤ Cpk < 1.33: Processo marginalmente capaz
- Cpk ≥ 1.33: Processo capaz
- Cpk ≥ 2.00: Processo Six Sigma

## 🎲 Conceitos Importantes

### Erro Tipo I e II
- **Tipo I (α):** Rejeitar H₀ verdadeira (falso positivo)
- **Tipo II (β):** Não rejeitar H₀ falsa (falso negativo)

### Poder Estatístico
Probabilidade de detectar efeito real (1 - β).
Meta: Poder ≥ 0.80

### Tamanho de Efeito
- **Cohen's d:** Para teste t
  - 0.2: Pequeno
  - 0.5: Médio
  - 0.8: Grande

### Outliers
Valores atípicos que podem influenciar análises.

**Detecção:**
- IQR: Valores além de Q1 - 1.5×IQR ou Q3 + 1.5×IQR
- Z-score: |z| > 3

## 💡 Dicas Práticas

1. **Sempre visualize os dados** antes de testar
2. **Verifique pressupostos** antes de aplicar testes
3. **Use testes não-paramétricos** se pressupostos violados
4. **Cuidado com múltiplas comparações** (correção de Bonferroni)
5. **Significância estatística ≠ significância prática**
6. **Documente todas as decisões** estatísticas
