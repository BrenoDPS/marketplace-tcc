# Contexto da monografia — análise dos documentos e do projeto

Documento de apoio à redação dos capítulos 4 e 5 do `Report 6 - Resultados.docx`.
Complementa [`research_pdf_model.md`](research_pdf_model.md) com extração real dos
PDFs de referência e do relatório principal (out/2026).

Texto bruto gerado por `python docs/tcc/_extract_tcc_docs.py` → pasta
`_extracted/` (local, não versionada).

---

## 1. Estado atual do Report 6

### 1.1 O que já está escrito

| Parte | Situação |
|-------|----------|
| Cap. 1 Introdução | Redigido (objetivos a–d, VSA, BFF, FastAPI, React, Locust, Redis) |
| Cap. 2 Referencial | Redigido (e-commerce, logística verde, SDUI, CO₂, stack) |
| Cap. 3 Metodologia | Redigido (Olist, Haversine, fluxo SDUI, §3.3 carga e cache) |
| Cap. 4 Desenvolvimento | **Somente sumário** (4.1–4.3 e subseções listadas, sem corpo) |
| Cap. 5 Resultados | **Somente sumário** (5.1.1–5.1.5, 5.2.1–5.2.2, sem corpo) |
| Cap. 6 | Títulos de discussão, limitações, conclusão, trabalhos futuros |

### 1.2 Esqueleto acordado no Report 6 (caps. 4–5)

**Capítulo 4: DESENVOLVIMENTO**

- 4.1 ESPECIFICAÇÃO  
  - 4.1.1 Requisitos funcionais  
  - 4.1.2 Requisitos não funcionais, métricas e critérios de aceitação  
  - 4.1.3 Delimitações do escopo  
- 4.2 PROJETO  
  - 4.2.1 Organização em Vertical Slices  
  - 4.2.2 Modelo de dados relacional (PostgreSQL)  
  - 4.2.3 Contrato SDUI (esquema e tipos de componentes)  
- 4.3 IMPLEMENTAÇÃO  
  - 4.3.1 Tratamento e carga do dataset Olist  
  - 4.3.2 BFF em FastAPI: motor de cálculo logístico e cache (Redis)  
  - 4.3.3 Engine SDUI no servidor e renderizador React  
  - 4.3.4 Ambiente de execução (Docker Compose)

**Capítulo 5 — RESULTADOS**

- 5.1 RESULTADOS QUANTITATIVOS  
  - 5.1.1 Qualidade e cobertura dos dados  
  - 5.1.2 Verificação funcional do motor de cálculo  
  - 5.1.3 Acurácia da distância: Haversine × OSRM  
  - 5.1.4 Potencial estimado de redução de emissões  
  - 5.1.5 Desempenho sob carga e efeito do cache  
- 5.2 RESULTADOS QUALITATIVO-ESTRUTURAIS  
  - 5.2.1 Desacoplamento por mutação de contrato  
  - 5.2.2 Robustez do contrato: componentes desconhecidos e dados insuficientes

O esqueleto está **bem alinhado** ao padrão dos PDFs (requisitos → projeto →
implementação; resultados por dimensão de avaliação). Falta apenas o corpo textual
e as figuras/tabelas referenciadas.

---

## 2. Modelo dos PDFs de referência (extraído)

### 2.1 ETL-DataHub (66 páginas)

**Numeração diferente do Report 6** — o “desenvolvimento” está repartido em dois
capítulos:

| Cap. | Título (sumário) | Papel |
|------|------------------|--------|
| 4 | ESPECIFICAÇÃO DO PROJETO | Requisitos (ISO/IEC 9126), escopo, limitações |
| 5 | ARQUITETURA E TECNOLOGIAS APLICADAS | Stack, camadas, implementação ETL/RPA/API |
| 6 | RESULTADOS | Metodologia de testes **por módulo** → eficiência (tabela comparativa tempo manual × automatizado) → comercialização |
| 7 | CONSIDERAÇÕES FINAIS | Síntese |

**Padrões úteis para o seu cap. 5:**

- Abre o capítulo de resultados retomando o que foi construído nos capítulos
  anteriores.
- **6.1 Metodologia de testes** antes dos números: ETL/integridade → Data Mart →
  ciclo completo (RPA + SAP).
- Resultado central: **comparativo quantitativo de tempo/esforço** (antes/depois),
  não ordem de sprint.
