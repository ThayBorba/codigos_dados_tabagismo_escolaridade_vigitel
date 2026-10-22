"""
Executa o pipeline completo, do arquivo oficial do Vigitel até tabelas e figuras.
Uso: python executar_tudo.py caminho/para/vigitel-2006-2024-peso-rake-csv.zip
"""
import subprocess
import sys
from pathlib import Path

if len(sys.argv) != 2:
    sys.exit('Uso: python executar_tudo.py <arquivo .zip ou .csv do Vigitel 2006-2024>')
pasta = Path(__file__).resolve().parent / 'scripts'
etapas = [['00_preparar_base.py', sys.argv[1]], ['01_analise.py'], ['02_tabelas.py'], ['03_figuras.py']]
for etapa in etapas:
    print(f'\n=== {etapa[0]} ===')
    subprocess.run([sys.executable, str(pasta / etapa[0]), *etapa[1:]], check=True)
