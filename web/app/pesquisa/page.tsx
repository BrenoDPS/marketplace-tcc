import { InfoScreen } from "@/components/info-screen";

const first = (value: string | string[] | undefined) =>
  Array.isArray(value) ? value[0] : value;

/** Painel da pesquisa (Sprint 16, V8): as tabelas de docs/resultados/, montadas pelo servidor. */
export default async function PesquisaPage({ searchParams }: PageProps<"/pesquisa">) {
  const params = await searchParams;
  return <InfoScreen endpoint="research" customerZipPrefix={first(params.customer_zip_prefix)} wide />;
}
