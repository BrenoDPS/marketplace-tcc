# Parecer de revisão — Capítulos 4 e 5 (rascunhos)

> Revisão imparcial conduzida segundo [`MANUAL-REVISAO-AGENTE.md`](MANUAL-REVISAO-AGENTE.md).
> Data: 2026-10-13. Repositório no commit `b3d6c48`.
> Tipos dos achados: **Fato** (verificável no código/evidência), **Inferência**
> (conclusão derivada que exige explicação), **Opinião** (preferência editorial),
> **Lacuna** (algo necessário e não encontrado).

## 1. Escopo e base da análise

- **Objeto:** revisão global de [`capitulo-4-rascunho.md`](capitulo-4-rascunho.md) e
  [`capitulo-5-rascunho.md`](capitulo-5-rascunho.md), confrontados com o repositório.
- **Leitura, na ordem do manual:** `AGENTS.md`/`CLAUDE.md` →
  [`CONTEXTO_MONOGRAFIA.md`](CONTEXTO_MONOGRAFIA.md) → os dois capítulos →
  [`docs/tese-rastreabilidade.md`](../tese-rastreabilidade.md) →
  [`docs/performance.md`](../performance.md) §11–12 → `docs/resultados/*.md` → código
  (`co2.py`, `offers.py`, `badge.py`, `delivery_options.py`, `alternatives.py`, `sdui.py`,
  `repository.py`, `etl_load_sample.py`, `models.py`, `contract-mutation.spec.ts`, `test_co2.py`).
- **Executado na sessão de revisão:** `pytest -q` → **194 passed**; `cd web && npm test` →
  **35 passed**. E2E e carga **não** foram reexecutados (exigem a pilha e `data/raw/`).
- **Não consultados:** os PDFs de referência e o `.docx`; nenhuma afirmação dos capítulos
  sobre literatura exigiu essa consulta.

## 2. Veredito provisório

**Seguir após correções.** O esqueleto é bom, a separação entre observado, modelo e
contrafactual é madura, e a maior parte dos números bate com a evidência. Dois problemas,
porém, impedem defender o texto como está:

- o Cap. 4 afirma que o artefato descrito é o mesmo que passou pelos testes de carga, e
  isso é falso;
- o Cap. 5 não traz nenhum resultado sobre personalização contextual, que é metade do eixo
  do TCC e está na própria pergunta de abertura do capítulo.

Há ainda vários erros localizados de fato — fatores de emissão invertidos, tabela de carga
com células omitidas e "Não registrada" onde há registro, base do ganho de 1,7× errada —
todos corrigíveis com a evidência que já existe no repositório.

## 3. Pontos fortes (observáveis)

- **Separação de três tipos de resultado** (Cap. 5, l.28-34): observação, saída de modelo e
  contrafactual. Poucas monografias fazem isso.
- **Honestidade sobre limites:** OSRM usa rota de carro e centroides; a mutação prova o
  cliente e não o servidor; 9,8% vale para os casos com alternativa e 0,9% para o universo.
- **Números do ETL, do CO₂ evitado e do OSRM** batem com `docs/resultados/`. Recalculados na
  revisão: 0,021194 kg, 0,022865 kg, 254,2 / 2.601,3 = 9,8% e 254,2 / 26.934,9 = 0,94%.
- **O repositório sustenta uma defesa rara para TCC:** rastreabilidade com commit por
  resultado, invalidações registradas com motivo e decisões medidas em vez de presumidas.

## 4. Achados priorizados

Prioridades: **bloqueador** compromete a validade ou a compreensão central; **maior** é
correção necessária antes da entrega; **menor** é melhoria localizada; **sugestão** é
aprimoramento editorial.

