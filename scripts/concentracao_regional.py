"""Concentracao logistica regional — o problema que a logistica verde ataca.

Tres perguntas por UF do comprador, sobre o dataset Olist COMPLETO (`data/raw/`,
nao a amostra de 10 mil):

1. **mesma UF** — % dos itens vendidos em que o vendedor estava no mesmo estado;
2. **compra local** — % dos itens em que o vendedor estava a menos de 100 km
   (o limiar do selo, `badge.DISTANCE_THRESHOLD_KM`);
3. **oferta local disponivel** — % dos compradores que tem ALGUM vendedor do
   dataset a menos de 100 km. Teto do que a recomendacao poderia fazer: quem nao
   tem vendedor perto nao tem escolha local a fazer.

    python -m scripts.concentracao_regional      # grava docs/resultados/concentracao-regional.md

Distancias em linha reta entre centroides de prefixo de CEP (mediana da
geolocalizacao), como no resto do sistema.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.etl_load_sample import build_cep_centroids, load_csvs, normalize_prefixes
from src.features.green_logistics.badge import DISTANCE_THRESHOLD_KM
from src.features.green_logistics.distance import EARTH_RADIUS_KM

SAIDA = Path("docs/resultados/concentracao-regional.md")
MIN_ITENS_UF = 1000  # abaixo disso a porcentagem por UF e ruido


def _haversine(lat1, lng1, lat2, lng2):
    """`distance.haversine_km` vetorizado (numpy, com broadcasting)."""
    lat1, lng1, lat2, lng2 = map(np.radians, (lat1, lng1, lat2, lng2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lng2 - lng1) / 2) ** 2
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))


def _tem_vendedor_perto(clientes: np.ndarray, vendedores: np.ndarray) -> np.ndarray:
    """Para cada centroide de cliente, existe vendedor a < limiar? Em blocos: 15 mil x 2 mil."""
    perto = np.zeros(len(clientes), dtype=bool)
    for i in range(0, len(clientes), 1000):
        c = clientes[i : i + 1000]
        d = _haversine(c[:, :1], c[:, 1:], vendedores[:, 0][None, :], vendedores[:, 1][None, :])
        perto[i : i + 1000] = (d < DISTANCE_THRESHOLD_KM).any(axis=1)
    return perto


def calcular(data_dir: Path = Path("data/raw")) -> tuple[pd.DataFrame, dict[str, int]]:
    frames = load_csvs(data_dir)
    normalize_prefixes(frames)
    clientes, vendedores = frames["customers"], frames["sellers"]

    itens = (
        frames["order_items"][["order_id", "seller_id"]]
        .merge(frames["orders"][["order_id", "customer_id"]], on="order_id")
        .merge(clientes[["customer_id", "customer_zip_code_prefix", "customer_state"]], on="customer_id")
        .merge(vendedores[["seller_id", "seller_zip_code_prefix", "seller_state"]], on="seller_id")
    )
    prefixos = set(clientes["customer_zip_code_prefix"].dropna()) | set(vendedores["seller_zip_code_prefix"].dropna())
    centroides = build_cep_centroids(frames["geolocation"], prefixos).set_index("zip_prefix")

    pos = centroides[["lat", "lng"]]
    c = pos.reindex(itens["customer_zip_code_prefix"]).to_numpy()
    v = pos.reindex(itens["seller_zip_code_prefix"]).to_numpy()
    itens["distancia_km"] = _haversine(c[:, 0], c[:, 1], v[:, 0], v[:, 1])
    itens["mesma_uf"] = itens["customer_state"] == itens["seller_state"]
    itens["local"] = itens["distancia_km"] < DISTANCE_THRESHOLD_KM

    # Comprador = pessoa (customer_unique_id), nao pedido; com seu CEP.
    pessoas = clientes.drop_duplicates("customer_unique_id")[["customer_zip_code_prefix", "customer_state"]]
    pref_pessoas = pessoas["customer_zip_code_prefix"].dropna().unique()
    pref_pessoas = [p for p in pref_pessoas if p in pos.index]
    sellers_xy = pos.loc[[p for p in vendedores["seller_zip_code_prefix"].dropna().unique() if p in pos.index]].to_numpy()
    perto = pd.Series(_tem_vendedor_perto(pos.loc[pref_pessoas].to_numpy(), sellers_xy), index=pref_pessoas)
    pessoas = pessoas[pessoas["customer_zip_code_prefix"].isin(perto.index)].copy()
    pessoas["oferta_local"] = pessoas["customer_zip_code_prefix"].map(perto)

    com_distancia = itens.dropna(subset=["distancia_km"])
    por_uf = (
        com_distancia.groupby("customer_state")
        .agg(itens=("order_id", "size"), mesma_uf=("mesma_uf", "mean"), local=("local", "mean"),
             distancia_mediana_km=("distancia_km", "median"))
        .join(pessoas.groupby("customer_state").agg(compradores=("oferta_local", "size"),
                                                    oferta_local=("oferta_local", "mean")))
    )
    brasil = pd.DataFrame({
        "itens": [len(com_distancia)], "mesma_uf": [com_distancia["mesma_uf"].mean()],
        "local": [com_distancia["local"].mean()],
        "distancia_mediana_km": [com_distancia["distancia_km"].median()],
        "compradores": [len(pessoas)], "oferta_local": [pessoas["oferta_local"].mean()],
    }, index=["Brasil"])
    tabela = pd.concat([brasil, por_uf.sort_values("itens", ascending=False)])
    volume = {
        "itens": len(itens), "itens_com_distancia": len(com_distancia),
        "compradores": len(pessoas), "vendedores": vendedores["seller_id"].nunique(),
    }
    return tabela, volume


def _markdown(tabela: pd.DataFrame, volume: dict[str, int]) -> str:
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    pct = lambda x: f"{x * 100:.1f}%".replace(".", ",")  # noqa: E731
    num = lambda x: f"{x:,.0f}".replace(",", ".")  # noqa: E731
    linhas = [
        "# Concentração logística regional",
        "",
        f"> Gerado por `python -m scripts.concentracao_regional` no commit `{commit}`, sobre o",
        f"> dataset Olist **completo**: {num(volume['itens'])} itens vendidos "
        f"({num(volume['itens_com_distancia'])} com centroide de CEP nas duas pontas),",
        f"> {num(volume['compradores'])} compradores (pessoas, `customer_unique_id`) e "
        f"{num(volume['vendedores'])} vendedores.",
        "",
        "- **mesma UF:** itens em que o vendedor estava no estado do comprador",
        f"- **compra local:** itens com vendedor a menos de {DISTANCE_THRESHOLD_KM:.0f} km (o limiar do selo)",
        f"- **oferta local disponível:** compradores com ALGUM vendedor do dataset a menos de "
        f"{DISTANCE_THRESHOLD_KM:.0f} km — o teto do que a recomendação poderia fazer",
        "",
        f"UFs com pelo menos {num(MIN_ITENS_UF)} itens. Distância em linha reta entre centroides de prefixo de CEP.",
        "",
        "| UF | itens | mesma UF | compra local (< 100 km) | distância mediana | compradores | oferta local disponível |",
        "|---|---|---|---|---|---|---|",
    ]
    for uf, r in tabela.iterrows():
        if uf != "Brasil" and r["itens"] < MIN_ITENS_UF:
            continue
        nome = f"**{uf}**" if uf == "Brasil" else uf
        linhas.append(
            f"| {nome} | {num(r['itens'])} | {pct(r['mesma_uf'])} | {pct(r['local'])} | "
            f"{num(r['distancia_mediana_km'])} km | {num(r['compradores'])} | {pct(r['oferta_local'])} |"
        )
    return "\n".join(linhas) + "\n"


def main() -> None:
    tabela, volume = calcular()
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(_markdown(tabela, volume), encoding="utf-8")
    print(SAIDA)
    print(tabela.head(12).to_string(float_format=lambda x: f"{x:.3f}"))


if __name__ == "__main__":
    main()
