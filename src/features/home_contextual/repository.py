"""Repository da home: consulta produtos reais da amostra Olist.

Sobre a busca (Sprint 5): **o Olist nao tem nome de produto.** O dataset traz
`product_category_name` e nada mais textual — o `title` que aparece no card ja e
a categoria formatada. Entao "busca textual" aqui so pode ser busca sobre
categoria, e e isso que esta implementado. Nao ha como buscar "fone bluetooth"
porque essa string nao existe em lugar nenhum da amostra.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import Offer, Product, RegionalCategory, Seller
from src.features.green_logistics.repository import get_uf


@dataclass(frozen=True, slots=True)
class ProductRow:
    """Estrutura interna (nao SDUI) para passar dados do Postgres ao composer."""

    product_id: str
    seller_id: str
    seller_zip_prefix: str
    price: float
    weight_g: float | None
    category: str | None
    # Volume do dataset; entra no CO2 como massa cubada quando ela supera
    # a real. Default `None` para quem so tem massa (fixtures, chamadas antigas).
    volume_cm3: float | None = None


@dataclass(frozen=True, slots=True)
class CategoryRow:
    slug: str
    product_count: int


# `%` e `_` sao curingas de LIKE: sem escapar, quem digita "50%" varre a tabela
# inteira. Entrada de usuario, entao escapa antes de virar padrao.
_LIKE_SPECIALS = str.maketrans({"\\": r"\\", "%": r"\%", "_": r"\_"})


def normalize_search(term: str) -> str:
    """Dobra acentos, minusculiza e normaliza espacos. String vazia = sem busca.

    As categorias do Olist ja sao ASCII com `_` no lugar de espaco
    (`moveis_decoracao`, `relogios_presentes`), entao so o **termo do usuario**
    precisa ser dobrado — "móveis" e "moveis" chegam iguais na consulta.
    """
    folded = unicodedata.normalize("NFKD", term).encode("ascii", "ignore").decode()
    return " ".join(folded.replace("_", " ").lower().split())


# Contextos ESCOLHIDOS (query param). Sao o override: quem pede um deles recebe
# ele. Sem pedido (`default`), o contexto vem do CEP — `regional_pick`.
_CONTEXT_TO_CATEGORY: dict[str, str] = {
    "electronics_expert": "informatica_acessorios",
    "beauty_lover": "beleza_saude",
}


def category_for_context(context: str) -> str | None:
    return _CONTEXT_TO_CATEGORY.get(context)


@dataclass(frozen=True, slots=True)
class RegionalPick:
    uf: str
    category: str
    lift: float


# ponytail: snapshot de processo, como os centroides — recarregou o ETL com a
# API no ar, reinicie a API. Sem lock: sao <= 27 linhas e carregar duas vezes
# na partida fria e inofensivo.
_regional: dict[str, RegionalPick] | None = None


async def regional_pick(
    session: AsyncSession, customer_zip_prefix: str
) -> RegionalPick | None:
    """A categoria que a UF do comprador compra acima da media nacional.

    Derivada no ETL sobre o dataset completo (`build_regional_categories`).
    `None` quando a UF nao tem sinal regional suficiente — a Home fica a geral.
    Zero consulta no caminho quente: UF e tabela vivem em memoria.
    """
    global _regional
    uf = await get_uf(session, customer_zip_prefix)
    if uf is None:
        return None
    if _regional is None:
        rows = (await session.execute(select(RegionalCategory))).scalars().all()
        _regional = {r.uf: RegionalPick(r.uf, r.category, float(r.lift)) for r in rows}
    return _regional.get(uf)


async def fetch_products_for_home(
    session: AsyncSession,
    category: str | None = None,
    limit: int = 6,
    search: str | None = None,
) -> list[ProductRow]:
    """Retorna TODAS as ofertas dos ate `limit` produtos da vitrine.

    Uma linha por (produto, vendedor), entao um produto com tres vendedores vem
    em tres linhas. **Quem escolhe entre elas e o composer**, porque a escolha
    depende de onde o comprador esta e o repositorio nao sabe isso.

    Duas etapas numa consulta so: a subconsulta decide QUAIS produtos entram na
    vitrine (com os filtros, e limitada a `limit`), e a externa traz as ofertas
    deles. Aplicar o `LIMIT` direto sobre as ofertas devolveria menos produtos
    do que o pedido sempre que um deles tivesse mais de um vendedor.

    **Sem fallback:** filtro que nao casa devolve lista vazia. Quem decide se
    cabe cair para a vitrine sem filtro e o composer, que sabe se a categoria
    veio do usuario ou do contexto — mostrar produtos aleatorios para quem
    buscou algo especifico seria mentir sobre o resultado.
    """
    escolhidos = select(Offer.product_id).join(
        Product, Product.product_id == Offer.product_id
    )
    if category is not None:
        escolhidos = escolhidos.where(Product.product_category_name == category)
    if search:
        # ponytail: ILIKE com `%` a esquerda ignora o indice de categoria; com
        # 6,5k produtos na amostra e irrelevante. Se o dataset crescer para o
        # Olist completo, trocar por trigram (pg_trgm) ou tsvector.
        pattern = f"%{search.translate(_LIKE_SPECIALS)}%"
        escolhidos = escolhidos.where(
            func.replace(Product.product_category_name, "_", " ").ilike(
                pattern, escape="\\"
            )
        )
    # Sem ORDER BY, SQL nao promete ordem nenhuma: a vitrine mudava de produtos
    # a cada recarga do ETL, com a MESMA amostra e o mesmo seed — verificado
    # rodando o ETL duas vezes e comparando a resposta. Isso quebrava a demo da
    # defesa (produtos diferentes a cada carga) e tornava as medicoes de carga
    # incomparaveis entre si. `product_id` e criterio arbitrario, mas estavel;
    # ordenacao com significado entra quando a vitrine tiver por que ordenar.
    escolhidos = (
        escolhidos.group_by(Offer.product_id)
        .order_by(Offer.product_id)
        .limit(limit)
        .subquery()
    )

    stmt = (
        select(
            Offer.product_id,
            Offer.seller_id,
            Seller.seller_zip_code_prefix,
            Offer.price,
            Product.product_weight_g,
            Product.product_category_name,
            Product.product_volume_cm3,
        )
        .join(Product, Product.product_id == Offer.product_id)
        .join(Seller, Seller.seller_id == Offer.seller_id)
        .join(escolhidos, escolhidos.c.product_id == Offer.product_id)
        # `seller_id` desempata entre ofertas do mesmo produto: sem ele, duas
        # ofertas a mesma distancia poderiam trocar de lugar entre execucoes.
        .order_by(Offer.product_id, Offer.seller_id)
    )

    result = await session.execute(stmt)
    return [
        ProductRow(
            product_id=product_id,
            seller_id=seller_id,
            seller_zip_prefix=zip_prefix,
            price=float(price),
            weight_g=float(weight_g) if weight_g is not None else None,
            category=cat,
            volume_cm3=float(volume) if volume is not None else None,
        )
        for product_id, seller_id, zip_prefix, price, weight_g, cat, volume in result
    ]


async def list_categories(
    session: AsyncSession, limit: int | None = None
) -> list[CategoryRow]:
    """Categorias da amostra com contagem de produtos, da maior para a menor.

    Conta em `olist_products` direto: o ETL so carrega produtos que aparecem em
    `order_items`, entao toda categoria listada tem produto navegavel.
    """
    total = func.count(Product.product_id)
    stmt = (
        select(Product.product_category_name, total)
        .where(Product.product_category_name.is_not(None))
        .group_by(Product.product_category_name)
        .order_by(total.desc(), Product.product_category_name)
    )
    if limit is not None:
        stmt = stmt.limit(limit)

    result = await session.execute(stmt)
    return [CategoryRow(slug=slug, product_count=count) for slug, count in result.all()]
