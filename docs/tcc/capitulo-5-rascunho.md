# Capítulo 5. Resultados

## 5 RESULTADOS

Este capítulo apresenta os resultados obtidos com a implementação descrita no
capítulo anterior. A análise foi organizada para responder a uma pergunta
central: em que medida o artefato construído consegue combinar personalização
contextual, escolha de ofertas próximas, estimativa de impacto ambiental e
flexibilidade de apresentação sem comprometer o funcionamento da jornada de
compra?

Os resultados foram divididos em duas dimensões. A primeira é quantitativa e
reúne evidências sobre a cobertura dos dados, o comportamento do motor de
cálculo, a aproximação da distância rodoviária, o potencial estimado de redução
de emissões e o desempenho da aplicação sob carga. A segunda é
qualitativo-estrutural e examina aquilo que não pode ser resumido por uma única
métrica, como a capacidade de alterar a árvore de componentes, a tolerância a
blocos desconhecidos e a correspondência entre o contrato produzido pelo
backend e o contrato interpretado pelo frontend.

Essa separação não significa que as duas dimensões sejam independentes. Os
resultados quantitativos dependem do tratamento dos dados e das regras
implementadas no backend, enquanto os resultados estruturais indicam se essas
regras podem ser apresentadas e alteradas sem reescrever a interface. Por isso,
cada seção apresenta primeiro o procedimento de avaliação, depois os valores
observados e, por fim, uma interpretação relacionada aos objetivos do trabalho.

É importante distinguir três tipos de resultado apresentados ao longo do
capítulo. Alguns valores são observações diretas do conjunto de dados, como a
quantidade de pedidos e a distância dos casos avaliados. Outros são resultados
de um modelo, como a emissão de CO₂ calculada a partir de distância e massa.
Há ainda resultados contrafactuais, como a emissão que seria obtida caso o
comprador tivesse escolhido uma oferta alternativa. Essa distinção impede que
uma estimativa seja apresentada como medição operacional.

### 5.1 RESULTADOS QUANTITATIVOS

#### 5.1.1 Qualidade e cobertura dos dados

O primeiro resultado diz respeito à capacidade do conjunto de dados da Olist de
sustentar as análises propostas. O conjunto completo reúne 112.650 itens
vendidos, associados a 95.828 compradores identificados por
`customer_unique_id` e a 3.095 vendedores. A quantidade de itens é relevante
porque as análises de concentração regional e de CO₂ evitado não foram feitas
somente sobre o catálogo operacional utilizado pela demonstração. Elas foram
realizadas sobre o conjunto mais amplo disponível para preservar a capacidade
de observar padrões de distância, localização e escolha de vendedor.

Entretanto, nem todos os itens possuem as informações necessárias ao cálculo
logístico. Após o cruzamento entre os CEPs de clientes e vendedores e a tabela
de geolocalização, 112.096 itens apresentaram centroides disponíveis nas duas
pontas da entrega. Esse número representa a parcela do conjunto em que foi
possível estimar uma distância entre comprador e vendedor. A diferença em
relação ao total não deve ser interpretada como erro do modelo de distância,
mas como uma limitação da cobertura espacial da base original.

O processo de carga utilizado pela aplicação possui uma finalidade diferente.
Ele prepara uma amostra operacional suficientemente ampla para alimentar a
API, o frontend e os ensaios de jornada. Foram processados 60.636 itens. Desse
total, 17 foram descartados por ausência de peso utilizável, 144 por falta de
CEP geolocalizado do vendedor e 183 por falta de CEP geolocalizado do cliente.
Ao final, 60.292 itens foram persistidos, juntamente com 53.114 pedidos, 7.356
ofertas e 12.933 centroides de CEP.

**Tabela 5.1. Funil de preparação da base operacional.** A tabela deve
apresentar a quantidade de registros em cada etapa, distinguindo o total
processado, as exclusões por motivo e os registros persistidos.

| Etapa da preparação | Quantidade |
|---|---:|
| Itens processados pelo ETL | 60.636 |
| Itens sem peso utilizável | 17 |
| Itens sem geolocalização do vendedor | 144 |
| Itens sem geolocalização do cliente | 183 |
| Itens persistidos | 60.292 |
| Pedidos persistidos | 53.114 |
| Ofertas derivadas | 7.356 |
| Centroides de CEP | 12.933 |

Os descartes somam 344 itens, aproximadamente 0,57% dos registros processados.
Essa proporção é pequena no contexto da amostra, mas a informação é
metodologicamente importante. O sistema não atribui coordenadas padrão a uma
entrega sem geolocalização e não calcula emissões com massa inexistente. Assim,
o filtro reduz o universo de observação, mas evita transformar ausência de
dado em uma estimativa artificialmente precisa.

O tratamento das ofertas produziu um efeito particularmente importante. Em uma
amostragem simples por linha de pedido, um produto com vários vendedores poderia
aparecer somente com o vendedor associado à linha sorteada. O teste de
amostragem identificou 474 produtos com múltiplos vendedores entre 528 produtos
que seriam truncados dessa maneira. A etapa posterior de complementação foi,
portanto, necessária para preservar as alternativas de oferta e permitir uma
comparação significativa entre distância e preço.

