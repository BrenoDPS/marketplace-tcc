# Capítulo 6. Discussão e considerações finais (rascunho)

> Rascunho para o grupo passar ao Word, na estrutura do Sumário do Report 6.
> Fontes: `docs/tese-rastreabilidade.md` (§§6 e 8), Cap. 5 do Report 6 e
> `docs/tcc/ajustes-versao-final.md`. Cada número já aparece no Cap. 5; nenhum é
> novo aqui. O teste de usabilidade **não** será feito (decisão do grupo com o orientador,
> 02/11): fica como limitação na §6.2 e como trabalho futuro no item a) da §6.4. v2 (02/11): pontos de `analise-app-x-monografia.md` (C1, C2, C4, C5) e o
> tamanho das respostas medido em `de-para-metricas.md` §10.

## 6 DISCUSSÃO E CONSIDERAÇÕES FINAIS

Este capítulo interpreta os resultados do Capítulo 5 à luz do problema e dos
objetivos definidos na Introdução. Primeiro, discutem-se as relações de
compromisso assumidas no projeto e a aderência do artefato aos objetivos e aos
critérios de aceitação. Em seguida, são apresentadas as limitações e as ameaças à
validade dos resultados, a conclusão do trabalho e os trabalhos futuros.

### 6.1 DISCUSSÃO

#### 6.1.1 Relação de compromisso no projeto

Toda decisão relevante do projeto trocou um benefício por um custo declarado. As
principais estão reunidas a seguir.

**Contrato tipado em dois lados.** A Server-Driven UI concentra no servidor a
decisão sobre o que aparece na tela, mas exige que o contrato exista duas vezes:
em Pydantic, no backend, e em TypeScript, no frontend. A duplicação é o preço do
desacoplamento. O projeto não a eliminou; tornou a divergência detectável, com
testes que comparam tipos de blocos, tipos de ações e campos de cada bloco em
todos os níveis. Um contrato genérico, com campos livres, evitaria a duplicação,
mas deixaria o erro aparecer só na tela do usuário. O custo do contrato na rede
é pequeno: as telas medidas ocupam de 3 a 13 KB de JSON, ou de 1,5 a 4,3 KB
comprimidos.

**Proximidade em vez de rota.** A distância é calculada em linha reta entre
centroides de prefixos de CEP e corrigida por um fator de circuidade. Uma rota
real por requisição seria mais precisa, mas acrescentaria latência e uma
dependência externa ao caminho de cada tela. A comparação com o OSRM mostrou que
a aproximação erra 8,7% e preserva a escolha do vendedor mais próximo em 86,5%
das decisões. Para comparar vendedores, que é o uso do sistema, a precisão obtida
é suficiente; para informar a emissão de uma entrega específica, não é, e por
isso a interface apresenta os valores como estimativas.

**Selo por distância, e não por emissão.** O selo de logística verde usa um
limite de 100 km, simples de comunicar e de verificar pelo usuário. A escolha tem
um efeito colateral: um produto pesado a 99 km recebe o selo, e um produto leve a
101 km, não. Um selo por emissão relativa seria mais fiel ao impacto, mas mais
difícil de explicar em uma etiqueta. O trabalho optou pela comunicação clara e
exibe a emissão estimada ao lado do selo, para que o usuário compare.

**Proximidade antes do preço.** A regra de escolha da oferta prioriza a menor
distância e só usa o preço para desempatar ofertas praticamente equidistantes (até
1% da menor distância). O comparador de origens mostrou um caso que essa regra
decide contra o comprador: para o mesmo produto e o mesmo CEP, a oferta escolhida
custa R$ 337,69 a 22 km, enquanto outra, a 28 km, custa R$ 130,00 e emite apenas
0,4 g a mais. A regra é coerente com a proposta do trabalho, mas não é a única
defensável. Sobre as compras reais, o desempate por preço já muda a escolha em
12,7% dos itens, reduz o preço em R$ 6,11 na mediana e mantém o CO₂ evitado em
9,8%. Ampliar a tolerância, por exemplo tratando como empate diferenças de emissão
menores que 1 g, reduziria casos como o citado, ao custo de parte do benefício
ambiental. Como a diferença de preço é visível no comparador, a decisão final
continua com o usuário. O mesmo vale para a sugestão de troca no checkout, que
propõe outro produto da mesma categoria vindo de mais perto. Na primeira versão,
a regra escolhia apenas a maior economia: no caso usado na demonstração, sugeria
evitar 4,58 g de CO₂ ao custo de R$ 142,00 a mais, troca que dificilmente seria
aceita. A versão final só sugere substitutos até 20% mais caros que o item,
abrindo mão de parte da economia possível em troca de sugestões plausíveis.

