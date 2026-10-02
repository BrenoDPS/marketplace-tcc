# Handoff — Sprint 8: o protocolo de carga da §3.3

> **Para agentes sem contexto:** leia `AGENTS.md` primeiro, depois este arquivo.
> Sprints 1–7 **já estão implementadas**.

## Objetivo

Executar os **27 ensaios** do protocolo da §3.3 da metodologia (3 condições de
cache × 3 cargas × 3 repetições) e **fechar a decisão sobre o Redis** com
números que sobrevivam à banca. Nada de feature nova no produto nesta sprint.

## Estado de partida

| Fato | Prova |
|---|---|
| O runner existe e fixa os defeitos de validade conhecidos: `DEBUG=false`, TTL longo, mesma semente de CEP nas três condições de uma carga, `--reset-stats`, ordem intercalada, taxa de acerto por ensaio | `python -m load.protocolo --help`; docstring de `load/protocolo.py` |
| Smoke a 50 VU (15 s, não é dado): p50 off 16 · frio 11 · aquecido 8 ms — o aquecido agora difere do frio | rodado em 2026-10-02, descartado |
| **Piloto a 1.000 VU, cache off, 1 worker, 120 s:** p50 **3,9 s**, p99,9 26 s, 163 req/s; **8 respostas 500** por `QueuePool limit of size 5 overflow 10 reached`; o Locust **não** saturou a CPU | `load/results/s8-piloto-u1000-off/u1000_stats.csv` |

O piloto responde duas perguntas: o gerador de carga aguenta 1.000 VU nesta
máquina; e a 1.000 VU com 1 worker a API está **saturada** — o que se mede ali é
fila, não cache.

## Decisões a fechar ANTES do primeiro ensaio (autor)

| # | Decisão | Recomendação |
|---|---|---|
| 1 | **TTL do cache.** O padrão é 60 s: a condição "aquecido" (chaves do ensaio anterior) vira "frio" 1 min depois de começar, e o "frio" vira estado estacionário. | `--ttl 3600` (padrão do runner). O catálogo só muda com o ETL, então TTL longo é o realista. |
| 2 | **A previsão do §9** ("250 e 1.000 VU dão taxa de acerto menor") foi escrita sob TTL 60 s. Com TTL longo, cada chave erra uma vez e acerta até o fim — a taxa passa a depender da **duração do ensaio**, não do nº de VUs. | Reescrever a previsão sob o TTL escolhido e commitar **antes** de medir. |
| 3 | **1.000 VU com 1 worker é saturação** (piloto). | Manter 1 worker e declarar o cenário como saturação: a pergunta a 1.000 VU passa a ser *"o cache desloca o ponto de saturação?"*. Trocar o nº de workers muda as três cargas e invalida a sondagem do §9 como comparação. |
| 4 | **Pool de conexões (5 + 10)**: no off a 1.000 VU as falhas são timeout do pool, não erro da aplicação. | Manter — é a configuração real — e reportar falhas como resultado, separadas da latência. |
| 5 | **Cargas 50/250/1.000 e plateau de 600 s** foram derivados de "27 ensaios", "~4,5 h de plateau" e da previsão do §9. | Conferir com o texto da §3.3; o runner aceita `--cargas` e `--plateau`. |

Tempo real: 27 × (600 s + ~20 s de rampa e subida da API) ≈ **4 h 40 min**.

## Critérios de aceite

- [ ] Decisões 1–5 registradas nesta tabela → leitura
- [ ] Previsões commitadas antes dos resultados → `git log --oneline -- docs/performance.md`
- [ ] 27 ensaios completos → `ls load/results/protocolo/*_stats.csv | wc -l` = 27
- [ ] Nenhum ensaio com o gerador saturado → `grep -l "CPU usage above" load/results/protocolo/*.log` vazio
- [ ] `docs/performance.md` §11: por célula (condição × carga), mediana e amplitude das 3 repetições de p50/p95/p99, throughput, falhas e taxa de acerto (`*_redis.txt`)
- [ ] Decisão sobre o Redis escrita no README, no `tech_spec.md` e na regra "Redis" do `AGENTS.md` → `pytest -q`

## Fora de escopo

`--workers` em produção · PostGIS · dataset completo · E2E no CI · `orchestrator` ·
mudar `DEBUG` para `false` por padrão (o runner já força; mudar o padrão é decisão
à parte).

## Pendência herdada — fechar como obsoleta

`docs/snapshots/depois.json` nunca foi gerado. O diff exigia a **mesma amostra**
dos dois lados, e o ETL mudou depois do `antes.json` (`428118a` completa as
ofertas), então um `depois.json` gerado hoje diferiria por desenho. Registrar
como não realizável no `scripts/snapshot_api.py` em vez de gerá-lo.

## Falhas encontradas e o que virou regra

| Falha | Virou |
|---|---|
| TTL de 60 s anulava a condição "aquecido" | `--ttl` no runner, padrão 3600 |
| CEP sorteado sem semente: o aquecido media outros compradores | `LOAD_SEED` no `locustfile` |
| `DEBUG=True` por padrão liga o `echo` em toda medição manual | o runner força `DEBUG=false` |
