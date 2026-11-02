"use client";

import Form from "next/form";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { CONTEXTS, DEMO_ZIPS } from "@/lib/sdui";
import { Icon, type IconName } from "./icons";
import { useSdui } from "./sdui-context";

/**
 * Trocar CEP ou contexto preserva o filtro ativo: contexto e filtro compoem
 * (`conscious_buyer` + busca = "informatica mais perto de mim"), e perder a
 * busca a cada clique escondia justamente essa combinacao.
 */
function hrefFor(
  customerZipPrefix: string,
  context: string,
  filter: { search?: string; category?: string; sort?: string } = {},
) {
  const params = new URLSearchParams({ customer_zip_prefix: customerZipPrefix, context });
  if (filter.search) params.set("q", filter.search);
  if (filter.category) params.set("category", filter.category);
  if (filter.sort) params.set("sort", filter.sort);
  return `/?${params}`;
}

const CONTEXT_ICONS: Record<string, IconName> = {
  default: "pin",
  electronics_expert: "laptop",
  beauty_lover: "sparkles",
  conscious_buyer: "leaf",
};

/** Marca: folha + nome. O ponto verde da versao anterior virou o icone. */
export function Brand({ href = "/" }: { href?: string }) {
  return (
    <Link href={href} className="group flex items-center gap-2 rounded-lg" aria-label="Olist — início">
      <span className="flex size-8 items-center justify-center rounded-xl bg-ink text-paper transition group-hover:bg-signal">
        <Icon name="leaf" className="size-4" />
      </span>
      <span className="font-display text-xl tracking-tight text-ink">
        Olist<span className="text-signal">.</span>
      </span>
    </Link>
  );
}

/** Passo [0] da jornada: sem CEP o backend nao responde (422), entao ele vem antes da vitrine. */
export function EntryScreen() {
  const router = useRouter();
  const [zip, setZip] = useState("");
  const valores: [IconName, string, string][] = [
    ["route", "Distância de verdade", "Calculada entre o seu CEP e o do vendedor, convertida em estrada."],
    ["leaf", "CO₂ de cada entrega", "Estimado pela cadeia de transporte (ISO 14083 e GLEC), com a conta aberta."],
    ["pin", "Selo de entrega local", "Vendedores a menos de 100 km de você ganham destaque na vitrine."],
  ];

  return (
    <main className="relative flex min-h-dvh flex-col overflow-hidden">
      <div
        aria-hidden
        className="pointer-events-none absolute -right-40 top-10 hidden h-[720px] w-[720px] bg-[url('/mapa-brasil.svg')] bg-contain bg-no-repeat opacity-[0.22] lg:block dark:opacity-10"
      />
      <header className="mx-auto flex w-full max-w-6xl items-center px-6 py-6">
        <Brand />
      </header>
      <div className="mx-auto grid w-full max-w-6xl flex-1 items-center gap-12 px-6 pb-16 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]">
        <section className="max-w-xl">
          <p className="inline-flex items-center gap-2 rounded-full border border-line bg-surface px-3 py-1 text-xs font-medium text-muted shadow-soft">
            <span className="size-1.5 rounded-full bg-signal" />
            Marketplace com logística verde
          </p>
          <h1 className="mt-6 font-display text-5xl leading-[1.05] tracking-tight text-ink [overflow-wrap:anywhere] sm:text-6xl">
            Compre de quem está perto.
          </h1>
          <p className="mt-5 text-lg leading-relaxed text-muted">
            A distância entre você e o vendedor define o frete, o CO₂ estimado e o selo de logística
            verde. Informe o prefixo do seu CEP para montar a sua vitrine.
          </p>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (zip.trim()) router.push(hrefFor(zip.trim(), "default"));
            }}
            className="mt-8 flex flex-col gap-3 rounded-2xl border border-line bg-surface p-2 shadow-lift sm:flex-row"
          >
            <label className="flex flex-1 items-center gap-3 px-3">
              <Icon name="pin" className="size-5 text-muted" />
              <input
                value={zip}
                onChange={(e) => setZip(e.target.value.replace(/\D/g, "").slice(0, 5))}
                inputMode="numeric"
                placeholder="Prefixo do CEP (5 dígitos)"
                aria-label="Prefixo do CEP"
                className="w-full bg-transparent py-3 text-base text-ink outline-none placeholder:text-muted/70"
              />
            </label>
            <button
              type="submit"
              disabled={!zip.trim()}
              className="flex items-center justify-center gap-2 rounded-xl bg-ink px-6 py-3 text-sm font-medium text-paper transition hover:bg-signal disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-ink"
            >
              Entrar
              <Icon name="arrowRight" className="size-4" />
            </button>
          </form>

          <div className="mt-8">
            <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted">Exemplos para testar</p>
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              {DEMO_ZIPS.map((demo) => (
                <button
                  key={demo.value}
                  type="button"
                  onClick={() => router.push(hrefFor(demo.value, "default"))}
                  className="group flex items-center gap-3 rounded-2xl border border-line bg-surface px-4 py-3 text-left shadow-soft transition hover:-translate-y-0.5 hover:border-line-strong hover:shadow-lift"
                >
                  <span className="flex size-10 items-center justify-center rounded-xl bg-paper-2 text-ink">
                    <Icon name="pin" className="size-5" />
                  </span>
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-medium text-ink">{demo.label}</span>
                    <span className="block truncate text-xs tabular-nums text-muted">
                      CEP {demo.value} · {demo.hint}
                    </span>
                  </span>
                  <Icon name="arrowRight" className="ml-auto size-4 text-muted transition group-hover:translate-x-0.5 group-hover:text-ink" />
                </button>
              ))}
            </div>
          </div>
        </section>

        <ul className="grid gap-4">
          {valores.map(([icone, titulo, texto], i) => (
            <li
              key={titulo}
              className="flex items-start gap-4 rounded-2xl border border-line bg-surface/90 p-5 shadow-soft backdrop-blur animate-rise"
              style={{ animationDelay: `${i * 80}ms` }}
            >
              <span className={`flex size-11 items-center justify-center rounded-xl ${i === 1 ? "bg-signal-soft text-signal-ink" : "bg-paper-2 text-ink"}`}>
                <Icon name={icone} className="size-5" />
              </span>
              <span>
                <span className="block font-display text-lg text-ink">{titulo}</span>
                <span className="mt-1 block text-sm leading-relaxed text-muted">{texto}</span>
              </span>
            </li>
          ))}
        </ul>
      </div>
      <SiteFooter />
    </main>
  );
}

