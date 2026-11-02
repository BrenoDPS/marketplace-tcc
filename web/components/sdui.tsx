"use client";

import { useEffect, useRef } from "react";
import { MUTACOES_DEMO, brl } from "@/lib/sdui";
import type { ScreenResponse, UIComponent } from "@/lib/sdui";
import {
  CategoryGrid,
  CheckoutSummary,
  ContentSection,
  DataTable,
  DeliveryOptions,
  HeroBanner,
  ImpactBanner,
  OfferComparison,
  OriginMap,
  ProductCard,
  ProductDetail,
  ShipmentBreakdown,
  Stepper,
} from "./blocks";
import { Icon } from "./icons";
import { useSdui } from "./sdui-context";

/**
 * Mapa `component.type` -> componente React. Um bloco que o servidor mande e
 * este cliente ainda nao conheca renderiza `null`: a tela degrada, nao quebra.
 * Bloco novo no backend = uma linha aqui.
 */
const REGISTRY = {
  hero_banner: HeroBanner,
  category_grid: CategoryGrid,
  product_card: ProductCard,
  product_detail: ProductDetail,
  checkout_summary: CheckoutSummary,
  delivery_options: DeliveryOptions,
  shipment_breakdown: ShipmentBreakdown,
  impact_banner: ImpactBanner,
  offer_comparison: OfferComparison,
  origin_map: OriginMap,
  content_section: ContentSection,
  data_table: DataTable,
} as const;

/**
 * Etiqueta do modo de inspecao: o envelope do bloco e o JSON que veio do
 * servidor. Fica no fluxo (nao e popover) de proposito — dentro do `<dialog>`
 * do checkout um painel absoluto seria recortado pelo scroll do modal.
 */
function InspectorTag({ block, known }: { block: UIComponent; known: boolean }) {
  return (
    <details className="group/tag mb-2">
      <summary
        className={`inline-flex cursor-pointer list-none items-center gap-1.5 rounded-lg px-2 py-1 font-mono text-[11px] leading-none transition ${
          known ? "bg-ink text-paper hover:bg-signal" : "bg-danger text-paper"
        }`}
      >
        {block.type} · v{block.version}
        {block.actions.length > 0 && <span className="opacity-60">{block.actions.length} action(s)</span>}
        {!known && <span>· sem renderer</span>}
        <Icon name="chevronDown" className="size-3 opacity-60 transition group-open/tag:rotate-180" />
      </summary>
      <pre className="mt-2 max-h-64 overflow-auto rounded-xl bg-ink p-3 font-mono text-xs leading-relaxed text-paper">
        {JSON.stringify(block, null, 2)}
      </pre>
    </details>
  );
}

function Block({ block }: { block: UIComponent }) {
  const { inspecting } = useSdui();
  const Component = REGISTRY[block.type as keyof typeof REGISTRY] as
    | ((props: { block: UIComponent }) => React.ReactNode)
    | undefined;

  if (!inspecting) return Component ? <Component block={block} /> : null;

  // Fora da inspecao o bloco desconhecido renderiza `null` — a tela degrada em
  // silencio. Com a inspecao ligada ele APARECE, porque "o servidor mandou algo
  // que este cliente nao conhece" e exatamente o que o modo existe para mostrar.
  // Contorno fino que acende no hover (redesign): o tracejado em tudo sujava a tela.
  return (
    <div className="rounded-2xl p-1.5 ring-1 ring-signal/25 transition hover:ring-2 hover:ring-signal/60">
      <InspectorTag block={block} known={Component !== undefined} />
      {Component ? (
        <Component block={block} />
      ) : (
        <p className="rounded-xl border border-dashed border-danger/40 bg-danger-soft p-4 text-sm text-danger">
          Bloco <code>{block.type}</code> não tem componente no <code>REGISTRY</code>.
          Sem o modo de inspeção ele seria omitido silenciosamente.
        </p>
      )}
    </div>
  );
}

/**
 * Hora em que ESTE bundle foi avaliado no navegador. O modo apresentacao a
 * exibe fixa: se as mutacoes recarregassem a pagina ou reconstruissem o JS, ela
 * mudaria. E a versao visivel do marcador `window.__contexto` do E2E.
 */
const CARREGADA_EM = new Date().toLocaleTimeString("pt-BR");

