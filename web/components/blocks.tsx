"use client";

import { brl, co2Label, decimal } from "@/lib/sdui";
import type {
  CategoryGridBlock,
  CheckoutSummaryBlock,
  DeliveryOptionsBlock,
  HeroBannerBlock,
  ImpactBannerBlock,
  ProductCardBlock,
  SustainabilityProps,
} from "@/lib/sdui";
import { useSdui } from "./sdui-context";

/** Unico elemento saturado da interface — ver comentario da paleta em globals.css. */
export function Badge({ badge }: { badge: SustainabilityProps | null }) {
  if (!badge) return null;
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-signal-soft px-2.5 py-1 text-[11px] font-medium leading-none text-signal-ink ring-1 ring-signal/20">
      {badge.icon === "leaf" && (
        <svg viewBox="0 0 16 16" aria-hidden className="size-3 fill-current">
          <path d="M13.5 2.5c0 6-3.6 9-7.2 9a4 4 0 0 1-2.6-.9c1.4-3.4 4-5.3 6.8-6.3-2.9.6-5.5 2.3-7.2 5.4a5.2 5.2 0 0 1-.8-2.8c0-3 2.6-4.6 5.4-4.8 1.9-.1 3.6-.4 5.6.4Z" />
        </svg>
      )}
      {badge.label}
    </span>
  );
}

