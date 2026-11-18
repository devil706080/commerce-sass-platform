import type { Metadata } from "next";
import { Footer } from "@/components/Footer";
import { Header } from "@/components/Header";
import { CatalogueUnavailableError, listCategories } from "@/lib/catalogue";
import { brandStyle, resolveTenantBrand } from "@/lib/tenant";
import type { CatalogueCategory } from "@/lib/types";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "Your health, delivered", template: "%s | Store" },
  description: "Browse published health and wellness products from your trusted local store.",
};

export const dynamic = "force-dynamic";

export default async function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const brand = await resolveTenantBrand();
  let categories: CatalogueCategory[] = [];
  try { categories = await listCategories(); }
  catch (error) { if (!(error instanceof CatalogueUnavailableError)) throw error; }
  return (
    <html lang="en" style={brandStyle(brand)}>
      <body>
        <a className="skip-link" href="#main-content">Skip to content</a>
        <Header brand={brand} categories={categories} />
        <main id="main-content">{children}</main>
        <Footer brand={brand} />
      </body>
    </html>
  );
}
