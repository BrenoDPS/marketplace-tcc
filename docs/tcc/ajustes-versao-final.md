# Report 6 → versão final: parecer e trechos prontos

> **Escopo:** revisão do `Report 6 - Resultados.pdf` (entrega de 14/10, versão mais
> atual do texto; o `.docx` do repositório está desatualizado) contra o código e a
> evidência do repositório no commit `e1ffaa4` + ajustes de 02/11. Segue
> `MANUAL-REVISAO-AGENTE.md`. Suítes conferidas em 02/11: pytest 229, Vitest 42,
> lint e typecheck verdes; E2E 7/7.
>
> **Como usar:** cada achado diz **onde** está no PDF e traz o texto pronto para
> colar no Word. Os trechos preservam a redação do grupo sempre que possível.
> Marque aqui o que já foi passado.

## 1. Veredito

**Seguir após correções.** O Cap. 6 está vazio (bloqueador da versão final;
rascunho em `capitulo-6-rascunho.md`). Os Caps. 4 e 5 descrevem o sistema da
entrega de 14/10, mas o código evoluiu depois (4 blocos novos, mutação no servidor,
controle de carga no código final, contrato comparado campo a campo), e alguns
trechos dos rascunhos v2 não entraram no PDF.

## 2. Achados

| ID | Prioridade | Local no PDF | Tipo | Observação verificável | Feito |
|---|---|---|---|---|---|
| B1 | bloqueador | Cap. 6 (p. 51) | lacuna | Todas as subseções vazias | [ ] |
| M1 | maior | §5.1.5 e Sumário | fato | Título duplicado "Desempenho sob carga e efeito do cache"; o conteúdo é a personalização regional | [ ] |
| M2 | maior | §5.3 | lacuna | A síntese não responde aos objetivos (a)–(d) e omite a personalização (objetivo c) | [ ] |
| M3 | maior | §§5.1.2, 5.1.4, 5.1.6, 5.2.1, 5.2.2 | contradito pelo código | Contagem de testes, desempate por preço, controle de carga no código final, mutação no servidor e contrato campo a campo estão desatualizados | [ ] |
| M4 | maior | §4.2.1, §4.2.3 (Tabela 2) | contradito pelo código | 8 blocos na Tabela 2; o contrato tem 12. Orchestrator descrito só como "reservado" | [ ] |
| M5 | maior | §3.2 × §4.1.1 | inconsistência | Cap. 3: fator único 0,104 kg/(t·km) e Figura 4 com "React" e "E = d × m × f"; Cap. 4: cadeia van + caminhão. O PDF não explica a mudança | [ ] |
| M6 | maior | Referências (SMART FREIGHT CENTRE) | fato | Cita GLEC v3.0 (2023); os fatores do código (0,680 e 0,092) vêm da v2.0 (rev. 2022) | [ ] |
| M7 | maior | Resumo e Abstract | inferência forte demais | "Reduziu a latência de 4.100 ms para 95 ms" é a **mediana** com 1.000 VU; o p95 ficou em ~3 s. "Comprovando" excede a evidência | [ ] |
| M8 | maior | Tabela 5 (§5.1.6) | lacuna | A §3.3 promete média ± desvio padrão e p50/p95/p99; a tabela só traz médias e não tem p99 | [ ] |
| M9 | maior | §4.1.1 "Modalidades de entrega" | lacuna | Fatores da Expressa e da Verde sem tabela nem justificativa; a Verde passou a × 0,7 (02/11) | [ ] |
| m1 | menor | §4.1.2, 2º parágrafo | lacuna | Falta dizer que o Locust mede a resposta completa (limite superior do TTFB) | [ ] |
| m2 | menor | §4.1.1, regra de oferta | omissão | O desempate nunca troca oferta com selo por oferta sem selo (`escolher_oferta`) | [ ] |
| m3 | menor | Figura 5 | fato | "Protótipo" — é captura do sistema implementado | [ ] |
| m4 | menor | Lista de siglas | editorial | Fora de ordem alfabética e incompleta | [ ] |
| m5 | menor | Tabela 1, Equação 1, §3.2 "((1))" | formatação | Cabeçalho da Tabela 1 repetido no meio; "O(1)" e a Equação 1 saem corrompidos no PDF | [ ] |
| m6 | menor | §4.1.1 cubagem; Referências | consistência | O texto cita Bsoft (2026); o app (página de metodologia) e o código citam Olist (2022). Na referência BSOFT falta ":" após "Disponível em" | [ ] |
| m7 | menor | §5.2 (título) × §3.3 | editorial | "Resultados qualitativos" × "verificação qualitativa-estrutural" na metodologia | [ ] |

