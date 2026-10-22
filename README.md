# Desigualdades por escolaridade na prevalência do tabagismo em adultos — capitais brasileiras e Distrito Federal, 2014-2024

Códigos e base analítica que reproduzem todas as estimativas, tabelas e figuras do artigo submetido à revista *Epidemiologia e Serviços de Saúde: revista do SUS*.

## Fonte dos dados

Base harmonizada de microdados do Sistema de Vigilância de Fatores de Risco e Proteção para Doenças Crônicas por Inquérito Telefônico (Vigitel), edições 2006-2024, de acesso público, disponibilizada pelo Ministério da Saúde:

- Página: https://svs.aids.gov.br/daent/cgdnt/vigitel/
- Arquivo utilizado: `vigitel-2006-2024-peso-rake-csv.zip` (contém `vigitel-2006-2024-peso-rake.csv`, 1.014.484.615 bytes, datado de 29/01/2026)
- SHA-256 do arquivo ZIP: `3713a3d20972e03329b5e830016c6ceadd128df2a2cd303fe8965088e647faa5`

Referência: Brasil. Ministério da Saúde. Secretaria de Vigilância em Saúde e Ambiente. Vigitel: base de dados harmonizada 2006-2024 [dataset]. Brasília: Ministério da Saúde; 2026. Available from: https://svs.aids.gov.br/daent/cgdnt/vigitel/

## Estrutura

```
├── README.md
├── requirements.txt            dependências (versões fixadas)
├── executar_tudo.py            executa as quatro etapas em sequência
├── scripts/
│   ├── 00_preparar_base.py     base oficial -> base analítica (2014-2024, variáveis do estudo)
│   ├── 01_analise.py           base analítica -> resultados/resultados.json
│   ├── 02_tabelas.py           resultados -> Tabelas 1, 2 e 3 no padrão numérico da revista
│   └── 03_figuras.py           resultados -> Figuras 1 e 2 (PDF, SVG e PNG)
├── dados/
│   └── base_analitica_vigitel_2014_2024.csv
├── resultados/                 saídas geradas pelos scripts
└── figuras/                    saídas geradas pelos scripts
```

## Como reproduzir

Requer Python 3.11.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# a partir da base oficial (baixar o ZIP na página do Ministério da Saúde):
python executar_tudo.py caminho/para/vigitel-2006-2024-peso-rake-csv.zip
```

Para partir da base analítica já incluída em `dados/`, sem baixar a base oficial, execute apenas as etapas seguintes:

```bash
python scripts/01_analise.py
python scripts/02_tabelas.py
python scripts/03_figuras.py
```

Tempo de execução aproximado: 40 segundos para o pipeline completo.

## Correspondência com o artigo

| Saída | Conteúdo no artigo |
|---|---|
| `resultados/tabela1.csv` | Tabela 1 — prevalência e razões de chances ajustadas por característica |
| `resultados/tabela2.csv` | Tabela 2 — prevalência por edição e escolaridade, SII e RII |
| `resultados/tabela3.csv` | Tabela 3 — variação percentual anual (VPA), 2014-2024 e 2014-2023 |
| `resultados/valores_citados_no_texto.txt` | valores citados no texto e nas notas das tabelas (VPA 2014-2021, n da regressão, efeito da edição, testes de interação) |
| `figuras/figura1.*` | Figura 1 — prevalência total (A) e segundo escolaridade (B) |
| `figuras/figura2.*` | Figura 2 — SII (A) e RII (B) |
| `resultados/resultados.json` | todas as estimativas, sem arredondamento |

## Base analítica (`dados/base_analitica_vigitel_2014_2024.csv`)

409.017 registros (adultos entrevistados nas edições de 2014 a 2024; a edição de 2022 não foi realizada). Codificação UTF-8, separador vírgula.
SHA-256: `2d14d363b287dca8b8f9c57df7f7cddb27b352739cf58b6a27006deac59b743a`

| Variável | Descrição | Origem na base oficial |
|---|---|---|
| `edicao` | edição do inquérito (2014-2021, 2023, 2024) | `ano` |
| `cidade` | capital de residência (26 capitais e Distrito Federal) | `cidade` |
| `regiao` | macrorregião (Norte, Nordeste, Centro-Oeste, Sudeste, Sul) | `regiao` |
| `sexo` | Feminino; Masculino | `q7` |
| `idade` | idade em anos (18 ou mais) | `q6` |
| `faixa_etaria` | 18-34; 35-54; 55 ou mais | derivada de `q6` |
| `escolaridade_cod` | 1 = 0-8; 2 = 9-11; 3 = 12 ou mais anos de estudo | `fesc` |
| `escolaridade` | rótulo de `escolaridade_cod` | `fesc` |
| `raca_cor` | Branca; Preta; Parda; Amarela; Indígena; vazio = sem informação | `q69` (ver nota) |
| `fumante` | 1 = fuma diariamente ou ocasionalmente; 0 = não fuma | `fumante` |
| `peso` | fator de ponderação pós-estratificação (rake) | `pesorake2025` |

Nota sobre raça/cor da pele: na versão CSV da base oficial, os rótulos "amarela" e "parda/morena" estão invertidos em relação ao dicionário de dados oficial do Vigitel (código 3 = amarela; código 4 = parda). A base analítica segue o dicionário; a recodificação está em `scripts/00_preparar_base.py`.

## Métodos implementados (resumo)

- Prevalências ponderadas pelo peso rake, com IC95% por linearização em escala logit.
- Tendência temporal: regressão de Prais-Winsten do logaritmo da prevalência anual sobre o ano da edição, com correção da autocorrelação de primeira ordem; VPA e IC95% pela distribuição t de Student.
- Desigualdade: índice angular (SII) e índice relativo (RII) de desigualdade por regressão linear ponderada sobre a posição relativa dos grupos de escolaridade; IC95% por estimador robusto (SII) e método delta (RII).
- Regressão logística ponderada com IC95% por estimador robusto da variância (participantes com raça/cor informada, n=393.718); teste de Wald da interação escolaridade × edição.
