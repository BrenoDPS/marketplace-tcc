"""Teste de carga da jornada da defesa — meta do PRD: TTFB < 200 ms.

Roda contra a PILHA REAL (Postgres + ETL + FastAPI), como o E2E do Playwright.
Nao ha mock: a pergunta aqui e quanto custa uma consulta que realmente vai ao
banco, e um mock responderia outra pergunta.

    uvicorn src.main:app --port 8000        # SEM --reload: o file-watcher entra na medicao
    locust -f load/locustfile.py --headless -u 50 -r 10 -t 60s --host http://127.0.0.1:8000

Fora do CI pelo mesmo motivo do E2E: `data/raw/` e gitignored, entao o runner
do GitHub nao tem os CSVs do Olist para popular o banco. E uma medicao local.
"""

from __future__ import annotations

import random

from locust import HttpUser, between, task

# Sao Paulo tem vendedores da amostra por perto (selo verde); Fortaleza nao.
# Medir os dois separa "custo de calcular distancia" de "custo de montar selo".
ZIP_PERTO = "05311"
ZIP_LONGE = "60165"

# Maiores categorias do Olist — presentes em qualquer amostra razoavel.
TERMOS = ["cama mesa banho", "beleza saude", "moveis", "informatica"]


class JornadaUser(HttpUser):
    """Um comprador navegando. `between` evita medir um ataque de DoS.

    Sem pausa entre requisicoes o teste mede o quanto o cliente consegue
    empurrar, nao o quanto o servidor responde para gente de verdade — e a
    fila que se forma inflaria a latencia de todo mundo por igual.
    """

    wait_time = between(0.5, 2.0)

    def on_start(self) -> None:
        """Pega ids reais uma vez. O checkout precisa deles e nao os inventa."""
        self.product_ids: list[str] = []
        res = self.client.get(
            f"/api/v1/home?customer_zip_prefix={ZIP_PERTO}",
            name="[setup] home",
        )
        if res.status_code == 200:
            self.product_ids = [
                c["props"]["product_id"]
                for c in res.json()["components"]
                if c["type"] == "product_card"
            ]

    # --- Home: quatro formatos, porque eles custam coisas MUITO diferentes ---

    @task(10)
    def home_default(self) -> None:
        self.client.get(
            f"/api/v1/home?customer_zip_prefix={ZIP_PERTO}",
            name="GET /home (default)",
        )

    @task(5)
    def home_contexto(self) -> None:
        self.client.get(
            f"/api/v1/home?customer_zip_prefix={ZIP_PERTO}&context=electronics_expert",
            name="GET /home (electronics_expert)",
        )

    @task(5)
    def home_consciente(self) -> None:
        """O contexto-bandeira do TCC — e o mais caro: ordena por proximidade."""
        self.client.get(
            f"/api/v1/home?customer_zip_prefix={ZIP_PERTO}&context=conscious_buyer",
            name="GET /home (conscious_buyer)",
        )

    @task(5)
    def home_busca(self) -> None:
        self.client.get(
            f"/api/v1/home?customer_zip_prefix={ZIP_PERTO}&q={random.choice(TERMOS)}",
            name="GET /home (busca)",
        )

    @task(3)
    def home_cliente_distante(self) -> None:
        """Cliente longe: nenhum selo. Isola o custo de montar o selo."""
        self.client.get(
            f"/api/v1/home?customer_zip_prefix={ZIP_LONGE}",
            name="GET /home (cliente distante)",
        )

    # --- Telas seguintes da jornada ---

    @task(6)
    def detalhe(self) -> None:
        if not self.product_ids:
            return
        pid = random.choice(self.product_ids)
        self.client.get(
            f"/api/v1/products/{pid}?customer_zip_prefix={ZIP_PERTO}",
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
                "customer_zip_prefix": ZIP_PERTO,
                "items": itens,
                "delivery_option": random.choice([None, "green", "express"]),
            },
            name="POST /checkout/simulate",
        )
