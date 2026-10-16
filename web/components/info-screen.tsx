import Link from "next/link";
import { SduiRoot } from "@/components/sdui";
import { SduiProvider } from "@/components/sdui-context";
import { fetchInfoScreen } from "@/lib/api";

/**
 * Casca das telas explicativas (metodologia V7, pesquisa V8). Server
 * Component, como a Home: a tela inteira vem do servidor e o MESMO renderer
 * desenha; aqui so o cabecalho de volta a vitrine.
 */
export async function InfoScreen({
  endpoint,
  customerZipPrefix,
  wide = false,
}: {
  endpoint: "methodology" | "research";
  customerZipPrefix?: string;
  wide?: boolean;
}) {
  const result = await fetchInfoScreen(endpoint, customerZipPrefix);
  const largura = wide ? "max-w-5xl" : "max-w-3xl";

  return (
    <SduiProvider customerZipPrefix={customerZipPrefix ?? ""}>
      <header className="border-b border-line">
        <div className={`mx-auto flex ${largura} items-center px-4 py-4 sm:px-6`}>
          <Link href={customerZipPrefix ? `/?customer_zip_prefix=${customerZipPrefix}` : "/"} className="font-display text-lg tracking-tight text-ink">
            Olist<span className="text-signal">.</span>
          </Link>
        </div>
      </header>
      <main className={`mx-auto w-full ${largura} px-4 py-8 sm:px-6 sm:py-10`}>
        {result.ok ? (
          <SduiRoot screen={result.screen} />
        ) : (
          <p className="rounded-xl border border-line bg-surface p-6 text-muted">{result.detail}</p>
        )}
      </main>
    </SduiProvider>
  );
}
