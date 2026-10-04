# Rastreabilidade da tese — o que a metodologia promete, o que prova e o que mudou

> Documento de **defesa**: para cada promessa da metodologia (§3.3), qual teste ou
> medição a sustenta e o comando que a reexecuta; e o registro de tudo que mudou
> em relação ao que estava estabelecido, com o motivo. Números de latência ficam
> em `docs/performance.md`, não aqui — este arquivo aponta para eles.
>
> Atualizado em 2026-10-03 (Sprint 8). Regra: resultado sem comando não entra.

## 1. Estado das suítes

| Suíte | Comando | Último resultado | Data |
|---|---|---|---|
| Backend (unitários + integração por `dependency_overrides`) | `pytest -q` | **167 passed** | 2026-10-03 |
| Frontend (executor de `actions`, `ScreenRenderer`, carrinho) | `cd web && npm test` | **32 passed** | 2026-10-03 |
| E2E — jornada da defesa | `cd web && npm run e2e` (exige pilha e `data/raw/`) | não reexecutado nesta sprint | — |
| E2E — mutação de contrato SDUI | idem, `web/e2e/contract-mutation.spec.ts` | evidência em `docs/evidencia/` (Sprint 7) | — |
| Carga — protocolo da §3.3 | `python -m load.protocolo` | **parcial**: 27 rodados, 14 válidos (13 em bateria) — `docs/performance.md` §11 | 2026-10-03 |

O CI (`.github/workflows/ci.yml`) roda `pytest -q`, lint, typecheck, `npm test` e
build a cada push. E2E e carga ficam fora por dependerem de `data/raw/`
(gitignored).

## 2. §3.3 — testes funcionais com entradas controladas

| A metodologia promete verificar | Testes que sustentam | Comando |
|---|---|---|
| **Conversão de unidades e resultado da equação** com distância, massa e fator de emissão conhecidos | `tests/test_co2.py` — `test_emission_factor_value`, `test_100km_1000g`, `test_50km_2500g`, casos zero, peso cubado (`test_carga_leve_e_volumosa_usa_o_peso_cubado`, `test_o_cubado_entra_no_calculo_de_emissao`); `tests/test_distance.py` — `test_sao_paulo_rio_de_janeiro`, simetria, ponto igual; exibição g/kg em `tests/test_delivery_options.py` (`test_format_co2_*`) e no front (`formatacao de CO2`) | `pytest -q tests/test_co2.py tests/test_distance.py` |
| **Ordenação das alternativas** | `tests/test_checkout_simulate.py` — `test_shipments_come_sorted_by_footprint`, `test_ranking_weighs_mass_not_only_distance`, `test_alternative_reduces_co2_and_reports_the_saving`; `tests/test_home_contextual.py` — `test_conscious_buyer_orders_cards_by_proximity`, `test_vitrine_mostra_a_oferta_mais_proxima_do_comprador` | `pytest -q tests/test_checkout_simulate.py tests/test_home_contextual.py` |
| **Geração do payload** | `tests/test_schemas.py` (envelope, uniões discriminadas, ida e volta JSON, espelho do contrato no front); `test_sdui_envelope_preserved`, `test_valid_payload_returns_checkout_screen`, `test_returns_a_screen_response` | `pytest -q tests/test_schemas.py` |
| **Ausência de recomendação com dados insuficientes** | `test_no_alternative_when_nothing_is_closer`, `test_alternative_never_comes_from_a_seller_already_in_the_cart`, `test_badge_null_for_distant_seller`, `test_label_only_km_when_weight_absent`, `test_mode_co2_is_none_without_distance_or_weight`, `test_produto_de_um_vendedor_so_nao_inventa_comparacao`, `test_mesma_regiao_e_diferente_de_distancia_desconhecida`, `test_product_without_reviews_omits_the_rating` | `pytest -q` |
| **Renderização dos componentes esperados pelo React** | `web/tests/sdui.test.tsx` — `ScreenRenderer` (grade de cards, bloco desconhecido não quebra a tela), modo de inspeção, executor de `actions`; E2E `web/e2e/journey.spec.ts` | `cd web && npm test` |

