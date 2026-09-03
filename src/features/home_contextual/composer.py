"""Composicao da Home contextual (Sprint 2 - dados reais Olist + selo verde).

Heros sao estaticos por contexto. Os ProductCards vem do Postgres (amostra
ETL) e o `badge` e injetado pela fatia `green_logistics` (Haversine sobre
centroides de CEP). Sem mocks de product_id.
"""

from __future__ import annotations

from urllib.parse import urlencode

from sqlalchemy.ext.asyncio import AsyncSession

from src.features.green_logistics.service import (
    build_badge_for_pair,
    compute_distance_km,
)
from src.features.home_contextual.repository import (
    CategoryRow,
    ProductRow,
    category_for_context,
    fetch_products_for_home,
    list_categories,
)
from src.schemas.sdui import (
    ApiCallAction,
    ApiCallPayload,
    CategoryGridBlock,
    CategoryGridProps,
    CategoryItemProps,
    HeroBannerBlock,
    HeroBannerProps,
    NavigateAction,
    NavigatePayload,
    OpenModalAction,
    OpenModalPayload,
    ProductCardBlock,
    ProductCardProps,
    ScreenResponse,
    UIComponent,
)

CONSCIOUS_BUYER_CONTEXT = "conscious_buyer"
_DEFAULT_LIMIT = 6
_CONSCIOUS_POOL_LIMIT = 24
# 70 categorias na amostra; a grade mostra as maiores e o resto fica a um clique
# de distancia pela busca. Uma parede de 70 chips nao ajuda ninguem a navegar.
_CATEGORY_GRID_LIMIT = 12

_HEROS: dict[str, HeroBannerBlock] = {
    "electronics_expert": HeroBannerBlock(
        props=HeroBannerProps(
            title="Tech Deals",
            subtitle="Eletronicos com entrega rapida",
            image_url="https://placeholders.dev/800x400?text=Tech+Deals",
        ),
        actions=[NavigateAction(payload=NavigatePayload(path="/categories/electronics"))],
    ),
    "beauty_lover": HeroBannerBlock(
        props=HeroBannerProps(
            title="Semana da Beleza",
            subtitle="Ate 40% OFF em skincare",
            image_url="https://placeholders.dev/800x400?text=Beauty+Sale",
        ),
        actions=[NavigateAction(payload=NavigatePayload(path="/categories/beauty"))],
    ),
    CONSCIOUS_BUYER_CONTEXT: HeroBannerBlock(
        props=HeroBannerProps(
            title="Consumo consciente",
            subtitle="Entregas locais com menor impacto ambiental",
            image_url="https://placeholders.dev/800x400?text=Entregas+Locais",
        ),
        actions=[NavigateAction(payload=NavigatePayload(path="/explore"))],
    ),
}

_DEFAULT_HERO = HeroBannerBlock(
    props=HeroBannerProps(
        title="Olist Marketplace",
        subtitle="Compre de pequenos vendedores brasileiros",
        image_url="https://placeholders.dev/800x400?text=Olist",
    ),
    actions=[NavigateAction(payload=NavigatePayload(path="/explore"))],
)


def _humanize(slug: str) -> str:
    return slug.replace("_", " ").title()


def _count_label(total: int) -> str:
    if total == 0:
        return "Nenhum produto encontrado nesta amostra"
    return f"{total} produto{'s' if total > 1 else ''} nesta vitrine"


def _hero_for(
    context: str,
    search: str | None,
    category: str | None,
    found: int,
    customer_zip_prefix: str,
) -> HeroBannerBlock:
    """Busca e categoria substituem o hero do contexto: a tela precisa dizer o
    que esta filtrando, inclusive quando nao achou nada."""
    if not (search or category):
        return _HEROS.get(context, _DEFAULT_HERO)

    clear = NavigateAction(
        payload=NavigatePayload(
            path=f"/?{urlencode({'customer_zip_prefix': customer_zip_prefix, 'context': context})}"
        )
    )
    title = f"Busca: {search}" if search else _humanize(category or "")
    return HeroBannerBlock(
        props=HeroBannerProps(
            title=title,
            subtitle=_count_label(found),
            image_url="https://placeholders.dev/800x400?text=Filtro",
            cta_label="Ver tudo",
        ),
        actions=[clear],
    )


