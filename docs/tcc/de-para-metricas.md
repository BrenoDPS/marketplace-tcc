# De/para das métricas: evidência × monografia (02/11/2026)

> Cada número citado na monografia (Report 6 + ajustes da versão final), confrontado
> com a fonte que o gerou. **Fonte** é o arquivo versionado ou o comando rodado
> nesta data; **texto** é onde o número aparece (numeração da versão final, em
> que a Tabela 3 das modalidades é nova). Status: ✅ bate · ⚠️ bate com ressalva ·
> ❌ diverge (corrigido na versão final).

## 1. Suítes de teste (rodadas em 02/11)

| Métrica | Texto | Valor no texto | Fonte | Valor na fonte | Status |
|---|---|---|---|---|---|
| Testes do backend | §5.1.2 | 229 (PDF: 194) | `pytest -q` | 229 passed | ❌ → corrigido |
| Testes do frontend | §5.1.2 | 42 (PDF: 35) | `npm test` (Vitest) | 42 passed | ❌ → corrigido |
| Testes de jornada no navegador | §5.1.2 | 7 | `npm run e2e` | 7 passed | ✅ (novo no texto) |
| Lint e tipos | §4.3.4 | "rodam na integração contínua" | `npm run lint`, `npm run typecheck` | verdes | ✅ |

## 2. Dados e ETL

| Métrica | Texto | Valor no texto | Fonte | Valor na fonte | Status |
|---|---|---|---|---|---|
| Itens vendidos (base completa) | §5.1.1 | 112.650 | `docs/resultados/concentracao-regional.md` | 112.650 | ✅ |
| Com coordenadas nas duas pontas | §5.1.1 | 112.096 | idem | 112.096 | ✅ |
| Com todos os campos do cálculo | §5.1.1 | 112.070 | `docs/resultados/co2-evitado.md` | 112.070 | ✅ |
| Amostra completada | §§4.3.1, 5.1.1 | 60.636 | `docs/tese-rastreabilidade.md` §4b (log do ETL) | 60.636 | ✅ |
| Descartados | §5.1.1 | 344 (0,57%) | idem: 17 + 144 + 183 | 344; 0,567% | ✅ |
| Gravados: itens, pedidos, ofertas, centroides | §5.1.1 | 60.292; 53.114; 7.356; 12.933 | `load/results/s12-controle-head/meta.json` (linhas por tabela) | 60.292; 53.114; 7.356; 12.933 | ✅ |
| Produtos com mais de um vendedor | §5.1.1 | 106 → 580 | `scripts/etl_load_sample.py` (docstring); banco carregado | 580 antes dos descartes; **579** no banco | ⚠️ 580 é a amostra antes dos 344 descartes; um produto perde o segundo vendedor. Texto ajustado para "580, antes dos descartes" |
| Entregas reais para os prazos | §§4.1.1, 4.3.2 | 95.921 | `delivery_options.py` (`ETA_BANDS`) | 95.921 | ✅ |

## 3. Motor de cálculo

