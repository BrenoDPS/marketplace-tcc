/**
 * Icones do redesign (02/11): SVG inline, traco de 1,75 sobre grade de 24 —
 * sem biblioteca nova (o build ja pesa ~190 KB). Desenho no estilo dos icones
 * abertos (Lucide/Feather). Todo icone e decorativo (`aria-hidden`): o nome
 * acessivel fica no texto do controle.
 */
const PATHS = {
  search: <><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></>,
  pin: <><path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21Z" /><circle cx="12" cy="9.5" r="2.5" /></>,
  bag: <><path d="M5 8h14l-1.2 12H6.2L5 8Z" /><path d="M9 8V6.5a3 3 0 0 1 6 0V8" /></>,
  x: <path d="M6 6l12 12M18 6 6 18" />,
  plus: <path d="M12 5v14M5 12h14" />,
  minus: <path d="M5 12h14" />,
  check: <path d="m5 12.5 4.5 4.5L19 7.5" />,
  leaf: <><path d="M20 4c0 9-5.5 14-11.5 14a6 6 0 0 1-3.8-1.3C6.9 11.3 11 8.2 15.5 6.6 10.8 7.4 6.7 10 4 14.6A7.8 7.8 0 0 1 3 10.5C3 6 7.2 3.7 11.4 3.4c3-.2 5.7-.6 8.6.6Z" /></>,
  truck: <><path d="M3 6h11v10H3zM14 9h4l3 3.5V16h-7" /><circle cx="7" cy="17.5" r="1.8" /><circle cx="17.5" cy="17.5" r="1.8" /></>,
  zap: <path d="M13 3 5 13.5h6L10 21l8-10.5h-6L13 3Z" />,
  star: <path d="m12 3.5 2.6 5.4 5.9.8-4.3 4.1 1 5.8L12 16.9l-5.2 2.7 1-5.8-4.3-4.1 5.9-.8L12 3.5Z" />,
  scale: <><path d="M6 8h12l1.5 12h-15L6 8Z" /><circle cx="12" cy="5.5" r="2" /></>,
  box: <><path d="m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3Z" /><path d="m4 7.5 8 4.5 8-4.5M12 12v9" /></>,
  store: <><path d="M4 9.5 5.5 4h13L20 9.5" /><path d="M4 9.5h16v.5a3 3 0 0 1-5.3 1.9 3 3 0 0 1-5.4 0A3 3 0 0 1 4 10v-.5Z" /><path d="M5.5 12.5V20h13v-7.5M10 20v-4.5h4V20" /></>,
  sparkles: <><path d="M12 3.5 13.6 9l5.4 1.6-5.4 1.6L12 17.7l-1.6-5.5L5 10.6 10.4 9 12 3.5Z" /><path d="M19 15.5l.6 1.9 1.9.6-1.9.6-.6 1.9-.6-1.9-1.9-.6 1.9-.6.6-1.9Z" /></>,
  laptop: <><rect x="4.5" y="5" width="15" height="10" rx="1.5" /><path d="M2.5 19h19" /></>,
  arrowLeft: <path d="M19 12H5m6-6-6 6 6 6" />,
  arrowRight: <path d="M5 12h14m-6-6 6 6-6 6" />,
  chevronLeft: <path d="m15 6-6 6 6 6" />,
  chevronRight: <path d="m9 6 6 6-6 6" />,
  chevronDown: <path d="m6 9 6 6 6-6" />,
  code: <path d="m8 7-5 5 5 5M16 7l5 5-5 5M13.5 4.5l-3 15" />,
  book: <><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5v-15Z" /><path d="M4 20.5A2.5 2.5 0 0 0 6.5 23H20v-5" /></>,
  chart: <><path d="M4 20V4M4 20h16" /><path d="M8 16v-4M12 16V8M16 16v-6" /></>,
  info: <><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 8h.01" /></>,
  route: <><circle cx="6" cy="18" r="2.5" /><circle cx="18" cy="6" r="2.5" /><path d="M8.5 18H16a3.5 3.5 0 0 0 0-7H8a3.5 3.5 0 0 1 0-7h7.5" /></>,
  tag: <><path d="M3.5 12.5V4h8.5l8.5 8.5-8 8-9-8Z" /><circle cx="8" cy="8.5" r="1.3" /></>,
  menu: <path d="M4 7h16M4 12h16M4 17h16" />,
  sliders: <path d="M4 7h10M18 7h2M4 17h4M12 17h8M14 4.5v5M8 14.5v5" />,
  compass: <><circle cx="12" cy="12" r="9" /><path d="m15.5 8.5-2 5-5 2 2-5 5-2Z" /></>,
  layers: <><path d="m12 3 9 5-9 5-9-5 9-5Z" /><path d="m3 13 9 5 9-5" /></>,
  globe: <><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3c2.5 2.7 3.5 5.7 3.5 9s-1 6.3-3.5 9c-2.5-2.7-3.5-5.7-3.5-9S9.5 5.7 12 3Z" /></>,
  // Categorias
  utensils: <><path d="M7 3v8M5 3v5a2 2 0 0 0 4 0V3M7 11v10" /><path d="M17 3c-1.7 0-3 2-3 5s1.3 4 3 4v9" /></>,
  bed: <><path d="M3 18V7M3 13h18v5M21 13a4 4 0 0 0-4-4h-7v4" /><circle cx="6.5" cy="10.5" r="1.5" /></>,
  dumbbell: <path d="M3 10v4M6.5 7v10M17.5 7v10M21 10v4M6.5 12h11" />,
  sofa: <><path d="M5 11V8a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v3" /><path d="M3 13a2 2 0 0 1 4 0v2h10v-2a2 2 0 0 1 4 0v5H3v-5ZM5 18v2M19 18v2" /></>,
  home: <><path d="m3 11 9-7 9 7" /><path d="M5.5 9.5V20h13V9.5M10 20v-5h4v5" /></>,
  car: <><path d="M5 16V11.5L7 7h10l2 4.5V16" /><path d="M3.5 16h17v2.5h-17zM5 11.5h14" /><circle cx="7.5" cy="14" r=".6" /><circle cx="16.5" cy="14" r=".6" /></>,
  gift: <><rect x="4" y="9" width="16" height="11" rx="1" /><path d="M3 9h18M12 9v11" /><path d="M12 9S9.5 4 7.5 5.5 9 9 12 9Zm0 0s2.5-5 4.5-3.5S15 9 12 9Z" /></>,
  watch: <><circle cx="12" cy="12" r="5" /><path d="M12 10v2l1.5 1.5M9 7.5 9.8 3h4.4L15 7.5M9 16.5l.8 4.5h4.4l.8-4.5" /></>,
  phone: <><rect x="7" y="3" width="10" height="18" rx="2" /><path d="M11 18h2" /></>,
  puzzle: <path d="M8 4h4v2a1.5 1.5 0 0 0 3 0V4h4v4h-2a1.5 1.5 0 0 0 0 3h2v9h-4v-2a1.5 1.5 0 0 0-3 0v2H8v-4H6a1.5 1.5 0 0 1 0-3h2V4Z" />,
  baby: <><circle cx="12" cy="8" r="4" /><path d="M10.5 8h.01M13.5 8h.01M5 21c.5-4 3.3-6.5 7-6.5s6.5 2.5 7 6.5" /></>,
  droplet: <path d="M12 3.5S6 10 6 14a6 6 0 0 0 12 0c0-4-6-10.5-6-10.5Z" />,
  wrench: <path d="M14.5 6.5a4 4 0 0 0 4.8 5L21 13.2 13.2 21l-1.7-1.7a4 4 0 0 0-5-4.8L3 11V3h8l3.5 3.5Z" />,
  shirt: <path d="m8 4-5 3 2 4 2-1v10h10V10l2 1 2-4-5-3a4 4 0 0 1-8 0Z" />,
  briefcase: <><rect x="3" y="7" width="18" height="13" rx="2" /><path d="M9 7V5h6v2M3 12h18" /></>,
  gamepad: <><path d="M7 8h10a4 4 0 0 1 4 4.5l-.5 3a2.5 2.5 0 0 1-4.3 1.3L14.5 15h-5l-1.7 1.8a2.5 2.5 0 0 1-4.3-1.3l-.5-3A4 4 0 0 1 7 8Z" /><path d="M8 10.5v3M6.5 12h3M15.5 11h.01M17.5 13h.01" /></>,
  headphones: <path d="M4 15v-3a8 8 0 0 1 16 0v3M4 15a2 2 0 0 1 2-2h1v7H6a2 2 0 0 1-2-2v-3Zm16 0a2 2 0 0 0-2-2h-1v7h1a2 2 0 0 0 2-2v-3Z" />,
  plug: <path d="M9 3v5M15 3v5M6 8h12v3a6 6 0 0 1-12 0V8ZM12 17v4" />,
  paw: <><circle cx="7" cy="10" r="1.6" /><circle cx="17" cy="10" r="1.6" /><circle cx="10" cy="6.5" r="1.6" /><circle cx="14" cy="6.5" r="1.6" /><path d="M12 12.5c-3 0-5 3.5-5 5.5 0 1.5 1.2 2 2.5 2 1 0 1.6-.5 2.5-.5s1.5.5 2.5.5c1.3 0 2.5-.5 2.5-2 0-2-2-5.5-5-5.5Z" /></>,
  pencil: <path d="M4 20l1-4.5L16 4.5 19.5 8 8.5 19 4 20ZM14 7l3 3" />,
  hammer: <path d="M14 6 9.5 4 6 7.5 8 9l-5 9 3 3 9-5 1.5 2L20 14.5 14 6Z" />,
  lamp: <><path d="M8 3h8l3 8H5l3-8ZM12 11v7M8 21h8" /></>,
} as const;