## 3. Trechos prontos

### B1 — Cap. 6

Ver `docs/tcc/capitulo-6-rascunho.md`.

### M1 — título da §5.1.5

Trocar o título (e a linha do Sumário) por: **5.1.5 Personalização contextual regional**.

### M2 — §5.3, substituir os parágrafos 2 a 6 (de "A comparação com o OSRM…" a "…adicionados.")

> Os resultados respondem aos quatro objetivos específicos do trabalho.
>
> a) Arquitetura SDUI orientada a contexto: as cinco mutações do contrato foram
> refletidas na tela sem novo *build*, tanto injetadas na resposta quanto
> produzidas pelo próprio servidor, e componentes desconhecidos ou incompletos não
> interromperam a jornada. O servidor determina a composição; o cliente a interpreta.
>
> b) Motor de pegada de carbono baseado em atividade: o motor passou nos testes de
> unidade, conversão e monotonicidade. A distância corrigida pela circuidade erra
> 8,7% em relação à rota do OSRM e escolhe o mesmo vendedor mais próximo em 86,5%
> das decisões, com superestimação de 5% a 10% nas distâncias longas. Variar os
> parâmetros do motor altera a emissão absoluta, mas a parcela evitada fica entre
> 9,5% e 10,0%.
>
> c) Personalização integrada aos dados logísticos: a página inicial adapta-se à
> região do comprador em 12 das 27 UFs, sem custo de desempenho. A recomendação do
> vendedor mais próximo reduziria em 9,8% a emissão dos itens com alternativa,
> equivalentes a 0,9% de todas as compras, com custo mediano de R$ 0,01 para o
> comprador. O alcance é limitado pela oferta de alternativas, e não pela
> existência de vendedores próximos.
>
> d) Desempenho e flexibilidade: a meta de 200 ms foi cumprida com 50 usuários em
> todos os estados e com 250 usuários quando o cache estava ativo, inclusive no
> código final. Com 1.000 usuários, o cache multiplicou a vazão por 2,6 e manteve
> a rota cacheada no limite da meta, enquanto as rotas sem cache saturaram.

Manter o último parágrafo do PDF ("Em conjunto, os resultados indicam…").

### M3 — atualizações do Cap. 5

**§5.1.2, 1º parágrafo**, trocar a última frase por:

> Na versão final, a suíte do backend somava 229 testes aprovados e a do
> frontend, 42, além de 7 testes de jornada no navegador.

**§5.1.4**, inserir depois do parágrafo "O custo para o comprador foi pequeno…":

> A aplicação não usa a oferta mais próxima pura, e sim uma regra com desempate:
> entre ofertas a até 1% da menor distância (com piso de 1 km), escolhe a mais
> barata, sem trocar uma oferta com selo por uma sem. Repetida com essa regra, a
> análise muda a escolha em 1.823 itens (12,7%). Nesses itens, a distância a mais
> é nula na mediana, porque são vendedores do mesmo prefixo de CEP, e o preço cai
> R$ 6,11 na mediana. O CO₂ evitado passa de 254,2 para 253,7 kg CO₂e e continua
> em 9,8%. Nos itens em que a regra trocaria o vendedor, a oferta recomendada fica
> mais cara em 39,3% dos casos, contra 50,4% sem o desempate. O desempate por
> preço reduz o custo da recomendação sem alterar o benefício ambiental.

No parágrafo seguinte ("Esses números são contrafactuais…"), **apagar** a frase
"A análise compara a escolha real com a oferta mais próxima, sem o desempate por
preço usado pela aplicação." e acrescentar ao fim da seção:

