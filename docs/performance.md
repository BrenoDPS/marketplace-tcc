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

## 8. Sprint 7 — a medição das §§1–7 tinha um defeito de validade

**Tudo acima foi medido com DOIS CEPs fixos** (`05311` e `60165`) e com
`wait_time` de 0,5 a 2 s. Os dois pontos são problema:

| defeito | consequência |
|---|---|
| 2 CEPs fixos | o espaço de chaves é ficcional: qualquer cache teria ~100% de acerto **por construção**, e a §7 conclui contra o Redis sem nunca ter medido um |
| think time 0,5–2,0 s | a §3.3 da metodologia declara **1 a 3 s** — o texto do TCC e o código diziam coisas diferentes |

Corrigido em `load/locustfile.py`: os CEPs saem agora de `olist_customers`, na
proporção real (**53.114 clientes, 12.809 prefixos distintos**), e cada usuário
virtual sorteia um CEP e o mantém pela jornada inteira, que é o que uma pessoa
faz. `wait_time` passou a `between(1, 3)`.

**A distribuição real é quase plana**: os 100 prefixos mais frequentes somam
**6,5% do tráfego**. Um cache com chave por CEP não tem muito o que reaproveitar —
registrado aqui *antes* de rodar o experimento de Redis, para que a previsão
possa ser conferida contra o resultado.

### Linha de base nova (50 VU, 60 s, 1 worker)

| | valor |
|---|---|
| p50 agregado | **16 ms** |
| p95 agregado | 140 ms |
| p99 agregado | **470 ms** |
| throughput | 24,8 req/s |
| falhas | 0 de 1.490 |

A meta de 200 ms é cumprida no p50 e no p95, e **não** no p99. O throughput caiu
em relação à Sprint 6 porque o think time subiu: 50 usuários com pausa de 1–3 s
geram ~25 req/s por construção, não por limite do servidor.

> :warning: **Estes números ainda saem de uma API com `echo` do SQLAlchemy
> ligado** — o confundidor só apareceu na §9, que traz a linha de base limpa
> (p50 14 ms, p95 210 ms, p99 650 ms). A comparação com/sem selo abaixo continua
> válida: o `echo` estava nos dois lados.

### O selo não custa nada

O perfil "com selo / sem selo" agora **emerge** do CEP real de cada usuário, em
vez de vir de dois CEPs escolhidos a mão:

| | p50 | p95 | # reqs |
|---|---|---|---|
| Home com selo | 14 ms | 67 ms | 230 |
| Home sem selo | 15 ms | 78 ms | 272 |

Montar o selo é indistinguível do ruído. A suspeita antiga de que o selo era
caro fica descartada — o custo estava no N+1 de centroides, já corrigido na §6.

> **Achado lateral, relevante para o texto do TCC:** 54% das requisições caíram no
> perfil *sem selo* — com a distribuição real de clientes, **a maioria dos
> compradores não tem nenhum vendedor próximo na amostra**. Isso não é defeito da
> medição, é o retrato da concentração logística brasileira, e merece virar número
> no capítulo 5.

Dados brutos em `load/results/s7-ceps-reais/`.

---

## 9. Redis entra como variável de experimento (sondagem, não o protocolo)

`src/core/cache.py`, atrás de `CACHE_ENABLED` (padrão **desligado**). O que é
cacheado é o **JSON já serializado** da Home; numa batida os bytes voltam sem
reconstruir o modelo, porque revalidar só para re-serializar cobraria do cache
um custo que ele não tem na prática.

**Frio e aquecido não viraram modos de código** — são procedimento de ensaio:

| condição | como se produz |
|---|---|
| desabilitado | `CACHE_ENABLED=false` |
| frio | `CACHE_ENABLED=true` + `docker exec olist-redis redis-cli FLUSHALL` |
| aquecido | `CACHE_ENABLED=true` + as chaves do ensaio anterior |

### Antes dos números: um confundidor que estava em TODAS as medições

