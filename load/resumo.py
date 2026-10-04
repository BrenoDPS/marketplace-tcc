"""Consolida os ensaios de `load/protocolo.py`: media e desvio padrao (§3.3).

Uma linha por cenario x condicao, cada metrica como "media ± dp" das
repeticoes. Com n = 3 o desvio padrao e fragil; os valores de cada repeticao
continuam nos CSVs para quem quiser conferir.

    python -m load.resumo load/results/protocolo
    python -m load.resumo load/results/protocolo --rota "GET /home (conscious_buyer)"

Falhas saem segregadas por codigo HTTP; "conexao" e erro sem resposta (socket
recusado/derrubado, o que a §3.3 chama de esgotamento de descritores).
"""

from __future__ import annotations

import argparse
import csv
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

NOME = re.compile(r"r(\d+)-u(\d+)-(off|frio|aquecido)_stats\.csv$")
CODIGO = re.compile(r"\b([1-5]\d\d) (?:Server|Client) Error")
ORDEM = {"off": 0, "frio": 1, "aquecido": 2}
COLUNAS = ["p50", "p95", "p99", "rps", "falhas_pct", "acerto_pct", "cpu_api_media", "cpu_api_max"]


def ler_ensaio(stats: Path, rota: str) -> tuple[dict[str, float], Counter, int]:
    base = str(stats)[: -len("_stats.csv")]
    with stats.open(encoding="utf-8") as f:
        linha = next(r for r in csv.DictReader(f) if r["Name"] == rota)
    n = int(linha["Request Count"])
    m = {
        "p50": float(linha["50%"]),
        "p95": float(linha["95%"]),
        "p99": float(linha["99%"]),
        "rps": float(linha["Requests/s"]),
        "falhas_pct": 100 * int(linha["Failure Count"]) / n if n else 0.0,
    }

    codigos: Counter = Counter()
    falhas = Path(base + "_failures.csv")
    if falhas.exists():
        # O Locust grava este CSV no encoding do sistema (cp1252 no Windows), e
        # as mensagens de erro de socket vem traduzidas ("conexao" com cedilha).
        with falhas.open(encoding="utf-8", errors="replace") as f:
            for r in csv.DictReader(f):
                if rota == "Aggregated" or r["Name"] == rota:
                    achado = CODIGO.search(r["Error"])
                    codigos[achado.group(1) if achado else "conexao"] += int(r["Occurrences"])

    redis = Path(base + "_redis.txt")
    if redis.exists():
        kv = dict(l.split(":", 1) for l in redis.read_text(encoding="utf-8").split() if ":" in l)
        hits, misses = int(kv.get("keyspace_hits", 0)), int(kv.get("keyspace_misses", 0))
        if hits + misses:
            m["acerto_pct"] = 100 * hits / (hits + misses)

    cpu = Path(base + "_cpu.csv")
    if cpu.exists():
        with cpu.open(encoding="utf-8") as f:
            valores = [float(r["api_cpu_pct_de_um_nucleo"]) for r in csv.DictReader(f)]
        if valores:
            m["cpu_api_media"] = statistics.fmean(valores)
            m["cpu_api_max"] = max(valores)
    return m, codigos, n


def _fmt(valores: list[float]) -> str:
    if not valores:
        return "—"
    media = statistics.fmean(valores)
    dp = statistics.stdev(valores) if len(valores) > 1 else 0.0
    casas = 0 if media >= 100 else 1
    return f"{media:.{casas}f} ± {dp:.{casas}f}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("pasta", type=Path)
    ap.add_argument("--rota", default="Aggregated", help='linha do Locust, ex.: "GET /products/{id}"')
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # "±" no console do Windows (cp1252)

    celulas: dict[tuple[int, str], list[dict[str, float]]] = defaultdict(list)
    codigos: dict[tuple[int, str], Counter] = defaultdict(Counter)
    total: Counter = Counter()
    for stats in sorted(args.pasta.glob("*_stats.csv")):
        casa = NOME.search(stats.name)
        if not casa:
            continue
        chave = (int(casa.group(2)), casa.group(3))
        m, c, n = ler_ensaio(stats, args.rota)
        celulas[chave].append(m)
        codigos[chave] += c
        total[chave] += n

    print(f"Rota: {args.rota}. Latencias em ms; CPU da API em % de um nucleo.\n")
    print("| VU | cache | n | " + " | ".join(COLUNAS) + " | falhas por codigo |")
    print("|---" * (len(COLUNAS) + 4) + "|")
    for chave in sorted(celulas, key=lambda k: (k[0], ORDEM[k[1]])):
        ms = celulas[chave]
        cols = [_fmt([m[c] for m in ms if c in m]) for c in COLUNAS]
        por_codigo = ", ".join(
            f"{cod}: {100 * q / total[chave]:.2f}%" for cod, q in sorted(codigos[chave].items())
        ) or "—"
        print(f"| {chave[0]} | {chave[1]} | {len(ms)} | " + " | ".join(cols) + f" | {por_codigo} |")


if __name__ == "__main__":
    main()
