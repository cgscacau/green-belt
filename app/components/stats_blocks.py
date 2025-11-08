import pandas as pd
import numpy as np
import scipy.stats as stats
import statsmodels.api as sm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import streamlit as st

def desc_stats(df: pd.DataFrame, numeric_cols=None):
    """Estatísticas descritivas"""
    try:
        if numeric_cols:
            num = df[numeric_cols]
        else:
            num = df.select_dtypes(include=['number'])
        
        if num.empty:
            return pd.DataFrame()
        
        stats_df = num.describe().T
        stats_df['missing'] = len(df) - num.count()
        stats_df['missing_%'] = (stats_df['missing'] / len(df)) * 100
        stats_df['cv'] = (num.std() / num.mean()) * 100  # Coeficiente de variação
        
        return stats_df.round(2)
    except Exception as e:
        st.error(f"Erro em estatísticas descritivas: {e}")
        return pd.DataFrame()

def detect_outliers(series: pd.Series, method='iqr'):
    """Detecta outliers usando IQR ou Z-score"""
    series = series.dropna()
    
    if len(series) < 4:
        return pd.Series(dtype=bool)
    
    if method == 'iqr':
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        outliers = (series < lower) | (series > upper)
    else:  # z-score
        z = np.abs(stats.zscore(series))
        outliers = z > 3
    
    return outliers

def shapiro_test(series: pd.Series):
    """Teste de normalidade Shapiro-Wilk"""
    series = series.dropna()
    if len(series) < 3:
        return None
    
    try:
        W, p = stats.shapiro(series)
        return {
            "W": float(W),
            "p_value": float(p),
            "normal": p > 0.05,
            "interpretation": "Normal" if p > 0.05 else "Não normal"
        }
    except:
        return None

def anderson_test(series: pd.Series):
    """Teste Anderson-Darling para normalidade"""
    series = series.dropna()
    if len(series) < 8:
        return None
    
    try:
        result = stats.anderson(series)
        return {
            "statistic": float(result.statistic),
            "critical_5%": float(result.critical_values[2]),
            "normal": result.statistic < result.critical_values[2]
        }
    except:
        return None

def levene_test(df, value_col, group_col):
    """Teste de Levene para homogeneidade de variâncias"""
    groups = []
    for name, group in df.groupby(group_col):
        groups.append(group[value_col].dropna())
    
    if len(groups) < 2:
        return None
    
    try:
        stat, p = stats.levene(*groups)
        return {
            "statistic": float(stat),
            "p_value": float(p),
            "equal_var": p > 0.05,
            "interpretation": "Variâncias iguais" if p > 0.05 else "Variâncias diferentes"
        }
    except:
        return None

def ttest_two_groups(df, value_col, group_col, g1, g2):
    """Teste t para duas amostras"""
    a = df[df[group_col]==g1][value_col].dropna()
    b = df[df[group_col]==g2][value_col].dropna()
    
    if len(a) < 3 or len(b) < 3:
        return None
    
    try:
        # Teste de Levene primeiro
        lev_stat, lev_p = stats.levene(a, b)
        equal_var = lev_p > 0.05
        
        # Teste t
        t, p = stats.ttest_ind(a, b, equal_var=equal_var)
        
        # Effect size (Cohen's d)
        pooled_std = np.sqrt((a.var() + b.var()) / 2)
        cohens_d = (a.mean() - b.mean()) / pooled_std
        
        return {
            "t": float(t),
            "p_value": float(p),
            "mean_diff": float(a.mean() - b.mean()),
            "cohens_d": float(cohens_d),
            "n1": len(a),
            "n2": len(b),
            "equal_var": equal_var,
            "significant": p < 0.05,
            "interpretation": "Diferença significativa" if p < 0.05 else "Sem diferença significativa"
        }
    except Exception as e:
        st.error(f"Erro no teste t: {e}")
        return None

def anova_test(df, value_col, group_col):
    """ANOVA one-way"""
    groups = []
    group_names = []
    
    for name, group in df.groupby(group_col):
        data = group[value_col].dropna()
        if len(data) >= 3:
            groups.append(data)
            group_names.append(name)
    
    if len(groups) < 2:
        return None
    
    try:
        # ANOVA
        f_stat, p = stats.f_oneway(*groups)
        
        # Post-hoc Tukey se significativo
        tukey_result = None
        if p < 0.05:
            df_clean = df[[value_col, group_col]].dropna()
            tukey = pairwise_tukeyhsd(
                df_clean[value_col],
                df_clean[group_col],
                alpha=0.05
            )
            tukey_result = str(tukey)
        
        return {
            "F": float(f_stat),
            "p_value": float(p),
            "n_groups": len(groups),
            "significant": p < 0.05,
            "interpretation": "Diferença entre grupos" if p < 0.05 else "Sem diferença entre grupos",
            "tukey": tukey_result
        }
    except Exception as e:
        st.error(f"Erro na ANOVA: {e}")
        return None