/** "Entregar em": CEP editavel num popover. Os CEPs de exemplo ficam rotulados como exemplos (D8). */
function LocationPicker({
  customerZipPrefix,
  onChange,
}: {
  customerZipPrefix: string;
  onChange: (zip: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [zip, setZip] = useState(customerZipPrefix);
  const box = useRef<HTMLDivElement>(null);
  const demo = DEMO_ZIPS.find((d) => d.value === customerZipPrefix);

  useEffect(() => {
    if (!open) return;
    const fora = (e: MouseEvent) => box.current && !box.current.contains(e.target as Node) && setOpen(false);
    const esc = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", fora);
    document.addEventListener("keydown", esc);
    return () => {
      document.removeEventListener("mousedown", fora);
      document.removeEventListener("keydown", esc);
    };
  }, [open]);

  const go = (value: string) => {
    setOpen(false);
    if (value && value !== customerZipPrefix) onChange(value);
  };

  return (
    <div ref={box} className="relative">
      <button
        type="button"
        aria-expanded={open}
        aria-haspopup="dialog"
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 rounded-xl px-2 py-1.5 text-left transition hover:bg-paper-2"
      >
        <Icon name="pin" className="size-5 text-signal" />
        <span className="leading-tight">
          <span className="hidden text-[11px] text-muted sm:block">Entregar em</span>
          <span className="block text-sm font-medium tabular-nums text-ink">
            {customerZipPrefix}
            {demo && <span className="hidden font-normal text-muted lg:inline"> · {demo.label}</span>}
          </span>
          {/* Nome acessivel = texto visivel + acao (WCAG 2.5.3, achado do axe no T9). */}
          <span className="sr-only">, alterar CEP</span>
        </span>
        <Icon name="chevronDown" className={`size-4 text-muted transition ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <div
          role="dialog"
          aria-label="Alterar CEP de entrega"
          className="absolute left-0 top-full z-30 mt-2 w-80 rounded-2xl border border-line bg-surface p-4 shadow-float animate-rise"
        >
          <p className="text-sm font-medium text-ink">Onde você está?</p>
          <p className="mt-1 text-xs leading-relaxed text-muted">
            O prefixo do CEP (5 dígitos) define a distância, o frete e o CO₂ de cada oferta.
          </p>
          <form
            className="mt-3 flex gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              go(zip.trim());
            }}
          >
            <input
              autoFocus
              value={zip}
              onChange={(e) => setZip(e.target.value.replace(/\D/g, "").slice(0, 5))}
              inputMode="numeric"
              aria-label="Novo prefixo do CEP"
              className="w-full rounded-xl border border-line bg-surface-2 px-3 py-2 text-sm tabular-nums text-ink outline-none focus:border-signal"
            />
            <button type="submit" className="rounded-xl bg-ink px-3.5 py-2 text-sm font-medium text-paper transition hover:bg-signal">
              Usar
            </button>
          </form>
          <p className="mt-4 text-[11px] font-medium uppercase tracking-[0.14em] text-muted">Exemplos para testar</p>
          <ul className="mt-2 space-y-1">
            {DEMO_ZIPS.map((d) => (
              <li key={d.value}>
                <button
                  type="button"
                  onClick={() => go(d.value)}
                  className="flex w-full items-center justify-between rounded-lg px-2 py-1.5 text-left text-sm transition hover:bg-paper-2"
                >
                  <span className="text-ink">
                    {d.value} <span className="text-muted">· {d.label}</span>
                  </span>
                  <span className="text-xs text-muted">{d.hint}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

/** Trocar contexto ou CEP so muda a URL: o servidor decide o layout que volta. */
export function Controls({
  customerZipPrefix,
  context,
  search,
  category,
  sort,
}: {
  customerZipPrefix: string;
  context: string;
  search?: string;
  category?: string;
  sort?: string;
}) {
  const { cart, openCart, inspecting, toggleInspecting, navigate, navigating } = useSdui();
  const [menuOpen, setMenuOpen] = useState(false);
  const filter = { search, category, sort };
  const cartCount = cart.reduce((sum, entry) => sum + entry.quantity, 0);

  const searchForm = (className: string) => (
    /* `next/form` com action string = GET nativo: sem JS continua funcionando.
       Com JS a busca vai pela transicao (indicador de carregamento). */
    <Form
      action="/"
      onSubmit={(e) => {
        e.preventDefault();
        const dados = new FormData(e.currentTarget);
        navigate(`/?${new URLSearchParams(dados as unknown as Record<string, string>)}`);
      }}
      className={`group relative flex items-center ${className}`}
    >
      <input type="hidden" name="customer_zip_prefix" value={customerZipPrefix} />
      <input type="hidden" name="context" value={context} />
      {sort && <input type="hidden" name="sort" value={sort} />}
      <Icon name="search" className="pointer-events-none absolute left-3.5 size-4 text-muted" />
      <input
        // `key` amarrado ao termo forca o remount: sem isso o input fica com o
        // valor antigo depois de uma navegacao client-side.
        key={search ?? ""}
        name="q"
        type="search"
        defaultValue={search ?? ""}
        placeholder="Buscar categoria — ex.: relógios"
        aria-label="Buscar por categoria"
        className="h-10 w-full rounded-xl border border-line bg-surface-2 pl-10 pr-24 text-sm text-ink outline-none transition placeholder:text-muted/70 focus:border-line-strong focus:bg-surface focus:shadow-soft"
      />
      <button
        type="submit"
        className="absolute right-1 h-8 rounded-lg bg-ink px-3.5 text-xs font-medium text-paper transition hover:bg-signal"
      >
        Buscar
      </button>
    </Form>
  );

  const sduiToggle = (
    // Mostra o JSON por tras de cada bloco: a prova ao vivo de que a tela vem do
    // servidor. Discreto de proposito (apontamento de 02/11): e ferramenta da
    // banca, nao da compra. O nome acessivel "SDUI" e o do roteiro e do E2E.
    <button
      type="button"
      aria-pressed={inspecting}
      onClick={toggleInspecting}
      title="Inspecionar a tela: contorna cada bloco e mostra o JSON que veio do servidor"
      className={`flex h-10 items-center gap-1.5 rounded-xl px-2.5 text-xs font-medium transition ${
        inspecting ? "bg-signal text-on-signal shadow-soft" : "text-muted hover:bg-paper-2 hover:text-ink"
      }`}
    >
      <Icon name="code" className="size-4" />
      <span className="sr-only lg:not-sr-only">SDUI</span>
    </button>
  );

  return (
    <header className="sticky top-0 z-20 border-b border-line/80 bg-paper/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-6xl items-center gap-3 px-4 sm:gap-5 sm:px-6">
        <Brand href={`/?customer_zip_prefix=${customerZipPrefix}`} />
        <div className="hidden h-6 w-px bg-line sm:block" />
        <LocationPicker
          customerZipPrefix={customerZipPrefix}
          onChange={(zip) => navigate(hrefFor(zip, context, filter))}
        />
        {searchForm("ml-auto hidden max-w-md flex-1 md:flex")}
        <div className="ml-auto flex items-center gap-1 md:ml-0">
          <div className="hidden sm:block">{sduiToggle}</div>
          <button
            type="button"
            onClick={() => openCart(true)}
            className="relative flex h-10 items-center gap-2 rounded-xl border border-line bg-surface px-3 text-sm font-medium text-ink shadow-soft transition hover:border-line-strong hover:shadow-lift"
          >
            <Icon name="bag" className="size-[18px]" />
            {/* Nome acessivel sai do proprio texto (WCAG 2.5.3, T9): "Carrinho 1 item". */}
            <span className="sr-only lg:not-sr-only">Carrinho</span>
            {cartCount > 0 && (
              <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-signal px-1.5 text-[11px] font-semibold tabular-nums text-on-signal">
                <span className="sr-only">&nbsp;</span>
                {cartCount}
                <span className="sr-only">&nbsp;{cartCount === 1 ? "item" : "itens"}</span>
              </span>
            )}
          </button>
          <button
            type="button"
            aria-expanded={menuOpen}
            aria-controls="busca-celular"
            aria-label="Busca e inspeção"
            onClick={() => setMenuOpen((open) => !open)}
            className="flex size-10 items-center justify-center rounded-xl text-ink transition hover:bg-paper-2 md:hidden"
          >
            <Icon name={menuOpen ? "x" : "search"} className="size-5" />
          </button>
        </div>
      </div>
      {menuOpen && (
        <div id="busca-celular" className="flex items-center gap-2 border-t border-line px-4 py-3 md:hidden">
          {searchForm("flex-1")}
          <div className="sm:hidden">{sduiToggle}</div>
        </div>
      )}
      {/* Servidor recompondo a vitrine: barra fina e anuncio para leitor de tela. */}
      <div
        aria-hidden
        className={`absolute inset-x-0 -bottom-px h-0.5 origin-left bg-signal transition-opacity ${
          navigating ? "animate-pulse opacity-100" : "opacity-0"
        }`}
      />
      <span role="status" className="sr-only">
        {navigating ? "Atualizando a vitrine…" : ""}
      </span>
    </header>
  );
}

/**
 * "Ver como": perfis de comprador, logo abaixo do cabecalho (saiu de dentro
 * dele no redesign — la ficava tudo colado). A direita, o caminho para a
 * metodologia e a pesquisa, que antes so se achava pelo selo.
 */
export function ContextBar({
  customerZipPrefix,
  context,
  search,
  category,
  sort,
}: {
  customerZipPrefix: string;
  context: string;
  search?: string;
  category?: string;
  sort?: string;
}) {
  const { navigate } = useSdui();
  const filter = { search, category, sort };
  const ativo = context === "geral" ? "default" : context;
  const query = `?${new URLSearchParams({ customer_zip_prefix: customerZipPrefix })}`;

  return (
    <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
      <nav aria-label="Ver a vitrine como" className="no-scrollbar -mx-4 overflow-x-auto px-4 sm:mx-0 sm:px-0">
        <div className="flex w-max items-center gap-1 rounded-2xl border border-line bg-surface p-1 shadow-soft">
          {CONTEXTS.map((item) => {
            const atual = item.value === ativo;
            return (
              <button
                key={item.value}
                type="button"
                aria-current={atual}
                title={item.hint}
                onClick={() => navigate(hrefFor(customerZipPrefix, item.value, filter))}
                className={`flex items-center gap-2 whitespace-nowrap rounded-xl px-3.5 py-2 text-sm font-medium transition ${
                  atual ? "bg-ink text-paper shadow-soft" : "text-muted hover:bg-paper-2 hover:text-ink"
                }`}
              >
                <Icon name={CONTEXT_ICONS[item.value] ?? "store"} className="size-4" />
                {item.label}
              </button>
            );
          })}
        </div>
      </nav>
      <div className="no-scrollbar -mx-4 flex items-center gap-1 overflow-x-auto px-1 text-sm sm:mx-0 sm:px-0">
        <Link
          href={`/metodologia${query}`}
          className="flex shrink-0 items-center gap-2 whitespace-nowrap rounded-xl px-3 py-2 text-muted transition hover:bg-surface hover:text-ink"
        >
          <Icon name="book" className="size-4" />
          Como calculamos
        </Link>
        <Link
          href={`/pesquisa${query}`}
          className="flex shrink-0 items-center gap-2 whitespace-nowrap rounded-xl px-3 py-2 text-muted transition hover:bg-surface hover:text-ink"
        >
          <Icon name="chart" className="size-4" />
          O que a pesquisa encontrou
        </Link>
      </div>
    </div>
  );
}

export function SiteFooter() {
  return (
    <footer className="mt-auto border-t border-line">
      <div className="mx-auto flex max-w-6xl flex-col gap-2 px-6 py-6 text-xs text-muted sm:flex-row sm:items-center sm:justify-between">
        <p>
          Marketplace contextual adaptativo · TCC de Engenharia de Computação · Facens, 2026
        </p>
        <p>Dados públicos da Olist (2016–2018) · simulação acadêmica, sem pagamento</p>
      </div>
    </footer>
  );
}