| ID | Prioridade | Local | Tipo | Observação verificável | Impacto | Recomendação |
|---|---|---|---|---|---|---|
| B1 | bloqueador | Cap. 4, l.19-21 | Fato | O texto diz que o artefato "é o mesmo que foi submetido [...] ao protocolo de carga". Os 27 ensaios rodaram em `f15f8a1`/`30ebe97` (Sprint 8; `performance.md` §11.1). Depois entraram o motor de CO₂ em cadeia (`953fc4e`), a Home regional (`7ac98fa`) e a regra `escolher_oferta`, que também mudou a consulta do checkout (`2de753d`). O ensaio de workers rodou em `f760996`/`df0ec49`, antes do `2de753d`. | Um examinador que confira o `meta.json` derruba a frase e, com ela, a credibilidade do 5.1.5. | Trocar por declaração de versão (tabela "resultado × commit"); citar a §12.5 (Sprint 9 sem efeito mensurável na latência); para o `2de753d`, reexecutar um controle curto no HEAD ou declarar que não foi medido. |
| B2 | bloqueador | Cap. 5 inteiro; l.124-131 | Lacuna | A pergunta do capítulo (l.6-10) começa por "personalização contextual", mas nenhuma seção a mede; a l.124-131 fala só de "cobertura suficiente". A evidência existe em `tese-rastreabilidade.md` §4c: 12 de 27 UFs personalizadas, lift de 1,22× a 1,80×, 15 UFs sem sinal, sem teste de significância, latência 9,3 × 9,5 ms. | Um dos dois eixos da tese fica sem resultado; o objetivo (a) não fecha. | Criar subseção (ex.: 5.1.6 ou dentro da 5.2) com UF × categoria × lift, cobertura 12/27, a ressalva "por região, não por pessoa" e o custo nulo de latência. |
| M1 | maior | Cap. 5, l.185-186 | Fato | "0,092 e 0,680 kg/(t·km), respectivamente" atribui 0,092 à van e 0,680 ao caminhão. O código faz o contrário: van 0,680, caminhão 0,092 (`src/features/green_logistics/co2.py:42-43`). O caso de 0,021194 kg só fecha com a ordem do código. | Erro de fato justamente na seção que prova os fatores. | Inverter a ordem na frase. |
| M2 | maior | Cap. 5, l.158-164; Tab. 5.2 | Fato | Os 15.000 g não são "a soma da cubagem por item", e sim a soma dos `max(real, cubada)` de cada item (5.000 + 10.000). A cubagem é linear; consolidar o volume não muda nada. O que muda é aplicar o `max` à remessa (`tests/test_co2.py:104-122`). | Mecanismo mal explicado; alvo fácil para a banca. | Reescrever: "aplicar o máximo entre massa real e cubada à remessa, e não a cada item"; declarar como escolha de modelagem. |
| M3 | maior | Cap. 4, l.70-72; `co2.py:45-47` | Lacuna + Inferência | 6.000 cm³/kg é chamado de "convenção do transporte rodoviário" sem fonte, no código ou no texto. A verificar: a carga fracionada rodoviária no Brasil costuma usar 300 kg/m³ (≈ 3.333 cm³/kg); 6.000 cm³/kg é a convenção aérea/courier. | Afeta todo número de CO₂: em 66,4% dos produtos o peso cubado supera o real. | Citar fonte para 6.000 ou trocar o valor; em caso de troca, mostrar a sensibilidade no CO₂ evitado. |
| M4 | maior | Cap. 5, l.236-261; Tab. 5.3 | Inferência | O Spearman 0,997 vem de amostra estratificada de 1 a mais de 2.000 km; com essa amplitude, correlação de postos alta é quase garantida pelo desenho. Por faixa, cai para 0,85–0,98 (`docs/resultados/haversine-osrm.md`). A coluna "corrigida" repete 0,997 porque multiplicar por constante não muda postos — não é resultado independente. | "Preservação muito elevada da ordenação" superestima o achado; a ordem entre ofertas próximas é respondida pela análise B. | Reportar o Spearman por faixa, dizer que o global é inflado pela estratificação e remover a duplicação. |
| M5 | maior | Cap. 5, 5.1.3 e 5.1.4 | Lacuna | Falta o principal achado: até 100 km o fator 1,345 acerta (viés 0,5%); acima, superestima a estrada — e o CO₂ absoluto — em 5–10% (`tese-rastreabilidade.md` §4d). Falta também que 3 das 5 divergências caem na tolerância do `escolher_oferta`. | Omitir o próprio achado negativo enfraquece a transparência, que é o ponto forte do texto. | Parágrafo + tabela por faixa; levar a consequência ao 5.1.4 (kg absolutos podem estar até ~10% acima). |
| M6 | maior | Cap. 5, l.264-273 | Fato + Inferência | "102 pares" e "111 comparações" sem definição: o primeiro conta rotas comprador→vendedor; o segundo, comparações vendedor × vendedor dentro de cada decisão. O 86,5% vem de n = 37, sem intervalo; Wilson 95%, calculado na revisão: ~72% a ~94%. | O leitor não sabe o denominador; a precisão parece maior do que é. | Definir os termos; informar 32/37 e o intervalo. |
| M7 | maior | Cap. 5, l.353-354 e l.377-382 | Fato | A "regra de recomendação" da análise é a oferta mais próxima pura (`scripts/co2_evitado.py:74`, `idxmin`), não o `escolher_oferta` com desempate por preço. O trade-off de preço usa denominador de **7.430** itens (os que trocariam de vendedor), não 14.367. O preço na análise é a mediana por vendedor; a aplicação usa a primeira linha (`scripts/etl_load_sample.py:224`). | Os percentuais de preço parecem ter a mesma base do CO₂, e não têm. | Declarar a regra, o denominador e a diferença no preço; acrescentar dispersão (IQR), pois a mediana de R$ 0,01 esconde a cauda. |
| M8 | maior | Cap. 5, Tab. 5.7 | Fato | Omite 3 das 9 células (50 VU frio e aquecido, 250 VU frio) e escreve "Não registrada" para falhas registradas: 0%, 0,02%, 0,03%, 0,07% (`performance.md` §11.3). | Afirmação falsa sobre a própria evidência; o protocolo 3 × 3 × 3 parece incompleto. | Reproduzir a tabela da §11.3 completa, com ± dp, p99, taxa de acerto e CPU. |
| M9 | maior | Cap. 5, l.491-495; 5.3 l.714-718 | Fato | "Meta de 200 ms alcançada nos cenários de cache" não se sustenta: a 1.000 VU com cache, p95 agregado de 2.900–3.000 ms; `/products` e `/checkout` acima de 5 s. Só a Home `conscious_buyer` ficou em 190 ± 35 e 200 ± 26 ms — e 200 não é < 200. | Sobreafirmação no resultado central de desempenho. | Reformular: cumprida a 50 VU nas três condições e a 250 VU com cache; a 1.000 VU só a rota cacheada ficou no limite, e o agregado saturou. |
| M10 | maior | Cap. 5, l.501-507; Tab. 5.8 | Fato | O 1,7× é 284 / **170** req/s (controle remedido na Sprint 10, `performance.md` §12.2). Contra 153 seria 1,86×. A tabela mistura Sprint 8 e Sprint 10 e omite que 4 workers usaram ~3 núcleos contra 1, e que o p95 a 250 VU foi instável (58 / 93 / 1.500 ms). | A conta não fecha com os números apresentados; omite o custo em CPU. | Usar 170 como base, indicar a sprint de cada linha, acrescentar coluna de núcleos. |
| M11 | maior | Cap. 5, l.443-446 e l.533-537 | Fato | "Cache frio" mal definido: é o *ensaio* que começa com Redis vazio (acerto de 93,9–97,6%); no regime permanente frio ≈ aquecido, e a penalidade dura 1–3 min (§11.5; `docs/graficos/fig-5-2-serie-temporal-frio-aquecido.png`). Motivo dos descartes errado: 13 ensaios com o **notebook na bateria** (clock reduzido) e 1 com gerador saturado (§11.1-11.2), não "ordem de execução ou configuração". | Distorce a narrativa sobre a validade dos ensaios. | Corrigir a definição, incluir a série temporal e relatar o motivo real dos descartes. |
| M12 | maior | Cap. 5, l.457-463 | Fato | O texto diz que a 250 VU o sistema "ainda encontrava capacidade". A fonte diz o contrário: sem cache, 91% de CPU e vazão de 111 req/s abaixo da demanda (~125). A vazão parecida vem do modelo fechado com *think time*, em que a demanda limita a vazão. | Interpretação contradiz a fonte. | Explicar o modelo fechado (a Lei de Little já está na §11.1). |
| M13 | maior | Cap. 5, l.57-63; Cap. 4, 4.3.1 | Lacuna | Não diz como a amostra é formada: 10.000 linhas, semente 42, completadas para 60.636 itens. A completude pondera por popularidade: produtos multivendedor são 8,8% da amostra contra 3,7% do universo (`scripts/etl_load_sample.py:96-117`). Falta também o salto de 106 para 580 produtos multivendedor. | Reprodutibilidade comprometida; o leitor pode generalizar proporções da demo. | Descrever procedimento e viés; usar o 106 → 580 como resultado. |
| M14 | maior | Cap. 4, l.283-286 e l.364-369; Cap. 5, Tab. 5.10 | Fato | Dois mecanismos confundidos: `escolher_oferta` (mesmo produto, outro vendedor) e alternativas do checkout (**outro produto da mesma categoria** de vendedor mais próximo — `src/features/checkout/alternatives.py:1-20`). O texto nunca diz que a substituição troca o produto. | Pergunta previsível da banca; a Tab. 5.10 descreve o mecanismo errado. | Nomear os dois mecanismos; declarar que a substituição não é equivalente. |
| M15 | maior | Cap. 4, l.98-104 e l.355-360 | Lacuna | Fatores das modalidades arbitrados e não mostrados: Expressa preço 1,6 / CO₂ 2,5 / prazo 0,5; Verde 0,85 / 0,6 / 1,5 (`delivery_options.py:83-106`). O selo do checkout multiplica o CO₂ pelo fator da modalidade, então o número de cenário aparece ao usuário como estimativa. | O leitor não consegue avaliar o cenário. | Tabela com os fatores e a justificativa ou fonte de cada um. |
| m1 | menor | Cap. 4, l.118; 5.1.5 | Inferência | A meta fala em TTFB, mas o Locust mede o tempo total da resposta, corpo incluído (o `locustfile` não usa `stream`). | O número é limite superior do TTFB: conservador, mas a nomenclatura diverge. | Declarar "tempo de resposta (limite superior do TTFB)". |
| m2 | menor | Cap. 4, l.57-60 | Fato | CO₂ no selo exige `weight_g > 0` (só volume não basta — `badge.py`); abaixo de 1 km o selo mostra "mesma região" sem número; o limite de 100 km é em **linha reta** (≈ 134,5 km de estrada); o desempate nunca troca oferta com selo por uma sem. Nada disso está no texto. | Imprecisão na regra central do selo. | Ajustar a redação. |
| m3 | menor | Cap. 4, l.224-227 | Fato | Não há tabelas de "categorias" nem de "avaliações": categoria é coluna; avaliações são agregadas em `olist_products` (`src/core/models.py:48-52`) a partir da nota do *pedido*, atribuída a todos os produtos dele. `olist_orders` não é citada. | Modelo de dados impreciso; nota do pedido parece nota do produto. | Corrigir a lista e declarar a ressalva. |
| m4 | menor | Cap. 4, l.347; Cap. 5, l.517-524 | Fato | Só a Home é cacheada; detalhe e checkout não (o que explica a cauda a 1.000 VU). O runtime atual usa pool bloqueante, adotado *depois* do protocolo (§11.7). | Configuração medida ≠ configuração descrita. | Declarar as duas coisas. |
| m5 | menor | Cap. 5, Tab. 5.5 | Opinião | Linhas de diferença repetem o mesmo valor nas duas colunas. | Ruído visual. | Usar uma coluna "Δ". |
| m6 | menor | Figuras do Cap. 5 | Fato | Numeração do texto não bate com os arquivos (no texto o OSRM é a Fig. 5.3; no repositório, `fig-5-4`). A `fig-5-4` não destaca as 5 divergências que a legenda pede. A `fig-5-2` não é usada. | Retrabalho na diagramação. | Alinhar numeração de texto e arquivos. |
| m7 | menor | Cap. 5, 5.2.1 | Fato | A mutação roda na tela de **detalhe** (`web/e2e/contract-mutation.spec.ts:75`); a mutação 4 não tem captura; no modo de inspeção o bloco desconhecido vira painel (`web/components/sdui.tsx:68`), só fora dele é ignorado. | Precisão do procedimento. | Declarar a tela e os dois comportamentos. |
| m8 | menor | Código (afeta a defesa) | Fato | Docstrings divergentes: `green_logistics/repository.py` diz "6403 linhas" (o ETL grava 12.933); `checkout/alternatives.py` diz "cada product_id pertence a um vendedor" e "FE do GHG Protocol". **A docstring está errada:** a tabela `offers` e os 474/580 produtos multivendedor a contradizem, e o motor da Sprint 9 usa GLEC. | Examinador que abra o código encontra a contradição. | Corrigir as docstrings. |
| s1 | sugestão | Cap. 5, todo | Opinião | Resultados não ligados explicitamente aos objetivos (a)–(d). | Coerência com o Cap. 1. | Fechar cada subseção com "atende ao objetivo X". |
| s2 | sugestão | Cap. 5, 5.1.5 | Opinião | Com n = 3, média ± dp de percentis é frágil. | Dispersão real invisível. | Mostrar mínimo–máximo ou os três valores (os CSVs já os têm). |
| s3 | sugestão | Cap. 4, Tab. 4.1 | Opinião | A tabela ainda é placeholder. | Pendência fácil. | Preencher a partir de `src/schemas/sdui.py`: 8 blocos e 3 ações (`open_modal` não é emitida por nenhum bloco). |

