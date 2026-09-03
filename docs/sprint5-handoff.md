# Handoff — Sprint 5: Busca, categorias, carrinho multi-item, testes e CI

> **Para agentes sem contexto:** leia primeiro `@docs/PROJECT_BOOTSTRAP.md`, depois este arquivo.
> Sprints 1–4 **já estão implementadas** — não reimplementar do zero.

> **Sprint concluída.** As três trilhas estão no código e verificadas. Documento
> escrito em duas etapas: a trilha A primeiro, B e C depois.

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
| **A — Busca e categorias** | `q` e `category` em `GET /home`; bloco `category_grid`; UI de busca e chips | Entregue |
| **B — Carrinho multi-item** | `checkout/simulate` com vários itens, frete e CO₂ agregados por vendedor | Entregue |
| **C — Testes de frontend + CI** | Vitest sobre o executor de `actions` e o `ScreenRenderer`; workflow de CI | Entregue |

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

## Trilha B — Carrinho multi-item

### O achado que mudou a premissa

Esta sprint foi planejada com a hipótese de que **consolidar itens do mesmo vendedor
reduziria o CO₂** — o argumento da modalidade verde. Ao implementar, a hipótese não se
sustentou:

```
E = d × w × FE   →   Σᵢ (d × wᵢ × FE)  =  d × (Σᵢ wᵢ) × FE
```

O modelo é **linear na massa**, então agrupar N itens do mesmo vendedor numa remessa dá
exatamente a mesma emissão de N remessas separadas. Consolidação economiza **frete**, não
emissão.

Fazer a economia de CO₂ aparecer exigiria um termo fixo por remessa (custo de coleta e
última milha, que não escala com a carga). Isso foi **deliberadamente não implementado**:
um valor honesto de última milha (~0,1 kg CO₂ por encomenda) é ~250× maior que a emissão
de transporte de um item típico desta amostra (4 km, 500 g → 0,0002 kg), e dominaria
completamente os números, apagando o eixo de distância construído nas Sprints 2–4. Um
valor pequeno o bastante para não dominar teria de ser inventado.

**O que o carrinho entrega no lugar** é mais defensável e não precisa de coeficiente novo:
o `co2_share` por remessa mostra **qual vendedor domina a pegada**. Num carrinho de 3
itens verificado no navegador, a remessa a 79 km respondeu por **75%** do CO₂ total
enquanto as duas locais (4 km e 7 km) somaram 25%. A ação que reduz a pegada é trocar
*aquele* vendedor, não agrupar itens — e agora dá para ver isso.

Essa ressalva está em três lugares: `CONSOLIDATION_NOTE` no composer, o campo `note` que
viaja no JSON, e o texto exibido na tela.

### Decisões da trilha B

| Tópico | Decisão |
|--------|---------|
| Forma do corpo | **Só `items`**, mesmo com um item. Aceitar duas formas (produto solto ou lista) dobraria o contrato para sempre; o único cliente é o front deste repo |
| Frete por remessa | O **maior** `freight_value` do grupo. Somar suporia que cada item viaja sozinho, anulando a consolidação; a amostra não tem noção de remessa |
| Agrupamento | Por `seller_id`, na ordem em que os itens entraram no carrinho |
| Produto repetido | Colapsa numa linha no router — duas linhas iguais dariam dois fretes |
| Banner com N remessas | `distance_km` vira `null`: não existe UMA distância. Quem detalha é o `shipment_breakdown` |
| Prazo do carrinho | Sai da remessa **mais distante** — o pedido só está completo quando a última chega |
| Consulta | Uma só (`product_id IN (...)`) para o carrinho inteiro |
| Estado do carrinho | **Do cliente.** Por isso `delivery_options` deixou de ecoar `product_id`/`quantity` (a razão da Sprint 4 era o cliente não guardar estado — um carrinho é estado por natureza) |
| Limite | 20 itens por carrinho |

### Trilha C — Testes e CI

`web/tests/sdui.test.tsx` (14 casos) cobre só o que tem lógica: dispatch de cada tipo de
`action`, agrupamento de cards em grade, bloco desconhecido renderizando nada sem derrubar
a tela, corpo do checkout, colapso de item repetido e formatação de CO₂. Componentes de
apresentação não ganharam teste de propósito.

Duas coisas descobertas montando isso:

- **`@types/node` estava em `^20` com Node 22 rodando** — os tipos já divergiam do runtime.
  Alinhar resolveu de quebra o conflito de peer dependency do Vitest 5, sem `--force`.
- **`vite-tsconfig-paths` é desnecessário**: o Vite avisa no console que resolve `tsconfig`
  paths nativamente (`resolve.tsconfigPaths: true`). Removido — 3 pacotes a menos.

O job de backend do CI **não** sobe Postgres: a suíte usa `dependency_overrides` e
monkeypatch. Se um teste passar a exigir banco, ele quebra lá — e essa quebra é a
informação útil.

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
- [x] `pytest` verde — **98 testes**; `npm test` verde — **14 testes**
- [x] `tsc --noEmit` e `npm run build` limpos

**Trilha B:**

- [x] `items` (1 a 20) no lugar de um `product_id` solto; carrinho vazio → **422**
- [x] Itens do mesmo vendedor viram **uma** remessa, com um frete só (o maior do grupo)
- [x] Vendedores diferentes viram remessas separadas e os fretes somam
- [x] `co2_share` por remessa, somando 1,0
- [x] Selo verde por remessa, não do carrinho inteiro
- [x] Produto repetido colapsa numa linha (senão pagaria dois fretes)
- [x] `delivery_options` precifica o carrinho inteiro e o prazo segue a remessa mais distante
- [x] Uma consulta ao banco para todos os produtos do carrinho

**Trilha C:**

- [x] Vitest em `web/` — 14 casos sobre executor de `actions`, `ScreenRenderer` e carrinho
- [x] Bloco desconhecido não derruba a tela (teste de degradação)
- [x] `.github/workflows/ci.yml` com jobs de backend e frontend

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
- Emissão fixa por remessa (última milha) — ver "O achado que mudou a premissa"
- Persistência do carrinho (recarregar a página esvazia; não há `localStorage` nem sessão)
- Paginação / "carregar mais": a Home segue em 6 cards
- Ordenação escolhida pelo usuário (preço, relevância)
- Filtro por faixa de preço ou por estado do vendedor
- Página dedicada de categoria (o filtro reusa `/` com query string)
- Teste E2E (Playwright) — a verificação de fluxo completo segue manual
- Redis, Locust, PostGIS, `orchestrator`

---

## Sugestões para a Sprint 6

1. **Ordenar o carrinho por pegada.** O `co2_share` já existe; falta a UI destacar a
   remessa dominante e sugerir alternativas do mesmo produto em vendedores mais próximos.
   É o passo que transforma o diagnóstico em ação, e o `conscious_buyer` já sabe ranquear
   por proximidade.
2. **Persistir o carrinho** em `localStorage` — hoje um F5 zera tudo, o que atrapalha
   demonstrar o fluxo numa apresentação.
3. **E2E com Playwright** cobrindo a jornada inteira (CEP → busca → carrinho → checkout →
   troca de modalidade), já que é exatamente o roteiro da defesa.
