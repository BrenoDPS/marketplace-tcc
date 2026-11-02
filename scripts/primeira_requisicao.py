"""Custo da primeira requisicao depois de subir a API (carga dos centroides em memoria).

Os centroides de CEP (12.933 linhas) sao carregados na primeira requisicao que precisa
deles (`green_logistics/repository.py`); as seguintes consultam um dicionario. Aqui se
mede quanto custa esse primeiro acesso, numa API propria na porta 8001 (nao atrapalha a
da 8000) e sem o cache do Redis, numa tela que nao e guardada em cache (detalhe).

    python -m scripts.primeira_requisicao   # grava docs/resultados/primeira-requisicao.md (~1 min)

Requer Postgres e Redis no ar com o ETL carregado.
"""

from __future__ import annotations

import os
import statistics as st
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

PORTA = 8001
URL = f"http://127.0.0.1:{PORTA}/api/v1/products/89321f94e35fc6d7903d36f74e351d40?customer_zip_prefix=05311"
RODADAS, SEGUINTES = 5, 20
SAIDA = Path("docs/resultados/primeira-requisicao.md")


def br(x: float, casas: int = 1) -> str:
    return f"{x:.{casas}f}".replace(".", ",")


def rodada() -> tuple[float, float]:
    api = subprocess.Popen([sys.executable, "-m", "uvicorn", "src.main:app", "--port", str(PORTA), "--log-level", "warning"],
                           env={**os.environ, "SQL_ECHO": "false", "CACHE_ENABLED": "false"},
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(150):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{PORTA}/docs", timeout=1).read()
                break
            except OSError:
                time.sleep(0.2)
        tempos = []
        for _ in range(SEGUINTES + 1):
            t = time.perf_counter()
            urllib.request.urlopen(URL).read()
            tempos.append((time.perf_counter() - t) * 1000)
        return tempos[0], st.median(tempos[1:])
    finally:
        api.terminate()
        api.wait()


def main() -> None:
    res = [rodada() for _ in range(RODADAS)]
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    linhas = "\n".join(f"| {i} | {br(p, 0)} | {br(s)} |" for i, (p, s) in enumerate(res, 1))
    primeiras = [p for p, _ in res]
    SAIDA.write_text(
        f"""# Primeira requisição depois de subir a API

> Gerado por `python -m scripts.primeira_requisicao` no commit `{commit}`. Detalhe de produto
> (sem cache de resposta), API recém-iniciada na porta {PORTA}, {RODADAS} rodadas.

| rodada | primeira requisição (ms) | seguintes: mediana de {SEGUINTES} (ms) |
|---|---|---|
{linhas}

**Primeira requisição: mediana {br(st.median(primeiras), 0)} ms (de {br(min(primeiras), 0)} a {br(max(primeiras), 0)} ms);
seguintes: mediana {br(st.median(s for _, s in res))} ms.** A diferença é a carga dos
centroides em memória e o aquecimento do processo. Na demonstração, uma requisição de
aquecimento antes do primeiro clique evita a espera (`docs/roteiro-banca.md`, preparação).
""",
        encoding="utf-8")
    print(SAIDA.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
