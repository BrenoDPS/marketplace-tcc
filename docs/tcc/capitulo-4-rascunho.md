# Capítulo 4. Desenvolvimento

## 4 DESENVOLVIMENTO

Este capítulo apresenta o desenvolvimento do marketplace contextual adaptativo
proposto neste trabalho. A solução foi construída a partir do conjunto de dados
público da Olist e combina uma interface orientada pelo servidor com mecanismos
de personalização contextual e de apoio à logística verde. A exposição está
organizada em três momentos. Primeiro, são apresentados os requisitos e as
delimitações que orientaram o desenvolvimento. Em seguida, descrevem-se a
arquitetura, o modelo de dados e o contrato de comunicação entre o servidor e a
interface. Por fim, são detalhadas as principais decisões de implementação,
incluindo o tratamento dos dados, o cálculo logístico, a composição das telas e
o ambiente de execução.

Essa organização acompanha o percurso de construção do sistema, mas não pretende
reproduzir a ordem cronológica das sprints. O objetivo é explicar como os
componentes se relacionam e de que maneira cada decisão contribui para os
objetivos definidos no trabalho. O artefato descrito neste capítulo é o mesmo
que foi submetido aos testes funcionais, à avaliação do contrato de interface e
ao protocolo de carga apresentados no Capítulo 5.

### 4.1 ESPECIFICAÇÃO

#### 4.1.1 Requisitos funcionais

Os requisitos funcionais foram definidos a partir dos objetivos específicos do
trabalho e das situações de uso previstas para o marketplace. O sistema deveria
ser capaz de adaptar a apresentação dos produtos ao contexto do comprador, levar
em consideração a localização dos vendedores e apresentar uma jornada de compra
simulada sem transformar o protótipo em uma plataforma de comércio eletrônico
completa.

O primeiro requisito refere-se à composição da tela inicial. A rota
`GET /api/v1/home` recebe o prefixo de CEP do comprador e devolve uma tela
completa, representada pelo modelo `ScreenResponse`. A tela pode conter um
banner principal, uma grade de categorias e cartões de produtos. O parâmetro de
contexto permite selecionar perfis como especialista em eletrônicos, interessado
em beleza ou consumidor consciente. Quando o comprador não escolhe um contexto
específico, o sistema utiliza a UF associada ao seu CEP para identificar uma
categoria com participação acima da média nacional. Essa escolha é feita pelo
maior *lift* regional, calculado sobre o conjunto completo de dados, desde que
sejam respeitados os limiares mínimos de volume definidos no processo de carga.

Também foram previstos mecanismos de busca e filtragem. Como o conjunto de
dados da Olist não apresenta um nome textual para cada produto, a busca é
realizada sobre a categoria do produto. O termo informado pelo usuário passa por
normalização de acentuação, caixa e separação de palavras. O filtro por
categoria, por sua vez, utiliza o identificador da categoria presente no
conjunto de dados. Dessa maneira, a interface não apresenta uma funcionalidade
de busca por nome de produto que a base original não poderia sustentar.

O segundo requisito está relacionado à localização da oferta. Para cada produto
considerado na composição da vitrine, calcula-se a distância entre o CEP do
comprador e o CEP do vendedor por meio da fórmula de Haversine aplicada aos
centroides geográficos. Ofertas com distância inferior a 100 km podem receber o
selo de logística verde. O selo é acompanhado de uma indicação de distância e,
quando há massa ou volume disponível, de uma estimativa de emissão. Na ausência
de dados suficientes, o sistema omite o selo ou a informação correspondente,
evitando apresentar uma recomendação ambiental sem fundamento numérico.

