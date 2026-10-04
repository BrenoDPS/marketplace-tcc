"""Tests de GET /api/v1/products/{product_id}.

Nao depende de Postgres: `dependency_overrides` + monkeypatch nos repositorios,
mesmo padrao dos outros endpoints.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.database import get_db
from src.features.product_detail.repository import ProductDetailRow
from src.main import app

KNOWN_PREFIXES = {"05311", "01000"}

PRODUCT = ProductDetailRow(
    product_id="prod_real_1",
    category="informatica_acessorios",
    weight_g=2500.0,
    rating=4.25,
    review_count=8,
    unit_price=199.90,
    seller_id="seller_close",
    seller_zip_prefix="08275",
    seller_city="sao paulo",
    seller_state="SP",
)

# Produto sem nenhum pedido avaliado: a tela precisa OMITIR, nao inventar.
PRODUCT_UNRATED = ProductDetailRow(
    product_id="prod_sem_nota",
    category="bebes",
    weight_g=800.0,
    rating=None,
    review_count=0,
    unit_price=59.90,
    seller_id="seller_far",
    seller_zip_prefix="60000",
    seller_city=None,
    seller_state=None,
)

# Mesmo produto, duas origens: e o caso que a amostra tem 579 vezes e que o
# detalhe escondia ate a Sprint 7 (mostrava a oferta `is_default`, arbitraria).
PRODUCT_MULTI_PERTO = ProductDetailRow(
    product_id="prod_dois_vendedores",
    category="relogios_presentes",
    weight_g=1000.0,
    rating=4.0,
    review_count=3,
    unit_price=39.90,
    seller_id="seller_recife",
    seller_zip_prefix="08275",
    seller_city="recife",
    seller_state="PE",
)
PRODUCT_MULTI_LONGE = ProductDetailRow(
    product_id="prod_dois_vendedores",
    category="relogios_presentes",
    weight_g=1000.0,
    rating=4.0,
    review_count=3,
    unit_price=39.90,
    seller_id="seller_maringa",
    seller_zip_prefix="60000",
    seller_city="maringa",
    seller_state="PR",
)

# Vendedor no MESMO prefixo do comprador: distancia entre centroides = 0.
# Caso raro antes, comum depois que o sistema passou a buscar o mais proximo.
PRODUCT_MESMA_REGIAO = ProductDetailRow(
    product_id="prod_mesma_regiao",
    category="bebes",
    weight_g=1000.0,
    rating=None,
    review_count=0,
    unit_price=29.90,
    seller_id="seller_vizinho",
    seller_zip_prefix="05311",
    seller_city="sao paulo",
    seller_state="SP",
)

# Vendedor sem centroide: distancia DESCONHECIDA, que nao e a mesma coisa que
# distancia pequena demais para medir.
PRODUCT_SEM_CENTROIDE = ProductDetailRow(
    product_id="prod_sem_centroide",
    category="bebes",
    weight_g=1000.0,
    rating=None,
    review_count=0,
    unit_price=19.90,
    seller_id="seller_sem_geo",
    seller_zip_prefix="99999",
    seller_city="lugar nenhum",
    seller_state="ZZ",
)

CATALOG: dict[str, list[ProductDetailRow]] = {
    "prod_real_1": [PRODUCT],
    "prod_sem_nota": [PRODUCT_UNRATED],
    # Longe PRIMEIRO: se o composer pegasse a primeira em vez da mais proxima,
    # os testes de multi-vendedor passariam por acidente.
    "prod_dois_vendedores": [PRODUCT_MULTI_LONGE, PRODUCT_MULTI_PERTO],
    "prod_mesma_regiao": [PRODUCT_MESMA_REGIAO],
    "prod_sem_centroide": [PRODUCT_SEM_CENTROIDE],
}
# `05311` ausente do mapa de proposito: `_fake_distance` devolve None para
# vendedor sem centroide, e 0.0 so para o vizinho do proprio comprador.
DISTANCE_BY_SELLER_ZIP = {"08275": 27.0, "60000": 2000.0, "05311": 0.0}


async def _override_get_db() -> AsyncIterator[None]:
    yield None


async def _fake_list_known_prefixes(_session: object) -> set[str]:
    return KNOWN_PREFIXES


async def _fake_fetch(_session: object, product_id: str) -> list[ProductDetailRow]:
    return CATALOG.get(product_id, [])


async def _fake_distance(
    _session: object, customer_zip_prefix: str, seller_zip_prefix: str
) -> float | None:
    """So a distancia e falsa. O selo sai da regra de verdade (`badge.py`).

    Antes o teste tambem falseava `build_badge_for_pair`, e com isso a regra do
    limiar de 100 km nunca era exercida aqui.
    """
    return DISTANCE_BY_SELLER_ZIP.get(seller_zip_prefix)


@pytest.fixture(autouse=True)
def patch_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    app.dependency_overrides[get_db] = _override_get_db
    monkeypatch.setattr(
        "src.features.product_detail.router.list_known_prefixes",
        _fake_list_known_prefixes,
    )
    monkeypatch.setattr(
        "src.features.product_detail.router.fetch_product_offers", _fake_fetch
    )
    monkeypatch.setattr(
        "src.features.product_detail.composer.compute_distance_km", _fake_distance
    )
    yield
    app.dependency_overrides.clear()


async def _get(path: str) -> tuple[int, dict]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(path)
    return response.status_code, response.json()


def _block(body: dict, block_type: str) -> dict:
    return next(c for c in body["components"] if c["type"] == block_type)


# ---------------------------------------------------------------------------
# Casos
# ---------------------------------------------------------------------------

async def test_returns_a_screen_response() -> None:
    status, body = await _get("/api/v1/products/prod_real_1?customer_zip_prefix=05311")
    assert status == 200
    assert body["screen_id"] == "product_detail"
    assert body["context"] == "product"
    assert [c["type"] for c in body["components"]] == ["product_detail", "impact_banner"]


async def test_detail_carries_real_dataset_fields() -> None:
    _, body = await _get("/api/v1/products/prod_real_1?customer_zip_prefix=05311")
    props = _block(body, "product_detail")["props"]
    assert props["title"] == "Informatica Acessorios"
    assert props["price"] == pytest.approx(199.90)
    assert props["weight_g"] == pytest.approx(2500.0)
    assert props["seller_city"] == "sao paulo"
    assert props["seller_state"] == "SP"


async def test_rating_comes_from_the_dataset() -> None:
    _, body = await _get("/api/v1/products/prod_real_1?customer_zip_prefix=05311")
    props = _block(body, "product_detail")["props"]
    assert props["rating"] == pytest.approx(4.25)
    assert props["review_count"] == 8


async def test_product_without_reviews_omits_the_rating() -> None:
    """Nenhum pedido avaliado => `rating` nulo. Preencher com um valor
    'plausivel' seria inventar dado numa tela sobre credibilidade."""
    _, body = await _get("/api/v1/products/prod_sem_nota?customer_zip_prefix=05311")
    props = _block(body, "product_detail")["props"]
    assert props["rating"] is None
    assert props["review_count"] == 0


async def test_badge_and_impact_reflect_the_customer_distance() -> None:
    _, body = await _get("/api/v1/products/prod_real_1?customer_zip_prefix=05311")
    assert _block(body, "product_detail")["props"]["badge"] is not None
    banner = _block(body, "impact_banner")["props"]
    assert banner["distance_km"] == pytest.approx(27.0)
    # 27 km de linha reta -> 36,315 km de estrada: 21,315 de caminhao + 15 de van
    # (21,315 * 0,092 + 15 * 0,680) * 0,0025 t = 0,03040245 kg
    assert banner["co2_kg"] == pytest.approx(0.03040245)
    assert "27 km" in banner["message"]
    assert "sao paulo" in banner["message"]


async def test_distant_seller_has_no_badge() -> None:
    _, body = await _get("/api/v1/products/prod_sem_nota?customer_zip_prefix=05311")
    assert _block(body, "product_detail")["props"]["badge"] is None


async def test_detail_carries_the_checkout_action() -> None:
    """A tela de detalhe tem de dizer COMO comprar — senao o cliente precisaria
    lembrar da acao que veio no card."""
    _, body = await _get("/api/v1/products/prod_real_1?customer_zip_prefix=05311")
    actions = _block(body, "product_detail")["actions"]
    assert any(
        a["type"] == "api_call" and a["payload"]["body_key"] == "checkout"
        for a in actions
    )


# ---------------------------------------------------------------------------
# Mesmo produto, varios vendedores (Sprint 7)
# ---------------------------------------------------------------------------

async def test_escolhe_o_vendedor_mais_proximo_do_comprador() -> None:
    """O nucleo da feature.

    O produto tem duas origens: 27 km e 2000 km. A lista chega com a distante
    primeiro, entao pegar "a primeira" daria a errada.
    """
    _, body = await _get(
        "/api/v1/products/prod_dois_vendedores?customer_zip_prefix=05311"
    )
    props = _block(body, "product_detail")["props"]

    assert props["seller_id"] == "seller_recife"
    assert props["seller_city"] == "recife"
    assert _block(body, "impact_banner")["props"]["distance_km"] == pytest.approx(27.0)


async def test_a_origem_proxima_ganha_selo_que_a_distante_nao_teria() -> None:
    """A escolha muda o selo, nao so um rotulo: 27 km tem selo, 2000 km nao.

    E o que a feature compra — anunciar a origem distante seria declarar
    impacto maior do que o necessario, numa tela cujo assunto e impacto.
    """
    _, body = await _get(
        "/api/v1/products/prod_dois_vendedores?customer_zip_prefix=05311"
    )
    assert _block(body, "product_detail")["props"]["badge"] is not None


async def test_a_tela_revela_que_havia_outra_origem() -> None:
    """Sem isto a feature fica invisivel: o usuario veria o vendedor proximo
    sem saber que existia um distante, e o argumento do trabalho e a
    comparacao, nao o resultado dela."""
    _, body = await _get(
        "/api/v1/products/prod_dois_vendedores?customer_zip_prefix=05311"
    )
    mensagem = _block(body, "impact_banner")["props"]["message"]

    assert "outro vendedor" in mensagem
    assert "2000 km" in mensagem
    assert "maringa" in mensagem
    assert "evita" in mensagem
    # A origem escolhida aparece UMA vez: a primeira frase ja a nomeou, e o
    # comparativo so descreve a alternativa.
    assert mensagem.count("recife") == 1


async def test_produto_de_um_vendedor_so_nao_inventa_comparacao() -> None:
    """Nao ha com o que comparar: a mensagem nao pode sugerir que ha."""
    _, body = await _get("/api/v1/products/prod_real_1?customer_zip_prefix=05311")
    mensagem = _block(body, "impact_banner")["props"]["message"]

    assert "vendedores" not in mensagem
    assert "evita" not in mensagem


async def test_unknown_product_returns_404() -> None:
    status, body = await _get("/api/v1/products/nao_existe?customer_zip_prefix=05311")
    assert status == 404
    assert "product_id" in body["detail"]


async def test_unknown_cep_returns_422() -> None:
    status, body = await _get("/api/v1/products/prod_real_1?customer_zip_prefix=99999")
    assert status == 422
    assert "customer_zip_prefix" in body["detail"]


async def test_missing_cep_returns_422() -> None:
    status, _ = await _get("/api/v1/products/prod_real_1")
    assert status == 422


async def test_banner_nao_anuncia_0km_nem_0g_para_vendedor_da_mesma_regiao() -> None:
    """A aresta que a feature do vendedor mais proximo tornou comum.

    Escolher ativamente o vendedor mais perto faz cair com frequencia no caso
    "mesmo prefixo de CEP", onde a distancia entre centroides e exatamente 0.
    O banner nao pode responder "Distancia: 0 km / CO₂: 0,00 g" — o cliente
    omite a linha quando o campo vem nulo, e o texto explica o porque.
    """
    _, body = await _get("/api/v1/products/prod_mesma_regiao?customer_zip_prefix=05311")
    banner = _block(body, "impact_banner")["props"]

    assert banner["distance_km"] is None
    assert banner["co2_kg"] is None
    assert "0 km" not in banner["message"]
    assert "sua região" in banner["message"]
    assert _block(body, "product_detail")["props"]["badge"]["label"] == (
        "Entrega local (mesma região)"
    )


async def test_mesma_regiao_e_diferente_de_distancia_desconhecida() -> None:
    """Os dois casos caem no mesmo nulo; so a `message` os separa.

    Sem esta distincao, "o vendedor e do seu bairro" e "nao faco ideia de onde
    ele esta" ficariam indistinguiveis na tela.
    """
    _, perto = await _get(
        "/api/v1/products/prod_mesma_regiao?customer_zip_prefix=05311"
    )
    _, desconhecido = await _get(
        "/api/v1/products/prod_sem_centroide?customer_zip_prefix=05311"
    )

    m_perto = _block(perto, "impact_banner")["props"]["message"]
    m_desconhecido = _block(desconhecido, "impact_banner")["props"]["message"]

    assert "sua região" in m_perto
    assert "Não foi possível estimar" in m_desconhecido
    assert _block(perto, "product_detail")["props"]["badge"] is not None
    assert _block(desconhecido, "product_detail")["props"]["badge"] is None


def test_co2_evitado_e_a_diferenca_das_emissoes_nao_a_emissao_da_diferenca() -> None:
    """Com o motor de cadeia (Sprint 9) as duas contas divergem.

    A emissao da DIFERENCA de distancias ignorava a ultima milha das duas
    entregas; o que a escolha evita e a diferenca entre as duas emissoes.
    """
    from src.features.green_logistics.co2 import calculate_co2_kg, format_co2
    from src.features.product_detail.composer import _mensagem_comparativa

    perto_km, longe_km = 20.0, 2483.0
    texto = _mensagem_comparativa(
        (perto_km, PRODUCT_MULTI_PERTO), [(longe_km, PRODUCT_MULTI_LONGE)]
    )
    certo = calculate_co2_kg(longe_km, 1000.0) - calculate_co2_kg(perto_km, 1000.0)
    errado = calculate_co2_kg(longe_km - perto_km, 1000.0)
    assert format_co2(certo) != format_co2(errado)
    assert f"evita ~{format_co2(certo)} de CO₂" in texto
