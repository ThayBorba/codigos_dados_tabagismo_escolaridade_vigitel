"""
03_figuras.py
Gera as Figuras 1 e 2 do artigo a partir de resultados/resultados.json, em PDF, SVG e PNG (300 dpi).

Figura 1: prevalência de tabagismo total (A) e segundo escolaridade (B), com IC95%, por edição.
Figura 2: índice angular de desigualdade - SII (A) e índice relativo de desigualdade - RII (B), com IC95%.
A linha é interrompida em 2022 (edição não realizada).
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MultipleLocator

RAIZ = Path(__file__).resolve().parents[1]
r = json.load(open(RAIZ / 'resultados' / 'resultados.json', encoding='utf-8'))
SAIDA = RAIZ / 'figuras'
SAIDA.mkdir(exist_ok=True)
r['ano'] = r['por_edicao']; r['ano_esc'] = r['por_edicao_escolaridade']; r['ineq'] = r['desigualdade']

years = sorted(int(a) for a in r['ano'])
C = ['#2a78d6', '#eb6834', '#1baf7a']          # paleta testada para daltonismo
MK = ['o', 's', '^']
TXT, TXT2, GRID = '#0b0b0b', '#52514e', '#e4e3df'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.edgecolor': TXT2, 'axes.labelcolor': TXT,
                     'xtick.color': TXT2, 'ytick.color': TXT2, 'svg.fonttype': 'none', 'pdf.fonttype': 42})
comma = FuncFormatter(lambda v, _: f'{v:.0f}' if abs(v - round(v)) < 1e-9 else f'{v:.1f}'.replace('.', ','))
comma2 = FuncFormatter(lambda v, _: f'{v:.1f}'.replace('.', ','))

def segs(xs):
    """quebra a linha no hiato de 2022"""
    return [[x for x in xs if x <= 2021], [x for x in xs if x >= 2023]]

def style(ax, ylab):
    ax.set_xticks(years); ax.set_xticklabels([str(y) for y in years], rotation=0)
    ax.tick_params(axis='x', labelsize=8)
    ax.grid(axis='y', color=GRID, lw=0.8); ax.set_axisbelow(True)
    for s in ['top', 'right']: ax.spines[s].set_visible(False)
    ax.set_ylabel(ylab); ax.set_xlabel('Edição do inquérito')
    ax.set_xlim(2013.5, 2024.5)

def band(ax, xs, get, color, mk, label):
    for sg in segs(xs):
        ax.plot(sg, [get(a)['p'] for a in sg], color=color, lw=2, solid_capstyle='round')
    ax.errorbar(xs, [get(a)['p'] for a in xs],
                yerr=[[get(a)['p'] - get(a)['lo'] for a in xs], [get(a)['hi'] - get(a)['p'] for a in xs]],
                fmt=mk, ms=6, color=color, mec='white', mew=1.2, ecolor=color, elinewidth=1, capsize=2.5, label=label, zorder=3)

# ---------- Figura 1: A total, B por escolaridade ----------
fig, axs = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
band(axs[0], years, lambda a: r['ano'][str(a)], C[0], 'o', 'Total')
style(axs[0], 'Prevalência de tabagismo (%)')
axs[0].set_title('A', loc='left', fontweight='bold', color=TXT)
labs = ['0-8 anos de estudo', '9-11 anos de estudo', '≥12 anos de estudo']
for i, e in enumerate([1, 2, 3]):
    band(axs[1], years, lambda a, e=e: r['ano_esc'][f'{a}_{e}'], C[i], MK[i], labs[i])
style(axs[1], '')
axs[1].set_title('B', loc='left', fontweight='bold', color=TXT)
axs[1].legend(frameon=False, fontsize=8, loc='lower left', ncol=1, handletextpad=0.4)
for ax in axs:
    ax.set_ylim(0, 20); ax.yaxis.set_major_locator(MultipleLocator(2)); ax.yaxis.set_major_formatter(comma)
    ax.annotate('Sem coleta\nem 2022', xy=(2022, 3.2), ha='center', fontsize=7, color=TXT2)
fig.tight_layout()
for ext in ['svg', 'pdf', 'png']:
    fig.savefig(SAIDA / f'figura1.{ext}', dpi=300, facecolor='white')
plt.close(fig)

# ---------- Figura 2: A SII, B RII (painéis separados — escalas distintas, sem eixo duplo) ----------
fig, axs = plt.subplots(1, 2, figsize=(10, 4))
ineq = r['ineq']
def plot_idx(ax, key, lo, hi, color, mk, ylab, ylim, ref=None):
    xs = years
    for sg in segs(xs):
        ax.plot(sg, [ineq[str(a)][key] for a in sg], color=color, lw=2)
    ax.errorbar(xs, [ineq[str(a)][key] for a in xs],
                yerr=[[ineq[str(a)][key] - ineq[str(a)][lo] for a in xs], [ineq[str(a)][hi] - ineq[str(a)][key] for a in xs]],
                fmt=mk, ms=6, color=color, mec='white', mew=1.2, elinewidth=1, capsize=2.5, zorder=3)
    style(ax, ylab); ax.set_ylim(*ylim)
    if ref is not None:
        ax.axhline(ref, color=TXT2, lw=1)
plot_idx(axs[0], 'SII', 'SII_lo', 'SII_hi', C[0], 'o', 'Índice angular de desigualdade (pontos percentuais)', (0, 16))
axs[0].yaxis.set_major_locator(MultipleLocator(2)); axs[0].yaxis.set_major_formatter(comma)
axs[0].set_title('A', loc='left', fontweight='bold', color=TXT)
plot_idx(axs[1], 'RII', 'RII_lo', 'RII_hi', C[1], 's', 'Índice relativo de desigualdade', (0, 4.5), ref=1)
axs[1].yaxis.set_major_locator(MultipleLocator(0.5)); axs[1].yaxis.set_major_formatter(comma2)
axs[1].set_title('B', loc='left', fontweight='bold', color=TXT)
axs[1].annotate('Igualdade (1,0)', xy=(2014, 1.08), fontsize=7, color=TXT2)
fig.tight_layout()
for ext in ['svg', 'pdf', 'png']:
    fig.savefig(SAIDA / f'figura2.{ext}', dpi=300, facecolor='white')
plt.close(fig)
print(f'Figuras -> {SAIDA}')
