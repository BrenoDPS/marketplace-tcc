"""Schemas de entrada do checkout simulado (Sprint 3)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CheckoutSimulateRequest(BaseModel):
    customer_zip_prefix: str = Field(..., min_length=1, max_length=5)
    product_id: str = Field(..., min_length=1)
    quantity: int = Field(default=1, ge=1)
