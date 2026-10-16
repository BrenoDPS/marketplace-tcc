"""Contrato SDUI (Server-Driven UI) — Fase 1.

Implementa o envelope `{ type, version, props, actions }` definido em
docs/tech_spec.md §2. Mantém uma unica `ScreenResponse`.
"""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Acoes (comportamento definido pelo servidor)
# ---------------------------------------------------------------------------

class NavigatePayload(BaseModel):
    path: str
    replace: bool = False


class ApiCallPayload(BaseModel):
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
    path: str
    body_key: str | None = None


class OpenModalPayload(BaseModel):
    modal_id: str
    title: str | None = None


class NavigateAction(BaseModel):
    type: Literal["navigate"] = "navigate"
    payload: NavigatePayload


class ApiCallAction(BaseModel):
    type: Literal["api_call"] = "api_call"
    payload: ApiCallPayload


class OpenModalAction(BaseModel):
    type: Literal["open_modal"] = "open_modal"
    payload: OpenModalPayload


UIAction = Annotated[
    Union[NavigateAction, ApiCallAction, OpenModalAction],
    Field(discriminator="type"),
]


# ---------------------------------------------------------------------------
# Props (apresentacao / dados para renderizar)
# ---------------------------------------------------------------------------

class Co2ExplanationProps(BaseModel):
    """A conta por tras do numero do selo, passo a passo (Sprint 15, V2).
    Vem pronta do servidor: o cliente formata, nao recalcula."""

    straight_km: float
    circuity: float
    road_km: float
    line_haul_km: float  # trecho de caminhao
    last_mile_km: float  # trecho de van
    weight_g: float
    chargeable_weight_g: float  # max(real, cubado)
    fe_line_haul: float  # kg CO2e por t.km
    fe_last_mile: float
    mode_factor: float = 1.0  # modalidade de entrega (checkout); 1 = padrao
    co2_kg: float
    sources: list[str] = Field(default_factory=list)


class SustainabilityProps(BaseModel):
    label: str
    impact_level: Literal["green", "neutral"] = "green"
    icon: str | None = None
    # Opcional: so as telas que mostram o explicador pedem (detalhe, checkout);
    # os cards da vitrine nao carregam o peso de 6 explicacoes que nao exibem.
    explanation: Co2ExplanationProps | None = None


class ProductCardProps(BaseModel):
    product_id: str
    price: float
    title: str | None = None
    image_url: str | None = None
    badge: SustainabilityProps | None = None
    # Origem e impacto em TODO card, nao so no que ganhou selo: sem isso a
    # vitrine so dizia de onde vinha o que estava perto (Sprint 13, D2).
    seller_city: str | None = None
    seller_state: str | None = None
    # Mesma convencao do `impact_banner`: abaixo do piso de resolucao (mesma
    # regiao) os dois vem nulos e o selo fala por eles.
    distance_km: float | None = None
    co2_kg: float | None = None


class HeroBannerProps(BaseModel):
    title: str
    subtitle: str | None = None
    image_url: str
    # Rotulo do botao da primeira `action`. Sem isso o texto fica cravado no
    # cliente e um hero de "limpar filtro" acaba com o botao escrito "Explorar".
    cta_label: str | None = None
    # Rotulo do botao da SEGUNDA `action` (Sprint 14). O hero regional usa para
    # desfazer a personalizacao: "Ver vitrine geral".
    secondary_cta_label: str | None = None


class ProductDetailProps(BaseModel):
    """Detalhe do produto.

    O prototipo do TCC1 mostrava descricao, tags de sustentabilidade e nota.
    Aqui so entram campos que EXISTEM na amostra:

    - `rating`/`review_count`: reais, de `olist_order_reviews`. A nota no Olist
      e do pedido, nao do item; atribui-la ao produto e aproximacao, mas o
      numero nao e inventado. Sem pedido avaliado, vem nulo.
    - `seller_city`/`seller_state`: reais, de `olist_sellers`.
    - FORA: descricao e tags do tipo "algodao organico". O Olist tem apenas o
      COMPRIMENTO da descricao (`product_description_lenght`), nao o texto, e
      nao tem nenhuma tag de sustentabilidade. Preencher isso seria inventar
      dado numa tela cujo assunto e justamente credibilidade ambiental.
    """

    product_id: str
    title: str | None = None
    price: float
    image_url: str | None = None
    category: str | None = None
    weight_g: float | None = None
    seller_id: str
    seller_city: str | None = None
    seller_state: str | None = None
    rating: float | None = None
    review_count: int = 0
    badge: SustainabilityProps | None = None