`src/core/database.py:8` liga o `echo` do SQLAlchemy ao flag `DEBUG`, que é
`True` por padrão. **Toda medição das §§1–8 foi feita com a API imprimindo cada
SQL executado.** As primeiras sondagens do cache também, até isso aparecer —
numa delas o log bloqueou o event loop o bastante para o cliente Redis estourar
o timeout e devolver 28 respostas 500.

Os números abaixo são os primeiros medidos com `DEBUG=false`. Comparações
internas às §§1–8 continuam válidas (o confundidor estava nos dois lados), mas
**nenhum valor absoluto daquelas seções descreve a aplicação em produção**.

### Sondagem limpa — 1 ensaio de 60 s por condição, 50 VU, 1 worker

| | cache off | cache frio |
|---|---|---|
| p50 agregado | 14 ms | **7 ms** |
| p95 agregado | 210 ms | **75 ms** |
| p99 agregado | 650 ms | **400 ms** |
| throughput | 24,7 req/s | 25,3 req/s |
| taxa de acerto | — | **77,2%** (880 de 1.140) |
| falhas | 0 de 1.492 | 0 de 1.520 |

Por rota, p50:

| rota | off | frio | |
|---|---|---|---|
| Home (default, sem selo) | 14 ms | **5 ms** | cacheada |
| Home (default, com selo) | 13 ms | **5 ms** | cacheada |
| Home (`conscious_buyer`) | 15 ms | **6 ms** | cacheada |
| `GET /products/{id}` | 8 ms | 7 ms | **não cacheada** |
| `POST /checkout/simulate` | 20 ms | 18 ms | **não cacheada** |

As duas últimas são o **controle interno**: não passam pelo cache e quase não se
moveram. A queda das rotas de Home é o cache, não deriva entre execuções.

### O que esta sondagem mostra — e o que ela não pode mostrar

**A mediana cai pela metade, e desta vez a cauda também melhora.** Uma sondagem
anterior, ainda com `echo` ligado, tinha dado o contrário (p99 de 470 para
550 ms) e eu havia concluído que "Redis compra mediana, não cauda". **Com a
medição limpa, a conclusão não se sustenta** — o p99 caiu de 650 para 400 ms.

**Mas um ensaio por condição não decide a cauda.** Duas execuções da MESMA
condição "cache off" deram p95 de 140 e 210 ms. A mediana é estável entre
execuções; a cauda não é. É exatamente por isso que o protocolo da §3.3 pede
**três repetições** — sem elas, qualquer afirmação sobre p95/p99 está dentro do
ruído.

**A previsão que eu registrei antes de medir estava errada, e o motivo importa.**
O card previa pouco reaproveitamento porque a distribuição de CEPs é quase plana
(os 100 prefixos mais frequentes são 6,5% do tráfego). Deu 77% de acerto. A razão
está declarada no próprio `locustfile`: cada usuário virtual **mantém seu CEP
pela jornada inteira**, então o espaço de chaves ativo é da ordem do número de
VUs (203 chaves para 50 usuários), não dos 12.809 prefixos. A previsão descrevia
a **população**; quem decide a taxa de acerto é a **sessão**.

> Previsão falsificável para o protocolo, escrita antes dos ensaios: se a taxa de
> acerto é governada pelo número de VUs, os cenários de 250 e 1.000 VU devem dar
> taxa **menor**, não maior — o oposto do que "mais carga, mais cache" sugere.
>
> **Substituída pela §10.9** (Sprint 8): foi escrita sob TTL de 60 s; com o TTL
> de 3600 s do protocolo, a taxa passa a depender da duração do ensaio.

**Isto não decide nada ainda.** Um ensaio por condição, um worker, Locust na
mesma máquina. A decisão sobre Redis depende dos 27 ensaios do protocolo.

### De quebra: 0,54 ms por requisição que o cache não alcançava

`list_known_prefixes` fazia `set()` de 12.809 strings a cada requisição para
responder a um `in` que custa 0,06 µs — dez mil vezes o preço da pergunta. Pior:
a validação acontece **antes** do cache, então era um piso que cache nenhum
derruba. Passou a devolver a visão das chaves. Com o p50 cacheado em 5 ms, eram
~10% do tempo de resposta.

