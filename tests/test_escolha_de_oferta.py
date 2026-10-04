"""A regra comum de escolha de oferta (Sprint 10): mais proxima, desempate por preco.

Ofertas sao `(nome, preco)`; a regra so ve distancia e preco.
"""

from __future__ import annotations

from src.features.green_logistics.offers import escolher_oferta

INF = float("inf")


def _escolha(*medidas: tuple[float, tuple[str, float]]) -> str:
    return escolher_oferta(list(medidas), lambda o: o[1])[1][0]


def test_equidistantes_vence_a_mais_barata():
    """O caso que abriu o card: Sarandi e Maringa, ambos a ~2.620 km de 60165,
    R$ 299,90 contra R$ 199,90. A escolha era decidida na casa decimal."""
    assert _escolha((2620.0, ("sarandi", 299.90)), (2620.4, ("maringa", 199.90))) == "maringa"


def test_fora_da_tolerancia_vale_a_distancia_mesmo_mais_cara():
    # 4% mais longe: a diferenca de CO2 ja nao e desprezivel.
    assert _escolha((500.0, ("perto", 300.0)), (520.0, ("longe", 100.0))) == "perto"


def test_tolerancia_e_relativa_a_distancia():
    # 1% de 2.000 km = 20 km.
    assert _escolha((2000.0, ("a", 300.0)), (2019.0, ("b", 100.0))) == "b"
    assert _escolha((2000.0, ("a", 300.0)), (2021.0, ("b", 100.0))) == "a"


def test_perto_o_piso_e_a_resolucao_do_modelo():
    # 1% de 10 km seria 100 m — abaixo do que centroides de CEP resolvem.
    assert _escolha((10.0, ("a", 300.0)), (10.8, ("b", 100.0))) == "b"


def test_desempate_nunca_custa_o_selo():
    # 100,4 km esta dentro do piso de 1 km, mas perde o selo (< 100 km).
    assert _escolha((99.5, ("com_selo", 300.0)), (100.4, ("sem_selo", 100.0))) == "com_selo"


def test_mesmo_preco_vale_a_mais_proxima_e_depois_a_ordem():
    assert _escolha((50.3, ("a", 100.0)), (50.0, ("b", 100.0))) == "b"
    assert _escolha((50.0, ("a", 100.0)), (50.0, ("b", 100.0))) == "a"


def test_distancia_conhecida_vence_a_desconhecida():
    assert _escolha((INF, ("sem_centroide", 10.0)), (3000.0, ("medida", 500.0))) == "medida"


def test_sem_distancia_nenhuma_vale_a_mais_barata():
    assert _escolha((INF, ("a", 300.0)), (INF, ("b", 100.0))) == "b"


def test_devolve_o_proprio_item_da_lista():
    """O detalhe separa as descartadas por identidade."""
    medidas = [(10.0, ("a", 1.0)), (900.0, ("b", 1.0))]
    assert escolher_oferta(medidas, lambda o: o[1]) is medidas[0]
