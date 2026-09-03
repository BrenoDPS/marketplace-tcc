/**
 * Espelho TypeScript do contrato SDUI (`src/schemas/sdui.py`, schema_version 1).
 *
 * Mantido a mao de proposito: o contrato tem 4 blocos e 3 acoes, e cada campo
 * aqui corresponde 1:1 a um campo Pydantic. Se o backend ganhar um bloco novo,
 * adicione o tipo aqui e registre-o no `REGISTRY` de components/sdui.tsx.
 */

// --- Acoes -----------------------------------------------------------------

export type NavigateAction = {
  type: "navigate";
  payload: { path: string; replace: boolean };
};

export type ApiCallAction = {
  type: "api_call";
  payload: {
    method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
    path: string;
    body_key: string | null;
  };
};

export type OpenModalAction = {
  type: "open_modal";
  payload: { modal_id: string; title: string | null };
};

export type UIAction = NavigateAction | ApiCallAction | OpenModalAction;

// --- Props -----------------------------------------------------------------

export type SustainabilityProps = {
  label: string;
  impact_level: "green" | "neutral";
  icon: string | null;
};

// --- Blocos ----------------------------------------------------------------

type Envelope<T extends string, P> = {
  type: T;
  version: number;
  props: P;
  actions: UIAction[];
};

export type HeroBannerBlock = Envelope<
  "hero_banner",
  {
    title: string;
    subtitle: string | null;
    image_url: string;
    /** Rotulo do botao da primeira action. O servidor decide o texto. */
    cta_label: string | null;
  }
>;

export type CategoryItem = {
  slug: string;
  label: string;
  product_count: number;
  selected: boolean;
  actions: UIAction[];
};

export type CategoryGridBlock = Envelope<
  "category_grid",
  { title: string | null; categories: CategoryItem[] }
>;

export type ProductCardBlock = Envelope<
  "product_card",
  {
    product_id: string;
    price: number;
    title: string | null;
    image_url: string | null;
    badge: SustainabilityProps | null;
  }
>;

export type CartLine = {
  product_id: string;
  title: string | null;
  quantity: number;
  unit_price: number;
  line_total: number;
};

export type CheckoutSummaryBlock = Envelope<
  "checkout_summary",
  { items: CartLine[]; subtotal: number; freight: number; total: number }
>;

export type Shipment = {
  seller_id: string;
  product_ids: string[];
  total_quantity: number;
  weight_g: number | null;
  distance_km: number | null;
  freight: number;
  co2_kg: number | null;
  co2_share: number | null;
  badge: SustainabilityProps | null;
};

export type ShipmentBreakdownBlock = Envelope<
  "shipment_breakdown",
  { title: string | null; shipments: Shipment[]; note: string | null }
>;

export type ImpactBannerBlock = Envelope<
  "impact_banner",
  {
    distance_km: number | null;
    co2_kg: number | null;
    badge: SustainabilityProps | null;
    message: string;
  }
>;

export type DeliveryOption = {
  id: string;
  label: string;
  description: string | null;
  eta_days: number;
  price: number;
  co2_kg: number | null;
  recommended: boolean;
  selected: boolean;
};

export type DeliveryOptionsBlock = Envelope<
  "delivery_options",
  {
    distance_km: number | null;
    selected_id: string;
    options: DeliveryOption[];
    note: string | null;
  }
>;

export type UIComponent =
  | HeroBannerBlock
  | CategoryGridBlock
  | ProductCardBlock
  | CheckoutSummaryBlock
  | DeliveryOptionsBlock
  | ShipmentBreakdownBlock
  | ImpactBannerBlock;

export type ScreenResponse = {
  schema_version: number;
  screen_id: string;
  context: string;
  components: UIComponent[];
};

// --- Constantes de demo ----------------------------------------------------

export const CONTEXTS = [
  { value: "default", label: "Padrão" },
  { value: "electronics_expert", label: "Eletrônicos" },
  { value: "beauty_lover", label: "Beleza" },
  { value: "conscious_buyer", label: "Consciente" },
] as const;

/** Pares documentados no README: um perto dos sellers da amostra, outro longe. */
export const DEMO_ZIPS = [
  { value: "05311", label: "São Paulo · SP", hint: "vendedores próximos" },
  { value: "60165", label: "Fortaleza · CE", hint: "vendedores distantes" },
] as const;

export const brl = (value: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value);

export const decimal = (value: number, digits: number) =>
  new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);

/**
 * A amostra Olist tem pesos baixos: a 7 km a emissao fica na ordem de 0,0004 kg
 * e "0,00 kg" apagaria justamente o numero que sustenta o trabalho. Abaixo de
 * 10 g exibimos em gramas.
 */
export const co2Label = (kg: number) =>
  kg >= 0.01 ? `${decimal(kg, 2)} kg` : `${decimal(kg * 1000, 2)} g`;
