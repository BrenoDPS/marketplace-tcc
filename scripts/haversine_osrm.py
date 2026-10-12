"""Haversine x rota real (OSRM) — o quanto a simplificacao da linha reta pesa.

A metodologia (§3) promete: 100 pares origem-destino em faixas de distancia,
Haversine contra a rota do OSRM (malha do OpenStreetMap), com MAE, MAPE e
Spearman, e o percentual em que os dois metodos preservam a ordem dos vendedores.

Duas amostras do dataset Olist COMPLETO, semente fixa:

- **A — precisao:** 100 pares (vendedor, comprador) de COMPRAS REAIS, 20 por
  faixa de linha reta. Mede a linha reta crua E a estrada estimada pelo motor de
  CO2 (`co2.road_distance_km`, x 1,345) contra a rota.
- **B — ordem:** decisoes reais da vitrine — um comprador de um produto vendido
  por mais de um vendedor, com TODAS as ofertas dele — ate somar 100 pares.
  Mede se o vendedor mais proximo em linha reta e o mais proximo pela estrada,
  e quanto custa em km de estrada quando nao e.

    python -m scripts.haversine_osrm            # grava docs/resultados/haversine-osrm.{md,csv}
    python -m scripts.haversine_osrm --grafico  # docs/graficos/fig-5-4-haversine-osrm.png, so do CSV

O CSV guarda a resposta do OSRM por par e serve de cache: rodar de novo nao
consulta o servidor (a malha do OSM muda; o resultado publicado fica fixo).
Servidor publico de demonstracao, perfil `driving`: 1 requisicao/s, como pede a
politica de uso dele.
"""

from __future__ import annotations

import json
import subprocess
import time
import urllib.request
from datetime import date
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.concentracao_regional import _haversine
from scripts.etl_load_sample import build_cep_centroids, load_csvs, normalize_prefixes
from src.features.green_logistics.badge import RESOLUTION_FLOOR_KM
from src.features.green_logistics.co2 import CIRCUITY_FACTOR
from src.features.green_logistics.offers import TOLERANCIA_RELATIVA

SAIDA = Path("docs/resultados/haversine-osrm.md")
CACHE = SAIDA.with_suffix(".csv")
OSRM = "https://router.project-osrm.org/table/v1/driving/"
SEMENTE = 42
FAIXAS = [RESOLUTION_FLOOR_KM, 100, 500, 1000, 2000, np.inf]  # 100 = limiar do selo
POR_FAIXA = 20
PARES_B = 100