O terceiro requisito corresponde ao cálculo da pegada de carbono. A emissão é
estimada por uma abordagem baseada em atividade, compatível com o enquadramento
da ISO 14083 e com os fatores do GLEC Framework. A distância geodésica é
convertida em uma distância rodoviária aproximada por meio do fator de
circuidade 1,345, com base na referência de Gonçalves et al. (2014). O percurso
é representado por dois trechos: uma etapa de transferência realizada por
caminhão pesado e uma etapa final de até 15 km realizada por van, conforme a
referência do World Economic Forum (2024). A massa utilizada no cálculo é a
massa cobrável, isto é, o maior valor entre o peso real e o peso cubado. Para a
cubagem, adotou-se a relação de 6.000 cm³ para cada quilograma, conforme a
convenção utilizada no transporte rodoviário de cargas.

O sistema também deveria manter uma regra única para a escolha da oferta. Um
mesmo produto pode aparecer associado a mais de um vendedor e, por isso, a
vitrine, a tela de detalhe e o checkout precisam apresentar uma escolha
coerente. A regra prioriza a menor distância. Consideram-se praticamente
equivalentes as ofertas cuja distância esteja dentro de uma tolerância de 1% da
menor distância, com piso de 1 km. Nesse conjunto, o preço é utilizado como
critério de desempate. Assim, pequenas diferenças que não são significativas
para a aproximação geográfica não impedem a escolha de uma oferta mais barata.

Outro requisito foi a criação de uma tela de detalhe de produto orientada pelo
servidor. A rota `GET /api/v1/products/{product_id}` devolve uma nova
`ScreenResponse`, composta principalmente pelos blocos de detalhe do produto e
de impacto logístico. As avaliações são obtidas da agregação de dados reais de
avaliações da Olist, enquanto a cidade e a UF do vendedor provêm da tabela de
vendedores. Não foram incluídas descrições textuais ou tags de sustentabilidade,
pois esses dados não estão disponíveis no conjunto original.

Para representar a etapa de compra, foi implementado um checkout simulado. A
rota `POST /api/v1/checkout/simulate` recebe uma lista de itens, suas
quantidades e, opcionalmente, a modalidade de entrega. A resposta apresenta o
resumo do carrinho, as opções de entrega, a divisão das remessas por vendedor e
o impacto logístico estimado. O fluxo não realiza pagamento, não baixa estoque
e não persiste um pedido.

As modalidades de entrega foram incluídas para permitir uma comparação de
preço, prazo e emissão. A modalidade padrão utiliza o frete observado na base.
Os prazos de referência foram derivados de entregas reais agrupadas por faixas
de distância. As modalidades expressa e verde são cenários declarados sobre
essa linha de base, pois a Olist não informa modalidade de transporte,
transportadora ou fator de emissão por opção de entrega. Essa distinção é
apresentada ao usuário no próprio bloco de opções.

Por fim, as ações da interface são descritas pelo servidor. Navegação, chamadas
à API e abertura de modais são representadas como variantes do contrato de
ações. Na versão implementada, o fluxo principal utiliza navegação e chamadas
à API. A ação de abertura de modal permanece prevista no contrato, embora o
detalhe de produto tenha passado a ser carregado como uma nova tela server-driven.

#### 4.1.2 Requisitos não funcionais, métricas e critérios de aceitação

Além das funcionalidades diretamente visíveis ao usuário, o desenvolvimento
considerou requisitos de desempenho, integridade do contrato, tolerância a
dados incompletos e reprodutibilidade.

O desempenho foi estabelecido como uma meta experimental de tempo até o primeiro
byte inferior a 200 ms nos cenários e percentis definidos na metodologia. Essa
meta não foi tratada como uma garantia universal, pois o comportamento depende
do nível de concorrência e da condição do cache. A avaliação deveria comparar
três estados da camada de respostas em Redis, com cache desabilitado, frio e
aquecido, além de considerar o tempo de reflexão entre as requisições. O acesso
ao banco de dados da aplicação foi implementado de forma assíncrona, utilizando
SQLAlchemy e asyncpg.

A integridade do contrato foi tratada com modelos Pydantic v2 e uniões
discriminadas pelo campo `type`. No frontend, o contrato foi espelhado em
TypeScript, e o registro de componentes React mantém a correspondência entre
os tipos recebidos e os componentes renderizados. Essa correspondência é
verificada por testes, pois uma divergência entre servidor e cliente poderia
produzir uma tela incompleta mesmo quando cada parte estivesse funcionando
isoladamente.

