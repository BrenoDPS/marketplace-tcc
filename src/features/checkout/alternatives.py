"""Sugestao de troca por vendedor mais proximo (Sprint 6).

O `co2_share` da Sprint 5 DIAGNOSTICA qual remessa domina a pegada. Este modulo
transforma o diagnostico em acao: para os itens da remessa mais poluente,
procura na mesma categoria um produto de vendedor mais perto e calcula quanto
de CO2 a troca economizaria.

HONESTIDADE DOS DADOS — ler antes de citar isto no TCC:

Nao e "o mesmo produto em outro vendedor". O Olist nao tem catalogo
compartilhado entre sellers: cada `product_id` pertence a um vendedor. O mais
proximo que da para afirmar com este dataset e "outro produto da MESMA
CATEGORIA, de um vendedor mais perto de voce". Por isso a sugestao mostra
preco e distancia do substituto — a troca nao e equivalente, e quem decide e o
usuario.

A economia e real e vem so de dados reais: distancia (Haversine sobre
centroides de CEP), massa cobravel (`max` entre `product_weight_g` e o peso
cubado das dimensoes, ver `co2.chargeable_weight_g`) e o FE do GHG Protocol.
Nenhum coeficiente arbitrado entra aqui.
"""

from __future__ import annotations

from src.features.checkout.repository import AlternativeRow, CheckoutProductRow
from src.features.green_logistics.co2 import calculate_co2_kg
from src.features.green_logistics.distance import haversine_km
from src.schemas.sdui import AlternativeProps

# Uma sugestao por item da remessa: mais que isso vira parede de opcoes numa
# tela que ja tem resumo, modalidades e remessas.
MAX_SUGGESTIONS = 3


def _co2(
    distance_km: float,
    weight_g: float | None,
    quantity: int,
    factor: float,
    volume_cm3: float | None = None,
) -> float:
    volume = volume_cm3 * quantity if volume_cm3 else None
    return calculate_co2_kg(distance_km, (weight_g or 0.0) * quantity, volume) * factor


def best_alternative_for(
    product: CheckoutProductRow,
    quantity: int,
    current_distance_km: float,
    candidates: list[AlternativeRow],
    customer_lat: float,
    customer_lng: float,
    co2_factor: float,
    exclude_product_ids: set[str],
) -> AlternativeProps | None:
    """Melhor substituto para UM item, ou None se nenhum reduz a emissao.

    "Melhor" = maior economia de CO2, nao menor distancia: um vendedor mais
    perto com produto mais pesado pode emitir mais. Distancia e massa entram
    juntas porque e assim que a emissao se comporta.
    """
    current = _co2(
        current_distance_km, product.weight_g, quantity, co2_factor, product.volume_cm3
    )

    best: AlternativeProps | None = None
    for row in candidates:
        if row.category != product.category:
            continue
        if row.product_id in exclude_product_ids:
            continue

        distance = haversine_km(customer_lat, customer_lng, row.lat, row.lng)
        if distance >= current_distance_km:
            continue

        emission = _co2(
            distance, row.weight_g, quantity, co2_factor, row.volume_cm3
        )
        saved = current - emission
        if saved <= 0:
            continue

        if best is None or saved > best.co2_saved_kg:
            best = AlternativeProps(
                product_id=row.product_id,
                title=_title_for(row),
                price=row.unit_price,
                seller_id=row.seller_id,
                distance_km=distance,
                co2_kg=emission,
                replaces_product_id=product.product_id,
                co2_saved_kg=saved,
                saved_share=saved / current if current else 0.0,
            )
    return best


def _title_for(row: AlternativeRow) -> str:
    if row.category:
        return row.category.replace("_", " ").title()
    return row.product_id


def build_alternatives(
    group: list[tuple[CheckoutProductRow, int]],
    current_distance_km: float,
    candidates: list[AlternativeRow],
    customer_lat: float,
    customer_lng: float,
    co2_factor: float,
    cart_product_ids: set[str],
) -> list[AlternativeProps]:
    """Uma sugestao por item da remessa, da maior economia para a menor."""
    taken = set(cart_product_ids)
    out: list[AlternativeProps] = []
    for product, quantity in group:
        best = best_alternative_for(
            product,
            quantity,
            current_distance_km,
            candidates,
            customer_lat,
            customer_lng,
            co2_factor,
            exclude_product_ids=taken,
        )
        if best is not None:
            # Nao sugerir o mesmo substituto duas vezes na mesma tela.
            taken.add(best.product_id)
            out.append(best)

    out.sort(key=lambda a: a.co2_saved_kg, reverse=True)
    return out[:MAX_SUGGESTIONS]