Esse resultado influencia diretamente a interpretação das seções seguintes.
Uma avaliação de proximidade só é representativa quando há mais de uma
possibilidade de origem para o mesmo produto. Se a amostragem eliminasse as
ofertas alternativas, o sistema pareceria escolher o vendedor mais próximo
simplesmente porque não teria outra opção. Ao preservar as combinações de
produto e vendedor, o ETL cria as condições para que a regra de escolha seja
avaliada.

**Figura 5.1. Funil de preparação dos dados.** A figura deve representar o
fluxo desde o conjunto completo e a amostra operacional até os itens
persistidos, mostrando visualmente os três motivos de descarte e as tabelas
derivadas. Fonte: elaborada pelos autores a partir dos resultados do ETL.

Os centroides utilizados pelo sistema são obtidos a partir das coordenadas
disponíveis para os prefixos de CEP. Eles não representam o endereço exato de
um comprador ou de um vendedor, mas uma posição representativa daquele
prefixo. Essa escolha permite que o sistema opere sem armazenar ou expor
endereços individuais e torna viável manter os centroides em memória durante a
execução da API. Em contrapartida, introduz uma incerteza que deve acompanhar
qualquer interpretação sobre quilômetros percorridos ou emissões.

Outra diferença relevante está entre disponibilidade histórica e disponibilidade
comercial. O conjunto da Olist registra transações ocorridas em determinado
período, mas não funciona como um inventário atualizado. A presença de um
vendedor associado a um produto demonstra que essa relação existiu na base,
não que ela estaria disponível em uma loja real no instante da recomendação.
As análises devem ser lidas, portanto, como estudos sobre o potencial de uma
regra de seleção aplicada a dados históricos.

O primeiro objetivo específico do trabalho era desenvolver uma experiência
contextual. Para esse objetivo, a base mostrou cobertura suficiente para
associar compradores, vendedores, categorias e localizações em escala
compatível com o protótipo. O segundo objetivo, relacionado à logística verde,
também pôde ser investigado, mas com a ressalva de que as estimativas dependem
da disponibilidade dos centroides e da massa cobrável. A cobertura alcançada
não elimina as limitações do dataset, mas oferece um universo observável para
comparar escolhas e cenários.

#### 5.1.2 Verificação funcional do motor de cálculo

Antes de avaliar os resultados agregados, foram executados testes controlados
para verificar as funções que sustentam as decisões logísticas. Essa etapa
teve a finalidade de conferir se as fórmulas e as regras de ordenação
produziam os resultados esperados em casos conhecidos. Ela não substitui uma
validação externa do modelo de emissões, mas reduz a possibilidade de que
resultados posteriores sejam explicados por erros elementares de unidade,
conversão ou ordenação.

Os testes cobriram a distância Haversine, a conversão da distância geodésica
para uma aproximação rodoviária, o cálculo do peso cubado, a separação entre
transferência e última milha, a aplicação dos fatores de emissão, a
monotonicidade da emissão e a escolha de ofertas. Também foram verificados os
casos em que não há dados suficientes para exibir selo ou estimativa de
emissão.

Um caso de referência utilizou distância de 100 km e massa de 1.000 g. O motor
produziu 0,021194 kg de CO₂e. Em um segundo caso, com distância de 10 km e
massa de 2.500 g, o resultado foi de 0,022865 kg de CO₂e. Os valores não devem
ser interpretados como fatores universais de emissão para qualquer entrega.
Eles são saídas da parametrização adotada no trabalho e servem para demonstrar
que o cálculo é sensível simultaneamente à distância, à massa e à divisão entre
os trechos do transporte.

O teste de massa também confirmou a aplicação do peso cubado. Para um volume
de 60.000 cm³, a conversão adotada resulta em 10.000 g. Em uma remessa com
mais de um item, a cubagem é aplicada ao volume consolidado. Um caso controlado
produziu 10.166,7 g de peso cubado, enquanto a soma da cubagem calculada
separadamente por item produziria 15.000 g. A diferença mostra por que a ordem
da operação importa: consolidar o volume antes da conversão evita superestimar
a massa utilizada pelo cálculo.

**Tabela 5.2. Casos controlados do cálculo de CO₂ e massa.** A tabela deve
apresentar as entradas, a saída esperada e a finalidade de cada caso.

| Caso | Entrada principal | Resultado observado | Finalidade |
|---|---|---:|---|
| Emissão unitária 1 | 100 km e 1.000 g | 0,021194 kg CO₂e | Verificar conversão de distância e massa |
| Emissão unitária 2 | 10 km e 2.500 g | 0,022865 kg CO₂e | Verificar a composição dos trechos |
| Peso cubado | 60.000 cm³ | 10.000 g | Verificar a relação volume e massa |
| Cubagem consolidada | Remessa com múltiplos itens | 10.166,7 g | Evitar soma incorreta por item |

A emissão também apresentou crescimento monotônico nos testes. Ao aumentar a
distância ou a massa, a saída não diminuiu. Essa propriedade é simples, mas
fundamental para a interpretação da interface: uma alternativa apresentada
como mais distante ou mais pesada não pode resultar em menor emissão apenas por
um erro de ordenação ou de unidade.

O motor utiliza fator de circuidade de 1,345 para aproximar o percurso
rodoviário a partir da distância em linha reta. A última milha considera um
trecho de até 15 km com fator de emissão de van, enquanto o trecho restante
utiliza o fator do caminhão pesado. Foram verificados os fatores de 0,092 e
0,680 kg/(t·km), respectivamente. A existência de testes para cada parte não
significa que o modelo represente todas as operações de uma transportadora,
mas torna explícita a cadeia que produz a estimativa exibida.