## 3. §3.3 — desempenho e estresse

Situação item a item em `docs/performance.md` §10.7 (runner × texto). Resumo:

- **Conforme:** cenários da Tabela 1, *think time*, triplicata × três estados de
  cache, p50/p95/p99, falhas por código HTTP, média e desvio padrão, catálogo de
  metadados (`meta.json`), CPU da API por segundo.
- **Ajustado no texto** (§5 abaixo): rede, endpoint, pré-aquecimento.
- **Resultado (parcial, só ensaios na tomada):** meta de 200 ms cumprida a 50 VU
  nas três condições; a 250 VU, sem cache a API satura (p95 630 ms) e com cache
  atende a demanda com p95 de ~27 ms; a 1.000 VU, saturação nas três condições,
  com o cache triplicando a vazão (139 → 380–411 req/s). Previsões: 2 confirmadas,
  2 parcialmente refutadas — `docs/performance.md` §11.5.
- **Falta:** refazer as repetições 2 e 3 na tomada para n = 3 por célula.

## 4. §3.3 — mutação de contrato (flexibilidade da SDUI)

| Promessa | Evidência | Limite declarado |
|---|---|---|
| Reordenar blocos, injetar selo e inserir componente novo **sem alterar o cliente** e **sem rebuild** | `web/e2e/contract-mutation.spec.ts` — muta a resposta real do BFF e confere que a página não recarrega (marcador no `window` sobrevive); capturas em `docs/evidencia/` | prova que o **cliente** aceita árvores novas em runtime; **não** prova que o servidor as produza sem deploy (as mutações são injetadas no tráfego) |
| Contrato servidor ↔ cliente consistente | `tests/test_schemas.py::TestEspelhoDoContratoNoFront` — os `type` de blocos e ações são iguais em `src/schemas/sdui.py`, `web/lib/sdui.ts` e no `REGISTRY` | compara `type`, não `props` |

## 5. Ajustes ao texto da §3.3 (fechados em 2026-10-03)

Quatro trechos do texto não descrevem o experimento executado com precisão. O ambiente foi
mantido; o **texto** muda. Redação proposta para a monografia:

**5.1 Rede** — onde se lê *"os contêineres do motor de aplicação, da base de
dados e dos nós de injeção de carga do Locust serão orquestrados sob uma mesma
sub-rede virtualizada isolada em modo bridge"*:

> Para suprimir ruídos decorrentes de atrasos dinâmicos de rede externa (jitter e
> perda de pacotes), o motor de aplicação e o gerador de carga Locust são
> executados no mesmo hospedeiro e se comunicam pela interface de *loopback*,
> sem atravessar qualquer rede física; a base de dados PostgreSQL e o Redis
> executam em contêineres Docker no mesmo hospedeiro. Optou-se por não
> conteinerizar a aplicação porque, no ambiente Windows utilizado, o Docker opera
> sobre uma máquina virtual (WSL2), o que acrescentaria uma camada de
> virtualização ao caminho medido. A reprodutibilidade é assegurada pelo catálogo
> de metadados de cada execução (hash do commit, imagens Docker, volume de dados e
> hash do arquivo de parametrização).

**5.2 Alvo da carga** — onde se lê *"sobre o endpoint responsável pela
orquestração da SDUI e pelo cálculo de pegada de carbono"*:

> A carga é aplicada sobre a jornada de navegação completa — a tela inicial em
> quatro variações de contexto (padrão, especialista em eletrônicos, consumidor
> consciente e busca), o detalhe de produto e a simulação de checkout —, todas
> elas montadas pelo orquestrador SDUI e todas com cálculo de distância e pegada
> de carbono. As estatísticas são registradas por rota, o que permite isolar o
> endpoint de orquestração da tela inicial na análise.