class CartLineProps(BaseModel):
    product_id: str
    title: str | None = None
    quantity: int
    unit_price: float
    line_total: float


class CheckoutSummaryProps(BaseModel):
    items: list[CartLineProps]
    subtotal: float
    freight: float
    total: float


class AlternativeProps(BaseModel):
    """Produto da MESMA CATEGORIA num vendedor mais proximo.

    Nao e "o mesmo produto em outro vendedor": o Olist nao tem catalogo
    compartilhado entre sellers, entao o mais proximo que da para afirmar e
    "outro produto da mesma categoria". `replaces_product_id` amarra a
    sugestao ao item do carrinho, para a troca ter semantica definida.
    """

    product_id: str
    title: str | None = None
    price: float
    seller_id: str
    distance_km: float
    co2_kg: float
    replaces_product_id: str
    co2_saved_kg: float
    saved_share: float
    actions: list[UIAction] = Field(default_factory=list)


class ShipmentProps(BaseModel):
    """Uma remessa = um vendedor. Itens do mesmo vendedor saem juntos.

    `alternatives` so vem preenchida na remessa de maior emissao: sugerir
    troca nas outras seria ruido, porque mexer nelas quase nao move a pegada.
    """

    seller_id: str
    product_ids: list[str]
    total_quantity: int
    weight_g: float | None = None
    distance_km: float | None = None
    freight: float
    co2_kg: float | None = None
    # Fatia do CO2 total do carrinho (0..1). E o numero que revela qual
    # vendedor domina a pegada — a leitura util do carrinho multi-item.
    co2_share: float | None = None
    badge: SustainabilityProps | None = None
    alternatives: list[AlternativeProps] = Field(default_factory=list)


class ShipmentBreakdownProps(BaseModel):
    """`shipments` vem ordenada por emissao DECRESCENTE — a remessa que mais
    pesa na pegada aparece primeiro, que e onde o usuario pode agir."""

    title: str | None = None
    shipments: list[ShipmentProps]
    note: str | None = None


class CategoryItemProps(BaseModel):
    """Item da grade de categorias.

    Carrega a propria `actions` porque cada categoria navega para um caminho
    diferente — o envelope do bloco so comporta uma acao para o conjunto.
    """

    slug: str
    label: str
    product_count: int
    selected: bool = False
    actions: list[UIAction] = Field(default_factory=list)


class SortOptionProps(BaseModel):
    """Uma ordenacao da vitrine (Sprint 15, V4). Mesmo desenho do item de
    categoria: rotulo, se esta em vigor e a `navigate` que a aplica."""

    value: str
    label: str
    selected: bool = False
    actions: list[UIAction] = Field(default_factory=list)


class CategoryGridProps(BaseModel):
    title: str | None = None
    categories: list[CategoryItemProps]
    # Ordenar e filtrar moram juntos: e a barra de controle da vitrine.
    sort_options: list[SortOptionProps] = Field(default_factory=list)


class DeliveryOptionProps(BaseModel):
    id: str
    label: str
    description: str | None = None
    eta_days: int
    price: float
    co2_kg: float | None = None
    recommended: bool = False
    selected: bool = False


class DeliveryOptionsProps(BaseModel):
    """Comparativo de modalidades.

    Na Sprint 4 este bloco devolvia `product_id`/`quantity` porque o cliente
    nao guardava estado de checkout. Com o carrinho da Sprint 5 ele guarda — um
    carrinho e estado do cliente por natureza — entao o eco saiu daqui.
    """

    distance_km: float | None = None
    selected_id: str
    options: list[DeliveryOptionProps]
    note: str | None = None


class OfferOptionProps(BaseModel):
    """Uma origem do MESMO produto. Distancia e CO2 nulos = desconhecida ou
    abaixo do piso de resolucao (mesma regiao) — a regra do `impact_banner`."""

    seller_id: str
    seller_city: str | None = None
    seller_state: str | None = None
    price: float
    distance_km: float | None = None
    co2_kg: float | None = None
    # Mesma regiao (< piso de resolucao): o numero existe mas seria ruido.
    same_region: bool = False
    local: bool = False  # ganharia o selo (< 100 km)
    chosen: bool = False
    # So na escolhida: POR QUE ela (a regra de `escolher_oferta`, em texto).
    reason: str | None = None


