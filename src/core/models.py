"""Modelos SQLAlchemy 2.0 para a amostra Olist carregada pelo ETL.

Tabelas espelham um subconjunto do dataset Olist filtrado pelo `scripts/etl_load_sample.py`.
A tabela `cep_centroids` e derivada (mediana de lat/lng por prefixo).
"""

from __future__ import annotations

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Customer(Base):
    __tablename__ = "olist_customers"

    customer_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    customer_zip_code_prefix: Mapped[str] = mapped_column(String(5), index=True, nullable=False)
    customer_city: Mapped[str | None] = mapped_column(String(120))
    customer_state: Mapped[str | None] = mapped_column(String(4))


class Seller(Base):
    __tablename__ = "olist_sellers"

    seller_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    seller_zip_code_prefix: Mapped[str] = mapped_column(String(5), index=True, nullable=False)
    seller_city: Mapped[str | None] = mapped_column(String(120))
    seller_state: Mapped[str | None] = mapped_column(String(4))


class Product(Base):
    __tablename__ = "olist_products"

    product_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    product_category_name: Mapped[str | None] = mapped_column(String(120), index=True)
    product_weight_g: Mapped[float | None] = mapped_column(Float)
    # Media/contagem de `review_score` dos pedidos que contem o produto. A nota
    # no Olist e do PEDIDO, nao do item — a atribuicao e uma aproximacao, mas os
    # numeros sao reais. Sem pedido avaliado, `rating` fica nulo.
    rating: Mapped[float | None] = mapped_column(Float)
    review_count: Mapped[int] = mapped_column(Integer, default=0)


class Order(Base):
    __tablename__ = "olist_orders"

    order_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("olist_customers.customer_id"), nullable=False, index=True
    )
    order_status: Mapped[str | None] = mapped_column(String(32))


class OrderItem(Base):
    __tablename__ = "olist_order_items"

    order_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("olist_orders.order_id"), primary_key=True
    )
    order_item_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("olist_products.product_id"), nullable=False, index=True
    )
    seller_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("olist_sellers.seller_id"), nullable=False, index=True
    )
    price: Mapped[float] = mapped_column(Float, nullable=False)
    freight_value: Mapped[float | None] = mapped_column(Float)


class Offer(Base):
    """Um vendedor oferecendo um produto por um preco. Derivada no ETL.

    O Olist nao tem tabela de oferta: `olist_products_dataset.csv` nao traz
    `seller_id`, e o vinculo produto->vendedor so existe dentro de
    `order_items`. Por isso as telas liam um LOG DE PEDIDOS como se fosse
    catalogo, cada uma reimplementando a regra tacita "primeira order_item do
    produto" para escolher um vendedor entre varios.

    Esta tabela materializa o vinculo uma vez, no ETL. As telas passam a ler
    catalogo, e o mesmo produto vendido por varios vendedores deixa de ser um
    caso a desempatar e vira a informacao que sustenta o argumento da tese:
    dos dois vendedores do mesmo item, o mais perto emite menos.
    """

    __tablename__ = "offers"

    product_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("olist_products.product_id"), primary_key=True
    )
    seller_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("olist_sellers.seller_id"), primary_key=True
    )
    price: Mapped[float] = mapped_column(Float, nullable=False)
    freight_value: Mapped[float | None] = mapped_column(Float)
    # Reproduz a "primeira order_item" de hoje para as telas que mostram UM
    # vendedor. Exatamente uma por produto — `tests/test_offers.py` cobre o
    # invariante. Quando a escolha passar a ser por distancia, isto vira o
    # fallback de quando nao da para medir (vendedor sem centroide).
    is_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )


class CepCentroid(Base):
    """Centroide (mediana) de lat/lng por prefixo de CEP. Derivado no ETL."""

    __tablename__ = "cep_centroids"

    zip_prefix: Mapped[str] = mapped_column(String(5), primary_key=True)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
