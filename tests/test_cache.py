"""O cache e variavel de experimento: o que os testes garantem e que ele nao
muda o comportamento da aplicacao quando esta desligado, e que a chave nao
confunde duas telas diferentes.

Nao ha teste contra um Redis de verdade: a suite inteira roda sem servico
externo (nem Postgres). A conferencia da batida real esta em
`docs/performance.md` §9, feita na propria execucao.
"""

from src.core import cache
from src.core.config import settings


def test_chave_distingue_none_de_vazio_na_outra_posicao():
    """("a", None) e (None, "a") sao telas diferentes e nao podem colidir."""
    assert cache.key("home", "a", None) != cache.key("home", None, "a")


def test_chave_e_deterministica():
    assert cache.key("home", "05311", "default", None, None) == cache.key(
        "home", "05311", "default", None, None
    )


def test_chave_muda_com_cada_parametro():
    base = cache.key("home", "05311", "default", None, None)
    variacoes = [
        cache.key("home", "60165", "default", None, None),
        cache.key("home", "05311", "conscious_buyer", None, None),
        cache.key("home", "05311", "default", "moveis", None),
        cache.key("home", "05311", "default", None, "beleza_saude"),
        cache.key("checkout", "05311", "default", None, None),
    ]
    assert len(set(variacoes)) == len(variacoes)
    assert base not in variacoes


def test_chave_tem_prefixo_de_namespace():
    """FLUSHALL e grosseiro; o prefixo permite limpar so o que e nosso."""
    assert cache.key("home", "05311").startswith("sdui:")


async def test_desligado_nao_toca_no_redis(monkeypatch):
    """Com CACHE_ENABLED=false nao existe cliente — nem conexao tentada."""
    monkeypatch.setattr(settings, "CACHE_ENABLED", False)
    monkeypatch.setattr(cache, "_client", None)
    assert cache.get_client() is None
    assert await cache.get("sdui:home|x") is None
    await cache.set("sdui:home|x", "{}")  # no-op, nao pode levantar
