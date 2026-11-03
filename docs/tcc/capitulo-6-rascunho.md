# Capítulo 6. Considerações finais (rascunho)

> v3 (03/11): reescrito conforme a orientação da professora para a versão final:
> **sem subtítulos** e mais curto, em parágrafos corridos, na ordem do modelo
> "Sugestão para Considerações Finais": (1) ideia geral, com foco na parte
> teórica; (2) desenvolvimento; (3) experimentos; (4) resultados, objetivos
> atingidos e pontos fortes; (5) trabalhos futuros. Modelo de extensão: o Cap. 7 do
> TCC "Software de codificação para análises qualitativas" (Facens), ~1,5 página
> sem tabelas.
>
> Saíram as antigas §§6.1 (discussão e relações de compromisso), 6.2 (limitações e
> ameaças à validade), 6.3 e 6.4 e o Quadro 1 (aderência aos objetivos). O essencial
> de cada uma ficou nos parágrafos abaixo; o detalhe continua nos Caps. 4 e 5 e em
> `docs/tese-rastreabilidade.md`. Nenhum número é novo: todos estão no Cap. 5.
> O teste de usabilidade não foi feito (decisão do grupo com o orientador, 02/11):
> aparece como limitação e como trabalho futuro.

## 6 CONSIDERAÇÕES FINAIS

O comércio eletrônico reúne dois problemas que costumam ser tratados
separadamente. De um lado, as interfaces dos aplicativos dependem de novas versões
do cliente para mudar, o que torna lenta qualquer adaptação ao contexto de quem
compra. De outro, a escolha de um produto quase nunca considera de onde ele sai,
embora a distância entre vendedor e comprador determine boa parte do frete e da
emissão do transporte, sobretudo na última milha. A Server-Driven UI, em que o
servidor descreve a tela e o cliente apenas a renderiza, responde ao primeiro
problema; a estimativa de emissões baseada em atividade, no enquadramento da ISO
14083 e do GLEC Framework, oferece um caminho para o segundo, desde que o resultado
seja apresentado como estimativa comparativa, e não como medição.

Este trabalho uniu as duas frentes em um marketplace contextual adaptativo,
construído sobre o conjunto de dados público da Olist. O servidor compõe a
interface e entrega, junto de cada oferta, a distância até o comprador, um selo
para entregas a menos de 100 km e a emissão estimada. O objetivo foi verificar se
essa composição no servidor permite adaptar a vitrine ao contexto e tornar visível
a opção de menor impacto, sem depender de atualizações do front-end e sem
comprometer o desempenho.

O desenvolvimento adotou um Backend-for-Frontend em FastAPI, organizado em fatias
verticais, com PostgreSQL, cache de respostas em Redis e um cliente Next.js que
apenas interpreta a árvore de componentes recebida. O contrato entre os dois lados
é tipado e existe duas vezes, em Pydantic e em TypeScript; essa duplicação, preço do
desacoplamento, foi controlada por testes que comparam os dois lados campo a campo.
O motor de emissão converte a distância em linha reta em distância rodoviária,
separa a última milha feita por van da transferência por caminhão e considera a
massa cobrável. A vitrine passou a destacar a categoria mais comprada na UF do
comprador, e vitrine, detalhe e checkout escolhem o vendedor pela mesma regra de
proximidade. A interface expõe a conta de cada estimativa, para que o selo não seja
uma caixa-preta.

Os experimentos seguiram a metodologia. O desempenho foi medido em 27 ensaios, com
três níveis de carga, três estados do cache e três repetições, e repetido no código
final. A flexibilidade foi avaliada por mutações do contrato aplicadas à resposta
do servidor. A aproximação de distância foi comparada com rotas do OSRM em 100
pares de origem e destino, e o potencial de redução de emissão foi calculado sobre
a base completa da Olist, com análise de sensibilidade dos parâmetros. A jornada de
compra também foi percorrida por testes automatizados no navegador, incluindo a
navegação só por teclado.

Os resultados indicam que o objetivo geral foi atingido no escopo de um protótipo.
As mutações do contrato foram refletidas na tela sem nova compilação do cliente, e
componentes desconhecidos foram ignorados sem interromper a página. A distância
estimada errou 8,7% em relação às rotas e preservou a escolha do vendedor mais
próximo em 86,5% das decisões, precisão suficiente para comparar vendedores. A
vitrine se adaptou à região em 12 das 27 UFs, e escolher o vendedor mais próximo
reduziria em 9,8% a emissão das compras que tinham alternativa, ou 0,9% do total.
Sob carga, o cache de respostas foi a decisão que manteve a aplicação dentro da
meta de 200 ms até 250 usuários simultâneos; com 1.000 usuários, multiplicou a vazão
por 2,6, mas as telas de detalhe e de checkout, que não passam pelo cache, elevaram
o percentil 95 para cerca de 3 s. Entre os pontos fortes do projeto estão a
transparência da estimativa, a regra única de escolha de oferta, a recusa em
completar dados que a base não possui e a rastreabilidade dos experimentos, cada
um registrado com o commit, as versões e os dados utilizados.

Esses resultados também delimitam a contribuição. A emissão é uma estimativa de
modelo, com fatores internacionais e não da frota brasileira, e o CO₂ evitado é
contrafactual, pois supõe que o comprador seguiria a recomendação. Esse
comportamento não foi medido, já que o trabalho não incluiu estudo com
participantes. A base mostrou ainda que o maior obstáculo à logística verde não é a
falta de vendedores próximos, presentes para 94,7% dos compradores, mas a falta de
alternativas para o mesmo produto, que existem em 12,8% dos itens, e que o benefício
se concentra nas regiões com mais vendedores: 23,5% de emissão evitada em SP, contra
3,7% na BA. A interface pode tornar a escolha local visível e comparável, mas o
efeito depende de haver o que escolher.

Como trabalhos futuros, o passo mais importante é medir o efeito da recomendação
com usuários, por teste A/B ou estudo de preferência, substituindo o CO₂ evitado
contrafactual por um efeito observado. Em seguida, a personalização pode passar da
região para a pessoa, com autenticação e histórico próprio, mantendo o contexto
regional como ponto de partida. No desempenho, estender o cache às telas de detalhe
e de checkout e distribuir a carga entre vários processos atacaria o gargalo
encontrado com 1.000 usuários. No modelo de emissão, um selo baseado na emissão
relativa, distâncias rodoviárias pré-calculadas e fatores da frota brasileira
aproximariam a estimativa da entrega real. Por fim, um painel para o vendedor,
com a pegada das próprias entregas, levaria a mesma informação ao outro lado do
marketplace.
