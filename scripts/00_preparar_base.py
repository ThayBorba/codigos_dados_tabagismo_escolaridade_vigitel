"""
00_preparar_base.py
Gera a base analítica do estudo a partir da base harmonizada oficial do Vigitel 2006-2024.

Entrada : arquivo oficial do Ministério da Saúde, em CSV ou no ZIP original
          (vigitel-2006-2024-peso-rake-csv.zip), disponível em
          https://svs.aids.gov.br/daent/cgdnt/vigitel/
Saída   : dados/base_analitica_vigitel_2014_2024.csv (UTF-8, separador vírgula)

Uso:
    python scripts/00_preparar_base.py caminho/para/vigitel-2006-2024-peso-rake-csv.zip

Procedimentos:
  - seleção das edições 2014 a 2024 (a edição de 2022 não foi realizada);
  - seleção das variáveis do estudo;
  - recodificação de raça/cor da pele: na versão CSV da base, os rótulos "amarela" e
    "parda/morena" estão invertidos em relação ao dicionário de dados oficial
    (código 3 = amarela; código 4 = parda); a correção segue o dicionário;
  - criação da faixa etária (18-34, 35-54, 55 anos ou mais).
"""
import sys
import zipfile
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / 'dados' / 'base_analitica_vigitel_2014_2024.csv'
COLUNAS = ['ano', 'cidade', 'regiao', 'q6', 'q7', 'q69', 'fesc', 'fumante', 'pesorake2025']

RACA = {  # rótulo no CSV -> categoria segundo o dicionário oficial
    'branca': 'Branca',
    'negra': 'Preta',
    'amarela': 'Parda',          # rótulo invertido no CSV
    'parda/morena': 'Amarela',   # rótulo invertido no CSV
    'vermelha': 'Indígena',
}
ESCOLARIDADE = {1: '0-8 anos', 2: '9-11 anos', 3: '12 anos ou mais'}


def abrir(caminho: Path):
    if caminho.suffix.lower() == '.zip':
        z = zipfile.ZipFile(caminho)
        nome = next(n for n in z.namelist() if n.lower().endswith('.csv'))
        return z.open(nome)
    return open(caminho, 'rb')


def main(caminho: Path):
    partes = []
    with abrir(caminho) as f:
        leitor = pd.read_csv(f, usecols=COLUNAS, encoding='latin-1', dtype=str, chunksize=100_000)
        for bloco in leitor:
            ano = pd.to_numeric(bloco['ano'], errors='coerce')
            partes.append(bloco[ano.between(2014, 2024)])
    d = pd.concat(partes, ignore_index=True)

    base = pd.DataFrame({
        'edicao': pd.to_numeric(d['ano']).astype(int),
        'cidade': d['cidade'],
        'regiao': d['regiao'].str.title(),
        'sexo': d['q7'].str.capitalize(),
        'idade': pd.to_numeric(d['q6']).astype(int),
        'escolaridade_cod': pd.to_numeric(d['fesc']).astype(int),
        'raca_cor': d['q69'].map(RACA),  # demais respostas = sem informação (vazio)
        'fumante': (d['fumante'] == 'Sim').astype(int),
        'peso': pd.to_numeric(d['pesorake2025']),
    })
    base['escolaridade'] = base['escolaridade_cod'].map(ESCOLARIDADE)
    base['faixa_etaria'] = pd.cut(base['idade'], [17, 34, 54, 200],
                                  labels=['18-34', '35-54', '55 ou mais']).astype(str)

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    base.to_csv(SAIDA, index=False, encoding='utf-8')

    print(f'Base analítica: {len(base):,} registros -> {SAIDA}'.replace(',', '.'))
    print(base['edicao'].value_counts().sort_index().to_string())
    print('Sem informação de raça/cor:', int(base['raca_cor'].isna().sum()))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('Uso: python scripts/00_preparar_base.py <arquivo .zip ou .csv do Vigitel 2006-2024>')
    main(Path(sys.argv[1]))
