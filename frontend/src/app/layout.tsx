import type { Metadata } from "next";

import { themeInitScript } from "@/components/theme";

import "./globals.css";

export const metadata: Metadata = {
  title: "Sistema Prefeitura",
  description:
    "Automação de download de documentos fiscais com certificado digital (NFS-e Nacional e São Paulo)",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body>{children}</body>
    </html>
  );
}
