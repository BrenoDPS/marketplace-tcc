# Medição de latência — a meta de TTFB < 200 ms

**Meta declarada:** `docs/prd.md` e `docs/tech_spec.md` §4 prometem **TTFB < 200 ms
em cenários de alta concorrência**, "com auxílio de cache Redis".

Até esta medição a promessa não tinha **nenhum número** por trás. Este documento
tem os números, a causa da lentidão e o que a correção vale — medido, não estimado.

**Resposta curta:** a meta **não era cumprida**, e o motivo **não era falta de
cache** — era a aplicação perguntar ao banco a mesma coisa dezenas de vezes por
requisição. Corrigido nas §6 e §7: `conscious_buyer` foi de **63 para 2 queries**
e de **150 ms para 12 ms**, e a meta passa a ser cumprida **até 25 usuários**.
Acima disso o limite deixa de ser o banco e vira o **worker único** — com
`--workers 4` o p50 a 50 usuários cai de 940 ms para **58 ms**.

> As §§1–5 são o diagnóstico, escritas antes das correções; §6 e §7 são o que foi
> feito e o que cada passo rendeu. Os números de "antes" ficam de propósito: eles
> são a evidência de que o diagnóstico estava certo.

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

Dados brutos em `load/results/antes/` (antes da deduplicação) e
`load/results/depois/` — ver §6.

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

1. ~~**Não perguntar duas vezes.**~~ **Feito** — §6.
2. ~~**Carregar `cep_centroids` na memória.**~~ **Feito** — §7. Acabou substituindo
   o item 1 em vez de somar a ele.
3. **Paralelizar o ranking** com `asyncio.gather` — hoje os `await` são
   sequenciais. **Provavelmente não vale mais:** depois do item 2 as 24 chamadas
   de distância não tocam o banco, viraram aritmética. Medir antes de mexer.
4. **Redis, se ainda fizer falta.** Continua sem justificativa — ver §7.

**O que esta medição ainda não responde:** os itens 1–3 foram medidos
**sem concorrência**. Confirmar que eles levam o p95 sob carga para baixo de
200 ms exige implementá-los e rodar o Locust de novo — a suíte já está pronta
para isso.

---

---

## 6. Correção aplicada: a deduplicação (item 1)

Feita em `get_centroid` ([`repository.py`](../src/features/green_logistics/repository.py)) — um
memo em `session.info`, que nasce e morre com a requisição porque `get_db` abre
uma sessão por request. **Nenhuma assinatura mudou**, então Home, detalhe e
checkout ganharam junto: `get_centroid` era o ponto por onde todos passavam.

É seguro porque `cep_centroids` é dado de referência estático — escrito uma vez
pelo ETL, nunca em runtime. Dentro de uma requisição a resposta não pode mudar.

**Queries por requisição:**

| contexto | antes | depois |
|---|---|---|
| `default` | 15 (6 repetindo o CEP do comprador) | **10** (1) |
| `electronics_expert` | 15 (6) | **10** (1) |
| `conscious_buyer` | 63 (30) | **27** (1) |

**Latência com 1 usuário** (30 amostras, p50):

| endpoint | antes | depois | |
|---|---|---|---|
| `default` | 44 ms | 39 ms | −11% |
| `electronics_expert` | 84 ms | 37 ms | −56% |
| **`conscious_buyer`** | **150 ms** | **63 ms** | **−58%** |
| busca | 54 ms | 33 ms | −39% |

Bate com a previsão de −52% da §4, e o `conscious_buyer` saiu de 250 ms de p50
para dentro da meta sem concorrência.

### O que a correção NÃO resolveu

Sob carga o ganho é bem menor do que a medição isolada sugeria. p50 agregado:

| | u=1 | u=10 | u=25 | u=50 |
|---|---|---|---|---|
| `conscious_buyer` | 250 → 210 | 300 → **130** | 640 → **260** | 2200 → **1300** |
| **agregado** | 87 → 130 | 130 → 89 | 270 → 230 | **890 → 760** |
| throughput | 0,7 → 0,7 | 7,0 → 7,3 | 15,8 → 15,3 | 22,4 → **24,6** |

O endpoint que era o alvo melhorou de forma consistente (cai à metade de u=10
para cima). **Mas o agregado quase não se moveu e o throughput ficou praticamente
igual** — 22,4 → 24,6 req/s. A meta de 200 ms sob concorrência continua não sendo
cumprida.

> Os números de u=1 do Locust (87 → 130) são ruído: são ~30 requisições em 45 s,
> divididas entre 7 endpoints. A tabela de 30 amostras por endpoint acima é a
> medição confiável para um usuário.

**Por que o agregado não seguiu:** o N+1 não era o gargalo dominante sob carga.
Medindo as peças isoladas depois da correção:

