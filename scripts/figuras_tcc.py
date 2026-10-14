"""Figuras dos capitulos 4 e 5 da monografia, numeradas como no Report 6.

    python -m scripts.figuras_tcc      # grava em docs/tcc/figuras/

Pouco texto dentro da figura de proposito: o que ela significa vai na legenda
do capitulo. Fontes: os mesmos ensaios de `load.graficos` (§11 de
`docs/performance.md`), o CSV congelado do OSRM, a tabela `regional_categories`
do Postgres carregado (precisa da pilha no ar) e as capturas de
`docs/evidencia/` (so leitura). Os numeros do funil sao os do stdout do ETL
registrados em `docs/tese-rastreabilidade.md` §3.

A Figura 5 (Home no modo de inspecao) e captura de tela, nao sai daqui.
"""

from __future__ import annotations

import os
import statistics as st
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

from load.graficos import CARGAS, CONDICOES, META_MS, TINTA, TINTA_2, _ensaios, _estilo, _log, _meta  # noqa: E402

SAIDA = Path("docs/tcc/figuras")
VERDE, VERDE_CLARO = "#12704a", "#e9f3ed"
AZUL_CLARO, CINZA_CLARO, LARANJA_CLARO = "#e6effa", "#f3f2ef", "#fdeee6"


# ---------------------------------------------------------------------------
# Diagramas: caixa + seta, coordenadas de 0 a 100
# ---------------------------------------------------------------------------

def _tela(largura: float, altura: float):
    _estilo()
    fig, ax = plt.subplots(figsize=(largura, altura))
    ax.set(xlim=(0, 100), ylim=(0, 100))
    ax.axis("off")
    return fig, ax


def _caixa(ax, x, y, w, h, texto, fundo=CINZA_CLARO, borda=TINTA_2, peso="normal", tam=9, tracejada=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.5",
                                facecolor=fundo, edgecolor=borda, linewidth=1.1,
                                linestyle="--" if tracejada else "-"))
    ax.text(x + w / 2, y + h / 2, texto, ha="center", va="center", fontsize=tam, color=TINTA,
            fontweight=peso, linespacing=1.35)


def _seta(ax, de, para, texto="", tracejada=False, dupla=False, deslocamento=(0, 2.2)):
    ax.annotate("", xy=para, xytext=de, arrowprops=dict(
        arrowstyle="<|-|>" if dupla else "-|>", color=TINTA_2, lw=1.1, mutation_scale=11,
        linestyle="--" if tracejada else "-", shrinkA=2, shrinkB=2))
    if texto:
        meio = ((de[0] + para[0]) / 2 + deslocamento[0], (de[1] + para[1]) / 2 + deslocamento[1])
        ax.text(*meio, texto, ha="center", va="bottom", fontsize=7.5, color=TINTA_2)