export type IconName = keyof typeof PATHS;

export function Icon({ name, className = "size-4", strokeWidth = 1.75 }: { name: IconName; className?: string; strokeWidth?: number }) {
  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`shrink-0 ${className}`}
    >
      {PATHS[name]}
    </svg>
  );
}

/** Slug do Olist -> icone. Prefixo cobre as familias (`fashion_*`, `livros_*`). */
const POR_CATEGORIA: [string, IconName][] = [
  ["alimentos", "utensils"], ["bebidas", "utensils"], ["la_cuisine", "utensils"],
  ["cama_mesa_banho", "bed"], ["moveis_quarto", "bed"], ["moveis_colchao", "bed"],
  ["esporte_lazer", "dumbbell"], ["fashion_esporte", "dumbbell"],
  ["moveis_sala", "sofa"], ["moveis_decoracao", "lamp"], ["moveis_", "sofa"], ["casa_conforto", "sofa"],
  ["beleza_saude", "sparkles"], ["perfumaria", "droplet"], ["fraldas_higiene", "droplet"],
  ["utilidades_domesticas", "home"], ["casa_construcao", "hammer"], ["construcao_", "hammer"],
  ["informatica", "laptop"], ["pcs", "laptop"], ["pc_gamer", "laptop"], ["tablets", "laptop"], ["eletronicos", "laptop"],
  ["automotivo", "car"], ["relogios_presentes", "watch"], ["cool_stuff", "gift"], ["artigos_de", "gift"],
  ["telefonia", "phone"], ["brinquedos", "puzzle"], ["bebes", "baby"],
  ["ferramentas_jardim", "wrench"], ["fashion_", "shirt"], ["malas_acessorios", "briefcase"],
  ["consoles_games", "gamepad"], ["audio", "headphones"], ["eletrodomesticos", "plug"], ["eletroportateis", "plug"],
  ["portateis_", "plug"], ["climatizacao", "plug"], ["pet_shop", "paw"], ["papelaria", "pencil"],
  ["livros", "book"], ["instrumentos_musicais", "headphones"], ["musica", "headphones"],
];

