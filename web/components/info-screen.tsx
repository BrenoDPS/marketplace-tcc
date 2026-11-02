import Link from "next/link";
import { Brand, SiteFooter } from "@/components/controls";
import { Icon } from "@/components/icons";
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
      <header className="sticky top-0 z-20 border-b border-line/80 bg-paper/80 backdrop-blur-xl">
        <div className={`mx-auto flex h-16 ${largura} items-center justify-between gap-4 px-4 sm:px-6`}>
          <Brand href={customerZipPrefix ? `/?customer_zip_prefix=${customerZipPrefix}` : "/"} />
          <Link
            href={customerZipPrefix ? `/?customer_zip_prefix=${customerZipPrefix}` : "/"}
            className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-muted transition hover:bg-surface hover:text-ink"
          >
            <Icon name="arrowLeft" className="size-4" />
            <span className="hidden sm:inline">Vitrine</span>
          </Link>
        </div>
      </header>
      <main className={`mx-auto w-full ${largura} flex-1 px-4 py-8 sm:px-6 sm:py-10`}>
        {result.ok ? (
          <SduiRoot screen={result.screen} />
        ) : (
          <p className="rounded-2xl border border-line bg-surface p-6 text-muted">{result.detail}</p>
        )}
      </main>
      <SiteFooter />
    </SduiProvider>
  );
}
