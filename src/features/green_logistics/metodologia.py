"""Tela de metodologia (Sprint 16, V7): como selo, distancia e CO2 sao calculados.

Server-driven como as outras telas, e escrita a partir das MESMAS constantes do
motor: mudar um fator em `co2.py` muda o texto desta pagina. Texto de
metodologia copiado a mao em outro lugar e a primeira coisa a divergir do codigo.
"""

from __future__ import annotations

from urllib.parse import urlencode

from src.features.green_logistics.badge import DISTANCE_THRESHOLD_KM, RESOLUTION_FLOOR_KM
from src.features.green_logistics.co2 import (
    CIRCUITY_FACTOR,
    FE_LAST_MILE_KG_PER_T_KM,
    FE_LINE_HAUL_KG_PER_T_KM,
    FONTES,
    LAST_MILE_KM,
    VOLUMETRIC_FACTOR_CM3_PER_KG,
)
from src.features.green_logistics.delivery_options import MODES
from src.features.green_logistics.offers import TOLERANCIA_RELATIVA
from src.schemas.sdui import (
    ContentSectionBlock,
    ContentSectionProps,
    HeroBannerBlock,
    HeroBannerProps,
    NavigateAction,
    NavigatePayload,
    ScreenResponse,
)


def _n(valor: float, casas: int = 0) -> str:
    """Numero em pt-BR: milhar com ponto, decimal com virgula."""
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _secao(titulo: str, *paragrafos: str, itens: list[str] | None = None, nota: str | None = None) -> ContentSectionBlock:
    return ContentSectionBlock(
        props=ContentSectionProps(title=titulo, paragraphs=list(paragrafos), items=itens or [], note=nota)
    )


def compose_metodologia(customer_zip_prefix: str | None = None) -> ScreenResponse:
    volta = "/?" + urlencode({"customer_zip_prefix": customer_zip_prefix}) if customer_zip_prefix else "/"
    km = _n(DISTANCE_THRESHOLD_KM)
    modalidades = [
        f"{m.label}: preço × {_n(m.price_factor, 2)}, CO₂ × {_n(m.co2_factor, 1)}, prazo × {_n(m.eta_factor, 1)}."
        for m in MODES
    ]
    return ScreenResponse(
        screen_id="methodology",
        context="methodology",
        components=[
            HeroBannerBlock(
                props=HeroBannerProps(
                    title="Como calculamos",
                    subtitle=(
                        "De onde vêm a distância, o selo e o CO₂ que a loja mostra — "
                        "com as fontes e o que o modelo não captura."
                    ),
                    image_url="",
                    cta_label="Voltar à vitrine",
                ),
                actions=[NavigateAction(payload=NavigatePayload(path=volta))],
            ),
            _secao(
                "Distância",
                "Cada prefixo de CEP (5 dígitos) é representado por um ponto: a mediana das "
                "coordenadas dos endereços daquele prefixo no dataset Olist. A distância entre "
                "comprador e vendedor é a linha reta entre esses dois pontos (fórmula de Haversine).",
                f"Abaixo de {_n(RESOLUTION_FLOOR_KM)} km o modelo não distingue a distância de zero: "
                "um endereço real fica, na mediana, a meio quilômetro do ponto do seu prefixo. "
                "Por isso a loja diz \"mesma região\" em vez de afirmar \"0 km\".",
            ),
            _secao(
                "Selo de entrega local",
                f"O selo aparece quando o vendedor está a menos de {km} km do comprador. "
                "É um critério de distância, fácil de entender; a emissão aparece ao lado, em gramas "
                "ou quilos de CO₂.",
            ),
            _secao(
                "Emissão de CO₂",
                "A estimativa segue a lógica de cadeia de transporte da ISO 14083 e do GLEC Framework: "
                "distância rodoviária × massa × fator de emissão do veículo, trecho a trecho.",
                itens=[
                    f"Estrada estimada = linha reta × {_n(CIRCUITY_FACTOR, 3)} (fator de circuidade brasileiro).",
                    f"Os últimos {_n(LAST_MILE_KM)} km são de van ({_n(FE_LAST_MILE_KG_PER_T_KM, 3)} kg CO₂e por t·km); "
                    f"o resto, de caminhão pesado ({_n(FE_LINE_HAUL_KG_PER_T_KM, 3)} kg CO₂e por t·km).",
                    f"Massa considerada = o maior entre o peso real e o peso cúbico "
                    f"(volume ÷ {_n(VOLUMETRIC_FACTOR_CM3_PER_KG)} cm³ por kg): um produto leve e volumoso "
                    "ocupa o veículo como se pesasse mais.",
                ],
                nota="O botão \"Como calculamos?\" ao lado de cada selo mostra esta conta com os números daquela entrega.",
            ),
            _secao(
                "Modalidades de entrega",
                "Expressa, padrão e verde partem do frete e do prazo reais do Olist e aplicam fatores "
                "declarados. Eles são um cenário de comparação, não dados medidos.",
                itens=modalidades,
            ),
            _secao(
                "Qual vendedor entrega",
                "Quando o mesmo produto é vendido por mais de um vendedor, a loja escolhe a oferta mais "
                f"próxima de você. Entre ofertas praticamente equidistantes (até {_n(TOLERANCIA_RELATIVA * 100)}% "
                "de diferença), vence a mais barata — e o desempate nunca troca uma oferta com selo por "
                "uma sem. Vitrine, detalhe e compra usam a mesma regra.",
            ),
            _secao(
                "Vitrine da sua região",
                "Sem um perfil escolhido, a vitrine destaca a categoria que compradores da sua UF levam "
                "proporcionalmente mais do que a média do Brasil (lift). \"Ver vitrine geral\" desfaz a escolha.",
            ),
            _secao(
                "O que o modelo não captura",
                itens=[
                    "É uma estimativa comparativa: serve para comparar origens, não para inventário de emissões.",
                    "Acima de 100 km a estrada real tende a ser mais reta que o fator médio; ali a emissão fica "
                    "até ~10% superestimada.",
                    "Os fatores por veículo são da região \"Europa e América do Sul\" do GLEC, não específicos do Brasil.",
                    "Ficam fora: armazenagem, embalagem, coleta reversa e a ocupação real de cada veículo.",
                ],
            ),
            _secao("Fontes", itens=list(FONTES)),
        ],
    )
