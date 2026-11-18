import Link from "next/link";
import { Icon } from "@/components/Icon";
import { ProductCard } from "@/components/ProductCard";
import { CatalogueUnavailableError, listCategories, listProducts } from "@/lib/catalogue";
import { resolveTenantBrand } from "@/lib/tenant";
import type { CatalogueCategory, CatalogueProduct } from "@/lib/types";

export default async function HomePage() {
  const brand = await resolveTenantBrand();
  let products: CatalogueProduct[] = [];
  let categories: CatalogueCategory[] = [];
  let catalogueError = false;
  try {
    [products, categories] = await Promise.all([listProducts(undefined, 8), listCategories()]);
  } catch (error) {
    if (!(error instanceof CatalogueUnavailableError)) throw error;
    catalogueError = true;
  }

  return (
    <>
      <section className="hero">
        <div className="shell hero-grid">
          <div className="hero-copy">
            <p className="hero-badge"><Icon name="shield" /> Trusted tenant storefront</p>
            <h1>Everyday health, made <em>beautifully simple.</em></h1>
            <p className="hero-lead">Discover published health essentials from {brand.name}, with clear pricing and a shopping experience designed around trust.</p>
            <form className="hero-search" action="/products" role="search">
              <Icon name="search" />
              <label className="sr-only" htmlFor="hero-search">Search the catalogue</label>
              <input id="hero-search" name="q" maxLength={100} placeholder="What are you looking for today?" />
              <button type="submit">Search</button>
            </form>
            <div className="hero-trust"><span><Icon name="shield" /> Published products</span><span><Icon name="spark" /> Tenant-specific catalogue</span></div>
          </div>
          <div className="hero-visual" aria-label="Featured health collection">
            <div className="orb orb-one" /><div className="orb orb-two" />
            <div className="feature-card">
              <span className="feature-kicker">CURATED FOR YOU</span>
              <div className="feature-icon"><Icon name="bag" /></div>
              <h2>Care that fits your everyday</h2>
              <p>Explore essentials selected from the live {brand.name} catalogue.</p>
              <Link href="/products">Explore collection <Icon name="arrow" /></Link>
            </div>
            <div className="floating-note"><span>✓</span><div><strong>Clear pricing</strong><small>Direct from catalogue</small></div></div>
          </div>
        </div>
      </section>

      <section className="section shell">
        <div className="section-heading"><div><p className="eyebrow">EXPLORE YOUR WAY</p><h2>Shop by category</h2><p>Find the right care without the clutter.</p></div><Link href="/products">View all <Icon name="arrow" /></Link></div>
        {categories.length === 0 ? <div className="category-empty">Categories will appear here after this store publishes products into them.</div> : <div className="category-grid">
          {categories.slice(0, 8).map((category, index) => (
            <Link href={`/products?category=${encodeURIComponent(category.slug)}`} className={`category-card category-${(index % 4) + 1}`} key={category.id}>
              <span>{category.name.slice(0, 2).toUpperCase()}</span><div><strong>{category.name}</strong><small>{category.description || "Explore collection"}</small></div><Icon name="arrow" />
            </Link>
          ))}
        </div>}
      </section>

      <section className="section section-tint">
        <div className="shell">
          <div className="section-heading"><div><p className="eyebrow">LIVE CATALOGUE</p><h2>Featured essentials</h2><p>Published products available from this store.</p></div><Link href="/products">Browse catalogue <Icon name="arrow" /></Link></div>
          {catalogueError ? <CatalogueState title="We could not reach the catalogue" text="The store is temporarily unable to load products. Please try again shortly." /> : products.length === 0 ? <CatalogueState title="New products are on their way" text="This store has no published products yet." /> : <div className="product-grid">{products.map((product) => <ProductCard key={product.id} product={product} />)}</div>}
        </div>
      </section>

      <section className="shell trust-strip">
        <div><Icon name="shield" /><span><strong>Secure by design</strong><small>OIDC customer sign-in</small></span></div>
        <div><Icon name="spark" /><span><strong>Tenant isolated</strong><small>Dedicated catalogue boundary</small></span></div>
        <div><Icon name="bag" /><span><strong>Honest catalogue</strong><small>No fabricated availability</small></span></div>
      </section>
    </>
  );
}

function CatalogueState({ title, text }: { title: string; text: string }) {
  return <div className="catalogue-state"><div className="feature-icon"><Icon name="bag" /></div><h3>{title}</h3><p>{text}</p><Link href="/products">Try catalogue</Link></div>;
}