export function categoryIcon(slug: string | null | undefined): IconName {
  if (!slug) return "box";
  return POR_CATEGORIA.find(([prefixo]) => slug.startsWith(prefixo))?.[1] ?? "box";
}

/**
 * Tom da capa por CATEGORIA (mesma familia de cor para a mesma categoria) com
 * variacao por produto. Sem foto no Olist, a capa e o que separa um card do
 * outro na vitrine — e e decorativa, nunca carrega informacao.
 */
export function coverTone(category: string | null | undefined, productId: string) {
  const hash = (s: string) => [...s].reduce((h, c) => (h * 31 + c.charCodeAt(0)) % 3600, 7);
  // Familia de cor da categoria + deslocamento por produto (ate ±35°): cards da
  // mesma categoria lado a lado ficam parentes, nao identicos.
  const hue = ((hash(category ?? productId) / 10) + (hash(productId) % 70) - 35 + 360) % 360;
  const giro = hash(productId) % 90;
  return {
    backgroundImage: `radial-gradient(120% 90% at 85% 15%, hsl(${hue} 45% 92% / 0.9), transparent 60%), linear-gradient(${135 + giro}deg, hsl(${hue} 38% 86%), hsl(${(hue + 28) % 360} 30% 74%))`,
    color: `hsl(${hue} 30% 32%)`,
  };
}
