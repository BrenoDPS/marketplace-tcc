# Concentração logística regional

> Gerado por `python -m scripts.concentracao_regional` no commit `d712615`, sobre o
> dataset Olist **completo**: 112.650 itens vendidos (112.096 com centroide de CEP nas duas pontas),
> 95.828 compradores (pessoas, `customer_unique_id`) e 3.095 vendedores.

- **mesma UF:** itens em que o vendedor estava no estado do comprador
- **compra local:** itens com vendedor a menos de 100 km (o limiar do selo)
- **oferta local disponível:** compradores com ALGUM vendedor do dataset a menos de 100 km — o teto do que a recomendação poderia fazer

UFs com pelo menos 1.000 itens. Distância em linha reta entre centroides de prefixo de CEP.

| UF | itens | mesma UF | compra local (< 100 km) | distância mediana | compradores | oferta local disponível |
|---|---|---|---|---|---|---|
| **Brasil** | 112.096 | 36,3% | 18,7% | 432 km | 95.828 | 94,7% |
| SP | 47.338 | 76,3% | 39,5% | 163 km | 40.280 | 100,0% |
| RJ | 14.523 | 7,7% | 6,6% | 394 km | 12.365 | 100,0% |
| MG | 13.087 | 13,0% | 3,7% | 491 km | 11.244 | 95,9% |
| RS | 6.215 | 5,3% | 2,5% | 856 km | 5.273 | 97,0% |
| PR | 5.716 | 14,5% | 5,5% | 427 km | 4.871 | 100,0% |
| SC | 4.167 | 7,5% | 3,9% | 535 km | 3.529 | 100,0% |
| BA | 3.777 | 2,1% | 1,0% | 1.427 km | 3.267 | 74,9% |
| GO | 2.319 | 1,7% | 1,4% | 804 km | 1.943 | 88,0% |
| ES | 2.244 | 0,4% | 0,3% | 762 km | 1.958 | 96,1% |
| DF | 2.212 | 2,5% | 2,6% | 865 km | 1.907 | 100,0% |
| PE | 1.801 | 1,3% | 0,8% | 2.085 km | 1.600 | 89,3% |
| CE | 1.468 | 0,6% | 0,3% | 2.294 km | 1.308 | 83,7% |
| PA | 1.077 | 0,0% | 0,0% | 2.391 km | 946 | 0,0% |
| MT | 1.049 | 0,7% | 0,2% | 1.332 km | 874 | 54,3% |
