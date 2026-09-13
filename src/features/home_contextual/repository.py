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

from src.core.models import Offer, Product, Seller


@dataclass(frozen=True, slots=True)
class ProductRow:
    """Estrutura interna (nao SDUI) para passar dados do Postgres ao composer."""

    product_id: str
    seller_id: str
    seller_zip_prefix: str
    price: float
    weight_g: float | None
    category: str | None


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


# Heuristica context -> categoria Olist. Pode ser refinada na Sprint 3.
_CONTEXT_TO_CATEGORY: dict[str, str] = {
    "electronics_expert": "informatica_acessorios",
    "beauty_lover": "beleza_saude",
}


def category_for_context(context: str) -> str | None:
    return _CONTEXT_TO_CATEGORY.get(context)


async def fetch_products_for_home(
    session: AsyncSession,
    category: str | None = None,
    limit: int = 6,
    search: str | None = None,
) -> list[ProductRow]:
    """Retorna ate `limit` produtos distintos da amostra.

    JOIN offers -> products -> sellers, filtrando por categoria e/ou termo
    de busca quando informados. **Sem fallback:** filtro que nao casa devolve
    lista vazia. Quem decide se cabe cair para a vitrine sem filtro e o composer,
    que sabe se a categoria veio do usuario ou do contexto — mostrar produtos
    aleatorios para quem buscou algo especifico seria mentir sobre o resultado.

    `is_default` escolhe uma oferta por produto. Enquanto a vitrine mostrar um
    vendedor so, e ele; quando passar a mostrar o mais proximo do comprador, o
    filtro sai daqui e a escolha vira do composer, que sabe onde o cliente esta.
    """
    stmt = (
        select(
            Offer.product_id,
            Offer.seller_id,
            Seller.seller_zip_code_prefix,
            Offer.price,
            Product.product_weight_g,
            Product.product_category_name,
        )
        .join(Product, Product.product_id == Offer.product_id)
        .join(Seller, Seller.seller_id == Offer.seller_id)
        .where(Offer.is_default)
    )
    if category is not None:
        stmt = stmt.where(Product.product_category_name == category)
    if search:
        # ponytail: ILIKE com `%` a esquerda ignora o indice de categoria; com
        # 6,5k produtos na amostra e irrelevante. Se o dataset crescer para o
        # Olist completo, trocar por trigram (pg_trgm) ou tsvector.
        pattern = f"%{search.translate(_LIKE_SPECIALS)}%"
        stmt = stmt.where(
            func.replace(Product.product_category_name, "_", " ").ilike(
                pattern, escape="\\"
            )
        )
    # Sem ORDER BY, SQL nao promete ordem nenhuma: a vitrine mudava de produtos
    # a cada recarga do ETL, com a MESMA amostra e o mesmo seed — verificado
    # rodando o ETL duas vezes e comparando a resposta. Isso quebrava a demo da
    # defesa (produtos diferentes a cada carga) e tornava as medicoes de carga
    # incomparaveis entre si. `product_id` e criterio arbitrario, mas estavel;
    # ordenacao com significado (proximidade, preco) entra junto com a escolha
    # de oferta por distancia.
    stmt = stmt.order_by(Offer.product_id).limit(limit)

    result = await session.execute(stmt)
    return [
        ProductRow(
            product_id=product_id,
            seller_id=seller_id,
            seller_zip_prefix=zip_prefix,
            price=float(price),
            weight_g=float(weight_g) if weight_g is not None else None,
            category=cat,
        )
        for product_id, seller_id, zip_prefix, price, weight_g, cat in result
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
