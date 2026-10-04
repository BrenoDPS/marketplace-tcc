"""Graficos do capitulo 5 a partir dos ensaios do protocolo da §3.3.

A §3.3 promete "graficos de dispersao e evolucao temporal, confrontando a vazao
em requisicoes por segundo com a elevacao das curvas de latencia nos percentis
p50, p95 e p99". Tres figuras, das mesmas fontes do resultado final
(`docs/performance.md` §11): a repeticao 1 da primeira execucao e as
repeticoes 2-3 refeitas na tomada.

    pip install matplotlib        # so para isto; a API nao depende dele
    python -m load.graficos       # grava em docs/graficos/

Cores: tres condicoes de cache = os tres primeiros slots da paleta categorica
validada (todos os pares passam o teste de daltonismo); o aqua fica abaixo de
3:1 de contraste, por isso cada condicao tambem tem marcador proprio — a figura
continua legivel impressa em preto e branco.
"""

from __future__ import annotations

import csv
import statistics as st
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

from load.resumo import ler_ensaio  # noqa: E402

FONTES = [
    *sorted(Path("load/results/protocolo").glob("r1-*_stats.csv")),
    *sorted(Path("load/results/protocolo-rep23").glob("r*_stats.csv")),
]
SAIDA = Path("docs/graficos")
CONDICOES = {  # identidade fixa: a cor segue a condicao, nunca a ordem
    "off": ("cache desabilitado", "#2a78d6", "o"),
    "frio": ("cache frio", "#eb6834", "s"),
    "aquecido": ("cache aquecido", "#1baf7a", "^"),
}
CARGAS = (50, 250, 1000)
META_MS = 200
TINTA, TINTA_2, GRADE = "#0b0b0b", "#52514e", "#e4e3df"


def _estilo() -> None:
    plt.rcParams.update({
        "figure.facecolor": "white", "axes.facecolor": "white",
        "axes.edgecolor": TINTA_2, "axes.labelcolor": TINTA, "text.color": TINTA,
        "xtick.color": TINTA_2, "ytick.color": TINTA_2,
        "axes.grid": True, "grid.color": GRADE, "grid.linewidth": 0.6,
        "axes.spines.top": False, "axes.spines.right": False,
        "font.size": 9, "axes.titlesize": 10, "legend.frameon": False,
    })


def _numero(v: float, _pos: int) -> str:
    """Eixo log em numero comum ("20", "200", "2.000"), nao "2x10^2"."""
    mantissa = v / 10 ** int(f"{v:e}".split("e")[1])
    return f"{v:,.0f}".replace(",", ".") if round(mantissa) in (1, 2, 5) and v >= 1 else ""


def _log(ax, eixo: str = "y") -> None:
    getattr(ax, f"set_{eixo}scale")("log")
    alvo = ax.yaxis if eixo == "y" else ax.xaxis
    alvo.set_major_formatter(FuncFormatter(_numero))
    alvo.set_minor_formatter(FuncFormatter(_numero))


def _legenda(fig, eixo) -> None:
    """Legenda no topo da figura, fora da area de dados."""
    fig.legend(*eixo.get_legend_handles_labels(), loc="upper center", ncol=3,
               bbox_to_anchor=(0.5, 0.93), fontsize=8)


def _meta(ax, vertical: bool = False) -> None:
    linha = ax.axvline if vertical else ax.axhline
    linha(META_MS, color=TINTA_2, linestyle="--", linewidth=1, zorder=1)


def _ensaios(rota: str = "Aggregated") -> dict[tuple[int, str], list[dict[str, float]]]:
    por_celula: dict[tuple[int, str], list[dict[str, float]]] = defaultdict(list)
    for stats in FONTES:
        _, u, cond = stats.name[: -len("_stats.csv")].split("-")
        m, _, _ = ler_ensaio(stats, rota)
        por_celula[(int(u[1:]), cond)].append(m)
    return por_celula