def correlation_analysis(df, method='pearson'):
    """Análise de correlação"""
    try:
        numeric_df = df.select_dtypes(include=['number'])
        
        if numeric_df.shape[1] < 2:
            return None
        
        if method == 'pearson':
            corr_matrix = numeric_df.corr(method='pearson')
        elif method == 'spearman':
            corr_matrix = numeric_df.corr(method='spearman')
        else:
            corr_matrix = numeric_df.corr(method='kendall')
        
        # P-values para correlações
        p_values = pd.DataFrame(
            np.zeros_like(corr_matrix),
            columns=corr_matrix.columns,
            index=corr_matrix.index
        )
        
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                col1 = corr_matrix.columns[i]
                col2 = corr_matrix.columns[j]
                
                if method == 'pearson':
                    _, p = stats.pearsonr(
                        numeric_df[col1].dropna(),
                        numeric_df[col2].dropna()
                    )
                else:
                    _, p = stats.spearmanr(
                        numeric_df[col1].dropna(),
                        numeric_df[col2].dropna()
                    )
                
                p_values.iloc[i, j] = p
                p_values.iloc[j, i] = p
        
        return {
            "correlation_matrix": corr_matrix,
            "p_values": p_values,
            "method": method
        }
    except Exception as e:
        st.error(f"Erro na análise de correlação: {e}")
        return None

def ols_regression(df, y_col, x_cols):
    """Regressão linear múltipla"""
    try:
        # Remove NaN
        df_clean = df[[y_col] + x_cols].dropna()
        
        if len(df_clean) < len(x_cols) + 5:
            st.warning("Dados insuficientes para regressão.")
            return None
        
        # Adiciona constante
        X = sm.add_constant(df_clean[x_cols])
        y = df_clean[y_col]
        
        # Fit do modelo
        model = sm.OLS(y, X).fit()
        
        # Diagnósticos
        residuals = model.resid
        fitted = model.fittedvalues
        
        # Teste de normalidade dos resíduos
        _, shapiro_p = stats.shapiro(residuals)
        
        # Durbin-Watson para autocorrelação
        from statsmodels.stats.stattools import durbin_watson
        dw = durbin_watson(residuals)
        
        return {
            "model": model,
            "r_squared": model.rsquared,
            "adj_r_squared": model.rsquared_adj,
            "f_statistic": model.fvalue,
            "p_value": model.f_pvalue,
            "coefficients": model.params.to_dict(),
            "p_values_coef": model.pvalues.to_dict(),
            "residuals_normal": shapiro_p > 0.05,
            "durbin_watson": float(dw),
            "n_observations": len(df_clean)
        }
    except Exception as e:
        st.error(f"Erro na regressão: {e}")
        return None

def process_capability(series: pd.Series, lsl=None, usl=None, target=None):
    """Análise de capacidade do processo"""
    series = series.dropna()
    
    if len(series) < 30:
        st.warning("Recomenda-se ao menos 30 observações para análise de capacidade.")
    
    mean = series.mean()
    std = series.std()
    
    results = {
        "mean": float(mean),
        "std": float(std),
        "n": len(series)
    }
    
    if lsl is not None and usl is not None:
        # Cp - capacidade potencial
        cp = (usl - lsl) / (6 * std)
        
        # Cpk - capacidade real
        cpu = (usl - mean) / (3 * std)
        cpl = (mean - lsl) / (3 * std)
        cpk = min(cpu, cpl)
        
        # PPM defeituosos
        ppm_lsl = stats.norm.cdf(lsl, mean, std) * 1000000
        ppm_usl = (1 - stats.norm.cdf(usl, mean, std)) * 1000000
        ppm_total = ppm_lsl + ppm_usl
        
        results.update({
            "cp": float(cp),
            "cpk": float(cpk),
            "cpu": float(cpu),
            "cpl": float(cpl),
            "ppm_total": float(ppm_total),
            "process_capable": cpk >= 1.33
        })
    
    if target is not None:
        # Cpm - capacidade com alvo
        cpm = (usl - lsl) / (6 * np.sqrt(std**2 + (mean - target)**2))
        results["cpm"] = float(cpm)
        results["bias"] = float(mean - target)
    
    return results
