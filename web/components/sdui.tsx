"use client";

import { useEffect, useRef } from "react";
import { brl } from "@/lib/sdui";
import type { ScreenResponse, UIComponent } from "@/lib/sdui";
import {
  CategoryGrid,
  CheckoutSummary,
  DeliveryOptions,
  HeroBanner,
  ImpactBanner,
  ProductCard,
  ProductDetail,
  ShipmentBreakdown,
} from "./blocks";
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
} as const;

/**
 * Etiqueta do modo de inspecao: o envelope do bloco e o JSON que veio do
 * servidor. Fica no fluxo (nao e popover) de proposito — dentro do `<dialog>`
 * do checkout um painel absoluto seria recortado pelo scroll do modal.
 */
function InspectorTag({ block, known }: { block: UIComponent; known: boolean }) {
  return (
    <details className="mb-2">
      <summary
        className={`inline-flex cursor-pointer list-none items-center gap-1.5 rounded-full px-2.5 py-1 font-mono text-[10px] leading-none ${
          known
            ? "bg-signal-soft text-signal-ink ring-1 ring-signal/30"
            : "bg-red-50 text-red-700 ring-1 ring-red-200"
        }`}
      >
        {block.type} · v{block.version}
        {block.actions.length > 0 && <span className="opacity-60">{block.actions.length} action(s)</span>}
        {!known && <span>· sem renderer</span>}
      </summary>
      <pre className="mt-2 max-h-64 overflow-auto rounded-lg bg-ink/95 p-3 font-mono text-[11px] leading-relaxed text-paper">
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
  return (
    <div className="rounded-xl outline outline-1 outline-dashed outline-signal/40 outline-offset-2">
      <InspectorTag block={block} known={Component !== undefined} />
      {Component ? (
        <Component block={block} />
      ) : (
        <p className="rounded-lg border border-dashed border-red-200 bg-red-50/50 p-4 text-sm text-red-700">
          Bloco <code>{block.type}</code> não tem componente no <code>REGISTRY</code>.
          Sem o modo de inspeção ele seria omitido silenciosamente.
        </p>
      )}
    </div>
  );
}

/** Cabecalho do modo de inspecao: a tela inteira e uma resposta do servidor. */
function ScreenMeta({ screen }: { screen: ScreenResponse }) {
  const meta = [
    ["screen_id", screen.screen_id],
    ["context", screen.context],
    ["schema_version", String(screen.schema_version)],
    ["components", String(screen.components.length)],
  ];

  return (
    <section className="rounded-xl border border-signal/30 bg-signal-soft/50 p-4">
      <p className="font-mono text-[11px] text-signal-ink">ScreenResponse</p>
      <dl className="mt-2 flex flex-wrap gap-x-6 gap-y-1 font-mono text-[11px] text-muted">
        {meta.map(([k, v]) => (
          <div key={k} className="flex gap-1.5">
            <dt>{k}:</dt>
            <dd className="text-ink">{v}</dd>
          </div>
        ))}
      </dl>
      <p className="mt-2 font-mono text-[11px] leading-relaxed text-muted">
        {screen.components.map((c) => c.type).join(" → ")}
      </p>
    </section>
  );
}

/** Agrupa `product_card` consecutivos numa grade; demais blocos ficam em fluxo. */
export function ScreenRenderer({ screen }: { screen: ScreenResponse }) {
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
    <div className="space-y-8">
      {inspecting && <ScreenMeta screen={screen} />}
      {groups.map((group, i) =>
        group[0].type === "product_card" ? (
          <div key={i} className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {group.map((block, j) => (
              <Block key={j} block={block} />
            ))}
          </div>
        ) : (
          <Block key={i} block={group[0]} />
        ),
      )}
    </div>
  );
}

/** `<dialog>` nativo: Esc, foco preso e backdrop sem codigo nosso. */
function Modal({
  open,
  onClose,
  wide = false,
  children,
}: {
  open: boolean;
  onClose: () => void;
  /** O checkout carrega o comparativo de entrega em 3 colunas; 32rem espreme. */
  wide?: boolean;
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
      className={`m-auto rounded-2xl border border-line bg-paper p-0 text-ink backdrop:bg-ink/50 ${
        wide ? "w-[min(46rem,calc(100vw-2rem))]" : "w-[min(32rem,calc(100vw-2rem))]"
      }`}
    >
      {open && <div className="p-6">{children}</div>}
    </dialog>
  );
}

/**
 * Detalhe do produto. Ate a Sprint 5 esta tela era montada aqui a partir dos
 * props do `product_card` — a unica que o cliente compunha sozinho. Agora ela
 * chega inteira de `GET /products/{id}` e o MESMO renderer desenha; o que
 * sobrou aqui e a moldura do modal.
 */
function DetailScreen() {
  const { detail, pending, error, closeDetail } = useSdui();

  return (
    <>
      <div className="flex items-start justify-between gap-4">
        <p className="text-[11px] uppercase tracking-wide text-muted">
          {detail?.screen_id ?? "carregando"}
        </p>
        <button
          type="button"
          onClick={closeDetail}
          aria-label="Fechar"
          className="text-muted transition hover:text-ink"
        >
          ✕
        </button>
      </div>

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      <div className="mt-4">
        {detail ? (
          <ScreenRenderer screen={detail} />
        ) : (
          !error && (
            <p className="py-8 text-center text-sm text-muted">
              {pending ? "Carregando detalhe…" : ""}
            </p>
          )
        )}
      </div>
    </>
  );
}

