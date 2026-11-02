# Acessibilidade automatizada (axe-core)

> Gerado por `E2E_BASE_URL=http://localhost:3000 npx playwright test acessibilidade` (de `web/`)
> no commit `ff3c0a3`, com a pilha local no ar (ETL de amostra, CEP 05311). axe-core 4.14.0 via
> `@axe-core/playwright`, regras WCAG 2.0/2.1 níveis A e AA. Saída bruta em
> `web/test-results/acessibilidade.json`. O spec falha só com violação **crítica**.

## Violações por tela e gravidade

| Tela | Crítica | Séria | Moderada | Leve |
|---|---|---|---|---|
| Entrada (CEP) | 0 | 0 | 0 | 0 |
| Home (vitrine) | 0 | 1 regra (12 elementos) | 0 | 0 |
| Detalhe (dialog) | 0 | 0 | 0 | 0 |
| Checkout | 0 | 2 regras (1 elemento cada) | 0 | 0 |
| Metodologia | 0 | 0 | 0 | 0 |
| Pesquisa | 0 | 0 | 0 | 0 |

**Nenhuma violação crítica.** As três sérias:

| Tela | Regra (WCAG) | Onde | Achado | Correção sugerida |
|---|---|---|---|---|
| Home | `color-contrast` (1.4.3) | contador ao lado do nome da categoria (`text-xs tabular-nums opacity-60`, `web/components/blocks.tsx`) | contraste 2,55:1 (#a6a19d sobre branco, 12 px); o mínimo é 4,5:1 | tirar o `opacity-60` e usar a cor `text-muted` cheia |
| Checkout | `color-contrast` (1.4.3) | preço unitário no resumo do pedido (`ml-1.5 text-muted/70`, `web/components/blocks.tsx`) | contraste 3,08:1 (#97928d sobre branco, 14 px) | trocar `text-muted/70` por `text-muted` |
| Checkout | `label-content-name-mismatch` (2.5.3) | botão do carrinho no cabeçalho (`web/components/controls.tsx`) | o nome acessível "Carrinho, 1 item" não contém o texto visível "Carrinho 1"; quem usa comando de voz e fala o que vê não acerta o botão | nome acessível que comece pelo texto visível, ex.: "Carrinho 1 item" |

O botão do carrinho só aparece como violação no checkout porque é a única tela auditada com
item no carrinho (sem item, o nome é só "Carrinho" e coincide com o texto).

## Leitura

- As correções são de uma linha cada e não foram aplicadas aqui: o frontend estava sendo
  redesenhado em paralelo. Depois do redesenho, rodar o spec de novo e atualizar esta tabela.
- O axe confere o que é automatizável (estimativa da Deque: cerca de metade dos critérios WCAG).
  Foco visível e navegação só por teclado estão em `web/e2e/teclado.spec.ts`; leitor de tela
  real e usuários com deficiência não foram testados (limitação, junto com o T3).

## Depois do redesenho (02/11)

Rodado de novo com o redesenho visual aplicado (cards 1–7 do Trello), mesmo comando e mesma pilha.
A primeira rodada achou 4 regras **sérias**: 2 das 3 acima (o contraste do contador
da categoria já tinha saído com o redesenho), o mesmo problema de nome acessível também no botão do
CEP, e `definition-list`/`dlitem`, porque os blocos de impacto punham o ícone entre o `<dl>` e o par
`<dt>`/`<dd>`. Correções aplicadas:

| Regra | Correção |
|---|---|
| `color-contrast` (preço unitário do checkout) | `text-muted/70` → `text-muted` |
| `label-content-name-mismatch` (carrinho) | sem `aria-label`; o nome sai do texto visível + `sr-only` ("Carrinho 1 item") |
| `label-content-name-mismatch` (CEP) | sem `aria-label`; texto visível + `sr-only` ", alterar CEP" |
| `definition-list` / `dlitem` (blocos de impacto) | ícone dentro do `<dt>`, posicionado em absoluto |

**Resultado final: 0 violações (crítica, séria, moderada ou leve) nas seis telas.**
