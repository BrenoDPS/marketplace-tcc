# Guia para Frontend — Sprint 1 (API SDUI)

**Para quem:** desenvolvedor(a) de frontend **sem necessidade de saber Python**.  
**Objetivo:** subir o backend localmente, consumir o JSON **Server-Driven UI (SDUI)** e entregar a **primeira tela** (Home) guiada pelo servidor.

**Referência de produto:** `docs/prd.md`  
**Contrato técnico (JSON, performance, logística futura):** `docs/tech_spec.md`

---

## 1. O que é este backend (em uma frase)

É uma API **FastAPI** que devolve uma **lista de “blocos” de interface** em JSON. O app (React ou outro) **não inventa** a estrutura principal da tela: ela vem do campo `components`. Isso é o padrão **SDUI**.

---

## 2. O que a Sprint 1 significa (conversa original + estado do repo)

Na conversa que gerou o plano da Sprint 1 ([transcript](9177935b-3e76-4521-880a-5c01874da50a)), a ideia era:

1. **Subir o projeto** com Python, dependências e servidor (`uvicorn`).
2. **Definir o contrato JSON** dos componentes (tipos discriminados por `type`).
3. **Expor um endpoint stub** da **Home contextual**: `GET /api/v1/home` com query `context=...` e dados **mockados**.
4. **Documentar** o contrato no **Swagger** (`/docs`) e garantir testes no backend (`pytest` — opcional para você).

**No repositório atual**, o contrato segue o **`docs/tech_spec.md` §2** (Fase 1): cada bloco usa o envelope **`{ type, version, props, actions }`** e a resposta da tela inclui **`schema_version`**. Os valores de “logística verde” no composer são **mock** até a Fase 2 (ver `README.md` → Roadmap).

---

## 3. Como rodar o backend (você só precisa copiar os comandos)

