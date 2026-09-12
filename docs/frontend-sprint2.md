# Guia para Frontend — Sprint 2 (Home real + Selo de Logística Verde)

**Para quem:** desenvolvedor(a) de frontend **sem necessidade de saber Python**.  
**Objetivo:** entender o que **mudou** desde a Sprint 1, como **subir o backend com dados reais** e como **renderizar a Home** com produtos Olist e selo verde dinâmico.

**Referências:** `docs/prd.md`, `docs/tech_spec.md`, `README.md` (seção Demo)

> ### ⚠️ Leia antes: este documento é um registro da Sprint 2
>
> Ele foi escrito **antes de existir frontend**, para um(a) dev que ainda ia
> construir o cliente (por isso fala em Vite/React). O cliente **foi construído
> depois**, em `web/` — **Next.js 16 + App Router**, e as Sprints 3–6 mudaram
> parte do que está descrito aqui.
>
> **O que continua valendo:** a regra do selo (< 100 km), o papel do
> `customer_zip_prefix`, o envelope SDUI e a ideia de que o front não calcula
> nada — só renderiza `components[]`.
>
> **Onde está a verdade de hoje:**
>
> | Assunto | Fonte |
> |---------|-------|
> | Contrato SDUI completo (8 tipos de bloco) | `docs/tech_spec.md` §2 + Swagger `/docs` |
> | Endpoints, exemplos de `curl`, CEPs de demo | `README.md` |
> | O cliente de verdade | `web/` (`web/lib/sdui.ts` = tipos, `web/components/` = blocos) |
> | A jornada inteira, executável | `web/e2e/journey.spec.ts` (`npm run e2e`) |
>
> As seções abaixo trazem notas **“Hoje:”** onde a Sprint 2 ficou para trás.

---

## 1. O que mudou da Sprint 1 para a Sprint 2 (leia isto primeiro)

| Sprint 1 | Sprint 2 |
|----------|----------|
| Produtos **inventados** (`prod_001`, etc.) | Produtos **reais** da amostra Olist no PostgreSQL |
| Selo verde **sempre mockado** (`Entrega Local`) | Selo calculado: **só aparece se distância < 100 km** |
| Só query `context=...` | **`customer_zip_prefix` obrigatório** + `context` opcional |
| Backend rodava sem banco (só mock) | Backend **precisa de Postgres** com dados carregados (ETL) |
| Badge igual em todos os cards | Cada card pode ter **`badge` preenchido ou `null`** |

**O contrato SDUI não mudou:** cada bloco continua com `{ type, version, props, actions }` e a tela com `schema_version`. O que mudou é **o conteúdo** de `props` (dados reais + lógica do selo).

---

## 2. O que é a Sprint 2, em linguagem simples

Imagine que o comprador informa **onde mora** (prefixo do CEP, ex.: `05311`).  
O servidor:

1. Busca **produtos reais** no banco (amostra Olist).
2. Para **cada produto**, olha **onde o vendedor está** (CEP do vendedor).
3. Calcula a **distância em linha reta** entre os dois pontos no mapa (fórmula Haversine — não é rota de carro).
4. Se a distância for **menor que 100 km**, coloca um **selo verde** no card; senão, **não coloca selo** (`badge: null`).

O front **não calcula distância**. Ele só **mostra** o que veio no JSON.

---

## 3. Como subir o backend (para você testar a API)

Você **não precisa** rodar o ETL no dia a dia do front, mas **alguém do time** (ou você uma vez) precisa carregar os dados. Ordem:

### Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (para Postgres)
- [Python 3.12+](https://www.python.org/) (para API + script ETL)
- CSVs do Olist em `data/raw/` (não vêm no Git — baixar do Kaggle/dataset público)

### Passo a passo (Windows / PowerShell)

```powershell
cd projeto-tcc
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

```powershell
# 1. Postgres (porta 5433 no host — evita conflito com Postgres local na 5432)
docker compose up -d

# 2. Carregar ~10000 pedidos (seed fixa 42)
python -m scripts.etl_load_sample

# 3. API
uvicorn src.main:app --reload
```

- Swagger: **http://127.0.0.1:8000/docs**  
- API base: **http://127.0.0.1:8000**

> **Importante:** sem Docker + ETL, a Home **não** devolve produtos reais (pode dar erro de conexão ou lista vazia).

> **Hoje:** falta o passo 4 — subir o cliente. Com a API no ar:
>
> ```powershell
> cd web
> npm install
> npm run dev        # http://localhost:3000
> ```
>
> E `npm run e2e` (com a pilha inteira no ar) percorre a jornada da defesa de
> ponta a ponta. Detalhes em `README.md` → **Frontend (`web/`)**.

---

## 4. Endpoint da Home (o que o front chama)

### URL

```
GET /api/v1/home
```

### Parâmetros (query string)

| Parâmetro | Obrigatório? | Default | Descrição |
|-----------|--------------|---------|-----------|
| **`customer_zip_prefix`** | **Sim** | — | Prefixo do CEP do **comprador** (1–5 dígitos, formato Olist). Ex.: `05311` |
| **`context`** | Não | `default` | Personaliza o **banner** e tenta filtrar produtos por categoria |
| `q` | Não | — | **(Sprint 5)** Busca sobre o nome da categoria, sem acento e sem caixa: `moveis` encontra `moveis_decoracao` |
| `category` | Não | — | **(Sprint 5)** Filtro **exato** pelo slug do dataset. Slug inexistente na amostra → **422** |

### Valores úteis de `context`

| Valor | Efeito no banner | Produtos (heurística atual) |
|-------|------------------|------------------------------|
| `default` | Marketplace genérico | Qualquer categoria da amostra |
| `electronics_expert` | “Tech Deals” | Categoria `informatica_acessorios` |
| `beauty_lover` | “Semana da Beleza” | Categoria `beleza_saude` |
| `conscious_buyer` | **(Sprint 3)** Compra consciente | Qualquer categoria, **ordenada por proximidade** (mais perto primeiro) |

Se não houver produto da categoria na amostra, o backend **volta** a listar produtos sem filtro (fallback automático).

> **Hoje:** o fallback vale só para a categoria que o **contexto** escolheu (é
> uma heurística nossa). Filtro que o **usuário** pediu (`q`/`category`) não cai
> para a vitrine geral — resultado vazio é a resposta honesta.

### Exemplos prontos (copiar no navegador ou no `fetch`)

**Selo verde em pelo menos um card** (demo documentada no README):

```
http://127.0.0.1:8000/api/v1/home?customer_zip_prefix=05311&context=electronics_expert
```

**Sem selo em nenhum card** (cliente longe dos vendedores da amostra):

```
http://127.0.0.1:8000/api/v1/home?customer_zip_prefix=60165&context=default
```

**Erro — CEP desconhecido na amostra** (HTTP 422):

```
http://127.0.0.1:8000/api/v1/home?customer_zip_prefix=00000
```

Resposta de erro (formato FastAPI):

```json
{
  "detail": "customer_zip_prefix desconhecido: '00000'"
}
```

**Erro — parâmetro faltando** (HTTP 422):

```
http://127.0.0.1:8000/api/v1/home?context=default
```

---

## 5. Formato do JSON (igual à Sprint 1, com novidades no `badge`)

### Raiz: `ScreenResponse`

| Campo | Tipo | Significado |
|-------|------|-------------|
| `schema_version` | número | Versão do contrato da tela (hoje `1`) |
| `screen_id` | string | Sempre `"home"` por enquanto |
| `context` | string | Ecoa o `context` enviado |
| `components` | array | Lista de blocos na ordem de exibição |

### Ordem típica dos blocos

1. **Um** `hero_banner` (topo da página)  
2. **Até ~6** `product_card` (produtos reais)

> **Hoje:** a Home devolve `hero_banner` → **`category_grid`** → `product_card[]`.
> O `category_grid` entrou na Sprint 5 e cada categoria carrega a **própria**
> `actions` (o envelope do bloco só comporta uma ação para o conjunto todo).
> O contrato passou de 2 para **8 tipos de bloco** — os outros aparecem no
> detalhe e no checkout. A lista completa está em `docs/tech_spec.md` §2.

### Bloco `hero_banner`

```json
{
  "type": "hero_banner",
  "version": 1,
  "props": {
    "title": "Tech Deals",
    "subtitle": "Eletronicos com entrega rapida",
    "image_url": "https://placeholders.dev/800x400?text=Tech+Deals"
  },
  "actions": [
    {
      "type": "navigate",
      "payload": { "path": "/categories/electronics", "replace": false }
    }
  ]
}
```

### Bloco `product_card` — **com selo**

```json
{
  "type": "product_card",
  "version": 1,
  "props": {
    "product_id": "abc123...",
    "price": 199.9,
    "title": "Informatica Acessorios",
    "image_url": null,
    "badge": {
      "label": "Entrega local (~21 km · ~4,14 g CO₂)",
      "impact_level": "green",
      "icon": "leaf"
    }
  },
  "actions": [
    {
      "type": "api_call",
      "payload": {
        "method": "GET",
        "path": "/api/v1/products/abc123...?customer_zip_prefix=05311",
        "body_key": null
      }
    },
    {
      "type": "api_call",
      "payload": {
        "method": "POST",
        "path": "/api/v1/checkout/simulate",
        "body_key": "checkout"
      }
    }
  ]
}
```

> **Hoje (Sprint 6):** na Sprint 2 o card trazia um `open_modal` e o **cliente**
> remontava o detalhe com os props do próprio card — era a única tela que o
> cliente montava sozinho. Agora o detalhe é **outra tela do servidor**
> (`GET /products/{id}`), e o caminho já vem com o CEP porque distância e selo
> dependem dele: **o cliente não monta query string**. A segunda ação é o
> checkout — `body_key: "checkout"` diz qual chave do estado do cliente (o
> carrinho) vai no corpo do POST.

### Bloco `product_card` — **sem selo**

Quando o vendedor está a **100 km ou mais** (ou distância não calculável), o backend envia:

```json
"badge": null
```

**No React:** trate `badge === null` como “não renderizar selo” — **não** invente selo no cliente.

### Campos do selo (`SustainabilityProps`)

| Campo | Uso no front |
|-------|----------------|
| `label` | Texto do selo — **use este texto, não remonte**. Desde a Sprint 3 ele inclui o CO₂ quando o produto tem peso: `"Entrega local (~21 km · ~4,14 g CO₂)"` (a unidade alterna entre g e kg conforme a ordem de grandeza) |
| `impact_level` | `"green"` = estilo sustentável; `"neutral"` reservado para futuro |
| `icon` | Nome lógico (`"leaf"`) — mapeie para ícone do seu design system |

### O que pode ser `null` na Sprint 2

- **`image_url`** nos cards: muitas vezes **`null`** (Olist na amostra não traz URL de foto). Use **placeholder** no componente quando `null`.

---

## 6. Ações (`actions`) — mesmo contrato da Sprint 1

Cada bloco tem uma **lista** `actions`. Tipos:

| `type` | O que fazer no front |
|--------|----------------------|
| `navigate` | Ir para `payload.path` no router (`replace` = substituir histórico?) |
| `open_modal` | Abrir modal `payload.modal_id` |
| `api_call` | Chamar `payload.method payload.path` e **renderizar a `ScreenResponse` que voltar** |

> **Hoje:** `api_call` deixou de ser reservado — virou a ação principal. Ela não
> é "um efeito colateral": a resposta **é a próxima tela**. `body_key` nomeia a
> chave do estado do cliente que vai no corpo (hoje só `"checkout"`, o carrinho).
> O `open_modal` continua no contrato, mas a Home não o usa mais.

---

## 7. O que implementar no front nesta Sprint 2

> **Hoje: tudo abaixo está implementado em `web/`.** A lista virou um mapa de
> onde cada item foi parar:
>
> | Item | Onde |
> |------|------|
> | Enviar `customer_zip_prefix` | `web/app/page.tsx` (o CEP vive na URL) |
> | Renderizar dados reais | `web/components/blocks.tsx` |
> | Selo só se `badge !== null` | `web/components/blocks.tsx` |
> | Tratar 422 | `web/lib/api.ts` lê o `detail` (string **ou** array do Pydantic), `web/app/page.tsx` exibe |
> | Seletor de `context` e de CEP | `web/lib/sdui.ts` (`CONTEXTS`, `DEMO_ZIPS`) |
>
> O que a Sprint 2 listava como **fora de escopo** entrou depois: carrinho
> (Sprint 5, em `localStorage`) e checkout simulado (Sprint 3). O que continua
> fora: calcular distância ou CO₂ no browser — isso é do servidor, e é o ponto
> do SDUI.

### Obrigatório

1. **Enviar `customer_zip_prefix`** em toda chamada à Home.  
   - Pode vir de: input do usuário, perfil, query na URL (`?cep=05311`), ou valor fixo de demo.
2. **Renderizar `product_id` e `price` reais** — não hardcodar produtos da Sprint 1.
3. **Renderizar selo só se `props.badge !== null`.**
4. **Tratar HTTP 422** — CEP inválido: mensagem amigável (“CEP não disponível na base de demo”).
5. **Placeholder de imagem** quando `image_url` for `null`.

### Recomendado (UX)

6. **Seletor de `context`** (dropdown) para mostrar home adaptativa na demo.
7. **Seletor de CEP** com os exemplos do README (`05311` vs `60165`) para ver selo on/off.
8. **Estilo visual** para `impact_level: "green"` (cor, ícone folha, etc.).

### Ainda fora do escopo do front nesta sprint

- Calcular distância ou CO₂ no browser.
- Pagamento, carrinho real, checkout.
- Cache / segunda chamada “below the fold”.

---

## 8. Fluxo mental (diagrama)

```
Usuário informa CEP (customer_zip_prefix)
        │
        ▼
Front chama GET /api/v1/home?customer_zip_prefix=...&context=...
        │
        ▼
Backend busca produtos no Postgres
        │
        ▼
Para cada produto: distância(comprador, vendedor)
        │
        ├── distância < 100 km → badge preenchido
        └── distância ≥ 100 km → badge = null
        │
        ▼
Front renderiza components[] na ordem
```

---

## 9. CORS e proxy (mesmo aviso da Sprint 1)

> **Hoje esta seção está invertida.** O backend **configura** CORS: quando
> `APP_ENV=development`, `src/main.py` libera `localhost:5173`, `127.0.0.1:5173`
> e `localhost:3000`. Em produção o CORS permissivo fica desabilitado.
>
> E o cliente real **não usa proxy do Vite** — usa `rewrites()` do Next
> (`web/next.config.ts`) mandando `/api/v1/*` para `API_BASE_URL`. O motivo é o
> mesmo do proxy: as ações `api_call` trazem caminhos **absolutos** da API, e o
> rewrite faz o `fetch` do browser sair da **mesma origem**, então o CORS nem
> entra no caminho. O `CORSMiddleware` fica como rede de segurança para quem
> chamar a API direto (curl, Swagger, outro cliente).
>
> ```ts
> // web/next.config.ts
> async rewrites() {
>   return [{ source: "/api/v1/:path*", destination: `${API_BASE}/api/v1/:path*` }];
> }
> ```
>
> O registro original da Sprint 2 fica abaixo.

O backend **não** configura CORS. Se o React rodar em `http://localhost:5173`:

- **Opção A (recomendada):** proxy no Vite:

```javascript
// vite.config.js — exemplo
export default {
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
};
```

- **Opção B:** pedir ao backend `CORSMiddleware` só em dev.

Chamada com proxy:

```javascript
fetch('/api/v1/home?customer_zip_prefix=05311&context=default')
```

---

## 10. Exemplo mínimo em JavaScript (fetch)

```javascript
async function loadHome(customerZipPrefix, context = 'default') {
  const params = new URLSearchParams({
    customer_zip_prefix: customerZipPrefix,
    context,
  });

  const res = await fetch(`/api/v1/home?${params}`);

  if (res.status === 422) {
    const err = await res.json();
    throw new Error(err.detail ?? 'CEP inválido');
  }

  if (!res.ok) throw new Error(`HTTP ${res.status}`);

  return res.json(); // ScreenResponse
}

// Uso
const screen = await loadHome('05311', 'electronics_expert');

for (const block of screen.components) {
  if (block.type === 'hero_banner') {
    // renderHero(block.props)
  }
  if (block.type === 'product_card') {
    const { product_id, price, title, badge, image_url } = block.props;
    // renderCard({ product_id, price, title, image_url, badge })
    // if (badge) show badge.label + badge.icon
  }
}
```

---

## 11. Mapa de componentes React (sugestão)

> **Hoje isso deixou de ser sugestão:** `web/components/sdui.tsx` tem um
> `REGISTRY` que mapeia `component.type` → componente React, e
> `web/components/blocks.tsx` implementa **um componente por bloco** — os 8, não
> só estes 2.

| `block.type` | Componente | Props principais |
|--------------|------------|------------------|
| `hero_banner` | `<HeroBanner />` | `title`, `subtitle`, `image_url` |
| `product_card` | `<ProductCard />` | `product_id`, `price`, `title`, `image_url`, `badge` |

Componente auxiliar:

```jsx
// Pseudocódigo
function SustainabilityBadge({ badge }) {
  if (!badge) return null;
  return (
    <span className={badge.impact_level === 'green' ? 'badge-green' : ''}>
      {badge.icon === 'leaf' && <LeafIcon />}
      {badge.label}
    </span>
  );
}
```

---

## 12. Critérios de aceite (lado frontend)

> **Hoje todos passam, e não no olho:** `web/tests/` (Vitest) cobre os blocos e
> `web/e2e/journey.spec.ts` percorre a jornada contra a pilha real.

- [x] Home carrega com **`customer_zip_prefix` real** (não só `context`).
- [x] Com `05311` + `electronics_expert`, **pelo menos um** card mostra selo verde.
- [x] Com `60165`, **nenhum** card mostra selo (todos `badge: null`).
- [x] CEP inválido (`00000`) mostra erro tratado (422).
- [x] Cards usam `product_id`/`price` da API, não lista fixa da Sprint 1.
- [x] `image_url: null` não quebra layout (placeholder).
- [x] ~~Ação `open_modal` no card~~ → hoje o card dispara `api_call` e abre a
      **tela de detalhe do servidor**.

---

## 13. Perguntas frequentes

**Preciso rodar Docker todo dia?**  
Só se o Postgres for desligado. Com `docker compose up -d` e ETL já rodado, os dados persistem no volume Docker.

**Por que o título do produto parece a categoria?**  
O backend usa a categoria Olist como título quando não há nome comercial no dataset (`informatica_acessorios` → “Informatica Acessorios”).

**O selo garante entrega rápida ou ecológica na vida real?**  
Não. É uma **estimativa educativa** por distância em linha reta entre CEPs, para o TCC. O front só exibe o que o servidor manda.

**Mudou algo no envelope SDUI?**  
Não. Continua `type`, `version`, `props`, `actions` e `schema_version`.

**E o Figma do TCC1?**  
O protótipo Figma pode ser atualizado para incluir selo condicional; a **fonte de verdade da API** é este JSON.

---

## 14. Checklist de breaking changes (Sprint 1 → 2)

Se você já tinha código da Sprint 1:

- [ ] Adicionar **`customer_zip_prefix`** em todas as requisições `/home`.
- [ ] Remover dependência de IDs fixos (`prod_001`, etc.).
- [ ] Tratar **`badge: null`** (antes podia sempre existir mock).
- [ ] Tratar **`image_url: null`**.
- [ ] Atualizar testes/mocks do front para incluir CEP.

---

## 15. Onde tirar dúvidas

| Assunto | Onde olhar |
|---------|------------|
| Demo curl / CEPs de exemplo | `README.md` → seção **Demo** |
| Contrato JSON completo | `docs/tech_spec.md` §2 + Swagger `/docs` |
| Regra do selo (< 100 km) | `docs/prd.md`, `README.md` → Logística Verde |
| O cliente de hoje | `web/` + `README.md` → **Frontend (`web/`)** |
| A jornada inteira, executável | `web/e2e/journey.spec.ts` (`npm run e2e`) |
| Sprints 3–5 (histórico) | `docs/sprint3-handoff.md`, `docs/sprint4-handoff.md`, `docs/sprint5-handoff.md` |
| Sprint 6 | `README.md` → **Sprint 6** (não tem handoff próprio) |
| Sprint 1 (histórico) | `docs/frontend-sprint1.md` |

---

*Documento para integrantes de frontend — Sprint 2 (dados reais Olist + selo de logística verde). **Mantido como registro histórico:** o cliente que ele antecipava existe em `web/` desde logo depois da Sprint 3 (commit `548c96d`), e as notas “Hoje:” marcam onde a Sprint 2 ficou para trás. Para consumir a API hoje, comece pelo `README.md` e por `docs/tech_spec.md` §2.*
