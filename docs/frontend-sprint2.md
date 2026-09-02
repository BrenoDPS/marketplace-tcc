# Guia para Frontend — Sprint 2 (Home real + Selo de Logística Verde)

**Para quem:** desenvolvedor(a) de frontend **sem necessidade de saber Python**.  
**Objetivo:** entender o que **mudou** desde a Sprint 1, como **subir o backend com dados reais** e como **renderizar a Home** com produtos Olist e selo verde dinâmico.

**Referências:** `docs/prd.md`, `docs/tech_spec.md`, `README.md` (seção Demo)

> **Sprint 3 (backend):** checkout simulado, CO₂ no selo e `context=conscious_buyer` — ver `docs/sprint3-handoff.md`. Guia front Sprint 3 será publicado após a implementação do backend.

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

### Valores úteis de `context`

| Valor | Efeito no banner | Produtos (heurística atual) |
|-------|------------------|------------------------------|
| `default` | Marketplace genérico | Qualquer categoria da amostra |
| `electronics_expert` | “Tech Deals” | Categoria `informatica_acessorios` |
| `beauty_lover` | “Semana da Beleza” | Categoria `beleza_saude` |

Se não houver produto da categoria na amostra, o backend **volta** a listar produtos sem filtro (fallback automático).

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
      "label": "Entrega local (~27 km)",
      "impact_level": "green",
      "icon": "leaf"
    }
  },
  "actions": [
    {
      "type": "open_modal",
      "payload": { "modal_id": "product_detail", "title": null }
    }
  ]
}
```

### Bloco `product_card` — **sem selo**

Quando o vendedor está a **100 km ou mais** (ou distância não calculável), o backend envia:

```json
"badge": null
```

**No React:** trate `badge === null` como “não renderizar selo” — **não** invente selo no cliente.

### Campos do selo (`SustainabilityProps`)

| Campo | Uso no front |
|-------|----------------|
| `label` | Texto do selo (ex.: `"Entrega local (~27 km)"`) — **use este texto** |
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
| `open_modal` | Abrir modal `payload.modal_id` (MVP: modal de detalhe do produto) |
| `api_call` | Reservado para futuro (checkout); pode `console.log` no MVP |

---

## 7. O que implementar no front nesta Sprint 2

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

- [ ] Home carrega com **`customer_zip_prefix` real** (não só `context`).
- [ ] Com `05311` + `electronics_expert`, **pelo menos um** card mostra selo verde.
- [ ] Com `60165`, **nenhum** card mostra selo (todos `badge: null`).
- [ ] CEP inválido (`00000`) mostra erro tratado (422).
- [ ] Cards usam `product_id`/`price` da API, não lista fixa da Sprint 1.
- [ ] `image_url: null` não quebra layout (placeholder).
- [ ] Ação `open_modal` no card abre algo (mesmo que modal simples).

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
| Sprint 1 (histórico) | `docs/frontend-sprint1.md` |

---

*Documento para integrantes de frontend — Sprint 2 (dados reais Olist + selo de logística verde). Backend em Python; este guia cobre só o que o cliente precisa consumir e renderizar.*