## 5. Rastreabilidade das afirmações centrais

**Sustentadas**

- Envelope SDUI, uniões discriminadas e espelho no front (testes passando na revisão).
- Funil do ETL: 60.636 → 60.292 itens; 7.356 ofertas; 12.933 centroides.
- Casos de CO₂: 0,021194 e 0,022865 kg.
- OSRM: MAE e MAPE; 86,5% e 91,0%; 2,0 e 6,4 km; encaixe de 14 e 150 m.
- Concentração regional: 36,3%, 18,7%, 432 km e 94,7%.
- CO₂ evitado: 254,2 kg, 9,8% e 0,9%.
- Busca normalizada; centroides em memória com lock; TTL de 1 h; prazo de 95.921 entregas.
- As 5 mutações do contrato; contagens de 194 e 35 testes.

**Parcialmente sustentadas**

- Spearman 0,997: número correto, leitura extrapolada (M4).
- Cumprimento da meta de 200 ms: só em alguns cenários (M9).
- Ganho de 1,7×: base trocada (M10).
- "Regra de recomendação" da análise de CO₂ ≠ regra da aplicação (M7).
- Selo e CO₂ descritos com imprecisões (m2).

**Contraditas**

- Artefato descrito = artefato medido (B1).
- Ordem dos fatores de emissão (M1).
- Mecanismo da cubagem consolidada (M2).
- "Falhas não registradas" (M8).
- Definição de cache frio e motivo dos descartes (M11).
- Leitura da vazão a 250 VU (M12).
- Tabelas originais de categorias e avaliações (m3).

