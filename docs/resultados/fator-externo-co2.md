# Conferência externa do motor de CO₂: fator brasileiro de caminhão

> Gerado por `python -m scripts.fator_externo_co2` no commit `8544e3b`. Emissão de 1 kg de massa
> cobrável, por distância em linha reta. Motor: GLEC v2.0 (caminhão 0,092,
> van 0,680 kg CO₂e/t·km, circuidade 1,345).
> Referência: Programa Brasileiro GHG Protocol, 0,104 kg CO₂/t·km (frota rodoviária a diesel).

| linha reta (km) | motor (g CO₂e) | caminhão com fator brasileiro | + circuidade medida no OSRM (1,27 acima de 100 km) |
|---|---|---|---|
| 50 | 15,0 | 15,6 (+4,2%) | 15,6 (+4,2%) |
| 100 | 21,2 | 22,6 (+6,8%) | 22,6 (+6,8%) |
| 432 | 62,3 | 69,1 (+10,9%) | 65,7 (+5,5%) |
| 1.000 | 132,6 | 148,5 (+12,0%) | 140,7 (+6,2%) |
| 2.000 | 256,3 | 288,4 (+12,5%) | 272,8 (+6,4%) |

**Leitura.** O fator de caminhão do GLEC é 11,5% menor que o brasileiro; com ele, a emissão das
entregas longas sobe até 12,5%. A circuidade do motor, por outro lado, superestima a estrada
acima de 100 km (§5.1.3). As duas aproximações puxam em sentidos opostos: juntas, a diferença
na distância mediana das compras (432 km) é de cerca de +5%. A ordem de grandeza do motor se
confirma contra uma referência brasileira independente; a parcela evitada não depende disso
(sensibilidade: 9,5% a 10,0% com o fator de caminhão em ±20%).

**Limites.** Escopos diferentes (CO₂ da queima × CO₂e do poço à roda); não há fator brasileiro
independente para a van da última milha, que domina as entregas locais.
