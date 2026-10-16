import Link from "next/link";
import { SduiRoot } from "@/components/sdui";
import { SduiProvider } from "@/components/sdui-context";
import { fetchMethodology } from "@/lib/api";

const first = (value: string | string[] | undefined) =>
  Array.isArray(value) ? value[0] : value;

/**
 * Metodologia (Sprint 16, V7). Server Component, como a Home: a tela inteira
 * vem de `GET /api/v1/methodology` e o MESMO renderer desenha. O texto e
 * escrito pelo servidor a partir das constantes do motor de CO2.
 */
export default async function MetodologiaPage({ searchParams }: PageProps<"/metodologia">) {
  const params = await searchParams;
  const customerZipPrefix = first(params.customer_zip_prefix);
  const result = await fetchMethodology(customerZipPrefix);

  return (
    <SduiProvider customerZipPrefix={customerZipPrefix ?? ""}>
      <header className="border-b border-line">
        <div className="mx-auto flex max-w-3xl items-center px-4 py-4 sm:px-6">
          <Link href={customerZipPrefix ? `/?customer_zip_prefix=${customerZipPrefix}` : "/"} className="font-display text-lg tracking-tight text-ink">
            Olist<span className="text-signal">.</span>
          </Link>
        </div>
      </header>
      <main className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6 sm:py-10">
        {result.ok ? (
          <SduiRoot screen={result.screen} />
        ) : (
          <p className="rounded-xl border border-line bg-surface p-6 text-muted">{result.detail}</p>
        )}
      </main>
    </SduiProvider>
  );
}
