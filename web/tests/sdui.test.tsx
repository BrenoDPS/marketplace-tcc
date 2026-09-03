/**
 * Cobre as duas pecas do frontend com logica nao trivial: o executor de
 * `actions` (sdui-context) e o renderer/registry (sdui.tsx). O resto dos
 * componentes e apresentacao e nao ganha teste — YAGNI vale para teste tambem.
 */
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import { ScreenRenderer } from "@/components/sdui";
import {
  CART_STORAGE_KEY,
  SduiProvider,
  checkoutBody,
  readStoredCart,
  useSdui,
} from "@/components/sdui-context";
import { co2Label, decimal, findCheckoutAction } from "@/lib/sdui";
import type { ProductCardBlock, ScreenResponse, UIComponent } from "@/lib/sdui";

const push = vi.fn();
const replace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push, replace }),
}));

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  push.mockReset();
  replace.mockReset();
  localStorage.clear();
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

/** Bloco que o servidor manda e este cliente nao conhece. */
const unknownBlock = {
  type: "widget_do_futuro",
  version: 1,
  props: {},
  actions: [],
} as unknown as UIComponent;

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
    expect(() =>
      render(
        <SduiProvider customerZipPrefix="05311">
          <ScreenRenderer screen={screenOf([unknownBlock, hero("sobrevivi")])} />
        </SduiProvider>,
      ),
    ).not.toThrow();
    // O bloco conhecido continua na tela: a degradacao e parcial, nao total.
    expect(screen.getByText("sobrevivi")).toBeTruthy();
    expect(screen.queryByText(/widget_do_futuro/)).toBeNull();
  });
});

// --- modo de inspecao -------------------------------------------------------

/** Liga a inspecao pelo proprio contexto e renderiza a tela. */
function Inspected({ screen: s }: { screen: ScreenResponse }) {
  const { inspecting, toggleInspecting } = useSdui();
  return (
    <>
      <button onClick={toggleInspecting}>toggle</button>
      <span data-testid="on">{String(inspecting)}</span>
      <ScreenRenderer screen={s} />
    </>
  );
}

function renderInspected(s: ScreenResponse) {
  return render(
    <SduiProvider customerZipPrefix="05311">
      <Inspected screen={s} />
    </SduiProvider>,
  );
}

describe("modo de inspecao", () => {
  test("comeca desligado e nao polui a tela", () => {
    renderInspected(screenOf([hero("A"), card("p1")]));
    expect(screen.getByTestId("on").textContent).toBe("false");
    expect(screen.queryByText(/hero_banner/)).toBeNull();
  });

  test("ligado, expoe o envelope de cada bloco", () => {
    const { container } = renderInspected(screenOf([hero("A"), card("p1")]));
    fireEvent.click(screen.getByText("toggle"));
    // Uma etiqueta por bloco, com `type` e `version` do envelope.
    const tags = [...container.querySelectorAll("summary")].map((s) => s.textContent);
    expect(tags).toHaveLength(2);
    expect(tags[0]).toContain("hero_banner");
    expect(tags[0]).toContain("v1");
    expect(tags[1]).toContain("product_card");
    // O product_card tem duas actions (open_modal + api_call).
    expect(tags[1]).toContain("2 action(s)");
  });

  test("ligado, mostra os metadados da ScreenResponse", () => {
    renderInspected(screenOf([hero("A"), card("p1")]));
    fireEvent.click(screen.getByText("toggle"));
    expect(screen.getByText("ScreenResponse")).toBeTruthy();
    expect(screen.getByText("home")).toBeTruthy(); // screen_id
    expect(screen.getByText("hero_banner → product_card")).toBeTruthy();
  });

  test("o JSON exposto e o bloco inteiro que veio do servidor", () => {
    const { container } = renderInspected(screenOf([card("p1", 42)]));
    fireEvent.click(screen.getByText("toggle"));
    const json = JSON.parse(container.querySelector("pre")!.textContent!);
    expect(json).toEqual(card("p1", 42));
  });

  test("bloco sem renderer fica VISIVEL na inspecao", () => {
    // Fora da inspecao ele some em silencio; o modo existe justamente para
    // mostrar que o servidor mandou algo que este cliente nao conhece.
    renderInspected(screenOf([unknownBlock]));
    fireEvent.click(screen.getByText("toggle"));
    expect(screen.getByText(/sem renderer/)).toBeTruthy();
    expect(screen.getByText(/não tem componente no/)).toBeTruthy();
  });

  test("desligar devolve a tela ao normal", () => {
    renderInspected(screenOf([hero("A")]));
    fireEvent.click(screen.getByText("toggle"));
    fireEvent.click(screen.getByText("toggle"));
    expect(screen.queryByText("ScreenResponse")).toBeNull();
    expect(screen.getByText("A")).toBeTruthy();
  });
});

// --- executor de actions ----------------------------------------------------

