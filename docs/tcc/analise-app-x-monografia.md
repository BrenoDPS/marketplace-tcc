# Análise: aplicação × monografia (02/11/2026)

> **O que é:** anotações de uma verificação completa da aplicação em execução,
> confrontada com o texto do Report 6 (PDF de 14/10). Aqui ficam só os pontos
> **novos**: o que a aplicação faz e a monografia não diz, imagens candidatas a
> figura, insights dos dados que ainda não estão no texto e melhorias de
> interface. Os ajustes já levantados antes estão em `ajustes-versao-final.md` e
> aplicados nos rascunhos `capitulo-4/5-rascunho.md` (v3); não se repetem aqui.
>
> **Base:** pilha local (commit `beb0fd0` + Verde × 0,7), CEP 05311 (SP), 60165
> (CE) e 69005 (AM), 1440 px e 390 px. Capturas em `figuras/candidatas/`,
> regeneráveis com `web/scripts/capturas-tcc.mjs`.
>
> **Classificação** (como no manual de revisão): **fato** (verificado na
> aplicação ou no código), **inferência** (conclusão a partir de fatos),
> **sugestão** (preferência editorial ou de interface).
>
> **Status (02/11, tarde):** A1–A11, B1, B2, C1–C5 e as figuras recomendadas
> (`c06`, `c08`, `c02` + `c04`, `c12`, gráfico por UF, série temporal) **entraram no
> texto**: rascunhos v4 e `Monografia - versao final.docx`. B3/B4 e D1–D10 são
> mudanças no app (card de interface no Trello). A seção 8 lista os testes e
> roteiros que ainda valem a pena.

## 1. O que a aplicação faz e a monografia não descreve

| # | Funcionalidade | Onde no app / código | No PDF? | Sugestão | Prioridade |
|---|---|---|---|---|---|
| A1 | **Ordenar a vitrine** por mais próximo, menor CO₂ ou menor preço | Home, "Ordenar"; `sort` em `home_contextual/router.py` | Não | Uma frase no §4.1.1 (2º requisito): o comprador escolhe o critério, e o servidor reordena. É a forma mais direta de "destacar alternativas de menor impacto" (objetivo c) | Alta |
| A2 | **"Como calculamos?"** no selo: linha reta → estrada → trechos → massa cubada → fatores → emissão, com fontes | Selo no detalhe e nas remessas | Não | Citar no §4.1.1 (3º requisito) e usar a captura `c06` como figura: mostra o motor da §4.3.2 aberto ao usuário | Alta |
| A3 | **Mapa de origem** (`origin_map`): regiões com CEP no dataset como pontos, círculo de 100 km, linha até a origem | Detalhe | Só na Tabela 2 (ajuste M4) | Uma frase no §4.3.3; figura junto com A2 | Média |
| A4 | **Comparador de origens** (`offer_comparison`): todas as ofertas do produto, com preço, distância, CO₂ e "5,5× a emissão da escolhida" | Detalhe | Só na Tabela 2 (ajuste M4) | Cumpre literalmente a §3.2 ("a redução relativa poderá ser apresentada em comparação com outra alternativa"). Dizer isso no §4.1.1 | Alta |
| A5 | **Páginas de metodologia e de resultados da pesquisa**, montadas pelo servidor | `/metodologia`, `/pesquisa`; `green_logistics/metodologia.py`, `pesquisa.py` | Não | Parágrafo no §4.3.3 sobre **transparência**: a fonte de cada fator e as tabelas do Cap. 5 estão no próprio app. Captura `c09` | Média |
| A6 | **"Seu impacto nesta sessão"**: soma do CO₂ evitado pelas trocas aceitas | Checkout, depois de "Trocar" | Não | Uma frase no §4.1.1 (checkout); fecha o ciclo sugestão → decisão → efeito | Baixa |
| A7 | **Checkout em página com etapas** (Carrinho, Entrega, Impacto) e "Editar carrinho" | Checkout | Parcial ("checkout simulado") | Basta a figura `c08` | Baixa |
| A8 | **Jornada só com teclado** verificada por teste automatizado | `web/e2e/teclado.spec.ts` | Não | Requisito não funcional de acessibilidade ainda não declarado. Uma frase no §4.1.2 e uma linha no §5.2.2 ("a jornada completa foi percorrida só com teclado") | Média |
| A9 | **Layout responsivo** (390 px): cabeçalho compacto com "Filtros" | Todas as telas | Não | Opcional: uma frase no §4.3.3 com as capturas `c13`/`c14` em apêndice | Baixa |
| A10 | **"Mesma região"** abaixo de 1 km, em vez de "0 km" | Metodologia, cards | Não | Bom exemplo da regra "não inventar precisão"; cabe no §5.2.2 | Baixa |
| A11 | **Vitrine geral sem sinal regional** (ex.: AM): hero genérico | Home com CEP 69005 | Sim, no texto (§5.1.5: "15 UFs recebem a vitrine geral") | Figura em par `c02` × `c04` no §5.1.5 deixa o resultado visível | Média |