def figura_dispersao() -> Path:
    """Vazao x p50/p95/p99: cada ponto pequeno e um ensaio; a linha liga as medias."""
    dados = _ensaios()
    fig, eixos = plt.subplots(1, 3, figsize=(10, 3.6), sharex=True)
    for ax, pct in zip(eixos, ("p50", "p95", "p99")):
        for cond, (rotulo, cor, marcador) in CONDICOES.items():
            xs, ys = [], []
            for u in CARGAS:
                ms = dados[(u, cond)]
                ax.scatter([m["rps"] for m in ms], [m[pct] for m in ms], s=14, facecolors="none",
                           edgecolors=cor, linewidths=0.8, marker=marcador, zorder=2)
                xs.append(st.fmean(m["rps"] for m in ms))
                ys.append(st.fmean(m[pct] for m in ms))
            ax.plot(xs, ys, color=cor, linewidth=1.6, marker=marcador, markersize=6, label=rotulo, zorder=3)
            if cond == "off":
                for u, x, y in zip(CARGAS, xs, ys):
                    # 50 VU acima do ponto: a direita ficam as linhas com cache
                    deslocamento, alinhamento = ((4, 8), "left") if u == 50 else ((7, -10), "left")
                    ax.annotate(f"{u} VU", (x, y), textcoords="offset points", xytext=deslocamento,
                                ha=alinhamento, fontsize=7, color=TINTA_2)
        _meta(ax)
        _log(ax)
        ax.set_xlim(0, 450)
        ax.set_title(f"Latência {pct}")
        ax.set_xlabel("vazão (req/s)")
    eixos[0].set_ylabel("latência (ms, escala log)")
    eixos[0].text(200, META_MS * 1.15, "meta 200 ms", fontsize=7, color=TINTA_2)
    _legenda(fig, eixos[0])
    fig.suptitle("Vazão × latência por condição de cache — 1 worker, n = 3 (pontos vazados: ensaios)", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    return _salvar(fig, "fig-5-1-vazao-x-latencia.png")


def _serie(stats_history: Path) -> dict[int, tuple[float, float]]:
    with stats_history.open(encoding="utf-8") as f:
        linhas = [r for r in csv.DictReader(f) if r["Name"] == "Aggregated"]
    t0 = int(linhas[0]["Timestamp"])
    return {
        int(r["Timestamp"]) - t0: (float(r["50%"]), float(r["95%"]))
        for r in linhas if r["50%"] not in ("", "N/A") and r["95%"] not in ("", "N/A")
    }


def figura_serie_temporal() -> Path:
    """Inicio do ensaio, mediana das 3 repeticoes a cada segundo: a rajada de misses do frio."""
    fig, eixos = plt.subplots(2, 2, figsize=(10, 6.2), sharex="col")
    for linha, (u, rampa, janela) in enumerate(((250, 25, 300), (1000, 40, 300))):
        for cond, (rotulo, cor, marcador) in CONDICOES.items():
            series = [
                _serie(s.with_name(s.name.replace("_stats.csv", "_stats_history.csv")))
                for s in FONTES if s.name.endswith(f"-u{u}-{cond}_stats.csv")
            ]
            ts = [t for t in range(janela + 1) if all(t in s for s in series)]
            for col, idx in enumerate((0, 1)):
                ys = [st.median(s[t][idx] for s in series) for t in ts]
                eixos[linha][col].plot(ts, ys, color=cor, linewidth=1.4, label=rotulo,
                                       marker=marcador, markevery=(15, 30), markersize=5)
        for col, pct in enumerate(("p50", "p95")):
            ax = eixos[linha][col]
            ax.axvspan(0, rampa, color=GRADE, alpha=0.6, zorder=0, linewidth=0)
            ax.text(rampa / 2, 0.97, "rampa", transform=ax.get_xaxis_transform(), ha="center",
                    va="top", fontsize=7, color=TINTA_2)
            _meta(ax)
            _log(ax)
            ax.set_title(f"{u} VU — {pct} (janela móvel do Locust)")
            if linha == 1:
                ax.set_xlabel("tempo desde o início do ensaio (s)")
        eixos[linha][0].set_ylabel("latência (ms, escala log)")
    _legenda(fig, eixos[0][0])
    fig.suptitle("Penalidade dos cache misses: os primeiros 5 minutos (mediana de 3 repetições por segundo)", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    return _salvar(fig, "fig-5-2-serie-temporal-frio-aquecido.png")


def figura_por_rota() -> Path:
    """1.000 VU: a Home cacheada cumpre a meta; as rotas sem cache carregam a fila."""
    with FONTES[0].open(encoding="utf-8") as f:
        rotas = [r["Name"] for r in csv.DictReader(f) if r["Name"] not in ("Aggregated", "[setup] home")]
    rotas = sorted(rotas, key=lambda r: (not r.startswith("GET /home"), r)) + ["Aggregated"]
    fig, eixos = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
    deslocamento = {"off": -0.22, "frio": 0.0, "aquecido": 0.22}
    for ax, pct in zip(eixos, ("p50", "p95")):
        for cond, (rotulo, cor, marcador) in CONDICOES.items():
            for i, rota in enumerate(rotas):
                ms = _ensaios(rota)[(1000, cond)]
                vals = [m[pct] for m in ms]
                media = st.fmean(vals)
                dp = st.stdev(vals) if len(vals) > 1 else 0.0
                ax.errorbar(media, i + deslocamento[cond], xerr=[[min(dp, media * 0.9)], [dp]], fmt=marcador,
                            color=cor, markersize=6, elinewidth=1, capsize=2,
                            label=rotulo if i == 0 else None, zorder=3)
        _meta(ax, vertical=True)
        _log(ax, "x")
        ax.set_title(f"{pct} a 1.000 VU (média ± dp)")
        ax.set_xlabel("latência (ms, escala log)")
        ax.grid(axis="y", visible=False)
    nomes = [r.replace("Aggregated", "agregado (todas as rotas)") for r in rotas]
    eixos[0].set_yticks(range(len(rotas)), nomes)
    eixos[0].invert_yaxis()
    eixos[0].text(META_MS * 1.1, len(rotas) - 0.6, "meta 200 ms", fontsize=7, color=TINTA_2)
    _legenda(fig, eixos[0])
    fig.suptitle("Por rota, no pico: a Home é cacheada; /products e /checkout não", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.89))
    return _salvar(fig, "fig-5-3-por-rota-1000vu.png")


def _salvar(fig, nome: str) -> Path:
    SAIDA.mkdir(parents=True, exist_ok=True)
    destino = SAIDA / nome
    fig.savefig(destino, dpi=300)
    plt.close(fig)
    return destino


def main() -> None:
    _estilo()
    for f in (figura_dispersao, figura_serie_temporal, figura_por_rota):
        print(f())


if __name__ == "__main__":
    main()
