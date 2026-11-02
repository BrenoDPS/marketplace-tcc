# Pré-textuais e pós-textuais da versão final

> Fonte do Resumo, do Abstract, da Lista de siglas e das Referências do `.docx` da
> versão final (`python -m scripts.monografia_docx`). Base: Report 6 (PDF de 14/10),
> com os ajustes M6, M7, m4 e m6 de `ajustes-versao-final.md` e as versões de software
> corrigidas pelo `de-para-metricas.md` §8. Cada seção é lida pelo gerador pelo título
> `## `; não renomear.

## RESUMO

O Marketplace Contextual Adaptativo é um protótipo de comércio eletrônico construído sobre o conjunto de dados público da Olist, no qual o servidor define a interface por meio de uma engine de Server-Driven UI (SDUI). Um Backend-for-Frontend (BFF) em FastAPI, organizado em fatias verticais, com PostgreSQL e cache de respostas em Redis, envia ao cliente uma árvore de componentes tipados que ele apenas renderiza. Sobre essa arquitetura, a vitrine se adapta à região do comprador, derivada do CEP, e cada oferta exibe distância e pegada de carbono estimadas por um motor baseado em atividade, alinhado à ISO 14083 e ao GLEC Framework, com selo para entregas a menos de 100 km. Corrigida por fator de circuidade, a distância estimada apresentou erro de 8,7% em relação a rotas do OSRM. No conjunto completo da Olist, escolher o vendedor mais próximo reduziria em 9,8% a emissão estimada das compras que tinham alternativa, ou 0,9% do total, com efeito concentrado nas regiões com mais vendedores. Com 1.000 usuários virtuais, o cache elevou a vazão de 153 para cerca de 400 requisições por segundo e reduziu a latência mediana de 4,1 s para 95 ms, embora o percentil 95 tenha ficado em torno de 3 s. Testes de mutação do contrato mostraram que a interface reflete alterações da árvore enviada pelo servidor sem nova compilação do cliente. Os resultados indicam a viabilidade técnica da abordagem, dentro dos limites de um protótipo com dados históricos e emissões estimadas.

Palavras-chave: Server-Driven UI. Logística Verde. Backend-for-Frontend. Marketplace Contextual. FastAPI.

## ABSTRACT

The Adaptive Contextual Marketplace is an e-commerce prototype built on the public Olist dataset, in which the server defines the interface through a Server-Driven UI (SDUI) engine. A Backend-for-Frontend (BFF) in FastAPI, organized in vertical slices, with PostgreSQL and a Redis response cache, sends the client a tree of typed components that the client only renders. On top of this architecture, the storefront adapts to the buyer's region, derived from the postal code, and each offer shows distance and carbon footprint estimated by an activity-based engine aligned with ISO 14083 and the GLEC Framework, with a badge for deliveries under 100 km. Corrected by a circuity factor, the estimated distance showed an 8.7% error against OSRM routes. In the full Olist dataset, choosing the nearest seller would reduce the estimated emissions of purchases that had an alternative by 9.8%, or 0.9% of the total, with the effect concentrated in regions with more sellers. With 1,000 virtual users, the cache raised throughput from 153 to about 400 requests per second and reduced median latency from 4.1 s to 95 ms, although the 95th percentile stayed around 3 s. Contract mutation tests showed that the interface reflects changes in the server-sent tree without rebuilding the client. The results indicate the technical feasibility of the approach, within the limits of a prototype with historical data and estimated emissions.

Key words: Server-Driven UI. Green Logistics. Backend-for-Frontend. Contextual Marketplace. FastAPI.

## LISTA DE SIGLAS

| Sigla | Significado |
|---|---|
| API | Application Programming Interface |
| BFF | Backend-for-Frontend |
| CEP | Código de Endereçamento Postal |
| CO₂e | Dióxido de carbono equivalente |
| ETL | Extract, Transform, Load |
| GEE | Gases de efeito estufa |
| GLEC | Global Logistics Emissions Council |
| ISO | International Organization for Standardization |
| JSON | JavaScript Object Notation |
| MAE | Mean Absolute Error (erro absoluto médio) |
| MAPE | Mean Absolute Percentage Error (erro percentual absoluto médio) |
| ODS | Objetivos de Desenvolvimento Sustentável |
| OSRM | Open Source Routing Machine |
| RPS | Requisições por segundo |
| SDUI | Server-Driven UI |
| TTFB | Time to First Byte (tempo até o primeiro byte) |
| UF | Unidade Federativa |
| UI | User Interface |
| UX | User Experience |
| VU | Virtual User (usuário virtual) |

## REFERÊNCIAS

BSOFT. **Entenda a diferença entre cubagem, peso cubado e fator de cubagem**. [S. l.]: Bsoft Internet e Tecnologia, 2026. Disponível em: https://bsoft.com.br/blog/diferenca-cubagem-peso-cubado-fator-cubagem. Acesso em: 13 out. 2026.

