"""Conferencia externa do motor de CO2: fator de caminhao do Programa Brasileiro GHG Protocol.

O motor usa fatores do GLEC v2.0 (caminhao pesado 0,092 kg CO2e/t.km, regiao "Europa e
America do Sul"). A referencia brasileira independente que a metodologia ja cita (§3.2) e o
fator da frota rodoviaria a diesel do Programa Brasileiro GHG Protocol: 0,104 kg CO2/t.km.
Este script mede quanto a emissao de 1 kg muda por distancia se o caminhao usar o fator
brasileiro, e o efeito combinado com a circuidade medida contra o OSRM acima de 100 km
(1,27, `docs/resultados/haversine-osrm.md`), que puxa no sentido contrario.

    python -m scripts.fator_externo_co2   # grava docs/resultados/fator-externo-co2.md (instantaneo)

Limite: o fator do GHG Protocol e de CO2 da queima (tanque a roda) e o do GLEC e CO2e do poco
a roda; a comparacao confere a ordem de grandeza, nao a equivalencia de escopo. Nao ha fator
brasileiro independente para a van da ultima milha.
"""

from __future__ import annotations

import subprocess
from contextlib import contextmanager
from pathlib import Path

from src.features.green_logistics import co2

FATOR_BR = 0.104  # kg CO2/(t.km), Programa Brasileiro GHG Protocol (2026), citado na §3.2
CIRCUIDADE_OSRM = 1.27  # mediana rota/linha reta acima de 100 km (§5.1.3)
DISTANCIAS = (50, 100, 432, 1000, 2000)  # km em linha reta; 432 = mediana das compras do dataset
SAIDA = Path("docs/resultados/fator-externo-co2.md")


@contextmanager
def constantes(**valores):
    antes = {k: getattr(co2, k) for k in valores}
    for k, v in valores.items():
        setattr(co2, k, v)
    try:
        yield
    finally:
        for k, v in antes.items():
            setattr(co2, k, v)


def g_por_kg(km: float) -> float:
    return co2.calculate_co2_kg(km, 1000.0) * 1000


def br(x: float, casas: int = 1, sinal: bool = False) -> str:
    return (f"{x:+.{casas}f}" if sinal else f"{x:.{casas}f}").replace(".", ",")


def main() -> None:
    linhas = []
    for km in DISTANCIAS:
        ref = g_por_kg(km)
        with constantes(FE_LINE_HAUL_KG_PER_T_KM=FATOR_BR):
            so_fator = g_por_kg(km)
        with constantes(FE_LINE_HAUL_KG_PER_T_KM=FATOR_BR, CIRCUITY_FACTOR=CIRCUIDADE_OSRM if km > 100 else co2.CIRCUITY_FACTOR):
            combinado = g_por_kg(km)
        linhas.append(f"| {km:,} | {br(ref)} | {br(so_fator)} ({br((so_fator / ref - 1) * 100, sinal=True)}%) | "
                      f"{br(combinado)} ({br((combinado / ref - 1) * 100, sinal=True)}%) |".replace(",", ".", 1 if km >= 1000 else 0))
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    SAIDA.write_text(
        f"""# Conferência externa do motor de CO₂: fator brasileiro de caminhão

> Gerado por `python -m scripts.fator_externo_co2` no commit `{commit}`. Emissão de 1 kg de massa
> cobrável, por distância em linha reta. Motor: GLEC v2.0 (caminhão {br(co2.FE_LINE_HAUL_KG_PER_T_KM, 3)},
> van {br(co2.FE_LAST_MILE_KG_PER_T_KM, 3)} kg CO₂e/t·km, circuidade {br(co2.CIRCUITY_FACTOR, 3)}).
> Referência: Programa Brasileiro GHG Protocol, {br(FATOR_BR, 3)} kg CO₂/t·km (frota rodoviária a diesel).

| linha reta (km) | motor (g CO₂e) | caminhão com fator brasileiro | + circuidade medida no OSRM ({br(CIRCUIDADE_OSRM, 2)} acima de 100 km) |
|---|---|---|---|
{chr(10).join(linhas)}

**Leitura.** O fator de caminhão do GLEC é 11,5% menor que o brasileiro; com ele, a emissão das
entregas longas sobe até 12,5%. A circuidade do motor, por outro lado, superestima a estrada
acima de 100 km (§5.1.3). As duas aproximações puxam em sentidos opostos: juntas, a diferença
na distância mediana das compras (432 km) é de cerca de +5%. A ordem de grandeza do motor se
confirma contra uma referência brasileira independente; a parcela evitada não depende disso
(sensibilidade: 9,5% a 10,0% com o fator de caminhão em ±20%).

**Limites.** Escopos diferentes (CO₂ da queima × CO₂e do poço à roda); não há fator brasileiro
independente para a van da última milha, que domina as entregas locais.
""",
        encoding="utf-8")
    print(SAIDA.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