function Probe() {
  const { run, cart, addToCart, swapInCart, checkoutAction, error } = useSdui();
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
      <button
        onClick={() => {
          const updated = swapInCart("p1", {
            productId: "p2",
            title: "Alternativa",
            price: 19,
          });
          if (checkoutAction) run(checkoutAction, { cart: updated });
        }}
      >
        swap
      </button>
      <span data-testid="count">{cart.length}</span>
      <span data-testid="ids">{cart.map((e) => `${e.productId}x${e.quantity}`).join(",")}</span>
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

  test("trocar mantem a quantidade do item substituido", () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => screenOf([]) }));
    renderProbe();
    fireEvent.click(screen.getByText("add")); // p1, quantidade 2
    fireEvent.click(screen.getByText("swap"));
    expect(screen.getByTestId("ids").textContent).toBe("p2x2");
  });

  test("re-simulacao apos a troca envia o carrinho NOVO", async () => {
    // Regressao do closure: `setCart` nao atualiza o valor capturado por `run`,
    // entao sem o override o servidor receberia o carrinho antigo (p1) e
    // devolveria uma tela que contradiz o que esta na frente do usuario.
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => screenOf([]) });
    vi.stubGlobal("fetch", fetchMock);

    renderProbe();
    fireEvent.click(screen.getByText("add"));
    fireEvent.click(screen.getByText("swap"));

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const body = JSON.parse(fetchMock.mock.calls.at(-1)![1].body);
    expect(body.items).toEqual([{ product_id: "p2", quantity: 2 }]);
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

// --- persistencia do carrinho -----------------------------------------------

describe("persistencia do carrinho", () => {
  const stored = (items: unknown) =>
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(items));

  test("grava no storage quando o carrinho muda", async () => {
    renderProbe();
    fireEvent.click(screen.getByText("add"));
    await waitFor(() =>
      expect(JSON.parse(localStorage.getItem(CART_STORAGE_KEY)!)).toEqual([
        { productId: "p1", title: "Produto p1", price: 25, quantity: 2 },
      ]),
    );
  });

  test("restaura o carrinho ao montar", async () => {
    stored([{ productId: "p9", title: "Salvo", price: 10, quantity: 3 }]);
    renderProbe();
    await waitFor(() => expect(screen.getByTestId("ids").textContent).toBe("p9x3"));
  });

  test("montar nunca grava um carrinho vazio por cima do restaurado", async () => {
    // Regressao da ordem dos efeitos: com `hydrated` como ref, a escrita
    // rodaria no commit da montagem, ainda com `cart` vazio no closure, e
    // gravaria "[]". O render seguinte corrigiria o valor — por isso checar so
    // o estado final NAO pegaria o bug. O que pega e observar as escritas: quem
    // fechar a aba naquele instante perde o carrinho.
    stored([{ productId: "p9", title: "Salvo", price: 10, quantity: 3 }]);
    const setItem = vi.spyOn(Storage.prototype, "setItem");

    renderProbe();
    await waitFor(() => expect(screen.getByTestId("ids").textContent).toBe("p9x3"));

    const wroteEmpty = setItem.mock.calls.some(
      ([key, value]) => key === CART_STORAGE_KEY && value === "[]",
    );
    expect(wroteEmpty).toBe(false);
  });

  test("descarta itens com formato invalido em vez de confiar no JSON", () => {
    stored([
      { productId: "ok", title: null, price: 10, quantity: 1 },
      { productId: "", title: null, price: 10, quantity: 1 }, // id vazio
      { title: "sem id", price: 10, quantity: 1 }, // formato antigo
      { productId: "z", title: null, price: 10, quantity: 0 }, // backend exige >= 1
      { productId: "w", title: null, price: "10", quantity: 1 }, // preco string
      "lixo",
    ]);
    expect(readStoredCart().map((e) => e.productId)).toEqual(["ok"]);
  });

  test("JSON corrompido nao derruba a aplicacao", () => {
    localStorage.setItem(CART_STORAGE_KEY, "{isso nao e json");
    expect(readStoredCart()).toEqual([]);
  });

  test("storage indisponivel (aba anonima) nao derruba a aplicacao", () => {
    vi.stubGlobal("localStorage", {
      getItem: () => {
        throw new Error("acesso negado");
      },
      setItem: () => {
        throw new Error("acesso negado");
      },
    });
    expect(readStoredCart()).toEqual([]);
    expect(() => renderProbe()).not.toThrow();
  });

  test("carrinho restaurado consegue fechar a compra sem reabrir um produto", async () => {
    // A `checkoutAction` nao e persistida de proposito; ela vem da tela.
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => screenOf([]) });
    vi.stubGlobal("fetch", fetchMock);
    stored([{ productId: "p9", title: "Salvo", price: 10, quantity: 1 }]);

    render(
      <SduiProvider
        customerZipPrefix="05311"
        checkoutAction={findCheckoutAction(screenOf([card("p1")]))}
      >
        <Probe />
      </SduiProvider>,
    );

    await waitFor(() => expect(screen.getByTestId("ids").textContent).toBe("p9x1"));
    fireEvent.click(screen.getByText("checkout"));

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    expect(JSON.parse(fetchMock.mock.calls[0][1].body).items).toEqual([
      { product_id: "p9", quantity: 1 },
    ]);
  });
});

describe("findCheckoutAction", () => {
  test("acha a api_call de checkout em qualquer bloco", () => {
    expect(findCheckoutAction(screenOf([hero("A"), card("p1")]))).toEqual({
      type: "api_call",
      payload: {
        method: "POST",
        path: "/api/v1/checkout/simulate",
        body_key: "checkout",
      },
    });
  });

  test("devolve null quando a tela nao tem essa acao", () => {
    expect(findCheckoutAction(screenOf([hero("A")]))).toBeNull();
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
