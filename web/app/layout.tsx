import type { Metadata } from "next";
// Fontes self-hosted (subset latino, so os pesos em uso). Nao usamos
// `next/font/google` porque fonts.googleapis.com/gstatic.com estao bloqueados
// nesta rede e o build falha ao busca-las.
import "@fontsource/fraunces/latin-400.css";
import "@fontsource/inter/latin-400.css";
import "@fontsource/inter/latin-500.css";
import "@fontsource/inter/latin-600.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "Olist SDUI Marketplace",
  description:
    "Marketplace contextual adaptativo com Server-Driven UI e selo de logística verde.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="pt-BR" className="h-full antialiased">
      <body className="min-h-full flex flex-col font-sans">{children}</body>
    </html>
  );
}
