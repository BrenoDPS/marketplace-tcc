PRD: Marketplace Contextual Adaptativo (Olist + ODS 9/12)
1. Visão Geral
Marketplace baseado no dataset Olist que utiliza Server-Driven UI (SDUI) para personalização de interface e incentivo à Logística Verde (ODS 12).

Alinhamento ODS:
ODS 9: Inovação na infraestrutura de software para pequenas empresas (vendedores Olist).
ODS 12: Incentivo ao consumo responsável via "Logística Verde".

2. Objetivos
SDUI: Orquestrar componentes de UI pelo backend para evitar deploys no front-end.

Logística Verde: Identificar e priorizar entregas locais para redução da pegada de carbono.

3. Personas e Cenários
Consumidor Consciente: Busca reduzir sua pegada de carbono. A UI deve destacar produtos de vendedores geograficamente próximos.

Microempreendedor (Seller): Pequeno lojista que ganha visibilidade através de uma infraestrutura de tecnologia de ponta democratizada.

4. Funcionalidades
Home Contextual: Layouts dinâmicos baseados na categoria (Ex: Eletrônicos vs Beleza).

Motor de Proximidade: Cálculo em tempo real da distância Vendedor-Comprador via CEP.

Sustainability Badge: Injeção automática de selo de "Logística Verde" para entregas locais (< 100km).

Checkout Simulado: Fluxo completo de compra com validação de frete e impacto ambiental.

Sistema de Ações Dinâmicas: Botões e cliques cujas ações (navegação, chamada de API, abertura de modal) são definidas pelo servidor.

5. Métricas de Sucesso
Latência: < 200ms (com auxílio de cache Redis) em cenários de alta concorrência.

> **Nota da Sprint 6 (medição):** a premissa entre parênteses não se confirmou. A meta é
> atingida **sem Redis** — o gargalo era um N+1 de consultas, não falta de cache. Acima de
> ~25 usuários simultâneos o limite passa a ser o número de processos da API, não o banco.
> O requisito de latência permanece; o meio previsto para alcançá-lo foi revisto. Ver
> `docs/performance.md`.

Arquitetura: Vertical Slice Architecture (VSA) para isolamento de funcionalidades.