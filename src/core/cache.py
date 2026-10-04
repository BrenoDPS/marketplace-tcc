"""Cache de resposta SDUI — ligado por padrao desde a Sprint 8.

Comecou como VARIAVEL DE EXPERIMENTO e virou decisao medida: o protocolo da
§3.3 (27 ensaios, `docs/performance.md` §11) mostrou que ele e dispensavel em
carga nominal e e o que cumpre a meta de 200 ms a partir de 250 usuarios com 1
worker. O historico abaixo continua valido para quem for remedir.

`docs/performance.md` §7 concluiu que Redis nao era necessario **sem nunca ter
rodado Redis**: a conclusao veio por inferencia sobre o gargalo medido (N+1 de
centroides, depois o processo unico). Inferencia e argumento, nao medicao, e a
secao 3.3 da metodologia promete tres condicoes de cache. Este modulo existe
para que a decisao vire resultado.

O QUE E CACHEADO: o JSON ja serializado da tela. Numa batida devolvemos os bytes
direto, sem reconstruir o `ScreenResponse` — revalidar o modelo so para
re-serializa-lo cobraria do Redis um custo que um cache real nao tem, e
enviesaria o experimento contra ele.

FRIO x AQUECIDO NAO SAO MODOS DE CODIGO. Sao procedimento de ensaio:

    desabilitado  CACHE_ENABLED=false
    frio          CACHE_ENABLED=true  + FLUSHALL antes do run
    aquecido      CACHE_ENABLED=true  + o run anterior deixou as chaves

    docker exec olist-redis redis-cli FLUSHALL

Escrever tres modos no codigo seria inventar complexidade para um estado que o
`redis-cli` ja expressa em uma linha.

SEM FAIL-OPEN de proposito. Se o Redis cair no meio de um ensaio, a excecao sobe
e vira falha visivel no relatorio do Locust. Um cache que degrada em silencio
produziria um numero que parece valido e nao e — o mesmo defeito que o
`locustfile` tinha com dois CEPs fixos.
"""

from __future__ import annotations

from redis.asyncio import BlockingConnectionPool, Redis

from src.core.config import settings

_client: Redis | None = None

# Pool BLOQUEANTE: esgotadas as conexoes, a requisicao espera ate 5 s por uma
# livre em vez de falhar na hora. O pool padrao do redis-py 8 (100 conexoes,
# sem fila) virou HTTP 500 a 1.000 usuarios no protocolo (§11.3). Passado o
# tempo, a excecao sobe — continua sem fail-open.
_MAX_CONEXOES = 100
_ESPERA_POR_CONEXAO_S = 5


def get_client() -> Redis | None:
    """Cliente unico do processo, ou `None` com o cache desligado."""
    global _client
    if not settings.CACHE_ENABLED:
        return None
    if _client is None:
        pool = BlockingConnectionPool.from_url(
            settings.REDIS_URL, max_connections=_MAX_CONEXOES, timeout=_ESPERA_POR_CONEXAO_S
        )
        _client = Redis(connection_pool=pool)
    return _client


async def close() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def key(screen_id: str, *partes: str | None) -> str:
    """Chave da tela: o contrato JSON depende so destes parametros.

    `None` vira string vazia e o separador e `|`, que nao ocorre em CEP,
    contexto, termo de busca normalizado nem slug de categoria — sem isso,
    ("a", None) e (None, "a") colidiriam.
    """
    return "sdui:" + screen_id + "|" + "|".join(p or "" for p in partes)


async def get(chave: str) -> bytes | None:
    client = get_client()
    if client is None:
        return None
    return await client.get(chave)


async def set(chave: str, valor: str | bytes) -> None:
    client = get_client()
    if client is None:
        return
    await client.set(chave, valor, ex=settings.CACHE_TTL_SECONDS)
