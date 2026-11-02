# Olist SDUI Marketplace 🛍️

Um marketplace que monta as telas no servidor e mostra o custo climático da entrega — feito com dados reais da Olist.

**Em 30 segundos:** o backend (FastAPI) envia a tela pronta como JSON, o front (Next.js) só renderiza. Cada produto mostra de onde vem, quantos km viaja e quanto CO₂ emite. Se o vendedor for vizinho (< 100 km), ganha o selo **Entrega Local**.

> 👋 **Primeira vez aqui?** Siga o [Comece aqui](#-comece-aqui-em-5-minutos) abaixo. O conteúdo técnico completo do README antigo foi preservado em [docs/GUIA-COMPLETO.md](docs/GUIA-COMPLETO.md).

## Por que olhar este projeto?

- **Server-Driven UI de verdade:** contrato em `src/schemas/sdui.py`, espelho no front em `web/lib/sdui.ts` e renderização em `web/components/sdui.tsx`.
- **Personalização contextual:** a Home muda por região do CEP, busca (`q`) e categoria.
- **Logística verde:** distância por CEP (Haversine), selo < 100 km e CO₂ por cadeia de transporte em `src/features/green_logistics/co2.py`.
- **TCC com evidência:** metodologia × teste × resultado em [docs/tese-rastreabilidade.md](docs/tese-rastreabilidade.md), latência em [docs/performance.md](docs/performance.md).

## 🚀 Comece aqui em 5 minutos

**Você precisa de:** Python 3.12+, Node 20+, Docker.

```bash
# 1. Subir banco + cache
docker compose up -d

# 2. Carregar a amostra (~10 mil itens, os CSVs da Olist vão em data/raw/)
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
python -m scripts.etl_load_sample

# 3. Subir a API
uvicorn src.main:app --reload
# Docs interativas: http://localhost:8000/docs

# 4. Subir o front (em outro terminal)
cd web
npm install
npm run dev
# Abra: http://localhost:3000/?customer_zip_prefix=05311&context=conscious_buyer
```

**CEP mágico para demo:** `05311` (São Paulo) — mostra os melhores resultados para vendedores e maior uso do selo verde.

```bash
# Ver o JSON que o servidor manda:
curl "http://localhost:8000/api/v1/home?customer_zip_prefix=05311&context=conscious_buyer"
```

## Como o projeto se organiza

```text
src/features/
  home_contextual/   # monta a Home
  green_logistics/   # distância, CO₂, selo, modalidades
  checkout/          # simulação de compra
  product_detail/    # tela de detalhe do produto
src/schemas/sdui.py  # o contrato: { type, version, props, actions }
web/                 # app Next.js que só renderiza o que o servidor manda
scripts/etl_load_sample.py  # carrega a amostra Olist
```

Regras e mapa completo para contribuir: [AGENTS.md](AGENTS.md) + [docs/PROJECT_BOOTSTRAP.md](docs/PROJECT_BOOTSTRAP.md).

## Para ir mais fundo

| Quero... | Abrir |
|---|---|
| Guia técnico completo (antigo README) | [docs/GUIA-COMPLETO.md](docs/GUIA-COMPLETO.md) |
| Entender o contrato SDUI + logística | [docs/tech_spec.md](docs/tech_spec.md) |
| Ver números de latência e Redis | [docs/performance.md](docs/performance.md) |
| Entender a defesa do TCC | [docs/tese-rastreabilidade.md](docs/tese-rastreabilidade.md) |

## Checks rápidos

```bash
pytest -q                          # backend (igual ao CI)
cd web && npm run lint && npm run typecheck && npm test   # frontend
```

## Reprodução do zero em outra máquina (T2)

Para provar que o projeto sobe fora da máquina de desenvolvimento. Faça num computador que
**nunca** rodou o projeto, cronometre cada passo e anote divergências no card do Trello.
Tempos de referência medidos em 02/11 num notebook na tomada (download depende da rede).

| # | Passo | Comando | Tempo esperado | Confere |
|---|---|---|---|---|
| 1 | Clonar | `git clone <url> && cd marketplace-tcc` | < 1 min | |
| 2 | Configurar | copiar `.env.example` para `.env` (os valores padrão servem) | — | |
| 3 | Dados brutos | baixar o *Brazilian E-Commerce Public Dataset by Olist* (Kaggle) e pôr os 9 CSVs em `data/raw/` (não são versionados) | 2–5 min | |
| 4 | Banco e cache | `docker compose up -d` | 1–3 min na 1ª vez (imagens `postgres:16` e `redis:7-alpine`) | `docker ps` mostra `olist-postgres` e `olist-redis` |
| 5 | Python | `python -m venv .venv`, ativar, `pip install -r requirements.txt` | 1–3 min | |
| 6 | ETL | `python -m scripts.etl_load_sample` | **~70 s** | termina com a linha `DEMO MULTI-VENDEDOR` |
| 7 | Testes do backend | `pytest -q` | **~15 s** | 0 falhas |
| 8 | API | `uvicorn src.main:app --port 8000` (outro terminal) | ~5 s | `http://localhost:8000/docs` abre |
| 9 | Front | `cd web && npm install && npx playwright install chromium` | 2–4 min | |
| 10 | Checks do front | `npm run lint && npm run typecheck && npm test` | ~1 min | 0 falhas |
| 11 | Jornada real | `npm run e2e` (sobe o próprio `next dev` na porta 3100) | **~1 min** + ~30 s da 1ª compilação | 8 de 8 verdes |

Total esperado: **~15 a 20 min**, quase todo de download. Se um `next dev` já estiver
rodando em `web/`, o Next 16 recusa outro: use `E2E_BASE_URL=http://localhost:3000 npm run e2e`.

Recarregou o ETL com a API no ar? Limpe o cache (TTL de 1h):

```bash
docker exec olist-redis redis-cli FLUSHALL
```

---
Feito com dados reais, telas dirigidas pelo servidor e uma pergunta simples: **e se comprar perto fosse o padrão?**
