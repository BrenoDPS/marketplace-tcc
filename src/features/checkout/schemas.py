"""Schemas de entrada do checkout simulado (Sprint 3)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CheckoutSimulateRequest(BaseModel):
    customer_zip_prefix: str = Field(..., min_length=1, max_length=5)
    product_id: str = Field(..., min_length=1)
    quantity: int = Field(default=1, ge=1)
    # Ausente = modalidade padrao. O router valida contra MODES_BY_ID para o
    # erro citar as opcoes validas em vez de um 500 por KeyError.
    delivery_option: str | None = None
