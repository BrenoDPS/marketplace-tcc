/** Acesso ao FastAPI. Usado apenas em Server Components / rotas do servidor. */

import type { ScreenResponse } from "./sdui";

const API_BASE = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";

export type ScreenResult =
  | { ok: true; screen: ScreenResponse }
  | { ok: false; status: number; detail: string };

/** FastAPI devolve `detail` como string (erros nossos) ou array (validacao Pydantic). */
function readDetail(body: unknown, fallback: string): string {
  if (typeof body !== "object" || body === null) return fallback;
  const detail = (body as { detail?: unknown }).detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const first = detail[0] as { msg?: unknown } | undefined;
    if (first && typeof first.msg === "string") return first.msg;
  }
  return fallback;
}

async function readScreen(res: Response): Promise<ScreenResult> {
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    return {
      ok: false,
      status: res.status,
      detail: readDetail(body, `Erro HTTP ${res.status}`),
    };
  }
  return { ok: true, screen: body as ScreenResponse };
}

export async function fetchHome(
  customerZipPrefix: string,
  context: string,
): Promise<ScreenResult> {
  const query = new URLSearchParams({
    customer_zip_prefix: customerZipPrefix,
    context,
  });
  try {
    // Dados dependem do CEP e mudam com o ETL: sem cache entre requisicoes.
    const res = await fetch(`${API_BASE}/api/v1/home?${query}`, { cache: "no-store" });
    return await readScreen(res);
  } catch {
    return {
      ok: false,
      status: 0,
      detail: "API indisponível. Suba o backend com `uvicorn src.main:app --reload`.",
    };
  }
}
