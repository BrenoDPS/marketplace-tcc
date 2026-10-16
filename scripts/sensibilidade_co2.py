"""Sensibilidade do CO2 aos parametros do motor (Sprint 12).

Varia cada constante de `green_logistics/co2.py` (circuidade, ultima milha,
fatores GLEC, cubagem) em +-20% e em valores alternativos com fonte, refaz a
analise de CO2 evitado sobre as compras reais (`scripts.co2_evitado.calcular`,
dataset completo) e reporta o que muda: a emissao absoluta e a parcela evitada.

    python -m scripts.sensibilidade_co2   # grava docs/resultados/sensibilidade-co2.md (~7 min)

Deterministico: sem amostragem, nao ha semente; o mesmo dado e o mesmo commit
dao a mesma tabela. "O mais proximo emite menos" nao e testado por cenario: com o
mesmo produto (mesma massa), o motor cresce com a distancia para QUALQUER
parametro positivo, e `calcular` ja falha (assert) se a recomendacao emitir mais.
"""

from __future__ import annotations

import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

from scripts.co2_evitado import calcular
from src.features.green_logistics import co2

SAIDA = Path("docs/resultados/sensibilidade-co2.md")
PARAMS = ("CIRCUITY_FACTOR", "LAST_MILE_KM", "FE_LINE_HAUL_KG_PER_T_KM", "FE_LAST_MILE_KG_PER_T_KM",
          "VOLUMETRIC_FACTOR_CM3_PER_KG")
NOMES = {
    "CIRCUITY_FACTOR": "circuidade",
    "LAST_MILE_KM": "última milha (km)",
    "FE_LINE_HAUL_KG_PER_T_KM": "fator do caminhão",
    "FE_LAST_MILE_KG_PER_T_KM": "fator da van",
    "VOLUMETRIC_FACTOR_CM3_PER_KG": "divisor de cubagem",
}
BASE = {p: getattr(co2, p) for p in PARAMS}


def _cenarios() -> list[tuple[str, dict[str, float]]]:
    out: list[tuple[str, dict[str, float]]] = [("referência", {})]
    for p in PARAMS:
        out += [(f"{NOMES[p]} −20%", {p: BASE[p] * 0.8}), (f"{NOMES[p]} +20%", {p: BASE[p] * 1.2})]
    out += [
        ("circuidade 1,27 (mediana medida contra o OSRM, §5.1.3)", {"CIRCUITY_FACTOR": 1.27}),
        ("última milha 20 km (limite superior do WEF, 2024)", {"LAST_MILE_KM": 20.0}),
        ("cubagem rodoviária 300 kg/m³ (3.333 cm³/kg)", {"VOLUMETRIC_FACTOR_CM3_PER_KG": 1e6 / 300}),
        ("todos × 0,8", {p: BASE[p] * 0.8 for p in PARAMS}),
        ("todos × 1,2", {p: BASE[p] * 1.2 for p in PARAMS}),
    ]
    return out


@contextmanager
def _com(valores: dict[str, float]):
    # O motor le as constantes do modulo a cada chamada: trocar o atributo basta.
    try:
        for p, v in valores.items():
            setattr(co2, p, v)
        yield
    finally:
        for p, v in BASE.items():
            setattr(co2, p, v)


def medir() -> list[dict]:
    linhas = []
    for nome, valores in _cenarios():
        with _com(valores):
            _, r = calcular()
            razao = co2.calculate_co2_kg(432, 1000) / co2.calculate_co2_kg(50, 1000)
        linhas.append({"cenario": nome, **r, "razao_432_50": razao})
        print(f"{nome:58} evitado {r['evitado_kg'] / r['co2_real_kg']:.4f}  real {r['co2_real_kg']:.1f} kg")
    return linhas


def _markdown(linhas: list[dict]) -> str:
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    num = lambda x, casas=0: f"{x:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")  # noqa: E731
    pct = lambda x: f"{x * 100:.1f}%".replace(".", ",").replace("-", "−")  # noqa: E731
    ref = linhas[0]
    tabela = [
        "| cenário | CO₂ das escolhas reais (kg) | vs. referência | CO₂ evitado (kg) | evitado | evitado, regra da aplicação | CO₂ a 432 km ÷ a 50 km |",
        "|---|---|---|---|---|---|---|",
    ]
    for x in linhas:
        variacao = x["co2_real_kg"] / ref["co2_real_kg"] - 1
        cenario = f"**{x['cenario']}**" if x is ref else x["cenario"]
        tabela.append(
            f"| {cenario} | {num(x['co2_real_kg'], 1)} | {'—' if x is ref else ('+' if variacao >= 0 else '') + pct(variacao)} | "
            f"{num(x['evitado_kg'], 1)} | {pct(x['evitado_kg'] / x['co2_real_kg'])} | "
            f"{pct(x['app_evitado_kg'] / x['co2_real_kg'])} | {num(x['razao_432_50'], 1)}× |"
        )
    evitados = [x["evitado_kg"] / x["co2_real_kg"] for x in linhas]
    absolutos = [x["co2_real_kg"] / ref["co2_real_kg"] - 1 for x in linhas]
    return "\n".join([
        "# Sensibilidade do CO₂ aos parâmetros do motor",
        "",
        f"> Gerado por `python -m scripts.sensibilidade_co2` no commit `{commit}`, sobre as compras reais do",
        f"> dataset Olist **completo** ({num(ref['itens_com_alternativa'])} itens com mais de um vendedor). Cada cenário troca",
        "> constantes de `src/features/green_logistics/co2.py` e refaz `scripts.co2_evitado`.",
        "",
        "## Resultado",
        "",
        f"A parcela de CO₂ evitado fica entre **{pct(min(evitados))} e {pct(max(evitados))}** em todos os cenários "
        f"(referência {pct(evitados[0])}); a emissão absoluta varia de {pct(min(absolutos))} a +{pct(max(absolutos))}. "
        "A recomendação nunca emite mais que a escolha real em nenhum cenário: o mesmo produto, mais perto, "
        "emite menos para qualquer valor positivo dos parâmetros.",
        "",
        *tabela,
        "",
        "Valores de referência: circuidade 1,345; última milha 15 km; caminhão 0,092 e van 0,680 kg CO₂e por t·km; "
        "cubagem 6.000 cm³/kg. \"CO₂ a 432 km ÷ a 50 km\": quantas vezes 1 kg na distância mediana das compras "
        "(432 km) emite o mesmo kg vindo de 50 km, dentro do raio do selo.",
        "",
        "## Limites",
        "",
        "- Um parâmetro de cada vez, mais dois cenários extremos com todos juntos; não é uma análise de incerteza "
        "conjunta (Monte Carlo).",
        "- ±20% é uma faixa arbitrada; os cenários com fonte (OSRM, WEF, cubagem rodoviária) ancoram a faixa em "
        "valores defensáveis.",
    ]) + "\n"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # console do Windows (cp1252) nao tem o "−"
    linhas = medir()
    SAIDA.write_text(_markdown(linhas), encoding="utf-8")
    print(SAIDA)


if __name__ == "__main__":
    main()