A regra de ofertas também foi submetida a casos controlados. A menor distância
é priorizada. Quando duas distâncias se encontram dentro de 1% da menor
distância, considerando um piso de 1 km para a tolerância, o preço passa a ser
utilizado como desempate. Essa regra evita que uma diferença geográfica muito
pequena produza uma escolha significativamente mais cara, sem permitir que uma
oferta distante seja escolhida apenas por ter preço menor.

Esse comportamento é importante para a coerência entre vitrine, detalhe e
checkout. As três etapas da jornada precisam partir da mesma regra, caso
contrário o comprador poderia visualizar um vendedor na Home e receber outro
no checkout sem que houvesse uma explicação. Os testes controlados verificam a
regra em situações isoladas. A análise do conjunto histórico, apresentada mais
adiante, verifica o seu potencial quando existem alternativas reais na base.

**Figura 5.2. Verificação do motor de cálculo.** A figura deve apresentar um
diagrama ou quadro de casos de teste, relacionando distância, massa, cubagem,
emissão e escolha da oferta. Fonte: elaborada pelos autores.

Os testes funcionais aprovados demonstram consistência interna, não precisão
externa. Para validar externamente os fatores de emissão seriam necessários
dados operacionais de transportadoras, informações sobre veículos, rotas,
ocupação, combustível e condições de tráfego. Esses dados não fazem parte da
Olist e, por isso, o resultado desta subseção deve ser entendido como
verificação da implementação do modelo adotado.

#### 5.1.3 Acurácia da distância: Haversine e OSRM

A comparação entre Haversine e OSRM foi realizada para verificar se a distância
em linha reta, utilizada como base do sistema, preserva uma aproximação
razoável do deslocamento rodoviário. A análise foi planejada para não avaliar
somente o erro absoluto. Em um marketplace, interessa também saber se a
ordenação dos vendedores muda quando a distância é calculada por uma rota.
Uma aproximação pode não reproduzir o número exato de quilômetros e, ainda
assim, conservar a decisão relativa sobre qual oferta está mais próxima.

Foram selecionados 100 pares reais, distribuídos em cinco faixas de distância,
com 20 observações em cada faixa. Para cada par, foram comparadas três
medidas: a distância Haversine sem correção, a distância Haversine multiplicada
pelo fator de circuidade 1,345 e a distância obtida pelo OSRM. O serviço foi
consultado com o perfil de condução de veículos e os pares foram formados a
partir dos centroides de CEP utilizados pela aplicação.

**Tabela 5.3. Comparação agregada entre Haversine, Haversine corrigida e
OSRM.** A tabela deve apresentar o erro absoluto médio, o erro percentual
absoluto médio, o viés e a correlação de Spearman.

| Medida | Haversine crua | Haversine corrigida |
|---|---:|---:|
| MAE em relação ao OSRM | 248,9 km | 83,2 km |
| MAPE em relação ao OSRM | 21,9% | 8,7% |
| Viés mediano | Não corrigido | +6,2% após correção |
| Correlação de Spearman | 0,997 | 0,997 |

O erro absoluto médio da Haversine crua foi de 248,9 km, com MAPE de 21,9%.
Depois da aplicação do fator de circuidade, o MAE caiu para 83,2 km e o MAPE
para 8,7%. A redução indica que a distância em linha reta subestima de maneira
relevante o percurso rodoviário em parte dos casos, enquanto a correção
aproxima a estimativa da rota observada pelo OSRM.

A razão entre a rota e a linha reta apresentou mediana de 1,27, com percentis
10 e 90 entre 1,16 e 1,41. O fator 1,345, portanto, não reproduz cada rota
individualmente. Ele funciona como uma aproximação central para o conjunto
observado. O viés mediano de +6,2% após a correção mostra que a estimativa
corrigida tende a ficar acima do OSRM nesse conjunto, mas em magnitude muito
menor do que a Haversine crua.

A correlação de Spearman foi de 0,997, o que indica preservação muito elevada
da ordenação dos pares. Esse resultado deve ser lido com cuidado. Correlação
alta não significa que as distâncias sejam intercambiáveis em qualquer uso,
nem que a aproximação consiga representar a rota real de uma transportadora.
Ela mostra que, para os pares observados, os casos mais longos segundo uma
medida tendem a permanecer entre os mais longos segundo a outra.

Para avaliar a consequência da aproximação na escolha da oferta, foi realizada
uma segunda análise com grupos inteiros de ofertas. Foram obtidas 37 decisões
reais, totalizando 102 pares. A preservação dos grupos foi importante porque
comparar somente um par por decisão poderia esconder a existência de uma
terceira ou quarta oferta mais próxima.

O vendedor mais próximo pela Haversine também foi o mais próximo pelo OSRM em
86,5% das decisões. Em 91,0% das 111 comparações de pares, a ordenação foi
mantida. Foram identificadas cinco divergências. A diferença mediana entre as
escolhas foi de 2,0 km e o pior caso apresentou custo adicional de 6,4 km, ou
2,1% da rota.

**Figura 5.3. Relação entre distância corrigida e distância OSRM.** A figura
deve apresentar um gráfico de dispersão com a linha de referência, além de
destacar as cinco divergências de ordenação. Fonte: resultado da comparação
Haversine e OSRM.

