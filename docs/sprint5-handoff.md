# Handoff — Sprint 5: Busca e categorias (em andamento)

> **Para agentes sem contexto:** leia primeiro `@docs/PROJECT_BOOTSTRAP.md`, depois este arquivo.
> Sprints 1–4 **já estão implementadas** — não reimplementar do zero.

> **Sprint parcialmente entregue.** A trilha A (busca e categorias) está no código e
> verificada. As trilhas B e C abaixo ainda **não** foram implementadas — os critérios
> de aceite delas estão desmarcados de propósito.

## Fonte de verdade (ordem de leitura)

1. **Este arquivo** (`docs/sprint5-handoff.md`) — escopo desta entrega
2. `@docs/PROJECT_BOOTSTRAP.md` — visão geral do repo
3. `@README.md` — como subir docker + ETL + API + frontend
4. `@docs/sprint4-handoff.md` — sprint anterior (`delivery_options`)
5. `@docs/tech_spec.md` — contrato SDUI
6. `@.cursorrules` — regras de código

**Não** usar transcripts antigos como especificação.

---

## Objetivo

| Trilha | Entrega | Status |
|--------|---------|--------|
| **A — Busca e categorias** | `q` e `category` em `GET /home`; bloco `category_grid`; UI de busca e chips | **Entregue** |
| **B — Carrinho multi-item** | `checkout/simulate` com vários itens, frete e CO₂ agregados por vendedor | Pendente |
| **C — Testes de frontend + CI** | Vitest sobre o executor de `actions` e o `ScreenRenderer`; workflow de CI | Pendente |

---

## Contexto que motivou a sprint

A amostra de 10k (Sprint 4) trouxe **6.575 produtos em 70 categorias**. A Home mostra 6
cards por vez e não tinha nenhuma forma de navegação: o usuário via seis produtos e
acabou. Era a dor mais imediata criada pelo dataset maior.

---

## Decisões fechadas (não reinterpretar)

| Tópico | Decisão |
|--------|---------|
| Escopo da busca | **Só o nome da categoria.** O Olist não tem nome de produto — `product_category_name` é o único campo textual e o `title` do card já é ele formatado |
| Acentos | Dobrados **no termo do usuário** (`unicodedata` NFKD). As categorias do Olist já são ASCII (`moveis_decoracao`), então a coluna não precisa de `unaccent` |
| Casamento | `ILIKE` com `%termo%` sobre `replace(product_category_name, '_', ' ')` — "cama mesa" encontra `cama_mesa_banho` |
| Escape de LIKE | `%`, `_` e `\` escapados antes de virar padrão. Entrada de usuário: sem isso, buscar `%` varre a tabela |
| Busca em branco | Termo que **some** ao normalizar (só espaços) = sem busca. `###` sobrevive (é ASCII) e é busca de verdade com zero resultados |
| Fallback | Filtro explícito (`q`/`category`) que não casa devolve **vazio**. Só a categoria inferida do `context` cai para a vitrine geral |
| `category` inválida | **422**, consistente com o tratamento de `customer_zip_prefix` |
| Precedência | `category` explícita vence a categoria do `context` |
| Composição | Filtro **não** desliga o ranking por proximidade do `conscious_buyer` |
| Ação da categoria | Vive **no item**, não no envelope do bloco — cada categoria navega para um caminho diferente |
| Caminho de volta | O servidor devolve a ação "Ver tudo" no hero filtrado; o cliente não monta URL de limpeza |

---

## Trilha A — Backend

### A1. Repository

**Arquivo:** `src/features/home_contextual/repository.py`

- `normalize_search(term)` — dobra acentos, minusculiza, `_` → espaço, colapsa espaços
- `fetch_products_for_home(..., search=None)` — ganha o filtro `ILIKE`
- `list_categories(session, limit=None)` — `CategoryRow(slug, product_count)`, da maior para a menor
- **Fallback removido daqui** e movido para o composer

O docstring do módulo abre com a limitação do dataset. Ler antes de prometer busca de
produto em qualquer lugar do TCC.

Há um `ponytail:` marcando o teto conhecido: `ILIKE` com `%` à esquerda ignora o índice
de categoria. Com 6,5k produtos é irrelevante; no Olist completo, trocar por `pg_trgm`
ou `tsvector`.

### A2. Contrato SDUI

**Arquivo:** `src/schemas/sdui.py`

```python
class CategoryItemProps(BaseModel):
    slug: str
    label: str
    product_count: int
    selected: bool = False
    actions: list[UIAction] = []   # a acao vive no item

class CategoryGridProps(BaseModel):
    title: str | None = None
    categories: list[CategoryItemProps]
```

`CategoryGridBlock` (`type: "category_grid"`, `version: 1`) entra na união `UIComponent`.

`HeroBannerProps` ganha **`cta_label: str | None`** — sem ele o texto do botão fica
cravado no cliente e um hero de "limpar filtro" apareceria escrito "Explorar".

### A3. Composer e router

`compose_home(..., search=None, category=None)`. Toda Home passa a trazer
`hero_banner` → `category_grid` → cards.

O router normaliza `q` **uma vez, na borda**: daí para dentro o termo ou é útil ou é
`None`. Assim o hero nunca anuncia "Busca: " sobre uma vitrine que não está filtrada.

