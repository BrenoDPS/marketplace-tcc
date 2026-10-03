# Handoff — Sprint 8: o protocolo de carga da §3.3

> **Para agentes sem contexto:** leia `AGENTS.md` primeiro, depois este arquivo.
> Sprints 1–7 **já estão implementadas**.

## Objetivo

Executar os **27 ensaios** do protocolo da §3.3 da metodologia (3 condições de
cache × 3 cenários × 3 repetições) e **fechar a decisão sobre o Redis** com
números que sobrevivam à banca. Nada de feature nova no produto nesta sprint.

## Estado de partida

| Fato | Prova |
|---|---|
| O runner existe e fixa os defeitos de validade conhecidos: `DEBUG=false`, TTL longo, mesma semente de CEP nas três condições de uma carga, `--reset-stats`, ordem intercalada, taxa de acerto por ensaio | `python -m load.protocolo --help`; `python -m load.resumo --help` |
| Smoke a 50 VU (15 s, não é dado): p50 off 16 · frio 11 · aquecido 8 ms — o aquecido agora difere do frio | rodado em 2026-10-02, descartado |
| **Piloto a 1.000 VU, cache off, 1 worker, 120 s:** p50 **3,9 s**, p99,9 26 s, 163 req/s; **8 respostas 500** por `QueuePool limit of size 5 overflow 10 reached`; o Locust **não** saturou a CPU | `load/results/s8-piloto-u1000-off/u1000_stats.csv` |

O piloto responde duas perguntas: o gerador de carga aguenta 1.000 VU nesta
máquina; e a 1.000 VU com 1 worker a API está **saturada** — o que se mede ali é
fila, não cache.

## Decisões fechadas (não reinterpretar)

| # | Decisão | Motivo |
|---|---|---|
| 1 | **TTL de 3600 s** durante o protocolo (`--ttl`, padrão do runner) | Com 60 s, "aquecido" vira "frio" no 1º minuto. O catálogo só muda com o ETL. |
| 2 | **Previsões reescritas** sob o TTL de 3600 s → `docs/performance.md` §10.9; a do §9 fica marcada como substituída | A taxa de acerto passa a depender da duração do ensaio, não do nº de VUs. |
| 3 | **1 worker** nos três cenários; **1.000 VU declarado como saturação** | É o objetivo do cenário 3 na §3.3 ("ponto de esgotamento da CPU, formação de filas, taxa de erros"). Mais workers mudariam as três cargas. |
| 4 | **Pool mantido** em 5 + 10; falhas reportadas como resultado, separadas da latência | É a configuração real da aplicação. |
| 5 | **Parâmetros da Tabela 1 da §3.3**: 50 / 250 / 1.000 VU; spawn 5 / 10 / 25 VU/s; plateau 5 / 10 / 15 min | Texto da metodologia, fornecido pelo autor em 2026-10-02. `CENARIOS` em `load/protocolo.py`. |
| 6 | **Rede: ajustar o texto, não o ambiente.** API e Locust no host via *loopback*; Postgres e Redis em contêiner | O *loopback* suprime ruído de rede externa tanto quanto a *bridge*; no Windows o Docker roda em VM (WSL2), o que poria uma camada de virtualização no caminho medido. Reprodutibilidade pelo `meta.json`. Fechada pelo autor em 2026-10-03; redação em `docs/tese-rastreabilidade.md` §5. |

Declarado também no texto (`docs/tese-rastreabilidade.md` §5): (a) a carga percorre a jornada inteira (4 formatos de
Home, detalhe e checkout), não um endpoint só — as linhas por rota permitem
isolar a Home; (b) o aquecido é pré-aquecido pelo ensaio frio imediatamente
anterior, com os mesmos CEPs.

Tempo total: 9 × (5 + 10 + 15 min) de plateau + rampas e subida da API ≈
**4 h 50 min**, com a máquina dedicada.

## Como rodar

```bash
docker compose up -d
python -m load.protocolo
python -m load.resumo load/results/protocolo
```

## Critérios de aceite

- [x] Decisões 1–5 registradas → esta seção
- [x] Decisão 6 registrada → esta seção; texto ajustado em `docs/tese-rastreabilidade.md` §5
- [x] Previsões commitadas antes dos resultados → `git log --oneline -- docs/performance.md`
- [ ] 27 ensaios completos → `ls load/results/protocolo/*_stats.csv | wc -l` = 27
- [ ] Nenhum ensaio com o gerador saturado → `grep -l "CPU usage above" load/results/protocolo/*.log` vazio
- [ ] Metadados da execução → `load/results/protocolo/meta.json` com `commit` igual ao `git log -1` da medição
- [ ] `docs/performance.md` §11: tabela de `python -m load.resumo` (média ± dp de p50/p95/p99, RPS, falhas por código, taxa de acerto, CPU) para o agregado **e** para `GET /home (conscious_buyer)`; cada previsão da §10.9 marcada como confirmada ou refutada
- [ ] Série temporal do início do frio × aquecido (`_stats_history.csv`) — a penalidade dos *cache misses*
- [ ] `docs/tese-rastreabilidade.md` atualizado: §1 com os resultados, §3 com a conclusão, §6 com o que mudou na execução
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