Os valores sugerem que a aproximação utilizada pelo sistema é suficiente para
preservar a decisão de proximidade na maior parte dos casos analisados. Isso
fortalece a escolha de manter o cálculo por centroides no caminho quente da
API, sem consultar um serviço de roteamento para cada produto. A decisão não
decorre apenas de uma preocupação de desempenho. A comparação mostra que a
aproximação possui comportamento consistente no conjunto amostrado.

Ainda assim, o script da análise compara a ordenação por distância. Ele não
executa integralmente a função de escolha de oferta utilizada pela aplicação,
que considera o preço entre ofertas cuja distância esteja dentro da tolerância.
Por isso, o resultado de 86,5% deve ser descrito como coincidência do vendedor
mais próximo, e não como equivalência total da decisão comercial. Uma
comparação completa entre as duas regras exigiria aplicar também o critério de
preço às distâncias OSRM.

A análise não encontrou pares sem rota. Os pontos foram ajustados à via mais
próxima para a consulta ao OSRM, e o deslocamento desse ajuste teve mediana de
14 m e máximo de 150 m. A distância desse encaixe não foi somada à rota final.
Esse procedimento reduz problemas de consulta causados por centroides que não
estão exatamente sobre uma via, mas também introduz uma pequena transformação
na entrada do serviço.

Há limitações adicionais. O OSRM utiliza dados do OpenStreetMap e o perfil
`driving`, calculando a rota mais rápida de carro. O resultado não representa
necessariamente a rota efetivamente escolhida por uma transportadora, que pode
considerar centros de distribuição, restrições de carga, janelas de entrega e
consolidação de pedidos. Além disso, os dois métodos partem de centroides de
CEP. A validação, portanto, não transforma o selo de proximidade em uma
garantia de distância operacional.

O resultado mais adequado para a metodologia é interpretar o fator 1,345 como
uma aproximação empiricamente apoiada para o conjunto estudado. Ele melhora o
erro da distância e preserva a ordenação na maioria das decisões, mas deve ser
acompanhado das ressalvas sobre centroides, serviço público e perfil de rota.
Essa formulação é mais precisa do que afirmar que o sistema calcula a rota da
entrega.

#### 5.1.4 Potencial estimado de redução de emissões

A análise de concentração regional foi realizada sobre o conjunto completo de
itens com informações espaciais. Seu objetivo foi verificar se a base apresenta
oportunidades para uma recomendação de vendedor próximo e se essa oportunidade
é distribuída de maneira ampla ou concentrada em poucos casos.

Em 36,3% dos itens, comprador e vendedor estavam na mesma UF. Quando o critério
é restringido a uma distância inferior a 100 km, a proporção de compras locais
cai para 18,7%. A distância mediana observada foi de 432 km. Esses valores
mostram que proximidade estadual e proximidade quilométrica são conceitos
diferentes. Uma compra pode ocorrer dentro da mesma UF e ainda representar um
deslocamento significativo.

Apesar da baixa proporção de compras já realizadas abaixo de 100 km, 94,7% dos
compradores possuíam algum vendedor a menos de 100 km. O dado revela uma
diferença entre a existência de uma alternativa próxima e a escolha efetiva
registrada no histórico. Essa diferença sustenta a hipótese de que uma
interface contextual pode tornar visível uma possibilidade que não aparece
quando o produto é ordenado apenas por preço, catálogo ou ordem de consulta.

**Tabela 5.4. Concentração regional e disponibilidade potencial de proximidade.**

| Indicador | Resultado |
|---|---:|
| Itens na mesma UF | 36,3% |
| Compras abaixo de 100 km | 18,7% |
| Distância mediana | 432 km |
| Compradores com algum vendedor abaixo de 100 km | 94,7% |

O segundo estudo foi direcionado aos casos em que o mesmo produto possuía mais
de uma oferta. Foram identificados 14.367 itens com alternativa de vendedor,
equivalentes a 12,8% do total analisado. Em 48,3% desses casos, o comprador já
havia escolhido o vendedor mais próximo. Nos demais, existia uma diferença
entre a escolha histórica e a recomendação construída a partir da proximidade.

A distância mediana das compras nesses casos foi de 437 km. Quando aplicada a
regra de recomendação, a distância mediana caiu para 330 km. A diferença de
107 km não deve ser generalizada para todas as compras da Olist, pois somente
os itens com alternativa foram incluídos nessa comparação. Dentro desse
recorte, porém, ela indica que a regra possui potencial para reduzir a
distância de origem sem exigir a criação de um novo produto ou vendedor.

O modelo calculou 2.601,3 kg de CO₂e para as escolhas históricas e 2.347,1 kg
de CO₂e para as escolhas recomendadas. A diferença foi de 254,2 kg de CO₂e,
correspondente a uma redução estimada de 9,8% dentro dos casos que possuíam
alternativa e dados mensuráveis. Quando o cálculo é comparado ao conjunto
mensurável inteiro, que totaliza 26.934,9 kg de CO₂e, a redução equivalente é
de 0,9%.

**Tabela 5.5. Comparação entre escolha histórica e recomendação de proximidade.**

| Indicador | Escolha histórica | Recomendação |
|---|---:|---:|
| Distância mediana | 437 km | 330 km |
| Emissão estimada | 2.601,3 kg CO₂e | 2.347,1 kg CO₂e |
| Diferença de emissão | 254,2 kg CO₂e | 254,2 kg CO₂e |
| Redução dentro dos casos com alternativa | 9,8% | 9,8% |
| Redução no conjunto mensurável inteiro | 0,9% | 0,9% |

