# Handoff — Sprint 4: Comparativo de modalidades de entrega + correção do CO₂

> **Para agentes sem contexto:** leia primeiro `@docs/PROJECT_BOOTSTRAP.md`, depois este arquivo.
> Sprints 1–3 **já estão implementadas** — não reimplementar do zero.

> **Este handoff é retroativo:** ao contrário dos anteriores, foi escrito **depois** da entrega.
> Os critérios de aceite já estão marcados e as seções descrevem o que existe no código, não
> o que precisa ser feito. Serve como especificação do estado atual para a Sprint 5.

## Fonte de verdade (ordem de leitura)

1. **Este arquivo** (`docs/sprint4-handoff.md`) — estado atual
2. `@docs/PROJECT_BOOTSTRAP.md` — visão geral do repo
3. `@README.md` — como subir docker + ETL + API + frontend
4. `@docs/tech_spec.md` — contrato SDUI
5. `@docs/sprint3-handoff.md` — sprint anterior (histórico)
6. `@.cursorrules` — regras de código

**Não** usar transcripts antigos como especificação.

---

## Objetivo

| Trilha | Entrega |
|--------|---------|
| **A — Modalidades de entrega** | Bloco SDUI `delivery_options`; `POST /checkout/simulate` aceita `delivery_option` e recompõe a tela |
| **B — Frontend** | Renderização do bloco + re-simulação server-driven pela `action` do próprio bloco |
| **C — Dívida técnica** | `format_co2`, CO₂ por quantidade, arredondamento monetário |

Diferente da Sprint 3 (~95% backend), aqui as duas frentes andaram juntas.

---

## Contexto que motivou a sprint

A amostra do ETL subiu de 1.000 para **10.000 `order_items`** (commit `f7e5246`). Efeito colateral:

| | Antes (1k) | Depois (10k) |
|---|---|---|
| `cep_centroids` | ~700 prefixos | **6.403 prefixos** |
| `olist_products` | ~800 | **6.575** |
| Produto mais próximo (CEP 05311) | ~7 km | **~4 km** |

Com centroides mais densos o ranking do `conscious_buyer` finalmente tem o que ordenar — mas as
distâncias caíram tanto que a emissão passou para a ordem de `0,0004 kg`, e o `f"{co2_kg:.2f} kg"`
em `badge.py` imprimia **`~0.00 kg CO₂` em todo selo do sistema**. O número que sustenta o eixo de
logística verde do TCC aparecia zerado na tela.

---

## Decisões fechadas (não reinterpretar)

| Tópico | Decisão |
|--------|---------|
| Modalidades | Três: `express`, `standard`, `green`. `standard` é o **default** e usa o `freight_value` real da amostra **sem fator** — é a linha de base auditável |
| Origem dos fatores | `express`/`green` são **cenário declarado**, não dado do Olist. O dataset não tem modalidade, transportadora nem modal de transporte |
| Onde a ressalva vive | Docstring do módulo + campo `note` no JSON + exibida na tela. **Não** remover nenhuma das três |
| Coerência da tela | Frete, CO₂ do `impact_banner` e CO₂ do label do selo saem **todos do mesmo `mode`** |
| Selo | Continua sendo regra de **distância** (`d_km < 100`); a modalidade só altera o CO₂ no label |
| Formatação de CO₂ | `format_co2`: gramas abaixo de 10 g, kg acima, vírgula pt-BR. Corrigido na **origem** (`co2.py`), não em cada consumidor |
| CO₂ × quantidade | Emissão acompanha a massa embarcada (`weight_g * quantity`) |
| Frete × quantidade | **Não** multiplica — na amostra é o valor de um envio (decisão da Sprint 3, mantida) |
| Estado no cliente | O frontend **não** guarda contexto de checkout: o bloco carrega `product_id`/`quantity` que o servidor mandou |
| ETL | Não alterado nesta sprint |

---

## Trilha A — Backend

### A1. Módulo de modalidades

**Arquivo novo:** `src/features/green_logistics/delivery_options.py`

`DeliveryMode` é uma dataclass congelada; `MODES` é uma tupla na ordem
mais rápida → mais verde:

| id | label | `price_factor` | `co2_factor` | `base_days` | `km_per_day` |
|----|-------|---------------|-------------|------------|-------------|
| `express` | Expressa | 1.6 | 2.5 | 1 | 900 |
| `standard` | Padrão | **1.0** | **1.0** | 2 | 450 |
| `green` | Verde | 0.85 | 0.6 | 4 | 350 |

