# Primeira requisição depois de subir a API

> Gerado por `python -m scripts.primeira_requisicao` no commit `8544e3b`. Detalhe de produto
> (sem cache de resposta), API recém-iniciada na porta 8001, 5 rodadas.

| rodada | primeira requisição (ms) | seguintes: mediana de 20 (ms) |
|---|---|---|
| 1 | 254 | 5,1 |
| 2 | 234 | 5,6 |
| 3 | 358 | 7,6 |
| 4 | 205 | 5,2 |
| 5 | 233 | 5,3 |

**Primeira requisição: mediana 234 ms (de 205 a 358 ms);
seguintes: mediana 5,3 ms.** A diferença é a carga dos
centroides em memória e o aquecimento do processo. Na demonstração, uma requisição de
aquecimento antes do primeiro clique evita a espera (`docs/roteiro-banca.md`, preparação).
