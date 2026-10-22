"""
01_analise.py
Estima todos os resultados do artigo a partir da base analítica.

Entrada : dados/base_analitica_vigitel_2014_2024.csv  (gerada por 00_preparar_base.py)
Saída   : resultados/resultados.json  (valores sem arredondamento)

Análises:
  1. Prevalências ponderadas (peso rake do Vigitel) com IC95% por linearização,
     calculados em escala logit: total, por edição, por edição x escolaridade e por
     categoria das variáveis.
  2. Tendência temporal: regressão de Prais-Winsten do logaritmo da prevalência anual
     sobre o ano da edição, com correção da autocorrelação de primeira ordem; variação
     percentual anual (VPA) e IC95% pela distribuição t de Student. Séries completas
     (2014-2024), com exclusão de 2024 e, para o total, 2014-2021 (telefone fixo).
  3. Desigualdade por escolaridade em cada edição: índice angular (SII) e índice relativo
     (RII), por regressão linear ponderada da condição de fumante sobre a posição relativa
     (ridit) dos grupos de escolaridade, ordenados do maior para o menor nível. SII com IC95%
     por estimador robusto; RII = razão entre as prevalências preditas nos extremos, com
     IC95% pelo método delta.
  4. Regressão logística ponderada (participantes com raça/cor informada), com IC95% por
     estimador robusto da variância; edição como variável contínua; teste de Wald dos termos
     de interação escolaridade x edição (2 graus de liberdade), com e sem a edição de 2024.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

RAIZ = Path(__file__).resolve().parents[1]
ENTRADA = RAIZ / 'dados' / 'base_analitica_vigitel_2014_2024.csv'
SAIDA = RAIZ / 'resultados' / 'resultados.json'


# ---------------------------------------------------------------- funções
def prevalencia(d):
    """Prevalência ponderada (%) e IC95% por linearização, em escala logit."""
    y, w = d['fumante'].to_numpy(float), d['peso'].to_numpy(float)
    n, soma = len(y), w.sum()
    p = (w * y).sum() / soma
    var = n / (n - 1) * ((w ** 2) * (y - p) ** 2).sum() / soma ** 2
    ep_logit = np.sqrt(var) / (p * (1 - p))
    logit = np.log(p / (1 - p))
    lo, hi = (1 / (1 + np.exp(-(logit + s * 1.96 * ep_logit))) for s in (-1, 1))
    return {'n': int(n), 'p': 100 * p, 'lo': 100 * lo, 'hi': 100 * hi}


def prais_winsten(anos, prevalencias):
    """VPA (%) por Prais-Winsten sobre log(prevalência), IC95% pela distribuição t."""
    x = np.asarray(anos, float)
    y = np.log(np.asarray(prevalencias, float))
    n = len(y)
    X = np.column_stack([np.ones(n), x])
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    rho = 0.0
    for _ in range(200):
        e = y - X @ b
        rho_novo = float(np.clip((e[1:] @ e[:-1]) / (e[:-1] @ e[:-1]), -0.99, 0.99))
        ys = np.r_[np.sqrt(1 - rho_novo ** 2) * y[0], y[1:] - rho_novo * y[:-1]]
        Xs = np.vstack([np.sqrt(1 - rho_novo ** 2) * X[0], X[1:] - rho_novo * X[:-1]])
        b = np.linalg.lstsq(Xs, ys, rcond=None)[0]
        convergiu = abs(rho_novo - rho) < 1e-10
        rho = rho_novo
        if convergiu:
            break
    gl = n - 2
    residuos = ys - Xs @ b
    cov = (residuos @ residuos / gl) * np.linalg.inv(Xs.T @ Xs)
    ep = np.sqrt(cov[1, 1])
    t_crit = stats.t.ppf(0.975, gl)
    vpa = lambda v: 100 * (np.exp(v) - 1)
    return {'VPA': vpa(b[1]), 'lo': vpa(b[1] - t_crit * ep), 'hi': vpa(b[1] + t_crit * ep),
            'p': float(2 * stats.t.sf(abs(b[1] / ep), gl)), 'rho': rho, 'n_pontos': n}


def matriz_logistica(d, interacao=False):
    # categorias de referência: feminino; 18-34 anos; 12 anos ou mais de estudo; branca; Sudeste
    X = pd.DataFrame(index=d.index)
    X['sexo_masculino'] = (d['sexo'] == 'Masculino').astype(int)
    X['idade_35_54'] = (d['faixa_etaria'] == '35-54').astype(int)
    X['idade_55_mais'] = (d['faixa_etaria'] == '55 ou mais').astype(int)
    X['escolaridade_0_8'] = (d['escolaridade_cod'] == 1).astype(int)
    X['escolaridade_9_11'] = (d['escolaridade_cod'] == 2).astype(int)
    for r in ['Preta', 'Parda', 'Amarela', 'Indígena']:
        X['raca_' + r] = (d['raca_cor'] == r).astype(int)
    for g in ['Norte', 'Nordeste', 'Centro-Oeste', 'Sul']:
        X['regiao_' + g] = (d['regiao'] == g).astype(int)
    X['edicao'] = d['edicao'] - 2014
    if interacao:
        X['esc_0_8_x_edicao'] = X['escolaridade_0_8'] * X['edicao']
        X['esc_9_11_x_edicao'] = X['escolaridade_9_11'] * X['edicao']
    return sm.add_constant(X.astype(float))


def logistica(d, interacao=False):
    X = matriz_logistica(d, interacao)
    pesos = d['peso'] / d['peso'].mean()
    return sm.GLM(d['fumante'], X, family=sm.families.Binomial(), var_weights=pesos).fit(cov_type='HC0')


def wald_interacao(modelo):
    nomes = list(modelo.params.index)
    R = np.zeros((2, len(nomes)))
    R[0, nomes.index('esc_0_8_x_edicao')] = 1
    R[1, nomes.index('esc_9_11_x_edicao')] = 1
    t = modelo.wald_test(R, scalar=True)
    return {'qui2': float(t.statistic), 'gl': 2, 'p': float(t.pvalue)}


def tabela_or(modelo):
    ic = modelo.conf_int()
    return {k: {'OR': float(np.exp(modelo.params[k])), 'lo': float(np.exp(ic.loc[k, 0])),
                'hi': float(np.exp(ic.loc[k, 1])), 'p': float(modelo.pvalues[k])}
            for k in modelo.params.index if k != 'const'}


# ---------------------------------------------------------------- análise
def main():
    d = pd.read_csv(ENTRADA, encoding='utf-8')
    out = {}

    # 1. Prevalências
    out['total'] = prevalencia(d)
    out['por_edicao'] = {int(a): prevalencia(g) for a, g in d.groupby('edicao')}
    out['por_edicao_escolaridade'] = {f'{a}_{e}': prevalencia(g)
                                      for (a, e), g in d.groupby(['edicao', 'escolaridade_cod'])}
    out['por_categoria'] = {}
    for var in ['sexo', 'faixa_etaria', 'escolaridade', 'raca_cor', 'regiao']:
        for k, g in d.groupby(var):
            out['por_categoria'][f'{var}:{k}'] = prevalencia(g)
    out['por_categoria']['raca_cor:sem informação'] = prevalencia(d[d['raca_cor'].isna()])

    # 2. Tendência temporal
    anos = sorted(out['por_edicao'])
    sem2024 = [a for a in anos if a != 2024]
    fixo = [a for a in anos if a <= 2021]
    serie = lambda filtro, lista: [prevalencia(d[(d['edicao'] == a) & filtro])['p'] for a in lista]
    todos = pd.Series(True, index=d.index)
    grupos = {'total': todos,
              'masculino': d['sexo'] == 'Masculino', 'feminino': d['sexo'] == 'Feminino',
              'escolaridade_0_8': d['escolaridade_cod'] == 1,
              'escolaridade_9_11': d['escolaridade_cod'] == 2,
              'escolaridade_12_mais': d['escolaridade_cod'] == 3}
    out['tendencia'] = {}
    for nome, filtro in grupos.items():
        out['tendencia'][f'{nome}_2014_2024'] = prais_winsten(anos, serie(filtro, anos))
        out['tendencia'][f'{nome}_2014_2023'] = prais_winsten(sem2024, serie(filtro, sem2024))
    out['tendencia']['total_2014_2021'] = prais_winsten(fixo, serie(todos, fixo))

    # 3. SII e RII por edição
    out['desigualdade'] = {}
    for a, g in d.groupby('edicao'):
        prop = g.groupby('escolaridade_cod')['peso'].sum() / g['peso'].sum()
        posicao, acumulado = {}, 0.0
        for e in [3, 2, 1]:  # do maior para o menor nível de escolaridade
            posicao[e] = acumulado + prop[e] / 2
            acumulado += prop[e]
        X = sm.add_constant(g['escolaridade_cod'].map(posicao).to_numpy(float))
        pesos = (g['peso'] / g['peso'].mean()).to_numpy()
        lin = sm.GLM(g['fumante'].to_numpy(float), X, family=sm.families.Gaussian(),
                     var_weights=pesos).fit(cov_type='HC0')
        a0, b1 = lin.params
        ic = lin.conf_int()
        rii = (a0 + b1) / a0
        grad = np.array([-b1 / a0 ** 2, 1 / a0])
        ep_rii = float(np.sqrt(grad @ lin.cov_params() @ grad))
        out['desigualdade'][int(a)] = {'SII': 100 * b1, 'SII_lo': 100 * ic[1, 0], 'SII_hi': 100 * ic[1, 1],
                                       'RII': rii, 'RII_lo': rii - 1.96 * ep_rii, 'RII_hi': rii + 1.96 * ep_rii}

    # 4. Regressão logística (casos completos para raça/cor)
    cc = d[d['raca_cor'].notna()]
    m = logistica(cc)
    out['logistica'] = {'n': int(m.nobs), 'excluidos_sem_raca_cor': int(len(d) - m.nobs), 'OR': tabela_or(m)}
    m_sem2024 = logistica(cc[cc['edicao'] != 2024])
    out['logistica']['OR_edicao_sem_2024'] = tabela_or(m_sem2024)['edicao']
    out['interacao_escolaridade_edicao'] = {
        '2014_2024': wald_interacao(logistica(cc, interacao=True)),
        '2014_2023': wald_interacao(logistica(cc[cc['edicao'] != 2024], interacao=True)),
    }

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(SAIDA, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False, default=float)
    print(f'Resultados -> {SAIDA}')


if __name__ == '__main__':
    main()