| Métrica | Texto | Valor no texto | Fonte | Valor na fonte | Status |
|---|---|---|---|---|---|
| Exemplo: 100 km, 1 kg | §5.1.2 | 0,021 kg CO₂e | `calculate_co2_kg(100, 1000)` | 0,0212 | ✅ |
| Fatores van / caminhão | §5.1.2 | 0,680 / 0,092 | `co2.py` | 0,680 / 0,092 | ✅ |
| Circuidade; última milha | §4.1.1 | 1,345; 15 km | `co2.py` | 1,345; 15 km | ✅ |
| Cubagem | §4.1.1 | 6.000 cm³/kg | `co2.py` | 6.000 | ✅ |
| Fatores das modalidades | Tabela 3 | Expressa 1,6/0,5/2,5; Verde 0,85/1,5/**0,7** | `delivery_options.py` | idem (Verde 0,7 desde 02/11) | ✅ |

## 4. Distância (OSRM)

| Métrica | Texto | Valor no texto | Fonte | Valor na fonte | Status |
|---|---|---|---|---|---|
| MAE crua / corrigida | Tabela 4 | 248,9 / 83,2 km | `docs/resultados/haversine-osrm.md` | 248,9 / 83,2 | ✅ |
| MAPE crua / corrigida | Tabela 4, Resumo | 21,9% / 8,7% | idem | 21,9% / 8,7% | ✅ |
| Viés mediano corrigido | Tabela 4 | +6,2% | idem | 6,2% | ✅ |
| Spearman | Tabela 4 | 0,997 | idem | 0,997 | ✅ |
| Razão rota/linha reta | §5.1.3 | 1,34 até 100 km; 1,22–1,28 acima | idem | 1,34; 1,22–1,28 | ✅ |
| Superestimação acima de 100 km | §5.1.3 | 5% a 10% | idem (viés por faixa) | 5,0% a 10,3% | ⚠️ arredondado; aceitável |
| Concordância na decisão | §5.1.3 | 32 de 37 (86,5%); IC 95% 72–94% | idem | 86,5%; IC calculado | ✅ |
| Pior divergência | §5.1.3 | 6,4 km (2,1%) | idem | 6,4 km (2,1%) | ✅ |

## 5. CO₂ evitado e sensibilidade

| Métrica | Texto | Valor no texto | Fonte | Valor na fonte | Status |
|---|---|---|---|---|---|
| Itens com alternativa | Tabela 5 | 14.367 (12,8%) | `co2-evitado.md` | 14.367 (12,8%) | ✅ |
| Já escolheu o mais próximo | Tabela 5 | 48,3% | idem | 48,3% | ✅ |
| Distância mediana | Tabela 5 | 437 → 330 km | idem | 437 × 330 | ✅ |
| CO₂ evitado | Tabela 5, Resumo | 254,2 kg (9,8%); 0,9% do total | idem | 254,2 (9,8%); 0,9% | ✅ |
| Preço nos 7.430 itens | §5.1.4 | 43,3 / 6,3 / 50,4%; R$ 0,01 | idem | idem | ✅ |
| Regra da aplicação | §5.1.4 | 1.823 (12,7%); 0 km; R$ 6,11; 253,7 kg; 39,3% | idem | idem | ✅ |
| Mesma UF / compra local / oferta local | Tabela 5 | 36,3% / 18,7% / 94,7% | `concentracao-regional.md` | idem | ✅ |
| Sensibilidade | §5.1.4 | −23% a +67%; 9,5–10,0% | `sensibilidade-co2.md` | −23,4% a +66,8%; 9,5–10,0% | ✅ |
| CO₂ evitado por UF (novo) | §5.1.4, Figura nova | SP 23,5% … BA 3,7% | `co2-evitado.md` (por UF) | idem | ✅ |
| Oferta local por UF (novo) | §5.1.4 | PA 0%; MT 54,3%; BA 74,9% | `concentracao-regional.md` | idem | ✅ |

## 6. Personalização regional

| Métrica | Texto | Valor no texto | Fonte | Valor na fonte | Status |
|---|---|---|---|---|---|
| UFs personalizadas | §5.1.5 | 12 de 27 | `tese-rastreabilidade.md` §4c; `regional_categories` = 12 linhas | 12 | ✅ |
| Faixa de lift | §5.1.5 | 1,22 a 1,80 | idem | 1,22 (DF, SC) a 1,80 (RJ) | ✅ |
| Sinais mais fortes | §5.1.5 | RJ móveis de sala; PE e BA telefonia; CE relógios | idem | RJ 1,80; PE 1,77; CE 1,73; BA 1,63 | ✅ |
| Custo de desempenho | §5.1.5 | 9,3 × 9,5 ms | `performance.md` §12 | 9,3 × 9,5 ms | ✅ |
| Lift de SP na vitrine | app | 1,3× | tabela regional | 1,33 | ✅ |

## 7. Desempenho

| Métrica | Texto | Valor no texto | Fonte | Valor na fonte | Status |
|---|---|---|---|---|---|
| Tabela 6 (todas as células) | §5.1.6 | média ± DP | `load/results/protocolo-final/resumo-agregado.md` | idem | ✅ (o PDF só tinha médias: corrigido) |
| CPU sem cache a 250 VU | §5.1.6 | 91% | idem | 91,0 ± 1,7% | ✅ |
| "Um terço do processamento" com cache | §5.1.6 | ~1/3 | idem | 30–34% | ✅ |
| Vazão 2,6× a 1.000 VU | §5.1.6, Resumo | 153 → ~400 req/s | idem | 153; 397–401 | ✅ |
| Rota cacheada a 1.000 VU | §5.1.6 | p95 190–200 ms | `resumo-conscious_buyer.md` | 190 ± 35; 200 ± 26 | ✅ |
| Dispersão do p95 a 1.000 VU | §5.1.6 | "desvio de 1 a 1,5 s" | `resumo-agregado.md` | 1,06 a **1,73 s** (sem cache: 1,73) | ❌ → corrigido para "1 a 1,7 s" |
| Workers | §5.1.6 | 170 → 284 req/s (1,7×); ~3 núcleos | `s10-workers-final/resumo-agregado.md` | 170; 284; CPU 305% | ✅ |
| Controle no código final | §5.1.6 | 8,5 × 8,3 ms; p95 19 ms; 600–1.200 ms | `performance.md` §12 | 8,5 × 8,3; 19,0–19,3; 600–1.200 | ✅ |
| Ensaios descartados | §5.1.6 | 14 (13 bateria + 1 gerador) | `tese-rastreabilidade.md` §6, linhas 15–16 | idem | ✅ |
| Parâmetros dos cenários | Tabela 1 (Cap. 3) | spawn 5/10/25; plateau 5/10/15 min; think time 1–3 s | `load/protocolo.py` (`CENARIOS`), `locustfile.py` (`between(1, 3)`) | idem | ✅ |
| Metadados prometidos na §3.3 | §3.3 | commit, imagens Docker, volume no PostgreSQL, locustfile | `meta.json` de cada execução | todos presentes | ✅ |
| Máquina dos ensaios | — | **não citada** | `meta.json` | Windows 11, 8 núcleos lógicos, 7,9 GB; PostgreSQL 16, Redis 7.4, Python 3.13, Locust 2.46 | ❌ lacuna → frase nova no §5.1.6 |

## 8. Referências × software usado

| Item | Referências do PDF | Usado de fato (`meta.json`) | Status |
|---|---|---|---|
| Locust | "Versão 2.31" | 2.46.5 | ❌ → corrigido para 2.46 (ano 2024 mantido: é o citado no Cap. 3) |
| FastAPI | "Versão 0.111" | 0.141.1 | ❌ → corrigido para 0.141 (ano 2024 mantido: é o citado no Cap. 2) |
| GLEC Framework | v3.0 (2023) | fatores da v2.0 (código e página de metodologia) | ⚠️ v3.0 mantida para a §3.2; v2.0 acrescentada e citada onde entram os fatores |
| Cubagem | BSOFT (2026) | OLIST (2022) no código e no app | ⚠️ trocada por OLIST (2022) |

## 9. Números da demonstração (roteiro da banca)

| Número | Onde | Fonte | Status |
|---|---|---|---|
| Atibaia 50 km, 7,17 g; Videira 588 km, R$ 39,90, 5,5× | `roteiro-banca.md`, Figura nova | app (02/11), E2E `roteiro-banca` | ✅ |
| Verde 5,02 g; Expressa 17,9 g | roteiro | E2E (Verde), captura `c08` | ✅ (Verde mudou de 4,30 para 5,02 g com o fator 0,7) |
| Caso de preço do Cap. 6: R$ 337,69 a 22 km × R$ 130,00 a 28 km; 0,4 g | §6.1.1 | `GET /products/69455f41…` (02/11) | ✅ 6,32 × 6,72 g |

## 10. Medição nova (02/11), ainda fora do texto

Tamanho do JSON de cada tela (o argumento de custo da SDUI na rede):

| Tela | JSON | gzip |
|---|---|---|
| Página inicial (regional) | 7,6 KB | 1,6 KB |
| Página inicial (consciente) | 7,7 KB | 1,5 KB |
| Detalhe do produto | 3,0 KB | 1,5 KB |
| Checkout (1 item) | 4,2 KB | 1,6 KB |
| Metodologia | 4,9 KB | 2,1 KB |
| Pesquisa | 13,1 KB | 4,3 KB |

Comando: `curl -s <rota> | wc -c` e `gzip -c | wc -c`. Entrou no §6.1.1 (o contrato
descreve a tela inteira em poucos kilobytes).

## Resumo

- **Todos os números dos Caps. 4 a 6 e do Resumo conferidos.** Três divergências: a contagem de testes, o desvio do
  p95 e as versões nas Referências. Duas lacunas: o hardware dos ensaios e o
  desvio padrão na tabela de desempenho. Todas corrigidas na versão final.
- Nenhum resultado central (9,8%, 8,7%, 86,5%, 2,6×, 12/27) diverge da fonte.