Os resultados apresentam um trade-off econômico moderado, mas não uniforme. A
oferta recomendada era mais barata em 43,3% dos casos, tinha o mesmo preço em
6,3% e era mais cara em 50,4%. A diferença mediana de preço foi de R$ 0,01.
Essa última medida indica que a escolha por proximidade, na mediana, não
exigiria um aumento expressivo de preço, embora metade dos casos apresentasse
alguma diferença desfavorável.

O resultado econômico é tão importante quanto o ambiental porque uma
recomendação sustentável precisa ser compreensível e aceitável no contexto da
compra. Se a redução de distância viesse acompanhada de um custo elevado na
maioria dos casos, o sistema deveria apresentar explicitamente essa troca ao
usuário. Neste conjunto, a distribuição foi equilibrada: a proximidade reduziu
o preço em uma parcela expressiva, mas também aumentou o preço em outra. Isso
reforça a necessidade de exibir distância, emissão e preço simultaneamente,
em vez de esconder a decisão sob um selo único.

**Figura 5.4. Distribuição do efeito da recomendação sobre distância, preço e
emissão.** A figura deve apresentar, preferencialmente, três distribuições ou
painéis: diferença de distância, diferença de preço e diferença de CO₂e entre
a escolha histórica e a recomendação. Fonte: análise de CO₂ evitado.

É necessário caracterizar esse resultado como contrafactual. O cálculo
pressupõe que o comprador poderia ter escolhido a oferta recomendada, que o
vendedor estaria disponível no momento da compra e que a modalidade de entrega
não mudaria. Ele também altera somente a origem da oferta. Não foram modelados
estoque, capacidade do vendedor, consolidação de carga, tipo de veículo ou
restrições de rota.

A diferença entre os denominadores também precisa ser explicitada. O conjunto
total possui 112.650 itens, 112.096 itens com centroides nas duas pontas e
112.070 compras mensuráveis no cálculo de CO₂. Cada exclusão decorre de um
requisito diferente, como disponibilidade de coordenadas, massa ou demais
campos necessários ao modelo. Na versão final do capítulo, recomenda-se
inserir uma tabela de reconciliação para mostrar a passagem entre esses três
universos e evitar que o leitor compare percentuais calculados sobre bases
distintas.

**Tabela 5.6. Reconciliação dos universos de análise.** A tabela deve
apresentar o total de itens, os itens com centroides e as compras efetivamente
mensuráveis no cálculo de CO₂, acompanhados dos critérios de exclusão.

| Universo | Quantidade | Critério |
|---|---:|---|
| Itens do conjunto completo | 112.650 | Registros de venda disponíveis |
| Itens com centroides nas duas pontas | 112.096 | Cliente e vendedor geolocalizados |
| Compras mensuráveis em CO₂ | 112.070 | Campos necessários ao modelo disponíveis |

O resultado responde positivamente, mas com limites, ao objetivo de investigar
logística verde. Há um conjunto amplo de compradores com alguma alternativa
próxima, a regra reduz a distância mediana nos casos comparáveis e o modelo
estima redução de emissão. Entretanto, a redução de 9,8% não representa todo o
dataset. A medida de 0,9% no universo mensurável é a referência mais adequada
para dimensionar o efeito sobre o conjunto completo, enquanto a medida de 9,8%
descreve o potencial concentrado nos itens com alternativas.

#### 5.1.5 Desempenho sob carga e efeito do cache

O desempenho foi avaliado por meio de uma jornada que combina Home contextual,
detalhe de produto e checkout. A escolha da jornada, em vez de uma chamada
isolada, aproxima o ensaio do uso esperado e permite observar as consultas,
composições e cálculos executados em sequência. O protocolo principal reuniu
27 ensaios válidos, com três repetições por célula experimental. Também foi
realizada uma bateria complementar com 12 ensaios válidos, depois de quatro
execuções invalidadas e refeitas.

Os resultados foram analisados em três estados do cache de respostas em Redis:
desligado, frio e aquecido. Cache desligado significa que a resposta não foi
obtida do Redis. Cache frio representa a primeira solicitação após a expiração
ou limpeza da entrada, e cache aquecido representa solicitações subsequentes
com a resposta disponível. Os centroides permanecem em memória no processo da
API e o PostgreSQL possui seu próprio comportamento de cache, portanto esses
estados não significam que todo o sistema esteja sem qualquer forma de
memória.

Em 50 usuários virtuais, o estado sem Redis apresentou p50 de 12,7 ms, p95 de
34,0 ms, vazão agregada de 24,8 requisições por segundo e nenhuma falha. Nesse
nível, o custo das consultas e da composição permaneceu baixo o suficiente
para que a ausência do cache de respostas não comprometesse a meta
experimental de tempo até o primeiro byte inferior a 200 ms.

Em 250 usuários virtuais, o p50 sem cache subiu para 173 ms e o p95 para
613 ms, com vazão de 111 requisições por segundo. Quando o cache estava
aquecido, o p50 caiu para 5,7 ms, o p95 para 24,7 ms e a vazão aumentou para
124 requisições por segundo. A diferença de vazão é menor do que a diferença
de latência, o que sugere que, nesse nível, o sistema ainda encontrava
capacidade de atender às requisições, embora algumas respostas sem cache já
apresentassem espera significativa.