Também foi estabelecido que a interface deveria degradar de forma segura.
Componentes desconhecidos não podem interromper a renderização da tela, e um
envelope incompleto deve ser normalizado quando possível. Da mesma forma, a
ausência de coordenadas, massa, avaliação ou alternativa válida deve resultar
na omissão do campo correspondente. O sistema não deve substituir uma ausência
de informação por um valor inventado.

A reprodutibilidade foi considerada desde o tratamento dos dados até os ensaios
de desempenho. A amostragem operacional utiliza semente fixa, os ensaios de
carga registram seus parâmetros e as análises de concentração regional,
emissões evitadas e comparação entre Haversine e OSRM são executadas por
scripts específicos. As respostas obtidas do serviço público de roteamento
foram preservadas em arquivo para que as métricas publicadas possam ser
recalculadas sem depender de uma nova consulta à rede.

Os critérios de aceitação foram organizados em quatro grupos. O primeiro reúne
os testes de distância, massa e emissão com entradas controladas. O segundo
verifica a ordenação das ofertas, das remessas e das alternativas. O terceiro
confere a geração e a interpretação do contrato SDUI. O quarto avalia a jornada
completa e o comportamento sob carga. Os resultados da aplicação desses
critérios são apresentados no Capítulo 5.

#### 4.1.3 Delimitações do escopo

O sistema foi desenvolvido como um runtime de demonstração e avaliação, e não
como uma plataforma comercial pronta para produção. A API utiliza uma amostra
derivada do conjunto de dados da Olist, carregada em um PostgreSQL local após
os filtros de qualidade. As análises de concentração logística e de CO₂
evitado, por sua vez, são executadas offline sobre o conjunto completo. Essa
separação é necessária porque o volume utilizado para demonstrar a aplicação
não é o mesmo volume utilizado para estudar o potencial logístico do conjunto
de dados.

Ficaram fora do escopo a autenticação, os perfis de usuário, a persistência de
pedidos, o pagamento, o painel do vendedor e as consultas espaciais com
PostGIS. O módulo destinado a encaminhar diferentes versões de componentes
também permanece como uma extensão futura. O campo `version` já existe no
contrato, mas todos os componentes entregues utilizam a versão 1.

A distância utilizada pela aplicação continua sendo calculada entre centroides
de prefixos de CEP. A comparação realizada com o OSRM mostrou que a estimativa
corrigida pelo fator de circuidade apresenta erro menor do que a distância
Haversine crua e preserva, em grande parte, a ordenação das ofertas. Entretanto,
o OSRM representa a rota mais rápida de carro e não necessariamente a rota da
transportadora. Além disso, os pontos de origem e destino são centroides, não
endereços individuais. Por isso, as distâncias exibidas devem ser interpretadas
como estimativas comparativas.

Também foram declaradas as premissas das modalidades de entrega. O frete padrão
tem origem observada na base, enquanto os fatores de preço, prazo e emissão das
modalidades expressa e verde representam cenários. Do mesmo modo, agrupar
itens de um mesmo vendedor reduz o frete simulado, mas não reduz a emissão no
modelo adotado, que é linear em relação à massa. A recomendação de um vendedor
mais próximo só pode ser feita quando existem ofertas alternativas para o
produto analisado.

### 4.2 PROJETO

#### 4.2.1 Organização em fatias verticais

Adotou-se a organização em fatias verticais para manter próximas as regras de
negócio, a composição das telas e o acesso aos dados de cada funcionalidade.
Essa decisão foi importante porque o sistema não se limita a consultar produtos:
ele precisa combinar contexto, localização, emissão e apresentação em uma mesma
resposta.

A fatia `home_contextual` concentra a composição da tela inicial, a derivação
regional do contexto, a busca e os filtros. A fatia `green_logistics` reúne os
centroides, o cálculo de distância, a emissão, o selo e as modalidades de
entrega. A fatia `product_detail` é responsável pela tela de detalhe, enquanto
`checkout` reúne a simulação do carrinho, a divisão das remessas e as
alternativas de substituição. O módulo `orchestrator` foi reservado para uma
evolução futura relacionada ao roteamento entre versões de componentes.