**Pré-requisito:** [Python](https://www.python.org/) **3.12+** instalado (o `tech_spec` menciona 3.12+).

No diretório raiz do projeto (`projeto-tcc`):

### Windows (PowerShell)

```powershell
cd projeto-tcc
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

(se existir) copie variáveis de ambiente:

```powershell
copy .env.example .env
```

Suba o servidor:

```powershell
uvicorn src.main:app --reload
```

- API base: **http://127.0.0.1:8000**  
- Documentação interativa (útil para ver o schema): **http://127.0.0.1:8000/docs**  
- OpenAPI JSON: **http://127.0.0.1:8000/openapi.json**

**Nota:** O código inclui configuração de **PostgreSQL** e **Redis** para evolução futura. Para a **Home mock da Fase 1**, em muitos casos o endpoint `/home` funciona sem você usar o banco; se aparecer erro ligado a DB ao subir ou ao chamar rotas que usem DB, peça ao time de backend ou alinhe um `.env` com serviços locais.

---

## 4. Endpoint que você vai usar na Sprint 1

| Método | URL | Descrição |
|--------|-----|-----------|
| `GET` | `/api/v1/home` | Tela inicial SDUI |
| Query | `context` | String que altera o layout mock (ex.: `electronics_expert`, `beauty_lover`, `default`, `conscious_buyer` — confira valores reais no Swagger ou no código `composer.py`) |

**Exemplo:**

`GET http://127.0.0.1:8000/api/v1/home?context=electronics_expert`

---

## 5. Formato do JSON (o que você precisa renderizar)

### 5.1 Raiz: `ScreenResponse`

Campos principais:

- `schema_version` — versão do contrato da **tela inteira** (evoluir no futuro sem quebrar o app).
- `screen_id` — identificador da tela (ex.: `"home"`).
- `context` — ecoa o `context` pedido (ou default).
- `components` — **array de blocos**; cada item é um `UIComponent`.

### 5.2 Cada bloco: envelope comum

Todo item em `components` tem:

- `type` — **discriminador** (qual componente React/Vue/etc. montar).
- `version` — versão daquele **tipo de bloco**.
- `props` — **dados de apresentação** (títulos, preços, imagens, badge…).
- `actions` — **lista** de ações (comportamento mandado pelo servidor).

**Importante:** na Fase 1, as `actions` podem vir **mockadas**; ainda assim o frontend deve **interpretar** os tipos abaixo para já nascer preparado.

### 5.3 Tipos de `actions` (discriminador `action.type`)

Cada ação tem `type` e `payload`:

- `navigate` → `payload.path`, `payload.replace` (boolean).
- `api_call` → `payload.method`, `payload.path`, `payload.body_key` (opcional).
- `open_modal` → `payload.modal_id`, `payload.title` (opcional).

### 5.4 Tipos de blocos atuais (`component.type`)

No Fase 1 o backend está com pelo menos:

- `hero_banner` — `props`: `title`, `subtitle` (opcional), `image_url`.
- `product_card` — `props`: `product_id`, `price`, `title` (opcional), `image_url` (opcional), `badge` (opcional) com `label`, `impact_level`, `icon` (estrutura de sustentabilidade **mock** até Fase 2).

*(Novos tipos aparecerão no mesmo padrão: incluir no mapa `type → componente` no frontend.)*

### 5.5 Exemplo mínimo (ilustrativo)

```json
{
  "schema_version": 1,
  "screen_id": "home",
  "context": "electronics_expert",
  "components": [
    {
      "type": "hero_banner",
      "version": 1,
      "props": {
        "title": "Tech Deals",
        "subtitle": "Eletronicos com entrega rapida",
        "image_url": "https://..."
      },
      "actions": [
        {
          "type": "navigate",
          "payload": { "path": "/categories/electronics", "replace": false }
        }
      ]
    },
    {
      "type": "product_card",
      "version": 1,
      "props": {
        "product_id": "prod_001",
        "price": 199.9,
        "title": "Fone Bluetooth",
        "image_url": "https://...",
        "badge": {
          "label": "Entrega Local",
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
  ]
}
```

Use o Swagger (`/docs`) como **fonte atualizada** se algum campo mudar.

---

## 6. O que você implementa na Sprint 1 (checklist sugerido)

1. **Projeto frontend** (Vite + React, Next etc. — à escolha do time).
2. **Chamada HTTP** para `GET /api/v1/home?context=...`.
3. **Renderer SDUI:** função que percorre `components` e faz `switch (component.type)` (ou mapa de componentes).
4. **Ligar `props` aos apresentacionais** (texto, imagem, preço, badge).
5. **Executor de `actions`:**
   - `navigate` → router do SPA (ex.: `react-router`) usando `payload.path`.
   - `open_modal` → abrir modal placeholder (pode ser só `alert` ou modal simples no MVP).
   - `api_call` → por ora pode ser `console.log` ou `fetch` genérico; na Fase 2 alinha com rotas reais (`checkout`, etc.).
6. **Trocar `context`** na UI (dropdown ou query na URL) para mostrar que a home **muda** com o contexto (requisito original da Sprint 1 no transcript).
7. **CORS / proxy:** o backend **pode não ter CORS** habilitado para `localhost:5173`. Soluções comuns:
   - proxy no Vite apontando `/api` → `http://127.0.0.1:8000`, ou
   - pedir ao backend para adicionar `CORSMiddleware` em desenvolvimento.

---

## 7. Critérios de aceite (lado frontend, alinhados à Sprint 1)

- App inicia e **lista a Home** consumindo a API real (não JSON estático).
- Renderiza **pelo menos** `hero_banner` e `product_card` com dados vindos de `props`.
- Ao menos uma **ação** funciona de ponta a ponta (recomendado: `navigate`).
- Trocar `context` altera o JSON recebido (layouts mock diferentes).

---

## 8. Dúvidas / Fonte de verdade

- Contrato e roadmap: `docs/tech_spec.md`, `README.md`  
- Negócio e personas: `docs/prd.md`  
- Plano histórico da Sprint 1 na conversa: transcript [9177935b-3e76-4521-880a-5c01874da50a](9177935b-3e76-4521-880a-5c01874da50a)

---

*Documento gerado para integrantes de frontend; implementação backend em Python permanece responsabilidade do repositório `projeto-tcc`.*
