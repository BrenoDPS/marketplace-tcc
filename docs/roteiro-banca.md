# Roteiro da demonstração na banca (≈ 4 min 30 s)

Cinco passos, um clique de cada vez, cada um ligado a um objetivo específico e
a um número do Cap. 5. O ensaio automático percorre **exatamente** estes
cliques e confere os números citados abaixo:

```bash
cd web && npx playwright test roteiro-banca
```

Se ele falhar, a vitrine mudou (ETL recarregado, regra alterada): atualizar este
roteiro **antes** da defesa, não durante.

## Preparação (T − 30 min)

- [ ] Notebook **na tomada**; Chrome em **janela anônima** (carrinho vazio), modo claro, zoom 100% (125% se o projetor for pequeno).
- [ ] Pilha no ar: `docker compose up -d` → `uvicorn src.main:app --port 8000` (sem `--reload`) → `cd web && npm run dev`.
- [ ] `SDUI_MUTACOES_DEMO=true` no `.env` (padrão).
- [ ] Ensaio verde: `cd web && npx playwright test roteiro-banca` (≈ 10 s).
- [ ] Aquecer o cache: abrir uma vez `http://localhost:3000/?customer_zip_prefix=05311` e o detalhe do 5º card em "Menor CO₂".
- [ ] Abrir a aba de novo em `http://localhost:3000/` (tela "Onde você está?").
- [ ] Plano B aberto noutra aba: `docs/banca/demo-contingencia.webm` (1 min 04 s, sem som — narrar por cima).

## Roteiro

| Tempo | Clique | O que mostrar / falar | Objetivo · número |
|---|---|---|---|
| 0:00–0:40 | Digitar **05311** → **Entrar** | "A tela inteira vem do servidor. Sem perfil escolhido, ele olha a UF do CEP: *Em alta em SP: Alimentos* — compradores de SP levam 1,3× mais desta categoria que a média do Brasil. O porquê está na tela, e *Ver vitrine geral* desfaz." | (c) · adaptação regional em 12 das 27 UFs, sem custo de desempenho |
| 0:40–1:20 | **Ordenar → Menor CO₂** | "Todo card diz de onde sai. Ordenando por emissão, o 2º card sai de **106 km** e vem antes de outros a 24 km: é mais leve. Menor CO₂ não é o mesmo que mais perto." | (b) · motor por cadeia de transporte |
| 1:20–2:40 | Abrir o **5º card** (Atibaia) → **Como calculamos?** → rolar até o **mapa** e o **comparador** | "Selo: 50 km, 7,17 g. *Como calculamos* mostra a conta com as fontes — inclusive que o item pesa 150 g, mas ocupa como **479 g** (peso cúbico). O mapa mostra a origem; o comparador, a outra: **Videira (SC), 588 km, R$ 39,90 e 5,5× a emissão**. O mais perto é mais barato *e* emite menos. Vitrine, detalhe e compra escolhem a origem pela mesma regra." | (b)(c) · circuidade: erro de 8,7% contra o OSRM; mesma escolha em 86,5% · CO₂ evitado de 9,8% nos itens com alternativa |
| 2:40–3:20 | **Ir para o carrinho** → **Simular compra** → etapa **Entrega** → **Verde** | "A compra é uma página do servidor. Trocar a modalidade move frete, prazo e CO₂ juntos: Verde R$ 6,75 e **4,3 g**; Expressa R$ 12,70 e 17,9 g. Os fatores das modalidades são cenário declarado — está na metodologia." → **← Voltar à vitrine** | (c) |
| 3:20–4:30 | Ligar **SDUI** → abrir o 5º card → **Mutação do servidor**: *Reordenar*, depois *Bloco que o cliente não conhece* | "Cada bloco mostra o JSON que veio do servidor. Agora peço ao **servidor** que reordene a árvore: a tela obedece. Um bloco que este cliente não conhece degrada, não quebra. E o relógio *mesma página desde…* não mudou: nada recarregou, nada foi recompilado." | (a)(d) · 5 mutações sem *build* |
| 4:30 | (fala de fechamento, sem clique) | "Com 250 usuários e cache ligado, o p95 ficou em 19 ms; sem cache, entre 600 e 1.200 ms. Remedido no código atual, em 15/10." | (d) · `docs/performance.md` §13 |

**Se o tempo apertar:** pular o passo 2:40–3:20 (checkout). **Se sobrar:** abrir
*Ver metodologia completa* no explicador do selo.

## Plano B

| Falha | O que fazer |
|---|---|
| API ou banco não sobe | Tocar `docs/banca/demo-contingencia.webm` e narrar pela tabela acima (o vídeo segue a mesma ordem). |
| Vitrine diferente do roteiro | Ensaio falhou e ninguém viu: usar o vídeo; os números do vídeo são os do commit gravado. |
| Lentidão no primeiro clique | É o cache frio — por isso o aquecimento na preparação. |
| Projetor corta a tela | Zoom do navegador em 90%; o layout é testado de 390 a 1440 px. |

## Perguntas prováveis da banca

| Pergunta | Resposta curta | Onde está |
|---|---|---|
| Por que o selo é por distância e não por emissão? | Distância é compreensível para o comprador; a emissão aparece ao lado e ordena a vitrine ("Menor CO₂"). Selo por emissão relativa é trabalho futuro. | Card [Roadmap] no Trello; Cap. 6 |
| A regra escolhe a mais próxima mesmo quando outra, quase à mesma distância, é bem mais barata? | Sim, além do empate de 1% o preço não pesa. Há um caso real de R$ 337,69 × R$ 130,00 por 0,4 g. É escolha de desenho a discutir (card [Decisão]). | Comparador de origens; Cap. 6 |
| De onde vem o 1,345? É válido para o Brasil? | Média brasileira estrada × linha reta (Lee e Chae, 2023, sobre Gonçalves et al., 2014). Validamos com o OSRM: bate até 100 km; acima, superestima 5–10%. | Cap. 5, §5.1.3 |
| Por que 6.000 cm³/kg? | É o divisor do peso cúbico de encomendas dos Correios (Olist, 2022). Com o rodoviário (300 kg/m³), a emissão absoluta sobe ~60%, mas o CO₂ evitado relativo fica em 9,6% × 9,8%. | Cap. 5, §5.1.4; rastreabilidade, desvio 27 |
| O teste de carga numa máquina só vale? | Compara configurações entre si, não prevê produção. Foi refeito no código atual (CPU por requisição igual) e na tomada (13 ensaios em bateria descartados). | `docs/performance.md` §§11–13 |
| A mutação não é só o front mudando a resposta? | Há as duas provas: o E2E intercepta a rede (isola o renderizador) e o modo apresentação faz o **próprio BFF** mutar a árvore. | `web/e2e/contract-mutation.spec.ts`, `apresentacao.spec.ts` |
| Alguém usou a loja? | Teste de usabilidade (SUS + preferência declarada × revelada) — ver `docs/usabilidade/` e o resultado, se já rodado. | Cap. 5 (subseção qualitativa) |
