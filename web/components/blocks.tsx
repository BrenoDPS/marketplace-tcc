"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { brl, co2Label, decimal } from "@/lib/sdui";
import type {
  Alternative,
  CategoryGridBlock,
  CheckoutSummaryBlock,
  ContentSectionBlock,
  DeliveryOptionsBlock,
  HeroBannerBlock,
  Co2Explanation,
  ImpactBannerBlock,
  OfferComparisonBlock,
  OriginMapBlock,
  ProductCardBlock,
  ProductDetailBlock,
  ShipmentBreakdownBlock,
  SustainabilityProps,
} from "@/lib/sdui";
import { useSdui } from "./sdui-context";

/**
 * "De onde vem esse numero?" (V2): a conta do selo, passo a passo, com as
 * fontes. `<details>` nativo: teclado, leitor de tela e Esc sem codigo nosso.
 * Os numeros vem do servidor; aqui so formatacao.
 */
function Co2Explainer({ e }: { e: Co2Explanation }) {
  // O CEP da sessao vai junto so para o "Voltar a vitrine" da metodologia.
  const { customerZipPrefix } = useSdui();
  const cubado = e.chargeable_weight_g > e.weight_g;
  const passos: [string, string][] = [
    ["Linha reta entre os CEPs", `${decimal(e.straight_km, 1)} km`],
    [`Estrada estimada (× ${decimal(e.circuity, 3)})`, `${decimal(e.road_km, 1)} km`],
    [
      "Trechos",
      e.line_haul_km > 0
        ? `${decimal(e.line_haul_km, 1)} km de caminhão + ${decimal(e.last_mile_km, 1)} km de van`
        : `${decimal(e.last_mile_km, 1)} km de van (só última milha)`,
    ],
    [
      cubado ? "Massa considerada (peso cúbico)" : "Massa considerada",
      cubado
        ? `${decimal(e.chargeable_weight_g, 0)} g (o produto pesa ${decimal(e.weight_g, 0)} g, mas ocupa mais)`
        : `${decimal(e.chargeable_weight_g, 0)} g`,
    ],
    ["Fatores (kg CO₂e por t·km)", `caminhão ${decimal(e.fe_line_haul, 3)} · van ${decimal(e.fe_last_mile, 3)}`],
    ...(e.mode_factor !== 1
      ? [["Modalidade de entrega", `× ${decimal(e.mode_factor, 2)}`] as [string, string]]
      : []),
    ["Emissão estimada", `${co2Label(e.co2_kg)} CO₂e`],
  ];
  return (
    <details className="mt-2 text-xs text-muted">
      <summary className="w-fit cursor-pointer rounded underline decoration-dotted underline-offset-2 hover:text-ink">
        Como calculamos?
      </summary>
      <div className="mt-2 rounded-lg border border-line bg-paper p-3">
        <dl className="space-y-1.5">
          {passos.map(([k, v]) => (
            <div key={k} className="flex flex-wrap justify-between gap-x-4">
              <dt>{k}</dt>
              <dd className="tabular-nums text-ink">{v}</dd>
            </div>
          ))}
        </dl>
        <p className="mt-3 font-medium text-ink">Fontes</p>
        <ul className="mt-1 list-disc space-y-0.5 pl-4">
          {e.sources.map((s) => (
            <li key={s}>{s}</li>
          ))}
        </ul>
        <p className="mt-2">Estimativa comparativa: serve para comparar origens, não para inventário de emissões.</p>
        {e.methodology_path && (
          <Link
            href={`${e.methodology_path}?${new URLSearchParams({ customer_zip_prefix: customerZipPrefix })}`}
            className="mt-2 inline-block font-medium text-signal-ink underline underline-offset-2"
          >
            Ver metodologia completa
          </Link>
        )}
      </div>
    </details>
  );
}

