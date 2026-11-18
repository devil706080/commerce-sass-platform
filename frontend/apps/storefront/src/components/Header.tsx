import Link from "next/link";
import type { CatalogueCategory, TenantBrand } from "@/lib/types";
import { Icon } from "./Icon";

export function Header({ brand, categories }: { brand: TenantBrand; categories: CatalogueCategory[] }) {
  return (
    <header className="site-header">
      <div className="announcement">{brand.supportLine}</div>
      <div className="header-main shell">
        <details className="mobile-menu">
          <summary aria-label="Open navigation"><Icon name="menu" /></summary>
          <nav>{categories.map((category) => <Link key={category.id} href={`/products?category=${encodeURIComponent(category.slug)}`}>{category.name}</Link>)}</nav>
        </details>
        <Link href="/" className="brand" aria-label={`${brand.name} home`}>
          <span className="brand-mark">{brand.shortName}</span>
          <span>{brand.name}</span>
        </Link>
        <div className="delivery"><Icon name="location" /><span>Delivering locally<small>{brand.locationLabel}</small></span></div>
        <form className="header-search" action="/products" role="search">
          <label className="sr-only" htmlFor="header-search">Search products</label>
          <input id="header-search" name="q" maxLength={100} placeholder="Search medicines and health essentials" />
          <button type="submit" aria-label="Search"><Icon name="search" /></button>
        </form>
        <nav className="header-actions" aria-label="Customer actions">
          <Link href="/login" className="account-link"><Icon name="user" /><span>Account</span></Link>
          <button className="icon-button" type="button" aria-label="Wishlist unavailable until account service is enabled"><Icon name="heart" /></button>
          <button className="icon-button" type="button" aria-label="Cart unavailable until cart service is enabled"><Icon name="cart" /></button>
        </nav>
      </div>
      <nav className="category-nav" aria-label="Product categories">
        <div className="shell category-nav-inner">
          {categories.slice(0, 8).map((category) => <Link key={category.id} href={`/products?category=${encodeURIComponent(category.slug)}`}>{category.name}</Link>)}
          <Link href="/products" className="catalogue-pill">Browse all</Link>
        </div>
      </nav>
    </header>
  );
}