> Para verificar quanto esses resultados dependem dos parâmetros do modelo, a
> análise foi repetida variando cada um em 20% para baixo e para cima:
> circuidade, extensão da última milha, fator de emissão do caminhão, fator da van
> e divisor de cubagem. Também foram testados valores alternativos com fonte: a
> circuidade de 1,27 medida contra o OSRM (Seção 5.1.3), a última milha de 20 km
> (WORLD ECONOMIC FORUM, 2024) e a cubagem rodoviária de 300 kg/m³. A emissão
> absoluta varia de −23% a +67% entre os cenários, e o maior efeito vem da
> cubagem rodoviária. A parcela evitada, porém, fica entre 9,5% e 10,0% em todos
> eles, contra 9,8% na referência. Em nenhum cenário a recomendação emite mais
> que a escolha real, porque o mesmo produto, vindo de mais perto, emite menos
> para qualquer valor positivo dos parâmetros. Os números absolutos dependem das
> escolhas do modelo; a conclusão relativa, não.

Fontes: `docs/resultados/co2-evitado.md`, `docs/resultados/sensibilidade-co2.md`.

**§5.1.6, último parágrafo**, trocar "O controle repetido depois do contexto
regional não mostrou efeito mensurável, e a regra única de oferta não teve o
desempenho medido." por:

> Por isso, o cenário de 250 usuários foi repetido na versão final, nos três
> estados do cache e com três repetições. O custo de processamento por requisição
> ficou igual (8,5 contra 8,3 ms sem cache), e com cache o p95 ficou em 19 ms,
> abaixo dos 25 a 29 ms originais. Sem cache, o p95 variou entre 600 e 1.200 ms
> entre as repetições: com o processador acima de 90%, pequenas variações formam
> filas longas. A conclusão sobre o cache se mantém.

Fonte: `docs/tese-rastreabilidade.md` §6, linha 26.

**§5.2.1, último parágrafo**, trocar as duas últimas frases ("Há um limite,
contudo. … sem alterar seu próprio código.") por:

> As mesmas cinco mutações foram depois produzidas pelo próprio servidor: no modo
> de apresentação, o cliente apenas pede uma mutação por um cabeçalho da
> requisição, e o BFF altera a árvore que ele mesmo montou antes de enviá-la. Um
> segundo teste no navegador, sem interceptar a rede, confirmou que a tela
> obedece sem recarregar. Resta um limite: as mutações foram programadas no
> servidor para a demonstração; o teste mostra que árvores novas chegam ao
> cliente sem mudança nele, e não que o servidor as componha a partir de regras
> de negócio ainda inexistentes.

Fonte: `src/features/orchestrator/mutacoes.py`; `web/e2e/apresentacao.spec.ts`.

**§5.2.2, último parágrafo**, substituir por:

> A correspondência entre servidor e cliente também é verificada
> automaticamente, em dois níveis. Um teste compara os tipos de blocos e ações
> declarados no backend, no espelho em TypeScript e no registro de componentes.
> Um segundo compara, campo a campo e em todos os níveis, os dados de cada bloco:
> o backend exporta a forma de cada um a partir dos modelos Pydantic, e o frontend
> declara a mesma forma, que o compilador TypeScript amarra aos tipos do espelho.
> Um campo renomeado, removido ou acrescentado de um lado só faz a integração
> contínua falhar, o que foi conferido alterando o contrato de cada lado. Os
> testes conferem nomes de campo, não tipos de valor, e as situações avaliadas
> foram controladas, não exaustivas. A convivência de versões diferentes do
> contrato em produção não foi avaliada.

### M4 — Cap. 4: blocos novos e orchestrator

**§4.2.1**, item e) da lista, substituir por:

> e) orchestrator: mutações do contrato no modo de apresentação, usadas para
> demonstrar o desacoplamento ao vivo; o roteamento entre versões de componentes
> permanece como extensão futura.

E trocar "São quatro fatias e um módulo reservado:" por "São cinco fatias:".