CANO, Jose Alejandro; LONDOÑO-PINEDA, Abraham; OVALLE RODAS, C. Sustainable Logistics for E-Commerce: A Literature Review and Bibliometric Analysis. **Sustainability**, v. 14, n. 19, art. 12247, 27 set. 2022. DOI: 10.3390/su141912247.

CHERIPURATHU, Kurian George; KULKARNI, Sanjeev. Integrating Microservices and Microfrontends: A Comprehensive Literature Review on Architecture, Design Patterns, and Implementation Challenges. **Journal of Scientific Research and Technology**, p. 1-12, 2 jul. 2024. DOI: 10.61808/jsrt115.

EDRONE. **Dados do e-commerce no Brasil**: estatísticas e tendências. [S. l.], [202-?]. Disponível em: https://edrone.me/br/blog/dados-ecommerce-brasil. Acesso em: 14 abr. 2026.

ISO. **ISO 14083:2023**: Greenhouse gases — Quantification and reporting of greenhouse gas emissions arising from operations of transport chains. Geneva: International Organization for Standardization, 2023. 108 p.

GOOGLE. **Web Vitals**: essential metrics for a healthy site. [S. l.]: web.dev, 2024. Disponível em: https://web.dev/articles/vitals. Acesso em: 2 nov. 2026.

LEE, K.; CHAE, J. Estimation of travel cost between geographic coordinates using artificial neural network: potential application in vehicle routing problems. **ISPRS International Journal of Geo-Information**, Basel, v. 12, n. 2, p. 57, 2023. DOI: 10.3390/ijgi12020057.

LOCUST. **Locust**: an open source load testing tool. Versão 2.46. [S. l.]: Locust.io, 2024. Disponível em: https://docs.locust.io. Acesso em: 9 set. 2026.

MUNDIM, Arianne Alves da Silva. **Roteamento de Estoque e Transporte de Carga Multimodal**: Otimização Bi-objetivo com Considerações Ambientais e Econômicas. 2024. 114 p. Tese (Doutorado em Ciências de Computação e Matemática Computacional) – Universidade de São Paulo, São Paulo, 2024.

NAWAZ, Asif et al. Context-aware Frameworks and Architectures — A Comprehensive Survey. In: INTERNATIONAL CONFERENCE ON ADVANCED SCIENCE AND ENGINEERING TECHNOLOGIES (ASET), 2022. **Proceedings** [...]. IEEE, 21 fev. 2022. DOI: 10.1109/ASET53988.2022.9735024.

OLIST. **Brazilian E-Commerce Public Dataset by Olist**. Kaggle, 2024. Disponível em: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce. Acesso em: 28 mar. 2026.

OLIVEIRA, M. **O panorama do e-commerce no Brasil**: tendências e desafios. São Paulo: Varejo Digital, 2022. 41 p.

ORGANIZAÇÃO DAS NAÇÕES UNIDAS NO BRASIL. **As Nações Unidas no Brasil**. Brasília: ONU Brasil, 2024. Disponível em: https://brasil.un.org/pt-br. Acesso em: 28 mar. 2026.

PEREIRA, T. **Logística verde e a economia de baixo carbono**. Manaus: EcoLog, 2024. 29 p.

PERLIN, Rodrigo et al. An Approach to Follow Microservices Principles in Frontend. In: IEEE INTERNATIONAL CONFERENCE ON ADVANCED INFORMATION TECHNOLOGIES (AICT), 2023. **Proceedings** [...]. IEEE, 18 out. 2023. DOI: 10.1109/aict59525.2023.10313208.

PROGRAMA BRASILEIRO GHG PROTOCOL. **Ferramenta de cálculo**. São Paulo: FGVces, 2026. Disponível em: https://ghgprotocolbrasil.com.br/ferramentas. Acesso em: 17 maio 2026.

RAMÍREZ, Sebastián. **FastAPI**: high performance web framework for building APIs with Python. Versão 0.141. [S. l.]: Tiangolo, 2024. Disponível em: https://fastapi.tiangolo.com. Acesso em: 9 set. 2026.

RAPPL, Florian. **The Art of Micro Frontends**: Build websites using compositional UIs that grow naturally as your application scales. 2. ed. Birmingham: Packt Publishing, 2024. 356 p.

RATTANUKUL, Pattarakrit et al. Microusity: A testing tool for Backends for Frontends (BFF) Microservice Systems. In: INTERNATIONAL CONFERENCE ON PROGRAM COMPREHENSION (ICPC), 2023. **Proceedings** [...]. IEEE, maio 2023. DOI: 10.1109/icpc58990.2023.00021.