def _title_for(product_id: str, category: str | None) -> str:
    if category:
        return _humanize(category)
    return product_id


def _category_grid(
    categories: list[CategoryRow],
    customer_zip_prefix: str,
    context: str,
    selected: str | None,
) -> CategoryGridBlock:
    """O servidor monta o caminho de cada categoria ja com CEP e contexto: o
    cliente navega para onde mandaram, sem inventar query string."""

    def path_for(slug: str) -> str:
        params = urlencode(
            {
                "customer_zip_prefix": customer_zip_prefix,
                "context": context,
                "category": slug,
            }
        )
        return f"/?{params}"

    return CategoryGridBlock(
        props=CategoryGridProps(
            title="Categorias",
            categories=[
                CategoryItemProps(
                    slug=row.slug,
                    label=_humanize(row.slug),
                    product_count=row.product_count,
                    selected=row.slug == selected,
                    actions=[
                        NavigateAction(payload=NavigatePayload(path=path_for(row.slug)))
                    ],
                )
                for row in categories
            ],
        ),
    )


async def _rank_by_proximity(
    session: AsyncSession,
    products: list[ProductRow],
    customer_zip_prefix: str,
    limit: int,
) -> list[ProductRow]:
    """Ordena produtos por distancia ascendente (sem centroide vai para o fim)."""
    INFINITY = float("inf")

    async def _distance(product: ProductRow) -> float:
        distance = await compute_distance_km(
            session, customer_zip_prefix, product.seller_zip_prefix
        )
        return distance if distance is not None else INFINITY

    scored = [(await _distance(product), product) for product in products]
    scored.sort(key=lambda item: item[0])
    return [product for _, product in scored[:limit]]


def _checkout_action() -> ApiCallAction:
    return ApiCallAction(
        payload=ApiCallPayload(
            method="POST",
            path="/api/v1/checkout/simulate",
            body_key="checkout",
        )
    )


async def compose_home(
    session: AsyncSession,
    context: str,
    customer_zip_prefix: str,
    search: str | None = None,
    category: str | None = None,
) -> ScreenResponse:
    """Filtro explicito (`search`/`category`) vence a categoria do contexto.

    `conscious_buyer` continua ordenando por proximidade — agora **dentro** do
    filtro, o que da "produtos de beleza mais proximos de mim".
    """
    explicit_filter = bool(search or category)
    effective_category = category if category else category_for_context(context)

    if context == CONSCIOUS_BUYER_CONTEXT:
        pool = await fetch_products_for_home(
            session,
            category=category,
            search=search,
            limit=_CONSCIOUS_POOL_LIMIT,
        )
        products = await _rank_by_proximity(
            session, pool, customer_zip_prefix, limit=_DEFAULT_LIMIT
        )
    else:
        products = await fetch_products_for_home(
            session,
            category=effective_category,
            search=search,
            limit=_DEFAULT_LIMIT,
        )
        # Categoria vinda do contexto e uma heuristica nossa: se nao rende
        # produtos, cair para a vitrine geral (comportamento da Sprint 2). Filtro
        # que o usuario pediu nao cai — resultado vazio e a resposta honesta.
        if not products and effective_category and not explicit_filter:
            products = await fetch_products_for_home(session, limit=_DEFAULT_LIMIT)

    categories = await list_categories(session, limit=_CATEGORY_GRID_LIMIT)

    components: list[UIComponent] = [
        _hero_for(
            context,
            search,
            category,
            found=len(products),
            customer_zip_prefix=customer_zip_prefix,
        ),
        _category_grid(categories, customer_zip_prefix, context, selected=category),
    ]
    for product in products:
        _, badge = await build_badge_for_pair(
            session,
            customer_zip_prefix=customer_zip_prefix,
            seller_zip_prefix=product.seller_zip_prefix,
            weight_g=product.weight_g,
        )
        components.append(
            ProductCardBlock(
                props=ProductCardProps(
                    product_id=product.product_id,
                    price=product.price,
                    title=_title_for(product.product_id, product.category),
                    image_url=None,
                    badge=badge,
                ),
                actions=[
                    OpenModalAction(
                        payload=OpenModalPayload(
                            modal_id="product_detail",
                            title=None,
                        )
                    ),
                    _checkout_action(),
                ],
            )
        )

    return ScreenResponse(
        screen_id="home",
        context=context,
        components=components,
    )
