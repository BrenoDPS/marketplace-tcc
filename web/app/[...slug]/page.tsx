/**
 * O servidor pode mandar `navigate` para caminhos que este cliente ainda nao
 * implementa (ex.: /explore, /categories/electronics vindos do hero). Em vez de
 * um 404 seco no meio da demo, a rota se assume incompleta — que e exatamente o
 * ponto de atencao do SDUI: o servidor referencia telas que o app pode nao ter.
 */
export default async function NotBuiltYet({ params }: PageProps<"/[...slug]">) {
  const { slug } = await params;
  const path = `/${slug.join("/")}`;

  return (
    <main className="mx-auto flex min-h-dvh w-full max-w-xl flex-col justify-center px-6">
      <p className="text-[11px] uppercase tracking-[0.2em] text-muted">Rota não implementada</p>
      <h1 className="mt-4 font-display text-3xl text-ink">
        O servidor pediu <code className="text-signal">{path}</code>
      </h1>
      <p className="mt-4 text-muted">
        Esta tela ainda não existe no cliente. A ação <code>navigate</code> foi executada
        corretamente — falta o destino.
      </p>
      <a
        href="/"
        className="mt-8 w-fit rounded-full bg-ink px-5 py-2.5 text-sm font-medium text-paper"
      >
        Voltar à vitrine
      </a>
    </main>
  );
}