O backend atua como uma camada específica para a aplicação. Ele consulta os
dados necessários, executa as regras de negócio e devolve uma árvore de
componentes pronta para ser interpretada pelo cliente. Essa organização reduz
o acoplamento entre a interface e as regras de recomendação. Uma alteração na
forma de ordenar produtos, por exemplo, permanece no servidor e não exige que
o cliente conheça o cálculo de distância ou de emissão.

**Figura 4.1. Arquitetura da solução proposta.** A figura deve apresentar o
fluxo entre o navegador, o frontend Next.js, o backend FastAPI, as fatias
verticais, o Redis, o PostgreSQL e o processo offline de carga do dataset.
Fonte: elaborada pelos autores.

#### 4.2.2 Modelo de dados relacional

O PostgreSQL foi utilizado para persistir as entidades necessárias à aplicação
e as tabelas derivadas durante o processo de preparação dos dados. As tabelas
originais representam produtos, vendedores, itens de pedido, clientes,
categorias e avaliações. Sobre essa base foram criadas estruturas que tornam
possíveis as consultas e decisões específicas do sistema.

A tabela `cep_centroids` representa cada prefixo de CEP por meio da mediana das
coordenadas encontradas na tabela de geolocalização. Ela também armazena a UF
mais frequente para o prefixo. Como esse conjunto é estático durante a execução
da API, seus registros são carregados de forma lazy na primeira consulta e
mantidos em memória no processo da aplicação. Um mecanismo de sincronização
impede que requisições concorrentes provoquem várias cargas simultâneas.

A tabela `offers` reúne as combinações de produto e vendedor identificadas no
processo de carga, incluindo preço e demais informações necessárias à escolha
da oferta. Sua utilização evita que a vitrine dependa exclusivamente da ordem
em que as linhas de pedidos foram sorteadas. Assim, produtos que possuem mais
de uma oferta podem ser comparados segundo a mesma regra de proximidade usada
no detalhe e no checkout.

A tabela `regional_categories` armazena a categoria de maior *lift* para cada
UF que atende aos limiares definidos. O cálculo utiliza o conjunto completo de
dados, mas somente categorias presentes no catálogo carregado são utilizadas na
Home. Essa separação permite preparar o sinal regional durante o ETL, sem
introduzir uma consulta adicional no caminho de cada requisição.

O processo de carga é independente do runtime da API. O script de ETL utiliza
Pandas para ler e transformar os arquivos CSV e psycopg para gravar o resultado
no PostgreSQL. A API, por outro lado, utiliza acesso assíncrono ao banco. Essa
separação evita que as dependências e as operações de processamento em lote
sejam incorporadas ao caminho de atendimento das telas.

**Figura 4.2. Modelo de dados simplificado.** A figura deve destacar as
entidades do Olist e as tabelas derivadas `cep_centroids`, `offers` e
`regional_categories`. Fonte: elaborada pelos autores.

#### 4.2.3 Contrato da interface orientada pelo servidor

O contrato de comunicação foi definido para que cada bloco da interface pudesse
ser descrito pelo servidor sem que o cliente precisasse conhecer as regras que
levaram à sua composição. Cada bloco possui o envelope
`{ type, version, props, actions }`. O campo `type` identifica o componente,
`version` permite evolução futura do contrato, `props` contém os dados de
apresentação e `actions` descreve os comportamentos que o cliente deve executar.

A resposta completa é representada por `ScreenResponse`, que reúne a versão do
esquema, o identificador da tela, o contexto aplicado e a lista de componentes.
A validação é feita com uniões discriminadas em Pydantic, o que permite
distinguir as variantes pelo campo `type` e manter explícitos os campos de cada
bloco.

