"""Regra de troca "Mais perto de voce" do checkout (T7, achado C4).

Fixa o comportamento ATUAL: o preco nao entra na escolha do substituto — vence
a maior economia de CO2, mesmo muito mais cara, e o preco so e exibido.
DECISAO PENDENTE do grupo (card [Decisao] no Trello; analise-app-x-monografia
C4/D5): se houver teto de preco, este teste muda junto com
`src/features/checkout/alternatives.py`.
"""

from __future__ import annotations

from src.features.checkout.alternatives import best_alternative_for
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


def test_substituto_mais_caro_vence_se_economiza_mais_co2() -> None:
    caro_perto = _candidato("caro", 169.90, 0.117)  # ~13 km
    barato_meio = _candidato("barato", 20.00, 0.27)  # ~30 km: mais barato, economiza menos

    best = best_alternative_for(
        ITEM, 1, 50.0, [barato_meio, caro_perto], *CLIENTE, co2_factor=1.0, exclude_product_ids=set()
    )

    assert best is not None
    assert best.product_id == "caro"
    assert round(best.distance_km) == 13
    assert best.co2_saved_kg > 0
    # Sem teto: R$ 142 a mais e aceito, e o preco vai para a tela.
    assert best.price == 169.90
    assert best.price - ITEM.unit_price > 140