**Sem evidência localizada**

- Fonte de 6.000 cm³/kg como convenção rodoviária (M3).
- Justificativa dos fatores das modalidades (M15).
- E2E no HEAD atual: último registro em 04/10, logo após o `2de753d`; não reexecutado na revisão.

## 6. Perguntas ao autor

1. Os Caps. 1 e 3 prometem personalização **individual** em algum ponto? Se sim, a
   personalização regional precisa ser renegociada no texto, não só relatada.
2. Existe fonte para 6.000 cm³/kg (tabela de transportadora, norma) não encontrada no repositório?
3. Os fatores das modalidades vieram de alguma referência ou foram escolhidos pelo grupo?
4. O orientador aceita resultados de carga medidos em commit anterior, com declaração
   explícita, ou exige reexecução no commit final?
5. As redações da §5 de `tese-rastreabilidade.md` (rede, endpoint, cache, OSRM) já estão no
   Cap. 3 do `.docx`? Os Caps. 4 e 5 pressupõem que sim.

## 7. Próximo passo recomendado (menor sequência)

1. **Correções de uma linha:** M1, M2, M10, m3.
2. **Tabela 5.7 completa e reescrita do 5.1.5:** M8, M9, M11, M12, a partir da
   §11.3–11.5; incluir a `fig-5-2`.
