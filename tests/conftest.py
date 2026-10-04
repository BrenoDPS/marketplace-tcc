"""A suite roda sem Redis — no CI nao ha Redis, e localmente um cache de outra
execucao devolveria a tela antiga e mascararia o teste. O cache e ligado por
padrao na aplicacao (`src/core/config.py`); aqui ele e desligado ANTES de
qualquer modulo de `src` ser importado, porque `settings` le o ambiente uma vez.
"""

import os

os.environ["CACHE_ENABLED"] = "false"