def _salvar(fig, nome: str) -> Path:
    SAIDA.mkdir(parents=True, exist_ok=True)
    caminho = SAIDA / nome
    fig.savefig(caminho, dpi=220, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    print(caminho)
    return caminho


def figura_arquitetura() -> Path:
    """Figura 6 — o que roda onde, e o que fala com o que."""
    fig, ax = _tela(9.5, 4.6)
    _caixa(ax, 1, 62, 12, 20, "Navegador")
    _caixa(ax, 17, 62, 13, 20, "Next.js\n(React)\nrenderizador\nSDUI", fundo=AZUL_CLARO)
    # BFF com as fatias verticais dentro
    ax.add_patch(FancyBboxPatch((45, 38), 32, 58, boxstyle="round,pad=0.4,rounding_size=2",
                                facecolor="white", edgecolor=TINTA_2, linewidth=1.2))
    ax.text(61, 92, "FastAPI (BFF)", ha="center", fontsize=10, fontweight="bold")
    for i, fatia in enumerate(("home_contextual", "product_detail", "checkout")):
        _caixa(ax, 47.5, 75 - i * 11.5, 27, 7.5, fatia, fundo=CINZA_CLARO, tam=8.5)
    _caixa(ax, 47.5, 41, 27, 8.5, "green_logistics\ncentroides em memória", fundo=VERDE_CLARO, borda=VERDE, tam=8.5)
    _caixa(ax, 84, 72, 15, 14, "Redis\ncache de telas", fundo=LARANJA_CLARO)
    _caixa(ax, 84, 42, 15, 14, "PostgreSQL")
    _caixa(ax, 50, 4, 22, 13, "ETL\n(Pandas)", fundo=CINZA_CLARO, tracejada=True)
    _caixa(ax, 18, 4, 21, 13, "CSV Olist", fundo=CINZA_CLARO, tracejada=True)

    _seta(ax, (13.6, 72), (16.4, 72), dupla=True)
    _seta(ax, (30.6, 76), (44.4, 76), "CEP + contexto", deslocamento=(0, 1.2))
    _seta(ax, (44.4, 68), (30.6, 68), "ScreenResponse", deslocamento=(0, -5.5))
    _seta(ax, (77.6, 79), (83.4, 79), dupla=True)
    _seta(ax, (77.6, 49), (83.4, 49), dupla=True)
    _seta(ax, (39.6, 10.5), (49.4, 10.5))
    _seta(ax, (72.6, 10.5), (91.5, 41.4), "carga", tracejada=True, deslocamento=(3, -4))
    return _salvar(fig, "fig-06-arquitetura.png")


def figura_modelo_dados() -> Path:
    """Figura 7 — tabelas do Olist (cinza) e derivadas no ETL (verde)."""
    fig, ax = _tela(9.5, 4.8)
    olist = {
        "clientes": (2, 66, "olist_customers\ncustomer_id · CEP · UF"),
        "pedidos": (2, 36, "olist_orders\norder_id · customer_id"),
        "itens": (35, 36, "olist_order_items\npedido · produto · vendedor\npreço · frete"),
        "produtos": (35, 66, "olist_products\nproduct_id · categoria\npeso · volume · nota"),
        "vendedores": (35, 4, "olist_sellers\nseller_id · CEP · UF"),
    }
    derivadas = {
        "ofertas": (70, 66, "offers\nproduto × vendedor\npreço · frete"),
        "centroides": (70, 30, "cep_centroids\nprefixo · lat · lng · UF"),
        "regional": (70, 2, "regional_categories\nUF · categoria · lift"),
    }
    w, h = 27, 21
    for x, y, texto in olist.values():
        _caixa(ax, x, y, w, h, texto, tam=8)
    for x, y, texto in derivadas.values():
        _caixa(ax, x, y, w, h, texto, fundo=VERDE_CLARO, borda=VERDE, tam=8)

    def centro(chave, lado):
        x, y, _ = {**olist, **derivadas}[chave]
        return {"d": (x + w + 0.6, y + h / 2), "e": (x - 0.6, y + h / 2),
                "c": (x + w / 2, y + h + 0.6), "b": (x + w / 2, y - 0.6)}[lado]

    _seta(ax, centro("clientes", "b"), centro("pedidos", "c"))
    _seta(ax, centro("pedidos", "d"), centro("itens", "e"))
    _seta(ax, centro("itens", "c"), centro("produtos", "b"))
    _seta(ax, centro("itens", "b"), centro("vendedores", "c"))
    _seta(ax, centro("produtos", "d"), centro("ofertas", "e"))
    _seta(ax, centro("vendedores", "d"), centro("centroides", "e"), "prefixo do CEP", tracejada=True, deslocamento=(-9, -2))
    _seta(ax, centro("centroides", "b"), centro("regional", "c"), "UF", tracejada=True, deslocamento=(3, -1))
    return _salvar(fig, "fig-07-modelo-de-dados.png")


def figura_fluxo_composicao() -> Path:
    """Figura 8 — uma requisicao da Home, do CEP ao componente na tela."""
    fig, ax = _tela(10, 2.5)
    ax.set_ylim(18, 84)
    etapas = [
        ("CEP +\ncontexto", AZUL_CLARO, TINTA_2), ("Redis", LARANJA_CLARO, TINTA_2),
        ("Ofertas\n(PostgreSQL)", CINZA_CLARO, TINTA_2), ("Distância\ne CO₂", VERDE_CLARO, VERDE),
        ("Escolha da\noferta", VERDE_CLARO, VERDE), ("Screen-\nResponse", CINZA_CLARO, TINTA_2),
        ("Next.js\nREGISTRY", AZUL_CLARO, TINTA_2),
    ]
    xs = [1 + i * 14.2 for i in range(len(etapas))]
    for x, (texto, fundo, borda) in zip(xs, etapas):
        _caixa(ax, x, 50, 11, 26, texto, fundo=fundo, borda=borda, tam=8.5)
    for x in xs[:-1]:
        _seta(ax, (x + 11.6, 63), (x + 14.6, 63))
    ax.text(xs[1] + 13.1, 78.5, "miss", ha="center", fontsize=7.5, color=TINTA_2)
    # Acerto no Redis pula a composicao inteira e devolve a tela pronta
    ax.annotate("", xy=(xs[-1] + 5.5, 49.4), xytext=(xs[1] + 5.5, 49.4),
                arrowprops=dict(arrowstyle="-|>", color=TINTA_2, lw=1.1, linestyle="--",
                                connectionstyle="arc3,rad=0.16", mutation_scale=11))
    ax.text(50, 31, "hit: tela pronta", ha="center", fontsize=7.5, color=TINTA_2)
    return _salvar(fig, "fig-08-fluxo-de-composicao.png")


# ---------------------------------------------------------------------------
# Capitulo 5
# ---------------------------------------------------------------------------

def figura_funil() -> Path:
    """Figura 9 — dois universos: o completo (analises) e a amostra (aplicacao)."""
    fig, ax = _tela(10, 3.9)
    ax.text(0, 93, "Análises offline", fontsize=9, fontweight="bold", color=TINTA_2)
    linha_a = [(1, "Dataset completo\n112.650 itens"), (34, "Com centroides\n112.096"), (68, "Mensuráveis em CO₂\n112.070")]
    for x, texto in linha_a:
        _caixa(ax, x, 64, 28, 20, texto, tam=8.5)
    for x0 in (28.6, 62.6):
        _seta(ax, (x0, 74), (x0 + 4.8, 74))

    ax.text(0, 46, "Aplicação (amostra, semente 42)", fontsize=9, fontweight="bold", color=TINTA_2)
    linha_b = [(1, "Sorteio\n10.000 linhas"), (24, "Completada\n60.636 itens"), (48, "Persistidos\n60.292 itens")]
    for x, texto in linha_b:
        _caixa(ax, x, 17, 19, 20, texto, tam=8.5)
    for x0 in (19.6, 43.6):
        _seta(ax, (x0, 27), (x0 + 3.8, 27))
    ax.text(45.5, 9, "−344: sem peso (17), sem CEP do vendedor (144),\nsem CEP do cliente (183)",
            ha="center", va="top", fontsize=7.5, color=TINTA_2)
    for i, texto in enumerate(("53.114 pedidos", "7.356 ofertas", "12.933 centroides")):
        y = 31 - i * 10
        _caixa(ax, 78, y, 21, 6.5, texto, fundo=VERDE_CLARO, borda=VERDE, tam=8)
        _seta(ax, (67.6, 27), (77.4, y + 3.2))
    return _salvar(fig, "fig-09-funil-dos-dados.png")


def figura_osrm() -> Path:
    """Figura 10 — reaproveita a do `scripts.haversine_osrm`, gravada aqui."""
    from scripts.haversine_osrm import grafico

    caminho = SAIDA / "fig-10-haversine-osrm.png"
    grafico(saida=caminho)
    return caminho


ROTULOS = {
    "moveis_sala": "Móveis de sala", "telefonia": "Telefonia", "relogios_presentes": "Relógios e presentes",
    "malas_acessorios": "Malas e acessórios", "alimentos": "Alimentos", "eletronicos": "Eletrônicos",
    "cool_stuff": "Cool stuff", "automotivo": "Automotivo", "ferramentas_jardim": "Ferramentas e jardim",
}


def figura_contexto_regional() -> Path:
    """Figura 11 — a categoria que cada UF compra acima da media, e quanto acima."""
    from sqlalchemy import create_engine, text

    url = os.environ.get("DATABASE_URL") or next(
        linha.split("=", 1)[1].strip() for linha in Path(".env").read_text(encoding="utf-8").splitlines()
        if linha.startswith("DATABASE_URL="))
    url = url.replace("postgresql+asyncpg://", "postgresql+psycopg://")
    with create_engine(url).connect() as con:
        linhas = con.execute(text("SELECT uf, category, lift FROM regional_categories ORDER BY lift")).all()

    _estilo()
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ufs = [r.uf for r in linhas]
    ax.barh(ufs, [r.lift for r in linhas], color=VERDE, height=0.62)
    for i, r in enumerate(linhas):
        rotulo = ROTULOS.get(r.category, r.category.replace("_", " ").capitalize())
        ax.text(r.lift + 0.02, i, f"{rotulo}  {r.lift:.2f}×".replace(".", ","), va="center", fontsize=8, color=TINTA)
    ax.axvline(1, color=TINTA_2, linestyle="--", linewidth=1)
    ax.set(xlim=(0.9, 2.45), xlabel="lift (participação na UF ÷ participação no Brasil)")
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.1f}".replace(".", ",")))
    ax.grid(axis="y", visible=False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.tight_layout()
    return _salvar(fig, "fig-11-contexto-regional.png")


def figura_desempenho() -> Path:
    """Figura 12 — p95 contra vazao: onde cada condicao de cache sai da meta."""
    dados = _ensaios()
    _estilo()
    fig, ax = plt.subplots(figsize=(6.4, 4))
    for cond, (rotulo, cor, marcador) in CONDICOES.items():
        xs, ys = [], []
        for u in CARGAS:
            ms = dados[(u, cond)]
            xs.append(st.fmean(m["rps"] for m in ms))
            ys.append(st.fmean(m["p95"] for m in ms))
        ax.plot(xs, ys, color=cor, linewidth=1.8, marker=marcador, markersize=7, label=rotulo, zorder=3)
        if cond == "off":
            for u, x, y in zip(CARGAS, xs, ys):
                ax.annotate(f"{u:,} VU".replace(",", "."), (x, y), textcoords="offset points", xytext=(7, -4), fontsize=8, color=TINTA_2)
    ax.annotate("1.000 VU", (397, 3000), textcoords="offset points", xytext=(-8, 8), ha="right", fontsize=8, color=TINTA_2)
    _meta(ax)
    _log(ax)
    ax.text(300, META_MS * 1.12, "meta 200 ms", fontsize=8, color=TINTA_2)
    ax.set(xlim=(0, 450), xlabel="vazão (req/s)", ylabel="latência p95 (ms, escala log)")
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    return _salvar(fig, "fig-12-desempenho.png")


def figura_mutacoes() -> Path:
    """Figura 13 — as capturas do E2E de mutacao, lado a lado, so com a letra."""
    capturas = ["0-linha-de-base", "1-reordenacao", "2-injecao-de-selo", "3a-bloco-novo", "3b-bloco-desconhecido"]
    _estilo()
    # 2 x 3: cinco capturas numa linha ficam ilegiveis na largura de uma pagina A4
    fig, eixos = plt.subplots(2, 3, figsize=(10, 6.4))
    for ax in eixos.flat:
        ax.axis("off")
    for ax, nome, letra in zip(eixos.flat, capturas, "abcde"):
        ax.imshow(plt.imread(Path("docs/evidencia") / f"{nome}.png"))
        ax.set_title(f"({letra})", fontsize=10)
    fig.tight_layout(w_pad=0.8, h_pad=1.0)
    return _salvar(fig, "fig-13-mutacoes.png")


def main() -> None:
    for figura in (figura_arquitetura, figura_modelo_dados, figura_fluxo_composicao, figura_funil,
                   figura_osrm, figura_contexto_regional, figura_desempenho, figura_mutacoes):
        figura()


if __name__ == "__main__":
    main()