**§4.2.3**, trocar "A Tabela 2 lista os oito componentes implementados." por
"A Tabela 2 lista os doze componentes implementados." e acrescentar à Tabela 2:

| Componente (type) | Tela | Função |
|---|---|---|
| offer_comparison | Detalhe | Ofertas do mesmo produto por origem, com preço, distância e CO₂ |
| origin_map | Detalhe | Mapa com a origem da oferta escolhida e das alternativas |
| content_section | Metodologia e pesquisa | Texto explicativo enviado pelo servidor |
| data_table | Metodologia e pesquisa | Tabelas de parâmetros e resultados |

Depois da Tabela 2, acrescentar:

> Os quatro últimos componentes foram incluídos depois da primeira versão da
> jornada, sem alterar os anteriores. Dois deles compõem as telas de metodologia
> e de resultados da pesquisa, que expõem ao usuário as fontes e os fatores do
> cálculo, também montadas pelo servidor.

### M5 — Cap. 3 × Cap. 4 (depende da resposta do orientador, pergunta P5)

**Opção A — o orientador libera mexer na §3.3/§3.2:** aplicar as redações de
`docs/tese-rastreabilidade.md` §5 (rede, alvo da carga, cache aquecido, o que
"cache desabilitado" desliga, parâmetros, Haversine × OSRM) e, na §3.2, trocar o
parágrafo da equação de fator único pela cadeia de transporte (estrada = linha
reta × 1,345; últimos 15 km por van; o restante por caminhão pesado; massa
cobrável). Refazer a Figura 4 com "Next.js (React)" e sem "E = d × m × f".