Dados brutos em `load/results/s7-limpo-off/` e `load/results/s7-limpo-frio/`. As
sondagens com `echo` ligado ficaram em `s7-redis-frio/` e `s7-redis-frio-sem-copia/`
como evidência do confundidor.

---

## 10. Sprint 8 — preparação do protocolo: três defeitos de validade e o piloto

Antes de gastar ~4 h 40 min nos 27 ensaios, a pergunta foi: **o protocolo, como
estava, mede o que diz medir?** Não media. Três defeitos, nenhum visível no
número final — o mesmo padrão dos dois CEPs fixos e do `echo` ligado.

### 10.1 Os defeitos e a correção

| # | Defeito | Efeito no resultado | Correção |
|---|---|---|---|
| 1 | `CACHE_TTL_SECONDS = 60` (`src/core/config.py`) | "Aquecido" é definido como *as chaves do ensaio anterior*; com plateau de 10 min elas expiram no 1º minuto. Frio e aquecido convergem para o mesmo estado estacionário — **9 dos 27 ensaios mediriam a mesma coisa que outros 9**. | `--ttl` no runner, padrão 3600 s (decisão do autor; ver handoff da Sprint 8) |
| 2 | CEP sorteado com `random.choice` **sem semente** | O aquecido sorteia **outros** compradores: as chaves que o frio deixou quase não são pedidas. A condição não existia na prática. Além disso, as condições comparavam populações diferentes. | `LOAD_SEED` no `locustfile` (RNG só do CEP, `ORDER BY` na consulta); o runner usa a mesma semente nas 3 condições de uma carga → **comparação pareada** |
| 3 | `DEBUG=True` por padrão liga o `echo` (§9) | 27 reinícios manuais da API = 27 chances de medir com log de SQL | o runner sobe a API com `DEBUG=false` sempre |

Também entraram no runner (`load/protocolo.py`): `--reset-stats` (o CSV é só o
plateau — a rampa de 1.000 VU seriam 10 s de setup na conta), API reiniciada a
cada ensaio (nenhuma condição herda processo de outra), ordem das cargas
sorteada por repetição (deriva da máquina ao longo de horas não vira diferença
entre condições) e taxa de acerto do Redis por ensaio (`CONFIG RESETSTAT` antes,
`INFO stats` depois → `*_redis.txt`).

### 10.2 Smoke do runner — verificação funcional, não dado

50 VU, plateau de **15 s**, uma execução por condição, mesma semente:

| | off | frio | aquecido |
|---|---|---|---|
| p50 agregado | 16 ms | 11 ms | **8 ms** |
| requisições | 395 | 395 | 402 |

Serve para uma coisa só: com a semente, **aquecido < frio**, ou seja, a condição
agora existe. 15 s não sustentam nenhuma comparação de latência.

### 10.3 Piloto — 1.000 VU, cache off, 1 worker, plateau de 120 s

Dados: `load/results/s8-piloto-u1000-off/u1000_stats.csv`.

| rota | n | falhas | p50 | p95 | p99 | máx |
|---|---|---|---|---|---|---|
| Home (default, sem selo) | 4.433 | 4 | 3,9 s | 12 s | 18 s | 30,1 s |
| Home (default, com selo) | 2.297 | 1 | 3,8 s | 12 s | 19 s | 30,1 s |
| Home (`conscious_buyer`) | 2.592 | 0 | 3,8 s | 12 s | 18 s | 27,5 s |
| Home (`electronics_expert`) | 2.503 | 0 | 3,8 s | 12 s | 17 s | 29,2 s |
| Home (busca) | 2.544 | 1 | 3,8 s | 12 s | 18 s | 30,1 s |
| `GET /products/{id}` | 3.156 | 1 | 3,8 s | 12 s | 18 s | 31,5 s |
| `POST /checkout/simulate` | 2.092 | 1 | 3,9 s | 12 s | 19 s | 30,2 s |
| **agregado** | **19.972** | **8** | **3,9 s** | **12 s** | **18 s** | 31,5 s |

