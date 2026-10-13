# Avaliação de design do front-end e sequência de evolução

> Avaliação feita em 2026-10-13 sobre o `web/` no commit `b3d6c48`, com a pilha
> rodando (API + Next.js) e capturas em 1440 × 900 (desktop) e 390 × 844 (mobile)
> de todas as telas: entrada, Home `default` e `conscious_buyer`, detalhe,
> carrinho, checkout e modo de inspeção SDUI. Os cards correspondentes estão no
> Trello, Sprints 13 a 16 (prefixo `[Sprint N] [Front]`).

## 1. Veredito

A identidade visual é coerente e madura: base editorial (Fraunces + Inter,
off-white quente) com o verde reservado como **cor de sinal**, tokens de cor com
modo escuro e um modo de inspeção SDUI que é o melhor ativo de demonstração do
projeto. O problema não é estética, é **informação e hierarquia**: as telas não
mostram as variáveis que a tese defende (origem, distância, CO₂, comparação de
ofertas), a tela mais rica — o checkout — está espremida num modal, e há
vazamentos de debug e quebras de layout visíveis em qualquer demonstração.

## 2. O que manter

- Paleta com o verde como único elemento saturado (`web/app/globals.css`).
- Tipografia de display para preços e títulos; `tabular-nums` nos valores.
- Modo de inspeção SDUI (contorno por bloco + `ScreenResponse` no topo): prova
  visual do desacoplamento — usar na defesa.
- Notas de honestidade nas telas ("cenário declarado", "simulação acadêmica").
- Semântica já cuidada: `radiogroup` nas modalidades, `aria-current`, `aria-pressed`.

## 3. Problemas encontrados

| ID | Severidade | Tela | Observação (verificada nas capturas ou no código) | Correção |
|---|---|---|---|---|
| D1 | Alta | Todas | Cabeçalho quebra em 1440 px: "Carrinho" cai para a segunda linha. No mobile o cabeçalho ocupa ~165 px e 5 linhas antes do conteúdo. | Cabeçalho em duas zonas (marca + contexto à esquerda; busca, CEP, SDUI e carrinho à direita); no mobile, busca e contexto num painel recolhível. |
| D2 | Alta | Home | Os cards não identificam o produto: o título é a categoria ("Alimentos" seis vezes) e a capa em gradiente ocupa ~65% do card. No mobile cada card tem quase uma tela de altura. Cards sem selo reservam um espaço vazio. | Redesenho do card: capa menor com ícone da categoria, cidade/UF do vendedor, distância e CO₂ sempre que houver (não só no selo), nota; grade 2 colunas no mobile. |
| D3 | Alta | Detalhe, checkout | O cabeçalho dos modais mostra o `screen_id` cru ("PRODUCT_DETAIL", "CHECKOUT_SIMULATE") fora do modo de inspeção (`web/components/sdui.tsx:192` e `:336`). | Título humano; o `screen_id` só no modo de inspeção. |
| D4 | Alta | Checkout | A cor de sinal premia a pior opção: na "Expressa" (mais CO₂) a barra verde é a mais longa. | Barras de emissão em tom neutro; verde só na opção de menor emissão. |
| D5 | Alta | Checkout | A tela mais rica (modalidades, remessas, alternativas, impacto) vive num modal com rolagem interna; remessas e alternativas ficam abaixo da dobra. | Checkout como página própria, com etapas (carrinho → entrega → impacto). |
| D6 | Média | Detalhe | Hash do `product_id` exibido ao usuário; cidade em minúsculas ("pirituba"); selo duplicado (bloco de detalhe e banner de impacto). | Esconder o id (só inspeção), capitalizar a cidade, um selo por tela. |
| D7 | Média | Home | Rótulos sem acento vindos do backend: "Moveis Decoracao", "Beleza Saude" (`slug.replace("_", " ").title()` em `home_contextual/composer.py:92`) e "media do Brasil" (`:144`). | Mapa de rótulos pt-BR das categorias no backend; corrigir o texto do hero. |
| D8 | Média | Home | Hero de ~400 px com véu de 92% sobre placeholder cinza: um painel grande e vazio. | Hero compacto com o "porquê" do contexto (UF, lift, categoria) e um dado visual. |
| D9 | Média | Home | Os chips de categoria são cortados na borda direita sem indicação de rolagem. | Máscara de fade nas bordas + setas no desktop. |
| D10 | Média | Todas | Nenhum estilo `focus-visible` em botões ou inputs (0 ocorrências em `web/`); muito texto a 11 px em tom `muted`. | Anel de foco consistente; 12 px como piso para texto informativo. |
| D11 | Média | Todas | Sem estados de carregamento: só opacidade durante `pending`. | Skeletons dos blocos e indicador de ação em curso. |
| D12 | Baixa | Home | Contextos ("Padrão", "Consciente") parecem abas de categoria; o usuário não sabe que mudam a lógica da vitrine. | Rótulo "Ver como:" e uma linha explicando cada perfil. |
| D13 | Baixa | Demo | Indicador do `next dev` (botão "N") aparece em toda captura. | `devIndicators: false` no `next.config.ts` para gravações. |