Em 1.000 usuários virtuais, a diferença entre os estados tornou-se mais
acentuada. Sem cache, o p50 foi de 4.100 ms e o p95 de 14.000 ms, com vazão de
153 requisições por segundo e 0,21% de falhas. Com cache frio, o p50 foi de
93 ms e o p95 de 2.900 ms, com 401 requisições por segundo. Com cache
aquecido, os valores foram 95 ms de p50, 3.000 ms de p95 e 397 requisições por
segundo.

**Tabela 5.7. Desempenho agregado por concorrência e estado do cache.**

| Usuários virtuais | Estado | p50 | p95 | Vazão | Falhas |
|---:|---|---:|---:|---:|---:|
| 50 | Desligado | 12,7 ms | 34,0 ms | 24,8 req/s | 0% |
| 250 | Desligado | 173 ms | 613 ms | 111 req/s | Não registrada |
| 250 | Aquecido | 5,7 ms | 24,7 ms | 124 req/s | Não registrada |
| 1.000 | Desligado | 4.100 ms | 14.000 ms | 153 req/s | 0,21% |
| 1.000 | Frio | 93 ms | 2.900 ms | 401 req/s | Não registrada |
| 1.000 | Aquecido | 95 ms | 3.000 ms | 397 req/s | Não registrada |

Os resultados mostram que o cache desloca o ponto de inflexão do sistema. Sem
Redis, a vazão cresce de 24,8 para 153 requisições por segundo entre 50 e
1.000 usuários virtuais, mas a latência cresce de dezenas de milissegundos
para segundos. Com Redis, a vazão alcança aproximadamente 400 requisições por
segundo no maior nível de concorrência, enquanto o p50 permanece próximo de
100 ms. O ganho aproximado de vazão é de 2,6 vezes, comparando 153 com cerca
de 400 requisições por segundo.

Na Home do contexto `conscious_buyer`, o p95 com cache ficou em 190 ± 35 ms
no estado frio e 200 ± 26 ms no estado aquecido. Sem cache, o p95 chegou a
14.000 ms. Esse resultado sugere que a meta de 200 ms foi alcançada nos
cenários de cache avaliados, embora o intervalo de variação e as condições do
ensaio não permitam afirmar que ela seja garantida para qualquer carga.

**Figura 5.5. Latência e vazão em função da concorrência.** A figura deve
apresentar a evolução do p50, p95 e da vazão para 50, 250 e 1.000 usuários
virtuais, com séries separadas para cache desligado, frio e aquecido.

A bateria complementar avaliou o efeito de quatro trabalhadores da API. Sem
cache, quatro workers atingiram aproximadamente 284 requisições por segundo,
um ganho de cerca de 1,7 vezes em relação às 153 requisições por segundo de um
worker. Esse ganho é relevante, mas inferior ao obtido pela camada de
respostas em Redis no cenário de alta concorrência. O resultado indica que a
paralelização ajuda a distribuir o trabalho, mas não substitui a redução de
operações repetidas proporcionada pelo cache.

**Tabela 5.8. Comparação entre aumento de trabalhadores e uso do cache.**

| Configuração | Vazão aproximada |
|---|---:|
| Um worker, sem Redis, 1.000 VU | 153 req/s |
| Quatro workers, sem Redis | 284 req/s |
| Um worker, com Redis, 1.000 VU | Cerca de 400 req/s |

O principal efeito observado não foi somente a redução da mediana. Em cargas
elevadas, o cache reduziu a cauda de latência e evitou que uma parcela das
requisições permanecesse bloqueada por consultas e composição de respostas.
Essa propriedade é particularmente importante em uma interface server-driven,
porque a resposta de uma tela pode reunir vários blocos, regras de oferta,
informações logísticas e ações. O cache da resposta completa impede que esse
trabalho seja repetido para solicitações contextualmente equivalentes dentro do
período de validade.

Os resultados de desempenho devem ser interpretados dentro do ambiente
experimental. A API, o banco, o Redis e o gerador de carga estavam no mesmo
hospedeiro, com comunicação por loopback. O protocolo principal utilizou um
worker, e os tamanhos padrão dos pools foram mantidos. Essas condições
permitem comparar configurações de cache dentro do mesmo ambiente, mas não
representam automaticamente um serviço distribuído em produção.

Também foram observadas limitações estatísticas. Em 1.000 usuários virtuais,
o p95 apresentou desvio padrão aproximado entre 1 e 1,5 segundo. Algumas
execuções de bateria foram descartadas e refeitas porque a ordem de execução
ou a configuração de medição não correspondia ao protocolo final. As seções
iniciais do documento de desempenho contêm medições anteriores com SQL `echo`
ativado e não devem ser utilizadas como base dos valores deste capítulo. Os
números aqui apresentados correspondem ao protocolo final validado na
rastreabilidade do projeto.

Os ensaios sustentam duas conclusões. Primeiro, a eliminação de consultas
repetidas e o carregamento dos centroides em memória são importantes para a
condição sem cache. Segundo, o Redis é decisivo quando a concorrência aumenta,
pois a resposta SDUI completa pode ser reutilizada por um período de uma hora.
O desempenho, portanto, não deve ser atribuído a uma única tecnologia. Ele
resulta da combinação entre consultas assíncronas, preparação dos dados,
memória de referência, composição server-driven e cache de respostas.

### 5.2 RESULTADOS QUALITATIVO-ESTRUTURAIS