- Declara que dados de estudo de caso **não representam necessariamente o dia a
  dia** da empresa — ressalva de validade externa.

**Padrões úteis para o seu cap. 4:**

- Requisitos funcionais e não funcionais **explícitos**, amarrados a norma ou
  critério de qualidade.
- Escopo e delimitação **no mesmo capítulo** da especificação (equivalente ao seu
  4.1.3).

### 2.2 Software de codificação para análises qualitativas (89 páginas)

**Cap. 4 — DESENVOLVIMENTO** (p. 34+): SDLC adaptado em três macrofases:

1. **4.1 Planejamento e análise** — viabilidade (benchmark mercado em **quadros
   comparativos**), Product Vision, requisitos.
2. **4.2 Design** — casos de uso, componentes, interface.
3. **4.3 Implementação** — código, testes unitários, CI, documentação (figura
   “pipeline de desenvolvimento”).

**Cap. 5 — RESULTADOS** (p. 54+):

- Parágrafo-guia: avaliação em **três etapas** (uso real → questionários
  quantitativos → dissertativos).
- **Caracterização da amostra de avaliação** (n=10, perfil, % experientes).
- **5.1 Quantitativos** — SUS desdobrado por heurísticas (subseções 5.1.1.1–5.1.1.5),
  cada uma com **figura de distribuição** + interpretação; depois NPS.
- **5.2 Qualitativos** — exemplos de codificação, nuvem de palavras, feedback
  aberto.

**Cap. 6–7:** discussão amarrada às métricas (SUS/NPS), limitações, considerações
finais **sem número novo**.

**Lições para o Report 6:**

- Subseções de resultado **finas** (por heurística ou por dimensão) funcionam bem
  com figura + parágrafo interpretativo.
- Apêndices com requisitos formais (RF/RNF) — no seu caso, o equivalente é
  `docs/prd.md`, `docs/tech_spec.md` e tabelas em `tese-rastreabilidade.md`.

---

## 3. Texto prometido (cap. 3) × o que o repositório entrega

Use esta tabela ao redigir caps. 4–5 e ao ajustar o cap. 3 com o orientador
(redações prontas em [`docs/tese-rastreabilidade.md`](../tese-rastreabilidade.md) §5).

| Promessa no Report 6 (metodologia) | Realização no projeto | Onde documentar no TCC |
|-----------------------------------|------------------------|-------------------------|
| Front-end **React** renderizador genérico | **Next.js** (App Router), espelho TS em `web/lib/sdui.ts` | Cap. 4.3.3: “React/Next.js”; corrigir cap. 1 se mantiver só “React” |
| Comparação **Haversine × OSRM** | **Executada** em duas análises: 100 pares para precisão, com 20 por faixa de distância, e 102 pares agrupados em 37 decisões de oferta. O fator de circuidade 1,345 continua sendo usado no motor de CO₂ | **5.1.3:** apresentar MAPE, MAE, viés, correlação e preservação da ordenação, registrando que o OSRM representa a rota mais rápida de carro e que os pontos são centroides |
| Redis como premissa de latência na intro | Meta atingida **sem** Redis em carga nominal após N+1; Redis **decisivo** a 250 VU (protocolo §3.3) | 5.1.5 + discussão; alinhar com notas do `docs/prd.md` |
| Contêineres do app + Locust em bridge | App no host (Windows/WSL2); DB/Redis em Docker; loopback | Texto §5.1 de `tese-rastreabilidade.md` |
| Carga em “um endpoint” de orquestração | Jornada Locust: Home (4 contextos), detalhe, checkout | Idem §5.2 |
| Persona **Seller** (PRD) | Sem tela de vendedor | 4.1.3 delimitação; cap. 6 trabalhos futuros (`tese-rastreabilidade.md` §7–8) |
| Versionamento dinâmico de blocos (`orchestrator`) | Stub; `version` sempre 1 | 4.1.3 / 4.2.1 |
| Pagamento, pedido persistido, login | Fora de escopo (Sprint 9) | 4.1.3 |

---

## 4. Mapa capítulo 4 → evidências no repositório

Cada subseção: **o que escrever** + **onde provar** (comando quando existir).

### 4.1 Especificação

