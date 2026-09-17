"""Calculo de emissao de CO2 para deslocamento de carga.

Formula: E = d * w * FE
- d em km
- w em toneladas — a massa COBRAVEL, `max(real, cubada)`, ver
  `chargeable_weight_g`
- FE = 0.102 kg CO2/(t.km) (GHG Protocol, transporte rodoviario padrao)
"""

from __future__ import annotations

EMISSION_FACTOR_KG_PER_T_KM: float = 0.102

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


def calculate_co2_kg(
    distance_km: float, weight_g: float, volume_cm3: float | None = None
) -> float:
    """Emissao estimada em kg de CO2 para deslocar essa carga.

    `volume_cm3` opcional para nao quebrar quem so tem massa; informado, a
    conta usa a massa cubada quando ela for maior.
    """
    weight_t = chargeable_weight_g(weight_g, volume_cm3) / 1_000_000
    return distance_km * weight_t * EMISSION_FACTOR_KG_PER_T_KM


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