/** Unico elemento saturado da interface — ver comentario da paleta em globals.css. */
export function Badge({ badge, explain = false }: { badge: SustainabilityProps | null; explain?: boolean }) {
  if (!badge) return null;
  // Dentro do card da vitrine o selo esta num <button>: nada interativo ali.
  if (explain && badge.explanation) {
    return (
      <div>
        <Badge badge={badge} />
        <Co2Explainer e={badge.explanation} />
      </div>
    );
  }
  return (
    <span className="inline-flex w-fit items-center gap-1.5 rounded-2xl bg-signal-soft px-2.5 py-1 text-xs font-medium leading-tight text-signal-ink ring-1 ring-signal/20">
      {badge.icon === "leaf" && (
        <svg viewBox="0 0 16 16" aria-hidden className="size-3 shrink-0 fill-current">
          <path d="M13.5 2.5c0 6-3.6 9-7.2 9a4 4 0 0 1-2.6-.9c1.4-3.4 4-5.3 6.8-6.3-2.9.6-5.5 2.3-7.2 5.4a5.2 5.2 0 0 1-.8-2.8c0-3 2.6-4.6 5.4-4.8 1.9-.1 3.6-.4 5.6.4Z" />
        </svg>
      )}
      {badge.label}
    </span>
  );
}