Throughput **162,9 req/s**. O Locust **não** emitiu aviso de CPU — o gerador
aguenta 1.000 VU nesta máquina (8 núcleos).

### 10.4 Avaliação do piloto

**O sistema está saturado, e a medição é coerente.** Pela Lei de Little num
sistema fechado, `N = X · (R + Z)`: com N = 1.000 VU, X = 162,9 req/s e think
time médio Z = 2 s, o tempo de resposta implicado é R ≈ 4,1 s. O medido foi
4,04 s de média. O número não é artefato do gerador: é o regime de fila.

**A latência é a da fila, não a da rota.** Todas as rotas têm o mesmo p50
(3,8–3,9 s) — inclusive `/products` e `/checkout`, que custam 8 e 20 ms a 50 VU
(§9). Rotas de custo tão diferente só convergem quando a espera domina o serviço.

**Onde a fila aparece: o pool de conexões.** O máximo de **toda** rota fica em
~30 s, que é exatamente o `timeout` do `QueuePool` do SQLAlchemy (5 + 10
conexões, 30 s). As 8 falhas (0,04%) são esse timeout virando 500. **O que não dá
para afirmar ainda:** se o pool é a causa ou só o lugar onde a espera aparece. Com
um único event loop saturando a CPU, cada requisição segura a conexão por mais
tempo, e o pool esgota como consequência. Separar as duas coisas exige medir a CPU
do processo da API durante o ensaio — não medido.

**Capacidade estimada de 1 worker sem cache: ~160 req/s.** A demanda de cada
carga, com Z = 2 s e R pequeno, é ≈ N / 2:

| carga | demanda | utilização estimada | regime esperado |
|---|---|---|---|
| 50 VU | ~25 req/s | ~15% | folga — confere com o §9 (p50 14 ms) |
| 250 VU | ~125 req/s | **~75–80%** | **joelho da curva**: a cauda deve subir muito antes da mediana |
| 1.000 VU | ~500 req/s | >100% | saturação — confirmado acima |

> **Previsão registrada antes do protocolo, derivada do piloto:** a 250 VU, com o
> cache desligado, o p95/p99 sobe desproporcionalmente ao p50; é a carga em que o
> cache deve fazer **mais** diferença relativa, porque tira a Home (~74% das
> requisições) da disputa pelo pool. A 1.000 VU, o cache não deve tirar o sistema
> da saturação com 1 worker, porque `/products` e `/checkout` não são cacheadas e
> continuam disputando o mesmo pool.

### 10.5 Pontos de melhoria

| Ponto | Por que importa | Estado |
|---|---|---|
| Medir CPU do processo da API por ensaio | separar "event loop saturado" de "pool esgotado" (§10.4); a §3.3 promete "o ponto de esgotamento da CPU" | **aplicado** — `_cpu.csv` por ensaio; resultado em §10.8 |
| Agregação dos 27 CSVs em tabela | a §3.3 pede média e desvio padrão por métrica | **aplicado** — `python -m load.resumo` |
| Catálogo de metadados por execução | a §3.3 exige commit, imagens Docker, volume de dados e locustfile | **aplicado** — `meta.json`; o runner recusa árvore com mudança não commitada |
| `DEBUG=false` como padrão | o defeito 3 só some para medições **manuais** se o padrão mudar | aberto — muda o log de desenvolvimento; decisão à parte |
| Taxa de acerto inclui a rampa | `CONFIG RESETSTAT` roda antes da subida da API | aberto — efeito pequeno com plateau de 5–15 min; declarar |
| Locust e API na mesma máquina | sem aviso de CPU no piloto, mas disputam núcleos com Postgres e Redis | aberto — declarar como limitação (ver §10.7) |

### 10.6 Decisões fechadas pelo autor (2026-10-02)

TTL de **3600 s** durante o protocolo; **1 worker** nos três cenários, com o
cenário de 1.000 VU declarado como **saturação**; **pool mantido** em 5 + 10, com
falhas reportadas como resultado. Detalhe e alternativas descartadas em
`docs/sprint8-handoff.md`.