> **Hoje (Sprint 7): `base_days` e `km_per_day` não existem mais.** O prazo
> deixou de ser arbitrado e passou a sair de `ETA_BANDS`, a mediana medida em
> 95.921 entregas reais do Olist por faixa de distância. Cada modalidade agora
> tem um único `eta_factor` sobre essa linha de base: `express` 0.5,
> `standard` **1.0** (é a medição, sem fator), `green` 1.5. O modelo antigo
> subestimava — dava 3 dias para uma entrega local que leva 4,9, e 7 dias para
> 2.000 km que levam 17,2. Ver o docstring de `delivery_options.py`.

Funções expostas:

- `resolve_mode(id | None)` — cai em `standard` quando ausente
- `eta_days(mode, distance_km)` — `base_days + ceil(distance / km_per_day)`
  (**hoje:** `ceil(base_eta_days(distance) × eta_factor)`)
- `mode_co2_kg(mode, distance_km, weight_g)` — baseline GHG × `co2_factor`; `None` sem distância ou massa
- `build_delivery_options(base_freight, distance_km, weight_g, selected_id)` — uma `DeliveryOptionProps` por modalidade

`GREENEST_MODE_ID` é **derivado** de `MODES` (menor `co2_factor`), não escrito à mão — se os
fatores mudarem, a recomendação acompanha.

### A2. Contrato SDUI

**Arquivo:** `src/schemas/sdui.py`

```python
class DeliveryOptionProps(BaseModel):
    id: str
    label: str
    description: str | None = None
    eta_days: int
    price: float
    co2_kg: float | None = None
    recommended: bool = False
    selected: bool = False

class DeliveryOptionsProps(BaseModel):
    product_id: str        # viaja de volta na action
    quantity: int          # idem
    distance_km: float | None = None
    selected_id: str
    options: list[DeliveryOptionProps]
    note: str | None = None
```

`DeliveryOptionsBlock` (`type: "delivery_options"`, `version: 1`) entra na união discriminada
`UIComponent`.

**Uma `action` para o bloco todo**, não uma por opção: `api_call` POST
`/api/v1/checkout/simulate` com `body_key: "checkout"`. O cliente já sabe qual card foi
clicado — não precisa de três ações no envelope.

### A3. Endpoint

**Arquivos:** `checkout/schemas.py`, `checkout/router.py`, `checkout/composer.py`

`CheckoutSimulateRequest` ganha `delivery_option: str | None = None`. O router valida contra
`MODES_BY_ID` **antes** de tocar o banco e retorna **422** com o `detail` listando as válidas —
sem isso um id errado viraria `KeyError` → 500.

O composer resolve o `mode` uma vez e o usa em tudo:

```python
mode = resolve_mode(delivery_option)
shipped_weight_g = (product.weight_g or 0.0) * quantity or None

distance_km, badge = await build_badge_for_pair(..., weight_g=shipped_weight_g,
                                                co2_factor=mode.co2_factor)
co2_kg = mode_co2_kg(mode, distance_km, shipped_weight_g)
freight = round(product.freight_value * mode.price_factor, 2)
```

Tela resultante: `checkout_summary` → `delivery_options` → `impact_banner`.

### A4. Assinaturas alteradas (compatíveis)

| Função | Mudança |
|--------|---------|
| `build_sustainability_props` | `+ co2_factor: float = 1.0` |
| `build_badge_for_pair` | `+ co2_factor: float = 1.0` |
| `compose_checkout` | `+ delivery_option: str \| None = None` |

Defaults preservam o comportamento da Home, que não conhece modalidade.

---

## Trilha B — Frontend

| Arquivo | Mudança |
|---------|---------|
| `web/lib/sdui.ts` | Tipos `DeliveryOption` e `DeliveryOptionsBlock`; entram na união `UIComponent` |
| `web/components/blocks.tsx` | Componente `DeliveryOptions` |
| `web/components/sdui.tsx` | Uma linha no `REGISTRY`; `Modal` ganha prop `wide` |
| `web/components/sdui-context.tsx` | `RunContext` ganha `productId` e `deliveryOption`; `checkoutBody` os envia |

Detalhes que não são óbvios lendo só o diff:

