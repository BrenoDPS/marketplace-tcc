"""Tela de metodologia (Sprint 16, V7): server-driven e escrita das constantes do motor."""

from httpx import ASGITransport, AsyncClient

from src.features.green_logistics.badge import build_sustainability_props
from src.main import app


async def _get(path: str) -> tuple[int, dict]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(path)
    return r.status_code, r.json()


def _texto(body: dict) -> str:
    partes = []
    for c in body["components"]:
        p = c["props"]
        partes += [p.get("title", ""), *p.get("paragraphs", []), *p.get("items", []), p.get("note") or ""]
    return " ".join(partes)


async def test_metodologia_e_uma_tela_do_servidor_com_os_numeros_do_motor() -> None:
    status, body = await _get("/api/v1/methodology")
    assert status == 200
    assert body["screen_id"] == "methodology"
    tipos = [c["type"] for c in body["components"]]
    assert tipos[0] == "hero_banner" and set(tipos[1:]) == {"content_section"}
    texto = _texto(body)
    # Os numeros vem das constantes: mudar o motor muda a pagina.
    for trecho in ("1,345", "15 km", "0,680", "0,092", "6.000 cm³", "100 km", "até 1%", "Lee e Chae (2023)"):
        assert trecho in texto, trecho


async def test_voltar_leva_o_cep_de_quem_veio_da_vitrine() -> None:
    _, body = await _get("/api/v1/methodology?customer_zip_prefix=05311")
    assert body["components"][0]["actions"][0]["payload"]["path"] == "/?customer_zip_prefix=05311"
    _, sem = await _get("/api/v1/methodology")
    assert sem["components"][0]["actions"][0]["payload"]["path"] == "/"


async def test_cep_invalido_e_422() -> None:
    status, _ = await _get("/api/v1/methodology?customer_zip_prefix=abc")
    assert status == 422


def test_explicador_do_selo_aponta_para_a_metodologia() -> None:
    badge = build_sustainability_props(50.0, weight_g=1000.0, explain=True)
    assert badge is not None and badge.explanation is not None
    assert badge.explanation.methodology_path == "/metodologia"
