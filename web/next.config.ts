import type { NextConfig } from "next";

const API_BASE = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  // As `actions` do tipo `api_call` trazem caminhos absolutos da API
  // (ex.: /api/v1/checkout/simulate). O proxy deixa o fetch do browser sair
  // da mesma origem, entao o CORS do backend nao entra no caminho.
  async rewrites() {
    return [{ source: "/api/v1/:path*", destination: `${API_BASE}/api/v1/:path*` }];
  },
};

export default nextConfig;