## 2. Inconsistências entre capítulos e aplicação (fatos)

| # | Local | Observação | Recomendação |
|---|---|---|---|
| B1 | Cap. 2, §2.2.3 (micro-frontends) | O texto diz que micro-frontends "podem ser utilizados para hospedar componentes complexos, como calculadoras de impacto ambiental e mapas interativos de rotas". A aplicação tem os dois (explicador e mapa), mas como **blocos SDUI** no mesmo cliente, não como micro-frontends | Acrescentar no §4.2.3 ou no Cap. 6: o mapa e o explicador foram feitos como blocos do contrato, e não como micro-frontends, porque o registro de componentes já os isola. Ou suavizar o §2.2.3 |
| B2 | Cap. 3, §3.2 | Promete que "a opção de menor emissão será utilizada como referência sustentável, e a redução relativa poderá ser apresentada em comparação com outra alternativa" | Cumprida pelo comparador (A4) e pelo texto do impacto ("comprar do mais próximo evita ~31,9 g"). Citar no Cap. 4 e no quadro de aderência do Cap. 6 |
| B3 | Fontes na aplicação × Referências | A página de metodologia e o "Como calculamos?" citam "Lee e Chae (2023), **sobre Gonçalves et al. (2014)**"; a monografia tirou Gonçalves das Referências | Trocar o texto do app para "Lee e Chae (2023)" (`co2.py`, constante `FONTES`). A banca vai abrir a metodologia |
| B4 | Fontes na aplicação × Referências | O app diz "GLEC Framework **v2.0**"; as Referências do PDF citam a v3.0 | **Resolvido (02/11):** o grupo manteve a v3.0 (regra dos 5 anos); a tela passou a citar "GLEC Framework (Smart Freight Centre, 2023)" e a cubagem "(Bsoft, 2026)" |
| B5 | Cap. 1 e §3.2 | Falam em "front-end em React"; o Cap. 4 diz Next.js com React | Coerente, mas vale uma vez "Next.js (framework React)" no Cap. 1 |

## 3. Imagens candidatas a figura

Todas em `docs/tcc/figuras/candidatas/`, 1440 px de largura (celular: 390 px, 2×).

| Arquivo | O que mostra | Onde entra | Legenda sugerida | Recomendação |
|---|---|---|---|---|
| `c06-detalhe-selo-mapa-comparador.png` | Detalhe com "Como calculamos?" aberto, impacto, mapa e comparador (Atibaia × Videira) | §4.1.1 (2º e 3º requisitos) ou §4.3.3 | Figura X - Tela de detalhe: selo com cálculo explicado, mapa de origem e comparador de ofertas | **Incluir**: é a melhor imagem da integração SDUI + logística verde. Recortar o fundo cinza |
| `c08-checkout-completo.png` | Checkout: resumo, três modalidades (Verde 5,02 g), remessas com sugestão de troca, impacto | §4.1.1 (checkout e modalidades), junto da Tabela 3 | Figura X - Checkout simulado: modalidades de entrega, remessas e sugestão de troca | **Incluir** |
| `c02-home-regional-sp.png` + `c04-home-sem-sinal-am.png` | Vitrine regional de SP ("Em alta em SP: Alimentos, 1,3×") × vitrine geral do AM | §5.1.5, ao lado da Figura 11 | Figura X - Vitrine com contexto regional (SP) e sem sinal regional (AM) | **Incluir** (lado a lado) |
| `c12-detalhe-mutacao-servidor-reordenar.png` | Modo de apresentação: o servidor reordenou a árvore; inspeção mostra a nova ordem | §5.2.1, depois da Figura 13 | Figura X - Mutação produzida pelo servidor no modo de apresentação | Incluir se o ajuste M3 da §5.2.1 entrar |
| `c09-metodologia.png` | Página de metodologia montada pelo servidor | §4.2.3 ou §4.3.3 | Figura X - Página de metodologia composta por blocos do servidor | Opcional |
| `c05-home-consciente-menor-co2.png` | Contexto "Consciente" ordenado por menor CO₂ | §4.1.1 (ordenação, A1) | Figura X - Vitrine do consumidor consciente ordenada por menor emissão | Opcional (escolher entre esta e `c02`) |
| `c11-detalhe-inspecao-sdui.png` | Detalhe no modo de inspeção (tipos e versões dos blocos) | Alternativa à Figura 5 | — | Não incluir: a Figura 5 já cumpre o papel |
| `c13-mobile-home.png`, `c14-mobile-detalhe.png` | Telas no celular | Apêndice | Figura X - Interface em tela de celular | Opcional (apêndice) |
| `c10-pesquisa.png` | Página de resultados da pesquisa (muito alta: 6.168 px) | — | — | Não incluir como figura; citar a página no texto |
| `c01-entrada-cep.png`, `c03-home-regional-ce.png`, `c07-carrinho.png` | Entrada, vitrine do CE, carrinho | — | — | Referência; não precisam virar figura |

