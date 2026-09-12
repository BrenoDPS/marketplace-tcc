# Medição de latência — a meta de TTFB < 200 ms

**Meta declarada:** `docs/prd.md` e `docs/tech_spec.md` §4 prometem **TTFB < 200 ms
em cenários de alta concorrência**, "com auxílio de cache Redis".

Até esta medição a promessa não tinha **nenhum número** por trás. Este documento
tem os números, a causa da lentidão e o que a correção vale — medido, não estimado.

**Resposta curta:** a meta **não é cumprida hoje**, e o motivo **não é falta de
cache**. É a aplicação perguntar ao banco a mesma coisa dezenas de vezes por
requisição.

---

## 1. Como medir de novo

```bash
docker compose up -d
python -m scripts.etl_load_sample          # se o banco estiver vazio
uvicorn src.main:app --port 8000           # SEM --reload
pip install locust==2.46.5                 # dependencia so de desenvolvimento
locust -f load/locustfile.py --headless -u 50 -r 10 -t 45s --host http://127.0.0.1:8000
```

> **`--reload` fica de fora de propósito.** Ele liga um file-watcher que entra na
> medição. Um número tirado com `--reload` mede o ambiente de desenvolvimento,
> não a aplicação.

Fora do CI pelo mesmo motivo do E2E: `data/raw/` é gitignored, então o runner do
GitHub não tem os CSVs do Olist para popular o banco.

**Ambiente desta medição:** Windows 11, 8 vCPU, Postgres 16 em Docker, uvicorn com
**1 worker**, cliente e servidor **na mesma máquina** — a partir de ~25 usuários o
Locust disputa CPU com o uvicorn, então os números de 50 usuários são um piso
pessimista, não um teto. Amostra do ETL: seed 42, ~10k `order_items`.

Dados brutos em `load/results/u{1,10,25,50}_stats.csv`.

---

## 2. O que a medição deu

Latência **p50 / p95 em ms**, 45 s por nível:

| endpoint | u=1 | u=10 | u=25 | u=50 |
|---|---|---|---|---|
| `GET /home` (default) | 98 / 98 | 120 / 450 | 270 / 940 | 930 / 1500 |
| `GET /home` (electronics_expert) | 81 / 98 | 130 / 570 | 200 / 860 | 840 / 1400 |
| **`GET /home` (conscious_buyer)** | **250 / 320** | **300 / 550** | **640 / 1400** | **2200 / 2800** |
| `GET /home` (busca) | 110 / 110 | 110 / 420 | 320 / 940 | 880 / 1400 |
| `GET /home` (cliente distante) | 160 / 160 | 120 / 340 | 320 / 870 | 860 / 1500 |
| `GET /products/{id}` | 65 / 75 | 70 / 220 | 89 / 690 | 510 / 1000 |
| `POST /checkout/simulate` | 95 / 150 | 100 / 210 | 220 / 680 | 690 / 1200 |
| **agregado** | **87 / 310** | **130 / 570** | **270 / 1100** | **890 / 2500** |
| throughput (req/s) | 0,7 | 7,0 | 15,8 | 22,4 |
| falhas | 0 | 0 | 0 | 0 |

Três leituras:

1. **A meta já falha com um usuário só.** O `conscious_buyer` marca **250 ms de
   p50 sem concorrência nenhuma**. Não é um problema de escala — é o custo de
   montar **uma** tela.
2. **O contexto-bandeira do TCC é o mais lento.** `conscious_buyer` é justamente
   a tela do consumo consciente, a que a defesa vai mostrar. Ela é ~3× mais cara
   que as outras.
3. **Zero falhas, throughput travado em ~22 req/s.** O sistema não quebra sob
   carga: ele **enfileira**. Latência subindo enquanto o throughput estaciona é a
   assinatura de trabalho serializado, não de falta de recurso.

---

## 3. Por que está lento

Contando os *roundtrips* ao Postgres por requisição (SQLAlchemy
`before_cursor_execute`):

| contexto | queries | busca de centroide | **repetem o MESMO CEP do comprador** |
|---|---|---|---|
| `default` | 15 | 12 | **6** |
| `electronics_expert` | 15 | 12 | **6** |
| `conscious_buyer` | **63** | 60 | **30** |

