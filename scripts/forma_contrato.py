"""Forma do contrato SDUI para o espelho do front (Sprint 12).

Para cada bloco, os nomes de campo de `props`, recursivamente: modelo aninhado
(ou lista de modelos) vira a forma dele; folha (texto, numero, `actions`) vira
`true`. O front declara a mesma forma em `web/lib/contrato.ts` e o Vitest
compara; `tests/test_schemas.py` falha se este arquivo ficar velho.

    python -m scripts.forma_contrato   # regrava web/tests/contrato-bff.json
"""

from __future__ import annotations

import json
import types
from pathlib import Path
from typing import Annotated, Union, get_args, get_origin

from pydantic import BaseModel

from src.schemas.sdui import UIComponent

SAIDA = Path("web/tests/contrato-bff.json")


def _forma_do_tipo(anotacao: object) -> object:
    origem = get_origin(anotacao)
    if origem is Annotated:
        # `Annotated[Union[...], discriminator]` = uniao discriminada (actions): folha.
        return True
    if origem in (Union, types.UnionType):
        ramos = [a for a in get_args(anotacao) if a is not type(None)]
        return _forma_do_tipo(ramos[0]) if len(ramos) == 1 else True
    if origem in (list, tuple):
        return _forma_do_tipo(get_args(anotacao)[0])
    if isinstance(anotacao, type) and issubclass(anotacao, BaseModel):
        return forma(anotacao)
    return True


def forma(modelo: type[BaseModel]) -> dict[str, object]:
    return {nome: _forma_do_tipo(campo.annotation) for nome, campo in sorted(modelo.model_fields.items())}


def contrato() -> dict[str, object]:
    blocos = get_args(get_args(UIComponent)[0])
    return {b.model_fields["type"].default: forma(b.model_fields["props"].annotation) for b in sorted(blocos, key=lambda b: b.model_fields["type"].default)}


def texto() -> str:
    return json.dumps(contrato(), ensure_ascii=False, indent=2) + "\n"


if __name__ == "__main__":
    SAIDA.write_text(texto(), encoding="utf-8")
    print(SAIDA)
