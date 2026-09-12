"""Acesso a `cep_centroids` — a tabela inteira vive em memoria.

São 6403 linhas, 520 kB no Postgres e ~1,1 MB como `dict`. É dado de referência
**estático**: o ETL escreve uma vez, e nada em runtime altera. Manter a tabela
no processo troca uma ida ao banco por uma busca em `dict`, e serve as duas
perguntas que o resto do sistema faz — "onde fica este prefixo?" e "quais
prefixos existem?".

Antes disto, montar a Home do `conscious_buyer` custava 27 idas ao banco, e o
`list_known_prefixes` sozinho — `SELECT` dos 6403 prefixos para validar **um** —
era ~48% de uma Home `default`. Ver `docs/performance.md`.
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import CepCentroid

# ponytail: snapshot de processo, sem invalidacao. O ETL faz `drop_all` e
# recria a tabela, entao rodar `scripts.etl_load_sample` com a API no ar deixa
# este cache servindo centroides de uma tabela que nao existe mais — o sintoma e
# selo errado, nao erro. Hoje o conserto e reiniciar a API. Se recarregar o ETL
# em runtime virar rotina, chamar `reset_centroid_cache()` no fim do script ou
# expor uma rota administrativa que faca isso.
_centroids: dict[str, tuple[float, float]] | None = None
# So protege a PRIMEIRA carga: sem ele, N requisicoes concorrentes num processo
# frio disparariam N vezes o mesmo SELECT de 6403 linhas.
_loading = asyncio.Lock()


async def _load(session: AsyncSession) -> dict[str, tuple[float, float]]:
    """Carrega a tabela na primeira consulta e devolve sempre o mesmo `dict`.

    Preguicoso e nao no startup de proposito: assim a API sobe sem depender do
    Postgres estar de pe, que e como ela se comporta hoje. O custo da carga
    (~15 ms) e pago uma vez, pela primeira requisicao.
    """
    global _centroids
    # Caminho quente primeiro: depois da carga, nem toca no lock.
    if _centroids is not None:
        return _centroids

    async with _loading:
        # Outra corrotina pode ter carregado enquanto esta esperava o lock.
        if _centroids is None:
            stmt = select(CepCentroid.zip_prefix, CepCentroid.lat, CepCentroid.lng)
            rows = (await session.execute(stmt)).all()
            _centroids = {
                row.zip_prefix: (float(row.lat), float(row.lng)) for row in rows
            }
    return _centroids


def reset_centroid_cache() -> None:
    """Esquece o snapshot; a proxima consulta recarrega do banco.

    Existe para os testes e para quem recarregar o ETL com a API no ar.
    """
    global _centroids
    _centroids = None


async def get_centroid(
    session: AsyncSession, zip_prefix: str
) -> tuple[float, float] | None:
    """Centroide de um prefixo de CEP; `None` se ele nao esta na amostra."""
    return (await _load(session)).get(zip_prefix)


async def list_known_prefixes(session: AsyncSession) -> set[str]:
    """Prefixos com centroide conhecido. Usado pelos routers para validar o CEP."""
    return set(await _load(session))