class OfferComparisonProps(BaseModel):
    """Todas as origens do produto, da mais proxima para a mais distante
    (Sprint 15, V1). E o argumento da tese em tela: mesmo produto, origem
    mais perto, emite menos — e quanto custa a diferenca."""

    title: str
    offers: list[OfferOptionProps]
    note: str | None = None


class MapPointProps(BaseModel):
    """Ponto ja projetado nas coordenadas do SVG (`green_logistics.mapa`):
    o cliente desenha, nao faz conta geografica."""

    x: float
    y: float
    label: str
    chosen: bool = False
    local: bool = False


class OriginMapProps(BaseModel):
    """Mapa de origem (Sprint 15, V3): comprador, origens do produto e o raio
    de 100 km do selo, sobre o Brasil desenhado pelos CEPs do dataset."""

    title: str = "De onde sai"
    viewbox: str  # recorte que enquadra os pontos
    width: float  # tamanho do mapa inteiro, para posicionar o fundo
    height: float
    background_url: str | None = None
    buyer: MapPointProps
    origins: list[MapPointProps]
    radius_100km: float
    caption: str | None = None


class ImpactBannerProps(BaseModel):
    distance_km: float | None = None
    co2_kg: float | None = None
    badge: SustainabilityProps | None = None
    message: str


# ---------------------------------------------------------------------------
# Blocos de UI (envelope: type + version + props + actions)
# ---------------------------------------------------------------------------

class ProductCardBlock(BaseModel):
    type: Literal["product_card"] = "product_card"
    version: int = 1
    props: ProductCardProps
    actions: list[UIAction] = Field(default_factory=list)


class HeroBannerBlock(BaseModel):
    type: Literal["hero_banner"] = "hero_banner"
    version: int = 1
    props: HeroBannerProps
    actions: list[UIAction] = Field(default_factory=list)


class CheckoutSummaryBlock(BaseModel):
    type: Literal["checkout_summary"] = "checkout_summary"
    version: int = 1
    props: CheckoutSummaryProps
    actions: list[UIAction] = Field(default_factory=list)


class ProductDetailBlock(BaseModel):
    type: Literal["product_detail"] = "product_detail"
    version: int = 1
    props: ProductDetailProps
    actions: list[UIAction] = Field(default_factory=list)


class CategoryGridBlock(BaseModel):
    type: Literal["category_grid"] = "category_grid"
    version: int = 1
    props: CategoryGridProps
    actions: list[UIAction] = Field(default_factory=list)


class DeliveryOptionsBlock(BaseModel):
    type: Literal["delivery_options"] = "delivery_options"
    version: int = 1
    props: DeliveryOptionsProps
    actions: list[UIAction] = Field(default_factory=list)


class ShipmentBreakdownBlock(BaseModel):
    type: Literal["shipment_breakdown"] = "shipment_breakdown"
    version: int = 1
    props: ShipmentBreakdownProps
    actions: list[UIAction] = Field(default_factory=list)


class OfferComparisonBlock(BaseModel):
    type: Literal["offer_comparison"] = "offer_comparison"
    version: int = 1
    props: OfferComparisonProps
    actions: list[UIAction] = Field(default_factory=list)


class OriginMapBlock(BaseModel):
    type: Literal["origin_map"] = "origin_map"
    version: int = 1
    props: OriginMapProps
    actions: list[UIAction] = Field(default_factory=list)


class ImpactBannerBlock(BaseModel):
    type: Literal["impact_banner"] = "impact_banner"
    version: int = 1
    props: ImpactBannerProps
    actions: list[UIAction] = Field(default_factory=list)


UIComponent = Annotated[
    Union[
        ProductCardBlock,
        HeroBannerBlock,
        CategoryGridBlock,
        ProductDetailBlock,
        CheckoutSummaryBlock,
        DeliveryOptionsBlock,
        ImpactBannerBlock,
        ShipmentBreakdownBlock,
        OfferComparisonBlock,
        OriginMapBlock,
    ],
    Field(discriminator="type"),
]


# ---------------------------------------------------------------------------
# Resposta de tela
# ---------------------------------------------------------------------------

class ScreenResponse(BaseModel):
    schema_version: int = 1
    screen_id: str
    context: str
    components: list[UIComponent]