def _osrm(destino: tuple[float, float], origens: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Rota de cada origem ate o destino: `(km, metros do centroide ate a via)`. Sem rota = nan."""
    coords = ";".join(f"{lng:.6f},{lat:.6f}" for lat, lng in [destino, *origens])
    fontes = ";".join(str(i) for i in range(1, len(origens) + 1))
    url = f"{OSRM}{coords}?sources={fontes}&destinations=0&annotations=distance"
    req = urllib.request.Request(url, headers={"User-Agent": "marketplace-tcc/1.0 (TCC Facens)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        resp = json.load(r)
    time.sleep(1.0)
    assert resp["code"] == "Ok", resp
    return [
        (np.nan if linha[0] is None else linha[0] / 1000, fonte["distance"])
        for linha, fonte in zip(resp["distances"], resp["sources"], strict=True)
    ]


def _amostras(data_dir: Path) -> pd.DataFrame:
    frames = load_csvs(data_dir)
    normalize_prefixes(frames)
    itens = (
        frames["order_items"][["order_id", "product_id", "seller_id", "price"]]
        .merge(frames["orders"][["order_id", "customer_id"]], on="order_id")
        .merge(frames["customers"][["customer_id", "customer_zip_code_prefix"]], on="customer_id")
        .merge(frames["sellers"][["seller_id", "seller_zip_code_prefix"]], on="seller_id")
        .rename(columns={"customer_zip_code_prefix": "destino", "seller_zip_code_prefix": "origem"})
    )
    pos = build_cep_centroids(frames["geolocation"], set(itens["destino"]) | set(itens["origem"]))
    pos = pos.set_index("zip_prefix")[["lat", "lng"]]
    itens = itens[itens["destino"].isin(pos.index) & itens["origem"].isin(pos.index)]

    def hav(df: pd.DataFrame) -> np.ndarray:
        o, d = pos.reindex(df["origem"]).to_numpy(), pos.reindex(df["destino"]).to_numpy()
        return _haversine(o[:, 0], o[:, 1], d[:, 0], d[:, 1])

    # A: pares distintos de compras reais, estratificados pela linha reta.
    a = itens[["origem", "destino"]].drop_duplicates()
    a = a.assign(hav_km=hav(a), faixa=lambda d: pd.cut(d["hav_km"], FAIXAS, right=False))
    a = a.dropna(subset=["faixa"]).groupby("faixa", observed=True).sample(POR_FAIXA, random_state=SEMENTE)
    a = a.assign(parte="A", grupo=range(len(a)))

    # B: (comprador, produto) com ofertas em pelo menos 2 CEPs distintos — ofertas no
    # mesmo CEP empatam nos dois metodos e inflariam a concordancia.
    ofertas = itens[["product_id", "origem"]].drop_duplicates()
    ofertas = ofertas[ofertas.groupby("product_id")["origem"].transform("size") >= 2]
    decisoes = itens.loc[itens["product_id"].isin(ofertas["product_id"]), ["destino", "product_id"]].drop_duplicates()
    decisoes = decisoes.sample(frac=1, random_state=SEMENTE).merge(ofertas, on="product_id", sort=False)
    decisoes["grupo"] = decisoes.groupby(["destino", "product_id"], sort=False).ngroup()
    tamanho = decisoes.groupby("grupo").size()
    inteiros = tamanho.index[tamanho.cumsum() - tamanho < PARES_B]  # grupos inteiros ate somar 100 pares
    decisoes = decisoes[decisoes["grupo"].isin(inteiros)]
    b = decisoes.assign(hav_km=hav(decisoes), parte="B")

    pares = pd.concat([a, b], ignore_index=True)
    pares[["o_lat", "o_lng"]] = pos.reindex(pares["origem"]).to_numpy()
    pares[["d_lat", "d_lng"]] = pos.reindex(pares["destino"]).to_numpy()
    return pares


def _com_rotas(pares: pd.DataFrame) -> pd.DataFrame:
    cache = pd.read_csv(CACHE, dtype={"origem": str, "destino": str}) if CACHE.exists() else None
    if cache is not None:
        rotas = cache.drop_duplicates(["origem", "destino"]).set_index(["origem", "destino"])[["osrm_km", "snap_m"]]
        pares = pares.join(rotas, on=["origem", "destino"])
    else:
        pares = pares.assign(osrm_km=np.nan, snap_m=np.nan)
    falta = pares["osrm_km"].isna() & pares["snap_m"].isna()
    for (_, _), g in pares[falta].groupby(["parte", "grupo"]):
        d = tuple(g[["d_lat", "d_lng"]].iloc[0])
        pares.loc[g.index, ["osrm_km", "snap_m"]] = _osrm(d, list(map(tuple, g[["o_lat", "o_lng"]].to_numpy())))
        print(f"  {g['parte'].iloc[0]}{g['grupo'].iloc[0]}: {len(g)} rota(s)")
    return pares


def _erros(df: pd.DataFrame) -> dict[str, float]:
    est = df["hav_km"] * CIRCUITY_FACTOR
    return {
        "n": len(df),
        "mae_hav": (df["hav_km"] - df["osrm_km"]).abs().mean(),
        "mape_hav": ((df["hav_km"] - df["osrm_km"]).abs() / df["osrm_km"]).mean(),
        "mae_est": (est - df["osrm_km"]).abs().mean(),
        "mape_est": ((est - df["osrm_km"]).abs() / df["osrm_km"]).mean(),
        "vies_est": ((est - df["osrm_km"]) / df["osrm_km"]).median(),
        "spearman": df["hav_km"].rank().corr(df["osrm_km"].rank()),
        "circ_p10": (df["osrm_km"] / df["hav_km"]).quantile(0.10),
        "circ_med": (df["osrm_km"] / df["hav_km"]).median(),
        "circ_p90": (df["osrm_km"] / df["hav_km"]).quantile(0.90),
    }


def _ordem(b: pd.DataFrame) -> dict[str, float]:
    topo, custo, rel, empate, conc, total = [], [], [], 0, 0, 0
    for _, g in b.groupby("grupo"):
        escolha, melhor = g.loc[g["hav_km"].idxmin()], g.loc[g["osrm_km"].idxmin()]
        topo.append(escolha["osrm_km"] <= melhor["osrm_km"] + 1e-9)
        if not topo[-1]:
            custo.append(escolha["osrm_km"] - melhor["osrm_km"])
            rel.append(custo[-1] / melhor["osrm_km"])
            # A regra (`escolher_oferta`) ja trata as duas como equidistantes e decide pelo preco.
            empate += melhor["hav_km"] <= escolha["hav_km"] + max(RESOLUTION_FLOOR_KM, TOLERANCIA_RELATIVA * escolha["hav_km"])
        for (_, x), (_, y) in combinations(g.iterrows(), 2):
            if x["origem"] == y["origem"]:
                continue
            total += 1
            conc += np.sign(x["hav_km"] - y["hav_km"]) == np.sign(x["osrm_km"] - y["osrm_km"])
    return {
        "decisoes": len(topo),
        "pares": len(b),
        "topo": np.mean(topo),
        "divergentes": len(custo),
        "empate_na_regra": empate,
        "custo_km_med": np.median(custo) if custo else 0.0,
        "custo_km_max": max(custo, default=0.0),
        "custo_rel_max": max(rel, default=0.0),
        "comparacoes": total,
        "concordantes": conc / total,
    }


def _markdown(a: pd.DataFrame, b: pd.DataFrame, sem_rota: int) -> str:
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    pct = lambda x: f"{x * 100:.1f}%".replace(".", ",")  # noqa: E731
    num = lambda x, c=0: f"{x:,.{c}f}".replace(",", "X").replace(".", ",").replace("X", ".")  # noqa: E731
    fx = lambda f: f"≥ {num(f.left)} km" if np.isinf(f.right) else f"{num(f.left)}–{num(f.right)} km"  # noqa: E731

    def linha(rotulo: str, e: dict[str, float]) -> str:
        return (f"| {rotulo} | {e['n']} | {num(e['mae_hav'], 1)} | {pct(e['mape_hav'])} | {num(e['mae_est'], 1)} "
                f"| {pct(e['mape_est'])} | {pct(e['vies_est'])} | {num(e['spearman'], 3)} "
                f"| {num(e['circ_med'], 2)} ({num(e['circ_p10'], 2)}–{num(e['circ_p90'], 2)}) |")

    geral, o = _erros(a), _ordem(b)
    linhas = [
        "# Haversine × rota real (OSRM)",
        "",
        f"> Gerado por `python -m scripts.haversine_osrm` no commit `{commit}`, em {date.today():%d/%m/%Y}, sobre o",
        "> dataset Olist **completo**. Rotas: servidor público do OSRM (`router.project-osrm.org`, perfil",
        "> `driving`, malha do OpenStreetMap), entre os mesmos centroides de prefixo de CEP que a aplicação",
        f"> usa. Respostas por par em `{CACHE.as_posix()}` (cache: rodar de novo não consulta o servidor).",
        "",
        "## A — precisão: 100 pares de compras reais, 20 por faixa de linha reta",
        "",
        "\"Estimada\" = linha reta × 1,345, a estrada que o motor de CO₂ usa (`co2.road_distance_km`).",
        "Viés = mediana de (estimada − rota) / rota: positivo, o motor superestima a estrada.",
        "",
        "| faixa (linha reta) | n | MAE linha reta (km) | MAPE linha reta | MAE estimada (km) | MAPE estimada "
        "| viés estimada | Spearman | rota ÷ linha reta: mediana (p10–p90) |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    linhas += [linha(fx(f), _erros(g)) for f, g in a.groupby("faixa", observed=True)]
    linhas += [
        linha("**todas**", geral),
        "",
        "## B — ordem: a decisão que a vitrine toma",
        "",
        f"{o['decisoes']} decisões reais (um comprador de um produto vendido por vendedores em CEPs distintos, "
        f"com todas as ofertas do produto), {o['pares']} pares.",
        "",
        "| | valor |",
        "|---|---|",
        f"| o mais próximo em linha reta **é** o mais próximo pela estrada | **{pct(o['topo'])}** das decisões |",
        f"| pares de vendedores na mesma ordem nos dois métodos | {pct(o['concordantes'])} "
        f"de {o['comparacoes']} comparações |",
        f"| decisões em que diverge | {o['divergentes']} — em {o['empate_na_regra']} delas a regra da vitrine "
        "(`escolher_oferta`) já trata os dois vendedores como equidistantes e decide pelo preço |",
        f"| quando diverge: estrada a mais da escolha por linha reta | mediana {num(o['custo_km_med'], 1)} km; "
        f"pior caso {num(o['custo_km_max'], 1)} km ({pct(o['custo_rel_max'])} da rota) |",
        "",
        "## Limites",
        "",
        "- Origem e destino são **centroides de prefixo de CEP**, não endereços: o erro de posição do",
        "  centroide é o mesmo nos dois métodos e não entra nesta comparação.",
        f"- O OSRM encaixa cada ponto na via mais próxima; a distância até ela fica fora da rota "
        f"(mediana {num(pd.concat([a, b])['snap_m'].median())} m, máxima {num(pd.concat([a, b])['snap_m'].max())} m).",
        f"- Pares sem rota no OSRM: {sem_rota} (fora das métricas).",
        "- Rota = caminho mais rápido de carro, não o da transportadora; balsas entram na rota.",
    ]
    return "\n".join(linhas) + "\n"


def grafico(saida: Path = Path("docs/graficos/fig-5-4-haversine-osrm.png")) -> None:
    """Figura do cap. 5, so do CSV (sem dataset, sem rede). Paleta e estilo de `load.graficos`."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from load.graficos import TINTA_2, _estilo, _numero

    a = pd.read_csv(CACHE, dtype={"origem": str, "destino": str}).query("parte == 'A'").dropna(subset=["osrm_km"])
    a["circ"] = a["osrm_km"] / a["hav_km"]
    faixas = list(dict.fromkeys(a.sort_values("hav_km")["faixa"]))
    azul, laranja = "#2a78d6", "#eb6834"
    _estilo()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 3.9), gridspec_kw={"width_ratios": [1, 1.15]})

    x = np.array([1.0, 6000.0])
    ax1.plot(x, x * CIRCUITY_FACTOR, color=laranja, linewidth=2, label="motor: linha reta × 1,345")
    ax1.plot(x, x, color=TINTA_2, linestyle="--", linewidth=1.2, label="rota = linha reta")
    ax1.scatter(a["hav_km"], a["osrm_km"], s=22, color=azul, edgecolor="white", linewidth=0.6, zorder=3,
                label="par origem-destino")
    ax1.legend(loc="upper left", fontsize=8)
    ax1.set(xscale="log", yscale="log", xlim=(5, 5000), ylim=(5, 5000),
            xlabel="linha reta — Haversine (km)", ylabel="rota OSRM (km)")
    for eixo in (ax1.xaxis, ax1.yaxis):
        eixo.set_major_formatter(matplotlib.ticker.FuncFormatter(_numero))
    ax1.set_title("(a) 100 pares de compras reais", loc="left")

    rng = np.random.default_rng(SEMENTE)
    for i, f in enumerate(faixas):
        y = a.loc[a["faixa"] == f, "circ"]
        ax2.scatter(i + rng.uniform(-0.18, 0.18, len(y)), y, s=18, color=azul, alpha=0.75,
                    edgecolor="white", linewidth=0.5, zorder=3)
        ax2.plot([i - 0.28, i + 0.28], [y.median()] * 2, color=TINTA_2, linewidth=2.2, zorder=4,
                 label="mediana da faixa" if i == 0 else None)
        ax2.annotate(f"{y.median():.2f}".replace(".", ","), (i + 0.3, y.median()), va="center",
                     fontsize=8, color=TINTA_2)
    ax2.axhline(CIRCUITY_FACTOR, color=laranja, linewidth=2, zorder=2, label="fator do motor: 1,345")
    ax2.legend(loc="upper right", fontsize=8)
    ax2.set_xticks(range(len(faixas)), ["1–100", "100–500", "500–1.000", "1.000–2.000", "≥ 2.000"][: len(faixas)])
    ax2.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.1f}".replace(".", ",")))
    ax2.set(xlabel="faixa de linha reta (km)", ylabel="rota ÷ linha reta", ylim=(1.0, max(1.8, np.ceil(a["circ"].max() * 10) / 10 + 0.1)),
            xlim=(-0.5, len(faixas) - 0.3))
    ax2.grid(axis="x", visible=False)
    ax2.set_title("(b) Rota ÷ linha reta, por faixa", loc="left")

    fig.tight_layout()
    saida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(saida, dpi=200)
    print(saida)


def main(data_dir: Path = Path("data/raw")) -> None:
    pares = _com_rotas(_amostras(data_dir))
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    colunas = ["parte", "grupo", "faixa", "product_id", "origem", "destino", "hav_km", "osrm_km", "snap_m"]
    pares[colunas].to_csv(CACHE, index=False, float_format="%.3f")
    sem_rota = int(pares["osrm_km"].isna().sum())
    pares = pares.dropna(subset=["osrm_km"])
    SAIDA.write_text(_markdown(pares[pares["parte"] == "A"], pares[pares["parte"] == "B"], sem_rota), encoding="utf-8")
    print(SAIDA)
    print(json.dumps({"A": _erros(pares[pares["parte"] == "A"]), "B": _ordem(pares[pares["parte"] == "B"])},
                     indent=1, default=float))


if __name__ == "__main__":
    import sys

    grafico() if "--grafico" in sys.argv else main()