#### 5.2.1 Desacoplamento por mutação do contrato

Os testes quantitativos demonstram que o sistema calcula, ordena e responde
dentro de determinados limites. Ainda era necessário verificar se a interface
realmente poderia ser alterada a partir da árvore enviada pelo servidor, que é
a característica central da abordagem server-driven. Para isso, foi realizado
um teste de mutação do contrato SDUI no navegador.

O procedimento partiu de uma resposta de referência e aplicou alterações
controladas no JSON recebido pelo frontend. Foram avaliadas cinco mutações:
reordenação de blocos, injeção de um selo logístico, inclusão de um bloco novo,
apresentação de um tipo desconhecido e envio de um envelope sem o campo
`actions`. O critério de sucesso foi que a página permanecesse funcional sem
novo build ou recarga completa, que o marcador de execução no objeto `window`
continuasse disponível e que o conteúdo alterado fosse refletido na tela quando
o componente fosse conhecido.

**Tabela 5.9. Mutações realizadas no contrato SDUI.**

| Mutação | Alteração no payload | Critério de sucesso |
|---|---|---|
| Reordenação | Troca da posição de blocos existentes | A ordem visual acompanha o JSON |
| Injeção de selo | Inclusão de informação de proximidade | O selo aparece sem alterar o componente pai |
| Bloco novo | Inclusão de componente conhecido | O novo bloco é renderizado |
| Tipo desconhecido | Inclusão de componente sem registro | A tela não é interrompida |
| Envelope incompleto | Remoção de `actions` | O envelope é normalizado e a tela permanece funcional |

As cinco mutações foram aprovadas. A reordenação demonstrou que a estrutura da
tela não está fixada em uma sequência hard-coded no cliente. A injeção do selo
demonstrou que uma informação de logística pode ser incluída no payload e
renderizada sem modificar a lógica de seleção do produto. A inclusão de um
bloco novo mostrou que o registro de componentes pode receber uma composição
mais ampla desde que o tipo já seja conhecido pelo frontend.

O caso do tipo desconhecido é especialmente importante. Em vez de lançar uma
exceção que derrubaria a tela inteira, o cliente ignora o componente que não
possui renderizador. Essa decisão preserva os demais blocos e cria uma forma de
compatibilidade entre versões parcialmente diferentes do servidor e do
cliente. O comportamento não significa que qualquer componente novo seja
automaticamente compreendido pelo frontend. Significa que a evolução
desconhecida não transforma uma diferença localizada em uma falha global.

**Figura 5.6. Evidências visuais das mutações do contrato.** A figura deve
reunir a linha de base, a reordenação, a injeção do selo, o bloco novo e o
bloco desconhecido. Recomenda-se apresentar as imagens com legendas que
expliquem qual trecho do JSON foi alterado e qual efeito apareceu na tela.

O envelope sem `actions` foi normalizado na entrada. Essa tolerância é
importante porque o campo representa comportamento e pode estar ausente em
blocos puramente informativos. A normalização evita que o frontend precise
tratar uma ausência esperada como uma exceção, sem transformar um campo
obrigatório em uma estrutura sem validação.

O resultado apoia a afirmação de que o frontend atua como um interpretador do
contrato. A árvore de blocos, e não uma sequência de componentes fixa no
cliente, determina a composição da tela. Esse desacoplamento é mais forte do
que a simples reutilização de componentes React, pois permite modificar a
ordem e a presença dos blocos por meio da resposta.

Há, entretanto, uma delimitação importante. O teste injeta mutações no payload
em tempo de execução. Ele demonstra que o cliente aceita e interpreta árvores
alteradas, mas não demonstra que o servidor consiga gerar qualquer nova
composição sem uma alteração em seu próprio código. A flexibilidade observada
é, portanto, a flexibilidade do contrato e do renderizador diante dos tipos
conhecidos, acompanhada de degradação segura para tipos desconhecidos.

#### 5.2.2 Robustez do contrato, componentes desconhecidos e dados insuficientes

A segunda dimensão qualitativo-estrutural avaliou o comportamento diante de
informações incompletas. Um marketplace baseado em dados históricos precisa
assumir que nem todo produto possuirá distância, peso, avaliação ou uma segunda
oferta. A resposta mais segura não é inventar um valor, mas retirar da tela o
elemento que não pode ser sustentado pelo dado disponível.

Os testes cobriram ausência de distância, ausência de peso, vendedor distante,
produto com apenas um vendedor, ausência de avaliações e impossibilidade de
calcular o selo ou o CO₂. Quando faltam os dados necessários, o bloco continua
apresentando as informações disponíveis e omite o campo dependente. Dessa
forma, a ausência de selo não equivale a uma afirmação de que a entrega não é
sustentável. Ela informa que o sistema não possui dados suficientes para
classificar o caso segundo aquele critério.

Essa distinção é relevante para a comunicação ambiental. Um selo aplicado a
partir de um valor padrão poderia aumentar artificialmente a quantidade de
entregas consideradas verdes. A estratégia de omissão é menos chamativa, mas
preserva a relação entre afirmação e evidência. Ela também evita que um produto
sem massa seja apresentado com emissão igual a zero.

A robustez foi avaliada em três níveis. No primeiro, os modelos do backend
validaram os campos e as uniões discriminadas. No segundo, os compositores
geraram respostas parciais quando alguns dados estavam ausentes. No terceiro,
o frontend recebeu blocos desconhecidos ou envelopes incompletos e preservou a
renderização dos demais componentes.