**Eficiência e equidade regional.** A recomendação de proximidade rende mais onde
já há mais vendedores. Nos itens com alternativa, ela evitaria 23,5% da emissão
em SP e 3,7% na BA, e SP responde por 42% de todo o CO₂ evitado. No outro
extremo, nenhum comprador do PA tinha vendedor a menos de 100 km. A regra, por
construção, beneficia as regiões já bem servidas; reduzir a emissão das compras
do Norte e de parte do Nordeste dependeria de abrir oferta nessas regiões, e não
apenas de recomendar melhor.

**Personalização regional, e não individual.** Sem autenticação nem histórico, o
sistema conhece apenas o CEP do comprador. A vitrine se adapta à UF, pela
categoria com maior lift regional, e não à pessoa. Essa escolha evitou um
histórico sintético e não teve custo de desempenho, mas limita o alcance da
personalização: 15 das 27 UFs não têm volume suficiente e recebem a vitrine geral.

**Dados estáticos em memória e cache de respostas.** Os centroides de CEP e o
contexto regional ficam em memória, e as telas da página inicial ficam no Redis
por uma hora. As duas decisões reduzem o custo por requisição, e o Redis foi
decisivo a partir de 250 usuários. Em troca, o sistema passa a depender de um
procedimento operacional: recarregar a base exige reiniciar a API e limpar o
cache, ou a tela mostrará dados antigos. Em um catálogo estático como o da Olist,
o custo é baixo; em um catálogo vivo, exigiria invalidação por evento.

**Amostra na aplicação, base completa nas análises.** A aplicação usa uma amostra
de 60.636 itens, e as análises de logística verde usam a base completa. A
separação mantém a aplicação leve e as análises representativas, mas exige que o
leitor não confunda os dois universos, razão pela qual o Capítulo 5 os apresenta
separadamente.

#### 6.1.2 Aderência aos objetivos e critérios de aceitação

O Quadro 1 relaciona cada objetivo específico à evidência obtida.

Quadro 1 – Aderência aos objetivos específicos

| Objetivo específico | Evidência | Situação |
|---|---|---|
| a) Arquitetura SDUI orientada a contexto, sem depender de atualizações do front-end | Doze componentes descritos pelo servidor; cinco mutações do contrato refletidas na tela sem nova compilação, injetadas na resposta e produzidas pelo próprio servidor; componentes desconhecidos ignorados sem interromper a tela | Atendido |
| b) Engine de pegada de carbono baseada em atividade | Motor em cadeia (circuidade, última milha por van, transferência por caminhão pesado, massa cobrável) com fatores do GLEC; testes de unidade, conversão e monotonicidade; erro de distância de 8,7% contra o OSRM; parcela evitada estável (9,5% a 10,0%) sob variação dos parâmetros; fator de caminhão conferido com o do Programa Brasileiro GHG Protocol (diferença líquida de cerca de 5%) | Atendido como estimativa; sem validação contra dados de transportadora |
| c) Personalização integrada a dados logísticos, identificando compras locais | Vitrine regional em 12 das 27 UFs; selo, distância e emissão por oferta; comparador de origens; sugestão de troca no checkout; potencial de 9,8% de redução nos itens com alternativa (0,9% do total), concentrado nas regiões com mais vendedores; comparador que apresenta a redução relativa prevista na Seção 3.2 | Atendido no nível regional; efeito sobre o comportamento do usuário não medido |
| d) Avaliar desempenho e flexibilidade | Protocolo de 27 ensaios em três cargas e três estados de cache; controle repetido no código final; mutação do contrato; medição no navegador (página inicial pintada em 140 ms, telas pedidas ao servidor em até 150 ms) | Atendido, com a meta de 200 ms cumprida até 250 usuários com cache e não cumprida no p95 agregado com 1.000 usuários |

