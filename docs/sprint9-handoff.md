# Handoff — Sprint 9: os resultados que faltam aos dois eixos da tese

> **Para agentes sem contexto:** leia `AGENTS.md` primeiro, depois este arquivo.
> Sprints 1–8 **já estão implementadas**.

**Janela:** 2026-10-05 → **2026-10-14** (entrega dos resultados). A versão final
da monografia é em 2026-11-20 (Sprint 10).

## Objetivo

Produzir os números que os dois eixos da tese ainda não têm, a tempo do capítulo
de resultados:

- **Logística verde:** quão concentrada é a oferta (o problema), quanto CO₂ a
  recomendação evita (o efeito) — calculados com um motor de CO₂ que cumpra o que
  o objetivo específico (b) promete: metodologia **baseada em atividade**.
- **Personalização contextual:** contexto da Home derivado de dado regional real,
  não de um dicionário escrito à mão.

## Estado de partida

| Fato | Prova |
|---|---|
| Motor de CO₂: **um único fator** (0,102 kg CO₂/(t·km), GHG Protocol) sobre distância **em linha reta** (Haversine), com massa cobrável (peso cubado) | `src/features/green_logistics/co2.py` |
| Contexto da Home: `_CONTEXT_TO_CATEGORY`, dicionário de 2 entradas; o contexto vem do query param | `src/features/home_contextual/repository.py` |
| `cep_centroids` tem lat/lng por prefixo, **sem UF**; a UF existe no CSV de geolocalização (`geolocation_state`) e em clientes/vendedores | `src/core/models.py`; `data/raw/` |
| Dado de apoio do protocolo: 54% das requisições com CEPs reais não tiveram vendedor a menos de 100 km | `docs/performance.md` §8 |
| Exemplo de CO₂ do README ("~4,14 g") é da Sprint 4, anterior ao peso cubado | `README.md` §Demo; `98807f9` |
| Suítes: `pytest -q` 167 · `npm test` 35 · E2E 2 passando | `docs/sprint8-handoff.md` §Fechamento |

## Prioridades — a lista completa

Critério: **Alta** = até 14/10; **Média** = até 20/11 (Sprint 10); **Baixa** = só
com folga. O Backlog é o estoque: cada sprint puxa dele por prioridade; nada é
abandonado por ter sido criado numa sprint que terminou.

| Ordem | Item | Prioridade | Sprint |
|---|---|---|---|
| 0 | Caronas de 2 linhas: aviso no fim do ETL ("reinicie a API e esvazie o cache") e `SQL_ECHO` desacoplado do `DEBUG` | Média, mas baratas | **9** |
| 1 | Métrica de concentração logística regional | Alta | **9 (núcleo)** |
| 2 | Motor de CO₂ baseado em atividade (fator de desvio + FE por faixa) | Alta | **9 (núcleo)** |
| 3 | CO₂ evitado pela recomendação (sem persistência) | Alta | **9 (núcleo)** |
| 4 | Contexto derivado de dados regionais | Alta | **9 (meta)** — desce para a 10 se o prazo apertar |
| 5 | Conferir todos os números citados no texto | Alta | **9** — depois do item 2 |
| — | Capítulo 5 · ajustes da §3.3 com o orientador | Alta | **9, trabalho do autor**, em paralelo |
| 6 | Experimento Redis × mais workers | Média | 10 |
| 7 | Log de funil do ETL | Média | 10 |
| 8 | Conferir monografia: persona Seller e versionamento | Média | 10 |
| 9 | Trabalhos futuros (cap. 6) | Média | 10 |
| 10 | Desempate de ofertas por preço | Baixa | se sobrar |
| 11 | Observabilidade (contagem de queries) | Baixa | se sobrar |
| 12 | Decidir sobre `docs/revisao-harness.md` | Baixa | autor da revisão |

## Decisões fechadas (não reinterpretar)

| # | Decisão | Motivo |
|---|---|---|
| 1 | Login/JWT e pedidos persistidos **fora** do projeto | decisão do autor (04/10); viram trabalhos futuros |
| 2 | CO₂ evitado é calculado **sobre a amostra**, sem gravar pedido | o valor para a tese é o número; sem usuários reais, pedidos gravados seriam sintéticos de qualquer forma |
| 3 | Análises que produzem número para o texto são **scripts reprodutíveis** (`python -m scripts.<nome>`), não notebook | o número precisa de comando e commit, como o resto da rastreabilidade |
| 4 | Toda constante nova de CO₂ (fator de desvio, FE por faixa) tem **fonte citada no código** | o objetivo (b) e a banca; sem fonte, a constante é chute |
| 5 | O motor novo **substitui** o antigo (não fica atrás de flag) e o antes/depois fica documentado | dois motores = dois conjuntos de números no texto |

## Decisões a fechar durante a sprint

