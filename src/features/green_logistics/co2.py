"""Emissao de CO2e para deslocar uma carga — metodologia baseada em atividade.

ISO 14083 e GLEC Framework: emissao = massa x distancia x intensidade do
VEICULO de cada trecho da cadeia. A cadeia modelada (Sprint 9):

1. distancia de estrada = linha reta (Haversine) x `CIRCUITY_FACTOR`;
2. os ultimos `LAST_MILE_KM` vao de van (ultima milha); o restante, de
   caminhao pesado (transferencia);
3. entrega com menos de `LAST_MILE_KM` de estrada vai inteira de van.

Sem corte rigido por distancia: a emissao cresce continuamente com ela. Um
corte em 100 km (tudo de van abaixo, caminhao acima) faria uma entrega a 99 km
emitir ~4x a de 101 km — contradizendo o proprio selo verde.

- massa em toneladas: a COBRAVEL, `max(real, cubada)`, ver `chargeable_weight_g`
- resultado em kg de CO2e, do poco a roda (WTW), como nas tabelas do GLEC

:warning: **Antes da Sprint 9** havia um fator unico, 0,102 kg CO2/(t.km), sobre a
linha reta: na pratica o fator de caminhao pesado aplicado a toda entrega,
inclusive a ultima milha, que vai de van e emite ~7x mais por t.km. A correcao
AUMENTA a emissao de toda entrega e REDUZ a vantagem relativa da compra local
(compra mediana, 432 km, contra uma local de 20 km: de 21,6x para ~5,5x).
Registro em `docs/tese-rastreabilidade.md` §6 e no handoff da Sprint 9.
"""

from __future__ import annotations

# Gonçalves, D.N.S.; Gonçalves, C.D.M.; De Assis, T.F.; Silva, M.A. (2014).
# Analysis of the difference between the euclidean distance and the actual road
# distance in Brazil. Transportation Research Procedia 3, 876-885. Media
# brasileira estrada/linha reta para linha reta < 891 km; aplicada tambem acima
# (declarado). ISO 14083 aceita a linha reta (GCD); a estrada e o que o caminhao roda.
CIRCUITY_FACTOR: float = 1.345

# World Economic Forum (2024). Transforming Urban Logistics, p. 5: para operadores
# de encomendas e expresso, a ultima milha "may typically be the last 15-20
# kilometres". Limite inferior: nao infla a penalidade da compra distante.
LAST_MILE_KM: float = 15.0

# GLEC Framework v2.0 (Smart Freight Centre, 2019, rev. 2022), Modulo 2, regiao
# "Europe and South America", WTW, diesel com 5% de biodiesel, sem refrigeracao:
FE_LINE_HAUL_KG_PER_T_KM: float = 0.092  # p. 104: HGV > 20 t (ponto de partida)
FE_LAST_MILE_KG_PER_T_KM: float = 0.680  # Tabela 41: van < 3,5 t

# Fator de cubagem rodoviario: 6.000 cm3 equivalem a 1 kg de carga. E a
# convencao do transporte rodoviario de carga fracionada no Brasil.
VOLUMETRIC_FACTOR_CM3_PER_KG: float = 6000.0


def chargeable_weight_g(weight_g: float | None, volume_cm3: float | None) -> float:
    """Massa que a carga OCUPA, nao a que ela pesa: `max(real, cubada)`.

    Um veiculo enche por volume antes de atingir o limite de peso quando a
    carga e leve, e a emissao daquela viagem se reparte pelo espaco ocupado.
    GLEC (Smart Freight Centre, 2023) e a ISO 14083 tratam isso por *chargeable
    weight* — as duas ja estao na bibliografia do trabalho.

    Isto NAO e detalhe: as dimensoes estao preenchidas em 100% dos produtos do
    Olist, e em **66,4% deles o peso cubado supera o real** (razao mediana
    1,43x, p90 4,44x). Usar so a massa subestimava a emissao de dois tercos do
    catalogo.

    :warning: **A CORRECAO AUMENTA A EMISSAO ESTIMADA** — e isso precisa ser
    dito ao comparar com qualquer numero publicado antes da Sprint 7. Na
    amostra carregada, a massa cobravel agregada e **1,41x** a massa real, e um
    item leve-e-volumoso isolado chega a 3,3x. Numeros de CO2 anteriores a esta
    mudanca subestimavam, nao e a mudanca que superestima.

    Sem volume conhecido, devolve a massa real — nao ha o que corrigir.
    """
    real = weight_g or 0.0
    if not volume_cm3 or volume_cm3 <= 0:
        return real
    cubada = volume_cm3 / VOLUMETRIC_FACTOR_CM3_PER_KG * 1000.0
    return max(real, cubada)


def road_distance_km(straight_km: float) -> float:
    """Linha reta (Haversine) -> distancia de estrada estimada."""
    return straight_km * CIRCUITY_FACTOR


def calculate_co2_kg(
    distance_km: float, weight_g: float, volume_cm3: float | None = None
) -> float:
    """Emissao estimada em kg de CO2e para deslocar essa carga.

    `distance_km` e a LINHA RETA entre os centroides de CEP — a mesma que o
    resto do sistema calcula; a conversao para estrada acontece aqui.
    `volume_cm3` opcional; informado, a conta usa a massa cubada quando maior.

    Nao e linear na distancia: para comparar duas origens, subtraia as
    emissoes, nunca as distancias.
    """
    if distance_km <= 0:
        return 0.0
    weight_t = chargeable_weight_g(weight_g, volume_cm3) / 1_000_000
    estrada = road_distance_km(distance_km)
    van = min(estrada, LAST_MILE_KM)
    return weight_t * ((estrada - van) * FE_LINE_HAUL_KG_PER_T_KM + van * FE_LAST_MILE_KG_PER_T_KM)


def format_co2(kg: float) -> str:
    """Formata emissao para exibicao em pt-BR, escolhendo a unidade legivel.

    A amostra Olist tem pesos baixos e, com a densidade de CEPs da amostra de
    10k, as distancias caem para poucos km: a emissao fica na ordem de
    0,0004 kg e um `.2f` em kg imprimiria "0,00 kg" — apagando justamente o
    numero que sustenta o argumento de logistica verde. Abaixo de 10 g,
    exibimos em gramas.
    """
    if kg >= 0.01:
        return f"{kg:.2f} kg".replace(".", ",")
    return f"{kg * 1000:.2f} g".replace(".", ",")
