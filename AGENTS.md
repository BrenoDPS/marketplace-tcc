# AGENTS.md — mapa e regras do projeto

**Produto:** marketplace com **Server-Driven UI** sobre o dataset Olist. O backend
(FastAPI) envia uma árvore JSON de blocos (`type`, `version`, `props`, `actions`)
e o front (Next.js) só renderiza por `type` e executa as ações. Eixo do TCC:
**personalização contextual** + **logística verde** (distância por CEP, selo
< 100 km, CO₂). O produto não usa LLM; não adicione dependência de IA generativa
sem pedido explícito.

## Mapa — abra só o que a tarefa pede

| Preciso de | Vá para |
|---|---|
| Visão geral, sprints, o que não fazer | `docs/PROJECT_BOOTSTRAP.md` |
| Contrato SDUI (fonte de verdade) | `src/schemas/sdui.py`; descrição em `docs/tech_spec.md` |
| Espelho do contrato no front | `web/lib/sdui.ts` + `REGISTRY` em `web/components/sdui.tsx` |
| Latência, N+1, Redis, protocolo | `docs/performance.md` §8–10 (as §§1–7 são histórico) |
| Evidência já produzida | `docs/evidencia/`, `load/results/`, `docs/snapshots/` |

A tarefa atual é o que foi pedido na conversa. Se existir sprint ativa com
handoff, ela está em `docs/PROJECT_BOOTSTRAP.md` → "Sprint ativa".

**Não leia por padrão** (histórico): `docs/frontend-sprint1.md`,
`docs/frontend-sprint2.md`, `docs/sprint2-handoff.md` a `docs/sprint5-handoff.md`,
`docs/revisao-harness.md`, `docs/devolutiva-harness.md`.

## Comandos

| Quero | Comando |
|---|---|
| Testes backend (o mesmo do CI) | `pytest -q` |
| Checks frontend (os mesmos do CI) | `cd web && npm run lint && npm run typecheck && npm test` |
| Subir a pilha | `docker compose up -d` → `python -m scripts.etl_load_sample` → `uvicorn src.main:app --reload` |
| Jornada real (exige pilha e `data/raw/`) | `cd web && npm run e2e` |

"Verde" só vale com o comando rodado nesta sessão, não lido em doc.

## Regras de código

- **Vertical Slice:** lógica nova vai para a fatia da responsabilidade em
  `src/features/` — `home_contextual` (composição da Home), `green_logistics`
  (CEP, distância, CO₂, selo, modalidades), `checkout`, `product_detail`,
  `orchestrator` (stub).
- **SDUI:** todo bloco segue o envelope `{ type, version, props, actions }`;
  `props` só dado/apresentação, `actions` é união discriminada. Pydantic v2 com
  discriminated unions; não troque props tipados por `dict` genérico.
- **Mudou o contrato?** Atualize `tests/test_schemas.py`, `web/lib/sdui.ts` e o
  `REGISTRY` juntos — `tests/test_schemas.py` falha se os `type` divergirem.
- **Logística verde:** onde a resposta expuser produto, integrar distância/selo:
  Haversine sobre centroides de CEP, selo < 100 km, FE 0,102 kg CO₂/(t·km) em
  `src/features/green_logistics/co2.py`.
- **Performance:** todo I/O de banco é async. Meta TTFB < 200 ms. **Meça antes de
  otimizar** (`load/locustfile.py`). `cep_centroids` vive em memória
  (`src/features/green_logistics/repository.py`); não reintroduza consulta por CEP
  no caminho quente.
- **Redis** é **variável de experimento**, desligado por padrão
  (`CACHE_ENABLED=false`, `src/core/cache.py`). Não é arquitetura: não ligue por
  padrão nem remova sem pedido — a decisão depende dos ensaios do protocolo.

## Fronteiras — não altere sem pedido explícito

`data/raw/*` · `load/results/*` · `docs/evidencia/*` · `docs/snapshots/*` ·
`.github/workflows/*` — são dado bruto ou evidência; reescrever apaga a prova.

`web/AGENTS.md` é regravado pelo `next dev`; regra de frontend vai neste arquivo.

## Docs e código

- O código é a verdade; docs são registro. Se um doc diverge do código, **diga
  qual dos dois está errado** em vez de "consertar" um para bater com o outro.
- Prefira atualizar um doc existente a criar um novo.
- `tests/test_docs.py` falha se este arquivo, o bootstrap ou o README citarem um
  caminho que não existe.