**Opção B — o Cap. 3 fica como foi qualificado:** inserir no início do 3º
requisito do §4.1.1 ("O terceiro requisito corresponde ao cálculo da pegada de
carbono."):

> O modelo de emissão evoluiu em relação ao fator único descrito no Capítulo 3,
> porque aplicar o fator de caminhão também à última milha, feita por veículos
> menores, subestimava a emissão das entregas locais.

E em §4.3.4, depois de "…no mesmo hospedeiro.", acrescentar:

> Essa configuração difere da sub-rede de contêineres prevista no Capítulo 3; a
> diferença é declarada aqui porque mantém a comparação entre os estados do
> cache, mas acrescenta a disputa por processador entre API e gerador de carga.

Observação: o Cap. 3 cita 0,104 kg/(t·km); o código anterior à cadeia usava
0,102. Se ficar a Opção B, nenhum dos dois números aparece nos resultados.

### M6 — GLEC

Os fatores 0,680 (van) e 0,092 (caminhão pesado) estão documentados no código
como da v2.0. Recomendação: citar a versão usada.

> SMART FREIGHT CENTRE. **Global Logistics Emissions Council Framework for
> Logistics Emissions Accounting and Reporting**. Version 2.0. Amsterdam: Smart
> Freight Centre, 2019 (atualizado em 2022). Disponível em:
> https://www.smartfreightcentre.org/en/glec-framework/. Acesso em: 9 set. 2026.

Se a regra dos 5 anos impedir (2019), manter a v3.0 **somente** depois de
conferir que a v3.0 traz os mesmos fatores para van < 3,5 t e HGV > 20 t.

### M7 — Resumo e Abstract (substituir integralmente)

> O Marketplace Contextual Adaptativo é um protótipo de comércio eletrônico
> construído sobre o conjunto de dados público da Olist, no qual o servidor define
> a interface por meio de uma engine de Server-Driven UI (SDUI). Um
> Backend-for-Frontend (BFF) em FastAPI, organizado em fatias verticais, com
> PostgreSQL e cache de respostas em Redis, envia ao cliente uma árvore de
> componentes tipados que ele apenas renderiza. Sobre essa arquitetura, a vitrine
> se adapta à região do comprador, derivada do CEP, e cada oferta exibe distância
> e pegada de carbono estimadas por um motor baseado em atividade, alinhado à ISO
> 14083 e ao GLEC Framework, com selo para entregas a menos de 100 km. Corrigida
> por fator de circuidade, a distância estimada apresentou erro de 8,7% em
> relação a rotas do OSRM. No conjunto completo da Olist, escolher o vendedor mais
> próximo reduziria em 9,8% a emissão estimada das compras que tinham
> alternativa, ou 0,9% do total. Com 1.000 usuários virtuais, o cache elevou a
> vazão de 153 para cerca de 400 requisições por segundo e reduziu a latência
> mediana de 4,1 s para 95 ms, embora o percentil 95 tenha ficado em torno de 3 s.
> Testes de mutação do contrato mostraram que a interface reflete alterações da
> árvore enviada pelo servidor sem nova compilação do cliente. Os resultados
> indicam a viabilidade técnica da abordagem, dentro dos limites de um protótipo
> com dados históricos e emissões estimadas.

> The Adaptive Contextual Marketplace is an e-commerce prototype built on the
> public Olist dataset, in which the server defines the interface through a
> Server-Driven UI (SDUI) engine. A Backend-for-Frontend (BFF) in FastAPI,
> organized in vertical slices, with PostgreSQL and a Redis response cache, sends
> the client a tree of typed components that the client only renders. On top of
> this architecture, the storefront adapts to the buyer's region, derived from the
> postal code, and each offer shows distance and carbon footprint estimated by an
> activity-based engine aligned with ISO 14083 and the GLEC Framework, with a
> badge for deliveries under 100 km. Corrected by a circuity factor, the estimated
> distance showed an 8.7% error against OSRM routes. In the full Olist dataset,
> choosing the nearest seller would reduce the estimated emissions of purchases
> that had an alternative by 9.8%, or 0.9% of the total. With 1,000 virtual users,
> the cache raised throughput from 153 to about 400 requests per second and
> reduced median latency from 4.1 s to 95 ms, although the 95th percentile stayed
> around 3 s. Contract mutation tests showed that the interface reflects changes
> in the server-sent tree without rebuilding the client. The results indicate the
> technical feasibility of the approach, within the limits of a prototype with
> historical data and estimated emissions.

### M8 — Tabela 5 com desvio padrão e p99

Fonte: `load/results/protocolo-final/resumo-agregado.md` (média ± desvio padrão,
n = 3).

| Usuários virtuais | Cache | p50 (ms) | p95 (ms) | p99 (ms) | Vazão (req/s) | Falhas |
|---|---|---|---|---|---|---|
| 50 | Desabilitado | 12,7 ± 0,6 | 34 ± 6 | 46 ± 11 | 24,8 ± 0,1 | 0% |
| 50 | Frio | 6,3 ± 0,6 | 24 ± 2 | 39 ± 8 | 24,9 ± 0,0 | 0% |
| 50 | Aquecido | 6,7 ± 0,6 | 22 ± 2 | 36 ± 2 | 24,9 ± 0,1 | 0% |
| 250 | Desabilitado | 173 ± 6 | 613 ± 29 | 1.030 ± 214 | 111 ± 0 | 0% |
| 250 | Frio | 5,7 ± 0,6 | 29 ± 8 | 96 ± 83 | 124 ± 0 | 0% |
| 250 | Aquecido | 5,7 ± 0,6 | 25 ± 6 | 51 ± 17 | 124 ± 0 | 0,02% |
| 1.000 | Desabilitado | 4.100 ± 400 | 14.000 ± 1.732 | 22.000 ± 3.464 | 153 ± 13 | 0,21% |
| 1.000 | Frio | 93 ± 15 | 2.900 ± 1.513 | 6.567 ± 3.066 | 401 ± 35 | 0,03% |
| 1.000 | Aquecido | 95 ± 7 | 3.000 ± 1.058 | 7.167 ± 2.515 | 397 ± 27 | 0,07% |

Legenda: "Fonte: Elaborada pelos autores a partir dos ensaios de carga (2026).
Média ± desvio padrão de três repetições."

### M9 — modalidades de entrega (§4.1.1)

Depois do parágrafo "Modalidades de entrega.", acrescentar:

> A página de metodologia do sistema apresenta os fatores com a justificativa de
> cada um (Tabela 3).

Tabela 3 – Fatores das modalidades de entrega em relação à linha de base

| Modalidade | Preço | Prazo | CO₂ | Justificativa |
|---|---|---|---|---|
| Padrão | × 1,0 | × 1,0 | × 1,0 | Linha de base medida: frete da amostra e prazo mediano de 95.921 entregas reais, por faixa de distância |
| Expressa | × 1,6 | × 0,5 | × 2,5 | Cenário sem fonte quantitativa: o veículo parte antes de completar a carga; o fator de CO₂ equivale a viajar com 40% da ocupação da entrega padrão |
| Verde | × 0,85 | × 1,5 | × 0,7 | Consolidar pedidos reduz em 30% o número de viagens (WORLD ECONOMIC FORUM, 2024). Esperar a consolidação alonga o prazo, e um desconto compensa o comprador (WORLD ECONOMIC FORUM, 2024) |

Fonte: Elaborada pelos autores (2026).

> A literatura sustenta a direção dos fatores, não os valores: entregas mais
> rápidas reduzem a consolidação e aumentam as viagens, e entregas consolidadas
> fazem o contrário. Por isso, os números das modalidades expressa e verde são
> apresentados como cenário de comparação e não entram nos resultados de emissão
> do Capítulo 5, que usam apenas a linha de base.

Com a Tabela 3 nova, as Tabelas 3, 4 e 5 do Cap. 5 passam a 4, 5 e 6 (conferir
as chamadas no texto).

### m1 — §4.1.2, depois de "…da condição do cache."

> A ferramenta de carga mede o tempo até a resposta completa, que é um limite
> superior do tempo até o primeiro byte; o critério adotado é, portanto,
> conservador.

### m2 — §4.1.1, regra de oferta, depois de "…o preço é utilizado como critério de desempate."

> O desempate nunca troca uma oferta com selo de logística verde por outra sem
> selo.

### m3 — Figura 5

"Figura 5 - Página inicial no modo de inspeção SDUI" (legenda e Lista de Ilustrações).

### m4 — Lista de siglas (ordem alfabética)

API, BFF, CEP (Código de Endereçamento Postal), CO₂e (dióxido de carbono
equivalente), ETL (Extract, Transform, Load), GEE (gases de efeito estufa), GLEC
(Global Logistics Emissions Council), ISO (International Organization for
Standardization), JSON, MAE (Mean Absolute Error), MAPE (Mean Absolute Percentage
Error), ODS, OSRM (Open Source Routing Machine), RPS (requisições por segundo),
SDUI, TTFB (Time to First Byte), UF (Unidade Federativa), UI, UX, VU (Virtual
User). Se o teste de usabilidade entrar: SUS (System Usability Scale).

### m5 — formatação

Tabela 1: marcar "Repetir como linha de cabeçalho" só na 1ª linha e impedir
quebra da linha "Usuários Virtuais Concorrentes". §3.2: "complexidade analítica
constante, O(1)," e conferir a Equação 1 no editor de equações (no PDF exportado
os símbolos somem).

### m6 — cubagem

Recomendação: citar OLIST (2022), a mesma fonte que o código e a página de
metodologia do app mostram à banca, no lugar de BSOFT (2026):

> OLIST. **Como calcular o frete dos produtos para envio pelos Correios?** São
> Paulo: Olist, 20 set. 2022. Disponível em:
> https://olist.com/blog/pt/gestao-empresarial/operacao-e-logistica/como-calcular-o-frete-dos-produtos-na-loja-virtual/.
> Acesso em: 13 out. 2026.

Se mantiverem Bsoft: "Disponível em: https://…" (com dois-pontos).

### m7 — título da §5.2

"5.2 RESULTADOS QUALITATIVO-ESTRUTURAIS", como na §3.3 e no Sumário.

## 4. Fora do texto (para o grupo)

- Atualizar Sumário e Lista de Ilustrações no fim (Ctrl+A, F9).
- Se o teste de usabilidade acontecer: subseção nova no Cap. 5 e LOURENÇO;
  CARMONA; LOPES (2022) nas Referências (ver `docs/usabilidade/protocolo.md` §7).
