"""Tabula o teste de usabilidade: SUS, tarefas e preferencia declarada x revelada.

    python -m scripts.sus        # le docs/usabilidade/respostas.csv, grava docs/resultados/usabilidade.md

Protocolo e colunas em `docs/usabilidade/protocolo.md`.
"""

from __future__ import annotations

import csv
import statistics
from pathlib import Path

ENTRADA = Path("docs/usabilidade/respostas.csv")
SAIDA = Path("docs/resultados/usabilidade.md")
TAREFAS = ("t1", "t2", "t3", "t4", "t5")
REFERENCIA_SUS = 68.0


def sus(respostas: list[int]) -> float:
    """Pontuacao SUS (0-100) de UM participante, itens 1..10 em escala 1..5.

    Itens impares sao positivos (contribuem r - 1), pares negativos (5 - r);
    a soma (0-40) vezes 2,5.
    """
    if len(respostas) != 10 or any(not 1 <= r <= 5 for r in respostas):
        raise ValueError(f"SUS precisa de 10 respostas entre 1 e 5: {respostas}")
    return 2.5 * sum(r - 1 if i % 2 == 0 else 5 - r for i, r in enumerate(respostas))


def _num(x: float, casas: int = 1) -> str:
    return f"{x:.{casas}f}".replace(".", ",")


def _pct(parte: int, total: int) -> str:
    return f"{parte}/{total} ({_num(100 * parte / total, 0)}%)" if total else "—"


def tabular(linhas: list[dict[str, str]]) -> str:
    n = len(linhas)
    notas = [sus([int(l[f"sus{i}"]) for i in range(1, 11)]) for l in linhas]
    media = statistics.mean(notas)
    dp = statistics.stdev(notas) if n > 1 else 0.0

    out = [
        "# Teste de usabilidade — resultado",
        "",
        f"> Gerado por `python -m scripts.sus` a partir de `{ENTRADA.as_posix()}`. Protocolo em `docs/usabilidade/protocolo.md`.",
        "",
        f"## Amostra (n = {n})",
        "",
        "| Faixa etária | n |",
        "|---|---|",
    ]
    for faixa in sorted({l["faixa_etaria"] for l in linhas}):
        out.append(f"| {faixa} | {sum(l['faixa_etaria'] == faixa for l in linhas)} |")
    out += [
        "",
        "## SUS",
        "",
        "| | valor |",
        "|---|---|",
        f"| média ± desvio padrão | **{_num(media)} ± {_num(dp)}** |",
        f"| mediana (mín.–máx.) | {_num(statistics.median(notas))} ({_num(min(notas))}–{_num(max(notas))}) |",
        f"| participantes com SUS ≥ {_num(REFERENCIA_SUS, 0)} (referência usual) | {_pct(sum(s >= REFERENCIA_SUS for s in notas), n)} |",
        "",
        "## Tarefas",
        "",
        "| Tarefa | sucesso | tempo mediano (s) |",
        "|---|---|---|",
    ]
    for t in TAREFAS:
        ok = sum(l[t] == "1" for l in linhas)
        tempos = [float(l[f"{t}_s"]) for l in linhas if l[f"{t}_s"]]
        out.append(f"| {t.upper()} | {_pct(ok, n)} | {_num(statistics.median(tempos), 0) if tempos else '—'} |")

    def likert(col: str) -> str:
        v = [int(l[col]) for l in linhas]
        return f"{_num(statistics.mean(v))} (4 ou 5: {_pct(sum(x >= 4 for x in v), n)})"

    sim = lambda col: sum(l[col] == "sim" for l in linhas)  # noqa: E731
    viu = [l for l in linhas if l["t5_trocou"] != "nao_viu"]
    out += [
        "",
        "## Compreensão (1 a 5)",
        "",
        "| Afirmação | média |",
        "|---|---|",
        f"| Entendi o que o selo \"Entrega local\" quer dizer | {likert('entendi_selo')} |",
        f"| Confio no número de CO₂ mostrado | {likert('confio_co2')} |",
        "",
        "## Preferência declarada × revelada",
        "",
        "| Cenário | trocaria |",
        "|---|---|",
        f"| mesmo preço (declarado) | {_pct(sim('troca_mesmo_preco'), n)} |",
        f"| 5% mais caro (declarado) | {_pct(sim('troca_5pct'), n)} |",
        f"| 10% mais caro (declarado) | {_pct(sim('troca_10pct'), n)} |",
        f"| **T5: R$ 10 a mais (~17%), 91% menos CO₂ (revelado)** | **{_pct(sum(l['t5_trocou'] == 'sim' for l in viu), len(viu))}** dos que viram a sugestão |",
        f"| não encontrou a sugestão na T5 | {_pct(n - len(viu), n)} |",
        "",
        "## Comentários",
        "",
    ]
    out += [f"- {l['participante']}: {l['comentario']}" for l in linhas if l["comentario"].strip()]
    return "\n".join(out) + "\n"


def main() -> None:
    with ENTRADA.open(encoding="utf-8") as f:
        linhas = [l for l in csv.DictReader(f) if l["participante"].strip()]
    if not linhas:
        raise SystemExit(f"{ENTRADA} sem respostas ainda")
    SAIDA.write_text(tabular(linhas), encoding="utf-8")
    print(SAIDA)


if __name__ == "__main__":
    main()
