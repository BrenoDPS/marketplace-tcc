"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { brl, co2Label, decimal } from "@/lib/sdui";
import type {
  Alternative,
  CategoryGridBlock,
  CheckoutSummaryBlock,
  ContentSectionBlock,
  DataTableBlock,
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
import { Icon, categoryIcon, coverTone, type IconName } from "./icons";
import { useSdui } from "./sdui-context";

/* Redesign (02/11): todo bloco e um cartao com o mesmo raio, borda e sombra;
   o verde continua sinal (selo, menor emissao, escolhida), nunca decoracao. */
const CARD = "rounded-2xl border border-line bg-surface shadow-soft";
const EYEBROW = "text-[11px] font-medium uppercase tracking-[0.16em] text-muted";

/** Quantidade com − / +: o campo numerico puro parecia formulario de cadastro. */
export function Stepper({ value, onChange, label }: { value: number; onChange: (n: number) => void; label: string }) {
  const btn =
    "flex size-8 items-center justify-center rounded-lg text-muted transition hover:bg-paper-2 hover:text-ink disabled:opacity-40 disabled:hover:bg-transparent";
  return (
    <div className="flex items-center rounded-xl border border-line bg-surface p-0.5">
      <button type="button" aria-label={`Diminuir quantidade de ${label}`} disabled={value <= 1} onClick={() => onChange(value - 1)} className={btn}>
        <Icon name="minus" className="size-4" />
      </button>
      <input
        type="number"
        min={1}
        value={value}
        aria-label={`Quantidade de ${label}`}
        onChange={(e) => onChange(Math.max(1, Number(e.target.value) || 1))}
        className="w-10 bg-transparent text-center text-sm tabular-nums text-ink outline-none [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none"
      />
      <button type="button" aria-label={`Aumentar quantidade de ${label}`} onClick={() => onChange(value + 1)} className={btn}>
        <Icon name="plus" className="size-4" />
      </button>
    </div>
  );
}

/** Nota real dos pedidos (nunca preenchida quando nao ha avaliacao). */
function Rating({ rating, count, className = "" }: { rating: number | null | undefined; count?: number; className?: string }) {
  if (rating == null) return null;
  return (
    <span className={`inline-flex items-center gap-1 text-xs tabular-nums text-ink-2 ${className}`}>
      <Icon name="star" className="size-3.5 fill-star text-star" strokeWidth={1.5} />
      {decimal(rating, 1)}
      {count != null && count > 0 && (
        <span className="text-muted">
          ({count} {count === 1 ? "pedido" : "pedidos"})
        </span>
      )}
    </span>
  );
}

/**
 * "De onde vem esse numero?" (V2): a conta do selo, passo a passo, com as
 * fontes. `<details>` nativo: teclado, leitor de tela e Esc sem codigo nosso.
 * Os numeros vem do servidor; aqui so formatacao.
 */
function Co2Explainer({ e }: { e: Co2Explanation }) {
  // O CEP da sessao vai junto so para o "Voltar a vitrine" da metodologia.
  const { customerZipPrefix } = useSdui();
  const cubado = e.chargeable_weight_g > e.weight_g;
  const passos: [IconName, string, string][] = [
    ["pin", "Linha reta entre os CEPs", `${decimal(e.straight_km, 1)} km`],
    ["route", `Estrada estimada (× ${decimal(e.circuity, 3)})`, `${decimal(e.road_km, 1)} km`],
    [
      "truck",
      "Trechos",
      e.line_haul_km > 0
        ? `${decimal(e.line_haul_km, 1)} km de caminhão + ${decimal(e.last_mile_km, 1)} km de van`
        : `${decimal(e.last_mile_km, 1)} km de van (só última milha)`,
    ],
    [
      "scale",
      cubado ? "Massa considerada (peso cúbico)" : "Massa considerada",
      cubado
        ? `${decimal(e.chargeable_weight_g, 0)} g (o produto pesa ${decimal(e.weight_g, 0)} g, mas ocupa mais)`
        : `${decimal(e.chargeable_weight_g, 0)} g`,
    ],
    ["layers", "Fatores (kg CO₂e por t·km)", `caminhão ${decimal(e.fe_line_haul, 3)} · van ${decimal(e.fe_last_mile, 3)}`],
    ...(e.mode_factor !== 1
      ? [["sliders", "Modalidade de entrega", `× ${decimal(e.mode_factor, 2)}`] as [IconName, string, string]]
      : []),
    ["leaf", "Emissão estimada", `${co2Label(e.co2_kg)} CO₂e`],
  ];
  return (
    <details className="group/calc mt-2 text-xs text-muted">
      <summary className="inline-flex w-fit cursor-pointer list-none items-center gap-1 rounded-md font-medium text-signal-ink underline decoration-dotted underline-offset-4 hover:text-signal">
        Como calculamos?
        <Icon name="chevronDown" className="size-3.5 transition group-open/calc:rotate-180" />
      </summary>
      <div className="mt-3 rounded-xl border border-line bg-surface-2 p-4">
        <dl className="space-y-2">
          {passos.map(([icone, k, v]) => (
            <div key={k} className="flex flex-wrap items-center justify-between gap-x-4 gap-y-0.5">
              <dt className="flex items-center gap-2">
                <Icon name={icone} className="size-3.5 text-muted" />
                {k}
              </dt>
              <dd className="tabular-nums text-ink">{v}</dd>
            </div>
          ))}
        </dl>
        <p className="mt-4 font-medium text-ink">Fontes</p>
        <ul className="mt-1.5 list-disc space-y-0.5 pl-4">
          {e.sources.map((s) => (
            <li key={s}>{s}</li>
          ))}
        </ul>
        <p className="mt-3 flex items-start gap-1.5">
          <Icon name="info" className="mt-px size-3.5" />
          Estimativa comparativa: serve para comparar origens, não para inventário de emissões.
        </p>
        {e.methodology_path && (
          <Link
            href={`${e.methodology_path}?${new URLSearchParams({ customer_zip_prefix: customerZipPrefix })}`}
            className="mt-3 inline-flex items-center gap-1 font-medium text-signal-ink underline underline-offset-2"
          >
            Ver metodologia completa
            <Icon name="arrowRight" className="size-3.5" />
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
    <span className="inline-flex w-fit items-center gap-1.5 rounded-full bg-signal-soft px-2.5 py-1 text-xs font-medium leading-tight text-signal-ink ring-1 ring-signal/20">
      {badge.icon === "leaf" && <Icon name="leaf" className="size-3.5" />}
      {badge.label}
    </span>
  );
}

/** "Entrega local (~13 km · ~2,59 g CO₂)" -> "Local · ~13 km": no card do celular (D7). */
function shortBadge(label: string) {
  const dentro = label.match(/\(([^·)]+)/)?.[1]?.trim();
  return dentro ? `Local · ${dentro}` : label;
}

const SORT_ICONS: Record<string, IconName> = { proximo: "pin", co2: "leaf", preco: "tag" };

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

  const mask = `linear-gradient(to right, ${edges.start ? "transparent, black 3.5rem" : "black"}, ${
    edges.end ? "black calc(100% - 3.5rem), transparent" : "black"
  })`;
  const arrow =
    "absolute top-1/2 z-10 hidden size-9 -translate-y-1/2 items-center justify-center rounded-full border border-line bg-surface text-ink shadow-lift transition hover:scale-105 sm:flex";

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-3">
        {title && <h2 className="font-display text-2xl tracking-tight text-ink">{title.charAt(0) + title.slice(1).toLowerCase()}</h2>}
        {/* Ordenar (V4): opcoes, rotulos e caminhos vem do servidor. */}
        {sort_options.length > 0 && (
          <nav
            aria-label="Ordenar a vitrine"
            className="no-scrollbar -mx-4 flex w-[calc(100%+2rem)] items-center gap-2 overflow-x-auto px-4 py-1 sm:mx-0 sm:w-auto sm:px-0"
          >
            <span aria-hidden className="flex shrink-0 items-center gap-1.5 text-xs text-muted">
              <Icon name="sliders" className="size-4" />
              Ordenar
            </span>
            <div className="flex shrink-0 items-center gap-0.5 rounded-xl border border-line bg-surface p-0.5 shadow-soft">
              {sort_options.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  aria-current={opt.selected || undefined}
                  disabled={opt.actions.length === 0}
                  onClick={() => opt.actions[0] && run(opt.actions[0])}
                  className={`flex items-center gap-1.5 whitespace-nowrap rounded-lg px-2.5 py-1.5 text-xs font-medium transition sm:px-3 sm:text-sm ${
                    opt.selected ? "bg-ink text-paper shadow-soft" : "text-muted hover:bg-paper-2 hover:text-ink"
                  }`}
                >
                  <Icon name={SORT_ICONS[opt.value] ?? "sliders"} className="size-3.5" />
                  {opt.label}
                </button>
              ))}
            </div>
          </nav>
        )}
      </div>
      {/* Carrossel sem barra de rolagem (apontamento de 02/11): no desktop,
          setas sobre o fade; no toque, o gesto. */}
      <div className="relative">
        <div
          ref={scroller}
          onScroll={measure}
          className="no-scrollbar -mx-4 overflow-x-auto px-4 py-1 sm:mx-0 sm:px-0"
          style={{ maskImage: mask, WebkitMaskImage: mask }}
        >
          <ul className="flex w-max gap-2">
            {categories.map((item) => (
              <li key={item.slug}>
                <button
                  type="button"
                  aria-current={item.selected}
                  disabled={item.actions.length === 0}
                  onClick={() => item.actions[0] && run(item.actions[0])}
                  className={`group flex items-center gap-2 whitespace-nowrap rounded-xl border py-2 pl-2 pr-3 text-sm font-medium transition ${
                    item.selected
                      ? "border-ink bg-ink text-paper shadow-lift"
                      : "border-line bg-surface text-ink-2 shadow-soft hover:-translate-y-px hover:border-line-strong hover:text-ink"
                  }`}
                >
                  <span
                    className={`flex size-7 items-center justify-center rounded-lg ${
                      item.selected ? "bg-paper/15 text-paper" : "bg-paper-2 text-ink-2 group-hover:text-ink"
                    }`}
                  >
                    <Icon name={categoryIcon(item.slug)} className="size-4" />
                  </span>
                  {item.label}
                  <span
                    className={`rounded-md px-1.5 py-0.5 text-[11px] tabular-nums ${
                      item.selected ? "bg-paper/15 text-paper" : "bg-paper-2 text-muted"
                    }`}
                  >
                    {item.product_count}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
        {edges.start && (
          <button type="button" onClick={() => page(-1)} aria-label="Categorias anteriores" className={`${arrow} -left-4`}>
            <Icon name="chevronLeft" className="size-4" />
          </button>
        )}
        {edges.end && (
          <button type="button" onClick={() => page(1)} aria-label="Mais categorias" className={`${arrow} -right-4`}>
            <Icon name="chevronRight" className="size-4" />
          </button>
        )}
      </div>
    </section>
  );
}

function heroIcon(variant: string | undefined, eyebrow: string | null | undefined): IconName {
  if (variant === "regional") return "pin";
  if (variant === "filter" || variant === "empty") return "search";
  if (variant === "profile") {
    if (eyebrow?.includes("Eletr")) return "laptop";
    if (eyebrow?.includes("Beleza")) return "sparkles";
    return "leaf";
  }
  return "store";
}

export function HeroBanner({ block }: { block: HeroBannerBlock }) {
  const { title, subtitle, cta_label, secondary_cta_label, variant = "default", eyebrow } = block.props;
  const { run } = useSdui();
  const [action, secondary] = block.actions;
  // O lift vem no texto do servidor ("levam 1,3× mais"); destacado, nao inventado.
  const lift = variant === "regional" ? subtitle?.match(/(\d+,\d+)×/)?.[1] : undefined;
  const comMapa = (variant === "regional" || variant === "default") && Boolean(eyebrow);
  const vazio = variant === "empty";
  const icone = heroIcon(variant, eyebrow);

  const botoes = (action || secondary) && (
    <div className="flex shrink-0 flex-wrap gap-2">
      {action && (
        <button
          type="button"
          onClick={() => run(action)}
          className="flex items-center gap-2 rounded-xl bg-ink px-4 py-2.5 text-sm font-medium text-paper shadow-soft transition hover:bg-signal sm:px-5"
        >
          {cta_label ?? "Explorar"}
          <Icon name="arrowRight" className="size-4" />
        </button>
      )}
      {secondary && (
        <button
          type="button"
          onClick={() => run(secondary)}
          className="rounded-xl border border-line bg-surface px-4 py-2.5 text-sm font-medium text-ink transition hover:border-line-strong sm:px-5"
        >
          {secondary_cta_label ?? "Ver mais"}
        </button>
      )}
    </div>
  );

  if (vazio) {
    return (
      <section className={`${CARD} relative overflow-hidden px-6 py-10 text-center sm:py-14`}>
        <div className="mx-auto flex size-20 items-center justify-center rounded-full border-2 border-dashed border-line-strong bg-paper-2 text-muted">
          <Icon name="search" className="size-8" strokeWidth={1.5} />
        </div>
        {eyebrow && <p className={`${EYEBROW} mt-6`}>{eyebrow}</p>}
        <h1 className="mx-auto mt-2 max-w-2xl font-display text-3xl tracking-tight text-ink [overflow-wrap:anywhere] sm:text-4xl">
          {title}
        </h1>
        {subtitle && <p className="mx-auto mt-3 max-w-lg text-sm leading-relaxed text-muted sm:text-base">{subtitle}</p>}
        <div className="mt-6 flex justify-center">{botoes}</div>
      </section>
    );
  }

  /*
   * Compacto (D8): ate a Sprint 13 eram ~400 px de veu sobre um placeholder
   * cinza. A `image_url` da amostra e so placeholder: o hero e tipografico, com
   * o mapa dos CEPs do dataset como fundo nas vitrines de regiao.
   */
  return (
    <section
      className={`${CARD} relative overflow-hidden px-5 py-6 sm:px-8 sm:py-8 ${
        variant === "regional" ? "bg-gradient-to-br from-surface via-surface to-signal-soft/60" : ""
      }`}
    >
      {comMapa && (
        <div
          aria-hidden
          className="pointer-events-none absolute -right-16 -top-10 hidden h-[340px] w-[340px] bg-[url('/mapa-brasil.svg')] bg-contain bg-no-repeat opacity-25 md:block dark:opacity-10"
        />
      )}
      <div className="relative flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
        <div className="flex max-w-2xl gap-4">
          <span
            className={`hidden size-12 shrink-0 items-center justify-center rounded-2xl sm:flex ${
              variant === "regional" || variant === "profile" ? "bg-signal-soft text-signal-ink" : "bg-paper-2 text-ink"
            }`}
          >
            <Icon name={icone} className="size-6" />
          </span>
          <div className="min-w-0">
            {eyebrow && <p className={EYEBROW}>{eyebrow}</p>}
            <h1 className="mt-1 font-display text-3xl leading-tight tracking-tight text-ink [overflow-wrap:anywhere] sm:text-4xl">
              {title}
            </h1>
            {subtitle && <p className="mt-2 max-w-xl text-sm leading-relaxed text-muted sm:text-base">{subtitle}</p>}
          </div>
        </div>
        <div className="flex flex-col items-start gap-4 md:items-end">
          {lift && (
            <div className="rounded-2xl border border-signal/20 bg-surface/80 px-4 py-2.5 shadow-soft backdrop-blur">
              <p className="font-display text-3xl leading-none text-signal-ink">{lift}×</p>
              <p className="mt-1 text-xs text-muted">acima da média do Brasil</p>
            </div>
          )}
          {botoes}
        </div>
      </div>
    </section>
  );
}

/**
 * Card da vitrine. Sem nome nem foto no Olist, a identidade vem do que existe:
 * capa no tom da categoria com o icone dela, referencia, peso, volume e nota
 * (o servidor manda pronto). A ORDEM importa: titulo e logo "Sai de ..." — o
 * E2E de teclado encontra o card por esse nome acessivel.
 */
export function ProductCard({ block }: { block: ProductCardBlock }) {
  const {
    product_id,
    price,
    title,
    image_url,
    badge,
    seller_city,
    seller_state,
    distance_km,
    co2_kg,
    category,
    subtitle,
    rating,
    review_count,
  } = block.props;
  const { run } = useSdui();
  const origin = [seller_city, seller_state].filter(Boolean).join(" · ");
  // O card carrega duas `api_call`: o GET abre o detalhe, o POST e o checkout.
  // Distinguir pelo metodo evita depender da ordem em que vieram.
  const detail = block.actions.find((a) => a.type === "api_call" && a.payload.method === "GET");
  const tone = coverTone(category, product_id);

  return (
    <button
      type="button"
      disabled={!detail}
      onClick={() => detail && run(detail)}
      className="group flex h-full w-full flex-col overflow-hidden rounded-2xl border border-line bg-surface text-left shadow-soft transition duration-200 hover:-translate-y-1 hover:border-line-strong hover:shadow-lift disabled:cursor-default"
    >
      <div
        className="relative h-24 w-full overflow-hidden sm:h-32"
        style={image_url ? { backgroundImage: `url(${image_url})`, backgroundSize: "cover" } : { backgroundImage: tone.backgroundImage }}
      >
        {!image_url && (
          <span aria-hidden style={{ color: tone.color }} className="absolute -bottom-3 -right-2 opacity-40 transition duration-300 group-hover:scale-110 group-hover:opacity-60">
            <Icon name={categoryIcon(category)} className="size-24 sm:size-28" strokeWidth={1.2} />
          </span>
        )}
        {badge && (
          <span aria-hidden className="absolute left-2.5 top-2.5 inline-flex items-center gap-1 rounded-full bg-surface/90 px-2 py-0.5 text-[11px] font-medium text-signal-ink shadow-soft backdrop-blur">
            <Icon name="leaf" className="size-3" />
            Local
          </span>
        )}
      </div>
      <div className="flex flex-1 flex-col gap-2 p-3 sm:p-4">
        <h3 className="line-clamp-2 text-sm font-semibold leading-snug text-ink sm:text-[15px]">{title ?? product_id}</h3>
        {origin && (
          <p className="flex min-w-0 items-center gap-1 text-xs text-muted">
            <Icon name="pin" className="size-3.5 shrink-0" />
            <span className="truncate">Sai de {origin}</span>
          </p>
        )}
        {(subtitle || rating != null) && (
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
            {subtitle && <span className="block max-w-full truncate text-[11px] tabular-nums text-muted">{subtitle}</span>}
            <Rating rating={rating} count={review_count} />
          </div>
        )}
        {badge ? (
          <>
            <span className="sm:hidden">
              <span className="inline-flex items-center gap-1 rounded-full bg-signal-soft px-2 py-0.5 text-[11px] font-medium text-signal-ink">
                <Icon name="leaf" className="size-3" />
                {shortBadge(badge.label)}
              </span>
            </span>
            <span className="hidden sm:block">
              <Badge badge={badge} />
            </span>
          </>
        ) : (
          distance_km != null && (
            <p className="flex items-center gap-1 text-xs tabular-nums text-muted">
              <Icon name="route" className="size-3.5" />
              {decimal(distance_km, 0)} km
              {co2_kg != null && ` · ${co2Label(co2_kg)} CO₂`}
            </p>
          )
        )}
        <div className="mt-auto flex items-end justify-between gap-2 pt-2">
          <p className="font-display text-xl tabular-nums text-ink sm:text-2xl">{brl(price)}</p>
          <span
            aria-hidden
            className="flex size-8 items-center justify-center rounded-full bg-paper-2 text-ink transition group-hover:bg-ink group-hover:text-paper"
          >
            <Icon name="arrowRight" className="size-4" />
          </span>
        </div>
      </div>
    </button>
  );
}

/**
 * Detalhe do produto — um bloco vindo do servidor.
 *
 * Sem descricao e sem tags de sustentabilidade: o Olist nao tem esses campos
 * (so o COMPRIMENTO da descricao), e inventa-los numa tela cujo assunto e
 * credibilidade ambiental seria o pior lugar possivel para dado fabricado.
 */
export function ProductDetail({ block }: { block: ProductDetailBlock }) {
  const { product_id, title, price, weight_g, seller_city, seller_state, rating, review_count, badge, category, subtitle } =
    block.props;
  const { addToCart, openCart, closeDetail, inspecting } = useSdui();
  const [quantity, setQuantity] = useState(1);
  const checkout = block.actions.find((a) => a.type === "api_call") ?? null;
  const tone = coverTone(category, product_id);

  const local = [seller_city, seller_state].filter(Boolean).join(" · ");
  const facts = [
    local ? (["store", "Vendedor", local] as const) : null,
    weight_g ? (["scale", "Peso", `${decimal(weight_g, 0)} g`] as const) : null,
    rating !== null
      ? (["star", "Avaliação", `${decimal(rating, 1)} / 5 · ${review_count} ${review_count === 1 ? "pedido" : "pedidos"}`] as const)
      : null,
  ].filter((f) => f !== null);

  const add = (thenOpenCart: boolean) => {
    addToCart({ productId: product_id, title, price }, quantity, checkout);
    closeDetail();
    if (thenOpenCart) openCart(true);
  };

  return (
    <section className={`${CARD} p-4 sm:p-6`}>
      <div className="grid gap-5 sm:grid-cols-[12rem_minmax(0,1fr)] sm:gap-6">
        <div
          className="relative hidden aspect-square overflow-hidden rounded-2xl sm:block"
          style={{ backgroundImage: tone.backgroundImage }}
        >
          <span aria-hidden style={{ color: tone.color }} className="absolute inset-0 flex items-center justify-center opacity-50">
            <Icon name={categoryIcon(category)} className="size-24" strokeWidth={1.1} />
          </span>
        </div>
        <div className="min-w-0">
          <h2 className="font-display text-2xl leading-tight tracking-tight text-ink sm:text-3xl">{title ?? product_id}</h2>
          {subtitle && <p className="mt-1 text-xs tabular-nums text-muted">{subtitle}</p>}
          {/* O id e um hash de 32 caracteres: so interessa a quem inspeciona o JSON. */}
          {inspecting && <p className="mt-1 font-mono text-xs text-muted">{product_id}</p>}

          <p className="mt-4 font-display text-4xl tabular-nums tracking-tight text-ink">{brl(price)}</p>
          {/* Selo e "Como calculamos?" DEPOIS do preco (D10): aberto, empurrava o preco. */}
          {badge && <div className="mt-3">{<Badge badge={badge} explain />}</div>}

          {facts.length > 0 && (
            <dl className="mt-5 grid gap-2 sm:grid-cols-3">
              {facts.map(([icone, label, value]) => (
                <div key={label} className="rounded-xl border border-line bg-surface-2 px-3 py-2.5">
                  <dt className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-[0.12em] text-muted">
                    <Icon name={icone} className={`size-3.5 ${icone === "star" ? "fill-star text-star" : ""}`} />
                    {label}
                  </dt>
                  <dd className="mt-1 text-sm text-ink">{value}</dd>
                </div>
              ))}
            </dl>
          )}

          <div className="mt-5 flex flex-wrap items-center gap-3">
            <span className="text-sm text-muted">Quantidade</span>
            <Stepper value={quantity} onChange={setQuantity} label={title ?? "produto"} />
          </div>

          <div className="mt-5 flex flex-col gap-2 sm:flex-row">
            <button
              type="button"
              onClick={() => add(false)}
              className="flex flex-1 items-center justify-center gap-2 rounded-xl border border-line bg-surface px-5 py-3 text-sm font-medium text-ink transition hover:border-line-strong hover:shadow-soft"
            >
              <Icon name="plus" className="size-4" />
              Adicionar ao carrinho
            </button>
            <button
              type="button"
              onClick={() => add(true)}
              className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-signal px-5 py-3 text-sm font-medium text-on-signal shadow-soft transition hover:bg-signal-strong"
            >
              <Icon name="bag" className="size-4" />
              Ir para o carrinho
            </button>
          </div>
          <p className="mt-3 text-center text-xs text-muted sm:text-left">Simulação acadêmica — nenhum pagamento é processado.</p>
        </div>
      </div>
    </section>
  );
}

export function CheckoutSummary({ block }: { block: CheckoutSummaryBlock }) {
  const { items, subtotal, freight, total } = block.props;

  return (
    <section className={`${CARD} p-5 sm:p-6`}>
      <div className="flex items-center gap-3">
        <span className="flex size-10 items-center justify-center rounded-xl bg-paper-2 text-ink">
          <Icon name="bag" className="size-5" />
        </span>
        <h2 className="font-display text-2xl text-ink">
          {items.length === 1 ? (items[0].title ?? items[0].product_id) : "Seu pedido"}
        </h2>
      </div>
      <dl className="mt-5 space-y-3 text-sm">
        {items.map((item) => (
          <div key={item.product_id} className="flex justify-between gap-4">
            <dt className="text-muted">
              {item.quantity}× {item.title ?? item.product_id}
              <span className="ml-1.5 text-muted">{brl(item.unit_price)}</span>
            </dt>
            <dd className="tabular-nums text-ink">{brl(item.line_total)}</dd>
          </div>
        ))}
        <div className="flex justify-between gap-4 border-t border-line pt-3">
          <dt className="text-muted">Subtotal</dt>
          <dd className="tabular-nums text-ink">{brl(subtotal)}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="flex items-center gap-1.5 text-muted">
            <Icon name="truck" className="size-4" />
            Frete
          </dt>
          <dd className="tabular-nums text-ink">{brl(freight)}</dd>
        </div>
        <div className="flex items-baseline justify-between gap-4 rounded-xl bg-surface-2 px-4 py-3">
          <dt className="font-medium text-ink">Total</dt>
          <dd className="font-display text-2xl tabular-nums text-ink">{brl(total)}</dd>
        </div>
      </dl>
    </section>
  );
}

/** Sugestao de troca: outro produto da mesma categoria, vendedor mais perto. */
function Alternatives({ items }: { items: Alternative[] }) {
  const { run, pending, swapInCart, cart } = useSdui();
  if (items.length === 0) return null;

  return (
    <div className="mt-4 rounded-xl border border-signal/20 bg-signal-soft/50 p-3 sm:p-4">
      <p className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-[0.14em] text-signal-ink">
        <Icon name="leaf" className="size-3.5" />
        Mais perto de você
      </p>
      <ul className="mt-2 space-y-2">
        {items.map((alt) => {
          const action = alt.actions[0];
          // A troca tem preco proprio; a diferenca precisa estar a vista (D5):
          // a regra nao limita o preco, entao quem decide precisa ver quanto custa.
          const atual = cart.find((e) => e.productId === alt.replaces_product_id)?.price;
          const diferenca = atual != null ? alt.price - atual : null;
          return (
            <li key={alt.product_id} className="flex flex-wrap items-center justify-between gap-3 rounded-lg bg-surface px-3 py-2.5 shadow-soft">
              <div className="min-w-0">
                <p className="text-sm text-ink">
                  {alt.title ?? alt.product_id}
                  <span className="ml-2 tabular-nums text-muted">{brl(alt.price)}</span>
                  {diferenca != null && Math.abs(diferenca) >= 0.01 && (
                    <span
                      className={`ml-2 rounded-md px-1.5 py-0.5 text-[11px] font-medium tabular-nums ${
                        diferenca > 0 ? "bg-danger-soft text-danger" : "bg-signal-soft text-signal-ink"
                      }`}
                    >
                      {diferenca > 0 ? "+" : "−"}
                      {brl(Math.abs(diferenca))}
                    </span>
                  )}
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
                  const updated = swapInCart(
                    alt.replaces_product_id,
                    { productId: alt.product_id, title: alt.title, price: alt.price },
                    alt.co2_saved_kg,
                  );
                  run(action, { cart: updated });
                }}
                className="shrink-0 rounded-lg bg-signal px-3 py-1.5 text-xs font-medium text-on-signal transition hover:bg-signal-strong disabled:opacity-50"
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
  const { impacto, inspecting } = useSdui();
  if (shipments.length === 0) return null;

  return (
    <section className={`${CARD} p-5 sm:p-6`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-3">
          <span className="flex size-10 items-center justify-center rounded-xl bg-paper-2 text-ink">
            <Icon name="box" className="size-5" />
          </span>
          <h2 className="font-display text-2xl text-ink">{title ?? "Remessas"}</h2>
        </div>
        <p className="text-sm text-muted">
          {shipments.length === 1 ? "1 remessa" : `${shipments.length} remessas — da maior pegada para a menor`}
        </p>
      </div>

      {/* "Seu impacto" (V6): fecha o ciclo da sugestao "Mais perto de voce"
          no mesmo lugar em que a troca foi feita. */}
      {impacto.trocas > 0 && (
        <p role="status" className="mt-4 flex items-center gap-3 rounded-xl bg-signal px-4 py-3 text-sm text-on-signal shadow-soft">
          <Icon name="leaf" className="size-5" />
          <span>
            <span className="font-semibold">Seu impacto nesta sessão:</span> {co2Label(impacto.kg)} de CO₂ a menos em{" "}
            {impacto.trocas} {impacto.trocas === 1 ? "troca" : "trocas"} por um vendedor mais perto.
          </span>
        </p>
      )}

      <ul className="mt-5 space-y-3">
        {shipments.map((shipment, i) => {
          const origem = [shipment.seller_city, shipment.seller_state].filter(Boolean).join(" · ");
          return (
            <li
              key={shipment.seller_id}
              // O servidor manda ordenado por emissao: a primeira e a que pesa.
              className={`rounded-xl border p-4 ${i === 0 && shipments.length > 1 ? "border-line-strong bg-surface-2" : "border-line"}`}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                  <span className="mt-0.5 flex size-9 items-center justify-center rounded-lg bg-paper-2 text-ink">
                    <Icon name="store" className="size-4" />
                  </span>
                  <div>
                    {/* Cidade do vendedor no lugar do hash do id (D2). */}
                    <p className="text-sm font-medium text-ink">{origem || "Vendedor"}</p>
                    <p className="mt-0.5 text-xs text-muted">
                      {shipment.total_quantity} {shipment.total_quantity === 1 ? "item" : "itens"} ·{" "}
                      {shipment.distance_km !== null ? `${decimal(shipment.distance_km, 0)} km` : "distância indisponível"}
                    </p>
                    {inspecting && <p className="mt-0.5 font-mono text-[11px] text-muted">{shipment.seller_id.slice(0, 12)}…</p>}
                  </div>
                </div>
                <Badge badge={shipment.badge} explain />
              </div>

              <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-1 text-sm">
                <span className="flex items-center gap-1.5 tabular-nums text-ink">
                  <Icon name="truck" className="size-4 text-muted" />
                  {brl(shipment.freight)}
                </span>
                {shipment.co2_kg !== null && (
                  <span className="flex items-center gap-1.5 tabular-nums text-muted">
                    <Icon name="leaf" className="size-4" />
                    {co2Label(shipment.co2_kg)} CO₂
                  </span>
                )}
                {shipment.co2_share !== null && (
                  <span className="tabular-nums text-muted">{decimal(shipment.co2_share * 100, 0)}% da pegada</span>
                )}
              </div>

              {/* A barra e o que faz a remessa dominante saltar aos olhos. Neutra:
                  o verde e sinal de "bom" e aqui mede o quanto a remessa emite. */}
              {shipment.co2_share !== null && (
                <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-line">
                  <div className="h-full rounded-full bg-ink-2" style={{ width: `${shipment.co2_share * 100}%` }} />
                </div>
              )}

              <Alternatives items={shipment.alternatives} />
            </li>
          );
        })}
      </ul>

      {note && <p className="mt-5 text-xs leading-relaxed text-muted">{note}</p>}
    </section>
  );
}

const MODE_ICONS: Record<string, IconName> = { express: "zap", standard: "truck", green: "leaf" };

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
    <section className={`${CARD} p-5 sm:p-6`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-3">
          <span className="flex size-10 items-center justify-center rounded-xl bg-paper-2 text-ink">
            <Icon name="truck" className="size-5" />
          </span>
          <h2 className="font-display text-2xl text-ink">Como entregar</h2>
        </div>
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
            className={`relative flex flex-col gap-3 rounded-xl border p-4 text-left transition disabled:cursor-default ${
              option.selected
                ? "border-signal bg-signal-soft/60 shadow-lift ring-1 ring-signal/40"
                : "border-line bg-surface hover:-translate-y-0.5 hover:border-line-strong hover:shadow-soft disabled:hover:translate-y-0"
            } ${pending ? "opacity-60" : ""}`}
          >
            <div className="flex items-start justify-between gap-2">
              <span className="flex items-center gap-2 text-sm font-semibold text-ink">
                {option.label}
              </span>
              <span
                className={`flex size-8 items-center justify-center rounded-lg ${
                  option.recommended ? "bg-signal text-on-signal" : "bg-paper-2 text-ink"
                }`}
              >
                <Icon name={MODE_ICONS[option.id] ?? "truck"} className="size-4" />
              </span>
            </div>
            {option.recommended && (
              <span className="-mt-1 w-fit rounded-full bg-signal-soft px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-signal-ink ring-1 ring-signal/20">
                Menor emissão
              </span>
            )}

            <p className="font-display text-2xl tabular-nums text-ink">{brl(option.price)}</p>

            <p className="text-xs text-muted">
              {option.eta_days} {option.eta_days === 1 ? "dia útil" : "dias úteis"}
            </p>

            {option.co2_kg !== null && (
              <div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-line">
                  {/* Verde so na opcao de menor emissao: barra verde mais longa
                      na Expressa premiava a que mais emite. */}
                  <div
                    className={`h-full rounded-full ${option.recommended ? "bg-signal" : "bg-ink-2"}`}
                    style={{ width: `${maxCo2 > 0 ? (option.co2_kg / maxCo2) * 100 : 0}%` }}
                  />
                </div>
                <p className="mt-1.5 text-xs tabular-nums text-muted">{co2Label(option.co2_kg)} CO₂</p>
              </div>
            )}

            {option.description && <p className="text-xs leading-relaxed text-muted">{option.description}</p>}
          </button>
        ))}
      </div>

      {/* Sem esta nota os fatores viram "dado do Olist" na leitura de quem ve. */}
      {note && (
        <p className="mt-5 flex items-start gap-1.5 text-xs leading-relaxed text-muted">
          <Icon name="info" className="mt-px size-3.5" />
          {note}
        </p>
      )}
    </section>
  );
}

export function ImpactBanner({ block }: { block: ImpactBannerBlock }) {
  const { distance_km, co2_kg, badge, message } = block.props;
  const stats = [
    distance_km !== null ? (["route", "Distância", `${decimal(distance_km, 0)} km`] as const) : null,
    co2_kg !== null ? (["leaf", "CO₂ estimado", co2Label(co2_kg)] as const) : null,
  ].filter((s) => s !== null);

  return (
    <section className={`${CARD} p-5 sm:p-6`}>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <p className="flex max-w-xl items-start gap-2 text-sm leading-relaxed text-ink-2">
          <Icon name="info" className="mt-0.5 size-4 text-muted" />
          {message}
        </p>
        <Badge badge={badge} />
      </div>
      {stats.length > 0 && (
        <dl className="mt-5 grid grid-cols-2 gap-3">
          {stats.map(([icone, label, value]) => (
            // <dl> so aceita <div> com <dt>/<dd> direto (axe, T9): o icone vai dentro do <dt>.
            <div key={label} className="relative rounded-xl border border-line bg-surface-2 py-3 pl-[4.25rem] pr-4">
              <dt className="text-[11px] font-medium uppercase tracking-[0.12em] text-muted">
                <span
                  aria-hidden
                  className={`absolute left-4 top-1/2 flex size-10 -translate-y-1/2 items-center justify-center rounded-xl ${icone === "leaf" ? "bg-signal-soft text-signal-ink" : "bg-paper-2 text-ink"}`}
                >
                  <Icon name={icone} className="size-5" />
                </span>
                {label}
              </dt>
              <dd className="font-display text-2xl tabular-nums text-ink">{value}</dd>
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
    const vezes = !o.chosen && o.co2_kg !== null && chosenCo2 ? o.co2_kg / chosenCo2 : null;
    return (
      <li
        key={o.seller_id}
        aria-current={o.chosen || undefined}
        className={`rounded-xl border p-3.5 transition ${o.chosen ? "border-signal bg-signal-soft/50 ring-1 ring-signal/30" : "border-line bg-surface"}`}
      >
        <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1">
          <p className="flex items-center gap-2 text-sm font-medium text-ink">
            <Icon name="pin" className={`size-4 ${o.chosen ? "text-signal" : "text-muted"}`} />
            {origem}
            {o.local && (
              <span className="rounded-full bg-signal-soft px-2 py-0.5 text-[11px] font-medium text-signal-ink">entrega local</span>
            )}
          </p>
          <p className="font-display text-lg tabular-nums text-ink">{brl(o.price)}</p>
        </div>
        <p className="mt-1 pl-6 text-xs tabular-nums text-muted">
          {distancia}
          {o.co2_kg !== null && ` · ${co2Label(o.co2_kg)} CO₂`}
          {vezes !== null && vezes >= 1.05 && ` · ${decimal(vezes, 1)}× a emissão da escolhida`}
        </p>
        {o.co2_kg !== null && maxCo2 > 0 && (
          <div className="ml-6 mt-2 h-1.5 overflow-hidden rounded-full bg-line">
            <div
              className={`h-full rounded-full ${o.co2_kg === minCo2 ? "bg-signal" : "bg-ink-2"}`}
              style={{ width: `${(o.co2_kg / maxCo2) * 100}%` }}
            />
          </div>
        )}
        {o.chosen && o.reason && (
          <p className="mt-2 flex items-center gap-1.5 pl-6 text-xs font-medium text-signal-ink">
            <Icon name="check" className="size-3.5" />
            <span>Escolhida: {o.reason}</span>
          </p>
        )}
      </li>
    );
  };

  return (
    <section className={`${CARD} p-5 sm:p-6`}>
      <h2 className="flex items-center gap-2 font-display text-xl text-ink">
        <Icon name="compass" className="size-5 text-muted" />
        {title}
      </h2>
      <ol className="mt-4 space-y-2">{vista.map(row)}</ol>
      {resto.length > 0 && (
        <details className="group/mais mt-2">
          <summary className="flex cursor-pointer list-none items-center gap-1 rounded-lg px-1 py-1.5 text-sm font-medium text-muted transition hover:text-ink">
            Ver as outras {resto.length} {resto.length === 1 ? "origem" : "origens"}
            <Icon name="chevronDown" className="size-4 transition group-open/mais:rotate-180" />
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
  const { title, viewbox, width, height, background_url, buyer, origins, radius_100km, caption } = block.props;
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
    <section className={`${CARD} p-4 sm:p-6`}>
      <h2 className="flex items-center gap-2 font-display text-xl text-ink">
        <Icon name="globe" className="size-5 text-muted" />
        {title}
      </h2>
      <svg
        viewBox={viewbox}
        role="img"
        aria-label={resumo}
        className="mt-4 aspect-16/10 w-full rounded-xl border border-line bg-surface-2"
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
        {/* Rotulo afastado do marcador, com halo da cor do fundo (D6) e do lado
            OPOSTO ao da escolhida: perto (ex.: 50 km), "Voce" caia colado no
            ponto verde e parecia nomear o vendedor. */}
        <text
          x={buyer.x + (escolhida && escolhida.x > buyer.x ? -u * 11 : u * 11)}
          y={buyer.y + (escolhida && escolhida.y < buyer.y ? u * 20 : -u * 11)}
          textAnchor={escolhida && escolhida.x > buyer.x ? "end" : "start"}
          fontSize={u * 12}
          strokeWidth={u * 4}
          strokeLinejoin="round"
          className="fill-ink stroke-surface-2 font-semibold"
          style={{ paintOrder: "stroke" }}
        >
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
            <span aria-hidden className="size-2.5 rounded-full bg-muted" /> {outras} {outras === 1 ? "outra origem" : "outras origens"}
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
    <section className={`${CARD} p-5 sm:p-7`}>
      <h2 className="font-display text-2xl tracking-tight text-ink">{title}</h2>
      {paragraphs.map((texto) => (
        <p key={texto} className="mt-3 max-w-prose text-[15px] leading-relaxed text-ink-2">
          {texto}
        </p>
      ))}
      {items.length > 0 && (
        <ul className="mt-4 max-w-prose space-y-2 text-[15px] leading-relaxed text-ink-2">
          {items.map((item) => (
            <li key={item} className="flex gap-2.5">
              <span aria-hidden className="mt-2.5 size-1.5 shrink-0 rounded-full bg-signal" />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      )}
      {note && (
        <p className="mt-4 flex items-start gap-1.5 text-xs leading-relaxed text-muted">
          <Icon name="info" className="mt-px size-3.5" />
          {note}
        </p>
      )}
    </section>
  );
}

/**
 * Tabela de resultados (Sprint 16, V8). Celulas ja vem formatadas do servidor;
 * no celular a tabela rola na horizontal dentro do cartao, nao a pagina.
 */
export function DataTable({ block }: { block: DataTableBlock }) {
  const { title, caption, columns, rows } = block.props;
  return (
    <section className={`${CARD} p-5 sm:p-6`}>
      {title && <h3 className="font-display text-lg text-ink">{title}</h3>}
      {caption && <p className="mt-2 max-w-prose text-sm leading-relaxed text-muted">{caption}</p>}
      <div className="-mx-5 mt-4 overflow-x-auto px-5 sm:-mx-6 sm:px-6">
        {/* Largura minima por coluna: no celular a tabela larga rola; a de
            duas colunas cabe. O texto longo quebra em vez de vazar. */}
        <table className="w-full border-collapse text-sm" style={{ minWidth: `${columns.length * 6}rem` }}>
          <thead>
            <tr className="border-b border-line-strong text-left text-[11px] uppercase tracking-[0.1em] text-muted">
              {columns.map((coluna, i) => (
                <th key={i} scope="col" className={`py-2.5 pr-4 font-medium ${i > 0 ? "text-right" : ""}`}>
                  {coluna}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, r) => (
              <tr
                key={r}
                className={`border-b border-line/70 transition hover:bg-surface-2 ${row.emphasis ? "bg-signal-soft/50 font-medium text-ink" : "text-ink-2"}`}
              >
                {row.cells.map((cell, i) =>
                  i === 0 ? (
                    <th key={i} scope="row" className="py-2.5 pr-4 text-left font-[inherit]">
                      {cell}
                    </th>
                  ) : (
                    <td key={i} className="py-2.5 pr-4 text-right tabular-nums">
                      {cell}
                    </td>
                  ),
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
