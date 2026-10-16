"""Painel da pesquisa (Sprint 16, V8): a tela traz as tabelas de docs/resultados/ sem recalcular."""

from httpx import ASGITransport, AsyncClient

from src.features.green_logistics.pesquisa import ARQUIVOS, RESULTADOS, blocos_do_markdown
from src.main import app


async def _get(path: str) -> tuple[int, dict]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(path)
    return r.status_code, r.json()


async def test_toda_celula_de_docs_resultados_chega_a_tela() -> None:
    status, body = await _get("/api/v1/research?customer_zip_prefix=05311")
    assert status == 200 and body["screen_id"] == "research"
    tabelas = [c["props"] for c in body["components"] if c["type"] == "data_table"]
    na_tela = {cel for t in tabelas for linha in t["rows"] for cel in linha["cells"]} | {c for t in tabelas for c in t["columns"]}
    # Conferencia independente do parser: celula a celula, direto do Markdown.
    for nome in ARQUIVOS:
        for linha in (RESULTADOS / nome).read_text(encoding="utf-8").splitlines():
            if linha.startswith("|") and not set(linha) <= set("|-: "):
                for cel in linha.strip("|").split("|"):
                    assert cel.replace("**", "").replace("`", "").strip() in na_tela, (nome, cel)
    assert len(tabelas) == 6
    destaques = {linha["cells"][0] for t in tabelas for linha in t["rows"] if linha["emphasis"]}
    assert destaques == {"Brasil", "CO₂ evitado", "todas"}
    hero = body["components"][0]
    assert [a["payload"]["path"] for a in hero["actions"]] == ["/?customer_zip_prefix=05311", "/metodologia?customer_zip_prefix=05311"]


async def test_cep_invalido_e_422() -> None:
    status, _ = await _get("/api/v1/research?customer_zip_prefix=abc")
    assert status == 422


def test_tabela_herda_o_titulo_do_subtitulo_e_a_nota_de_baixo() -> None:
    blocos = blocos_do_markdown(
        "# Doc\n\n> Gerado por x.\n\n## Resultado\n\nLegenda.\n\n| UF | n |\n|---|---|\n| **Brasil** | 10 |\n| SP | 4 |\n\nNota.\n\n## Limites\n\n- um\n  continua\n"
    )
    secao, tabela, limites = (b.props for b in blocos)
    assert (secao.title, secao.note) == ("Doc", "Gerado por x.")
    assert (tabela.title, tabela.caption, tabela.columns) == ("Resultado", "Legenda. Nota.", ["UF", "n"])
    assert [(r.cells, r.emphasis) for r in tabela.rows] == [(["Brasil", "10"], True), (["SP", "4"], False)]
    assert (limites.title, limites.items) == ("Limites", ["um continua"])
