# Olist SDUI Marketplace

Marketplace contextual adaptativo com Server-Driven UI, baseado no dataset real da Olist.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

## Executar

```bash
uvicorn src.main:app --reload
```

Acesse a documentação interativa em **http://localhost:8000/docs**.

## Testes

```bash
pytest
```

## Arquitetura (Vertical Slice)

```
src/
  schemas/sdui.py            # Contrato SDUI (envelope + UIAction + ScreenResponse)
  features/
    home_contextual/         # Composicao de tela por contexto (ATIVA na Fase 1)
    green_logistics/         # Stub - PostGIS, distancia, CO2 (Fase 2)
    checkout/                # Stub - pedido simulado (Fase 2)
    orchestrator/            # Stub - versionamento e cache SDUI (Fase 2)
```

## Roadmap / Fase 2

A Fase 1 entrega o contrato SDUI base (`{ type, version, props, actions }` + `schema_version`)
e a tela `home_contextual` com mocks. Itens explicitamente fora de escopo nesta fase:

- **green_logistics**: integracao real PostGIS (`ST_DistanceSphere`), calculo
  de CO2 com EF=0.062 kg CO2/(t.km), selo automatico para entregas < 100 km e
  baseline ~139 km do dataset Olist (`docs/tech_spec.md` secao 3).
- **checkout**: persistencia de pedidos/sessoes e validacao de frete (`docs/prd.md` secao 4).
- **orchestrator**: versionamento de blocos por `version`, roteamento dinamico e
  chaves de cache SDUI no Redis alinhadas a `schema_version` da tela e `version`
  por bloco (`docs/tech_spec.md` secoes 1 e 4).
- **Ingestao Olist**: carga das tabelas `orders`, `products`, `customers`, `geolocation`.
- **Wiring real das `actions`**: hoje as `actions` sao geradas mock no composer; Fase 2
  conecta com endpoints reais (ex.: `api_call` para `/api/v1/checkout`).
- **Cache Redis**: o cliente existe mas ainda nao e usado para fragmentos SDUI.

Os `SustainabilityProps` no `home_contextual/composer.py` sao mockados com
`_MOCK_GREEN_BADGE` e marcados com `TODO[green_logistics]` para serem
substituidos pela logica real da fatia `green_logistics` na Fase 2.
