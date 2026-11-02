"""Regra de troca "Mais perto de voce" do checkout (T7, achado C4).

Decisao do grupo (02/11): o substituto pode custar no maximo 20% a mais que o
item (`MAX_PRICE_RATIO`); dentro do teto, vence a maior economia de CO2.
"""

from __future__ import annotations

from src.features.checkout.alternatives import MAX_PRICE_RATIO, best_alternative_for
from src.features.checkout.repository import AlternativeRow, CheckoutProductRow

# Caso do roteiro da banca: item de R$ 27,90 a 50 km; substituto a ~13 km por R$ 169,90.
CLIENTE = (-23.55, -46.63)
ITEM = CheckoutProductRow(
    product_id="atibaia",
    seller_id="s-atibaia",
    seller_zip_prefix="12940",
    unit_price=27.90,
    freight_value=10.0,
    weight_g=150.0,
    category="alimentos",
)


def _candidato(product_id: str, preco: float, graus_ao_norte: float) -> AlternativeRow:
    return AlternativeRow(
        product_id=product_id,
        category="alimentos",
        unit_price=preco,
        weight_g=150.0,
        seller_id=f"s-{product_id}",
        lat=CLIENTE[0] + graus_ao_norte,
        lng=CLIENTE[1],
    )


def test_substituto_muito_mais_caro_nao_e_sugerido() -> None:
    caro_perto = _candidato("caro", 169.90, 0.117)  # ~13 km, R$ 142 a mais
    barato_meio = _candidato("barato", 20.00, 0.27)  # ~30 km: mais barato, economiza menos

    best = best_alternative_for(
        ITEM, 1, 50.0, [barato_meio, caro_perto], *CLIENTE, co2_factor=1.0, exclude_product_ids=set()
    )

    assert best is not None
    assert best.product_id == "barato"
    assert round(best.distance_km) == 30
    assert best.co2_saved_kg > 0


def test_teto_de_preco_e_inclusivo_e_dentro_dele_vence_a_maior_economia() -> None:
    no_teto = _candidato("no-teto", round(ITEM.unit_price * MAX_PRICE_RATIO, 2), 0.117)
    barato_meio = _candidato("barato", 20.00, 0.27)

    best = best_alternative_for(
        ITEM, 1, 50.0, [barato_meio, no_teto], *CLIENTE, co2_factor=1.0, exclude_product_ids=set()
    )

    assert best is not None and best.product_id == "no-teto"


def test_sem_candidato_dentro_do_teto_nao_ha_sugestao() -> None:
    best = best_alternative_for(
        ITEM, 1, 50.0, [_candidato("caro", 169.90, 0.117)], *CLIENTE, co2_factor=1.0, exclude_product_ids=set()
    )

    assert best is None