**5.3 Cache aquecido** — complementar *"o cache aquecido é condicionado por meio
de um ciclo prévio de requisições de carga (pre-warming)"*:

> O ciclo de pré-aquecimento é o próprio ensaio de cache frio executado
> imediatamente antes, com a mesma semente de sorteio dos CEPs: os usuários
> virtuais do ensaio aquecido requisitam exatamente as chaves que o ensaio frio
> deixou em memória. A mesma semente é usada nas três condições de cada cenário,
> de modo que os três estados de cache são comparados sobre a mesma população de
> compradores (comparação pareada). O tempo de vida das chaves foi fixado em
> 3.600 s, superior à duração de um par frio–aquecido, para que as chaves não
> expirem entre os ensaios.

**5.4 O que "cache desabilitado" desliga** — a aplicação tem três camadas de
cache, e o texto não diz qual delas é a variável. Complementar a definição do
primeiro estado:

> O estado "cache desabilitado" refere-se exclusivamente à camada de respostas em
> Redis. Duas outras camadas permanecem ativas nos três estados e fazem parte da
> linha de base: a tabela de centroides de CEP (cerca de 12,9 mil linhas de dado
> de referência estático), mantida em memória no processo da aplicação desde a
> otimização que eliminou o padrão N+1 de consultas, e o cache de páginas do
> próprio PostgreSQL. Os CEPs dos usuários virtuais são sorteados da distribuição
> real de clientes da amostra, de modo que a taxa de acerto do cache reflete a
> concentração geográfica efetiva da demanda.

**5.5 Parâmetros a declarar** (não estavam no texto):

> Todos os ensaios utilizam um único processo de aplicação (1 *worker* do
> servidor ASGI) e os pools de conexões padrão das bibliotecas: no PostgreSQL, 5
> conexões fixas e 10 adicionais, com tempo limite de 30 s (SQLAlchemy); no Redis,
> até 100 conexões, sem fila de espera (redis-py 8.1). Esgotados, ambos resultam
> em resposta HTTP 500, contabilizada como falha. Os registros de SQL da aplicação são
> desligados durante as medições. As estatísticas descritivas consideram apenas
> o regime permanente (plateau); a série temporal completa, incluindo a rampa,
> é preservada para a análise da penalidade de *cache misses* no estado frio.

## 6. Registro de mudanças em relação ao estabelecido

O que estava definido (no PRD, na metodologia ou num handoff), o que mudou e por
quê. Cada linha aponta a evidência.