**Gráficos novos sugeridos** (dados já calculados, faltam só as figuras; dá para gerar
em `scripts/figuras_tcc.py`):

1. **CO₂ evitado por UF** (barras): SP 23,5%, RJ 13,2%, MG 11,2%, PR 11,1%,
   SC 8,6%, RS 7,2%, ES 6,9%, BA 3,7%. Sustenta o insight C2.
2. **Oferta local disponível × compra local por UF** (barras pareadas): mostra que
   a lacuna dos 94,7% × 18,7% não é igual no país (C1).

## 4. Insights dos dados que ainda não estão no texto

Fonte: tela `/pesquisa` (mesmos scripts e números do Cap. 5:
`docs/resultados/concentracao-regional.md` e `co2-evitado.md`).

**C1 — A média de 94,7% esconde a desigualdade regional (fato).** Têm algum
vendedor a menos de 100 km: 100% dos compradores em SP, RJ, PR, SC e DF; 74,9% na
BA; 54,3% no MT; **0% no PA**. A distância mediana vai de 163 km (SP) a 2.391 km
(PA). *Onde entra:* §5.1.4, depois da Tabela 5, e §6.2 (validade externa): a
recomendação de proximidade só funciona onde há vendedores, e o Norte não tem.

**C2 — O CO₂ evitado se concentra onde já há mais vendedores (fato + inferência).**
Nos itens com alternativa, a recomendação evitaria 23,5% da emissão em SP, contra
3,7% na BA. SP sozinho responde por 107,2 dos 254,2 kg evitados (42%).
*Inferência:* a regra beneficia mais as regiões já bem servidas, e o efeito
nacional (9,8%) é puxado por SP. *Onde entra:* §5.1.4 (uma frase e o gráfico 1) e
§6.1.1, como relação de compromisso (eficiência × equidade regional).

**C3 — Oferta local existe, mas a compra local depende do comportamento (fato).**
O RJ tem oferta local para 100% dos compradores e só 6,6% de compras locais; SP
tem 39,5%. *Onde entra:* §5.1.4, reforçando que a lacuna é de escolha, e não de
oferta, o que justifica a interface (selo, ordenação, comparador).

**C4 — A sugestão de troca ignora o preço (fato, verificado na aplicação).** No
roteiro da banca (Atibaia, R$ 27,90), o checkout sugere outro "Alimentos" a
R$ 169,90, a 13 km, que evita 4,58 g de CO₂: pagar R$ 142 a mais para evitar
menos de 5 g. A regra (`checkout/alternatives.py`) escolhe por distância e CO₂ e só
**exibe** o preço. *Onde entra:* §6.1.1, junto do trade-off preço × CO₂ da escolha
de oferta, e como melhoria de interface (D5). Se a banca clicar em "Trocar"
durante a demo, é a pergunta mais provável.

**C5 — Todos os produtos de uma categoria têm o mesmo nome (fato).** Sem nome de
produto no dataset, os cards mostram a categoria ("Alimentos" seis vezes na
vitrine de SP). O §4.1.1 explica o efeito na busca, mas não na identificação
visual. *Onde entra:* §6.2 (validade externa) ou §4.1.3, uma frase.

**C6 — Há casos em que o mais próximo é também o mais barato (fato).** Atibaia:
R$ 27,90 a 50 km (7,17 g) contra Videira: R$ 39,90 a 588 km (39,1 g, 5,5×). Junto
com os 43,3% de casos em que a oferta próxima é mais barata (§5.1.4), é um
exemplo concreto para a defesa: proximidade não é sempre custo.

## 5. Melhorias de interface observadas

