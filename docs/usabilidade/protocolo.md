# Teste de usabilidade — protocolo (Sprint 14)

Fecha a fragilidade 1 do parecer (`docs/tcc/parecer-revisao-cap4-cap5.md`, seção 8):
nada no projeto mostra que uma pessoa **entende** o selo e a pegada, nem que
**trocaria** de vendedor por eles. Este teste mede as duas coisas, além da
usabilidade geral (SUS).

| | |
|---|---|
| Amostra | 8 a 10 pessoas que compram online (colegas, familiares); ninguém do grupo |
| Duração | ~20 min por pessoa: 2 min de abertura, ~10 min de tarefas, ~8 min de questionário |
| Ambiente | Notebook do grupo, pilha local (`docker compose up -d`, API, `npm run dev`), Chrome em 1280 × 800 ou maior, carrinho vazio, modo SDUI desligado |
| Papéis | 1 moderador (lê as tarefas, não ajuda) e 1 anotador (sucesso, tempo, comentários) |
| Registro | `docs/usabilidade/respostas.csv`, uma linha por participante; nada que identifique a pessoa |
| Análise | `python -m scripts.sus` → `docs/resultados/usabilidade.md` |

## 1. Antes de cada sessão

1. Pilha no ar: `docker compose up -d`, API (`uvicorn src.main:app`) e front (`cd web && npm run dev`).
2. Abrir `http://localhost:3000/` (tela "Onde você está?") numa **janela anônima**:
   carrinho vazio e nada de sessão anterior.
3. Cronômetro zerado; ficha da seção 5 impressa ou aberta.

## 2. Abertura (ler em voz alta)

> "Obrigado por participar. Vamos testar o **site**, não você: se algo for difícil,
> é um problema do site. É uma loja simulada; nenhum pagamento é feito. Vou pedir
> algumas tarefas; tente fazê-las sozinho e, se puder, pense em voz alta. Eu não
> vou poder ajudar durante as tarefas. No fim há um questionário curto. Você pode
> parar a qualquer momento. Podemos começar?"

Antes de começar, ler o **termo de participação** (seção 6) e registrar o aceite.

## 3. Tarefas

Ler uma de cada vez. **Sucesso** = critério abaixo, sem ajuda. Tempo do fim da
leitura até o critério (ou desistência, ou 3 min). Anotar hesitações e frases.

| # | Tarefa (lida ao participante) | Critério de sucesso | O que mede |
|---|---|---|---|
| T1 | "Você mora no CEP **05311**. Entre na loja e encontre produtos de **cama, mesa e banho**." | Vitrine filtrada (chip ou busca) | Entrada e navegação |
| T2 | "Escolha um desses produtos e me diga **de onde ele sai** e **quanto CO₂** a entrega emite." | Diz cidade **e** distância ou CO₂ corretamente (card, selo ou detalhe) | Compreensão do card e do selo |
| T3 | "Agora quero ver a loja pensando no **meio ambiente**. Mude a vitrine para isso e coloque no carrinho o **primeiro** e o **quarto** produto." | Contexto "Consciente" e os 2 itens no carrinho (Esporte e lazer; Brinquedos) | Personalização e carrinho |
| T4 | "Simule a compra e escolha a forma de entrega que **menos polui**." | Modalidade "Verde" selecionada | Leitura do comparativo de entrega |
| T5 | "Antes de terminar: o site sugere alguma coisa sobre os seus produtos? **Decida** se aceita ou não, como faria numa compra de verdade." | Encontra a sugestão "Mais perto de você" (Remessas). A **decisão** (trocou / não trocou) é registrada, não é critério | Descoberta da alternativa e **preferência revelada** |

Na T5 a alternativa custa **R$ 69,99 contra R$ 59,90** e emite **91% menos CO₂**
(6 km contra 13 km). Trocar significa pagar R$ 10 a mais pela entrega mais limpa.
Não comentar o preço nem a emissão.

> Produtos da T3 conferidos em 15/10/2026 no commit `35ac6bc`, contexto
> `conscious_buyer`, CEP 05311: posição 1 `006baa9a…` (Esporte e lazer, Pirituba,
> 4 km), posição 4 `009af127…` (Brinquedos, Barueri, 13 km). Recarregou o ETL?
> Conferir antes da primeira sessão que a T5 ainda mostra a sugestão.

## 4. Questionário (depois das tarefas)

### 4.1 SUS — System Usability Scale

Escala de 1 (discordo totalmente) a 5 (concordo totalmente). Itens na ordem
original; **não reescrever** — os ímpares são positivos e os pares, negativos, e
o cálculo depende disso.

**Usar a versão brasileira validada** de Lourenço, Carmona e Lopes (2022),
Tabela 1 do artigo (DOI 10.5294/aqui.2022.22.2.8). Os itens 1, 7 e 9 abaixo já
estão na redação deles; **antes da primeira sessão, copiar os demais da
Tabela 1** (está em imagem no artigo, não deu para extrair). A lista abaixo é a
tradução de trabalho, só para ensaiar o roteiro.