| # | Estava estabelecido | O que mudou | Por quê | Evidência | Sprint |
|---|---|---|---|---|---|
| 1 | PRD: latência < 200 ms **"com auxílio de cache Redis"** | A meta foi atingida sem Redis em carga nominal; o gargalo era um N+1 (63 queries por requisição) | medição, não inferência | `docs/performance.md` §§2–7; nota no `docs/prd.md` | 6 |
| 2 | Redis descartado (Sprint 6) | Reinserido como **variável de experimento**, desligado por padrão | o descarte foi por inferência, sem nunca rodar Redis; a §3.3 promete três estados de cache | `src/core/cache.py`; `docs/performance.md` §9 | 7 |
| 3 | Todas as medições das §§1–8 | **Valores absolutos invalidados** — o log de SQL (`echo`) estava ligado; comparações internas continuam válidas | o padrão de `DEBUG` é `True` | `docs/performance.md` §9 | 7 |
| 4 | Teste de carga com 2 CEPs fixos e *think time* de 0,5–2 s | CEPs da distribuição real de clientes; *think time* de 1–3 s, como diz a §3.3 | com 2 chaves, qualquer cache teria ~100% de acerto por construção; código e texto divergiam | `load/locustfile.py`; `b3dc39c` | 7 |
| 5 | Prazo de entrega arbitrado (`base_days`, `km_per_day`) | Prazo **medido** em 95.921 entregas reais, por faixa de distância | o modelo arbitrado subestimava (3 d para entrega local que leva 4,9 d) | `src/features/green_logistics/delivery_options.py`; `a3a4b16` | 7 |
| 6 | CO₂ sobre o peso real | CO₂ sobre a **massa cobrável** (peso cubado, 6.000 cm³ = 1 kg); a emissão **aumenta** — números anteriores subestimavam | prática do setor (GLEC/ISO 14083) | `src/features/green_logistics/co2.py`; `98807f9` | 7 |
| 7 | Catálogo derivado de `order_items` | Tabela `offers` (oferta vendável independente de pedido histórico) | a vitrine mudava a cada recarga do ETL; a amostragem escondia 474 casos de mesmo produto com vendedores distantes | `79970c3`, `e528274`, `428118a` | 7 |
| 8 | PRD: ações dinâmicas incluem **abertura de modal** | `open_modal` permanece no contrato, mas **nenhum bloco o emite** desde que o detalhe virou tela do servidor (`api_call`) | o detalhe passou a ser server-driven | `docs/tech_spec.md` | 6 |
| 9 | Snapshot de API antes/depois para provar equivalência do refactor de `offers` | `depois.json` **não será gerado** | o ETL mudou depois do `antes.json` (`428118a`); o diff diferiria por desenho | `scripts/snapshot_api.py`; `docs/sprint8-handoff.md` | 8 |
| 10 | Protocolo: TTL padrão do cache (60 s) | **3.600 s** durante o protocolo | com 60 s, "aquecido" vira "frio" no 1º minuto | `docs/performance.md` §10.1 | 8 |
| 11 | Protocolo: sorteio de CEP sem semente | Mesma semente nas três condições de cada cenário | sem ela, o aquecido media outros compradores | `load/locustfile.py` (`LOAD_SEED`) | 8 |
| 12 | Previsão do §9: taxa de acerto **menor** com mais VUs | **Substituída** pela §10.9 | foi escrita sob TTL de 60 s | `docs/performance.md` §§9, 10.9 | 8 |
| 13 | §3.3: contêineres em sub-rede *bridge*; carga sobre um endpoint; pré-aquecimento genérico; "cache desabilitado" sem definição | Texto ajustado (§5 acima) | ver §5 | `docs/sprint8-handoff.md`, decisão 6 | 8 |
| 14 | Premissa de trabalho: "com 25 usuários a API já bate o limite" | **Não vale mais**: capacidade de 1 worker ≈ 165–180 req/s sem cache; 50 VU com folga | a premissa veio de medições com `echo` ligado | `docs/performance.md` §10.8 | 8 |
| 15 | Execução do protocolo em ambiente estável | 13 dos 27 ensaios da 1ª execução rodaram **em bateria** e foram descartados; repetições 2 e 3 serão refeitas | em bateria o clock cai e a mesma requisição custa ~3,5× mais CPU | `load/results/protocolo/energia.txt`; `docs/performance.md` §11.2 | 8 |
| 16 | Ordem intercalada dos ensaios | `r3-u1000-frio` reexecutado **fora da ordem**, após o bloco de 250 VU | o original teve aviso de CPU do Locust (gerador saturado) | `load/results/protocolo/invalidado/`; `docs/performance.md` §11.1 | 8 |

## 7. Pontos a confirmar contra o texto da monografia

Itens que o repositório não decide sozinho:

- O PRD cita a persona **Microempreendedor (Seller)**; não há tela do lado do
  vendedor. Se a monografia prometer algo para essa persona, precisa de ajuste
  de texto ou de escopo.
- O `orchestrator` (versionamento de blocos) está como **stub**: o campo
  `version` existe, mas todo bloco vale 1. Conferir se o texto promete
  roteamento entre versões.