function CartScreen() {
  const {
    cart,
    checkoutAction,
    pending,
    error,
    run,
    setQuantity,
    removeFromCart,
    openCart,
  } = useSdui();
  const subtotal = cart.reduce((sum, e) => sum + e.price * e.quantity, 0);

  return (
    <>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-[11px] uppercase tracking-wide text-muted">Carrinho</p>
          <h2 className="font-display text-2xl text-ink">
            {cart.length === 0
              ? "Vazio por enquanto"
              : `${cart.length} ${cart.length === 1 ? "produto" : "produtos"}`}
          </h2>
        </div>
        <button
          type="button"
          onClick={() => openCart(false)}
          aria-label="Fechar"
          className="text-muted transition hover:text-ink"
        >
          ✕
        </button>
      </div>

      {cart.length === 0 ? (
        <p className="mt-6 text-sm text-muted">
          Escolha produtos na vitrine para simular uma compra. Itens do mesmo vendedor
          viajam numa remessa só.
        </p>
      ) : (
        <>
          <ul className="mt-6 space-y-3">
            {cart.map((entry) => (
              <li
                key={entry.productId}
                className="flex flex-wrap items-center gap-3 rounded-lg border border-line p-3"
              >
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-ink">
                    {entry.title ?? entry.productId}
                  </p>
                  <p className="mt-0.5 text-xs tabular-nums text-muted">
                    {brl(entry.price)} cada
                  </p>
                </div>
                <input
                  type="number"
                  min={1}
                  value={entry.quantity}
                  aria-label={`Quantidade de ${entry.title ?? entry.productId}`}
                  onChange={(e) =>
                    setQuantity(entry.productId, Number(e.target.value) || 1)
                  }
                  className="w-16 rounded-lg border border-line bg-surface px-2 py-1 text-sm text-ink"
                />
                <span className="w-24 text-right text-sm tabular-nums text-ink">
                  {brl(entry.price * entry.quantity)}
                </span>
                <button
                  type="button"
                  onClick={() => removeFromCart(entry.productId)}
                  aria-label={`Remover ${entry.title ?? entry.productId}`}
                  className="text-muted transition hover:text-ink"
                >
                  ✕
                </button>
              </li>
            ))}
          </ul>

          <div className="mt-5 flex justify-between border-t border-line pt-4 text-sm">
            <span className="text-muted">Subtotal (sem frete)</span>
            <span className="font-display text-xl tabular-nums text-ink">
              {brl(subtotal)}
            </span>
          </div>

          {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

          <button
            type="button"
            disabled={!checkoutAction || pending}
            onClick={() => checkoutAction && run(checkoutAction)}
            className="mt-5 w-full rounded-full bg-signal px-5 py-3 text-sm font-medium text-white transition hover:opacity-90 disabled:opacity-50"
          >
            {pending ? "Simulando…" : "Simular compra"}
          </button>
          <p className="mt-3 text-center text-[11px] text-muted">
            Simulação acadêmica — nenhum pagamento é processado.
          </p>
        </>
      )}
    </>
  );
}

function CheckoutScreen() {
  const { checkout, closeCheckout } = useSdui();
  if (!checkout) return null;

  return (
    <>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-[11px] uppercase tracking-wide text-muted">
            {checkout.screen_id}
          </p>
          <h2 className="font-display text-2xl text-ink">Compra simulada</h2>
        </div>
        <button
          type="button"
          onClick={closeCheckout}
          aria-label="Fechar"
          className="text-muted transition hover:text-ink"
        >
          ✕
        </button>
      </div>

      {/* Mesma ScreenRenderer da Home: a tela de checkout tambem vem do servidor. */}
      <div className="mt-6">
        <ScreenRenderer screen={checkout} />
      </div>
    </>
  );
}

export function Host({ children }: { children: React.ReactNode }) {
  const { detailOpen, checkout, cartOpen, closeDetail, openCart, closeCheckout } =
    useSdui();
  return (
    <>
      {children}
      <Modal open={detailOpen && checkout === null} onClose={closeDetail} wide>
        <DetailScreen />
      </Modal>
      <Modal
        open={cartOpen && checkout === null}
        onClose={() => openCart(false)}
        wide
      >
        <CartScreen />
      </Modal>
      <Modal open={checkout !== null} onClose={closeCheckout} wide>
        <CheckoutScreen />
      </Modal>
    </>
  );
}

/**
 * Ponto de entrada da tela. O `SduiProvider` fica um nivel acima, em
 * `app/page.tsx`, porque o header tambem precisa dele: o botao do carrinho
 * mostra a contagem e abre o modal.
 */
export function SduiRoot({ screen }: { screen: ScreenResponse }) {
  return (
    <Host>
      <ScreenRenderer screen={screen} />
    </Host>
  );
}