export function CategoryGrid({ block }: { block: CategoryGridBlock }) {
  const { title, categories } = block.props;
  const { run } = useSdui();
  if (categories.length === 0) return null;

  return (
    <section>
      {title && (
        <h2 className="text-[11px] uppercase tracking-[0.2em] text-muted">{title}</h2>
      )}
      {/* Rolagem horizontal no mobile: 12 chips nao cabem em 375px sem virar
          quatro linhas de altura. */}
      <div className="-mx-6 mt-3 overflow-x-auto px-6">
        <ul className="flex w-max gap-2 pb-1">
          {categories.map((item) => (
            <li key={item.slug}>
              <button
                type="button"
                aria-current={item.selected}
                disabled={item.actions.length === 0}
                onClick={() => item.actions[0] && run(item.actions[0])}
                className={`flex items-baseline gap-1.5 whitespace-nowrap rounded-full border px-3.5 py-1.5 text-sm transition ${
                  item.selected
                    ? "border-signal bg-signal-soft text-signal-ink"
                    : "border-line bg-surface text-muted hover:border-ink/25 hover:text-ink"
                }`}
              >
                {item.label}
                <span className="text-[11px] tabular-nums opacity-60">
                  {item.product_count}
                </span>
              </button>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

export function HeroBanner({ block }: { block: HeroBannerBlock }) {
  const { title, subtitle, image_url, cta_label } = block.props;
  const { run } = useSdui();
  const action = block.actions[0];

  return (
    <section
      className="relative overflow-hidden rounded-2xl border border-line bg-surface px-6 py-14 sm:px-12 sm:py-20"
      style={{
        backgroundImage: `url(${image_url})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
    >
      {/* A amostra so traz placeholders cinza: o veu deixa a tipografia liderar. */}
      <div className="absolute inset-0 bg-paper/92" />
      <div className="relative max-w-2xl">
        <h1 className="font-display text-4xl leading-[1.05] tracking-tight text-ink sm:text-6xl">
          {title}
        </h1>
        {subtitle && <p className="mt-4 text-base text-muted sm:text-lg">{subtitle}</p>}
        {action && (
          <button
            type="button"
            onClick={() => run(action)}
            className="mt-8 rounded-full bg-ink px-5 py-2.5 text-sm font-medium text-paper transition hover:opacity-90"
          >
            {cta_label ?? "Explorar"}
          </button>
        )}
      </div>
    </section>
  );
}

/** Olist nao traz foto na amostra: gera uma capa estavel a partir do product_id. */
function coverStyle(productId: string) {
  let hue = 0;
  for (let i = 0; i < productId.length; i++) {
    hue = (hue * 31 + productId.charCodeAt(i)) % 360;
  }
  return {
    backgroundImage: `linear-gradient(135deg, hsl(${hue} 32% 82%), hsl(${(hue + 40) % 360} 28% 68%))`,
  };
}

export function ProductCard({ block }: { block: ProductCardBlock }) {
  const { product_id, price, title, image_url, badge } = block.props;
  const { run } = useSdui();
  const detail = block.actions.find((a) => a.type === "open_modal");

  return (
    <button
      type="button"
      disabled={!detail}
      onClick={() => detail && run(detail, { product: block })}
      className="group flex flex-col overflow-hidden rounded-xl border border-line bg-surface text-left transition hover:-translate-y-0.5 hover:shadow-lg hover:shadow-ink/5 disabled:cursor-default"
    >
      <div
        className="aspect-4/3 w-full"
        style={
          image_url
            ? { backgroundImage: `url(${image_url})`, backgroundSize: "cover" }
            : coverStyle(product_id)
        }
      />
      <div className="flex flex-1 flex-col gap-3 p-4">
        <div className="min-h-9">{badge ? <Badge badge={badge} /> : null}</div>
        <h3 className="text-sm font-medium text-ink">{title ?? product_id}</h3>
        <p className="mt-auto font-display text-xl text-ink">{brl(price)}</p>
      </div>
    </button>
  );
}

export function CheckoutSummary({ block }: { block: CheckoutSummaryBlock }) {
  const { title, product_id, quantity, unit_price, subtotal, freight, total } = block.props;
  const rows = [
    [`Subtotal (${quantity}× ${brl(unit_price)})`, brl(subtotal)],
    ["Frete", brl(freight)],
  ];

  return (
    <section className="rounded-xl border border-line bg-surface p-6">
      <h2 className="font-display text-2xl text-ink">{title ?? product_id}</h2>
      <dl className="mt-6 space-y-3 text-sm">
        {rows.map(([label, value]) => (
          <div key={label} className="flex justify-between gap-4">
            <dt className="text-muted">{label}</dt>
            <dd className="tabular-nums text-ink">{value}</dd>
          </div>
        ))}
        <div className="flex justify-between gap-4 border-t border-line pt-3">
          <dt className="font-medium text-ink">Total</dt>
          <dd className="font-display text-xl tabular-nums text-ink">{brl(total)}</dd>
        </div>
      </dl>
    </section>
  );
}

export function DeliveryOptions({ block }: { block: DeliveryOptionsBlock }) {
  const { options, note, product_id, quantity } = block.props;
  const { run, pending } = useSdui();
  const action = block.actions.find((a) => a.type === "api_call");

  /**
   * A leitura util da emissao aqui e relativa: "0,42 g" nao diz nada sozinho,
   * mas meia barra ao lado da vizinha diz. Escala pela maior das opcoes.
   */
  const maxCo2 = Math.max(...options.map((o) => o.co2_kg ?? 0));

  return (
    <section className="rounded-xl border border-line bg-surface p-6">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-display text-2xl text-ink">Como entregar</h2>
        <p className="text-sm text-muted">Mais rápido custa mais e emite mais.</p>
      </div>

      <div role="radiogroup" aria-label="Modalidade de entrega" className="mt-5 grid gap-3 sm:grid-cols-3">
        {options.map((option) => (
          <button
            key={option.id}
            type="button"
            role="radio"
            aria-checked={option.selected}
            disabled={!action || pending}
            onClick={() =>
              action &&
              run(action, {
                productId: product_id,
                quantity,
                deliveryOption: option.id,
              })
            }
            className={`flex flex-col gap-3 rounded-lg border p-4 text-left transition disabled:cursor-default ${
              option.selected
                ? "border-signal bg-signal-soft ring-1 ring-signal/30"
                : "border-line hover:border-ink/25 disabled:hover:border-line"
            } ${pending ? "opacity-60" : ""}`}
          >
            <div className="flex items-start justify-between gap-2">
              <span className="text-sm font-medium text-ink">{option.label}</span>
              {option.recommended && (
                <span className="shrink-0 rounded-full bg-signal-soft px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-signal-ink ring-1 ring-signal/20">
                  Menor emissão
                </span>
              )}
            </div>

            <p className="font-display text-xl tabular-nums text-ink">{brl(option.price)}</p>

            <p className="text-xs text-muted">
              {option.eta_days} {option.eta_days === 1 ? "dia útil" : "dias úteis"}
            </p>

            {option.co2_kg !== null && (
              <div>
                <div className="h-1 w-full overflow-hidden rounded-full bg-line">
                  <div
                    className="h-full rounded-full bg-signal"
                    style={{ width: `${maxCo2 > 0 ? (option.co2_kg / maxCo2) * 100 : 0}%` }}
                  />
                </div>
                <p className="mt-1.5 text-xs tabular-nums text-muted">
                  {co2Label(option.co2_kg)} CO₂
                </p>
              </div>
            )}

            {option.description && (
              <p className="text-[11px] leading-relaxed text-muted">{option.description}</p>
            )}
          </button>
        ))}
      </div>

      {/* Sem esta nota os fatores viram "dado do Olist" na leitura de quem ve. */}
      {note && <p className="mt-5 text-[11px] leading-relaxed text-muted">{note}</p>}
    </section>
  );
}

export function ImpactBanner({ block }: { block: ImpactBannerBlock }) {
  const { distance_km, co2_kg, badge, message } = block.props;
  const stats = [
    distance_km !== null ? ["Distância", `${decimal(distance_km, 0)} km`] : null,
    co2_kg !== null ? ["CO₂ estimado", co2Label(co2_kg)] : null,
  ].filter((s): s is string[] => s !== null);

  return (
    <section className="rounded-xl border border-line bg-surface p-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <p className="text-sm text-muted">{message}</p>
        <Badge badge={badge} />
      </div>
      {stats.length > 0 && (
        <dl className="mt-6 grid grid-cols-2 gap-4">
          {stats.map(([label, value]) => (
            <div key={label} className="rounded-lg border border-line px-4 py-3">
              <dt className="text-[11px] uppercase tracking-wide text-muted">{label}</dt>
              <dd className="mt-1 font-display text-2xl tabular-nums text-ink">{value}</dd>
            </div>
          ))}
        </dl>
      )}
    </section>
  );
}