| Subseção | Conteúdo sugerido | Fontes |
|----------|-------------------|--------|
| 4.1.1 RF | Home contextual, selo &lt; 100 km, CO₂ estimado, checkout simulado, busca/filtro por categoria, detalhe server-driven, comparativo de modalidades, sugestões de troca no carrinho | `docs/prd.md`, `README.md`, rotas em `src/main.py` |
| 4.1.2 RNF | TTFB &lt; 200 ms (§3.3), contrato tipado, degradar tipo desconhecido, reprodutibilidade (Git hash, meta.json), async I/O | `docs/performance.md`, `docs/tese-rastreabilidade.md` §1–3 |
| 4.1.3 Escopo | Amostra ETL ~60k itens para runtime; análises regional/CO₂ evitado no **dataset completo**; sem PostGIS/pagamento; validação OSRM offline; modalidades express/green = cenário declarado | `AGENTS.md`, docstring `delivery_options.py`, `tese-rastreabilidade.md` §8 |

### 4.2 Projeto

| Subseção | Conteúdo sugerido | Fontes |
|----------|-------------------|--------|
| 4.2.1 VSA | Fatias `home_contextual`, `green_logistics`, `checkout`, `product_detail`; regra única `escolher_oferta` | `README.md` arquitetura, `AGENTS.md` |
| 4.2.2 Dados | Tabelas Olist + `cep_centroids` (UF, lat/lng), `offers`, `regional_categories`; centroides em memória | `scripts/etl_load_sample.py`, `src/core/models.py` |
| 4.2.3 SDUI | Envelope, discriminated unions, blocos (`product_card`, `hero_banner`, `delivery_options`, `shipment_breakdown`, …), ações `navigate` / `api_call` / `open_modal` | `src/schemas/sdui.py`, `docs/tech_spec.md`, `web/components/sdui.tsx` |

### 4.3 Implementação

| Subseção | Conteúdo sugerido | Fontes |
|----------|-------------------|--------|
| 4.3.1 ETL | Amostragem seed 42, completude de ofertas, funil de descarte (Sprint 10), contexto regional | stdout do ETL; `tests/test_amostragem.py` |
| 4.3.2 BFF | Haversine, motor CO₂ (cadeia GLEC), cache Redis resposta SDUI (TTL 1 h), eliminação N+1 | `green_logistics/`, `core/cache.py`, `docs/performance.md` §2–7 |
| 4.3.3 Front | REGISTRY, executor de actions, carrinho cliente, modo inspeção SDUI, rewrite `/api/v1` | `web/`, `README.md` §Frontend |
| 4.3.4 Ambiente | `docker compose` (Postgres 5433, Redis), pytest/Vitest/E2E/Locust | `README.md`, `load/protocolo.py` |

**Parágrafo-guia (estilo PDFs):** “Este capítulo descreve, na ordem especificação →
projeto → implementação, como a engine SDUI e o motor de logística verde foram
materializados sobre o dataset Olist, culminando no ambiente reproduzível usado
nos testes da §3.3.”

---

## 5. Mapa capítulo 5 → evidências e ordem de redação

Ordem recomendada (ETL-DataHub + Software CAQDAS + `research_pdf_model.md`):

### 5.1 Quantitativos

| Subseção | Métricas / artefatos | Comando / caminho |
|----------|----------------------|-------------------|
| **5.1.1** Dados | Funil ETL; totais Postgres; 12,9k centroides; 7,3k ofertas na amostra | `python -m scripts.etl_load_sample`; `tese-rastreabilidade.md` §3 (volume consolidado) |
| **5.1.2** Motor | Casos controlados distância/massa/CO₂; ordenação conscious_buyer e alternatives; payload schema | `pytest -q` (tabela §2 em `tese-rastreabilidade.md`) |
| **5.1.3** Distância | MAPE Haversine crua 21,9%; MAPE após fator 1,345 8,7%; MAE 83,2 km; viés mediano +6,2%; Spearman 0,997; 86,5% das decisões escolheram o mesmo vendedor mais próximo; 91,0% dos pares mantiveram a ordenação | `docs/resultados/haversine-osrm.md`; `docs/resultados/haversine-osrm.csv`; `docs/graficos/fig-5-4-haversine-osrm.png` |
| **5.1.4** Emissões | Concentração 36,3% / 18,7% / 94,7%; CO₂ evitado 254 kg (9,8%); preço mediano R$ 0,01; contexto regional (lift) | `python -m scripts.concentracao_regional`; `python -m scripts.co2_evitado`; §4b–4c `tese-rastreabilidade.md`; `docs/resultados/*.md` |
| **5.1.5** Desempenho | 27 ensaios, n=3; figuras 5.1–5.3; conclusão Redis; complemento 4 workers (§12) | `docs/performance.md` §11–12; `docs/graficos/` |

