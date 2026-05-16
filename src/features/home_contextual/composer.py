"""Composicao da Home contextual (Fase 1 - mock).

Os `SustainabilityProps` aqui sao mockados — a logica real (PostGIS, distancia
CEP, calculo de CO2) entra na fatia `green_logistics` na Fase 2.
"""

from src.schemas.sdui import (
    HeroBannerBlock,
    HeroBannerProps,
    NavigateAction,
    NavigatePayload,
    OpenModalAction,
    OpenModalPayload,
    ProductCardBlock,
    ProductCardProps,
    ScreenResponse,
    SustainabilityProps,
    UIComponent,
)

# TODO[green_logistics]: substituir por calculo real de distancia/CO2 na Fase 2.
_MOCK_GREEN_BADGE = SustainabilityProps(
    label="Entrega Local",
    impact_level="green",
    icon="leaf",
)

_ELECTRONICS_COMPONENTS: list[UIComponent] = [
    HeroBannerBlock(
        props=HeroBannerProps(
            title="Tech Deals",
            subtitle="Eletronicos com entrega rapida",
            image_url="https://placeholders.dev/800x400?text=Tech+Deals",
        ),
        actions=[
            NavigateAction(payload=NavigatePayload(path="/categories/electronics")),
        ],
    ),
    ProductCardBlock(
        props=ProductCardProps(
            product_id="prod_001",
            price=199.90,
            title="Fone Bluetooth",
            image_url="https://placeholders.dev/300x300?text=Fone",
            badge=_MOCK_GREEN_BADGE,
        ),
        actions=[
            OpenModalAction(payload=OpenModalPayload(modal_id="product_detail")),
        ],
    ),
    ProductCardBlock(
        props=ProductCardProps(
            product_id="prod_002",
            price=89.50,
            title="Cabo USB-C",
            image_url="https://placeholders.dev/300x300?text=Cabo",
            badge=_MOCK_GREEN_BADGE,
        ),
    ),
]

_BEAUTY_COMPONENTS: list[UIComponent] = [
    HeroBannerBlock(
        props=HeroBannerProps(
            title="Semana da Beleza",
            subtitle="Ate 40% OFF em skincare",
            image_url="https://placeholders.dev/800x400?text=Beauty+Sale",
        ),
        actions=[
            NavigateAction(payload=NavigatePayload(path="/categories/beauty")),
        ],
    ),
    ProductCardBlock(
        props=ProductCardProps(
            product_id="prod_100",
            price=49.90,
            title="Hidratante Facial",
            image_url="https://placeholders.dev/300x300?text=Skincare",
            badge=_MOCK_GREEN_BADGE,
        ),
    ),
]

_DEFAULT_COMPONENTS: list[UIComponent] = [
    HeroBannerBlock(
        props=HeroBannerProps(
            title="Olist Marketplace",
            subtitle="Compre de pequenos vendedores brasileiros",
            image_url="https://placeholders.dev/800x400?text=Olist",
        ),
        actions=[
            NavigateAction(payload=NavigatePayload(path="/explore")),
        ],
    ),
    ProductCardBlock(
        props=ProductCardProps(
            product_id="prod_050",
            price=29.99,
            title="Produto em Destaque",
            badge=_MOCK_GREEN_BADGE,
        ),
    ),
]

_CONTEXT_MAP: dict[str, list[UIComponent]] = {
    "electronics_expert": _ELECTRONICS_COMPONENTS,
    "beauty_lover": _BEAUTY_COMPONENTS,
}


async def compose_home(context: str) -> ScreenResponse:
    components = _CONTEXT_MAP.get(context, _DEFAULT_COMPONENTS)
    return ScreenResponse(
        screen_id="home",
        context=context,
        components=components,
    )