## 4. Novas visualizações e vínculos

Prioridade pela força com que tornam a tese visível na interface.

| ID | Visualização | O que mostra | Por que importa | Contrato |
|---|---|---|---|---|
| V1 | **Comparador de origens** no detalhe | Todas as ofertas do mesmo produto: cidade, distância, preço, CO₂; a escolhida destacada com o motivo ("mais próxima"; "empate até 1% → mais barata"). | É o argumento central — "mesmo produto, origem mais perto, emite menos" — e hoje não aparece em tela alguma. | Bloco novo `offer_comparison` (schema, `sdui.ts`, `REGISTRY`, testes). |
| V2 | **Explicador do selo** | Popover no selo com a cadeia: linha reta → × 1,345 → últimos 15 km de van + caminhão; massa cobrável; fontes. | Transparência ambiental; responde "de onde vem esse número?". | Campo opcional em `SustainabilityProps` ou rota `/metodologia`. |
| V3 | **Mapa de origem** | Mapa do Brasil em SVG (centroides projetados, sem biblioteca de mapas) com comprador e vendedores. | A distância vira imagem; dá peso visual ao "perto". | Bloco `origin_map`. |
| V4 | **Ordenação da vitrine** | "Mais próximo / menor CO₂ / menor preço" como ação do servidor. | Mostra a personalização como escolha do usuário, não caixa-preta. | Ação `navigate` com parâmetro; sem bloco novo. |
| V5 | **Contexto explicado** | Faixa no hero: "Por que isto? Compradores de SP levam 1,3× mais Alimentos" + "ver vitrine geral". | Torna a personalização regional legível e reversível. | Props no `hero_banner`. |
| V6 | **Seu impacto** | Contador do CO₂ evitado pelas trocas feitas no carrinho na sessão. | Fecha o ciclo da recomendação com um resultado. | Cliente (estado do carrinho) + `impact_banner`. |
| V7 | **Página de metodologia** | Como selo, distância e CO₂ são calculados; limites; fontes (GLEC, Gonçalves et al.). | Credibilidade; ponto de apoio na banca. | Tela server-driven `/metodologia`. |
| V8 | **Painel da pesquisa** | Concentração regional por UF, CO₂ evitado por UF, Haversine × OSRM — os números do Cap. 5 dentro do app. | Liga o produto aos resultados; ótimo para a defesa. | Tela server-driven a partir de `docs/resultados/`. |
| V9 | **Modo apresentação SDUI** | Botões que aplicam ao vivo as mutações do contrato (reordenar, injetar selo, bloco desconhecido). | Repete na banca, ao vivo, o teste 5.2.1. | Cliente, apoiado no modo de inspeção. |

## 5. Sequência de desenvolvimento

| Sprint | Tema | Itens | Pronto quando |
|---|---|---|---|
| 13 | Correções de UX e identidade | D1, D3, D4, D6, D7, D9, D13; redesenho do card (D2) | Capturas desktop/mobile sem quebra de cabeçalho, sem rótulo de debug e com card identificável; E2E verde. |
| 14 | Fluxo e qualidade | Checkout em página (D5), estados de carregamento (D11), acessibilidade (D10), hero compacto (D8, V5), "Ver como" (D12); regressão visual com Playwright; **teste de usabilidade** (SUS + preferência declarada, n ≈ 10) | Jornada completa navegável por teclado; SUS registrado no Cap. 5. |
| 15 | Novas visualizações SDUI | V1 comparador de origens, V2 explicador do selo, V4 ordenação, V3 mapa de origem | Blocos novos no contrato com teste de espelho; mutação E2E cobre um bloco novo. |
| 16 | Transparência e defesa | V7 metodologia, V8 painel da pesquisa, V9 modo apresentação, V6 seu impacto | Roteiro de demonstração da banca percorrível em < 5 min. |

Regra para todas: cada bloco novo segue o envelope `{ type, version, props, actions }`
e atualiza juntos `src/schemas/sdui.py`, `web/lib/sdui.ts`, o `REGISTRY` e
`tests/test_schemas.py` (ver `AGENTS.md`).
