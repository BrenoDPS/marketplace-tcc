"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { CONTEXTS, DEMO_ZIPS } from "@/lib/sdui";

function hrefFor(customerZipPrefix: string, context: string) {
  const params = new URLSearchParams({ customer_zip_prefix: customerZipPrefix, context });
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
}: {
  customerZipPrefix: string;
  context: string;
}) {
  const router = useRouter();

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
              onClick={() => router.push(hrefFor(customerZipPrefix, item.value))}
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

        <label className="ml-auto flex items-center gap-2 text-sm">
          <span className="text-muted">CEP</span>
          <select
            value={customerZipPrefix}
            onChange={(e) => router.push(hrefFor(e.target.value, context))}
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
      </div>
    </header>
  );
}
