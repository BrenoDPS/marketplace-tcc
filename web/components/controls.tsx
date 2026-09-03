"use client";

import Form from "next/form";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { CONTEXTS, DEMO_ZIPS } from "@/lib/sdui";
import { useSdui } from "./sdui-context";

/**
 * Trocar CEP ou contexto preserva o filtro ativo: contexto e filtro compoem
 * (`conscious_buyer` + busca = "informatica mais perto de mim"), e perder a
 * busca a cada clique escondia justamente essa combinacao.
 */
function hrefFor(
  customerZipPrefix: string,
  context: string,
  filter: { search?: string; category?: string } = {},
) {
  const params = new URLSearchParams({ customer_zip_prefix: customerZipPrefix, context });
  if (filter.search) params.set("q", filter.search);
  if (filter.category) params.set("category", filter.category);
  return `/?${params}`;
}

/** Passo [0] da jornada: sem CEP o backend nao responde (422), entao ele vem antes da vitrine. */
export function EntryScreen() {
  const router = useRouter();
  const [zip, setZip] = useState("");

  return (
    <main className="mx-auto flex min-h-dvh w-full max-w-xl flex-col justify-center px-6 py-16">
      <p className="text-[11px] uppercase tracking-[0.2em] text-muted">
        Olist SDUI Marketplace
      </p>
      <h1 className="mt-4 font-display text-4xl leading-tight tracking-tight text-ink sm:text-5xl">
        Onde você está?
      </h1>
      <p className="mt-4 text-muted">
        A distância entre você e o vendedor define o frete, o CO₂ estimado e o selo de
        logística verde. Informe o prefixo do seu CEP para começar.
      </p>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (zip.trim()) router.push(hrefFor(zip.trim(), "default"));
        }}
        className="mt-8 flex gap-2"
      >
        <input
          value={zip}
          onChange={(e) => setZip(e.target.value.replace(/\D/g, "").slice(0, 5))}
          inputMode="numeric"
          placeholder="05311"
          aria-label="Prefixo do CEP"
          className="w-full rounded-full border border-line bg-surface px-5 py-3 text-ink placeholder:text-muted/60"
        />
        <button
          type="submit"
          disabled={!zip.trim()}
          className="shrink-0 rounded-full bg-ink px-6 py-3 text-sm font-medium text-paper transition hover:opacity-90 disabled:opacity-40"
        >
          Entrar
        </button>
      </form>

      <div className="mt-10 border-t border-line pt-6">
        <p className="text-[11px] uppercase tracking-wide text-muted">Atalhos de demonstração</p>
        <div className="mt-3 flex flex-col gap-2 sm:flex-row">
          {DEMO_ZIPS.map((demo) => (
            <button
              key={demo.value}
              type="button"
              onClick={() => router.push(hrefFor(demo.value, "default"))}
              className="flex-1 rounded-xl border border-line bg-surface px-4 py-3 text-left transition hover:border-ink/30"
            >
              <span className="font-medium text-ink">{demo.value}</span>
              <span className="ml-2 text-sm text-muted">{demo.label}</span>
              <span className="mt-0.5 block text-[11px] text-muted">{demo.hint}</span>
            </button>
          ))}
        </div>
      </div>
    </main>
  );
}

/** Trocar contexto ou CEP so muda a URL: o servidor decide o layout que volta. */
export function Controls({
  customerZipPrefix,
  context,
  search,
  category,
}: {
  customerZipPrefix: string;
  context: string;
  search?: string;
  category?: string;
}) {
  const router = useRouter();
  const { cart, openCart, inspecting, toggleInspecting } = useSdui();
  const filter = { search, category };
  const cartCount = cart.reduce((sum, entry) => sum + entry.quantity, 0);

  return (
    <header className="sticky top-0 z-10 border-b border-line bg-paper/85 backdrop-blur">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-3 px-6 py-3">
        <a href="/" className="font-display text-lg tracking-tight text-ink">
          Olist<span className="text-signal">.</span>
        </a>

        <nav className="flex flex-wrap gap-1" aria-label="Contexto da vitrine">
          {CONTEXTS.map((item) => (
            <button
              key={item.value}
              type="button"
              aria-current={item.value === context}
              onClick={() => router.push(hrefFor(customerZipPrefix, item.value, filter))}
              className={`rounded-full px-3 py-1.5 text-sm transition ${
                item.value === context
                  ? "bg-ink text-paper"
                  : "text-muted hover:bg-line/60 hover:text-ink"
              }`}
            >
              {item.label}
            </button>
          ))}
        </nav>

        {/* `next/form` com action string = GET nativo: os campos viram query
            string, a navegacao e client-side e continua funcionando sem JS.
            Os hidden preservam CEP e contexto; omitir `category` limpa o
            filtro de categoria a cada nova busca. */}
        <Form action="/" className="order-last flex w-full gap-2 sm:order-none sm:ml-auto sm:w-auto">
          <input type="hidden" name="customer_zip_prefix" value={customerZipPrefix} />
          <input type="hidden" name="context" value={context} />
          <input
            // `key` amarrado ao termo forca o remount: sem isso o input fica
            // com o valor antigo depois de uma navegacao client-side (ex.: "Ver
            // tudo" limpa a vitrine mas a caixa continuava escrita "bebes").
            key={search ?? ""}
            name="q"
            type="search"
            defaultValue={search ?? ""}
            placeholder="Buscar categoria…"
            aria-label="Buscar por categoria"
            className="w-full rounded-full border border-line bg-surface px-4 py-1.5 text-sm text-ink placeholder:text-muted/60 sm:w-52"
          />
          <button
            type="submit"
            className="shrink-0 rounded-full border border-line px-3.5 py-1.5 text-sm text-muted transition hover:border-ink/30 hover:text-ink"
          >
            Buscar
          </button>
        </Form>

        <label className="flex items-center gap-2 text-sm">
          <span className="text-muted">CEP</span>
          <select
            value={customerZipPrefix}
            onChange={(e) => router.push(hrefFor(e.target.value, context, filter))}
            className="rounded-full border border-line bg-surface px-3 py-1.5 text-ink"
          >
            {DEMO_ZIPS.some((z) => z.value === customerZipPrefix) ? null : (
              <option value={customerZipPrefix}>{customerZipPrefix}</option>
            )}
            {DEMO_ZIPS.map((demo) => (
              <option key={demo.value} value={demo.value}>
                {demo.value} · {demo.label}
              </option>
            ))}
          </select>
        </label>

        {/* Mostra o JSON por tras de cada bloco: e a prova ao vivo de que a
            tela vem montada do servidor, e nao um mockup. */}
        <button
          type="button"
          aria-pressed={inspecting}
          onClick={toggleInspecting}
          title="Contorna cada bloco e mostra o JSON que veio do servidor"
          className={`rounded-full px-3 py-1.5 font-mono text-xs transition ${
            inspecting
              ? "bg-signal text-white"
              : "text-muted hover:bg-line/60 hover:text-ink"
          }`}
        >
          SDUI
        </button>

        <button
          type="button"
          onClick={() => openCart(true)}
          className="flex items-center gap-2 rounded-full border border-line px-3.5 py-1.5 text-sm text-ink transition hover:border-ink/30"
        >
          Carrinho
          {cartCount > 0 && (
            <span className="rounded-full bg-signal px-1.5 py-0.5 text-[11px] font-medium tabular-nums leading-none text-white">
              {cartCount}
            </span>
          )}
        </button>
      </div>
    </header>
  );
}
