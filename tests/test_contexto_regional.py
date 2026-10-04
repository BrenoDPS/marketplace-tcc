"""ETL do contexto regional (Sprint 9): UF por prefixo e categoria por UF.

O que esta em teste sao as duas escolhas que a banca pode questionar: a
categoria e a de maior LIFT (nao a mais vendida, que seria igual em todo lugar),
e UF sem volume ou sem desvio relevante fica SEM personalizacao.
"""

from __future__ import annotations

import pandas as pd

from scripts import etl_load_sample as etl
from scripts.etl_load_sample import build_cep_centroids, build_regional_categories


def test_uf_do_prefixo_e_a_mais_frequente():
    geo = pd.DataFrame(
        {
            "geolocation_zip_code_prefix": ["01000", "01000", "01000", "02000", "02000"],
            "geolocation_lat": [-23.5] * 5,
            "geolocation_lng": [-46.6] * 5,
            # 02000: empate 1 x 1 desempata pela sigla, para ser estavel.
            "geolocation_state": ["SP", "SP", "MG", "SP", "MG"],
        }
    )
    uf = build_cep_centroids(geo, {"01000", "02000"}).set_index("zip_prefix")["uf"]

    assert uf["01000"] == "SP"
    assert uf["02000"] == "MG"


def _frames(linhas: list[tuple[str, str, int]]) -> dict[str, pd.DataFrame]:
    """(uf, categoria, n_itens) -> as quatro tabelas que a funcao junta."""
    itens, pedidos, clientes, produtos = [], [], [], []
    for uf, cat, n in linhas:
        for i in range(n):
            oid, cid, pid = f"o_{uf}_{cat}_{i}", f"c_{uf}_{cat}_{i}", f"p_{cat}"
            itens.append((oid, pid))
            pedidos.append((oid, cid))
            clientes.append((cid, uf))
        produtos.append((f"p_{cat}", cat))
    return {
        "order_items": pd.DataFrame(itens, columns=["order_id", "product_id"]),
        "orders": pd.DataFrame(pedidos, columns=["order_id", "customer_id"]),
        "customers": pd.DataFrame(clientes, columns=["customer_id", "customer_state"]),
        "products": pd.DataFrame(produtos, columns=["product_id", "product_category_name"]).drop_duplicates(),
    }


def test_escolhe_maior_lift_e_respeita_os_limiares(monkeypatch):
    monkeypatch.setattr(etl, "MIN_ITENS_UF", 100)
    monkeypatch.setattr(etl, "MIN_ITENS_CATEGORIA_UF", 10)
    frames = _frames(
        [
            # CE: cama e a mais vendida, mas relogios e o que CE compra ACIMA do Brasil.
            ("CE", "cama", 60), ("CE", "relogios", 40),
            ("SP", "cama", 900), ("SP", "relogios", 100),
            # AC: desvio enorme, mas so 50 itens — ruido.
            ("AC", "relogios", 50),
            # RJ: volume suficiente e nenhuma categoria 1,2x acima do Brasil.
            ("RJ", "cama", 85), ("RJ", "relogios", 15),
        ]
    )

    regional = build_regional_categories(frames, {"cama", "relogios"}).set_index("uf")

    assert regional.loc["CE", "category"] == "relogios"
    assert regional.loc["CE", "lift"] > 2
    assert "AC" not in regional.index, "UF abaixo de MIN_ITENS_UF"
    assert "RJ" not in regional.index, "sem categoria acima de MIN_LIFT"
    assert "SP" not in regional.index


def test_so_concorre_categoria_que_existe_na_amostra(monkeypatch):
    """Recomendar categoria sem produto na vitrine e anunciar o que nao existe."""
    monkeypatch.setattr(etl, "MIN_ITENS_UF", 100)
    monkeypatch.setattr(etl, "MIN_ITENS_CATEGORIA_UF", 10)
    frames = _frames([("CE", "cama", 60), ("CE", "relogios", 40), ("SP", "cama", 900), ("SP", "relogios", 100)])

    assert build_regional_categories(frames, {"cama"}).empty
