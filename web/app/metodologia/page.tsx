import { InfoScreen } from "@/components/info-screen";

const first = (value: string | string[] | undefined) =>
  Array.isArray(value) ? value[0] : value;

/** Metodologia (Sprint 16, V7): o texto e escrito pelo servidor a partir das constantes do motor de CO2. */
export default async function MetodologiaPage({ searchParams }: PageProps<"/metodologia">) {
  const params = await searchParams;
  return <InfoScreen endpoint="methodology" customerZipPrefix={first(params.customer_zip_prefix)} />;
}