/** Cabecalho do modo de inspecao: a tela inteira e uma resposta do servidor. */
function ScreenMeta({ screen }: { screen: ScreenResponse }) {
  const { mutacao } = useSdui();
  const meta = [
    ["screen_id", screen.screen_id],
    ["context", screen.context],
    ["schema_version", String(screen.schema_version)],
    ["components", String(screen.components.length)],
  ];

  return (
    <section className="rounded-2xl bg-ink p-4 text-paper shadow-lift sm:p-5">
      <p className="flex items-center gap-2 font-mono text-xs text-signal-strong">
        <Icon name="code" className="size-4" />
        ScreenResponse
      </p>
      <dl className="mt-3 flex flex-wrap gap-x-6 gap-y-1 font-mono text-xs text-paper/60">
        {meta.map(([k, v]) => (
          <div key={k} className="flex gap-1.5">
            <dt>{k}:</dt>
            <dd className="text-paper">{v}</dd>
          </div>
        ))}
      </dl>
      <p className="mt-3 font-mono text-xs leading-relaxed text-paper/80">
        {screen.components.map((c) => c.type).join(" → ")}
      </p>
      <p className="mt-2 font-mono text-xs text-paper/50">
        mesma página desde {CARREGADA_EM}
        {mutacao && <span className="text-signal-strong"> · mutação do servidor: {mutacao}</span>}
      </p>
    </section>
  );
}

/**
 * Agrupa `product_card` consecutivos numa grade; demais blocos ficam em fluxo.
 * `anchors` da a cada bloco um `id` igual ao `type`, para as etapas do checkout
 * levarem ate ele.
 */
export function ScreenRenderer({
  screen,
  anchors = false,
}: {
  screen: ScreenResponse;
  anchors?: boolean;
}) {
  const { inspecting } = useSdui();
  const groups: UIComponent[][] = [];
  for (const block of screen.components) {
    const last = groups.at(-1);
    if (block.type === "product_card" && last?.[0]?.type === "product_card") {
      last.push(block);
    } else {
      groups.push([block]);
    }
  }

  return (
    <div className="space-y-6 sm:space-y-8">
      {inspecting && <ScreenMeta screen={screen} />}
      {groups.map((group, i) =>
        group[0].type === "product_card" ? (
          <div key={i} className="space-y-3">
            {/* Quantos produtos a vitrine tem: a contagem que faltava (redesign). */}
            {screen.screen_id === "home" && (
              <p className="text-sm text-muted">
                <span className="font-medium text-ink">{group.length}</span>{" "}
                {group.length === 1 ? "produto nesta vitrine" : "produtos nesta vitrine"}
              </p>
            )}
            <div className="grid grid-cols-2 gap-3 sm:gap-5 lg:grid-cols-3 [&>*]:min-w-0">
              {group.map((block, j) => (
                <Block key={j} block={block} />
              ))}
            </div>
          </div>
        ) : anchors ? (
          <div key={i} id={group[0].type} tabIndex={-1} className="scroll-mt-24 outline-none">
            <Block block={group[0]} />
          </div>
        ) : (
          <Block key={i} block={group[0]} />
        ),
      )}
    </div>
  );
}

/**
 * `<dialog>` nativo: Esc, foco preso e backdrop sem codigo nosso. Redesign
 * (02/11): cabecalho fixo com titulo e fechar, corpo com rolagem PROPRIA (o
 * scroll do dialog cortava o arredondamento) e rodape opcional fixo.
 */
function Modal({
  open,
  onClose,
  wide = false,
  title,
  header,
  footer,
  children,
}: {
  open: boolean;
  onClose: () => void;
  /** O detalhe tem duas colunas e o comparador; 34rem espreme. */
  wide?: boolean;
  title: React.ReactNode;
  /** Substitui o titulo no cabecalho (o seletor de mutacao do modo apresentacao). */
  header?: React.ReactNode;
  footer?: React.ReactNode;
  children: React.ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (open && !el.open) el.showModal();
    if (!open && el.open) el.close();
  }, [open]);

  return (
    <dialog
      ref={ref}
      onClose={onClose}
      onClick={(e) => e.target === ref.current && onClose()}
      className={`m-auto max-h-[min(92dvh,56rem)] overflow-hidden rounded-3xl border border-line bg-paper p-0 text-ink shadow-float ${
        wide ? "w-[min(52rem,calc(100vw-1.5rem))]" : "w-[min(34rem,calc(100vw-1.5rem))]"
      }`}
    >
      {open && (
        <div className="flex max-h-[min(92dvh,56rem)] flex-col">
          <div className="flex items-center justify-between gap-4 border-b border-line bg-surface px-5 py-3.5 sm:px-6">
            <div className="min-w-0">{header ?? title}</div>
            <button
              type="button"
              onClick={onClose}
              aria-label="Fechar"
              className="flex size-9 shrink-0 items-center justify-center rounded-full text-muted transition hover:bg-paper-2 hover:text-ink"
            >
              <Icon name="x" className="size-5" />
            </button>
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-5 py-5 sm:px-6">{children}</div>
          {footer && <div className="border-t border-line bg-surface px-5 py-4 sm:px-6">{footer}</div>}
        </div>
      )}
    </dialog>
  );
}