O `conscious_buyer` faz **63 idas ao banco para montar 6 cards**. E metade das
buscas de centroide pede **o mesmo CEP do comprador, que não muda durante a
requisição**.

A causa está em [`composer.py:183`](../src/features/home_contextual/composer.py#L183):

```python
scored = [(await _distance(product), product) for product in products]
```

Um `await` sequencial por produto, sobre um pool de 24. Cada `_distance` chama
`compute_distance_km`, que em [`service.py:19`](../src/features/green_logistics/service.py#L19)
busca **dois** centroides — o do vendedor e, de novo, o do comprador:

```python
customer = await get_centroid(session, customer_zip_prefix)   # sempre o mesmo
seller   = await get_centroid(session, seller_zip_prefix)
```

24 produtos × 2 + 6 cards × 2 = 60 buscas, das quais 30 são idênticas entre si.

Há ainda um custo fixo em toda requisição: `list_known_prefixes` faz
`SELECT zip_prefix FROM cep_centroids` — **os 6403 prefixos** — só para validar
se um deles existe.

---

## 4. O que a correção vale (medido)

Três cenários, mesmo código de composição, 20 repetições, p50:

| contexto | hoje | memo por requisição | cache entre requisições |
|---|---|---|---|
| `default` | 42,2 ms (15 q) | 28,5 ms (10 q) — **−33%** | 22,2 ms (3 q) — **−47%** |
| `conscious_buyer` | 109,3 ms (63 q) | 52,3 ms (27 q) — **−52%** | 19,9 ms (3 q) — **−82%** |

> A contagem de queries caindo junto (63 → 27 → 3) é o que prova que a
> intervenção realmente aconteceu. Na primeira tentativa o *monkeypatch* foi
> aplicado no módulo errado — `compute_distance_km` importa `get_centroid` por
> nome, de `service.py`, então remendar `repository.py` não o alcançava. O
> resultado "não melhorou nada" era o patch não ter pegado, não a hipótese ser
> falsa. **Sem a contagem de queries isso teria passado por conclusão.**

---

## 5. Recomendação: não comece pelo Redis

O card *[Roadmap] Cache Redis em runtime* propõe "cachear `compute_distance_km`
por par de CEPs". Isso trataria o sintoma: **metade dessas buscas pede um valor
que a aplicação já tem em mãos.** Levá-las ao Redis troca um roundtrip de rede
por outro roundtrip de rede.

E o dado que decide:

| | |
|---|---|
| `cep_centroids` no Postgres | 520 kB, 6403 linhas |
| o mesmo como `dict` em Python | **~1,1 MB** |

A tabela de centroides é **dado de referência estático**, escrito uma vez pelo
ETL e nunca alterado em runtime. Ela **cabe inteira na memória do processo**.

Ordem sugerida, do mais barato para o mais caro:

1. **Não perguntar duas vezes.** Buscar o centroide do comprador uma vez por
   requisição e passá-lo adiante. Corta 30 queries do `conscious_buyer`; medido
   em **−52%**.
2. **Carregar `cep_centroids` na memória** no startup (~1,1 MB). Elimina também o
   `SELECT` dos 6403 prefixos por requisição. Medido em **−82%**, e chega mais
   perto que o Redis chegaria, porque não tem salto de rede.
3. **Paralelizar o ranking** com `asyncio.gather` se ainda faltar — hoje os
   `await` são sequenciais.
4. **Redis, se ainda fizer falta.** Ele resolve estado *compartilhado entre
   processos*; com 1 worker e dado estático de 1 MB, ainda não há esse problema.
   Quando houver mais de um worker, reavaliar.

**O que esta medição ainda não responde:** os itens 1–3 foram medidos
**sem concorrência**. Confirmar que eles levam o p95 sob carga para baixo de
200 ms exige implementá-los e rodar o Locust de novo — a suíte já está pronta
para isso.

---

*Medição da Sprint 6. Suíte em `load/locustfile.py`; dados em `load/results/`.*