Após cada tabela ou figura: **1–2 parágrafos** ligando ao objetivo (a), (b), (c) ou (d).

### 5.2 Qualitativo-estruturais

| Subseção | Evidência | Comando |
|----------|-----------|---------|
| **5.2.1** Mutação | Reordenar blocos, injetar selo, bloco novo, sem reload/build | `cd web && npm run e2e` (`contract-mutation.spec.ts`); PNG em `docs/evidencia/` |
| **5.2.2** Robustez | Tipo desconhecido não derruba tela; sem badge/dados insuficientes; espelho contrato backend/front | `web/tests/sdui.test.tsx`; `tests/test_schemas.py` |

**Estilo Software CAQDAS:** descrever **procedimento** da mutação (o que foi alterado
no JSON) e **critério de sucesso** (marcador `window` sobrevive, selo visível),
com uma figura por mutação quando possível.

---

## 6. Seção 5.1.3: Haversine e OSRM

O estudo comparativo prometido na metodologia foi executado offline e possui
relatório, CSV congelado e gráfico no repositório. A primeira análise utiliza
100 pares, distribuídos em 20 observações por faixa de distância, para comparar
Haversine crua, Haversine corrigida pelo fator 1,345 e OSRM. A segunda preserva
grupos inteiros de ofertas e totaliza 102 pares distribuídos em 37 decisões.

Na redação do Capítulo 5, é importante separar a precisão da distância da
preservação da decisão. O resultado de 21,9% de MAPE para a distância Haversine
crua cai para 8,7% após a aplicação do fator de circuidade. A correlação de
Spearman foi 0,997. Na análise de ofertas, o vendedor mais próximo segundo a
Haversine também foi o mais próximo segundo o OSRM em 86,5% das decisões, e
91,0% dos pares preservaram a ordenação. O script analítico compara a ordenação
por distância; ele não deve ser descrito como uma execução integral da função
de escolha de oferta, que também considera preço entre distâncias equivalentes.

O resultado deve ser acompanhado das limitações do método. O OSRM calcula a
rota mais rápida de carro, os pontos de origem e destino são centroides de
prefixos de CEP e o serviço público pode mudar sua malha viária. A validação
fortalece a justificativa da aproximação utilizada, mas não transforma a
estimativa em uma rota operacional da transportadora.

Qualquer número de CO₂/distância na demo usa **amostra**; concentração e CO₂
evitado usam **dataset completo** — deixar explícito no 5.1.1 e 5.1.4.

---

## 7. Figuras e tabelas já prontas

| Uso no cap. 5 | Arquivo |
|---------------|---------|
| Vazão × latência | `docs/graficos/fig-5-1-vazao-x-latencia.png` |
| Série temporal cache frio/aquecido | `docs/graficos/fig-5-2-serie-temporal-frio-aquecido.png` |
| Latência por rota a 1000 VU | `docs/graficos/fig-5-3-por-rota-1000vu.png` |
| Mutação SDUI | `docs/evidencia/0-linha-de-base.png` … `3b-bloco-desconhecido.png` |

Gerar gráficos: `python -m load.graficos` (`docs/performance.md` §11.10).

---

## 8. Próximos passos (redação)

1. ~~Redigir caps. 4~~ — rascunho em [`capitulo-4-rascunho.md`](capitulo-4-rascunho.md).
2. Preencher cap. 5 na ordem §5 (ou usar rascunho quando existir).
3. Preencher 5.1.1 → 5.1.5 → 5.2.1–5.2.2 na ordem §5.
4. Aplicar ajustes §3.3 do orientador (`tese-rastreabilidade.md` §5) no cap. 3
   **e** repetir premissas corretas no 5.1.5 (ambiente, jornada, cache).
5. Redigir 5.1.3 com a validação OSRM já executada e as limitações descritas na
   seção 6.
6. Harmonizar **React/Next.js**, a validação OSRM e a narrativa **Redis** entre
   caps. 1, 4 e 5.

Para regenerar extrações após editar o `.docx`:

```bash
python docs/tcc/_extract_tcc_docs.py
```