Fonte: Elaborado pelos autores (2026).

Os quatro grupos de critérios de aceitação definidos na Seção 4.1.2 foram
verificados. Os cálculos de distância, massa e emissão passaram nos testes com
entradas controladas. A ordenação de ofertas, remessas e alternativas é coberta
por testes de unidade e pela regra única de escolha de oferta, usada pela vitrine,
pelo detalhe e pelo checkout. A geração e a interpretação do contrato são
verificadas nos dois lados e por testes de navegador. A jornada completa é
percorrida por testes automatizados no navegador, e o comportamento sob carga foi
medido pelo protocolo da metodologia.

O critério de desempenho merece uma leitura separada. A meta de tempo de resposta
inferior a 200 ms foi definida como experimental, e os resultados mostram que ela
depende do nível de concorrência. Com 50 usuários, foi cumprida mesmo sem o cache
de respostas; com 250, só com ele; com 1.000, a rota em cache ficou no limite da
meta, mas as telas de detalhe e de checkout, que não passam pelo cache, formaram
fila e elevaram o p95 agregado para cerca de 3 s. O resultado não invalida a
arquitetura, mas indica o próximo gargalo: estender o cache a essas telas ou
distribuir a carga entre mais processos.

### 6.2 LIMITAÇÕES E AMEAÇAS À VALIDADE

As limitações são agrupadas pelo tipo de validade que afetam.

**Validade de construto.** A emissão de CO₂ é uma estimativa de modelo, e não uma
medição. A ordem de grandeza foi conferida contra o fator brasileiro de caminhão
do Programa Brasileiro GHG Protocol (diferença líquida de cerca de 5% na
distância mediana), mas não há referência brasileira independente para a van da
última milha. Os fatores são médias internacionais do GLEC, e não fatores da frota
brasileira, e a Olist não informa veículo, rota, ocupação nem consumo. O selo
mede distância, e não emissão. As modalidades expressa e verde são cenários
declarados sobre a linha de base, sustentados na direção, mas não no valor, pela
literatura. No desempenho, a ferramenta de carga mede a resposta completa, um
limite superior do tempo até o primeiro byte.

**Validade interna.** API, banco, cache e gerador de carga dividiram o mesmo
computador, e o gerador saturou em um dos ensaios, que foi refeito. Treze ensaios
foram descartados porque o computador funcionou na bateria. Com três repetições,
a dispersão na carga máxima é alta. O protocolo completo foi executado antes das
últimas mudanças de regra; o controle no código final cobriu apenas o cenário de
250 usuários.

**Validade externa.** A base é histórica (2016 a 2018): a presença de um vendedor
indica que a venda ocorreu, e não que a oferta estaria disponível hoje. As
distâncias são calculadas entre centroides de prefixos de CEP, e não entre
endereços, e o OSRM representa a rota mais rápida de carro, e não a da
transportadora. A amostra da aplicação favorece os produtos mais vendidos e não
representa as proporções do catálogo inteiro. Sem nome de produto na base, a
interface identifica cada item pela categoria, o que limita a avaliação da
experiência de compra. Os resultados de carga comparam
configurações entre si em uma máquina, e não representam um serviço distribuído.

**Validade de conclusão.** O CO₂ evitado é contrafactual: supõe que todos os
compradores seguiriam a recomendação e que a oferta mais próxima estaria
disponível. A concordância de 86,5% entre linha reta e rota vem de 37 decisões,
com intervalo de confiança de 95% entre 72% e 94%. Os limiares da personalização
regional protegem contra ruído, mas não constituem um teste de significância.

**Validação com pessoas.** O trabalho não avaliou se os usuários compreendem o selo e a estimativa de emissão,
nem se mudariam de vendedor por causa deles. O escopo não incluiu estudo com
participantes: a avaliação ficou restrita a verificações técnicas e automatizadas.
As conclusões sobre o potencial de redução dependem dessa hipótese.

