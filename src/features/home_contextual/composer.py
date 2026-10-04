"""Composicao da Home contextual (Sprint 2 - dados reais Olist + selo verde).

Heros sao estaticos por contexto. Os ProductCards vem do Postgres (amostra
ETL) e o `badge` e injetado pela fatia `green_logistics` (Haversine sobre
centroides de CEP). Sem mocks de product_id.
"""

from __future__ import annotations

from urllib.parse import urlencode

from sqlalchemy.ext.asyncio import AsyncSession

from src.features.green_logistics.offers import escolher_oferta
from src.features.green_logistics.service import (
    build_badge_for_pair,
    compute_distance_km,
)
from src.features.home_contextual.repository import (
    CategoryRow,
    ProductRow,
    RegionalPick,
    category_for_context,
    fetch_products_for_home,
    list_categories,
    regional_pick,
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
    ProductCardBlock,
    ProductCardProps,
    ScreenResponse,
    UIComponent,
)

CONSCIOUS_BUYER_CONTEXT = "conscious_buyer"
# Sem contexto escolhido, o contexto vem do CEP (Sprint 9). Qualquer outro valor
# do query param e escolha explicita e vence a derivacao.
DEFAULT_CONTEXT = "default"
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


def _regional_hero(pick: RegionalPick, customer_zip_prefix: str) -> HeroBannerBlock:
    """Diz POR QUE a vitrine mostra esta categoria: personalizacao que o
    comprador nao consegue explicar parece arbitraria."""
    path = "/?" + urlencode(
        {
            "customer_zip_prefix": customer_zip_prefix,
            "context": DEFAULT_CONTEXT,
            "category": pick.category,
        }
    )
    vezes = f"{pick.lift:.1f}".replace(".", ",")
    return HeroBannerBlock(
        props=HeroBannerProps(
            title=f"Em alta em {pick.uf}: {_humanize(pick.category)}",
            subtitle=f"Compradores de {pick.uf} levam {vezes}x mais desta categoria que a media do Brasil",
            image_url="https://placeholders.dev/800x400?text=Em+alta+na+regiao",
            cta_label="Ver a categoria",
        ),
        actions=[NavigateAction(payload=NavigatePayload(path=path))],
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


INFINITY = float("inf")


async def _nearest_offer_per_product(
    session: AsyncSession,
    offers: list[ProductRow],
    customer_zip_prefix: str,
) -> list[tuple[float, ProductRow]]:
    """Colapsa as ofertas em uma por produto: a mais perto do comprador,
    desempatada por preco (`green_logistics.offers.escolher_oferta`).

    E o ponto da feature. O mesmo item vendido de Recife e de Maringa sao duas
    origens a 2483 km uma da outra, e so uma delas ganha selo verde para quem
    mora perto — escolher a errada seria anunciar impacto maior do que o
    necessario, numa tela cujo assunto e justamente impacto.

    Custa zero consulta: os centroides vivem em memoria desde a Sprint 6, entao
    medir todas as ofertas de um produto e aritmetica em `dict`.

    Devolve `(distancia, oferta)` porque quem chama ja precisa da distancia para
    ordenar — sem isso o `conscious_buyer` mediria tudo duas vezes.
    """
    por_produto: dict[str, list[tuple[float, ProductRow]]] = {}
    for offer in offers:
        distance = await compute_distance_km(
            session, customer_zip_prefix, offer.seller_zip_prefix
        )
        if distance is None:
            # Vendedor sem centroide nao e descartado: o produto ainda existe e
            # tem preco. Fica por ultimo e sem selo, que e a resposta honesta —
            # "nao sei a distancia" nao e "a distancia e grande".
            distance = INFINITY
        por_produto.setdefault(offer.product_id, []).append((distance, offer))

    # `dict` preserva ordem de insercao: os produtos saem na ordem em que a
    # consulta os trouxe.
    return [escolher_oferta(medidas, lambda o: o.price) for medidas in por_produto.values()]


def _checkout_action() -> ApiCallAction:
    return ApiCallAction(
        payload=ApiCallPayload(
            method="POST",
            path="/api/v1/checkout/simulate",
            body_key="checkout",
        )
    )


def _detail_action(product_id: str, customer_zip_prefix: str) -> ApiCallAction:
    """Abre o detalhe buscando OUTRA tela no servidor.

    Antes era um `open_modal` e o cliente remontava o detalhe com os props do
    proprio card — a unica tela que o cliente montava sozinho. O caminho ja vem
    com o CEP porque a distancia e o selo dependem dele; o cliente nao monta
    query string.
    """
    params = urlencode({"customer_zip_prefix": customer_zip_prefix})
    return ApiCallAction(
        payload=ApiCallPayload(
            method="GET",
            path=f"/api/v1/products/{product_id}?{params}",
            body_key=None,
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

    Sem contexto escolhido (`default`) e sem filtro, a categoria vem da UF do
    CEP (Sprint 9, `regional_pick`); o query param e o override.
    """
    explicit_filter = bool(search or category)
    effective_category = category if category else category_for_context(context)
    # Contexto derivado do CEP: so quando ninguem escolheu nada — nem contexto
    # (override pelo query param) nem filtro.
    regional = None
    if context == DEFAULT_CONTEXT and not explicit_filter:
        regional = await regional_pick(session, customer_zip_prefix)
        if regional is not None:
            effective_category = regional.category

    if context == CONSCIOUS_BUYER_CONTEXT:
        pool = await fetch_products_for_home(
            session,
            category=category,
            search=search,
            limit=_CONSCIOUS_POOL_LIMIT,
        )
        escolhidas = await _nearest_offer_per_product(
            session, pool, customer_zip_prefix
        )
        # Cada produto ja entra com a sua MELHOR origem; a ordenacao aqui e
        # entre produtos. Antes o ranking usava o vendedor arbitrario do
        # produto, entao um item podia cair no fim da lista por causa de uma
        # origem distante enquanto tinha outra ao lado do comprador.
        escolhidas.sort(key=lambda par: par[0])
        products = [offer for _, offer in escolhidas[:_DEFAULT_LIMIT]]
    else:
        offers = await fetch_products_for_home(
            session,
            category=effective_category,
            search=search,
            limit=_DEFAULT_LIMIT,
        )
        # Categoria vinda do contexto e uma heuristica nossa: se nao rende
        # produtos, cair para a vitrine geral (comportamento da Sprint 2). Filtro
        # que o usuario pediu nao cai — resultado vazio e a resposta honesta.
        if not offers and effective_category and not explicit_filter:
            offers = await fetch_products_for_home(session, limit=_DEFAULT_LIMIT)
            # O hero regional anunciaria uma categoria que nao esta na tela.
            regional = None
        products = [
            offer
            for _, offer in await _nearest_offer_per_product(
                session, offers, customer_zip_prefix
            )
        ]

    categories = await list_categories(session, limit=_CATEGORY_GRID_LIMIT)

    components: list[UIComponent] = [
        _regional_hero(regional, customer_zip_prefix)
        if regional is not None
        else _hero_for(
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
            volume_cm3=product.volume_cm3,
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
                    _detail_action(product.product_id, customer_zip_prefix),
                    _checkout_action(),
                ],
            )
        )

    return ScreenResponse(
        screen_id="home",
        context=context,
        components=components,
    )