| # | Decisão | Recomendação |
|---|---|---|
| A | Valor do **fator de desvio rodoviário** (linha reta → estrada) | pesquisar fonte aplicável ao Brasil ou a do GLEC/ISO 14083; registrar a escolha e a fonte em `co2.py` e em `docs/tese-rastreabilidade.md` §6 |
| B | **Faixas de distância e FE por faixa** (última milha × transferência) | idem; preferir a mesma fonte de A |
| C | Onde mora a **UF do comprador** para o contexto regional | ETL grava a UF por prefixo em `cep_centroids` (moda de `geolocation_state`); o contexto vira derivado do CEP, com o query param como override — o contrato da API não muda |
| D | Lift categoria × UF: amostra ou **dataset completo** | dataset completo (o sinal regional precisa de volume; o card mediu com ele) |

### Pesquisa das decisões A e B (2026-10-04) — aguardando o autor

**Fontes encontradas**

| O quê | Fonte | Valor |
|---|---|---|
| Distância de atividade aceita | GLEC/ISO 14083, *Application of ISO 14083:2023 and the GLEC Framework for the Post & Parcel and e-commerce sector* (Smart Freight Centre, 2026), §2.1 | SFD **ou** GCD (linha reta) — o cálculo atual é admissível pela norma |
| Fator de circuidade rodoviária no Brasil | Gonçalves, D.N.S.; Gonçalves, C.D.M.; De Assis, T.F.; Silva, M.A. (2014). *Analysis of the difference between the euclidean distance and the actual road distance in Brazil*. Transportation Research Procedia 3, 876–885 | **1,345** para linha reta < 891 km (lido em citação de Lee & Chae, 2023; o original é de acesso aberto, mas bloqueou o download — **conferir no original**) |
| Intensidade por veículo, região **Europa e América do Sul**, WTW, diesel B5 | GLEC Framework v2.0 (Smart Freight Centre, 2019, rev. 2022), Módulo 2, p. 104–106, Tabelas 41–42 | van < 3,5 t **680** · caminhão urbano 3,5–7,5 t **370** · médio 7,5–20 t **200** · pesado > 20 t **92** g CO₂e/t·km |
| Aviso da própria norma | guia Post & Parcel (2026), §6 | fatores ponto a ponto **subestimam** rotas de coleta e entrega (última milha) |

O FE atual (0,102 kg/t·km ≈ 102 g) é praticamente o do caminhão pesado aplicado a **toda** entrega, inclusive a local.

**Impacto medido** (g CO₂e por kg de massa cobrável):

| Linha reta | Atual | Por faixa (van < 100 km de estrada, médio < 500, pesado) | Cadeia (pesado + 15 km de van na última milha) |
|---|---|---|---|
| 20 km | 2,0 | 18,3 | 18,3 |
| 432 km (mediana real) | 44,1 | 53,5 | 63,7 |
| 2.483 km (par de demonstração) | 253,3 | 307,2 | 317,4 |
| **mediana ÷ local** | **21,6×** | **2,9×** | **3,5×** |

**A conclusão "comprar perto emite menos" se mantém; a magnitude cai uma ordem de
grandeza.** Decisão do autor antes de implementar — muda todos os números de CO₂
do texto e do selo.

## Critérios de aceite

- [x] **Caronas:** o ETL termina avisando para reiniciar a API e esvaziar o cache → `python -m scripts.etl_load_sample` (fim da saída); `SQL_ECHO` próprio → `pytest -q`
- [x] **Concentração regional:** tabela por UF (itens com vendedor no mesmo estado; compradores sem vendedor a < 100 km) → `python -m scripts.concentracao_regional`; `docs/resultados/concentracao-regional.md`; leitura em `docs/tese-rastreabilidade.md` §4b
- [ ] **Motor de CO₂:** fator de desvio e FE por faixa com fonte no código; testes de valor conhecido atualizados → `pytest -q tests/test_co2.py`; antes/depois registrado em `docs/`
- [ ] **CO₂ evitado:** número citável ("em N compras simuladas, a recomendação evitaria X kg, Y%") → `python -m scripts.<script>`
- [ ] **Contexto regional** (meta): contexto derivado do CEP, query param como override, contrato SDUI inalterado → `pytest -q`; `cd web && npm run e2e`
- [ ] **Números do texto conferidos** depois do motor novo: README, `docs/` e a lista para o capítulo 5
- [ ] `docs/tese-rastreabilidade.md` atualizado: mudanças em §6, novos números com comando
- [ ] Suítes verdes no fim → `pytest -q`; `cd web && npm test && npm run lint && npm run typecheck`

## Fora de escopo

Login/JWT · pedidos persistidos · ReferenceBase/AppBase · PostGIS · versionamento
de blocos · ETag · os itens Média e Baixa da tabela de prioridades (exceto as
caronas) · remedir o protocolo de carga (o motor de CO₂ não muda latência).

## Falhas encontradas e o que virou regra

| Falha | Virou |
|---|---|
