# Haversine × rota real (OSRM)

> Gerado por `python -m scripts.haversine_osrm` no commit `2de753d`, em 12/10/2026, sobre o
> dataset Olist **completo**. Rotas: servidor público do OSRM (`router.project-osrm.org`, perfil
> `driving`, malha do OpenStreetMap), entre os mesmos centroides de prefixo de CEP que a aplicação
> usa. Respostas por par em `docs/resultados/haversine-osrm.csv` (cache: rodar de novo não consulta o servidor).

## A — precisão: 100 pares de compras reais, 20 por faixa de linha reta

"Estimada" = linha reta × 1,345, a estrada que o motor de CO₂ usa (`co2.road_distance_km`).
Viés = mediana de (estimada − rota) / rota: positivo, o motor superestima a estrada.

| faixa (linha reta) | n | MAE linha reta (km) | MAPE linha reta | MAE estimada (km) | MAPE estimada | viés estimada | Spearman | rota ÷ linha reta: mediana (p10–p90) |
|---|---|---|---|---|---|---|---|---|
| 1–100 km | 20 | 10,6 | 26,9% | 5,2 | 11,1% | 0,5% | 0,979 | 1,34 (1,18–1,61) |
| 100–500 km | 20 | 101,9 | 21,2% | 50,0 | 10,8% | 10,3% | 0,854 | 1,22 (1,13–1,46) |
| 500–1.000 km | 20 | 177,4 | 19,2% | 73,3 | 9,1% | 9,0% | 0,956 | 1,23 (1,15–1,34) |
| 1.000–2.000 km | 20 | 373,6 | 21,5% | 93,2 | 5,7% | 5,0% | 0,982 | 1,28 (1,21–1,34) |
| ≥ 2.000 km | 20 | 580,7 | 20,6% | 194,4 | 7,0% | 6,2% | 0,850 | 1,27 (1,20–1,32) |
| **todas** | 100 | 248,9 | 21,9% | 83,2 | 8,7% | 6,2% | 0,997 | 1,27 (1,16–1,41) |

## B — ordem: a decisão que a vitrine toma

37 decisões reais (um comprador de um produto vendido por vendedores em CEPs distintos, com todas as ofertas do produto), 102 pares.

| | valor |
|---|---|
| o mais próximo em linha reta **é** o mais próximo pela estrada | **86,5%** das decisões |
| pares de vendedores na mesma ordem nos dois métodos | 91,0% de 111 comparações |
| decisões em que diverge | 5 — em 3 delas a regra da vitrine (`escolher_oferta`) já trata os dois vendedores como equidistantes e decide pelo preço |
| quando diverge: estrada a mais da escolha por linha reta | mediana 2,0 km; pior caso 6,4 km (2,1% da rota) |

## Limites

- Origem e destino são **centroides de prefixo de CEP**, não endereços: o erro de posição do
  centroide é o mesmo nos dois métodos e não entra nesta comparação.
- O OSRM encaixa cada ponto na via mais próxima; a distância até ela fica fora da rota (mediana 14 m, máxima 150 m).
- Pares sem rota no OSRM: 0 (fora das métricas).
- Rota = caminho mais rápido de carro, não o da transportadora; balsas entram na rota.