### 10.7 O runner contra o texto da §3.3

| §3.3 diz | Implementação | Situação |
|---|---|---|
| 50 / 250 / 1.000 VU; spawn 5 / 10 / 25 VU/s; rampa 10 / 25 / 40 s; plateau 5 / 10 / 15 min | `CENARIOS` em `load/protocolo.py` (Tabela 1) | conforme |
| think time de 1 a 3 s | `between(1, 3)` | conforme |
| triplicata × {desabilitado, frio, aquecido} | `--reps 3`, ordem off → frio → aquecido por cenário | conforme |
| aquecido "condicionado por um ciclo prévio de requisições de carga (pre-warming)" | o ensaio frio, com a mesma semente de CEP, é o pré-aquecimento | conforme — texto complementado em `docs/tese-rastreabilidade.md` §5.3 |
| p50, p95, p99; RPS × percentis; ponto de inflexão | `_stats.csv` (plateau) e `_stats_history.csv` (série temporal) | conforme — gráficos a fazer na escrita |
| falhas segregadas por código HTTP (500, 503, 504) | `load.resumo`, coluna "falhas por código" | conforme — sem proxy na frente, a API não emite 503/504: espera-se 500 (timeout do pool) e erro de conexão |
| média e desvio padrão das três iterações | `load.resumo` | conforme — com n = 3 o desvio é frágil; manter os valores individuais nos anexos |
| metadados: commit, imagens Docker, volume de dados, locustfile | `meta.json` | conforme |
| carga "sobre o endpoint responsável pela orquestração da SDUI e pelo cálculo de pegada" | a jornada inteira: 4 formatos de Home, detalhe e checkout | **texto ajustado** — `docs/tese-rastreabilidade.md` §5.2; as linhas por rota isolam a Home (`--rota`) |
| contêineres da aplicação, do banco e do Locust numa sub-rede *bridge* isolada | Postgres e Redis em contêiner; API e Locust no host, via *loopback* | **texto ajustado** (decisão 6, 2026-10-03) — redação em `docs/tese-rastreabilidade.md` §5.1 |

### 10.8 É possível alcançar os cenários? Capacidade de 1 worker

A premissa *"com 25 usuários a API já bate o limite"* vem da Sprint 6 (§7) e
**não vale mais**: aquela medição tinha o `echo` ligado, think time de 0,5–2 s e
dois CEPs fixos. Com a medição limpa (§9), 50 VU deram p50 de 14 ms.

Duas estimativas **independentes** da capacidade de 1 worker, sem cache:

| fonte | como | capacidade |
|---|---|---|
| piloto a 1.000 VU (§10.3) | throughput no regime saturado | **~163 req/s** |
| smoke a 50 VU, 2 × 20 s (`load/results/s8-smoke-u50/`) | CPU da API ≈ 14% de um núcleo a 25 req/s → ~5,6 ms de CPU por requisição | **~180 req/s** |

Batem. O limite é **a CPU do event loop único**; o pool é onde a espera aparece
(§10.4). Com cache aquecido o smoke deu ~9% de CPU para a mesma vazão (~3,6 ms
por requisição) → **~280 req/s**. *Ressalva:* o smoke é curto e de baixa
utilização; o custo por requisição tende a subir sob contenção, então os tetos
são otimistas.

Demanda de cada cenário (sistema fechado, Z = 2 s → ≈ VU / 2):

| cenário | demanda | utilização sem cache | com cache | leitura |
|---|---|---|---|---|
| 1 — nominal, 50 VU | ~25 req/s | ~15% | ~9% | folga; meta de 200 ms cumprida no p50 |
| 2 — operacional, 250 VU | ~125 req/s | **~70–77%** | ~45% | **joelho da curva** sem cache; o cache deve tirá-lo de lá |
| 3 — estresse, 1.000 VU | ~500 req/s | **>100%** | >100% | saturação nas três condições |

