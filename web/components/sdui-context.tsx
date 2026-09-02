"use client";

import { useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useMemo, useState } from "react";
import type { ProductCardBlock, ScreenResponse, UIAction } from "@/lib/sdui";

/**
 * Executor de `actions`. O servidor decide o COMPORTAMENTO; aqui so existe o
 * mapa `action.type` -> efeito no cliente. Tipo desconhecido e ignorado em vez
 * de quebrar a tela (degradacao graciosa do SDUI).
 */

type RunContext = { product?: ProductCardBlock; quantity?: number };

type SduiValue = {
  customerZipPrefix: string;
  selected: ProductCardBlock | null;
  checkout: ScreenResponse | null;
  pending: boolean;
  error: string | null;
  run: (action: UIAction, ctx?: RunContext) => void;
  select: (block: ProductCardBlock | null) => void;
  closeCheckout: () => void;
};

const SduiCtx = createContext<SduiValue | null>(null);

export function useSdui(): SduiValue {
  const value = useContext(SduiCtx);
  if (!value) throw new Error("useSdui precisa estar dentro de <SduiProvider>");
  return value;
}

/** Corpo esperado por POST /api/v1/checkout/simulate (body_key: "checkout"). */
function checkoutBody(cep: string, ctx: RunContext) {
  return {
    customer_zip_prefix: cep,
    product_id: ctx.product?.props.product_id,
    quantity: ctx.quantity ?? 1,
  };
}

export function SduiProvider({
  customerZipPrefix,
  children,
}: {
  customerZipPrefix: string;
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [selected, setSelected] = useState<ProductCardBlock | null>(null);
  const [checkout, setCheckout] = useState<ScreenResponse | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(
    (action: UIAction, ctx: RunContext = {}) => {
      switch (action.type) {
        case "navigate": {
          const { path, replace } = action.payload;
          if (replace) router.replace(path);
          else router.push(path);
          return;
        }

        case "open_modal": {
          if (action.payload.modal_id === "product_detail" && ctx.product) {
            setError(null);
            setSelected(ctx.product);
          }
          return;
        }

        case "api_call": {
          const { method, path, body_key } = action.payload;
          // Hoje so existe um body_key ("checkout"). Outro valor = servidor
          // pede algo que este cliente ainda nao sabe montar.
          if (body_key !== "checkout") return;

          setPending(true);
          setError(null);
          fetch(path, {
            method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(checkoutBody(customerZipPrefix, ctx)),
          })
            .then(async (res) => {
              const body = await res.json().catch(() => null);
              if (!res.ok) {
                const detail = (body as { detail?: unknown } | null)?.detail;
                throw new Error(
                  typeof detail === "string" ? detail : `Erro HTTP ${res.status}`,
                );
              }
              // A resposta e outra ScreenResponse: o MESMO renderer desenha.
              setCheckout(body as ScreenResponse);
              setSelected(null);
            })
            .catch((err: Error) => setError(err.message))
            .finally(() => setPending(false));
          return;
        }
      }
    },
    [customerZipPrefix, router],
  );

  const value = useMemo<SduiValue>(
    () => ({
      customerZipPrefix,
      selected,
      checkout,
      pending,
      error,
      run,
      select: (block) => {
        setError(null);
        setSelected(block);
      },
      closeCheckout: () => setCheckout(null),
    }),
    [customerZipPrefix, selected, checkout, pending, error, run],
  );

  return <SduiCtx.Provider value={value}>{children}</SduiCtx.Provider>;
}
