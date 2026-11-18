import type { Metadata } from "next";
import Link from "next/link";
import { Icon } from "@/components/Icon";
import { ProductCard } from "@/components/ProductCard";
import { CatalogueUnavailableError, listProducts } from "@/lib/catalogue";
import { resolveTenantBrand } from "@/lib/tenant";
import type { CatalogueProduct } from "@/lib/types";

export const metadata: Metadata = { title: "Catalogue" };

export default async function ProductsPage({ searchParams }: { searchParams: Promise<{ q?: string; category?: string }> }) {
  const brand = await resolveTenantBrand();
  const { q, category } = await searchParams;
  const search = typeof q === "string" ? q.trim().slice(0, 100) : "";
  const categorySlug = typeof category === "string" && /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(category) ? category : undefined;
  let products: CatalogueProduct[] = [];
  let unavailable = false;
  try { products = await listProducts(search || undefined, 48, categorySlug); }
  catch (error) { if (!(error instanceof CatalogueUnavailableError)) throw error; unavailable = true; }

  return (
    <div className="catalogue-page shell">
      <nav className="breadcrumbs" aria-label="Breadcrumb"><Link href="/">Home</Link><span>/</span><span>Catalogue</span></nav>
          <div className="catalogue-header"><div><p className="eyebrow">{brand.name.toUpperCase()}</p><h1>{search ? `Results for “${search}”` : categorySlug ? "Category collection" : "Explore our catalogue"}</h1><p>{search || categorySlug ? `${products.length} published product${products.length === 1 ? "" : "s"} found.` : "Browse all products currently published by this store."}</p></div></div>
      <div className="catalogue-toolbar">
        <form action="/products" role="search"><Icon name="search" /><label className="sr-only" htmlFor="catalogue-search">Search catalogue</label><input id="catalogue-search" name="q" defaultValue={search} maxLength={100} placeholder="Search by product name or description" /><button type="submit">Search</button></form>
        {search && <Link className="clear-search" href="/products">Clear search</Link>}
      </div>
      {unavailable ? <EmptyState title="Catalogue temporarily unavailable" text="Please refresh in a moment." /> : products.length === 0 ? <EmptyState title="No products found" text="Try a different search or browse the full catalogue." /> : <div className="product-grid catalogue-products">{products.map((product) => <ProductCard key={product.id} product={product} />)}</div>}
    </div>
  );
}

function EmptyState({ title, text }: { title: string; text: string }) { return <div className="catalogue-state"><div className="feature-icon"><Icon name="search" /></div><h2>{title}</h2><p>{text}</p><Link href="/products">View all products</Link></div>; }