**Resposta:** os três cenários **são executáveis** nesta máquina (o Locust
sustentou 1.000 VU sem aviso de CPU). O que **não** acontece é o cenário 3 caber
em 200 ms com 1 worker — e a §3.3 não promete isso: o objetivo declarado do
cenário 3 é *"identificar o ponto de esgotamento da CPU, a formação de filas e a
taxa de erros"*. Saturar é o resultado esperado; o achado é **onde** e **como**.
Para servir ~500 req/s sem fila seriam necessários ~3 workers sem cache ou ~2 com
cache — mudança de desenho descartada na decisão do autor (§10.6). Se quiser o
dado, cabe como ensaio **complementar**, fora dos 27.

### 10.9 Previsões registradas antes do protocolo (TTL 3600 s)

Substituem a previsão do §9, escrita sob TTL de 60 s.

1. **Taxa de acerto do frio ≥ ~93% nos três cenários; aquecido ≥ ~99%.** Com
   TTL longo, cada chave erra **uma vez** e acerta até o fim. Cada VU usa ~7
   chaves de Home (default, dois contextos, quatro termos de busca) e faz
   ~115 (cenário 1) a ~230 (cenários 2 e 3) requisições de Home no ensaio. A taxa
   passa a depender da **duração do ensaio**, não do número de VUs — a previsão
   do §9 (taxa menor com mais VUs) deixa de se aplicar.
2. **No agregado do plateau, frio e aquecido ficam próximos.** A penalidade das
   rajadas de *cache miss* — o que a §3.3 quer medir no frio — acontece no
   primeiro minuto, boa parte durante a rampa, que o `--reset-stats` exclui do
   `_stats.csv`. **Ela tem de ser lida na série temporal** (`_stats_history.csv`),
   comparando o início do frio com o do aquecido.
3. **Cenário 2 sem cache: p95/p99 sobem muito mais que o p50**, e a CPU da API
   fica acima de ~70%. Com cache, o p95 cai mais em termos relativos aqui do que
   em qualquer outro cenário.
4. **Cenário 3: CPU da API em ~100% de um núcleo nas três condições.** O cache
   eleva o teto de vazão (de ~165 para algo entre 200 e 280 req/s) e reduz os
   timeouts do pool, mas não tira o sistema da saturação: `/products` e
   `/checkout` não são cacheadas.

---

## 11. Primeira execução do protocolo (2026-10-03) — resultado parcial

**Status: incompleto.** Os 27 ensaios rodaram, mas **13 deles rodaram em
bateria** e não valem como medida. As conclusões abaixo usam só os 14 ensaios
feitos na tomada; as repetições 2 e 3 precisam ser refeitas para fechar a
triplicata. Dados brutos em `load/results/protocolo/`.

### 11.1 Execução

| | |
|---|---|
| Início / fim | 18:37 / 23:27; reexecução de `r3-u1000-frio` 23:28–23:44 |
| Commit medido | `f15f8a1` (`meta.json`); reexecução em `748090c` — só runner e resumo mudaram, aplicação e locustfile idênticos |
| Dados no Postgres | 53.114 clientes, 7.356 ofertas, 12.933 centroides, 60.292 `order_items` |
| Ambiente | Windows 11, 8 núcleos lógicos, 7,9 GB; Postgres 16.15 e Redis 7.4.11 em contêiner; API e Locust no host |
| Ensaio invalidado pelo gerador | `r3-u1000-frio`: aviso de CPU do Locust no minuto ~14 de 15,7 (com o sistema em colapso, 10,3% de falhas). Reexecutado com a mesma semente; o original está em `protocolo/invalidado/` |

### 11.2 O confundidor: o notebook saiu da tomada

`powercfg /batteryreport` (`load/results/protocolo/energia.txt`): o notebook
saiu da tomada às **20:24:41** e só voltou às **22:57:31, com 2% de bateria** —
a execução quase terminou com a máquina desligando. Em bateria o Windows reduz o
clock da CPU.

