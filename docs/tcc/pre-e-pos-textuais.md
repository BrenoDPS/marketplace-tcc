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

OLIST. **Como calcular o frete dos produtos para envio pelos Correios?** São Paulo: Olist, 20 set. 2022. Disponível em: https://olist.com/blog/pt/gestao-empresarial/operacao-e-logistica/como-calcular-o-frete-dos-produtos-na-loja-virtual/. Acesso em: 13 out. 2026.

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

SMART FREIGHT CENTRE. **Global Logistics Emissions Council Framework for Logistics Emissions Accounting and Reporting**. Version 2.0. Amsterdam: Smart Freight Centre, 2019. Atualizado em 2022. Disponível em: https://www.smartfreightcentre.org/en/glec-framework/. Acesso em: 9 set. 2026.

SMART FREIGHT CENTRE. **Global Logistics Emissions Council Framework for Logistics Emissions Accounting and Reporting (GLEC Framework)**. Versão 3.0. Amsterdam: Smart Freight Centre, 2023. 164 p. Disponível em: https://www.smartfreightcentre.org/en/glec-framework/. Acesso em: 9 set. 2026.

TRANSVIAS. **Pegada de carbono no transporte de cargas**: como reduzir impactos ambientais. [S. l.], 6 out. 2025. Disponível em: https://noticias.transvias.com.br/2025/10/06/pegada-carbono-transporte-cargas/. Acesso em: 16 abr. 2026.

W3C. **Web Content Accessibility Guidelines (WCAG) 2.1**. [S. l.]: World Wide Web Consortium, 2018. Disponível em: https://www.w3.org/TR/WCAG21/. Acesso em: 2 nov. 2026.

WORLD ECONOMIC FORUM. **Transforming Urban Logistics**. [S. l.]: World Economic Forum, 2024. Disponível em: https://www.weforum.org/publications/transforming-urban-logistics-a-path-to-sustainable-and-efficient-last-mile-delivery-in-cities/. Acesso em: 13 out. 2026.

ZUBAIDAH, Tantri Risda et al. Sustainable Business of E-Commerce in the Smart Economy: A Systematic Review of Roles and Challenges for Future Research. In: INTERNATIONAL CONFERENCE ON INFORMATION SYSTEMS AND SOFTWARE ENGINEERING (ICISS), 2024. **Proceedings** [...]. IEEE, 2024. DOI: 10.1109/iciss62896.2024.10751282.