3. **B1:** tabela "resultado × commit" e, se possível, um controle curto de carga no HEAD.
4. **B2:** subseção de personalização com os dados da §4c.
5. **5.1.3 e 5.1.4:** M4–M7 (tabela por faixa, viés acima de 100 km, denominadores, intervalo).
6. **Lacunas de fonte:** M3 e M15; sem fonte, declarar como parâmetro arbitrado e mostrar
   a sensibilidade.

## 8. Avaliação do projeto como orientador (além do texto)

### O que está acima da média

O projeto trata a evidência como prova, não como ilustração: cada número tem commit e
comando, as invalidações estão registradas e decisões como manter o Redis ligado foram
tomadas por medição. A regra única de oferta, nascida de um bug real encontrado na própria
demo, é uma história excelente para a defesa — mostra que o argumento central foi testado
contra a própria aplicação.

### Fragilidades que precisam evoluir

1. **Não há validação com pessoas.** Tudo é contrafactual ou estrutural; nada mostra que
   alguém *escolheria* a oferta próxima ao ver o selo. A monografia de referência (CAQDAS)
   usou SUS com n = 10. Um teste rápido de usabilidade com 8 a 10 colegas, mais uma pergunta
   de preferência declarada ("com este selo, você trocaria?"), cobre a maior lacuna de
   validade externa a custo baixo.
