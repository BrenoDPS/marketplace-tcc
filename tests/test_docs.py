"""Sensor de frescor: todo caminho citado nos docs de entrada tem de existir.

Pega referencia pendurada — arquivo renomeado, handoff que nunca foi escrito.
NAO pega doc semanticamente velho ("sprint concluida marcada como ativa"):
isso continua sendo leitura humana.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DOCS = ["AGENTS.md", "docs/PROJECT_BOOTSTRAP.md", "README.md"]

_DIRS = r"(?:src|docs|web|tests|load|scripts|\.github)/"
# `caminho` em code span (sem glob nem placeholder) ou alvo de link markdown.
_SPAN = re.compile(rf"`({_DIRS}[^`\s*<>]+)`")
_LINK = re.compile(rf"\]\(({_DIRS}[^)\s#]+)\)")


def _cited(text: str) -> set[str]:
    # `src/core/database.py:8` cita uma linha; o arquivo e o que importa.
    return {p.split(":")[0] for p in _SPAN.findall(text) + _LINK.findall(text)}


@pytest.mark.parametrize("doc", DOCS)
def test_caminhos_citados_existem(doc: str) -> None:
    text = (ROOT / doc).read_text(encoding="utf-8")
    faltando = sorted(p for p in _cited(text) if not (ROOT / p).exists())
    assert not faltando, f"{doc} cita caminhos que nao existem: {faltando}"
