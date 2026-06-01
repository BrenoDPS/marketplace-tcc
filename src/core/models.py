"""Modelos SQLAlchemy 2.0 para a amostra Olist carregada pelo ETL.

Tabelas espelham um subconjunto do dataset Olist filtrado pelo `scripts/etl_load_sample.py`.
A tabela `cep_centroids` e derivada (mediana de lat/lng por prefixo).
"""

from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String
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


class CepCentroid(Base):
    """Centroide (mediana) de lat/lng por prefixo de CEP. Derivado no ETL."""

    __tablename__ = "cep_centroids"

    zip_prefix: Mapped[str] = mapped_column(String(5), primary_key=True)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
