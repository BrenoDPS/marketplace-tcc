# Handoff — Sprint 10: o que a banca vai perguntar

> **Para agentes sem contexto:** leia `AGENTS.md` primeiro, depois este arquivo.
> Sprints 1–9 **já estão implementadas**; a 9 deixou com o autor só trabalho de
> texto (ver o fechamento em `docs/sprint9-handoff.md`).

**Janela:** 2026-10-04 → **2026-11-20** (versão final da monografia). Até
14/10 o autor fecha o capítulo de resultados em paralelo.

## Objetivo

Fechar as perguntas previsíveis da banca com medição ou registro, sem feature
nova no produto:

- **"Mais processos não dariam o mesmo ganho sem Redis?"** — o protocolo fixou
  1 worker e não responde.
- **"Quanto o ETL descarta, e por quê?"** — a §3.3 promete registrar o volume
  consolidado no PostgreSQL; hoje `filter_valid` descarta em silêncio.
- **"O que ficou de fora?"** — trabalhos futuros com o motivo de cada corte.

## Estado de partida

| Fato | Prova |
|---|---|
| Protocolo da §3.3 com **1 worker**; cache decisivo a 250 VU (p95 613 → 25–29 ms) e +2,6× de vazão a 1.000 VU | `docs/performance.md` §11 |
| A Home `default` mudou na Sprint 9 (categoria regional): os números de 1 worker sem cache são de antes | `docs/sprint9-handoff.md`, fechamento |
| Máquina: 4 núcleos físicos / 8 lógicos, 7 GB; API, banco e gerador na mesma máquina | `load/results/protocolo/meta.json` |
| `filter_valid` não registra quanto cada filtro descarta | `scripts/etl_load_sample.py` |
| Suítes: `pytest -q` 182 · `npm test` 35 · E2E 2 | `docs/sprint9-handoff.md`, fechamento |

## Prioridades

| Ordem | Item | Prioridade |
|---|---|---|
| 6 | Experimento Redis × mais workers | Média |
| 7 | Log de funil do ETL | Média |
| 9 | Trabalhos futuros (cap. 6) — rascunho com motivos | Média |
| 8 | Conferir monografia: persona Seller e versionamento | Média — **autor** |
| 10 | Desempate de ofertas por preço | Baixa |
| 11 | Observabilidade (contagem de queries) | Baixa |
| 12 | Decidir sobre `docs/revisao-harness.md` | Baixa — autor da revisão |

## Decisões fechadas (não reinterpretar)

| # | Decisão | Motivo |
|---|---|---|
| 1 | Experimento de workers **sem cache**, 1 × 4 workers, 250 e 1.000 VU, n = 3 | a pergunta é se escala horizontal **substitui** o cache; 4 = núcleos físicos |
| 2 | O controle de 1 worker é **remedido**, intercalado e pareado (mesma semente) com o de 4 | a Home `default` mudou na Sprint 9; comparar com a Sprint 8 confundiria as duas mudanças. De brinde, mede o efeito da Sprint 9 na latência |
| 3 | Fora dos 27 ensaios do protocolo, em pasta própria (`load/results/s10-workers/`) | o protocolo da §3.3 está fechado; isto é ensaio complementar |
| 4 | Login/JWT, pedidos persistidos, PostGIS, versionamento de blocos: **trabalhos futuros**, não escopo | decisões da Sprint 9 e anteriores |

## Critérios de aceite

- [x] **Workers:** tabela 1 × 4 workers sem cache (p50/p95/p99, vazão, falhas, CPU) e leitura contra o cache de 1 worker → `python -m load.resumo load/results/s10-workers load/results/s10-workers-reexecucao load/results/s10-workers-reexecucao-w1`; `docs/performance.md` §12 — **não substituem o cache nesta máquina**: 1,7× de vazão com ~3 núcleos contra 2,6× do cache com 1
- [x] **Funil do ETL:** entrada → saída por filtro no stdout, e os totais batem com `count(*)` no Postgres → `python -m scripts.etl_load_sample`; teste do funil em `pytest -q` — 60.636 → 60.292 itens (−0,57%); totais conferidos contra o banco
- [x] **Trabalhos futuros:** cada item com o motivo do corte → `docs/tese-rastreabilidade.md` §8
- [x] `docs/tese-rastreabilidade.md` em dia (§1 suítes, §3, §4c, §6 linhas 21–22)
- [x] Suítes verdes no fim → `pytest -q` 183; `cd web && npm test` 35, lint e typecheck limpos; `cd web && npm run e2e` 2 (2026-10-04)

## Fora de escopo

Feature nova no produto · refazer o protocolo da §3.3 · workers **com** cache
(se a pergunta da banca vier, vira trabalho futuro) · gerador de carga em outra
máquina.

## Falhas encontradas e o que virou regra

| Falha | Virou |
|---|---|
| `terminate` no Windows só derruba o lançador do venv: com `--workers`, os workers órfãos ficariam na porta 8000 | `derrubar()` em `load/protocolo.py` mata a árvore; o runner já recusava subir com a porta ocupada |
| Um worker do uvicorn morreu ao subir (`WinError 10022`) e o amostrador de CPU parou junto: ensaio com 3 de 4 workers, sem CPU e sem registro de energia, sem aviso | `subir_api` só devolve com os N workers vivos (3 tentativas); `_cpu.csv` grava `workers_vivos`; ensaio sem amostra conta como inválido |
| Script de análise esquecido em segundo plano disputou CPU com um ensaio inteiro | detectado pela CPU do sistema no `_cpu.csv`; ensaio invalidado e refeito **em par** com o seu controle (`load/results/s10-workers/invalidado/MOTIVO.txt`) |
