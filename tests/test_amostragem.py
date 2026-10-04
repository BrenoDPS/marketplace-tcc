"""Amostragem: o produto sorteado entra com TODAS as suas ofertas.

A propriedade em teste nao e "a amostra tem N linhas" — e "nenhum produto da
amostra aparece com menos vendedores do que ele tem no dataset". Sortear
`order_items` por linha trazia produto pela metade, e nada no sistema
reclamaria: as telas funcionam igual, so que o caso que sustenta a tese
(mesmo item, duas origens) fica invisivel.

Medido no dataset real: 528 produtos truncados na amostra de 10 mil linhas,
474 deles multi-vendedor escondidos.
"""

from __future__ import annotations

import pandas as pd

from scripts.etl_load_sample import sample_order_items


def _universo(n_solo: int, n_multi: int, pedidos_por_solo: int = 1) -> pd.DataFrame:
    """`solo_*` tem um vendedor; `multi_*` tem dois, em pedidos diferentes."""
    linhas = []
    for i in range(n_solo):
        for k in range(pedidos_por_solo):
            linhas.append((f"ord_s{i}_{k}", 1, f"solo_{i}", "sell_a", 10.0, 1.0))
    for i in range(n_multi):
        linhas.append((f"ord_m{i}a", 1, f"multi_{i}", "sell_a", 10.0, 1.0))
        linhas.append((f"ord_m{i}b", 1, f"multi_{i}", "sell_b", 12.0, 2.0))
    return pd.DataFrame(
        linhas,
        columns=[
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "price",
            "freight_value",
        ],
    )


def test_nenhum_produto_vem_truncado():
    """O invariante central: vendedores na amostra == vendedores no universo."""
    universo = _universo(n_solo=200, n_multi=200)
    amostra = sample_order_items(universo, n=50, seed=42)

    no_universo = universo.groupby("product_id")["seller_id"].nunique()
    na_amostra = amostra.groupby("product_id")["seller_id"].nunique()

    for product_id, vendedores in na_amostra.items():
        assert vendedores == no_universo[product_id], (
            f"{product_id} entrou com {vendedores} vendedor(es), "
            f"mas tem {no_universo[product_id]} no dataset"
        )


def test_completar_revela_multi_vendedores_que_o_sorteio_escondia():
    """O ganho concreto: produto sorteado por UMA linha traz o outro vendedor.

    Com muitos produtos solo competindo pelo sorteio, e provavel que algum
    `multi_*` entre por apenas uma das suas duas linhas. Completar recupera a
    outra — e e exatamente esse par que a tese usa.
    """
    universo = _universo(n_solo=400, n_multi=100)
    amostra = sample_order_items(universo, n=60, seed=42)

    multi = amostra[amostra["product_id"].str.startswith("multi_")]
    por_produto = multi.groupby("product_id")["seller_id"].nunique()

    assert len(por_produto) > 0, "o sorteio nao pegou nenhum multi — teste inutil"
    assert (por_produto == 2).all(), "produto multi-vendedor veio pela metade"


def test_a_amostra_base_e_subconjunto_do_resultado():
    """Completar so ACRESCENTA: nao derruba linha que o sorteio escolheu.

    E o que garante que a correcao nao move os numeros ja publicados.
    """
    universo = _universo(n_solo=300, n_multi=150, pedidos_por_solo=3)
    base = universo.sample(n=100, random_state=42)
    amostra = sample_order_items(universo, n=100, seed=42)

    chaves_base = set(zip(base["order_id"], base["order_item_id"], strict=False))
    chaves_amostra = set(zip(amostra["order_id"], amostra["order_item_id"], strict=False))
    assert chaves_base <= chaves_amostra


def test_so_entram_produtos_sorteados():
    """Completar nao pode virar "carregar o dataset inteiro"."""
    universo = _universo(n_solo=500, n_multi=100)
    amostra = sample_order_items(universo, n=30, seed=42)

    assert amostra["product_id"].nunique() <= 30
    assert len(amostra) < len(universo)


def test_mesmo_seed_mesma_amostra():
    """Reprodutibilidade e requisito da metodologia (secao 3.3)."""
    universo = _universo(n_solo=300, n_multi=200)
    a = sample_order_items(universo, n=100, seed=42)
    b = sample_order_items(universo, n=100, seed=42)

    pd.testing.assert_frame_equal(a, b)


def test_seeds_diferentes_dao_amostras_diferentes():
    """Guarda do teste acima: se `seed` fosse ignorado, os dois passariam."""
    universo = _universo(n_solo=300, n_multi=200)
    a = sample_order_items(universo, n=100, seed=42)
    b = sample_order_items(universo, n=100, seed=7)

    assert set(a["product_id"]) != set(b["product_id"])


def test_nao_duplica_order_item():
    """`order_items` tem PK (order_id, order_item_id); duplicar quebra a carga."""
    universo = _universo(n_solo=100, n_multi=100)
    amostra = sample_order_items(universo, n=150, seed=42)

    chaves = list(zip(amostra["order_id"], amostra["order_item_id"], strict=False))
    assert len(chaves) == len(set(chaves))


def test_funil_registra_quanto_cada_filtro_descarta():
    """Sprint 10: a §3.3 pede o volume consolidado; o ETL descartava em silencio.

    Quatro itens, um barrado por etapa: o funil tem de contar 4 -> 3 -> 2 -> 1
    e o ultimo numero tem de ser o tamanho do `order_items` devolvido.
    """
    from scripts.etl_load_sample import filter_valid

    def dims(n):
        return {"product_length_cm": [10.0] * n, "product_height_cm": [10.0] * n, "product_width_cm": [10.0] * n}

    frames = {
        "products": pd.DataFrame({"product_id": ["ok", "sem_peso"], "product_weight_g": [100.0, 0.0], **dims(2)}),
        "geolocation": pd.DataFrame({"geolocation_zip_code_prefix": ["01000"]}),
        "customers": pd.DataFrame({"customer_id": ["c_ok", "c_sem_geo"], "customer_zip_code_prefix": ["01000", "99999"]}),
        "sellers": pd.DataFrame({"seller_id": ["s_ok", "s_sem_geo"], "seller_zip_code_prefix": ["01000", "99999"]}),
        "orders": pd.DataFrame({"order_id": ["o1", "o2", "o3", "o4"], "customer_id": ["c_ok", "c_ok", "c_ok", "c_sem_geo"]}),
    }
    itens = pd.DataFrame(
        {
            "order_id": ["o1", "o2", "o3", "o4"],
            "product_id": ["ok", "sem_peso", "ok", "ok"],
            "seller_id": ["s_ok", "s_ok", "s_sem_geo", "s_ok"],
        }
    )

    funil: list[tuple[str, int]] = []
    subset = filter_valid(frames, itens, funil)

    assert [n for _, n in funil] == [4, 3, 2, 1]
    assert funil[-1][1] == len(subset["order_items"])
