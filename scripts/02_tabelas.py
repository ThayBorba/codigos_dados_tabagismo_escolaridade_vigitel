"""
02_tabelas.py
Monta as Tabelas 1, 2 e 3 do artigo a partir de resultados/resultados.json, no padrão
numérico da revista: percentuais com 1 casa decimal, medidas de associação e VPA com
2 casas, p-valor com 3 casas ("<0,001"), vírgula decimal e ponto como separador de milhar.

Saída: resultados/tabela1.csv, resultados/tabela2.csv, resultados/tabela3.csv (UTF-8, separador ;)
"""
import csv
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
R = json.load(open(RAIZ / 'resultados' / 'resultados.json', encoding='utf-8'))
SAIDA = RAIZ / 'resultados'


def num(v, casas):
    q = Decimal(repr(float(v))).quantize(Decimal(1).scaleb(-casas), rounding=ROUND_HALF_UP)
    return f'{q:.{casas}f}'.replace('.', ',')


def milhar(n):
    return f'{n:,}'.replace(',', '.')


def pval(p):
    return '<0,001' if p < 0.001 else num(p, 3)


def prev_ic(d):
    return f"{num(d['p'], 1)} ({num(d['lo'], 1)}; {num(d['hi'], 1)})"


def med_ic(v, lo, hi, casas=2):
    return f'{num(v, casas)} ({num(lo, casas)}; {num(hi, casas)})'


def gravar(nome, cabecalho, linhas):
    with open(SAIDA / nome, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(cabecalho)
        w.writerows(linhas)
    print(f'{nome}: {len(linhas)} linhas')


# ---------------- Tabela 1: prevalência e OR ajustada por característica
cat, orr = R['por_categoria'], R['logistica']['OR']
def ou(chave):
    if chave is None:
        return '1,00'
    if chave == '-':
        return '-'
    o = orr[chave]
    return med_ic(o['OR'], o['lo'], o['hi'])

linhas = []
blocos = [
    ('Sexo', [('Feminino', 'sexo:Feminino', None), ('Masculino', 'sexo:Masculino', 'sexo_masculino')]),
    ('Faixa etária (anos)', [('18-34', 'faixa_etaria:18-34', None), ('35-54', 'faixa_etaria:35-54', 'idade_35_54'),
                             ('≥55', 'faixa_etaria:55 ou mais', 'idade_55_mais')]),
    ('Escolaridade (anos de estudo)', [('0-8', 'escolaridade:0-8 anos', 'escolaridade_0_8'),
                                       ('9-11', 'escolaridade:9-11 anos', 'escolaridade_9_11'),
                                       ('≥12', 'escolaridade:12 anos ou mais', None)]),
    ('Raça/cor da pele', [('Branca', 'raca_cor:Branca', None), ('Preta', 'raca_cor:Preta', 'raca_Preta'),
                          ('Parda', 'raca_cor:Parda', 'raca_Parda'), ('Amarela', 'raca_cor:Amarela', 'raca_Amarela'),
                          ('Indígena', 'raca_cor:Indígena', 'raca_Indígena'),
                          ('Sem informação', 'raca_cor:sem informação', '-')]),
    ('Macrorregião', [('Norte', 'regiao:Norte', 'regiao_Norte'), ('Nordeste', 'regiao:Nordeste', 'regiao_Nordeste'),
                      ('Centro-Oeste', 'regiao:Centro-Oeste', 'regiao_Centro-Oeste'), ('Sudeste', 'regiao:Sudeste', None),
                      ('Sul', 'regiao:Sul', 'regiao_Sul')]),
]
for titulo, itens in blocos:
    linhas.append([titulo, '', '', ''])
    for rotulo, kc, ko in itens:
        linhas.append([rotulo, milhar(cat[kc]['n']), prev_ic(cat[kc]), ou(ko)])
linhas.append(['Total', milhar(R['total']['n']), prev_ic(R['total']), ''])
gravar('tabela1.csv', ['Variável', 'n', 'Prevalência % (IC95%)', 'OR ajustada (IC95%)'], linhas)

# ---------------- Tabela 2: prevalência por edição e escolaridade, SII e RII
linhas = []
for a in sorted(R['por_edicao'], key=int):
    e, q = R['por_edicao_escolaridade'], R['desigualdade'][a]
    linhas.append([a, milhar(R['por_edicao'][a]['n']), prev_ic(R['por_edicao'][a]),
                   prev_ic(e[f'{a}_1']), prev_ic(e[f'{a}_2']), prev_ic(e[f'{a}_3']),
                   med_ic(q['SII'], q['SII_lo'], q['SII_hi'], 1), med_ic(q['RII'], q['RII_lo'], q['RII_hi'])])
gravar('tabela2.csv', ['Edição', 'n', 'Total % (IC95%)', '0-8 anos % (IC95%)', '9-11 anos % (IC95%)',
                       '≥12 anos % (IC95%)', 'SII, p.p. (IC95%)', 'RII (IC95%)'], linhas)

# ---------------- Tabela 3: VPA 2014-2024 e 2014-2023
t = R['tendencia']
linhas = []
for rotulo, chave in [('Total', 'total'), ('Masculino', 'masculino'), ('Feminino', 'feminino'),
                      ('0-8 anos de estudo', 'escolaridade_0_8'), ('9-11 anos de estudo', 'escolaridade_9_11'),
                      ('≥12 anos de estudo', 'escolaridade_12_mais')]:
    a, b = t[f'{chave}_2014_2024'], t[f'{chave}_2014_2023']
    linhas.append([rotulo, med_ic(a['VPA'], a['lo'], a['hi']), pval(a['p']),
                   med_ic(b['VPA'], b['lo'], b['hi']), pval(b['p'])])
gravar('tabela3.csv', ['Série', 'VPA 2014-2024 % (IC95%)', 'p-valor', 'VPA 2014-2023 % (IC95%)', 'p-valor'], linhas)

# ---------------- valores citados no texto e nas notas das tabelas
f = t['total_2014_2021']
lg = R['logistica']
texto = {
    'VPA total 2014-2021 (telefone fixo)': f"{med_ic(f['VPA'], f['lo'], f['hi'])}; p-valor {pval(f['p'])}",
    'Regressão logística: n analisado': milhar(lg['n']),
    'Regressão logística: excluídos sem raça/cor': milhar(lg['excluidos_sem_raca_cor']),
    'OR por edição (2014-2024)': med_ic(lg['OR']['edicao']['OR'], lg['OR']['edicao']['lo'], lg['OR']['edicao']['hi'], 3),
    'OR por edição (sem 2024)': med_ic(lg['OR_edicao_sem_2024']['OR'], lg['OR_edicao_sem_2024']['lo'],
                                       lg['OR_edicao_sem_2024']['hi'], 3),
    'Interação escolaridade x edição, p-valor (2014-2024)': pval(R['interacao_escolaridade_edicao']['2014_2024']['p']),
    'Interação escolaridade x edição, p-valor (2014-2023)': pval(R['interacao_escolaridade_edicao']['2014_2023']['p']),
}
with open(SAIDA / 'valores_citados_no_texto.txt', 'w', encoding='utf-8') as fh:
    for k, v in texto.items():
        fh.write(f'{k}: {v}\n')
        print(f'{k}: {v}')