**A prova está nos próprios dados**: o tempo de CPU que a API gasta por
requisição, com a mesma carga, triplicou. Carga de outros processos não muda o
tempo de CPU de um processo; clock menor muda.

| 50 VU, cache off (~25 req/s) | CPU da API | CPU por requisição | p50 |
|---|---|---|---|
| r1 — 18:37, tomada | 17% | ~6,8 ms | 13 ms |
| r2 — 20:13, tomada | 15% | ~6,0 ms | 12 ms |
| **r3 — 21:48, bateria** | **54%** | **~23,5 ms** | **60 ms** |

Todos os 13 ensaios da janela mostram o mesmo padrão; os de antes e de depois,
não. **Correção de uma leitura feita durante a execução:** a "bimodalidade" do
cenário de 1.000 VU com cache — uma repetição sustentando 400 req/s, outra
colapsando — era a bateria. Na tomada, as três execuções com cache a 1.000 VU dão
p50 de 86, 97 e 100 ms e 380–411 req/s.

### 11.3 Resultados — só ensaios na tomada

`python -m load.resumo` sobre os 14 ensaios na tomada
(`load/results/protocolo/resumo-tomada.md`). Latências em ms; média ± desvio
padrão quando n ≥ 2.

| VU | cache | n | p50 | p95 | p99 | req/s | falhas | acerto | CPU API |
|---|---|---|---|---|---|---|---|---|---|
| 50 | off | 2 | 12,5 ± 0,7 | 36,5 ± 6,4 | 52 ± 10 | 24,8 | 0% | — | 16% |
| 50 | frio | 2 | 6,5 ± 0,7 | 23,5 ± 2,1 | 43 ± 7 | 24,9 | 0% | 93,9% | 10% |
| 50 | aquecido | 1 | 6 | 20 | 34 | 24,9 | 0% | 100% | 9% |
| 250 | off | 1 | **170** | **630** | 1.100 | **111** | 0% | — | **90%** |
| 250 | frio | 2 | 5,5 ± 0,7 | 29,5 ± 7,8 | 165 ± 35 | 124 | 0% | 96,9% | 33% |
| 250 | aquecido | 2 | 5,5 ± 0,7 | 24,5 ± 0,7 | 79 ± 21 | 124 | 0,02% | 100% | 29% |
| 1.000 | off | 1 | **4.500** | 16.000 | 26.000 | **139** | 0,5% | — | 94% |
| 1.000 | frio | 2 | **93 ± 10** | 3.050 ± 919 | 6.800 ± 1.697 | **396 ± 22** | 0,1% | 97,6% | 97% |
| 1.000 | aquecido | 1 | 97 | 3.400 | 9.000 | 381 | 0,2% | 100% | 95% |

Falhas por código HTTP (1.000 VU): sem cache, 0,49% de 500 e 0,01% de conexão
derrubada pelo servidor; com cache, 0,13–0,15% de 500. **Nenhum 503/504** — sem
proxy na frente, a API não os emite (§10.7).

**De onde vêm os 500** (`execucao-erros-resumo.txt`, stderr da API): sem cache,
do **pool do Postgres** (`QueuePool limit of size 5 overflow 10`, 30 s); com
cache, do **pool do cliente Redis** — na reexecução de `r3-u1000-frio`, 823
`MaxConnectionsError` contra 6 timeouts do Postgres. O redis-py 8.1 limita o pool
assíncrono a **100 conexões** e falha na hora, sem fila; o `cache.py` não tem
fallback por desenho. É um segundo parâmetro de configuração do experimento,
mantido no padrão como o do Postgres (decisão 4) e declarado no texto.

### 11.4 Leitura

**Cenário 1 (50 VU) — a meta de 200 ms é cumprida com folga nas três
condições.** O cache corta o p50 pela metade (12,5 → 6 ms) e a CPU da API de 16%
para ~9%. Em carga nominal, cache é otimização, não necessidade.

