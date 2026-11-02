# Desempenho no cliente (build de produção)

> Gerado por `node scripts/desempenho-cliente.mjs` (de `web/`) no commit `8544e3b`. Next.js em
> produção (`next build` + `next start`), API local com cache de respostas ligado, Chromium do
> Playwright, 10 rodadas com contexto novo (primeira visita, sem cache HTTP). CEP 05311.
> "Celular simulado" = 390 px com a CPU 4× mais lenta (Chrome DevTools).

## Página inicial (renderizada no servidor a partir da ScreenResponse)

| Métrica | Mediana | p90 |
|---|---|---|
| Desktop — tempo até o primeiro byte | 15 ms | 20 ms |
| Desktop — primeira pintura (FCP) | 140 ms | 192 ms |
| Desktop — maior pintura (LCP) | 140 ms | 192 ms |
| Desktop — carga completa | 177 ms | 237 ms |
| Celular simulado — FCP | 442 ms | 520 ms |
| Celular simulado — LCP | 442 ms | 520 ms |
| Celular simulado — carga completa | 1.041 ms | 1.156 ms |

Deslocamento de layout acumulado (CLS): mediana 0,006 no desktop e 0,000 no celular simulado (bom: abaixo de 0,1).

## Interações (tela pedida ao servidor e interpretada no cliente)

| Interação | Mediana | p90 |
|---|---|---|
| Clique no produto → detalhe com comparador na tela | 150 ms | 244 ms |
| Simular compra → checkout com modalidades na tela | 83 ms | 101 ms |

JavaScript enviado ao navegador: ~190 KB comprimidos (620 KB sem compressão), em 10 arquivos
(`.next/static/chunks`).

**Referências do Google para Core Web Vitals:** LCP bom até 2,5 s; CLS bom até 0,1.
