"""Derivacao de `offers` a partir de `order_items`.

O refactor das telas troca `order_items` por `offers` e so e verificavel por
diff se `build_offers` reproduzir exatamente a regra tacita de hoje: "a
primeira order_item do produto, na ordem (order_id, order_item_id)". Estes
testes prendem essa regra — sem eles, `is_default` e so um booleano qualquer.
"""

from __future__ import annotations

import pandas as pd

from scripts.etl_load_sample import build_offers


def _items(linhas: list[tuple[str, int, str, str, float, float]]) -> pd.DataFrame:
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


def test_colapsa_order_items_repetidos_numa_oferta():
    """Mesmo par (produto, vendedor) em tres pedidos = uma oferta.

    As linhas chegam FORA de ordem de proposito: `ord_a` e o menor `order_id`
    mas aparece por ultimo. Se `build_offers` pegasse a primeira linha do
    arquivo em vez de ordenar antes, o preco viria 12,00 — verificado por
    mutacao, com a entrada ordenada o teste passava mesmo sem o `sort_values`.
    """
    offers = build_offers(
        _items(
            [
                ("ord_b", 1, "prod", "sell", 12.0, 2.0),
                ("ord_c", 1, "prod", "sell", 11.0, 3.0),
                ("ord_a", 1, "prod", "sell", 10.0, 1.0),
            ]
        )
    )

    assert len(offers) == 1
    # Preco da PRIMEIRA linha por (order_id, order_item_id), nao media nem
    # ultima: e o que o detalhe e o checkout exibem hoje.
    assert offers.iloc[0]["price"] == 10.0
    assert offers.iloc[0]["freight_value"] == 1.0


def test_um_produto_com_varios_vendedores_vira_varias_ofertas():
    """O caso que o `order_items` escondia — e que sustenta a tese."""
    offers = build_offers(
        _items(
            [
                ("ord_a", 1, "prod", "sell_sp", 10.0, 1.0),
                ("ord_b", 1, "prod", "sell_ce", 14.0, 5.0),
            ]
        )
    )

    assert len(offers) == 2
    assert set(offers["seller_id"]) == {"sell_sp", "sell_ce"}


def test_exatamente_uma_oferta_default_por_produto():
    """O invariante do qual as tres telas dependem.

    Se dois `is_default` sobrassem no mesmo produto, o detalhe e o checkout
    poderiam escolher vendedores diferentes e o preco da tela pararia de bater
    com o da simulacao — sem erro nenhum, so numero divergente.
    """
    offers = build_offers(
        _items(
            [
                ("ord_b", 1, "prod_1", "sell_x", 10.0, 1.0),
                ("ord_a", 2, "prod_1", "sell_y", 20.0, 2.0),
                ("ord_a", 1, "prod_1", "sell_z", 30.0, 3.0),
                ("ord_c", 1, "prod_2", "sell_x", 40.0, 4.0),
            ]
        )
    )

    for product_id, grupo in offers.groupby("product_id"):
        assert grupo["is_default"].sum() == 1, f"{product_id} tem default ambiguo"


def test_default_e_a_primeira_order_item_do_produto():
    """Reproduz `ORDER BY order_id, order_item_id LIMIT 1` do product_detail.

    Os nomes dos vendedores sao escolhidos para que a ordem ALFABETICA seja o
    inverso da ordem por `(order_id, order_item_id)`: o default correto e
    `sell_z`, o ultimo do alfabeto. Sem isso o teste passa mesmo quebrado,
    porque `groupby` ja devolve as linhas ordenadas por `seller_id` e a
    coincidencia entre as duas ordens esconde a falha — verificado por mutacao.
    """
    offers = build_offers(
        _items(
            [
                ("ord_z", 1, "prod", "sell_m", 99.0, 9.0),
                ("ord_a", 2, "prod", "sell_a", 50.0, 5.0),
                ("ord_a", 1, "prod", "sell_z", 10.0, 1.0),
            ]
        )
    )

    default = offers[offers["is_default"]].iloc[0]
    assert default["seller_id"] == "sell_z"
    assert default["price"] == 10.0


def test_cada_produto_tem_seu_proprio_default():
    """Dois produtos, dois defaults — nao um default global.

    Em `prod_2` o default correto (`sell_z`, de `ord_a`) e o ultimo em ordem
    alfabetica, pelo mesmo motivo do teste anterior.
    """
    offers = build_offers(
        _items(
            [
                ("ord_a", 1, "prod_1", "sell_x", 10.0, 1.0),
                ("ord_a", 2, "prod_2", "sell_z", 20.0, 2.0),
                ("ord_b", 1, "prod_2", "sell_a", 30.0, 3.0),
            ]
        )
    )

    assert offers["is_default"].sum() == 2
    default_2 = offers[offers["is_default"] & (offers["product_id"] == "prod_2")]
    assert default_2.iloc[0]["seller_id"] == "sell_z"
