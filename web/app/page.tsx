import Link from "next/link";
import { ContextBar, Controls, EntryScreen, SiteFooter } from "@/components/controls";
import { Icon } from "@/components/icons";
import { SduiRoot } from "@/components/sdui";
import { SduiProvider } from "@/components/sdui-context";
import { fetchHome } from "@/lib/api";
import { findCheckoutAction } from "@/lib/sdui";

const first = (value: string | string[] | undefined) =>
  Array.isArray(value) ? value[0] : value;

/**
 * Server Component: o `ScreenResponse` e buscado no servidor e chega ao browser
 * ja como HTML (meta de TTFB < 200 ms do PRD). Só o executor de `actions` roda
 * no cliente.
 */
export default async function HomePage({ searchParams }: PageProps<"/">) {
  const params = await searchParams;
  const customerZipPrefix = first(params.customer_zip_prefix) ?? first(params.cep);
  const context = first(params.context) ?? "default";
  const search = first(params.q);
  const category = first(params.category);
  const sort = first(params.sort);

  if (!customerZipPrefix) return <EntryScreen />;

  const result = await fetchHome(customerZipPrefix, context, search, category, sort);

  return (
    <SduiProvider
      customerZipPrefix={customerZipPrefix}
      // Sem isto, um carrinho restaurado do storage apos F5 ficaria sem como
      // fechar a compra ate o usuario reabrir algum produto.
      checkoutAction={result.ok ? findCheckoutAction(result.screen) : null}
    >
      <Controls
        customerZipPrefix={customerZipPrefix}
        context={context}
        search={search}
        category={category}
        sort={sort}
      />
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:px-6 sm:py-8">
        {result.ok ? (
          <SduiRoot
            screen={result.screen}
            before={
              <ContextBar
                customerZipPrefix={customerZipPrefix}
                context={context}
                search={search}
                category={category}
                sort={sort}
              />
            }
          />
        ) : (
          <div className="mx-auto mt-10 max-w-xl rounded-3xl border border-line bg-surface p-8 text-center shadow-lift">
            <span className="mx-auto flex size-14 items-center justify-center rounded-2xl bg-paper-2 text-muted">
              <Icon name="pin" className="size-6" />
            </span>
            <h2 className="mt-5 font-display text-2xl text-ink">Não foi possível montar a vitrine</h2>
            <p className="mt-2 text-muted">{result.detail}</p>
            {result.status === 422 && (
              <p className="mt-4 text-sm text-muted">
                Este CEP não existe na amostra de demonstração. Tente{" "}
                <Link className="font-medium text-signal-ink underline underline-offset-2" href="/?customer_zip_prefix=05311&context=default">
                  05311
                </Link>{" "}
                ou{" "}
                <Link className="font-medium text-signal-ink underline underline-offset-2" href="/?customer_zip_prefix=60165&context=default">
                  60165
                </Link>
                .
              </p>
            )}
          </div>
        )}
      </main>
      <SiteFooter />
    </SduiProvider>
  );
}