### 6.3 CONCLUSÃO

O trabalho partiu de dois problemas do comércio eletrônico: a rigidez de
interfaces que dependem de novas versões do cliente para mudar e a falta de
informação ambiental no momento da compra. Para tratá-los em conjunto, foi
desenvolvido um marketplace sobre o conjunto de dados público da Olist, no qual o
servidor compõe a interface por meio de uma engine de Server-Driven UI e cada
oferta carrega distância, selo e emissão estimada.

O objetivo geral foi atingido no escopo de um protótipo. A arquitetura mostrou que
a composição da tela pode mudar no servidor sem nova compilação do cliente e que
o cliente tolera componentes desconhecidos e dados incompletos. O motor de
emissão, baseado em atividade, produziu estimativas internamente consistentes e
uma aproximação de distância validada contra rotas reais. A personalização
contextual foi integrada à logística verde no nível regional, e a análise da base
completa mostrou que a recomendação de vendedores mais próximos tem potencial de
reduzir 9,8% da emissão onde há alternativas, efeito que se dilui para 0,9% no
conjunto das compras. Sob carga, o cache de respostas foi a decisão que manteve
a aplicação dentro da meta até 250 usuários simultâneos.

Os resultados também delimitam a contribuição. O maior obstáculo à logística
verde observado na base não foi a falta de vendedores próximos, presentes para
94,7% dos compradores, mas a falta de alternativas para o mesmo produto, que
ocorre em 12,8% dos itens. Uma interface pode tornar a escolha local visível e
comparável, mas o efeito depende de haver o que escolher e de o comprador decidir
a partir da informação apresentada, e hoje se concentra nas regiões que já
contam com mais vendedores. Nesse sentido, o artefato demonstra a
viabilidade técnica da abordagem e deixa a medição do efeito sobre o
comportamento como o passo seguinte.

### 6.4 TRABALHOS FUTUROS

Os itens a seguir estão ordenados do que mais afetaria as conclusões para o que
menos afetaria.

a) **Medir o efeito da recomendação com usuários**, por teste A/B ou estudo de
preferência, para substituir o CO₂ evitado contrafactual por um efeito observado.

b) **Personalização por pessoa**, com autenticação e pedidos persistidos,
separando a base de referência da Olist da base da aplicação; o contexto regional
passaria a ser o ponto de partida para quem ainda não tem histórico.

c) **Significância do contexto regional**, por *bootstrap* da participação de
cada categoria por UF, reavaliando os limiares de volume e de lift.

d) **Selo por emissão relativa**, comparando a emissão da oferta com a mediana da
categoria, para corrigir o caso do produto pesado próximo e do leve distante.

e) **Regra de oferta com tolerância por emissão**, tratando como equivalentes
ofertas cuja diferença de CO₂ seja menor que a incerteza do modelo, e medindo o
custo ambiental dessa ampliação com a mesma análise do Capítulo 5; na sugestão
de troca do checkout, um limite de diferença de preço.

f) **Distância rodoviária pré-calculada**, com uma matriz do OSRM entre os
prefixos de vendedores e de compradores, consultada em memória, ou um fator de
circuidade por faixa de distância estimado com amostra maior.

g) **Fatores de emissão da frota brasileira**, por tipo de veículo, quando houver
inventário nacional com o mesmo recorte do GLEC.

h) **Escala horizontal com cache**, repetindo o protocolo com vários processos e
cache ligado, com o gerador de carga em outra máquina, e estendendo o cache às
telas de detalhe e de checkout.

i) **Lado do vendedor**, atendendo a persona do microempreendedor com um painel da
pegada das próprias entregas e a sugestão de onde manter estoque.

j) **Versionamento de componentes**, com roteamento entre versões quando houver
duas versões vivas do mesmo bloco e clientes antigos a atender.

k) **Instrumentação permanente**, com contagem de consultas e tempo por
requisição atrás de uma opção de diagnóstico, para que regressões de desempenho
como a encontrada durante o desenvolvimento sejam detectadas por teste.
