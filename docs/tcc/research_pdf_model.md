# Modelo de escrita dos capítulos 4 a 7

## Fontes analisadas

- `ETL-DATAHUB AUTOMAÇÃO E INTEGRAÇÃO DE DADOS.pdf` (66 p.) — sumário:
  cap. 4 *Especificação do projeto*, cap. 5 *Arquitetura e tecnologias*,
  cap. 6 *Resultados*, cap. 7 *Considerações finais* (págs. ~32–66 no PDF).
- `SOFTWARE DE CODIFICAÇÃO PARA ANÁLISES QUALITATIVA.pdf` (89 p.) — sumário:
  cap. 4 *Desenvolvimento* (SDLC: planejamento → design → implementação),
  cap. 5 *Resultados* (SUS/NPS + qualitativos), cap. 6 *Discussão*, cap. 7
  *Considerações finais* (págs. ~34–69 no PDF).

Extração textual e mapa Report 6 × repositório:
[`CONTEXTO_MONOGRAFIA.md`](CONTEXTO_MONOGRAFIA.md). Regenerar texto bruto:
`python docs/tcc/_extract_tcc_docs.py` → `docs/tcc/_extracted/`.

## Padrão estrutural observado

### Capítulo 4 — desenvolvimento ou especificação

O capítulo normalmente começa com um parágrafo-guia que apresenta a ordem da
exposição. Em seguida, descreve o desenvolvimento de forma progressiva:

1. especificação do problema e dos requisitos;
2. arquitetura ou modelagem da solução;
3. implementação dos módulos e fluxos;
4. integração dos componentes;
5. ambiente de execução ou validação.

O texto é predominantemente técnico e descritivo. Cada subseção explica uma
decisão, apresenta sua materialização no sistema e conduz à próxima etapa.
Diagramas, fluxogramas, tabelas de requisitos e figuras de arquitetura são
usados para reduzir a necessidade de descrever toda a solução apenas em
prosa.

### Capítulo 5 — resultados

Os trabalhos analisados organizam os resultados por dimensão de avaliação, em
vez de seguir simplesmente a ordem em que as funcionalidades foram
implementadas. A sequência recorrente é:

1. caracterização dos dados ou da amostra;
2. resultados funcionais ou de qualidade;
3. métricas quantitativas;
4. evidências visuais ou qualitativas;
5. interpretação do atendimento aos requisitos.

Os dados aparecem primeiro em tabelas, gráficos, comparações ou exemplos
concretos. Depois de cada evidência há um parágrafo interpretativo que responde
o que o resultado significa para o problema estudado. Isso evita que o capítulo
seja apenas uma coleção de números.

O trabalho `ETL-DATAHUB` utiliza uma tabela comparativa central para evidenciar
ganhos de tempo e eficiência; o capítulo de resultados **começa pela metodologia
de testes por módulo** (ETL → repositório analítico → ciclo integrado) antes dos
números. O trabalho de software de codificação combina gráficos de SUS/NPS
(desdobrados por heurística de usabilidade), caracterização da amostra de
participantes (n e perfil) e exemplos qualitativos de uso, para triangular
resultados quantitativos e qualitativos.

### Capítulo 6 — discussão e limitações

O capítulo de discussão retoma os resultados sem apenas repeti-los. O texto:

- relaciona os achados aos objetivos e requisitos iniciais;
- explicita relações de compromisso e resultados que não confirmaram a hipótese
  original;
- diferencia evidência observada de interpretação;
- registra limitações metodológicas, de amostra e de generalização;
- apresenta melhorias ou extensões possíveis.

O tom é mais argumentativo e crítico que no capítulo de desenvolvimento.

### Capítulo 7 — conclusão

Quando existe um capítulo final separado, ele retoma o problema, os objetivos,
as contribuições, o atendimento aos requisitos e as limitações principais.
Também indica trabalhos futuros. A conclusão não deve introduzir resultados
novos: deve sintetizar o que foi demonstrado e qual é o alcance da solução.

## Padrões de redação aplicáveis a este TCC

- Abrir cada capítulo com um parágrafo que antecipe suas subseções.
- No Capítulo 4, explicar o que foi construído e como as partes se relacionam.
- No Capítulo 5, separar configuração do experimento, resultado e interpretação.
- Usar tabelas para números consolidados e figuras para arquitetura e evolução
  de métricas.
- Encerrar cada subseção de resultados com uma leitura relacionada ao objetivo
  correspondente.
- Usar linguagem cautelosa para estimativas: “estimado”, “na amostra”,
  “comparativo” e “sob as condições do experimento”.
- Declarar limites imediatamente após resultados que possam ser interpretados
  de forma excessivamente ampla.
- Fazer a transição entre subseções por função argumentativa, não apenas por
  mudança de assunto.

## Aplicação à estrutura atual

O relatório principal já propõe uma separação adequada:

- Capítulo 4: especificação, projeto e implementação.
- Capítulo 5: resultados quantitativos e qualitativo-estruturais.

Para este projeto, a ordem mais coerente é apresentar primeiro o funil e a
qualidade dos dados, depois a validação funcional do motor logístico, em seguida
os resultados de concentração regional e CO₂ evitado, e finalmente o
desempenho, a flexibilidade SDUI e a robustez do contrato.

Essa ordem acompanha o padrão observado nos PDFs e permite passar da validade
dos dados para a validade funcional, depois para impacto e desempenho.