export function CategoryGrid({ block }: { block: CategoryGridBlock }) {
  const { title, categories, sort_options = [] } = block.props;
  const { run } = useSdui();
  const scroller = useRef<HTMLDivElement>(null);
  // Bordas com conteudo escondido: so elas ganham fade e seta (D9 — os chips
  // eram cortados na borda sem nada dizer que havia mais).
  const [edges, setEdges] = useState({ start: false, end: false });
  const measure = () => {
    const el = scroller.current;
    if (!el) return;
    setEdges({
      start: el.scrollLeft > 4,
      end: el.scrollLeft + el.clientWidth < el.scrollWidth - 4,
    });
  };
  useEffect(() => {
    measure();
    window.addEventListener("resize", measure);
    return () => window.removeEventListener("resize", measure);
  }, [categories.length]);
  const page = (dir: 1 | -1) =>
    scroller.current?.scrollBy({ left: dir * scroller.current.clientWidth * 0.8, behavior: "smooth" });
  if (categories.length === 0) return null;

  const mask = `linear-gradient(to right, ${edges.start ? "transparent, black 3rem" : "black"}, ${
    edges.end ? "black calc(100% - 3rem), transparent" : "black"
  })`;
  const arrow =
    "absolute top-1/2 hidden size-8 -translate-y-1/2 items-center justify-center rounded-full border border-line bg-surface text-muted shadow-sm transition hover:text-ink sm:flex";

  return (
    <section>
      <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-2">
        {title && (
          <h2 className="text-xs uppercase tracking-[0.2em] text-muted">{title}</h2>
        )}
        {/* Ordenar (V4): opcoes, rotulos e caminhos vem do servidor. */}
        {sort_options.length > 0 && (
          <nav aria-label="Ordenar a vitrine" className="flex items-center gap-1 text-xs sm:text-sm">
            <span aria-hidden className="mr-1 text-xs text-muted">Ordenar</span>
            {sort_options.map((opt) => (
              <button
                key={opt.value}
                type="button"
                aria-current={opt.selected || undefined}
                disabled={opt.actions.length === 0}
                onClick={() => opt.actions[0] && run(opt.actions[0])}
                className={`whitespace-nowrap rounded-full px-2.5 py-1 transition sm:px-3 ${
                  opt.selected ? "bg-ink text-paper" : "text-muted hover:bg-line/60 hover:text-ink"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </nav>
        )}
      </div>
      {/* Rolagem horizontal: 12 chips nao cabem em 375px sem virar quatro
          linhas de altura. No desktop, setas; no toque, o fade basta. */}
      <div className="relative mt-3">
      <div
        ref={scroller}
        onScroll={measure}
        className="overflow-x-auto"
        style={{ maskImage: mask, WebkitMaskImage: mask }}
      >
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
                <span className="text-xs tabular-nums opacity-60">
                  {item.product_count}
                </span>
              </button>
            </li>
          ))}
        </ul>
      </div>
      {edges.start && (
        <button type="button" onClick={() => page(-1)} aria-label="Categorias anteriores" className={`${arrow} -left-3`}>
          ‹
        </button>
      )}
      {edges.end && (
        <button type="button" onClick={() => page(1)} aria-label="Mais categorias" className={`${arrow} -right-3`}>
          ›
        </button>
      )}
      </div>
    </section>
  );
}

export function HeroBanner({ block }: { block: HeroBannerBlock }) {
  const { title, subtitle, cta_label, secondary_cta_label } = block.props;
  const { run } = useSdui();
  const [action, secondary] = block.actions;

  /*
   * Compacto (D8): ate a Sprint 13 eram ~400 px de veu sobre um placeholder
   * cinza antes do primeiro produto. A `image_url` da amostra e so placeholder,
   * entao o hero fica tipografico e o espaco vai para a vitrine.
   */
  return (
    <section className="flex flex-col gap-4 rounded-2xl border border-line bg-surface px-5 py-5 sm:flex-row sm:items-end sm:justify-between sm:px-8 sm:py-7">
      <div className="max-w-2xl">
        <h1 className="font-display text-2xl leading-tight tracking-tight text-ink sm:text-4xl">
          {title}
        </h1>
        {subtitle && <p className="mt-2 text-sm text-muted sm:text-base">{subtitle}</p>}
      </div>
      {(action || secondary) && (
        <div className="flex shrink-0 flex-wrap gap-2">
          {action && (
            <button
              type="button"
              onClick={() => run(action)}
              className="rounded-full bg-ink px-4 py-2 text-sm font-medium text-paper transition hover:opacity-90 sm:px-5 sm:py-2.5"
            >
              {cta_label ?? "Explorar"}
            </button>
          )}
          {secondary && (
            <button
              type="button"
              onClick={() => run(secondary)}
              className="rounded-full border border-line px-4 py-2 text-sm text-ink transition hover:border-ink/30 sm:px-5 sm:py-2.5"
            >
              {secondary_cta_label ?? "Ver mais"}
            </button>
          )}
        </div>
      )}
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

/** "Esporte e lazer" -> "EL": sem foto no Olist, a capa leva a categoria. */
function monogram(title: string) {
  return title
    .split(/\s+/)
    .filter((w) => w.length > 2 || /^[A-Z]/.test(w))
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();
}

/**
 * Capa baixa + titulo + ORIGEM + impacto. Ate a Sprint 12 a capa ocupava ~65%
 * do card e so o selo dizia de onde o produto vinha — e so para quem estava
 * perto. Agora todo card diz cidade/UF; distancia e CO2 aparecem no selo
 * (perto) ou numa linha neutra (longe), nunca nos dois.
 */
export function ProductCard({ block }: { block: ProductCardBlock }) {
  const { product_id, price, title, image_url, badge, seller_city, seller_state, distance_km, co2_kg } =
    block.props;
  const { run } = useSdui();
  const origin = [seller_city, seller_state].filter(Boolean).join(" · ");
  // O card carrega duas `api_call`: o GET abre o detalhe, o POST e o checkout.
  // Distinguir pelo metodo evita depender da ordem em que vieram.
  const detail = block.actions.find(
    (a) => a.type === "api_call" && a.payload.method === "GET",
  );

  return (
    <button
      type="button"
      disabled={!detail}
      onClick={() => detail && run(detail)}
      className="group flex flex-col overflow-hidden rounded-xl border border-line bg-surface text-left transition hover:-translate-y-0.5 hover:shadow-lg hover:shadow-ink/5 disabled:cursor-default"
    >
      <div
        className="flex h-14 w-full items-end px-3 pb-1.5 sm:h-20 sm:px-4"
        style={
          image_url
            ? { backgroundImage: `url(${image_url})`, backgroundSize: "cover" }
            : coverStyle(product_id)
        }
      >
        {!image_url && (
          <span aria-hidden className="font-display text-2xl leading-none text-black/30 sm:text-3xl">
            {monogram(title ?? product_id)}
          </span>
        )}
      </div>
      <div className="flex flex-1 flex-col gap-1.5 p-3 sm:gap-2 sm:p-4">
        <h3 className="text-sm font-medium leading-snug text-ink">{title ?? product_id}</h3>
        {origin && <p className="truncate text-xs text-muted">Sai de {origin}</p>}
        {badge ? (
          <Badge badge={badge} />
        ) : (
          distance_km != null && (
            <p className="text-xs tabular-nums text-muted">
              {decimal(distance_km, 0)} km
              {co2_kg != null && ` · ${co2Label(co2_kg)} CO₂`}
            </p>
          )
        )}
        <p className="mt-auto pt-1 font-display text-lg text-ink sm:text-xl">{brl(price)}</p>
      </div>
    </button>
  );
}

/**
 * Detalhe do produto — agora um bloco vindo do servidor.
 *
 * Sem descricao e sem tags de sustentabilidade: o Olist nao tem esses campos
 * (so o COMPRIMENTO da descricao), e inventa-los numa tela cujo assunto e
 * credibilidade ambiental seria o pior lugar possivel para dado fabricado.
 */
export function ProductDetail({ block }: { block: ProductDetailBlock }) {
  const {
    product_id,
    title,
    price,
    weight_g,
    seller_city,
    seller_state,
    rating,
    review_count,
    badge,
  } = block.props;
  const { addToCart, openCart, closeDetail, inspecting } = useSdui();
  const [quantity, setQuantity] = useState(1);
  const checkout = block.actions.find((a) => a.type === "api_call") ?? null;

  const local = [seller_city, seller_state].filter(Boolean).join(" · ");
  const facts = [
    rating !== null
      ? [
          "Avaliação",
          `${decimal(rating, 1)} / 5`,
          `${review_count} ${review_count === 1 ? "pedido" : "pedidos"}`,
        ]
      : null,
    local ? ["Vendedor", local, ""] : null,
    weight_g ? ["Peso", `${decimal(weight_g, 0)} g`, ""] : null,
  ].filter((f): f is string[] => f !== null);

  const add = (thenOpenCart: boolean) => {
    addToCart({ productId: product_id, title, price }, quantity, checkout);
    closeDetail();
    if (thenOpenCart) openCart(true);
  };

  return (
    <section className="rounded-xl border border-line bg-surface p-6">
      <h2 className="font-display text-2xl text-ink">{title ?? product_id}</h2>
      {/* O id e um hash de 32 caracteres: so interessa a quem inspeciona o JSON. */}
      {inspecting && <p className="mt-1 font-mono text-xs text-muted">{product_id}</p>}

      <div className="mt-4">{badge ? <Badge badge={badge} explain /> : null}</div>
      <p className="mt-4 font-display text-3xl text-ink">{brl(price)}</p>

      {facts.length > 0 && (
        <dl className="mt-6 grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
          {facts.map(([label, value, hint]) => (
            <div key={label}>
              <dt className="text-xs uppercase tracking-wide text-muted">{label}</dt>
              <dd className="mt-0.5 text-ink">
                {value}
                {hint && <span className="ml-1.5 text-xs text-muted">({hint})</span>}
              </dd>
            </div>
          ))}
        </dl>
      )}

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

      <div className="mt-6 flex flex-col gap-2 sm:flex-row">
        <button
          type="button"
          onClick={() => add(false)}
          className="flex-1 rounded-full border border-line px-5 py-3 text-sm font-medium text-ink transition hover:border-ink/30"
        >
          Adicionar ao carrinho
        </button>
        <button
          type="button"
          onClick={() => add(true)}
          className="flex-1 rounded-full bg-signal px-5 py-3 text-sm font-medium text-on-signal transition hover:opacity-90"
        >
          Ir para o carrinho
        </button>
      </div>
      <p className="mt-3 text-center text-xs text-muted">
        Simulação acadêmica — nenhum pagamento é processado.
      </p>
    </section>
  );
}

export function CheckoutSummary({ block }: { block: CheckoutSummaryBlock }) {
  const { items, subtotal, freight, total } = block.props;

  return (
    <section className="rounded-xl border border-line bg-surface p-6">
      <h2 className="font-display text-2xl text-ink">
        {items.length === 1 ? (items[0].title ?? items[0].product_id) : "Seu pedido"}
      </h2>
      <dl className="mt-6 space-y-3 text-sm">
        {items.map((item) => (
          <div key={item.product_id} className="flex justify-between gap-4">
            <dt className="text-muted">
              {item.quantity}× {item.title ?? item.product_id}
              <span className="ml-1.5 text-muted/70">{brl(item.unit_price)}</span>
            </dt>
            <dd className="tabular-nums text-ink">{brl(item.line_total)}</dd>
          </div>
        ))}
        <div className="flex justify-between gap-4 border-t border-line pt-3">
          <dt className="text-muted">Subtotal</dt>
          <dd className="tabular-nums text-ink">{brl(subtotal)}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-muted">Frete</dt>
          <dd className="tabular-nums text-ink">{brl(freight)}</dd>
        </div>
        <div className="flex justify-between gap-4 border-t border-line pt-3">
          <dt className="font-medium text-ink">Total</dt>
          <dd className="font-display text-xl tabular-nums text-ink">{brl(total)}</dd>
        </div>
      </dl>
    </section>
  );
}

/** Sugestao de troca: outro produto da mesma categoria, vendedor mais perto. */
function Alternatives({ items }: { items: Alternative[] }) {
  const { run, pending, swapInCart } = useSdui();
  if (items.length === 0) return null;

  return (
    <div className="mt-4 border-t border-line pt-4">
      <p className="text-xs uppercase tracking-wide text-muted">
        Mais perto de você
      </p>
      <ul className="mt-2 space-y-2">
        {items.map((alt) => {
          const action = alt.actions[0];
          return (
            <li
              key={alt.product_id}
              className="flex flex-wrap items-center justify-between gap-3 rounded-lg bg-signal-soft/60 px-3 py-2"
            >
              <div className="min-w-0">
                <p className="text-sm text-ink">
                  {alt.title ?? alt.product_id}
                  <span className="ml-2 tabular-nums text-muted">
                    {brl(alt.price)}
                  </span>
                </p>
                <p className="mt-0.5 text-xs tabular-nums text-signal-ink">
                  {decimal(alt.distance_km, 0)} km ·{" "}
                  {/* Arredonda para BAIXO: 99,8% virava "−100%", que se le como
                      emissao zero. A alternativa ainda emite. */}
                  −{Math.floor(alt.saved_share * 100)}% CO₂
                  <span className="text-muted"> ({co2Label(alt.co2_saved_kg)} a menos)</span>
                </p>
              </div>
              <button
                type="button"
                disabled={!action || pending}
                onClick={() => {
                  if (!action) return;
                  // O carrinho novo vai explicito: `setCart` nao atualiza o
                  // valor que `run` capturou no closure.
                  const updated = swapInCart(alt.replaces_product_id, {
                    productId: alt.product_id,
                    title: alt.title,
                    price: alt.price,
                  });
                  run(action, { cart: updated });
                }}
                className="shrink-0 rounded-full border border-signal/40 px-3 py-1 text-xs font-medium text-signal-ink transition hover:bg-signal-soft disabled:opacity-50"
              >
                Trocar
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export function ShipmentBreakdown({ block }: { block: ShipmentBreakdownBlock }) {
  const { title, shipments, note } = block.props;
  if (shipments.length === 0) return null;

  return (
    <section className="rounded-xl border border-line bg-surface p-6">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-display text-2xl text-ink">{title ?? "Remessas"}</h2>
        <p className="text-sm text-muted">
          {shipments.length === 1
            ? "1 remessa"
            : `${shipments.length} remessas — da maior pegada para a menor`}
        </p>
      </div>

      <ul className="mt-5 space-y-3">
        {shipments.map((shipment, i) => (
          <li
            key={shipment.seller_id}
            // O servidor manda ordenado por emissao: a primeira e a que pesa.
            className={`rounded-lg border p-4 ${
              i === 0 && shipments.length > 1
                ? "border-ink/25 bg-paper"
                : "border-line"
            }`}
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-sm font-medium text-ink">
                  {shipment.total_quantity}{" "}
                  {shipment.total_quantity === 1 ? "item" : "itens"} ·{" "}
                  {shipment.distance_km !== null
                    ? `${decimal(shipment.distance_km, 0)} km`
                    : "distância indisponível"}
                </p>
                <p className="mt-0.5 font-mono text-xs text-muted">
                  {shipment.seller_id.slice(0, 12)}…
                </p>
              </div>
              <Badge badge={shipment.badge} explain />
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-1 text-sm">
              <span className="tabular-nums text-ink">{brl(shipment.freight)}</span>
              {shipment.co2_kg !== null && (
                <span className="tabular-nums text-muted">
                  {co2Label(shipment.co2_kg)} CO₂
                </span>
              )}
              {shipment.co2_share !== null && (
                <span className="tabular-nums text-muted">
                  {decimal(shipment.co2_share * 100, 0)}% da pegada
                </span>
              )}
            </div>

            {/* A barra e o que faz a remessa dominante saltar aos olhos. Neutra:
                o verde e sinal de "bom" e aqui mede o quanto a remessa emite. */}
            {shipment.co2_share !== null && (
              <div className="mt-2 h-1 w-full overflow-hidden rounded-full bg-line">
                <div
                  className="h-full rounded-full bg-muted"
                  style={{ width: `${shipment.co2_share * 100}%` }}
                />
              </div>
            )}

            <Alternatives items={shipment.alternatives} />
          </li>
        ))}
      </ul>

      {note && <p className="mt-5 text-xs leading-relaxed text-muted">{note}</p>}
    </section>
  );
}

export function DeliveryOptions({ block }: { block: DeliveryOptionsBlock }) {
  const { options, note } = block.props;
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
            onClick={() => action && run(action, { deliveryOption: option.id })}
            className={`flex flex-col gap-3 rounded-lg border p-4 text-left transition disabled:cursor-default ${
              option.selected
                ? "border-signal bg-signal-soft ring-1 ring-signal/30"
                : "border-line hover:border-ink/25 disabled:hover:border-line"
            } ${pending ? "opacity-60" : ""}`}
          >
            <div className="flex items-start justify-between gap-2">
              <span className="text-sm font-medium text-ink">{option.label}</span>
              {option.recommended && (
                <span className="shrink-0 rounded-full bg-signal-soft px-2 py-0.5 text-xs font-medium uppercase tracking-wide text-signal-ink ring-1 ring-signal/20">
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
                  {/* Verde so na opcao de menor emissao: barra verde mais longa
                      na Expressa premiava a que mais emite. */}
                  <div
                    className={`h-full rounded-full ${option.recommended ? "bg-signal" : "bg-muted"}`}
                    style={{ width: `${maxCo2 > 0 ? (option.co2_kg / maxCo2) * 100 : 0}%` }}
                  />
                </div>
                <p className="mt-1.5 text-xs tabular-nums text-muted">
                  {co2Label(option.co2_kg)} CO₂
                </p>
              </div>
            )}

            {option.description && (
              <p className="text-xs leading-relaxed text-muted">{option.description}</p>
            )}
          </button>
        ))}
      </div>

      {/* Sem esta nota os fatores viram "dado do Olist" na leitura de quem ve. */}
      {note && <p className="mt-5 text-xs leading-relaxed text-muted">{note}</p>}
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
              <dt className="text-xs uppercase tracking-wide text-muted">{label}</dt>
              <dd className="mt-1 font-display text-2xl tabular-nums text-ink">{value}</dd>
            </div>
          ))}
        </dl>
      )}
    </section>
  );
}

/**
 * Todas as origens do mesmo produto (V1): o argumento da tese em tela — mesmo
 * produto, origem mais perto, emite menos. A escolhida vem marcada pelo
 * servidor, com o motivo; o cliente so desenha. Barras neutras e verde so na
 * de menor emissao (a regra do D4).
 */
export function OfferComparison({ block }: { block: OfferComparisonBlock }) {
  const { title, offers, note } = block.props;
  const co2s = offers.map((o) => o.co2_kg).filter((c): c is number => c !== null);
  const maxCo2 = Math.max(0, ...co2s);
  const minCo2 = co2s.length ? Math.min(...co2s) : null;
  const chosenCo2 = offers.find((o) => o.chosen)?.co2_kg ?? null;
  // Ate 8 origens num produto da amostra: as 4 mais proximas (e a escolhida,
  // sempre) ficam a vista; o resto recolhe — no celular eram 2 telas de lista.
  const VISIVEIS = 4;
  const vista = offers.filter((o, i) => i < VISIVEIS || o.chosen);
  const resto = offers.filter((o) => !vista.includes(o));

  const row = (o: (typeof offers)[number]) => {
    const origem = [o.seller_city, o.seller_state].filter(Boolean).join(" · ") || "Origem não informada";
    const distancia = o.same_region
      ? "na sua região"
      : o.distance_km !== null
        ? `${decimal(o.distance_km, 0)} km`
        : "distância desconhecida";
    const vezes =
      !o.chosen && o.co2_kg !== null && chosenCo2
        ? o.co2_kg / chosenCo2
        : null;
    return (
      <li
        key={o.seller_id}
        aria-current={o.chosen || undefined}
        className={`rounded-lg border p-3 ${o.chosen ? "border-signal bg-signal-soft/60" : "border-line"}`}
      >
        <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
          <p className="text-sm font-medium text-ink">
            {origem}
            {o.local && <span className="ml-2 text-xs font-normal text-signal-ink">entrega local</span>}
          </p>
          <p className="text-sm tabular-nums text-ink">{brl(o.price)}</p>
        </div>
        <p className="mt-1 text-xs tabular-nums text-muted">
          {distancia}
          {o.co2_kg !== null && ` · ${co2Label(o.co2_kg)} CO₂`}
          {vezes !== null && vezes >= 1.05 && ` · ${decimal(vezes, 1)}× a emissão da escolhida`}
        </p>
        {o.co2_kg !== null && maxCo2 > 0 && (
          <div className="mt-2 h-1 w-full overflow-hidden rounded-full bg-line">
            <div
              className={`h-full rounded-full ${o.co2_kg === minCo2 ? "bg-signal" : "bg-muted"}`}
              style={{ width: `${(o.co2_kg / maxCo2) * 100}%` }}
            />
          </div>
        )}
        {o.chosen && o.reason && (
          <p className="mt-2 text-xs font-medium text-signal-ink">Escolhida: {o.reason}</p>
        )}
      </li>
    );
  };

  return (
    <section className="rounded-xl border border-line bg-surface p-6">
      <h2 className="font-display text-xl text-ink">{title}</h2>
      <ol className="mt-4 space-y-2">{vista.map(row)}</ol>
      {resto.length > 0 && (
        <details className="mt-2">
          <summary className="cursor-pointer rounded-lg px-1 py-1.5 text-sm text-muted transition hover:text-ink">
            Ver as outras {resto.length} {resto.length === 1 ? "origem" : "origens"}
          </summary>
          <ol className="mt-2 space-y-2">{resto.map(row)}</ol>
        </details>
      )}
      {note && <p className="mt-4 text-xs leading-relaxed text-muted">{note}</p>}
    </section>
  );
}

/**
 * Mapa de origem (V3): o "perto" vira imagem. Pontos e recorte chegam
 * projetados do servidor (`green_logistics/mapa.py`); aqui so SVG. O fundo e o
 * Brasil desenhado pelos CEPs do dataset (`scripts/mapa_base.py`), sem
 * biblioteca de mapas. Tracos e raios escalam com o recorte, para o desenho ter
 * o mesmo peso numa entrega de 4 km e numa de 2.000.
 */
export function OriginMap({ block }: { block: OriginMapBlock }) {
  const { title, viewbox, width, height, background_url, buyer, origins, radius_100km, caption } =
    block.props;
  const u = Number(viewbox.split(" ")[2]) / 400;
  const escolhida = origins.find((o) => o.chosen);
  const outras = origins.length - (escolhida ? 1 : 0);
  const resumo = [
    `Você e ${origins.length} ${origins.length === 1 ? "origem" : "origens"} no mapa`,
    escolhida && `escolhida: ${escolhida.label}`,
  ]
    .filter(Boolean)
    .join("; ");

  return (
    <section className="rounded-xl border border-line bg-surface p-4 sm:p-6">
      <h2 className="font-display text-xl text-ink">{title}</h2>
      <svg
        viewBox={viewbox}
        role="img"
        aria-label={resumo}
        className="mt-4 aspect-16/10 w-full rounded-lg border border-line bg-paper"
      >
        {/* O fundo tem pontos de tamanho fixo: no recorte de perto eles crescem
            e pesariam mais que a rota. Esmaecer com o zoom mantem a hierarquia. */}
        {background_url && (
          <image
            href={background_url}
            x={0}
            y={0}
            width={width}
            height={height}
            opacity={Math.min(1, Math.max(0.3, (u * 400) / width))}
          />
        )}
        <circle
          cx={buyer.x}
          cy={buyer.y}
          r={radius_100km}
          className="fill-signal/10 stroke-signal"
          strokeWidth={u}
          strokeDasharray={`${4 * u} ${3 * u}`}
        />
        {origins.map((o, i) => (
          <line
            key={`l${i}`}
            x1={o.x}
            y1={o.y}
            x2={buyer.x}
            y2={buyer.y}
            className={o.chosen ? "stroke-signal" : "stroke-muted"}
            strokeWidth={u * (o.chosen ? 2 : 0.8)}
            strokeOpacity={o.chosen ? 1 : 0.5}
          />
        ))}
        {origins.map((o, i) => (
          <circle
            key={`p${i}`}
            cx={o.x}
            cy={o.y}
            r={u * (o.chosen ? 5 : 3.5)}
            className={o.chosen ? "fill-signal stroke-paper" : "fill-muted stroke-paper"}
            strokeWidth={u}
          >
            <title>{o.label}</title>
          </circle>
        ))}
        <circle cx={buyer.x} cy={buyer.y} r={u * 5} className="fill-ink stroke-paper" strokeWidth={u * 1.5}>
          <title>{buyer.label}</title>
        </circle>
        <text x={buyer.x + u * 8} y={buyer.y - u * 8} fontSize={u * 13} className="fill-ink font-medium">
          {buyer.label}
        </text>
      </svg>
      <ul className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted">
        <li className="flex items-center gap-1.5">
          <span aria-hidden className="size-2.5 rounded-full bg-ink" /> Você
        </li>
        {escolhida && (
          <li className="flex items-center gap-1.5">
            <span aria-hidden className="size-2.5 rounded-full bg-signal" /> Escolhida: {escolhida.label}
          </li>
        )}
        {outras > 0 && (
          <li className="flex items-center gap-1.5">
            <span aria-hidden className="size-2.5 rounded-full bg-muted" /> {outras}{" "}
            {outras === 1 ? "outra origem" : "outras origens"}
          </li>
        )}
      </ul>
      {caption && <p className="mt-2 text-xs leading-relaxed text-muted">{caption}</p>}
    </section>
  );
}

/** Secao de texto vinda do servidor (V7). Sem markdown nem HTML: so texto. */
export function ContentSection({ block }: { block: ContentSectionBlock }) {
  const { title, paragraphs, items, note } = block.props;
  return (
    <section className="rounded-xl border border-line bg-surface p-6">
      <h2 className="font-display text-xl text-ink">{title}</h2>
      {paragraphs.map((texto) => (
        <p key={texto} className="mt-3 max-w-prose text-sm leading-relaxed text-ink/85">
          {texto}
        </p>
      ))}
      {items.length > 0 && (
        <ul className="mt-3 max-w-prose list-disc space-y-1.5 pl-5 text-sm leading-relaxed text-ink/85">
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}
      {note && <p className="mt-4 text-xs leading-relaxed text-muted">{note}</p>}
    </section>
  );
}
