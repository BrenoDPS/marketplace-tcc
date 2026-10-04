"""Protocolo de carga da §3.3: condicoes de cache x cenarios x repeticoes.

Existe para os 27 ensaios rodarem sem ninguem na maquina e sem repetir os
defeitos de validade que este projeto ja pagou (`docs/performance.md` §10):

- `DEBUG=false` sempre: o `echo` do SQLAlchemy estava em TODAS as medicoes ate
  a §9, porque o padrao de `DEBUG` e `True`.
- TTL maior que o protocolo: com o padrao de 60 s, "aquecido" vira "frio" um
  minuto depois de comecar, e "frio" vira estado estacionario.
- `LOAD_SEED` igual nas tres condicoes de um cenario: comparacao pareada, e o
  aquecido encontra as chaves que o frio deixou — o frio E o pre-aquecimento
  ("ciclo previo de requisicoes de carga", §3.3).
- `--reset-stats`: o `_stats.csv` e so o plateau. A rampa fica no
  `_stats_history.csv` — e nela que aparece a rajada de cache misses do frio.
- API reiniciada a cada ensaio: nenhuma condicao herda processo de outra. O
  Redis NAO e reiniciado — so o FLUSHALL antes do frio o esvazia.

Por ensaio grava, alem dos CSVs do Locust: `_cpu.csv` (CPU do processo da API e
do sistema, 1 amostra/s — "ponto de esgotamento da CPU"), `_redis.txt` (taxa de
acerto) e `.log`. Por execucao, `meta.json`: commit, imagens Docker, volume de
dados no Postgres e hash do locustfile (catalogo de metadados da §3.3).

Ordem: por repeticao, os cenarios em ordem sorteada (semente = repeticao); em
cada cenario, off -> frio -> aquecido. Intercalar evita que deriva da maquina ao
longo de horas vire diferenca entre condicoes.

    python -m load.protocolo                       # os 27 ensaios (~4 h 45 min)
    python -m load.protocolo --cargas 1000 --condicoes off --reps 1 --plateau 120 --saida load/results/piloto
    python -m load.resumo load/results/protocolo   # media e desvio padrao
    # reexecutar UM ensaio invalido (mesmo nome e semente), em pasta propria
    python -m load.protocolo --cargas 1000 --condicoes frio --rep 3 --saida load/results/protocolo-reexecucao

Requer Postgres e Redis no ar (`docker compose up -d`) com o ETL carregado, a
porta 8000 livre e a arvore sem mudanca nao commitada (o hash tem de descrever
o codigo medido). Sobe e derruba a propria API.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import random
import subprocess
import sys
import threading
import time
import urllib.request
from importlib.metadata import version
from pathlib import Path

import psutil
from sqlalchemy import create_engine, inspect, text

from scripts.etl_load_sample import _sync_database_url

API = "http://127.0.0.1:8000"
LOCUSTFILE = Path(__file__).with_name("locustfile.py")
ORDEM = ("off", "frio", "aquecido")
# §3.3, Tabela 1 — VU: (spawn rate em VU/s, plateau em s). Rampa = VU / spawn.
CENARIOS = {50: (5, 300), 250: (10, 600), 1000: (25, 900)}


def _sh(*cmd: str) -> str:
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip()


def _redis(*args: str) -> str:
    return _sh("docker", "exec", "olist-redis", "redis-cli", *args)


def _api_responde() -> bool:
    try:
        urllib.request.urlopen(API + "/openapi.json", timeout=1)
        return True
    except OSError:
        return False


def metadados(args: argparse.Namespace) -> dict:
    engine = create_engine(_sync_database_url())
    with engine.connect() as conn:
        linhas = {
            t: conn.execute(text(f'SELECT count(*) FROM "{t}"')).scalar_one()
            for t in sorted(inspect(conn).get_table_names())
        }
        postgres = conn.execute(text("SELECT version()")).scalar_one()
    engine.dispose()
    redis_info = dict(l.split(":", 1) for l in _redis("INFO", "server").splitlines() if ":" in l)
    return {
        "commit": _sh("git", "rev-parse", "HEAD"),
        "imagens_docker": _sh(
            "docker", "inspect", "--format", "{{.Name}} {{.Config.Image}} {{.Image}}",
            "olist-postgres", "olist-redis",
        ).splitlines(),
        "postgres": postgres,
        "redis": redis_info.get("redis_version", "?").strip(),
        "linhas_por_tabela": linhas,
        "locustfile_sha256": hashlib.sha256(LOCUSTFILE.read_bytes()).hexdigest(),
        "python": sys.version.split()[0],
        "locust": version("locust"),
        "maquina": {
            "plataforma": platform.platform(),
            "nucleos_logicos": os.cpu_count(),
            "memoria_gb": round(psutil.virtual_memory().total / 2**30, 1),
        },
        "parametros": {
            "cenarios": {u: {"spawn_rate": CENARIOS[u][0], "plateau_s": args.plateau or CENARIOS[u][1]}
                         for u in args.cargas},
            "condicoes": args.condicoes,
            "reps": args.reps,
            "cache_ttl_s": args.ttl,
            "workers_api": 1,
        },
        "inicio": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "ensaios": [],
    }


def subir_api(cache: bool, ttl: int) -> subprocess.Popen:
    if _api_responde():
        raise RuntimeError(f"ja ha algo respondendo em {API} — o ensaio mediria o processo errado")
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


def _amostrar_cpu(pid: int, destino: Path, parar: threading.Event) -> None:
    """CPU do processo da API, em % de UM nucleo — o event loop satura em ~100%.

    No Windows o `python.exe` do venv e um lancador; o interpretador que serve a
    API e filho dele. Por isso soma a arvore, nao o PID do Popen.
    """
    raiz = psutil.Process(pid)
    procs = [raiz, *raiz.children(recursive=True)]
    for p in procs:
        p.cpu_percent(None)
    psutil.cpu_percent(None)
    t0 = time.monotonic()
    with destino.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["t_s", "api_cpu_pct_de_um_nucleo", "sistema_cpu_pct"])
        while not parar.wait(1):
            try:
                api = sum(p.cpu_percent(None) for p in procs)
            except psutil.NoSuchProcess:
                return
            w.writerow([round(time.monotonic() - t0), round(api, 1), psutil.cpu_percent(None)])


def ensaio(saida: Path, nome: str, usuarios: int, spawn: int, plateau: int, semente: str, api_pid: int) -> bool:
    """Roda um ensaio; devolve False se o gerador de carga saturou."""
    log = saida / f"{nome}.log"
    rampa = -(-usuarios // spawn)
    cmd = [
        sys.executable, "-m", "locust", "-f", str(LOCUSTFILE), "--headless",
        "-u", str(usuarios), "-r", str(spawn), "-t", f"{rampa + plateau}s",
        "--reset-stats", "--only-summary", "--csv", str(saida / nome), "--host", API,
    ]
    parar = threading.Event()
    cpu = threading.Thread(target=_amostrar_cpu, args=(api_pid, saida / f"{nome}_cpu.csv", parar))
    cpu.start()
    try:
        with log.open("w", encoding="utf-8") as f:
            # Locust sai com 1 quando ha falha de requisicao: e dado, nao erro do runner.
            subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, env={**os.environ, "LOAD_SEED": semente})
    finally:
        parar.set()
        cpu.join()
    return "CPU usage above" not in log.read_text(encoding="utf-8", errors="replace")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cargas", type=int, nargs="+", choices=sorted(CENARIOS), default=sorted(CENARIOS))
    ap.add_argument("--condicoes", nargs="+", choices=ORDEM, default=list(ORDEM))
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--rep", type=int, nargs="+",
                    help="repeticoes especificas (ex.: --rep 3 para reexecutar um ensaio invalido com a mesma semente)")
    ap.add_argument("--plateau", type=int, help="sobrescreve o plateau da Tabela 1 (so para piloto/smoke)")
    ap.add_argument("--ttl", type=int, default=3600, help="CACHE_TTL_SECONDS durante o protocolo")
    ap.add_argument("--saida", type=Path, default=Path("load/results/protocolo"))
    ap.add_argument("--permitir-sujo", action="store_true", help="medir com mudanca nao commitada (nao auditavel)")
    args = ap.parse_args()

    condicoes = [c for c in ORDEM if c in args.condicoes]
    if "aquecido" in condicoes and "frio" not in condicoes:
        ap.error("'aquecido' so existe logo depois de um 'frio' no mesmo cenario")
    if _sh("git", "status", "--porcelain", "--untracked-files=no") and not args.permitir_sujo:
        sys.exit("ha mudanca nao commitada: o hash do commit nao descreveria o codigo medido")
    args.saida.mkdir(parents=True, exist_ok=True)
    meta = metadados(args)
    meta["parametros"]["condicoes"] = condicoes

    plano = [
        (rep, u, cond)
        for rep in (args.rep or range(1, args.reps + 1))
        for u in random.Random(rep).sample(args.cargas, len(args.cargas))
        for cond in condicoes
    ]
    estimado = sum(-(-u // CENARIOS[u][0]) + (args.plateau or CENARIOS[u][1]) + 10 for _, u, _ in plano)
    print(f"{len(plano)} ensaios, ~{estimado // 60} min", flush=True)

    for n, (rep, usuarios, cond) in enumerate(plano, 1):
        spawn, plateau = CENARIOS[usuarios][0], args.plateau or CENARIOS[usuarios][1]
        nome = f"r{rep}-u{usuarios}-{cond}"
        inicio = time.strftime("%Y-%m-%dT%H:%M:%S")
        print(f"[{n}/{len(plano)}] {nome} {inicio}", flush=True)
        if cond == "frio":
            _redis("FLUSHALL")
        _redis("CONFIG", "RESETSTAT")
        api = subir_api(cache=cond != "off", ttl=args.ttl)
        try:
            ok = ensaio(args.saida, nome, usuarios, spawn, plateau, f"{rep}-{usuarios}", api.pid)
        finally:
            api.terminate()
            api.wait()
        if not ok:
            print(f"  AVISO: o Locust saturou a CPU em {nome} — ensaio invalido", flush=True)
        # Taxa de acerto: keyspace_hits / (hits + misses). Inclui a rampa.
        stats = [l for l in _redis("INFO", "stats").splitlines() if l.startswith("keyspace_")]
        (args.saida / f"{nome}_redis.txt").write_text("\n".join(stats) + "\n", encoding="utf-8")
        meta["ensaios"].append({"nome": nome, "inicio": inicio, "gerador_saturou": not ok})
        meta["fim"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        (args.saida / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
