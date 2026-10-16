# Sensibilidade do CO₂ aos parâmetros do motor

> Gerado por `python -m scripts.sensibilidade_co2` no commit `dbde640`, sobre as compras reais do
> dataset Olist **completo** (14.367 itens com mais de um vendedor). Cada cenário troca
> constantes de `src/features/green_logistics/co2.py` e refaz `scripts.co2_evitado`.

## Resultado

A parcela de CO₂ evitado fica entre **9,5% e 10,0%** em todos os cenários (referência 9,8%); a emissão absoluta varia de −23,4% a +66,8%. A recomendação nunca emite mais que a escolha real em nenhum cenário: o mesmo produto, mais perto, emite menos para qualquer valor positivo dos parâmetros.

| cenário | CO₂ das escolhas reais (kg) | vs. referência | CO₂ evitado (kg) | evitado | evitado, regra da aplicação | CO₂ a 432 km ÷ a 50 km |
|---|---|---|---|---|---|---|
| **referência** | 2.601,3 | — | 254,2 | 9,8% | 9,8% | 4,1× |
| circuidade −20% | 2.137,3 | −17,8% | 204,3 | 9,6% | 9,5% | 3,7× |
| circuidade +20% | 3.065,0 | +17,8% | 304,3 | 9,9% | 9,9% | 4,5× |
| última milha (km) −20% | 2.544,7 | −2,2% | 253,4 | 10,0% | 9,9% | 4,6× |
| última milha (km) +20% | 2.657,6 | +2,2% | 255,2 | 9,6% | 9,6% | 3,8× |
| fator do caminhão −20% | 2.147,4 | −17,5% | 203,9 | 9,5% | 9,5% | 3,7× |
| fator do caminhão +20% | 3.055,3 | +17,5% | 304,6 | 10,0% | 9,9% | 4,6× |
| fator da van −20% | 2.535,0 | −2,5% | 253,7 | 10,0% | 10,0% | 4,6× |
| fator da van +20% | 2.667,6 | +2,5% | 254,7 | 9,5% | 9,5% | 3,8× |
| divisor de cubagem −20% | 3.113,5 | +19,7% | 301,7 | 9,7% | 9,7% | 4,1× |
| divisor de cubagem +20% | 2.315,0 | −11,0% | 224,3 | 9,7% | 9,7% | 4,1× |
| circuidade 1,27 (mediana medida contra o OSRM, §5.1.3) | 2.472,0 | −5,0% | 240,3 | 9,7% | 9,7% | 4,0× |
| última milha 20 km (limite superior do WEF, 2024) | 2.694,9 | +3,6% | 255,9 | 9,5% | 9,5% | 3,6× |
| cubagem rodoviária 300 kg/m³ (3.333 cm³/kg) | 4.340,1 | +66,8% | 414,5 | 9,5% | 9,5% | 4,1× |
| todos × 0,8 | 1.992,7 | −23,4% | 193,1 | 9,7% | 9,7% | 4,1× |
| todos × 1,2 | 3.333,6 | +28,1% | 323,0 | 9,7% | 9,7% | 4,1× |

Valores de referência: circuidade 1,345; última milha 15 km; caminhão 0,092 e van 0,680 kg CO₂e por t·km; cubagem 6.000 cm³/kg. "CO₂ a 432 km ÷ a 50 km": quantas vezes 1 kg na distância mediana das compras (432 km) emite o mesmo kg vindo de 50 km, dentro do raio do selo.

## Limites

- Um parâmetro de cada vez, mais dois cenários extremos com todos juntos; não é uma análise de incerteza conjunta (Monte Carlo).
- ±20% é uma faixa arbitrada; os cenários com fonte (OSRM, WEF, cubagem rodoviária) ancoram a faixa em valores defensáveis.