REDIS. **Redis documentation**: in-memory data store and caching strategies. [S. l.]: Redis Ltd., 2024. Disponível em: https://redis.io/docs. Acesso em: 9 set. 2026.

ROCHA, Hugo Filipe Oliveira. **Practical Event-Driven Microservices Architecture**: Building Sustainable and Highly Scalable Event-Driven Microservices. New York: Apress, 2022. 469 p.

SILVA, Sérgio Ferrigo da. **Inovação sustentável integrando Internet das coisas à logística 5.0**: armazéns inteligentes como infraestruturas de serviço de apoio à sociedade. 2023. 152 p. Tese (Doutorado em Administração) – Universidade de Caxias do Sul, Caxias do Sul, 2023.

SIMÃO, Angelo Guimarães; SALLES, Dayane Martins; FERNANDES, Valdir. Plataformas digitais de indicadores dos ODS: origem, abrangência e transparência. **Revista Tecnologia e Sociedade**, v. 20, n. 59, 15 abr. 2024. DOI: 10.3895/rts.v20n59.17828.

SMART FREIGHT CENTRE. **Global Logistics Emissions Council Framework for Logistics Emissions Accounting and Reporting (GLEC Framework)**. Versão 3.0. Amsterdam: Smart Freight Centre, 2023. 164 p. Disponível em: https://www.smartfreightcentre.org/en/glec-framework/. Acesso em: 9 set. 2026.

TRANSVIAS. **Pegada de carbono no transporte de cargas**: como reduzir impactos ambientais. [S. l.], 6 out. 2025. Disponível em: https://noticias.transvias.com.br/2025/10/06/pegada-carbono-transporte-cargas/. Acesso em: 16 abr. 2026.

W3C. **Web Content Accessibility Guidelines (WCAG) 2.1**. [S. l.]: World Wide Web Consortium, 2018. Disponível em: https://www.w3.org/TR/WCAG21/. Acesso em: 2 nov. 2026.

WORLD ECONOMIC FORUM. **Transforming Urban Logistics**. [S. l.]: World Economic Forum, 2024. Disponível em: https://www.weforum.org/publications/transforming-urban-logistics-a-path-to-sustainable-and-efficient-last-mile-delivery-in-cities/. Acesso em: 13 out. 2026.

ZUBAIDAH, Tantri Risda et al. Sustainable Business of E-Commerce in the Smart Economy: A Systematic Review of Roles and Challenges for Future Research. In: INTERNATIONAL CONFERENCE ON INFORMATION SYSTEMS AND SOFTWARE ENGINEERING (ICISS), 2024. **Proceedings** [...]. IEEE, 2024. DOI: 10.1109/iciss62896.2024.10751282.

## CAPÍTULO 3 — AJUSTES

<!-- Devolutiva do orientador à P5 (02/11): priorizar a documentação; se a API rodou
no hospedeiro com desempenho satisfatório, atualizar a seção 3. A evolução do motor
de CO₂ continua declarada no Cap. 4. Cada bloco: "### <início do parágrafo do
template>" e o texto que o substitui (parágrafos extras entram logo depois).
Redações de docs/tese-rastreabilidade.md §5, conferidas contra o código em 02/11. -->

### O ambiente de desenvolvimento será organizado

O ambiente de desenvolvimento será organizado com Docker e Docker Compose para os serviços de persistência, PostgreSQL e Redis, executados em contêineres. A API FastAPI e o front-end, desenvolvido em Next.js (React), serão executados diretamente no hospedeiro, porque, no ambiente Windows utilizado, o Docker opera sobre uma máquina virtual (WSL2), o que acrescentaria uma camada de virtualização ao caminho medido. O código-fonte será mantido em um repositório Git, e as dependências serão registradas em arquivos próprios de cada serviço, facilitando a reprodução do ambiente utilizado nos testes.

### Os testes de desempenho e estresse serão executados

Os testes de desempenho e estresse serão executados utilizando a ferramenta Locust, adotando-se o padrão de carga em degraus (*step-load pattern*) para simular o comportamento concorrente de usuários na interface web. A carga será aplicada de forma progressiva sobre a jornada de navegação completa: a tela inicial em quatro variações de contexto (padrão, especialista em eletrônicos, consumidor consciente e busca), o detalhe de produto e a simulação de checkout, todas montadas pelo orquestrador SDUI e com cálculo de distância e pegada de carbono. As estatísticas serão registradas por rota, o que permitirá isolar o *endpoint* de orquestração da tela inicial na análise. As requisições serão intercaladas com um tempo de reflexão (*think time*) parametrizado entre um e três segundos, modelando a navegação humana no catálogo de produtos.

### O protocolo experimental adotará