/** Forma do detalhe enquanto o GET nao volta: o modal nao pula de tamanho (D11). */
function DetailSkeleton() {
  const bar = "rounded-lg bg-line/70";
  return (
    <div role="status" aria-label="Carregando detalhe" className="animate-pulse space-y-5">
      <div className="grid gap-5 rounded-2xl border border-line bg-surface p-5 sm:grid-cols-[13rem_minmax(0,1fr)]">
        <div className={`${bar} aspect-square rounded-2xl`} />
        <div className="space-y-4">
          <div className={`${bar} h-7 w-2/3`} />
          <div className={`${bar} h-4 w-1/2`} />
          <div className={`${bar} h-10 w-40`} />
          <div className="grid grid-cols-3 gap-3">
            <div className={`${bar} h-14`} />
            <div className={`${bar} h-14`} />
            <div className={`${bar} h-14`} />
          </div>
          <div className={`${bar} h-11 w-full rounded-xl`} />
        </div>
      </div>
      <div className={`${bar} h-28 rounded-2xl`} />
    </div>
  );
}

/** Modo apresentacao (V9): escolhe a mutacao que o BFF aplica a este detalhe. */
function MutationPicker() {
  const { mutacao, setMutacao } = useSdui();
  return (
    <label className="flex flex-wrap items-center gap-2 text-xs text-muted">
      <Icon name="code" className="size-4 text-signal" />
      Mutação do servidor
      <select
        value={mutacao ?? ""}
        onChange={(e) => setMutacao(e.target.value || null)}
        className="rounded-lg border border-signal/40 bg-signal-soft px-2.5 py-1 text-xs text-signal-ink"
      >
        <option value="">Nenhuma (árvore original)</option>
        {MUTACOES_DEMO.map((m) => (
          <option key={m.value} value={m.value}>
            {m.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function ModalTitle({ eyebrow, children }: { eyebrow: string; children?: React.ReactNode }) {
  return (
    <div>
      <p className="text-[11px] font-medium uppercase tracking-[0.16em] text-muted">{eyebrow}</p>
      {children}
    </div>
  );
}

/**
 * Detalhe do produto. Chega inteiro de `GET /products/{id}` e o MESMO
 * renderer desenha; o que sobra aqui e a moldura do modal.
 */
function DetailBody() {
  const { detail, pending, error } = useSdui();
  return (
    <>
      {error && (
        <p className="mb-4 flex items-center gap-2 rounded-xl bg-danger-soft px-4 py-3 text-sm text-danger">
          <Icon name="info" className="size-4" />
          {error}
        </p>
      )}
      {detail ? <ScreenRenderer screen={detail} /> : !error && pending && <DetailSkeleton />}
    </>
  );
}

function CartBody() {
  const { cart, error, setQuantity, removeFromCart } = useSdui();

  if (cart.length === 0) {
    return (
      <div className="py-8 text-center">
        <span className="mx-auto flex size-14 items-center justify-center rounded-2xl bg-paper-2 text-muted">
          <Icon name="bag" className="size-6" />
        </span>
        <p className="mt-4 font-display text-xl text-ink">Nenhum produto ainda</p>
        <p className="mx-auto mt-2 max-w-xs text-sm text-muted">
          Escolha produtos na vitrine para simular uma compra. Itens do mesmo vendedor viajam numa remessa só.
        </p>
      </div>
    );
  }

  return (
    <>
      <ul className="space-y-3">
        {cart.map((entry) => {
          const nome = entry.title ?? entry.productId;
          return (
            <li key={entry.productId} className="flex flex-wrap items-center gap-3 rounded-2xl border border-line bg-surface p-3 shadow-soft">
              <span className="flex size-11 items-center justify-center rounded-xl bg-paper-2 text-muted">
                <Icon name="box" className="size-5" />
              </span>
              <div className="min-w-0 flex-1 basis-[calc(100%-6.5rem)] sm:basis-0">
                <p className="truncate text-sm font-medium text-ink">{nome}</p>
                <p className="mt-0.5 text-xs tabular-nums text-muted">{brl(entry.price)} cada</p>
              </div>
              <div className="order-last ml-14 sm:order-none sm:ml-0">
                <Stepper value={entry.quantity} onChange={(n) => setQuantity(entry.productId, n)} label={nome} />
              </div>
              <span className="order-last ml-auto w-20 text-right sm:order-none sm:ml-0 text-sm font-medium tabular-nums text-ink">{brl(entry.price * entry.quantity)}</span>
              <button
                type="button"
                onClick={() => removeFromCart(entry.productId)}
                aria-label={`Remover ${nome}`}
                className="flex size-8 items-center justify-center rounded-lg text-muted transition hover:bg-danger-soft hover:text-danger"
              >
                <Icon name="x" className="size-4" />
              </button>
            </li>
          );
        })}
      </ul>
      {error && <p className="mt-4 text-sm text-danger">{error}</p>}
    </>
  );
}

function CartFooter() {
  const { cart, checkoutAction, pending, run } = useSdui();
  const subtotal = cart.reduce((sum, e) => sum + e.price * e.quantity, 0);
  return (
    <>
      <div className="flex items-baseline justify-between text-sm">
        <span className="text-muted">Subtotal (sem frete)</span>
        <span className="font-display text-2xl tabular-nums text-ink">{brl(subtotal)}</span>
      </div>
      <button
        type="button"
        disabled={!checkoutAction || pending}
        onClick={() => checkoutAction && run(checkoutAction)}
        className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-signal px-5 py-3 text-sm font-medium text-on-signal shadow-soft transition hover:bg-signal-strong disabled:opacity-50"
      >
        {pending ? "Simulando…" : "Simular compra"}
      </button>
      <p className="mt-2.5 text-center text-xs text-muted">
        {/* A acao de checkout vem do servidor nos cards da vitrine; uma busca vazia
            aberta direto pela URL nao tem card, entao nao ha acao ate voltar a vitrine. */}
        {checkoutAction
          ? "Simulação acadêmica — nenhum pagamento é processado."
          : "Volte à vitrine para simular a compra destes itens."}
      </p>
    </>
  );
}

/** Etapa -> bloco do checkout onde ela comeca. O servidor manda os blocos; o
 * cliente so sabe por qual `type` cada etapa se ancora. "Impacto e remessas"
 * (D9): as remessas nao tinham atalho. */
const STEPS = [
  { label: "Carrinho", target: "checkout_summary" },
  { label: "Entrega", target: "delivery_options" },
  { label: "Impacto e remessas", target: "shipment_breakdown" },
] as const;

/**
 * Checkout como PAGINA (D5). Ate a Sprint 13 era um modal com rolagem interna,
 * e remessas e alternativas ficavam abaixo da dobra. Continua server-driven: o
 * conteudo e a mesma `ScreenResponse` do POST, desenhada pelo mesmo renderer.
 */
function CheckoutPage({ screen, onBack }: { screen: ScreenResponse; onBack: () => void }) {
  const { openCart, pending } = useSdui();
  const present = new Set(screen.components.map((c) => c.type));
  const goTo = (id: string) => {
    const el = document.getElementById(id);
    el?.scrollIntoView({ behavior: "smooth", block: "start" });
    el?.focus({ preventScroll: true });
  };
  const etapas = STEPS.filter((step) => present.has(step.target));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <button type="button" onClick={onBack} className="rounded-lg px-1 text-sm text-muted transition hover:text-ink">
            ← Voltar à vitrine
          </button>
          <p className="mt-4 text-[11px] font-medium uppercase tracking-[0.16em] text-muted">Checkout</p>
          <h1 className="mt-1 font-display text-4xl tracking-tight text-ink sm:text-5xl">Compra simulada</h1>
        </div>
        <button
          type="button"
          onClick={() => openCart(true)}
          className="flex items-center gap-2 rounded-xl border border-line bg-surface px-4 py-2 text-sm font-medium text-ink shadow-soft transition hover:border-line-strong"
        >
          <Icon name="bag" className="size-4" />
          Editar carrinho
        </button>
      </div>

      <nav aria-label="Etapas da compra" className="no-scrollbar -mx-4 overflow-x-auto px-4 sm:mx-0 sm:px-0">
        <ol className="flex w-max items-center gap-2">
          {etapas.map((step, i) => (
            <li key={step.target} className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => goTo(step.target)}
                className="flex items-center gap-2 whitespace-nowrap rounded-xl border border-line bg-surface px-3 py-2 text-sm font-medium text-ink shadow-soft transition hover:border-line-strong hover:shadow-lift"
              >
                <span className="flex size-6 items-center justify-center rounded-lg bg-ink text-xs font-semibold text-paper">
                  {i + 1}
                </span>
                {step.label}
              </button>
              {i < etapas.length - 1 && <span aria-hidden className="h-px w-6 bg-line-strong" />}
            </li>
          ))}
        </ol>
      </nav>

      {/* Trocar modalidade ou vendedor refaz o POST: a tela inteira muda junto
          (frete, CO2, selo), entao ela inteira sinaliza que esta sendo refeita. */}
      <p role="status" className="min-h-4 text-xs text-muted">
        {pending ? "Recalculando frete e emissão…" : ""}
      </p>
      <div aria-busy={pending} className={`transition-opacity ${pending ? "opacity-60" : ""}`}>
        <ScreenRenderer screen={screen} anchors />
      </div>
    </div>
  );
}

/** Parametro de URL da pagina de checkout: da endereco, voltar e recarga a ela. */
export const CHECKOUT_STEP_PARAM = "etapa";

export function Host({ children }: { children: React.ReactNode }) {
  const { detailOpen, checkout, cartOpen, closeDetail, openCart, closeCheckout, navigating, inspecting, cart } =
    useSdui();
  // "1 produto" conta LINHAS do carrinho, como antes (o E2E procura esse titulo).
  const cartCount = cart.length;
  // So volta pelo historico se fomos NOS que empilhamos a entrada; quem chegou
  // pela URL ja com `?etapa=checkout` (recarga) sairia do site com o back.
  const pushed = useRef(false);
  const wasOpen = useRef(false);

  // A pagina de checkout tem URL: `pushState` no lugar de navegar, porque o
  // conteudo e estado do cliente (a resposta do POST), nao uma rota do servidor.
  useEffect(() => {
    const url = new URL(window.location.href);
    const onUrl = url.searchParams.get(CHECKOUT_STEP_PARAM) === "checkout";
    if (checkout && !onUrl) {
      url.searchParams.set(CHECKOUT_STEP_PARAM, "checkout");
      window.history.pushState(null, "", url);
      pushed.current = true;
      window.scrollTo(0, 0);
    } else if (!checkout && onUrl && wasOpen.current) {
      // So ao FECHAR: na recarga o parametro chega antes da simulacao, e e
      // ele que diz ao provider para refaze-la.
      url.searchParams.delete(CHECKOUT_STEP_PARAM);
      window.history.replaceState(null, "", url);
    }
    wasOpen.current = checkout !== null;
  }, [checkout]);

  useEffect(() => {
    const onPop = () => {
      const onUrl = new URL(window.location.href).searchParams.get(CHECKOUT_STEP_PARAM);
      if (onUrl !== "checkout") {
        pushed.current = false;
        closeCheckout();
      }
    };
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, [closeCheckout]);

  const back = () => (pushed.current ? window.history.back() : closeCheckout());

  return (
    <>
      {checkout ? (
        <CheckoutPage screen={checkout} onBack={back} />
      ) : (
        <div aria-busy={navigating} className={`transition-opacity ${navigating ? "opacity-50" : ""}`}>
          {children}
        </div>
      )}
      <Modal
        open={detailOpen}
        onClose={closeDetail}
        wide
        title={<ModalTitle eyebrow="Produto" />}
        header={inspecting ? <MutationPicker /> : undefined}
      >
        <DetailBody />
      </Modal>
      {/* Tambem sobre a pagina de checkout: "Editar carrinho" reabre o modal,
          e "Simular compra" atualiza a pagina com a resposta nova. */}
      <Modal
        open={cartOpen}
        onClose={() => openCart(false)}
        title={
          <ModalTitle eyebrow="Carrinho">
            <h2 className="font-display text-2xl text-ink">
              {cartCount === 0 ? "Vazio por enquanto" : `${cartCount} ${cartCount === 1 ? "produto" : "produtos"}`}
            </h2>
          </ModalTitle>
        }
        footer={cartCount > 0 ? <CartFooter /> : undefined}
      >
        <CartBody />
      </Modal>
    </>
  );
}

/**
 * Ponto de entrada da tela. O `SduiProvider` fica um nivel acima, em
 * `app/page.tsx`, porque o header tambem precisa dele: o botao do carrinho
 * mostra a contagem e abre o modal.
 */
export function SduiRoot({ screen, before }: { screen: ScreenResponse; before?: React.ReactNode }) {
  return (
    <Host>
      {/* `before` vem do Server Component (a barra de perfis): com chave propria,
          o React nao o trata como item de lista sem `key`. */}
      <div className="space-y-6 sm:space-y-8">
        <div key="antes">{before}</div>
        <ScreenRenderer key="tela" screen={screen} />
      </div>
    </Host>
  );
}