Para discutir com o grupo antes de mexer (o usuário vai trazer os próprios
apontamentos visuais). Esforço: P (< 30 min), M (até 2 h).

| # | Tela | Observação | Proposta | Esforço |
|---|---|---|---|---|
| D1 | Cards, detalhe, comparador | Cidades sem acento, como vêm do dataset: "Sao Paulo", "Guanhaes", "Sao Jose do Rio Preto" | Normalizar a grafia das cidades mais frequentes no ETL ou num dicionário de rótulos (`src/core/rotulos.py` já faz isso com categorias) | M |
| D2 | Checkout, remessas | A remessa mostra o identificador do vendedor em hash ("16090f2ca825…") | Mostrar "Atibaia · SP" | P |
| D3 | Vitrine | Categoria "Cool stuff" sem tradução | Rótulo em português (ex.: "Presentes criativos") em `rotulos.py` | P |
| D4 | Vitrine sem sinal (AM) | Hero genérico "Olist Marketplace", sem dizer por que não há destaque regional | Ex.: "Ainda não há compras suficientes no AM para destacar uma categoria", coerente com o §5.1.5 | P |
| D5 | Checkout, "Mais perto de você" | Mostra o preço do substituto, mas não a diferença (C4) | Mostrar "+R$ 142,00" ao lado do CO₂ evitado, ou não sugerir acima de um teto de preço | P (exibir) / M (teto) |
| D6 | Detalhe, mapa | O rótulo "Você" fica sobre o marcador, e os pontos não têm contorno do país | Afastar o rótulo; opcional: contorno do Brasil e das UFs | P / M |
| D7 | Celular (390 px) | O selo quebra em três linhas no card, e a cidade é truncada | Selo curto no card ("Local · 13 km") e detalhe completo só no produto | P |
| D8 | Cabeçalho | O seletor de CEP mostra "69005" sem UF, enquanto o de SP mostra "05311 · SP" | Conferir a UF desse prefixo nos centroides | P |
| D9 | Checkout | Quatro seções (resumo, entrega, remessas, impacto) e três etapas no topo; "Remessas" não tem atalho | Acrescentar a etapa ou fundir com "Impacto" | P |
| D10 | Detalhe | Com "Como calculamos?" aberto, o preço desce para baixo da caixa de cálculo | Abrir o cálculo abaixo do preço, ou como popover | P |

## 6. O que a documentação ainda não aborda (além dos ajustes já levantados)