O protocolo experimental adotará procedimentos de isolamento de variáveis para neutralizar interferências transientes do sistema operacional e oscilações no agendamento de processos em segundo plano. Cada um dos cenários dimensionados será executado em triplicata (três ensaios independentes) sob três estados da camada de persistência transitória em Redis: cache desabilitado, cache frio (*cold cache*) e cache aquecido (*warm cache*). No primeiro estado (*bypass* integral), o sistema é forçado a percorrer todo o ciclo computacional, que compreende a consulta relacional no PostgreSQL, o cálculo geodésico de Haversine e a montagem dinâmica da árvore de nós da SDUI, fixando a linha de base (*baseline*) de esforço da CPU e de saturação de conexões. O estado "cache desabilitado" refere-se exclusivamente à camada de respostas em Redis; duas outras camadas permanecem ativas nos três estados e fazem parte da linha de base: a tabela de centroides de CEP (cerca de 12,9 mil linhas de dado de referência estático), mantida em memória no processo da aplicação, e o cache de páginas do próprio PostgreSQL. No estado de cache frio, a persistência em memória é inicializada vazia para mensurar a penalidade de processamento decorrente de rajadas simultâneas de falhas de localização de chaves (*cache misses*). Por fim, o cache aquecido é condicionado por um ciclo prévio de requisições (*pre-warming*): o próprio ensaio de cache frio, executado imediatamente antes e com a mesma semente de sorteio dos CEPs, de modo que os usuários virtuais do ensaio aquecido requisitam exatamente as chaves que o ensaio frio deixou em memória. A mesma semente será usada nas três condições de cada cenário, para que os três estados sejam comparados sobre a mesma população de compradores (comparação pareada), e os CEPs serão sorteados da distribuição real de clientes da amostra, de modo que a taxa de acerto do cache reflita a concentração geográfica efetiva da demanda. O tempo de vida das chaves será fixado em 3.600 s, superior à duração de um par frio–aquecido. Para suprimir ruídos decorrentes de atrasos dinâmicos de rede externa (*jitter* e perda de pacotes), o motor de aplicação e o gerador de carga Locust serão executados no mesmo hospedeiro e se comunicarão pela interface de *loopback*, sem atravessar qualquer rede física; a base de dados PostgreSQL e o Redis executarão em contêineres Docker no mesmo hospedeiro.

Os ensaios utilizarão um único processo de aplicação (um *worker* do servidor ASGI) e os *pools* de conexões padrão das bibliotecas: no PostgreSQL, 5 conexões fixas e 10 adicionais, com tempo limite de 30 s (SQLAlchemy); no Redis, até 100 conexões, com espera de até 5 s por uma conexão livre. Esgotado o *pool* do PostgreSQL, a requisição resulta em resposta HTTP 500, contabilizada como falha. Os registros de SQL da aplicação serão desligados durante as medições. As estatísticas descritivas considerarão apenas o regime permanente (*plateau*); a série temporal completa, incluindo a rampa, será preservada para a análise da penalidade de *cache misses* no estado frio.

### Como forma de avaliar a influência dessa simplificação

Para a estimativa de emissões, a distância de Haversine é convertida em distância rodoviária pelo fator de circuidade de 1,345, média brasileira entre a distância por rodovia e a distância euclidiana (LEE; CHAE, 2023). Como forma de avaliar a influência dessa simplificação, será selecionada uma amostra de 100 pares de origem e destino extraídos de compras reais do conjunto de dados, 20 em cada faixa de distância em linha reta (até 100 km, de 100 a 500 km, de 500 a 1.000 km, de 1.000 a 2.000 km e acima de 2.000 km). Para cada par, a distância de Haversine, crua e convertida pelo fator de circuidade, será comparada com a distância da rota calculada pelo Open Source Routing Machine (OSRM), serviço baseado na malha viária do OpenStreetMap, entre os mesmos centroides de prefixo de CEP utilizados pelo sistema. A comparação será realizada por meio do erro absoluto médio (MAE), do erro percentual absoluto médio (MAPE) e do coeficiente de correlação de Spearman.

### A utilização dessas métricas permitirá

Também será verificado se os dois métodos preservam a ordenação dos vendedores em decisões reais de compra: para compradores de produtos ofertados por vendedores em localidades distintas, será medido o percentual de casos em que o vendedor mais próximo em linha reta é também o mais próximo pela rota, o percentual de pares de vendedores ordenados da mesma forma pelos dois métodos e, nos casos divergentes, a distância rodoviária adicional decorrente da escolha por linha reta. A utilização dessas métricas permitirá verificar não somente a diferença entre as distâncias calculadas, mas também se a aproximação de Haversine é capaz de manter a finalidade principal do sistema: identificar comparativamente as alternativas de menor impacto ambiental. Caso sejam constatadas divergências relevantes, as limitações do método serão apresentadas na análise dos resultados, e as distâncias fornecidas pelo sistema serão classificadas explicitamente como estimativas comparativas.
