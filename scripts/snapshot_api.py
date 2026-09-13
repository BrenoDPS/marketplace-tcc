"""Congela a resposta da API inteira num JSON, para diff antes/depois.

Existe porque **nenhum teste toca SQL**: os testes usam `dependency_overrides`
com fixtures de `ProductRow`, entao trocar a consulta por baixo deles nao
quebra nada e tambem nao prova nada. O refactor de `order_items` para `offers`
precisa de uma evidencia que nao seja impressao — esta.

    # antes de mexer no codigo
    python -m scripts.snapshot_api --out docs/snapshots/antes.json
    # depois
    python -m scripts.snapshot_api --out depois.json
    diff docs/snapshots/antes.json depois.json    # tem que ser vazio

Precisa da API no ar e do banco carregado com a MESMA amostra (mesmo seed):
mudar os dados e mudar a resposta, e ai o diff nao diz nada sobre o codigo.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import httpx

DEFAULT_BASE = "http://127.0.0.1:8000"
DEFAULT_OUT = "docs/snapshots/api.json"

# Mesmos CEPs da suite de carga: um com vendedores por perto (selo verde) e um
# sem. Cobrem os dois lados do caminho que o refactor mexe.
ZIPS = ("05311", "60165")

CONTEXTS = ("default", "electronics_expert", "conscious_buyer")
BUSCAS = ("cama mesa banho", "informatica")


def _get(client: httpx.Client, path: str, **params: Any) -> dict[str, Any]:
    """Resposta como dict, ou o erro — um 422 tambem e comportamento a congelar."""
    res = client.get(path, params=params)
    if res.status_code != 200:
        return {"__status__": res.status_code, "__body__": res.text[:500]}
    return res.json()


def coletar(base_url: str) -> dict[str, Any]:
    snap: dict[str, Any] = {}
    with httpx.Client(base_url=base_url, timeout=30.0) as client:
        # --- Home: as variantes que o composer trata por caminhos diferentes ---
        for zip_prefix in ZIPS:
            for context in CONTEXTS:
                chave = f"home|zip={zip_prefix}|context={context}"
                snap[chave] = _get(
                    client,
                    "/api/v1/home",
                    customer_zip_prefix=zip_prefix,
                    context=context,
                )
            for termo in BUSCAS:
                chave = f"home|zip={zip_prefix}|q={termo}"
                snap[chave] = _get(
                    client,
                    "/api/v1/home",
                    customer_zip_prefix=zip_prefix,
                    q=termo,
                )

        # --- Detalhe e checkout: ids reais, vindos da propria Home ---
        base_home = snap[f"home|zip={ZIPS[0]}|context=default"]
        ids = sorted(
            c["props"]["product_id"]
            for c in base_home.get("components", [])
            if c.get("type") == "product_card"
        )
        if not ids:
            print(
                "[snapshot] AVISO: a Home nao devolveu product_card. "
                "Banco vazio? Detalhe e checkout ficam de fora.",
                file=sys.stderr,
            )

        for product_id in ids:
            chave = f"detalhe|{product_id}"
            snap[chave] = _get(
                client,
                f"/api/v1/products/{product_id}",
                customer_zip_prefix=ZIPS[0],
            )

        # Carrinhos de tamanho crescente: 1 item, 2 itens, tudo. Varios
        # vendedores viram varias remessas, que e onde o checkout tem logica.
        for n in (1, 2, len(ids)):
            if n == 0 or n > len(ids):
                continue
            itens = [{"product_id": pid, "quantity": 1} for pid in ids[:n]]
            for modalidade in (None, "green", "express"):
                chave = f"checkout|n={n}|modalidade={modalidade}"
                res = client.post(
                    "/api/v1/checkout/simulate",
                    json={
                        "customer_zip_prefix": ZIPS[0],
                        "items": itens,
                        "delivery_option": modalidade,
                    },
                )
                snap[chave] = (
                    res.json()
                    if res.status_code == 200
                    else {"__status__": res.status_code, "__body__": res.text[:500]}
                )

    return snap


def main() -> int:
    parser = argparse.ArgumentParser(description="Congela a resposta da API para diff")
    parser.add_argument("--base-url", default=DEFAULT_BASE)
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args()

    try:
        snap = coletar(args.base_url)
    except httpx.ConnectError:
        print(
            f"[snapshot] nao consegui falar com {args.base_url}. "
            "A API esta no ar? `uvicorn src.main:app --port 8000`",
            file=sys.stderr,
        )
        return 1

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    # `sort_keys` e o que torna o arquivo comparavel: sem isso a ordem das
    # chaves do dict entraria no diff e esconderia a mudanca de verdade.
    out.write_text(
        json.dumps(snap, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    rotas = len(snap)
    erros = sum(1 for v in snap.values() if "__status__" in v)
    print(f"[snapshot] {rotas} rotas gravadas em {out}")
    if erros:
        print(f"[snapshot] {erros} rotas responderam fora de 200 (congeladas assim mesmo)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
