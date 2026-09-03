"use client";

import { useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useMemo, useState } from "react";
import type { ProductCardBlock, ScreenResponse, UIAction } from "@/lib/sdui";

/**
 * Executor de `actions`. O servidor decide o COMPORTAMENTO; aqui so existe o
 * mapa `action.type` -> efeito no cliente. Tipo desconhecido e ignorado em vez
 * de quebrar a tela (degradacao graciosa do SDUI).
 */

/**
 * O carrinho e estado do cliente por natureza, entao `api_call` de checkout
 * envia o carrinho inteiro. `deliveryOption` e o unico extra que a acao do
 * bloco `delivery_options` precisa passar.
 */
/**
 * `cart` sobrescreve o estado ao montar o corpo. Existe para a troca por
 * vendedor mais proximo: `setCart` nao atualiza o valor que `run` capturou no
 * closure, entao quem troca passa a lista nova explicitamente.
 */
type RunContext = {
  product?: ProductCardBlock;
  deliveryOption?: string;
  cart?: CartEntry[];
};

export type CartEntry = {
  productId: string;
  title: string | null;
  price: number;
  quantity: number;
};

type SduiValue = {
  customerZipPrefix: string;
  selected: ProductCardBlock | null;
  checkout: ScreenResponse | null;
  cart: CartEntry[];
  cartOpen: boolean;
  /**
   * A `api_call` de checkout vem do `product_card`. Guardamos a do item
   * adicionado para o carrinho poder fechar o pedido: quem manda no COMO
   * continua sendo o servidor, o cliente so lembra o que ele disse.
   */
  checkoutAction: UIAction | null;
  pending: boolean;
  error: string | null;
  run: (action: UIAction, ctx?: RunContext) => void;
  select: (block: ProductCardBlock | null) => void;
  addToCart: (block: ProductCardBlock, quantity: number) => void;
  setQuantity: (productId: string, quantity: number) => void;
  removeFromCart: (productId: string) => void;
  /** Troca um item pelo substituto sugerido e devolve o carrinho ja novo. */
  swapInCart: (replacesProductId: string, entry: Omit<CartEntry, "quantity">) => CartEntry[];
  openCart: (open: boolean) => void;
  closeCheckout: () => void;
};

const SduiCtx = createContext<SduiValue | null>(null);

export function useSdui(): SduiValue {
  const value = useContext(SduiCtx);
  if (!value) throw new Error("useSdui precisa estar dentro de <SduiProvider>");
  return value;
}

/** Corpo esperado por POST /api/v1/checkout/simulate (body_key: "checkout"). */
export function checkoutBody(cep: string, cart: CartEntry[], ctx: RunContext = {}) {
  return {
    customer_zip_prefix: cep,
    items: cart.map((entry) => ({
      product_id: entry.productId,
      quantity: entry.quantity,
    })),
    delivery_option: ctx.deliveryOption ?? null,
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
  const [cart, setCart] = useState<CartEntry[]>([]);
  const [cartOpen, setCartOpen] = useState(false);
  const [checkoutAction, setCheckoutAction] = useState<UIAction | null>(null);
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
          const items = ctx.cart ?? cart;
          // Carrinho vazio: o backend recusaria com 422 e o usuario veria um
          // erro tecnico no lugar de "seu carrinho esta vazio".
          if (items.length === 0) return;

          setPending(true);
          setError(null);
          fetch(path, {
            method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(checkoutBody(customerZipPrefix, items, ctx)),
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
              setCartOpen(false);
            })
            .catch((err: Error) => setError(err.message))
            .finally(() => setPending(false));
          return;
        }
      }
    },
    [cart, customerZipPrefix, router],
  );

  const value = useMemo<SduiValue>(
    () => ({
      customerZipPrefix,
      selected,
      checkout,
      cart,
      cartOpen,
      checkoutAction,
      pending,
      error,
      run,
      select: (block) => {
        setError(null);
        setSelected(block);
      },
      addToCart: (block, quantity) => {
        const checkout = block.actions.find((a) => a.type === "api_call");
        if (checkout) setCheckoutAction(checkout);
        setCart((current) => {
          // Mesmo produto adicionado de novo soma na linha existente, em vez
          // de criar uma segunda linha do mesmo item.
          const found = current.find((e) => e.productId === block.props.product_id);
          if (found) {
            return current.map((e) =>
              e === found ? { ...e, quantity: e.quantity + quantity } : e,
            );
          }
          return [
            ...current,
            {
              productId: block.props.product_id,
              title: block.props.title,
              price: block.props.price,
              quantity,
            },
          ];
        });
      },
      setQuantity: (productId, quantity) =>
        setCart((current) =>
          current.map((e) =>
            e.productId === productId ? { ...e, quantity: Math.max(1, quantity) } : e,
          ),
        ),
      removeFromCart: (productId) =>
        setCart((current) => current.filter((e) => e.productId !== productId)),
      swapInCart: (replacesProductId, entry) => {
        // A quantidade acompanha a troca: quem tinha 2 unidades continua com 2.
        const updated = cart.map((e) =>
          e.productId === replacesProductId ? { ...entry, quantity: e.quantity } : e,
        );
        setCart(updated);
        return updated;
      },
      openCart: (open) => {
        setError(null);
        setCartOpen(open);
      },
      closeCheckout: () => setCheckout(null),
    }),
    [
      customerZipPrefix,
      selected,
      checkout,
      cart,
      cartOpen,
      checkoutAction,
      pending,
      error,
      run,
    ],
  );

  return <SduiCtx.Provider value={value}>{children}</SduiCtx.Provider>;
}