- **Barra comparativa de CO₂**, escalada pela maior emissão da lista. A leitura útil aqui é
  relativa: `0,42 g` sozinho não diz nada, meia barra ao lado da vizinha diz.
- **`role="radiogroup"` / `role="radio"` + `aria-checked`** — é uma escolha entre alternativas
  mutuamente exclusivas, não três botões independentes.
- **`productId` no `RunContext`** existe porque, ao re-simular a partir da tela de checkout, não
  há `ProductCardBlock` em mãos: `selected` já foi zerado. O bloco carrega o contexto que o
  servidor mandou.
- **Modal do checkout a 46rem** (`wide`) — a 32rem as três colunas espremem.

---

## Trilha C — Dívida técnica corrigida

| Bug | Correção | Onde |
|-----|----------|------|
| `~0.00 kg CO₂` em todo selo | `format_co2` escolhe g/kg e usa vírgula pt-BR | `co2.py` — corrigido na origem, selo e banner herdam |
| CO₂ ignorava `quantity` | `weight_g * quantity` | `checkout/composer.py` |
| `total: 233.70000000000002` no JSON | `round(..., 2)` em subtotal, frete e total | `checkout/composer.py` |

O frontend já contornava o primeiro no `impact_banner` (`co2Label` em `web/lib/sdui.ts`), mas o
`product_card` renderiza a string vinda do backend — por isso a correção teve de ser na origem.

---

## Critérios de aceite

- [x] Bloco `delivery_options` na tela de checkout com três modalidades
- [x] `standard` reflete o `freight_value` real da amostra, sem fator
- [x] `delivery_option` altera frete, CO₂ e selo de forma coerente entre si
- [x] `delivery_option` inválido retorna **422** listando as válidas
- [x] Ressalva sobre a origem dos fatores presente no JSON e na tela
- [x] Nenhum selo exibe `0,00 kg`
- [x] CO₂ escala com `quantity`
- [x] Frontend renderiza o bloco e re-simula sem guardar estado de checkout
- [x] `pytest` verde — **69 testes** (47 anteriores + 22 novos)
- [x] `tsc --noEmit` limpo
- [x] README com `curl` de `delivery_option`

Verificação end-to-end feita no navegador (CEP 05311, produto Brinquedos): ao escolher
**Verde**, frete R$ 7,78 → R$ 6,61, total R$ 66,51, CO₂ do selo 0,90 g → 0,54 g, mensagem
passando a citar a modalidade.

---

## Testes

**Novo:** `tests/test_delivery_options.py` (15 casos). Além do trivial, cobre as invariantes que
protegem o argumento do TCC:

- `standard` é linha de base intocada (`price_factor == co2_factor == 1.0`)
- a modalidade recomendada é de fato a de menor emissão
- **modalidades mais verdes são mais lentas** — se a opção verde fosse mais rápida *e* mais
  barata não haveria trade-off, e o comparativo perderia o sentido
- regressão do `0,00`: `format_co2(0.0004184) == "0,42 g"`

**Estendido:** `tests/test_checkout_simulate.py` (+7 casos) — seleção refletida no bloco, frete e
CO₂ menores no verde, total coerente com a modalidade, CO₂ dobrando com `quantity`, 422 para
modalidade inválida.

O fake `_fake_badge_for_pair` precisou ganhar `co2_factor` para acompanhar a assinatura real.

---

## Fora de escopo (não implementado)

- Carrinho multi-item; `checkout/simulate` segue com um `product_id` por chamada
- Busca, filtro por categoria, bloco `category_grid`
- Persistência da escolha de entrega (nada é gravado)
- Prazo/preço vindos de transportadora real ou API externa
- Testes de frontend (não há runner em `web/`) e CI — dívida conhecida
- Redis em runtime, Locust, PostGIS, `orchestrator`

---

## Sugestões para a Sprint 5

Em ordem de retorno para a defesa do TCC:

1. **Busca + categorias.** Com 6.575 produtos a vitrine sem filtro ficou pouco navegável — é a
   dor mais imediata criada pela amostra maior.
2. **Carrinho multi-item.** Agregar frete e CO₂ por vendedor tornaria o comparativo de entrega
   bem mais forte: consolidar itens de um mesmo seller é exatamente o argumento da modalidade
   verde, e hoje isso não pode ser demonstrado.
3. **Testes de frontend + CI.** Vitest cobrindo o executor de `actions` e o `ScreenRenderer`;
   workflow rodando `pytest` + `npm run build`.
