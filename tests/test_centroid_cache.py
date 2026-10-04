"""O snapshot de `cep_centroids` em memoria.

Nao depende de Postgres: uma sessao falsa conta quantas vezes o banco foi
consultado, que e exatamente a propriedade em teste. Sem essa contagem o cache
"funciona" mesmo quebrado — os valores voltam certos de qualquer jeito, so que
pagando a ida ao banco de novo.
"""

from __future__ import annotations

import asyncio
from collections.abc import KeysView

import pytest

from src.features.green_logistics import repository
from src.features.green_logistics.repository import (
    get_centroid,
    get_uf,
    list_known_prefixes,
    reset_centroid_cache,
)

CENTROIDS = {"01000": (-23.5, -46.6), "60000": (-3.7, -38.5)}
UFS = {"01000": "SP", "60000": "CE"}


class _Row:
    def __init__(self, zip_prefix: str, lat: float, lng: float) -> None:
        self.zip_prefix, self.lat, self.lng = zip_prefix, lat, lng
        self.uf = UFS.get(zip_prefix)


class _Result:
    def __init__(self, rows: list[_Row]) -> None:
        self._rows = rows

    def all(self) -> list[_Row]:
        return self._rows


class FakeSession:
    """Sessao minima que conta quantos SELECT da tabela inteira aconteceram."""

    def __init__(self, centroids: dict[str, tuple[float, float]] = CENTROIDS) -> None:
        self.centroids = centroids
        self.loads = 0

    async def execute(self, _stmt):  # noqa: ANN001 - o stmt nao importa aqui
        self.loads += 1
        # Cede o controle como uma consulta de verdade faz. Sem isto o `execute`
        # falso corre ate o fim sem suspender, as corrotinas do teste de
        # concorrencia nunca se intercalam e o teste passa mesmo sem o lock —
        # verificado por mutacao.
        await asyncio.sleep(0)
        return _Result([_Row(p, *latlng) for p, latlng in self.centroids.items()])


@pytest.fixture(autouse=True)
def _cache_limpo():
    """O cache e estado de MODULO: sem isto um teste contamina o seguinte."""
    reset_centroid_cache()
    yield
    reset_centroid_cache()


@pytest.mark.asyncio
async def test_carrega_uma_vez_e_serve_todo_o_resto_de_memoria():
    session = FakeSession()

    assert await get_centroid(session, "01000") == (-23.5, -46.6)
    assert await get_centroid(session, "60000") == (-3.7, -38.5)
    assert await get_centroid(session, "01000") == (-23.5, -46.6)
    assert await list_known_prefixes(session) == {"01000", "60000"}

    assert session.loads == 1, "so a primeira consulta deveria ir ao banco"


@pytest.mark.asyncio
async def test_list_known_prefixes_nao_copia():
    """Visao das chaves, nao copia: copiar custava 0,54 ms por requisicao.

    Testa a implementacao de proposito — a propriedade que importa e justamente
    nao materializar 12.809 strings para responder a um `in` de 0,06 us. Com o
    cache de resposta ligado isso valia 9% de um p50 de 6 ms.
    """
    assert isinstance(await list_known_prefixes(FakeSession()), KeysView)


@pytest.mark.asyncio
async def test_prefixo_desconhecido_nao_consulta_o_banco():
    """`None` e resposta, nao "cache vazio".

    O cliente fora da amostra e um caminho quente — e o `60165` da demo do
    README. Se ele furasse o cache, cada card sem selo pagaria uma ida ao banco.
    """
    session = FakeSession()

    assert await get_centroid(session, "99999") is None
    assert await get_centroid(session, "99999") is None

    assert session.loads == 1


@pytest.mark.asyncio
async def test_carga_concorrente_acontece_uma_vez_so():
    """O lock existe para isto: processo frio recebendo N requisicoes juntas."""
    session = FakeSession()

    await asyncio.gather(*(get_centroid(session, "01000") for _ in range(10)))

    assert session.loads == 1, "as 10 corrotinas deveriam compartilhar uma carga"


@pytest.mark.asyncio
async def test_reset_forca_recarga():
    """O escape para quem recarregar o ETL com a API no ar."""
    session = FakeSession()
    await get_centroid(session, "01000")
    assert session.loads == 1

    reset_centroid_cache()
    await get_centroid(session, "01000")

    assert session.loads == 2


@pytest.mark.asyncio
async def test_recarga_enxerga_a_tabela_nova():
    """Um snapshot velho serviria selo errado, nao erro — por isso o teste."""
    session = FakeSession({"01000": (-23.5, -46.6)})
    assert await list_known_prefixes(session) == {"01000"}

    reset_centroid_cache()
    session.centroids = {"01000": (-23.5, -46.6), "70000": (-15.8, -47.9)}

    assert await list_known_prefixes(session) == {"01000", "70000"}


@pytest.mark.asyncio
async def test_o_cache_e_do_processo_e_nao_da_sessao():
    """Duas requisicoes seguidas: a segunda nao paga carga nenhuma.

    E a diferenca entre este cache e o memo por requisicao que ele substituiu.
    """
    primeira, segunda = FakeSession(), FakeSession()

    await get_centroid(primeira, "01000")
    await get_centroid(segunda, "01000")

    assert primeira.loads == 1
    assert segunda.loads == 0, "a segunda sessao deveria achar tudo em memoria"


def test_o_cache_comeca_vazio():
    """Guarda o `reset` do fixture: se ele parasse de rodar, isto denuncia."""
    assert repository._centroids is None


@pytest.mark.asyncio
async def test_uf_vem_na_mesma_carga_dos_centroides():
    """Sprint 9: o contexto regional pergunta a UF a cada Home. Uma consulta
    a mais por requisicao desfaria a Sprint 6."""
    session = FakeSession({"01000": (-23.5, -46.6), "70000": (-15.8, -47.9)})

    assert await get_centroid(session, "01000") == (-23.5, -46.6)
    assert await get_uf(session, "01000") == "SP"
    assert await get_uf(session, "70000") is None, "prefixo sem UF no CSV"
    assert await get_uf(session, "99999") is None

    assert session.loads == 1