2. **O selo mede distância, não emissão.** Um item pesado a 99 km recebe o selo; um leve a
   101 km não. Como a tese é sobre CO₂, a banca pode perguntar por que o selo não é por
   emissão relativa. Defender como escolha de comunicação (distância é compreensível) ou
   discutir a alternativa no Cap. 6.
3. **Parâmetros do modelo com fontes de força desigual.** Circuidade e fatores GLEC têm
   citação; 6.000 cm³/kg e os fatores das modalidades não. Os fatores GLEC são da região
   "Europa e América do Sul". Uma análise de sensibilidade (variar cada parâmetro em ±X% e
   ver se "o próximo emite menos" se mantém) blinda o capítulo inteiro.
4. **O próprio OSRM sugere fator por faixa:** circuidade de 1,34 até 100 km e ~1,25 acima.
   Com 20 pares por faixa não se propõe fator nacional — o projeto acertou em não trocar —,
   mas fica como trabalho futuro com dados próprios.
5. **O contrato compara só `type`, não `props`.** Evolução barata: exportar o JSON Schema de
   `ScreenResponse` (`model_json_schema()`) e validar no front, com `parseScreen`, fixtures
   geradas pelo backend. Divergência de campo passa a falhar no CI.
6. **A medição não acompanhou a versão do código.** Um ensaio de calibração curto a cada
   release (a §11.9 de `performance.md` já sugere) evita o B1 no futuro.
7. **Amostra da demo ≠ universo da análise**, e a amostra é ponderada por popularidade.
   Está correto, mas precisa ser dito sempre que um número da demo aparecer.
8. **Pontas soltas na arquitetura:** o `orchestrator` é módulo vazio apresentado como fatia;
   `open_modal` é ação que nenhum bloco emite. Tratar explicitamente como "reservados" ou
   remover — elemento vazio no diagrama de arquitetura convida a pergunta.

### Visões de evolução

Da mais à menos impactante para as conclusões:

- estudo com usuários (A/B ou preferência declarada);
- matriz OSRM pré-calculada entre prefixos de vendedores e compradores, que remove a
  aproximação sem tocar o caminho quente;
- teste de significância do lift regional por *bootstrap*;
- workers combinados com cache;
- lado do vendedor ("onde abrir estoque para reduzir minha pegada"), reaproveitando o motor.
