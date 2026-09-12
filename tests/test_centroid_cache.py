"""O memo de centroides em `get_centroid`.

Nao depende de Postgres: uma sessao falsa conta quantas vezes o banco foi
consultado, que e exatamente a propriedade em teste. Sem esta contagem o memo
"funciona" mesmo quebrado — os valores voltam certos de qualquer jeito, so que
pagando a ida ao banco de novo.
"""

from __future__ import annotations

import pytest

from src.features.green_logistics.repository import get_centroid


class _Row:
    def __init__(self, lat: float, lng: float) -> None:
        self.lat, self.lng = lat, lng


class _Result:
    def __init__(self, row: _Row | None) -> None:
        self._row = row

    def first(self) -> _Row | None:
        return self._row


class FakeSession:
    """Sessao minima: um `info` (como a real) e um contador de consultas."""

    def __init__(self, centroids: dict[str, tuple[float, float]]) -> None:
        self.info: dict[str, object] = {}
        self.centroids = centroids
        self.queries: list[str] = []

    async def execute(self, stmt):  # noqa: ANN001 - so precisa do parametro
        # O prefixo procurado e o unico bind da clausula WHERE.
        prefix = next(iter(stmt.compile().params.values()))
        self.queries.append(prefix)
        found = self.centroids.get(prefix)
        return _Result(None if found is None else _Row(*found))


@pytest.mark.asyncio
async def test_mesmo_prefixo_consulta_o_banco_uma_vez():
    session = FakeSession({"01000": (-23.5, -46.6)})

    primeiro = await get_centroid(session, "01000")
    segundo = await get_centroid(session, "01000")

    assert primeiro == segundo == (-23.5, -46.6)
    assert session.queries == ["01000"], "o segundo acesso deveria vir do memo"


@pytest.mark.asyncio
async def test_prefixo_desconhecido_tambem_e_memoizado():
    """O caso que `.get()` no lugar de `in` deixaria passar.

    `None` e uma resposta valida — cliente fora da amostra. Se ela nao fosse
    memoizada, o CEP desconhecido voltaria ao banco a cada consulta, que e
    justamente o caminho mais quente quando nenhum selo e calculavel.
    """
    session = FakeSession({})

    assert await get_centroid(session, "99999") is None
    assert await get_centroid(session, "99999") is None

    assert session.queries == ["99999"]


@pytest.mark.asyncio
async def test_prefixos_diferentes_nao_se_confundem():
    session = FakeSession({"01000": (-23.5, -46.6), "60000": (-3.7, -38.5)})

    assert await get_centroid(session, "01000") == (-23.5, -46.6)
    assert await get_centroid(session, "60000") == (-3.7, -38.5)
    assert await get_centroid(session, "01000") == (-23.5, -46.6)

    assert session.queries == ["01000", "60000"]


@pytest.mark.asyncio
async def test_memo_nao_vaza_entre_sessoes():
    """O memo tem que morrer com a requisicao.

    `get_db` abre uma sessao por request; se o cache sobrevivesse a ela viraria
    estado global, e uma recarga do ETL passaria a servir centroides velhos.
    """
    centroids = {"01000": (-23.5, -46.6)}
    primeira = FakeSession(centroids)
    segunda = FakeSession(centroids)

    await get_centroid(primeira, "01000")
    await get_centroid(segunda, "01000")

    assert primeira.queries == ["01000"]
    assert segunda.queries == ["01000"], "cada sessao consulta por conta propria"