---

## Trilha A — Frontend

| Arquivo | Mudança |
|---------|---------|
| `web/lib/sdui.ts` | `CategoryItem`, `CategoryGridBlock`; `cta_label` no hero |
| `web/lib/api.ts` | `fetchHome(zip, context, search?, category?)` |
| `web/components/blocks.tsx` | `CategoryGrid`; hero usa `cta_label ?? "Explorar"` |
| `web/components/sdui.tsx` | Uma linha no `REGISTRY` |
| `web/components/controls.tsx` | Busca com `next/form`; `hrefFor` preserva o filtro |
| `web/app/page.tsx` | Lê `q` e `category` dos `searchParams` |

Detalhes que não são óbvios no diff:

- **`next/form` com `action="/"`** — GET nativo, campos viram query string, navegação
  client-side, funciona sem JS. Os `<input type="hidden">` preservam CEP e contexto;
  **omitir `category`** é o que limpa o filtro de categoria a cada nova busca.
- **`key={search}` no input** — sem isso o `defaultValue` não reage à navegação
  client-side e a caixa fica com o termo antigo depois de "Ver tudo" (bug encontrado no
  navegador, ver abaixo).
- **Chips com rolagem horizontal** (`-mx-6 px-6 overflow-x-auto`) — 12 chips em 375px
  viravam quatro linhas de altura.
- **`hrefFor` preserva o filtro** ao trocar CEP ou contexto: contexto e filtro compõem,
  e perder a busca a cada clique escondia exatamente essa combinação.

---

## Bug encontrado na verificação

Depois de clicar "Ver tudo", a vitrine limpava mas o campo de busca continuava escrito
`bebes` — `defaultValue` só vale na montagem, e a navegação client-side não remonta o
componente. A caixa contradizia a tela. Corrigido com `key` amarrado ao termo.

---

## Critérios de aceite

**Trilha A:**

- [x] `q` encontra categoria ignorando acento e caixa (`INFORMÁTICA` → `informatica_acessorios`)
- [x] `%` e `_` escapados: `q=%` retorna zero cards, não a vitrine inteira
- [x] `category` filtra exato; desconhecida retorna **422**
- [x] `category` explícita vence a categoria do `context`
- [x] Filtro explícito sem resultado devolve vitrine vazia com hero dizendo isso
- [x] `category_grid` em toda Home, com contagem e a categoria ativa marcada
- [x] Cada categoria carrega a própria `navigate`, com CEP e contexto no path
- [x] Hero filtrado oferece "Ver tudo" via `cta_label` + `navigate`
- [x] Filtro compõe com o ranking de `conscious_buyer`
- [x] `pytest` verde — **84 testes** (69 anteriores + 15 novos)
- [x] `tsc --noEmit` limpo

**Trilhas B e C:** não iniciadas.

Verificação end-to-end no navegador (CEP 05311, `conscious_buyer`): chip "Beleza Saude"
filtra e fica marcado; busca `RELÓGIOS` vira `Busca: relogios`; "Ver tudo" limpa filtro,
URL e campo. `category=bebes` sem contexto dá distâncias `[79, 61, —, —, 61, —]` km;
com `conscious_buyer` dá `[5, 12, 16, 20, 21, 23]`.

---

## Testes

`tests/test_home_contextual.py` foi de 9 para **24 casos**. Os fakes acompanharam as
assinaturas novas (`search=`, `list_categories`) e passaram a **espelhar o filtro real**
— um fake que ignora o filtro não testa filtro nenhum.

A fixture ganhou um terceiro produto (`prod_beauty`, outra categoria, seller **sem
centroide**), o que exercita de quebra o "sem distância vai para o fim" da ordenação do
`conscious_buyer` — comportamento documentado e até então sem teste.

Casos que valem conhecer antes de mexer:

- `test_search_ignores_accents_and_case`
- `test_search_without_results_says_so_instead_of_falling_back`
- `test_blank_search_is_treated_as_no_search` vs. `test_punctuation_search_is_a_real_search_with_no_results`
- `test_search_composes_with_conscious_buyer_ranking`
- `test_filtered_hero_offers_a_way_back`

---

## Fora de escopo (não implementado)

- Busca por nome de produto — **não é possível com o Olist**, ver decisões acima
- Paginação / "carregar mais": a Home segue em 6 cards
- Ordenação escolhida pelo usuário (preço, relevância)
- Filtro por faixa de preço ou por estado do vendedor
- Página dedicada de categoria (o filtro reusa `/` com query string)
- Redis, Locust, PostGIS, `orchestrator`

---

## Próximos passos (trilhas B e C)

1. **Carrinho multi-item.** `checkout/simulate` com uma lista de itens, agregando frete e
   CO₂ **por vendedor**. É o que falta para o `delivery_options` mostrar sua tese:
   consolidar itens do mesmo seller é exatamente o argumento da modalidade verde, e hoje
   isso não pode ser demonstrado porque só existe um item por simulação.
2. **Testes de frontend + CI.** Vitest sobre `sdui-context.tsx` (dispatch de `actions`) e
   `sdui.tsx` (agrupamento de cards, bloco desconhecido); workflow rodando `pytest` +
   `npm run build`.
