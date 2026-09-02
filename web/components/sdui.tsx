"use client";

import { useEffect, useRef, useState } from "react";
import { brl } from "@/lib/sdui";
import type { ScreenResponse, UIComponent } from "@/lib/sdui";
import { Badge, CheckoutSummary, HeroBanner, ImpactBanner, ProductCard } from "./blocks";
import { SduiProvider, useSdui } from "./sdui-context";

/**
 * Mapa `component.type` -> componente React. Um bloco que o servidor mande e
 * este cliente ainda nao conheca renderiza `null`: a tela degrada, nao quebra.
 * Bloco novo no backend = uma linha aqui.
 */
const REGISTRY = {
  hero_banner: HeroBanner,
  product_card: ProductCard,
  checkout_summary: CheckoutSummary,
  impact_banner: ImpactBanner,
} as const;

function Block({ block }: { block: UIComponent }) {
  const Component = REGISTRY[block.type as keyof typeof REGISTRY] as
    | ((props: { block: UIComponent }) => React.ReactNode)
    | undefined;
  if (!Component) return null;
  return <Component block={block} />;
}

/** Agrupa `product_card` consecutivos numa grade; demais blocos ficam em fluxo. */
export function ScreenRenderer({ screen }: { screen: ScreenResponse }) {
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
  children,
}: {
  open: boolean;
  onClose: () => void;
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
      className="m-auto w-[min(32rem,calc(100vw-2rem))] rounded-2xl border border-line bg-paper p-0 text-ink backdrop:bg-ink/50"
    >
      {open && <div className="p-6">{children}</div>}
    </dialog>
  );
}

function ProductDetail() {
  const { selected, pending, error, run, select } = useSdui();
  const [quantity, setQuantity] = useState(1);

  useEffect(() => setQuantity(1), [selected?.props.product_id]);

  if (!selected) return null;
  const { title, product_id, price, badge } = selected.props;
  const buy = selected.actions.find((a) => a.type === "api_call");

  return (
    <>
      <div className="flex items-start justify-between gap-4">
        <h2 className="font-display text-2xl text-ink">{title ?? product_id}</h2>
        <button
          type="button"
          onClick={() => select(null)}
          aria-label="Fechar"
          className="text-muted transition hover:text-ink"
        >
          ✕
        </button>
      </div>

      <p className="mt-1 font-mono text-[11px] text-muted">{product_id}</p>
      <div className="mt-4">{badge ? <Badge badge={badge} /> : null}</div>
      <p className="mt-4 font-display text-3xl text-ink">{brl(price)}</p>

      <div className="mt-6 flex items-center gap-3">
        <label htmlFor="qty" className="text-sm text-muted">
          Quantidade
        </label>
        <input
          id="qty"
          type="number"
          min={1}
          value={quantity}
          onChange={(e) => setQuantity(Math.max(1, Number(e.target.value) || 1))}
          className="w-20 rounded-lg border border-line bg-surface px-3 py-1.5 text-sm text-ink"
        />
      </div>

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      <button
        type="button"
        disabled={!buy || pending}
        onClick={() => buy && run(buy, { product: selected, quantity })}
        className="mt-6 w-full rounded-full bg-signal px-5 py-3 text-sm font-medium text-white transition hover:opacity-90 disabled:opacity-50"
      >
        {pending ? "Simulando…" : "Simular compra"}
      </button>
      <p className="mt-3 text-center text-[11px] text-muted">
        Simulação acadêmica — nenhum pagamento é processado.
      </p>
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

function Host({ children }: { children: React.ReactNode }) {
  const { selected, checkout, select, closeCheckout } = useSdui();
  return (
    <>
      {children}
      <Modal open={selected !== null && checkout === null} onClose={() => select(null)}>
        <ProductDetail />
      </Modal>
      <Modal open={checkout !== null} onClose={closeCheckout}>
        <CheckoutScreen />
      </Modal>
    </>
  );
}

/** Ponto de entrada: envolve a tela com o executor de acoes e os modais. */
export function SduiRoot({
  customerZipPrefix,
  screen,
}: {
  customerZipPrefix: string;
  screen: ScreenResponse;
}) {
  return (
    <SduiProvider customerZipPrefix={customerZipPrefix}>
      <Host>
        <ScreenRenderer screen={screen} />
      </Host>
    </SduiProvider>
  );
}