**Tabela 5.10. Situações de dados insuficientes e comportamento esperado.**

| Situação | Comportamento do sistema |
|---|---|
| Sem distância disponível | Não exibir distância ou selo dependente |
| Sem massa ou volume | Não exibir emissão calculada |
| Vendedor acima do limite de proximidade | Não atribuir selo verde |
| Produto com uma única oferta | Não sugerir substituição inexistente |
| Sem avaliações | Omitir a agregação de avaliações |
| Tipo de bloco desconhecido | Ignorar o bloco e preservar a tela |
| Envelope sem `actions` | Normalizar a ausência e continuar a renderização |

Além da tolerância a dados incompletos, foi verificada a correspondência entre
backend e frontend. Os tipos de blocos e ações foram comparados entre
`src/schemas/sdui.py`, `web/lib/sdui.ts` e o registro de componentes. Os testes
registraram 194 casos aprovados no backend, 35 no frontend, a jornada E2E
aprovada e cinco mutações do contrato aprovadas.

Os números de testes não devem ser confundidos com porcentagem de cobertura
funcional. Eles indicam a quantidade de casos aprovados nas suítes registradas,
mas não demonstram que todas as combinações possíveis de payload foram
exercitadas. A comparação de contrato verifica principalmente tipos e ações,
não todas as propriedades internas de cada bloco. Assim, ainda pode existir
uma divergência de campo que não seja detectada por essa verificação.

**Figura 5.7. Degradação segura diante de dados incompletos.** A figura deve
apresentar exemplos de uma tela com dados completos e de telas em que distância,
peso, avaliações ou ações estão ausentes, destacando que a composição
principal permanece utilizável.

A evidência estrutural complementa os resultados de desempenho. O cache só é
útil se a resposta reutilizada continuar sendo interpretada de maneira
consistente, e uma composição flexível só é relevante se puder incluir os
dados logísticos sem quebrar a jornada. A aprovação conjunta dos testes de
backend, frontend, navegador e mutação indica que o contrato funcionou como
uma fronteira efetiva entre composição e renderização no escopo avaliado.

O limite principal é que a robustez foi demonstrada por entradas controladas.
Não houve exploração exaustiva de todas as combinações inválidas de campos,
tipos e ações. Também não foi avaliada a evolução de versões diferentes do
contrato em um ambiente distribuído. Esses pontos permanecem como oportunidades
para uma etapa posterior, especialmente se o protótipo evoluir para múltiplas
versões de componentes em produção.

### 5.3 SÍNTESE DOS RESULTADOS

Os resultados quantitativos e qualitativo-estruturais respondem de maneira
complementar aos objetivos do trabalho. A preparação dos dados preservou
60.292 itens na amostra operacional, derivou 7.356 ofertas e manteve as
alternativas necessárias à comparação de vendedores. A verificação funcional
confirmou as unidades, os fatores e a monotonicidade do cálculo, sem afirmar
que o modelo de emissões seja uma medição operacional de transportadora.

A comparação com o OSRM mostrou que a correção por fator de circuidade reduziu
o MAPE de 21,9% para 8,7% e preservou uma correlação de ordenação de 0,997.
Nas decisões com alternativas, o vendedor mais próximo coincidiu em 86,5% dos
casos. Esses valores justificam a aproximação usada no caminho quente, desde
que a redação continue mencionando centroides, perfil de condução e diferença
entre proximidade e rota operacional.

O estudo de emissões mostrou potencial de redução dentro do recorte em que
existiam alternativas. A distância mediana caiu de 437 km para 330 km e a
redução estimada foi de 254,2 kg de CO₂e, ou 9,8% dos casos comparáveis. No
universo mensurável completo, o efeito equivalente foi de 0,9%. A diferença
entre os valores evita uma conclusão exagerada: a regra apresenta potencial
mais expressivo nos casos com alternativas, mas seu efeito agregado é menor
quando distribuído por todas as compras.

O desempenho demonstrou que a meta de 200 ms depende do cenário. Em baixa
concorrência, a aplicação permaneceu abaixo desse limite sem cache de respostas.
Em alta concorrência, o Redis aumentou a vazão de aproximadamente 153 para
cerca de 400 requisições por segundo e reduziu a latência da ordem de segundos
para a ordem de centenas de milissegundos. Essa diferença sustenta a decisão de
manter o cache ligado por padrão no runtime, sem atribuir todo o desempenho a
uma única camada.

Por fim, as mutações do contrato e os testes de robustez mostraram que a
interface pode alterar a composição da tela sem novo build e tolerar
componentes desconhecidos ou dados insuficientes. A evidência é compatível com
o objetivo de usar uma interface orientada pelo servidor, mas não elimina a
necessidade de versionar o contrato e testar propriedades internas quando novos
componentes forem adicionados.

Em conjunto, os resultados indicam que o artefato atende ao propósito de
demonstrar uma integração entre personalização contextual, logística verde e
composição server-driven. As conclusões são delimitadas pelo caráter histórico
do dataset, pelos centroides de CEP, pelo modelo estimativo de emissões, pelo
uso de um serviço público de roteamento e pelo ambiente controlado de carga.
Essas delimitações serão retomadas no capítulo de discussão, que deverá
separar o que foi demonstrado empiricamente do que permanece como hipótese,
cenário ou trabalho futuro.
