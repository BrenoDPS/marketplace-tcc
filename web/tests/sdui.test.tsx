/**
 * Cobre as duas pecas do frontend com logica nao trivial: o executor de
 * `actions` (sdui-context) e o renderer/registry (sdui.tsx). O resto dos
 * componentes e apresentacao e nao ganha teste — YAGNI vale para teste tambem.
 */
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import { ScreenRenderer } from "@/components/sdui";
import { SduiProvider, checkoutBody, useSdui } from "@/components/sdui-context";
import { co2Label, decimal } from "@/lib/sdui";
import type { ProductCardBlock, ScreenResponse, UIComponent } from "@/lib/sdui";

const push = vi.fn();
const replace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push, replace }),
}));

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  push.mockReset();
  replace.mockReset();
});

// --- fixtures ---------------------------------------------------------------

const card = (productId: string, price = 10): ProductCardBlock => ({
  type: "product_card",
  version: 1,
  props: {
    product_id: productId,
    price,
    title: `Produto ${productId}`,
    image_url: null,
    badge: null,
  },
  actions: [
    { type: "open_modal", payload: { modal_id: "product_detail", title: null } },
    {
      type: "api_call",
      payload: {
        method: "POST",
        path: "/api/v1/checkout/simulate",
        body_key: "checkout",
      },
    },
  ],
});

const screenOf = (components: UIComponent[]): ScreenResponse => ({
  schema_version: 1,
  screen_id: "home",
  context: "default",
  components,
});

const hero = (title: string): UIComponent => ({
  type: "hero_banner",
  version: 1,
  props: { title, subtitle: null, image_url: "", cta_label: null },
  actions: [],
});

// --- ScreenRenderer ---------------------------------------------------------

describe("ScreenRenderer", () => {
  test("agrupa product_cards consecutivos numa grade so", () => {
    const { container } = render(
      <SduiProvider customerZipPrefix="05311">
        <ScreenRenderer screen={screenOf([hero("A"), card("p1"), card("p2")])} />
      </SduiProvider>,
    );
    expect(container.querySelectorAll(".grid")).toHaveLength(1);
    expect(screen.getByText("Produto p1")).toBeTruthy();
    expect(screen.getByText("Produto p2")).toBeTruthy();
  });

  test("bloco entre cards quebra a grade em duas", () => {
    const { container } = render(
      <SduiProvider customerZipPrefix="05311">
        <ScreenRenderer
          screen={screenOf([card("p1"), hero("meio"), card("p2")])}
        />
      </SduiProvider>,
    );
    expect(container.querySelectorAll(".grid")).toHaveLength(2);
  });

  test("tipo desconhecido renderiza nada em vez de quebrar a tela", () => {
    const unknown = {
      type: "widget_do_futuro",
      version: 1,
      props: {},
      actions: [],
    } as unknown as UIComponent;

    expect(() =>
      render(
        <SduiProvider customerZipPrefix="05311">
          <ScreenRenderer screen={screenOf([unknown, hero("sobrevivi")])} />
        </SduiProvider>,
      ),
    ).not.toThrow();
    // O bloco conhecido continua na tela: a degradacao e parcial, nao total.
    expect(screen.getByText("sobrevivi")).toBeTruthy();
  });
});

// --- executor de actions ----------------------------------------------------

function Probe() {
  const { run, cart, addToCart, checkoutAction, error } = useSdui();
  return (
    <div>
      <button onClick={() => run({ type: "navigate", payload: { path: "/x", replace: false } })}>
        nav
      </button>
      <button
        onClick={() => run({ type: "navigate", payload: { path: "/y", replace: true } })}
      >
        nav-replace
      </button>
      <button onClick={() => addToCart(card("p1", 25), 2)}>add</button>
      <button onClick={() => checkoutAction && run(checkoutAction)}>checkout</button>
      <span data-testid="count">{cart.length}</span>
      <span data-testid="error">{error ?? ""}</span>
    </div>
  );
}

function renderProbe() {
  return render(
    <SduiProvider customerZipPrefix="05311">
      <Probe />
    </SduiProvider>,
  );
}

describe("executor de actions", () => {
  test("navigate empurra o caminho que o servidor mandou", () => {
    renderProbe();
    fireEvent.click(screen.getByText("nav"));
    expect(push).toHaveBeenCalledWith("/x");
  });

  test("navigate com replace usa replace, nao push", () => {
    renderProbe();
    fireEvent.click(screen.getByText("nav-replace"));
    expect(replace).toHaveBeenCalledWith("/y");
    expect(push).not.toHaveBeenCalled();
  });

  test("api_call com carrinho vazio nao chega a chamar a rede", () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    renderProbe();
    // Sem itens nao ha checkoutAction guardada, e mesmo que houvesse o guard
    // do carrinho vazio impede a chamada.
    fireEvent.click(screen.getByText("checkout"));
    expect(fetchMock).not.toHaveBeenCalled();
  });

  test("api_call envia o carrinho inteiro no corpo", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => screenOf([]),
    });
    vi.stubGlobal("fetch", fetchMock);

    renderProbe();
    fireEvent.click(screen.getByText("add"));
    fireEvent.click(screen.getByText("checkout"));

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const [path, init] = fetchMock.mock.calls[0];
    expect(path).toBe("/api/v1/checkout/simulate");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({
      customer_zip_prefix: "05311",
      items: [{ product_id: "p1", quantity: 2 }],
      delivery_option: null,
    });
  });

  test("erro da API vira mensagem legivel, nao excecao", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 422,
        json: async () => ({ detail: "customer_zip_prefix desconhecido" }),
      }),
    );

    renderProbe();
    fireEvent.click(screen.getByText("add"));
    fireEvent.click(screen.getByText("checkout"));

    await waitFor(() =>
      expect(screen.getByTestId("error").textContent).toBe(
        "customer_zip_prefix desconhecido",
      ),
    );
  });
});

// --- carrinho ---------------------------------------------------------------

describe("carrinho", () => {
  test("mesmo produto adicionado duas vezes vira uma linha", () => {
    renderProbe();
    fireEvent.click(screen.getByText("add"));
    fireEvent.click(screen.getByText("add"));
    expect(screen.getByTestId("count").textContent).toBe("1");
  });

  test("checkoutBody monta o corpo do carrinho", () => {
    const body = checkoutBody(
      "05311",
      [
        { productId: "a", title: null, price: 1, quantity: 2 },
        { productId: "b", title: null, price: 3, quantity: 1 },
      ],
      { deliveryOption: "green" },
    );
    expect(body).toEqual({
      customer_zip_prefix: "05311",
      items: [
        { product_id: "a", quantity: 2 },
        { product_id: "b", quantity: 1 },
      ],
      delivery_option: "green",
    });
  });
});

// --- formatacao -------------------------------------------------------------

describe("formatacao de CO2", () => {
  test("abaixo de 10 g exibe em gramas", () => {
    expect(co2Label(0.0004184)).toBe("0,42 g");
  });

  test("acima de 10 g exibe em kg", () => {
    expect(co2Label(1.5)).toBe("1,50 kg");
  });

  test("nunca imprime um zero seco", () => {
    expect(co2Label(0.0004184)).not.toBe("0,00 kg");
  });

  test("decimal usa virgula pt-BR", () => {
    expect(decimal(1234.5, 1)).toContain(",5");
  });
});