| peça | p50 |
|---|---|
| `list_known_prefixes` (`SELECT` dos 6403 prefixos) | **15,0 ms** |
| `compose_home(default)` inteiro | 16,3 ms |
| `compose_home(conscious_buyer)` inteiro | 39,6 ms |

`list_known_prefixes` virou **48% de uma requisição `default`** — um custo fixo
pago em toda request só para validar se um prefixo existe, com 1 worker de uvicorn
serializando tudo. É o item 2 da §5, e agora ele é o maior item isolado.

Dados brutos do antes e do depois em `load/results/antes/` e `load/results/depois/`.

---

---

## 7. Correção aplicada: `cep_centroids` em memória (item 2)

A tabela inteira passa a viver no processo, carregada **preguiçosamente na
primeira consulta** — e não no startup, para a API continuar subindo sem depender
do Postgres estar de pé. Um `asyncio.Lock` garante que N requisições concorrentes
num processo frio disparem **uma** carga, não N.

O mesmo `dict` serve as duas perguntas que o sistema faz: `get_centroid` é uma
busca, `list_known_prefixes` são as chaves. Com isso o `SELECT` dos 6403
prefixos **desapareceu de toda requisição**.

Isto **substituiu** o memo por requisição do item 1, em vez de empilhar: com a
tabela em memória, `get_centroid` não faz I/O nenhum, e o memo de sessão viraria
um segundo `dict` na frente do primeiro.

**Queries por requisição, os três estados:**

| contexto | original | item 1 | **item 2** |
|---|---|---|---|
| `default` | 15 | 10 | **2** |
| `conscious_buyer` | 63 | 27 | **2** |

Só sobraram as duas buscas de dados reais — produtos e categorias.

**Latência com 1 usuário** (30 amostras, p50):

| endpoint | original | item 1 | **item 2** | |
|---|---|---|---|---|
| `default` | 44 ms | 39 ms | **15 ms** | −66% |
| `electronics_expert` | 84 ms | 37 ms | **14 ms** | −83% |
| **`conscious_buyer`** | **150 ms** | 63 ms | **12 ms** | **−92%** |
| busca | 54 ms | 33 ms | **12 ms** | −78% |

### Sob carga: a meta é cumprida até 25 usuários

p50 agregado, `original > item 1 > item 2`:

| | u=1 | u=10 | u=25 | u=50 |
|---|---|---|---|---|
| **p50** | 87 > 130 > **13** | 130 > 89 > **16** | 270 > 230 > **39** | 890 > 760 > **940** |
| p95 | 310 > 270 > 150 | 570 > 470 > **76** | 1100 > 1300 > **670** | 2500 > 1900 > 2000 |
| throughput | 0,7 > 0,7 > 0,8 | 7,0 > 7,3 > **7,9** | 15,8 > 15,3 > **19,4** | 22,4 > 24,6 > 23,6 |

**A meta de 200 ms passa a ser cumprida até 25 usuários** — p50 de 39 ms, contra
270 ms no começo. Mas a 50 usuários **nada mudou**: 940 ms de p50 e throughput
preso em ~23 req/s, igual a antes de qualquer correção.

### A 50 usuários o gargalo não é mais o banco

Ir de 63 para 2 queries não mexeu no resultado de u=50. Isso é o bastante para
descartar o banco como causa. O suspeito seguinte era o **worker único** — um
processo Python, um core. Testado trocando só isso:

| 50 usuários | 1 worker | **4 workers** |
|---|---|---|
| p50 | 940 ms | **58 ms** |
| p95 | 2000 ms | 800 ms |
| throughput | 23,6 req/s | **37,2 req/s** |
| falhas | 0 | 0 |

**p50 de 940 ms para 58 ms sem tocar em uma linha de código.** O limite era o
processo único saturando.

> **Por que o throughput de u=25 não subiu junto:** com `wait_time` de 0,5 a 2 s,
> 25 usuários geram no máximo ~20 req/s **por construção**. Ali o teste é limitado
> pela demanda, não pela capacidade — por isso 19,4 req/s com 1 worker e 18,9 com
> 4. O gargalo real só aparece em u=50, onde a demanda passa de 40 req/s.

### O que continua em aberto

- **p95 sob carga.** Mesmo com 4 workers, o p95 a 50 usuários é 800 ms. Parte
  disso é o Locust disputando CPU com a API na mesma máquina; separar cliente e
  servidor é o próximo passo para uma medição limpa.
- **Redis continua sem justificativa.** Com 4 workers há 4 cópias do `dict`
  (~4,4 MB), o que continua desprezível. Redis resolveria a duplicação, não a
  latência — e cobraria um salto de rede por isso.
- **Escolher o número de workers** é uma decisão de deploy, não de código. O
  comando da §1 usa 1 worker; para carga real, `--workers`.

Dados brutos em `load/results/memoria/` e `load/results/memoria-4workers/`.

---

*Medição da Sprint 6. Suíte em `load/locustfile.py`; dados em `load/results/`.*
