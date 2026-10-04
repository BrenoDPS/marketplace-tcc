# CO₂ evitado pela recomendação "mesmo produto, vendedor mais próximo"

> Gerado por `python -m scripts.co2_evitado` no commit `953fc4e`, sobre as compras reais
> do dataset Olist **completo** (112.650 itens). Motor de CO₂ da aplicação
> (cadeia de transporte, Sprint 9). Sem pedido gravado: compara a escolha FEITA com a recomendada.

## Resultado

| | valor |
|---|---|
| itens cujo produto tinha mais de um vendedor | **14.367** (12,8% do total) |
| desses, o comprador **já** escolheu o mais próximo | 48,3% |
| distância mediana: escolha real × recomendada | 437 km × 330 km |
| CO₂ das escolhas reais | 2.601,3 kg CO₂e |
| CO₂ se todos seguissem a recomendação | 2.347,1 kg CO₂e |
| **CO₂ evitado** | **254,2 kg CO₂e (9,8%)** |
| escala: CO₂ de todas as 112.070 compras mensuráveis do dataset | 26.934,9 kg CO₂e — o evitado é 0,9% dele |

## O trade-off de preço — nos 7.430 itens em que a recomendação trocaria o vendedor

| a recomendada é | itens |
|---|---|
| mais barata | 43,3% |
| mesmo preço (± R$ 0,01) | 6,3% |
| mais cara | 50,4% |
| diferença mediana (recomendada − real) | R$ 0,01 |

Preço de cada vendedor = mediana do que ele cobrou por aquele produto no dataset.

## Por UF do comprador (UFs com pelo menos 300 itens com alternativa)

| UF | itens com alternativa | já escolheu o mais próximo | CO₂ real (kg) | evitado (kg) | evitado |
|---|---|---|---|---|---|
| SP | 6.186 | 49,0% | 456,7 | 107,2 | 23,5% |
| RJ | 1.924 | 45,7% | 295,6 | 39,1 | 13,2% |
| MG | 1.617 | 46,1% | 259,1 | 29,1 | 11,2% |
| PR | 765 | 49,7% | 104,0 | 11,5 | 11,1% |
| RS | 745 | 49,7% | 196,9 | 14,2 | 7,2% |
| SC | 512 | 47,7% | 94,0 | 8,1 | 8,6% |
| BA | 482 | 51,0% | 230,2 | 8,4 | 3,7% |
| ES | 314 | 40,1% | 82,3 | 5,7 | 6,9% |

## Limites

- Só a ORIGEM muda; modalidade de entrega (cenário declarado) não entra.
- "Vendedor do produto" = quem o vendeu ao menos uma vez em 2016–2018; disponibilidade na data da compra não é conhecida.
- Distância em linha reta entre centroides de prefixo de CEP, convertida em estrada pelo motor.
