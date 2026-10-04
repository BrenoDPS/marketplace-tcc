"""CO2 evitado pela recomendacao "mesmo produto, vendedor mais proximo".

Sobre as COMPRAS REAIS do dataset Olist completo (`data/raw/`), sem gravar
pedido nenhum: em cada item cujo produto era vendido por mais de um vendedor,
compara o CO2 da escolha que o comprador FEZ com o da que o sistema recomenda
(o vendedor do mesmo produto mais proximo dele).

    python -m scripts.co2_evitado        # grava docs/resultados/co2-evitado.md

O que NAO entra: as modalidades `express`/`green` de `delivery_options` — seus
fatores de emissao sao cenario declarado, nao dado. Aqui so muda a ORIGEM, e o
calculo e o mesmo motor da aplicacao (`co2.calculate_co2_kg`, cadeia de
transporte da Sprint 9). O preco de cada vendedor (mediana do que ele cobrou
pelo produto) entra para mostrar o trade-off, nao para escolher.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.concentracao_regional import _haversine
from scripts.etl_load_sample import build_cep_centroids, load_csvs, normalize_prefixes
from src.features.green_logistics.co2 import calculate_co2_kg

SAIDA = Path("docs/resultados/co2-evitado.md")
_co2 = np.vectorize(calculate_co2_kg, otypes=[float])


def calcular(data_dir: Path = Path("data/raw")) -> tuple[pd.DataFrame, dict[str, float]]:
    frames = load_csvs(data_dir)
    normalize_prefixes(frames)
    produtos = frames["products"].copy()
    # Mesma conta do ETL (`filter_valid`): sem alguma dimensao, cai no peso real.
    produtos["volume_cm3"] = produtos["product_length_cm"] * produtos["product_height_cm"] * produtos["product_width_cm"]

    itens = (
        frames["order_items"][["order_id", "product_id", "seller_id", "price"]]
        .merge(frames["orders"][["order_id", "customer_id"]], on="order_id")
        .merge(frames["customers"][["customer_id", "customer_zip_code_prefix", "customer_state"]], on="customer_id")
        .merge(frames["sellers"][["seller_id", "seller_zip_code_prefix"]], on="seller_id")
        .merge(produtos[["product_id", "product_weight_g", "volume_cm3"]], on="product_id")
    )
    total_itens = len(itens)

    prefixos = set(itens["customer_zip_code_prefix"].dropna()) | set(itens["seller_zip_code_prefix"].dropna())
    pos = build_cep_centroids(frames["geolocation"], prefixos).set_index("zip_prefix")[["lat", "lng"]]

    # Ofertas: cada vendedor que vendeu o produto, com a mediana do que cobrou.
    ofertas = (
        itens.groupby(["product_id", "seller_id", "seller_zip_code_prefix"], as_index=False)["price"].median()
        .rename(columns={"seller_id": "alt_seller", "seller_zip_code_prefix": "alt_zip", "price": "alt_price"})
    )
    ofertas = ofertas[ofertas["alt_zip"].isin(pos.index)]
    multi = ofertas.groupby("product_id")["alt_seller"].transform("size") > 1
    ofertas = ofertas[multi]

    cand = itens[
        itens["product_id"].isin(ofertas["product_id"])
        & itens["customer_zip_code_prefix"].isin(pos.index)
        & itens["seller_zip_code_prefix"].isin(pos.index)
        & (itens["product_weight_g"] > 0)
    ].reset_index(drop=True)
    cand["item"] = cand.index

    # Item x cada oferta do mesmo produto: a recomendacao e a de menor distancia.
    pares = cand[["item", "product_id", "customer_zip_code_prefix"]].merge(ofertas, on="product_id")
    c = pos.reindex(pares["customer_zip_code_prefix"]).to_numpy()
    o = pos.reindex(pares["alt_zip"]).to_numpy()
    pares["dist"] = _haversine(c[:, 0], c[:, 1], o[:, 0], o[:, 1])
    rec = pares.loc[pares.groupby("item")["dist"].idxmin(), ["item", "alt_seller", "dist", "alt_price"]]
    cand = cand.merge(rec.rename(columns={"alt_seller": "rec_seller", "dist": "dist_rec", "alt_price": "preco_rec"}), on="item")

    c = pos.reindex(cand["customer_zip_code_prefix"]).to_numpy()
    s = pos.reindex(cand["seller_zip_code_prefix"]).to_numpy()
    cand["dist_real"] = _haversine(c[:, 0], c[:, 1], s[:, 0], s[:, 1])
    vol = cand["volume_cm3"].where(cand["volume_cm3"] > 0)
    cand["co2_real"] = _co2(cand["dist_real"], cand["product_weight_g"], vol.fillna(0))
    cand["co2_rec"] = _co2(cand["dist_rec"], cand["product_weight_g"], vol.fillna(0))
    cand["evitado"] = cand["co2_real"] - cand["co2_rec"]
    # Invariante: o recomendado e o MAIS PROXIMO, com o mesmo produto (mesma massa), e o
    # motor cresce com a distancia — logo nunca emite mais que a escolha real.
    assert (cand["evitado"] >= -1e-12).all(), "recomendacao emitindo mais que a escolha real"
    cand["ja_era_o_mais_proximo"] = cand["seller_id"] == cand["rec_seller"]
    preco_real = itens.groupby(["product_id", "seller_id"])["price"].median()
    cand["preco_real"] = preco_real.reindex(pd.MultiIndex.from_frame(cand[["product_id", "seller_id"]])).to_numpy()

    trocaria = cand[~cand["ja_era_o_mais_proximo"]]
    # Contexto: o CO2 de TODAS as compras medivies, para dar a escala do evitado.
    med = itens[itens["customer_zip_code_prefix"].isin(pos.index) & itens["seller_zip_code_prefix"].isin(pos.index)
                & (itens["product_weight_g"] > 0)]
    c = pos.reindex(med["customer_zip_code_prefix"]).to_numpy()
    s = pos.reindex(med["seller_zip_code_prefix"]).to_numpy()
    vol_med = med["volume_cm3"].where(med["volume_cm3"] > 0).fillna(0)
    co2_todas = _co2(_haversine(c[:, 0], c[:, 1], s[:, 0], s[:, 1]), med["product_weight_g"], vol_med).sum()
    resumo = {
        "itens_total": total_itens,
        "itens_com_alternativa": len(cand),
        "ja_mais_proximo": cand["ja_era_o_mais_proximo"].mean(),
        "co2_real_kg": cand["co2_real"].sum(),
        "co2_rec_kg": cand["co2_rec"].sum(),
        "evitado_kg": cand["evitado"].sum(),
        "co2_todas_kg": co2_todas,
        "itens_mediveis": len(med),
        "dist_real_mediana": cand["dist_real"].median(),
        "dist_rec_mediana": cand["dist_rec"].median(),
        "trocas": len(trocaria),
        "rec_mais_barata": (trocaria["preco_rec"] < trocaria["preco_real"] - 0.005).mean(),
        "rec_mesmo_preco": ((trocaria["preco_rec"] - trocaria["preco_real"]).abs() <= 0.005).mean(),
        "rec_mais_cara": (trocaria["preco_rec"] > trocaria["preco_real"] + 0.005).mean(),
        "delta_preco_mediano": (trocaria["preco_rec"] - trocaria["preco_real"]).median(),
    }
    por_uf = (
        cand.groupby("customer_state")
        .agg(itens=("item", "size"), co2_real=("co2_real", "sum"), evitado=("evitado", "sum"),
             ja_mais_proximo=("ja_era_o_mais_proximo", "mean"))
        .assign(evitado_pct=lambda d: d["evitado"] / d["co2_real"])
        .sort_values("itens", ascending=False)
    )
    return por_uf, resumo


def _markdown(por_uf: pd.DataFrame, r: dict[str, float]) -> str:
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    pct = lambda x: f"{x * 100:.1f}%".replace(".", ",")  # noqa: E731
    num = lambda x, casas=0: f"{x:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")  # noqa: E731
    evitado_pct = r["evitado_kg"] / r["co2_real_kg"]
    linhas = [
        "# CO₂ evitado pela recomendação \"mesmo produto, vendedor mais próximo\"",
        "",
        f"> Gerado por `python -m scripts.co2_evitado` no commit `{commit}`, sobre as compras reais",
        f"> do dataset Olist **completo** ({num(r['itens_total'])} itens). Motor de CO₂ da aplicação",
        "> (cadeia de transporte, Sprint 9). Sem pedido gravado: compara a escolha FEITA com a recomendada.",
        "",
        "## Resultado",
        "",
        "| | valor |",
        "|---|---|",
        f"| itens cujo produto tinha mais de um vendedor | **{num(r['itens_com_alternativa'])}** "
        f"({pct(r['itens_com_alternativa'] / r['itens_total'])} do total) |",
        f"| desses, o comprador **já** escolheu o mais próximo | {pct(r['ja_mais_proximo'])} |",
        f"| distância mediana: escolha real × recomendada | {num(r['dist_real_mediana'])} km × {num(r['dist_rec_mediana'])} km |",
        f"| CO₂ das escolhas reais | {num(r['co2_real_kg'], 1)} kg CO₂e |",
        f"| CO₂ se todos seguissem a recomendação | {num(r['co2_rec_kg'], 1)} kg CO₂e |",
        f"| **CO₂ evitado** | **{num(r['evitado_kg'], 1)} kg CO₂e ({pct(evitado_pct)})** |",
        f"| escala: CO₂ de todas as {num(r['itens_mediveis'])} compras mensuráveis do dataset | "
        f"{num(r['co2_todas_kg'], 1)} kg CO₂e — o evitado é {pct(r['evitado_kg'] / r['co2_todas_kg'])} dele |",
        "",
        f"## O trade-off de preço — nos {num(r['trocas'])} itens em que a recomendação trocaria o vendedor",
        "",
        "| a recomendada é | itens |",
        "|---|---|",
        f"| mais barata | {pct(r['rec_mais_barata'])} |",
        f"| mesmo preço (± R$ 0,01) | {pct(r['rec_mesmo_preco'])} |",
        f"| mais cara | {pct(r['rec_mais_cara'])} |",
        f"| diferença mediana (recomendada − real) | R$ {num(r['delta_preco_mediano'], 2)} |",
        "",
        "Preço de cada vendedor = mediana do que ele cobrou por aquele produto no dataset.",
        "",
        "## Por UF do comprador (UFs com pelo menos 300 itens com alternativa)",
        "",
        "| UF | itens com alternativa | já escolheu o mais próximo | CO₂ real (kg) | evitado (kg) | evitado |",
        "|---|---|---|---|---|---|",
    ]
    for uf, x in por_uf.iterrows():
        if x["itens"] < 300:
            continue
        linhas.append(f"| {uf} | {num(x['itens'])} | {pct(x['ja_mais_proximo'])} | {num(x['co2_real'], 1)} | "
                      f"{num(x['evitado'], 1)} | {pct(x['evitado_pct'])} |")
    linhas += [
        "",
        "## Limites",
        "",
        "- Só a ORIGEM muda; modalidade de entrega (cenário declarado) não entra.",
        "- \"Vendedor do produto\" = quem o vendeu ao menos uma vez em 2016–2018; disponibilidade "
        "na data da compra não é conhecida.",
        "- Distância em linha reta entre centroides de prefixo de CEP, convertida em estrada pelo motor.",
    ]
    return "\n".join(linhas) + "\n"


def main() -> None:
    por_uf, resumo = calcular()
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(_markdown(por_uf, resumo), encoding="utf-8")
    print(SAIDA)
    for k, v in resumo.items():
        print(f"  {k:22} {v:,.4f}" if isinstance(v, float) else f"  {k:22} {v}")


if __name__ == "__main__":
    main()
