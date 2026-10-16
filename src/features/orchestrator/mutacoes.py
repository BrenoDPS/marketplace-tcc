"""Mutacoes de contrato no BFF, ao vivo (Sprint 16, V9 — modo apresentacao).

A §3.3 promete "testes de mutacao de contrato no servidor BFF, alterando
dinamicamente a hierarquia dos nos da arvore JSON". O E2E prova isso
interceptando a resposta (`web/e2e/contract-mutation.spec.ts`); aqui o PROPRIO
servidor muta, a pedido do cliente (cabecalho `X-SDUI-Mutacao`), para a banca
ver a tela obedecer sem recompilar nem recarregar nada.

As mutacoes operam sobre o JSON ja serializado, nao sobre os modelos: o bloco
desconhecido e o envelope sem `actions` nem passariam pela validacao do
Pydantic — e e exatamente isso que eles testam no cliente. Ficam atras de
`settings.SDUI_MUTACOES_DEMO`.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

Tela = dict[str, Any]


def _reordenar(tela: Tela) -> None:
    tela["components"].reverse()


def _selo(tela: Tela) -> None:
    for bloco in tela["components"]:
        if "badge" in bloco["props"]:
            bloco["props"]["badge"] = {
                "label": "Selo injetado pelo servidor",
                "impact_level": "green",
                "icon": "leaf",
            }


def _bloco_novo(tela: Tela) -> None:
    # `product_card` existe no REGISTRY, mas o detalhe nunca o emite.
    tela["components"].append({
        "type": "product_card",
        "version": 1,
        "props": {
            "product_id": "injetado-pelo-servidor",
            "price": 12.34,
            "title": "Card que o detalhe nunca emitiu",
            "image_url": None,
            "badge": None,
        },
        "actions": [],
    })


def _bloco_desconhecido(tela: Tela) -> None:
    tela["components"].append({
        "type": "promo_carousel_que_nao_existe",
        "version": 7,
        "props": {"titulo": "bloco de um cliente mais novo"},
        "actions": [],
    })


def _sem_actions(tela: Tela) -> None:
    for bloco in tela["components"]:
        bloco.pop("actions", None)


# Ordem = ordem dos botoes na tela; rotulo e o que a banca le.
MUTACOES: dict[str, tuple[str, Callable[[Tela], None]]] = {
    "reordenar": ("Reordenar os blocos", _reordenar),
    "selo": ("Injetar selo", _selo),
    "bloco_novo": ("Bloco que a tela nunca teve", _bloco_novo),
    "bloco_desconhecido": ("Bloco que o cliente não conhece", _bloco_desconhecido),
    "sem_actions": ("Envelope sem actions", _sem_actions),
}


def aplicar(tela: Tela, nome: str) -> Tela:
    """Muta `tela` no lugar e a devolve. Nome desconhecido = KeyError (422 na rota)."""
    MUTACOES[nome][1](tela)
    return tela


if __name__ == "__main__":
    def base() -> Tela:
        return {"components": [
            {"type": "product_detail", "props": {"badge": None}, "actions": [{"type": "api_call"}]},
            {"type": "impact_banner", "props": {"badge": None}, "actions": []},
        ]}

    assert [c["type"] for c in aplicar(base(), "reordenar")["components"]] == ["impact_banner", "product_detail"]
    assert all(c["props"]["badge"] for c in aplicar(base(), "selo")["components"])
    assert aplicar(base(), "bloco_novo")["components"][-1]["type"] == "product_card"
    assert aplicar(base(), "bloco_desconhecido")["components"][-1]["version"] == 7
    assert all("actions" not in c for c in aplicar(base(), "sem_actions")["components"])
    print("ok")