1. **Transparência como requisito** (A2, A5): o app expõe a cadeia de cálculo e as
   fontes ao usuário, o que responde à limitação da §2.3 ("estimativas
   informativas"). Hoje isso não aparece como decisão de projeto em nenhum
   capítulo. Sugestão: um parágrafo no §4.1.2 ("Transparência das estimativas").
2. **Acessibilidade** (A8): um teste automatizado percorre a jornada só com
   teclado. Não é citado.
3. **Desigualdade regional** (C1, C2): o resultado mais forte da tela de pesquisa
   ainda não está no texto e muda a leitura dos 9,8%.
4. **Validação das sugestões de troca** (C4): o texto diz que "a decisão fica com
   o usuário"; falta dizer que o preço do substituto não é limitado.
5. **Apêndices possíveis:** roteiro de demonstração (`docs/roteiro-banca.md`),
   protocolo de usabilidade (se o teste acontecer) e capturas em celular.

## 7. Prioridade sugerida para esta semana

| Ordem | Item | Por quê |
|---|---|---|
| 1 | B3 e D2/D3/D4 (textos e rótulos do app) | A banca vê o app; são poucos minutos cada |
| 2 | D5 (diferença de preço na troca) | Evita a pergunta mais provável na demo |
| 3 | Figuras `c06`, `c08`, `c02` + `c04` no texto | Mostram o que o texto já afirma |
| 4 | A1, A2, A4, A5, A8 no Cap. 4 (cinco frases e um parágrafo) | O artefato é maior do que o capítulo descreve |
| 5 | C1–C3 no §5.1.4 e no Cap. 6, com o gráfico de CO₂ evitado por UF | Insight novo, com dados já calculados |
| 6 | D1, D6–D10 | Refino visual, depois dos apontamentos do grupo |

## 8. Testes e roteiros que ainda faltam (visão ampliada, 02/11)

O que já existe e está verde: pytest (229), Vitest (42), E2E no navegador (7, incluindo
mutação de contrato, modo apresentação, metodologia, teclado e o roteiro da banca),
protocolo de carga (27 ensaios + controle de 250 VU no código final), OSRM,
sensibilidade e o de/para das métricas (`de-para-metricas.md`). O que falta,
do mais importante para o menos:

| # | Teste ou roteiro | Por que importa | Esforço | Quem |
|---|---|---|---|---|
| T1 | **Ensaio da demo na máquina e no local da banca**: pilha do zero, ETL carregado, aquecimento, roteiro cronometrado, **notebook na tomada** | 13 dos 27 ensaios de carga foram descartados porque a máquina estava na bateria: a CPU cai e a demo fica lenta. O roteiro já tem plano B (vídeo), mas nunca foi ensaiado fora da máquina de desenvolvimento | 1 h | grupo (eu preparo o checklist) |
| T2 | **Reprodução do zero em outra máquina**: clone limpo → `docker compose up` → ETL → `pytest` → `npm run e2e`, cronometrado | Reprodutibilidade é requisito não funcional declarado (§4.1.2) e nunca foi exercida fora da máquina original. Pega dependência esquecida antes da banca | 1 h | grupo, com o meu passo a passo |
| T3 | **Teste de usabilidade** (SUS + preferência declarada × revelada) | Única validação com pessoas; hoje é limitação declarada no Cap. 6 | 3–4 h | **não será feito** (02/11): limitação no Cap. 6 |
| T4 | **1.000 VU no código final** (3 estados × 1 repetição) | O controle no código final cobriu só 250 VU; o 1.000 VU do Cap. 5 é do código das Sprints 8 e 10 (declarado) | ~50 min de máquina | eu |
| T5 | **Desempenho no cliente** (build de produção; LCP, CLS e tempo de renderização da árvore SDUI por tela) | O trabalho mede só a API. A crítica natural à SDUI é o custo de interpretar a árvore no cliente; hoje não há número | 1 h | eu |
| T6 | **Validação externa do CO₂**: 3 a 5 rotas comparadas com uma calculadora independente (ex.: ferramenta do GHG Protocol Brasil) | O §5.1.2 diz "consistência interna, não precisão externa". Uma ordem de grandeza conferida fora do código responde à pergunta mais provável sobre o modelo | 1–2 h | eu |
| T7 | **Teste da regra de troca** (C4): fixar o comportamento atual (sem teto de preço) ou o novo, se o grupo decidir limitar | Hoje nenhum teste trava o caso de R$ 142 a mais para evitar 4,58 g | 30 min | eu |
| T8 | **Primeira requisição após subir a API** (carga dos 12.933 centroides) | Item de trabalho futuro sem número; na demo, é o "primeiro clique lento" que o roteiro manda aquecer | 10 min | eu |
| T9 | **Acessibilidade automatizada** (axe-core no Playwright) | Complementa o teste de teclado com contraste, rótulos e papéis ARIA | 1 h (nova dependência de teste) | eu |

Medição já feita nesta análise: tamanho do JSON por tela (3 a 13 KB; 1,5 a 4,3 KB
comprimido), registrado em `de-para-metricas.md` §10 e citado no §6.1.1.

**Feito em 02/11 (tarde):** T5 (`docs/resultados/desempenho-cliente.md`), T6
(`docs/resultados/fator-externo-co2.md`) e T8 (`docs/resultados/primeira-requisicao.md`),
todos já no Cap. 5. B3 também: as fontes exibidas no app citam só Lee e Chae (2023).
T4 aguarda a porta 8000 livre (~50 min de máquina); T7 resolvido com teto de 20% (02/11)
de preço da troca.

**Feito em 02/11 (noite):** T9 (`docs/resultados/acessibilidade.md`, `web/e2e/acessibilidade.spec.ts`:
0 críticas, 3 sérias de correção pontual; no §5.2.2). T1 e T2 viraram roteiros para o
grupo executar (`docs/roteiro-banca.md` → "Ensaio na máquina e no local da banca";
`README.md` → "Reprodução do zero", com ETL ~70 s, `pytest` ~15 s, E2E ~1 min). T7:
`tests/test_checkout_alternatives.py` fixa o teto de 20% decidido pelo grupo em 02/11
(`MAX_PRICE_RATIO` em `alternatives.py`). T4: 1.000 VU no
commit `6e5398c` (`docs/performance.md` §13.1), iguais ou melhores que a Tabela 6 e dentro
da sua dispersão; CPU saturada nos três estados; no §5.1.6.

Recomendação: T1 e T2 antes de qualquer outro (risco de demo); T4, T5 e T8 rodam
juntos numa tarde e entram no Cap. 5 como complemento; T6 fortalece a defesa do
modelo; T9 só se sobrar tempo.
