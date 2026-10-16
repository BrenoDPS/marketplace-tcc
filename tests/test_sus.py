import pytest

from scripts.sus import sus, tabular


def test_sus_nos_extremos_e_no_neutro() -> None:
    # Impares positivos, pares negativos: o melhor caso alterna 5 e 1.
    assert sus([5, 1] * 5) == 100.0
    assert sus([1, 5] * 5) == 0.0
    assert sus([3] * 10) == 50.0


def test_sus_recusa_resposta_fora_da_escala() -> None:
    with pytest.raises(ValueError):
        sus([6] + [3] * 9)
    with pytest.raises(ValueError):
        sus([3] * 9)


def _linha(p: str, notas: list[int], trocou: str, mesmo_preco: str) -> dict[str, str]:
    linha = {"participante": p, "faixa_etaria": "18-24", "compra_online": "1-2", "t5_trocou": trocou,
             "entendi_selo": "5", "confio_co2": "3", "troca_mesmo_preco": mesmo_preco,
             "troca_5pct": "nao", "troca_10pct": "nao", "comentario": ""}
    for t in ("t1", "t2", "t3", "t4", "t5"):
        linha[t], linha[f"{t}_s"] = "1", "30"
    linha.update({f"sus{i + 1}": str(r) for i, r in enumerate(notas)})
    return linha


def test_tabula_declarado_contra_revelado() -> None:
    md = tabular([
        _linha("P01", [5, 1] * 5, "sim", "sim"),
        _linha("P02", [3] * 10, "nao", "sim"),
        _linha("P03", [3] * 10, "nao_viu", "nao"),
    ])
    assert "**66,7 ± 28,9**" in md
    assert "| mesmo preço (declarado) | 2/3 (67%) |" in md
    # Revelado conta so quem VIU a sugestao: 1 de 2, nao 1 de 3.
    assert "**1/2 (50%)** dos que viram a sugestão" in md
