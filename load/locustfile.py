"""Teste de carga da jornada da defesa — meta do PRD: TTFB < 200 ms.

Roda contra a PILHA REAL (Postgres + ETL + FastAPI), como o E2E do Playwright.
Nao ha mock: a pergunta aqui e quanto custa uma consulta que realmente vai ao
banco, e um mock responderia outra pergunta.

    DEBUG=false uvicorn src.main:app --port 8000

`DEBUG=false` nao e detalhe: `src/core/database.py` liga o `echo` do SQLAlchemy
ao flag, e a API passa a imprimir cada SQL executado. Toda medicao ate a Sprint 7
foi feita assim, e numa das sondagens o log bloqueou o event loop o bastante para
o cliente Redis estourar o timeout. `--reload` tambem fica de fora: o
file-watcher entra na medicao.
    locust -f load/locustfile.py --headless -u 50 -r 10 -t 60s --host http://127.0.0.1:8000

Fora do CI pelo mesmo motivo do E2E: `data/raw/` e gitignored, entao o runner
do GitHub nao tem os CSVs do Olist para popular o banco. E uma medicao local.

VALIDADE DA MEDICAO (Sprint 7) — ler antes de citar estes numeros:

Ate a Sprint 6 o arquivo usava DOIS CEPs fixos. Isso tornava qualquer medicao
de cache uma fantasia: com duas chaves, a condicao "aquecida" teria ~100% de
acerto por construcao. Agora os CEPs saem da DISTRIBUICAO REAL de clientes da
amostra (`olist_customers`), que ja e desigual como a populacao brasileira —
Sao Paulo aparece muito mais que Roraima, e essa desigualdade e exatamente o
que decide a taxa de acerto de um cache real.

Cada usuario virtual sorteia UM CEP e o mantem na jornada inteira, porque e o
que uma pessoa faz. Consequencia a registrar no relatorio: o espaco de chaves
ativo e da ordem do numero de VUs, nao dos 12.933 prefixos do banco.
"""

from __future__ import annotations

import random

from locust import HttpUser, between, task
from sqlalchemy import create_engine, text

from scripts.etl_load_sample import _sync_database_url


def _cep_dos_clientes() -> list[str]:
    """CEPs na proporcao real: uma entrada por cliente, nao por prefixo distinto.

    Nao ha fallback de proposito. Um teste de carga que silenciosamente cai
    para CEPs inventados produz um numero que parece valido e nao e — foi
    exatamente esse o defeito corrigido aqui.
    """
    engine = create_engine(_sync_database_url())
    with engine.connect() as conn:
        ceps = [
            row[0]
            for row in conn.execute(
                text("SELECT customer_zip_code_prefix FROM olist_customers")
            )
            if row[0]
        ]
    engine.dispose()
    if not ceps:
        raise RuntimeError("olist_customers vazia — rode o ETL antes do teste de carga")
    return ceps


CEPS = _cep_dos_clientes()

# Maiores categorias do Olist — presentes em qualquer amostra razoavel.
TERMOS = ["cama mesa banho", "beleza saude", "moveis", "informatica"]


class JornadaUser(HttpUser):
    """Um comprador navegando. `between` evita medir um ataque de DoS.

    Sem pausa entre requisicoes o teste mede o quanto o cliente consegue
    empurrar, nao o quanto o servidor responde para gente de verdade — e a
    fila que se forma inflaria a latencia de todo mundo por igual.

    1 a 3 segundos e o que a secao 3.3 da metodologia declara. Ate a Sprint 7
    o codigo usava 0,5 a 2,0 — o texto e a medicao diziam coisas diferentes.
    """

    wait_time = between(1, 3)

    def on_start(self) -> None:
        """Sorteia o CEP deste comprador e pega ids reais de produto.

        O perfil (com/sem selo) sai do que a API respondeu para ESTE CEP, e nao
        de um par de CEPs escolhido a mao: as duas populacoes continuam
        separadas nas estatisticas do Locust, agora emergindo de CEPs reais.
        """
        self.cep = random.choice(CEPS)
        self.product_ids: list[str] = []
        self.perfil = "sem selo"
        res = self.client.get(
            f"/api/v1/home?customer_zip_prefix={self.cep}",
            name="[setup] home",
        )
        if res.status_code == 200:
            cards = [c for c in res.json()["components"] if c["type"] == "product_card"]
            self.product_ids = [c["props"]["product_id"] for c in cards]
            if any(c["props"].get("badge") for c in cards):
                self.perfil = "com selo"

    # --- Home: quatro formatos, porque eles custam coisas MUITO diferentes ---

    @task(13)
    def home_default(self) -> None:
        self.client.get(
            f"/api/v1/home?customer_zip_prefix={self.cep}",
            name=f"GET /home (default, {self.perfil})",
        )

    @task(5)
    def home_contexto(self) -> None:
        self.client.get(
            f"/api/v1/home?customer_zip_prefix={self.cep}&context=electronics_expert",
            name="GET /home (electronics_expert)",
        )

    @task(5)
    def home_consciente(self) -> None:
        """O contexto-bandeira do TCC — e o mais caro: ordena por proximidade."""
        self.client.get(
            f"/api/v1/home?customer_zip_prefix={self.cep}&context=conscious_buyer",
            name="GET /home (conscious_buyer)",
        )

    @task(5)
    def home_busca(self) -> None:
        self.client.get(
            f"/api/v1/home?customer_zip_prefix={self.cep}&q={random.choice(TERMOS)}",
            name="GET /home (busca)",
        )

    # --- Telas seguintes da jornada ---

    @task(6)
    def detalhe(self) -> None:
        if not self.product_ids:
            return
        pid = random.choice(self.product_ids)
        self.client.get(
            f"/api/v1/products/{pid}?customer_zip_prefix={self.cep}",
            name="GET /products/{id}",
        )

    @task(4)
    def checkout(self) -> None:
        """Carrinho de 1 a 3 itens — varios vendedores viram varias remessas."""
        if not self.product_ids:
            return
        k = min(len(self.product_ids), random.randint(1, 3))
        itens = [
            {"product_id": pid, "quantity": 1}
            for pid in random.sample(self.product_ids, k)
        ]
        self.client.post(
            "/api/v1/checkout/simulate",
            json={
                "customer_zip_prefix": self.cep,
                "items": itens,
                "delivery_option": random.choice([None, "green", "express"]),
            },
            name="POST /checkout/simulate",
        )
