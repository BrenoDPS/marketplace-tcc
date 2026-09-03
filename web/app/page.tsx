import { Controls, EntryScreen } from "@/components/controls";
import { SduiRoot } from "@/components/sdui";
import { fetchHome } from "@/lib/api";

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

  if (!customerZipPrefix) return <EntryScreen />;

  const result = await fetchHome(customerZipPrefix, context, search, category);

  return (
    <>
      <Controls
        customerZipPrefix={customerZipPrefix}
        context={context}
        search={search}
        category={category}
      />
      <main className="mx-auto w-full max-w-6xl px-6 py-10">
        {result.ok ? (
          <SduiRoot customerZipPrefix={customerZipPrefix} screen={result.screen} />
        ) : (
          <div className="rounded-xl border border-line bg-surface p-8">
            <h2 className="font-display text-2xl text-ink">Não foi possível montar a vitrine</h2>
            <p className="mt-3 text-muted">{result.detail}</p>
            {result.status === 422 && (
              <p className="mt-2 text-sm text-muted">
                Este CEP não existe na amostra de demonstração. Tente{" "}
                <a className="underline" href="/?customer_zip_prefix=05311&context=default">
                  05311
                </a>{" "}
                ou{" "}
                <a className="underline" href="/?customer_zip_prefix=60165&context=default">
                  60165
                </a>
                .
              </p>
            )}
          </div>
        )}
      </main>
    </>
  );
}