Os principais componentes implementados são o banner principal, o cartão de
produto, a grade de categorias, a tela de detalhe, o resumo do checkout, as
opções de entrega, a divisão de remessas e o banner de impacto. Essa variedade
permite que Home, detalhe e checkout utilizem o mesmo princípio de composição,
mesmo apresentando informações diferentes.

As ações disponíveis no contrato são navegação, chamada à API e abertura de
modal. A ação de chamada à API pode solicitar uma nova tela por meio de uma
requisição GET ou enviar os dados do carrinho para a simulação de checkout por
meio de uma requisição POST. Em dois casos, as ações aparecem em níveis internos
do bloco. Cada categoria possui seu próprio destino, e cada alternativa de
remessa pode representar uma substituição diferente. Essa organização mantém
explícita a relação entre o elemento visual e o comportamento correspondente.

No frontend, o registro de componentes associa cada `type` recebido ao
componente React responsável por sua renderização. O contrato também possui um
espelho em TypeScript. O cliente foi projetado para ignorar de forma segura um
tipo que ainda não possua renderizador, sem transformar esse caso em uma falha
da tela inteira. O modo de inspeção SDUI foi incluído para tornar visível o
envelope recebido, seus tipos, suas ações e seus dados, o que facilita a
verificação do desacoplamento proposto.

**Tabela 4.1. Componentes do contrato SDUI.** A tabela deve apresentar o tipo
do bloco, a tela em que ele é utilizado e sua responsabilidade principal.
Fonte: elaborada pelos autores a partir do contrato implementado.

### 4.3 IMPLEMENTAÇÃO

#### 4.3.1 Tratamento e carga do conjunto de dados

O processo de preparação começa com a leitura dos arquivos CSV do conjunto de
dados público da Olist. A amostragem utilizada pela API é realizada com semente
fixa, de modo que a mesma configuração possa ser reconstruída. Depois da
seleção inicial dos itens, o processo completa as ofertas dos produtos
selecionados. Essa etapa é necessária porque a seleção linha a linha de pedidos
poderia apresentar um produto sem revelar que ele também possui ofertas de
outros vendedores.

Em seguida, são construídos os centroides dos prefixos de CEP e é associada
uma UF a cada prefixo quando essa informação está disponível. O ETL também
deriva as ofertas, as categorias regionais, as avaliações agregadas e os
campos necessários à composição do detalhe e do checkout. Registros sem peso
utilizável ou sem geolocalização válida de cliente ou vendedor são retirados
antes da persistência.

A escolha por calcular os centroides durante o ETL reduz o custo das consultas
em tempo de execução. Da mesma forma, a derivação do contexto regional evita
que a API tenha de calcular novamente a participação das categorias a cada
acesso à Home. O resultado é um catálogo preparado para a demonstração, sem
alterar os arquivos brutos do Olist.

#### 4.3.2 Backend, cálculo logístico e cache

As rotas da aplicação são expostas pelo FastAPI e organizadas por fatias de
responsabilidade. Quando uma Home ou um checkout é solicitado, o backend valida
o CEP, recupera os produtos e as ofertas disponíveis, calcula as distâncias e
aplica a regra de escolha. Em seguida, o motor logístico calcula a emissão e
os compositores transformam os dados em componentes SDUI.

O cálculo de distância utiliza os centroides mantidos em memória. A primeira
requisição que necessita dessa informação carrega a tabela do banco, de forma
lazy, e as requisições seguintes utilizam o dicionário já carregado. Essa
decisão foi tomada porque os centroides são dados de referência estáticos. Ela
também elimina consultas repetidas ao mesmo CEP durante o ranqueamento de
vários produtos.

O motor de emissão recebe a distância Haversine e a massa cobrável. A primeira
é transformada em uma estimativa de distância rodoviária pela circuidade
adotada. O trecho correspondente à última milha recebe o fator de emissão da
van e o restante recebe o fator do caminhão pesado. O resultado pode ser
formatado em quilogramas ou gramas, conforme a magnitude, para evitar que
emissões pequenas apareçam como zero na interface.

