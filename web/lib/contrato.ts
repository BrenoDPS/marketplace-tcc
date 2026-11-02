import type { UIComponent } from "./sdui";

/**
 * Forma dos `props` de cada bloco, como o FRONT a entende (Sprint 12).
 *
 * O `satisfies` obriga esta forma a bater EXATAMENTE com os tipos de
 * `sdui.ts`: campo a mais ou a menos, em qualquer nivel, e erro de `tsc`. O
 * Vitest compara a forma com a que o backend exporta
 * (`web/tests/contrato-bff.json`, gerado por `python -m scripts.forma_contrato`).
 * Com as duas pontas, divergencia de props entre Pydantic e TS quebra o CI —
 * antes so os `type` eram comparados.
 *
 * Folha = `true`: texto, numero, lista de texto e `actions` (uniao
 * discriminada, ja conferida por `test_acoes_iguais_no_contrato_e_no_espelho`).
 */
type Folha<V> = V extends readonly (infer U)[]
  ? Folha<U>
  : V extends { type: string }
    ? true
    : V extends object
      ? Forma<V>
      : true;

type Forma<T> = { [K in keyof T]-?: Folha<NonNullable<T[K]>> };

type FormaDoContrato = { [B in UIComponent as B["type"]]: Forma<B["props"]> };

export const FORMA_PROPS = {
  category_grid: {
    categories: {
      actions: true,
      label: true,
      product_count: true,
      selected: true,
      slug: true,
    },
    sort_options: {
      actions: true,
      label: true,
      selected: true,
      value: true,
    },
    title: true,
  },
  checkout_summary: {
    freight: true,
    items: {
      line_total: true,
      product_id: true,
      quantity: true,
      title: true,
      unit_price: true,
    },
    subtotal: true,
    total: true,
  },
  content_section: {
    items: true,
    note: true,
    paragraphs: true,
    title: true,
  },
  data_table: {
    caption: true,
    columns: true,
    rows: {
      cells: true,
      emphasis: true,
    },
    title: true,
  },
  delivery_options: {
    distance_km: true,
    note: true,
    options: {
      co2_kg: true,
      description: true,
      eta_days: true,
      id: true,
      label: true,
      price: true,
      recommended: true,
      selected: true,
    },
    selected_id: true,
  },
  hero_banner: {
    cta_label: true,
    eyebrow: true,
    image_url: true,
    secondary_cta_label: true,
    subtitle: true,
    title: true,
    variant: true,
  },
  impact_banner: {
    badge: {
      explanation: {
        chargeable_weight_g: true,
        circuity: true,
        co2_kg: true,
        fe_last_mile: true,
        fe_line_haul: true,
        last_mile_km: true,
        line_haul_km: true,
        methodology_path: true,
        mode_factor: true,
        road_km: true,
        sources: true,
        straight_km: true,
        weight_g: true,
      },
      icon: true,
      impact_level: true,
      label: true,
    },
    co2_kg: true,
    distance_km: true,
    message: true,
  },
  offer_comparison: {
    note: true,
    offers: {
      chosen: true,
      co2_kg: true,
      distance_km: true,
      local: true,
      price: true,
      reason: true,
      same_region: true,
      seller_city: true,
      seller_id: true,
      seller_state: true,
    },
    title: true,
  },
  origin_map: {
    background_url: true,
    buyer: {
      chosen: true,
      label: true,
      local: true,
      x: true,
      y: true,
    },
    caption: true,
    height: true,
    origins: {
      chosen: true,
      label: true,
      local: true,
      x: true,
      y: true,
    },
    radius_100km: true,
    title: true,
    viewbox: true,
    width: true,
  },
  product_card: {
    badge: {
      explanation: {
        chargeable_weight_g: true,
        circuity: true,
        co2_kg: true,
        fe_last_mile: true,
        fe_line_haul: true,
        last_mile_km: true,
        line_haul_km: true,
        methodology_path: true,
        mode_factor: true,
        road_km: true,
        sources: true,
        straight_km: true,
        weight_g: true,
      },
      icon: true,
      impact_level: true,
      label: true,
    },
    category: true,
    co2_kg: true,
    distance_km: true,
    image_url: true,
    price: true,
    product_id: true,
    rating: true,
    review_count: true,
    seller_city: true,
    seller_state: true,
    subtitle: true,
    title: true,
  },
  product_detail: {
    badge: {
      explanation: {
        chargeable_weight_g: true,
        circuity: true,
        co2_kg: true,
        fe_last_mile: true,
        fe_line_haul: true,
        last_mile_km: true,
        line_haul_km: true,
        methodology_path: true,
        mode_factor: true,
        road_km: true,
        sources: true,
        straight_km: true,
        weight_g: true,
      },
      icon: true,
      impact_level: true,
      label: true,
    },
    category: true,
    image_url: true,
    price: true,
    product_id: true,
    rating: true,
    review_count: true,
    seller_city: true,
    seller_id: true,
    seller_state: true,
    subtitle: true,
    title: true,
    weight_g: true,
  },
  shipment_breakdown: {
    note: true,
    shipments: {
      alternatives: {
        actions: true,
        co2_kg: true,
        co2_saved_kg: true,
        distance_km: true,
        price: true,
        product_id: true,
        replaces_product_id: true,
        saved_share: true,
        seller_id: true,
        title: true,
      },
      badge: {
        explanation: {
          chargeable_weight_g: true,
          circuity: true,
          co2_kg: true,
          fe_last_mile: true,
          fe_line_haul: true,
          last_mile_km: true,
          line_haul_km: true,
          methodology_path: true,
          mode_factor: true,
          road_km: true,
          sources: true,
          straight_km: true,
          weight_g: true,
        },
        icon: true,
        impact_level: true,
        label: true,
      },
      co2_kg: true,
      co2_share: true,
      distance_km: true,
      freight: true,
      product_ids: true,
      seller_city: true,
      seller_id: true,
      seller_state: true,
      total_quantity: true,
      weight_g: true,
    },
    title: true,
  },
} satisfies FormaDoContrato;
