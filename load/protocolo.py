"""Protocolo de carga da §3.3: condicoes de cache x cargas x repeticoes.

Existe para os 27 ensaios rodarem sem ninguem na maquina e sem repetir os
defeitos de validade que este projeto ja pagou:

- `DEBUG=false` sempre: o `echo` do SQLAlchemy estava em TODAS as medicoes ate
  a §9 de `docs/performance.md`, porque o padrao de `DEBUG` e `True`.
- TTL maior que o protocolo: com o padrao de 60 s, "aquecido" vira "frio" um
  minuto depois de comecar, e "frio" vira estado estacionario.
- `LOAD_SEED` igual nas tres condicoes de uma carga: comparacao pareada, e o
  aquecido encontra as chaves que o frio deixou (ver o docstring do locustfile).
- `--reset-stats`: o CSV e so o plateau; a rampa nao entra na conta.
- API reiniciada a cada ensaio: nenhuma condicao herda processo aquecido de
  outra. O Redis NAO e reiniciado — so o FLUSHALL antes do frio o esvazia.

Ordem: por repeticao, as cargas em ordem sorteada (semente = repeticao); em cada
carga, off -> frio -> aquecido. Intercalar evita que deriva da maquina ao longo
de horas vire diferenca entre condicoes.

    # piloto: a carga mais alta, sem cache, 2 min — o Locust satura a CPU?
    python -m load.protocolo --cargas 1000 --condicoes off --reps 1 --plateau 120 --saida load/results/piloto
    # protocolo completo
    python -m load.protocolo

Requer Postgres e Redis no ar (`docker compose up -d`) com o ETL carregado, e a
porta 8000 livre. Sobe e derruba a propria API.
"""

from __future__ import annotations

import argparse
import os
import random
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

API = "http://127.0.0.1:8000"
LOCUSTFILE = Path(__file__).with_name("locustfile.py")
ORDEM = ("off", "frio", "aquecido")
RAMPA_S = 10


def _api_responde() -> bool:
    try:
        urllib.request.urlopen(API + "/openapi.json", timeout=1)
        return True
    except OSError:
        return False


def _redis(*args: str) -> str:
    return subprocess.run(
        ["docker", "exec", "olist-redis", "redis-cli", *args], check=True, capture_output=True, text=True
    ).stdout


def subir_api(cache: bool, ttl: int) -> subprocess.Popen:
    env = {
        **os.environ,
        "DEBUG": "false",
        "CACHE_ENABLED": "true" if cache else "false",
        "CACHE_TTL_SECONDS": str(ttl),
    }
    # Sem --reload: o file-watcher entraria na medicao.
    api = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.main:app", "--port", "8000", "--log-level", "warning"],
        env=env,
    )
    for _ in range(60):
        if api.poll() is not None:
            raise RuntimeError("a API morreu ao subir — Redis/Postgres no ar?")
        if _api_responde():
            return api
        time.sleep(1)
    api.kill()
    raise RuntimeError("a API nao respondeu em 60 s")


def ensaio(saida: Path, nome: str, usuarios: int, plateau: int, semente: str) -> bool:
    """Roda um ensaio; devolve False se o gerador de carga saturou."""
    log = saida / f"{nome}.log"
    cmd = [
        sys.executable, "-m", "locust", "-f", str(LOCUSTFILE), "--headless",
        "-u", str(usuarios), "-r", str(max(1, usuarios // RAMPA_S)),
        "-t", f"{RAMPA_S + plateau}s", "--reset-stats", "--only-summary",
        "--csv", str(saida / nome), "--host", API,
    ]
    with log.open("w", encoding="utf-8") as f:
        # Locust sai com 1 quando ha falha de requisicao: e dado, nao erro do runner.
        subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, env={**os.environ, "LOAD_SEED": semente})
    return "CPU usage above" not in log.read_text(encoding="utf-8", errors="replace")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cargas", type=int, nargs="+", default=[50, 250, 1000])
    ap.add_argument("--condicoes", nargs="+", choices=ORDEM, default=list(ORDEM))
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--plateau", type=int, default=600, help="segundos medidos por ensaio")
    ap.add_argument("--ttl", type=int, default=3600, help="CACHE_TTL_SECONDS durante o protocolo")
    ap.add_argument("--saida", type=Path, default=Path("load/results/protocolo"))
    args = ap.parse_args()

    condicoes = [c for c in ORDEM if c in args.condicoes]
    if "aquecido" in condicoes and "frio" not in condicoes:
        ap.error("'aquecido' so existe logo depois de um 'frio' na mesma carga")
    if _api_responde():
        sys.exit(f"ja ha algo respondendo em {API} — derrube antes de medir")
    args.saida.mkdir(parents=True, exist_ok=True)

    total = len(args.cargas) * len(condicoes) * args.reps
    n = 0
    for rep in range(1, args.reps + 1):
        cargas = list(args.cargas)
        random.Random(rep).shuffle(cargas)
        for usuarios in cargas:
            for cond in condicoes:
                n += 1
                nome = f"r{rep}-u{usuarios}-{cond}"
                print(f"[{n}/{total}] {nome} {time.strftime('%H:%M:%S')}", flush=True)
                if cond == "frio":
                    _redis("FLUSHALL")
                _redis("CONFIG", "RESETSTAT")
                api = subir_api(cache=cond != "off", ttl=args.ttl)
                try:
                    if not ensaio(args.saida, nome, usuarios, args.plateau, f"{rep}-{usuarios}"):
                        print(f"  AVISO: o Locust saturou a CPU em {nome} — ensaio invalido", flush=True)
                finally:
                    api.terminate()
                    api.wait()
                # Taxa de acerto: keyspace_hits / (hits + misses). Inclui a rampa.
                stats = _redis("INFO", "stats").splitlines()
                (args.saida / f"{nome}_redis.txt").write_text(
                    "\n".join(l for l in stats if l.startswith("keyspace_")) + "\n", encoding="utf-8"
                )


if __name__ == "__main__":
    main()