O Redis armazena respostas completas da Home e utiliza tempo de expiração de
uma hora. A presença do cache não substitui as otimizações estruturais do
backend. Mesmo quando o Redis está desligado, os centroides permanecem em
memória e o PostgreSQL pode utilizar seu próprio cache de páginas. Nos ensaios
de carga, portanto, a expressão “cache desabilitado” refere-se especificamente
à camada de respostas em Redis. Os efeitos dessas escolhas são analisados no
Capítulo 5.

As opções de entrega combinam dados observados e cenários declarados. O frete
da modalidade padrão é obtido da amostra, enquanto preço, prazo e emissão das
modalidades expressa e verde são calculados por fatores definidos para a
comparação. Os prazos de referência foram estimados por faixas de distância
com base em 95.921 entregas reais, e não por uma fórmula arbitrária de
quilômetros por dia.

#### 4.3.3 Composição das telas e renderização no cliente

Os compositores do servidor organizam os blocos de cada tela de acordo com o
contexto e a funcionalidade solicitada. Na Home de consumidor consciente, por
exemplo, os cartões são ordenados pela proximidade. No checkout, os itens são
agrupados por vendedor, as remessas são ordenadas pela emissão estimada e as
alternativas são selecionadas considerando distância, massa e potencial de
redução de CO₂.

O frontend foi implementado com Next.js e utiliza React como biblioteca de
renderização. O cliente recebe a `ScreenResponse`, consulta o registro de
componentes e monta a tela sem repetir as regras de recomendação. A navegação
para o detalhe e a chamada de simulação do checkout são executadas pelo
interpretador de ações.

O carrinho é mantido no armazenamento local do navegador, pois não há
persistência de pedidos neste escopo. Na leitura, seus dados são validados
antes de serem utilizados. A ausência de um backend de pedidos não impede a
avaliação da jornada, pois o objetivo desta etapa é verificar a composição
server-driven e a simulação das consequências logísticas.

O contrato foi acompanhado por testes do renderizador, do interpretador de
ações e dos casos de degradação. Também foram realizados testes de jornada com
o navegador, incluindo alterações controladas na resposta SDUI. A análise
dessas evidências pertence ao Capítulo 5, pois esta seção descreve apenas como
o mecanismo foi construído.

**Figura 4.3. Fluxo de composição de uma tela.** A figura deve mostrar o
recebimento do contexto, a consulta aos dados, o cálculo logístico, a montagem
da `ScreenResponse` e a renderização do bloco correspondente no cliente.
Fonte: elaborada pelos autores.

#### 4.3.4 Ambiente de execução

O ambiente foi organizado com Docker Compose para os serviços PostgreSQL e
Redis. A API FastAPI é executada no hospedeiro e o frontend pode ser iniciado
separadamente para a demonstração visual. Essa configuração foi mantida nas
medições porque o ambiente utilizado era Windows com Docker sobre WSL2. Dessa
forma, a comunicação entre a API e o gerador de carga ocorreu por loopback,
enquanto o banco e o cache permaneceram em contêineres no mesmo hospedeiro.

Para executar a demonstração, primeiro são iniciados os serviços de
persistência. Em seguida, o ETL carrega a amostra operacional e a API é
iniciada. Quando o banco é recarregado enquanto a API permanece ativa, o
snapshot de centroides e as respostas armazenadas no Redis precisam ser
invalidados. Essa exigência decorre do caráter estático dos dados mantidos em
memória durante a execução.

O projeto também possui verificações automatizadas para o backend e para o
frontend. Os testes de carga e os testes de navegador dependem dos arquivos
brutos e da pilha em execução, por isso são executados no ambiente de
avaliação, enquanto os testes unitários, de contrato, de lint e de tipos podem
ser executados no fluxo de integração contínua.

Com essa configuração, o sistema reúne o conjunto de dados preparado, o
backend responsável pelas regras de negócio e o cliente responsável pela
renderização. O capítulo seguinte apresenta as evidências obtidas a partir
desse artefato, separando a qualidade dos dados, o comportamento funcional,
as estimativas logísticas, o desempenho e a flexibilidade do contrato.