**Cenário 2 (250 VU) — onde o cache decide.** Sem cache, a API **já está
saturada**: CPU em 90%, vazão de 111 req/s **abaixo** da demanda (~125 req/s —
os usuários esperam na fila em vez de pedir), p95 de 630 ms, acima da meta. Com
cache, o mesmo hardware atende toda a demanda (124 req/s) com p50 de 5,5 ms, p95
de 25–30 ms e CPU em ~31%. É a maior diferença relativa do protocolo: **p50 ÷ 31,
p95 ÷ 23, CPU ÷ 3**.

**Cenário 3 (1.000 VU) — saturação nas três condições, mas não a mesma.** A CPU
da API fica em 94–97% em todas. Sem cache, o sistema entra em fila: p50 de 4,5 s
e 139 req/s. Com cache, a vazão **quase triplica** (380–411 req/s) e o p50 cai
para ~95 ms — mas a cauda continua saturada (p95 de 3–3,4 s, p99 de 7–9 s). O
cache não tira o sistema da saturação; **desloca o ponto de saturação**.

**Frio × aquecido — a penalidade dos misses é transitória.** No agregado do
plateau os dois são indistinguíveis. A diferença está no começo, e aparece na
série temporal (`r1-u250-*_stats_history.csv`):

| 250 VU, janela do Locust | t = 10 s | t = 30 s | t = 60 s | t = 120 s | t = 300 s |
|---|---|---|---|---|---|
| frio — p50 / p95 (ms) | 93 / 630 | 40 / 410 | 21 / 390 | 12 / 200 | 8 / 55 |
| aquecido — p50 / p95 (ms) | 12 / 73 | 6 / 20 | 5 / 17 | 5 / 16 | 5 / 18 |

O frio leva **2–3 minutos** para convergir; o aquecido já começa no regime.

### 11.5 As previsões da §10.9, contra os dados na tomada

| # | Previsão | Resultado |
|---|---|---|
| 1 | Acerto frio ≥ ~93%, aquecido ≥ ~99% | **Confirmada** — frio 93,9 / 96,9 / 97,6%; aquecido 100 / 100 / 100% |
| 2 | Frio ≈ aquecido no agregado; a penalidade está na série do 1º minuto | **Confirmada** — e dura 2–3 min, não 1 (§11.4) |
| 3 | 250 VU sem cache: p95/p99 sobem muito mais que o p50 | **Parcialmente refutada** — a 250 VU o sistema já passou do joelho: o p50 também sobe (170 ms) e a vazão fica abaixo da demanda. A capacidade de 1 worker (estimada em 165–180 req/s na §10.8) é **menor**: ~111–139 req/s sob carga. A outra metade — "o cache faz a maior diferença relativa a 250 VU" — **confirmada** |
| 4 | 1.000 VU: CPU ~100% nas três condições; o cache eleva o teto para 200–280 req/s, sem tirar da saturação | CPU e saturação da cauda: **confirmadas**. Teto: **refutado na magnitude** — 380–411 req/s, não 200–280. A estimativa veio de 20 s de smoke a 50 VU e superestimou o custo de CPU de um acerto de cache |

### 11.6 O que falta

- **Refazer as repetições 2 e 3 na tomada** (`python -m load.protocolo --rep 2 3`, ~3 h 15 min) para fechar n = 3 em todas as células. O runner agora recusa começar ensaio fora da tomada e invalida o que perder a tomada no meio.
- **Decisão sobre o Redis**: depende das triplicatas. A leitura provisória (§11.4) é que o cache é desnecessário em carga nominal e decisivo a partir de ~250 VU com 1 worker.
- Gráficos de evolução temporal e de dispersão RPS × percentis (§3.3) — a fazer na escrita, a partir dos `_stats_history.csv`.
- O stderr bruto da API (351 MB, um traceback por timeout) fica fora do git; a contagem por tipo de exceção está em `execucao-erros-resumo.txt`. O `meta.json` passa a registrar as versões das bibliotecas (o limite de 100 conexões é do redis-py 8).

---

*§§1–7: Sprint 6. §§8–9: Sprint 7. §§10–11: Sprint 8. Suíte em `load/locustfile.py`; runner em `load/protocolo.py`; dados em `load/results/`.*
