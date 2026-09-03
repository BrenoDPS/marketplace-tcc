"""Schemas de entrada do checkout simulado (Sprint 3, carrinho na Sprint 5)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CartItemRequest(BaseModel):
    product_id: str = Field(..., min_length=1)
    quantity: int = Field(default=1, ge=1)


class CheckoutSimulateRequest(BaseModel):
    customer_zip_prefix: str = Field(..., min_length=1, max_length=5)
    # Carrinho: sempre lista, mesmo com um item so. Aceitar duas formas de
    # corpo (um produto solto OU a lista) dobraria o contrato para sempre em
    # troca de nada — o unico cliente e o front deste repo.
    items: list[CartItemRequest] = Field(..., min_length=1, max_length=20)
    # Ausente = modalidade padrao. O router valida contra MODES_BY_ID para o
    # erro citar as opcoes validas em vez de um 500 por KeyError.
    delivery_option: str | None = None