1. Eu gostaria de usar esse sistema frequentemente.
2. Eu achei o sistema desnecessariamente complexo.
3. Eu achei o sistema fácil de usar.
4. Eu acho que precisaria do apoio de uma pessoa técnica para conseguir usar este sistema.
5. Eu achei que as diversas funções deste sistema estavam bem integradas.
6. Eu achei que havia muita inconsistência neste sistema.
7. Eu imagino que a maioria das pessoas pode aprender a usar esse sistema muito rapidamente.
8. Eu achei o sistema muito complicado de usar.
9. Eu me senti muito seguro usando o sistema.
10. Eu precisei aprender muitas coisas antes de conseguir usar este sistema.

### 4.2 Compreensão e preferência declarada

| Coluna no CSV | Pergunta | Resposta |
|---|---|---|
| `entendi_selo` | "Eu entendi o que o selo 'Entrega local' quer dizer." | 1 a 5 |
| `confio_co2` | "Eu confio no número de CO₂ mostrado." | 1 a 5 |
| `troca_mesmo_preco` | "Numa loja real, se o mesmo produto saísse de um vendedor mais perto, emitindo menos, **pelo mesmo preço**, você trocaria?" | sim / nao |
| `troca_5pct` | "E se fosse **5% mais caro**?" | sim / nao |
| `troca_10pct` | "E **10% mais caro**?" | sim / nao |
| `comentario` | "O que mais te chamou atenção — bom ou ruim?" | texto livre, curto |

### 4.3 Perfil (sem identificar)

`faixa_etaria` (18-24, 25-34, 35-44, 45+) e `compra_online` (quantas vezes por mês:
0, 1-2, 3-5, 6+).

## 5. Ficha do anotador → `respostas.csv`

Colunas, nesta ordem (o script confere):

```
participante,faixa_etaria,compra_online,t1,t1_s,t2,t2_s,t3,t3_s,t4,t4_s,t5,t5_s,t5_trocou,sus1,sus2,sus3,sus4,sus5,sus6,sus7,sus8,sus9,sus10,entendi_selo,confio_co2,troca_mesmo_preco,troca_5pct,troca_10pct,comentario
```

- `participante`: P01, P02… (nunca nome).
- `tN`: 1 = sucesso, 0 = não; `tN_s`: segundos.
- `t5_trocou`: sim / nao / nao_viu (não achou a sugestão).
- `comentario`: entre aspas se tiver vírgula.

## 6. Termo de participação (ler e registrar o aceite)

> Você está convidado a participar de um teste de usabilidade do Trabalho de
> Conclusão de Curso *[título]*, de *[autores]*, curso de *[curso]*, Facens,
> orientado por *[orientador]*. O objetivo é avaliar se a interface de uma loja
> simulada é fácil de usar e se as informações ambientais são compreensíveis.
>
> - A participação dura cerca de 20 minutos e é voluntária; você pode desistir a
>   qualquer momento, sem justificativa e sem prejuízo.
> - Não coletamos nome, e-mail, documento, imagem nem voz. As respostas são
>   registradas com um código (P01, P02…) e usadas apenas, de forma agregada,
>   neste trabalho.
> - Não há riscos além do desconforto de ser observado durante as tarefas; não há
>   pagamento nem custo.
> - Dúvidas: *[contato do grupo]*.
>
> Declaro que li e aceito participar. ( ) Sim ( ) Não

**A confirmar com o orientador:** se o teste precisa passar pelo Comitê de Ética
(CEP/Conep) ou se a coordenação aceita este termo para uma pesquisa anônima de
opinião com colegas. A Resolução CNS nº 510/2016 trata desse caso; a decisão
é da instituição, não do grupo.

## 7. Como entra no Cap. 5

Nova subseção qualitativa, curta: amostra (n, perfil), taxa de sucesso por tarefa,
SUS (média, desvio, comparação com a referência de 68), compreensão do selo, e
preferência declarada × revelada (quantos disseram que trocariam × quantos
trocaram na T5, pagando R$ 10 a mais). A diferença entre as duas é, por si, um
resultado: o que as pessoas dizem sobre sustentabilidade nem sempre é o que fazem.

**Referência do instrumento** (dentro da regra dos 5 anos):

> LOURENÇO, D. F.; CARMONA, E. V.; LOPES, M. H. B. M. Tradução e adaptação
> transcultural da System Usability Scale para o português do Brasil.
> **Aquichan**, v. 22, n. 2, e2228, 2022. DOI: 10.5294/aqui.2022.22.2.8.

Validação com 100 estudantes, estrutura unidimensional, alfa de Cronbach 0,76.
A referência de 68 pontos vem de trabalhos de 2009–2011: citar via uma fonte
recente que a use ou apresentar o SUS sem o ponto de corte (média e desvio
bastam) — decidir com o orientador.
