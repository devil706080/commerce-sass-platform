import Link from "next/link";
import { formatMoney } from "@/lib/catalogue";
import type { CatalogueProduct } from "@/lib/types";
import { Icon } from "./Icon";

function initials(value: string): string {
  return value.split(/\s+/).slice(0, 2).map((word) => word[0]).join("").toUpperCase();
}

export function ProductCard({ product }: { product: CatalogueProduct }) {
  return (
    <article className="product-card">
      <Link href={`/products/${product.id}`} className="product-art" aria-label={`View ${product.name}`}>
        <span>{initials(product.name)}</span>
        <small>Health essential</small>
      </Link>
      <div className="product-content">
        <p className="eyebrow">Verified catalogue</p>
        <h3><Link href={`/products/${product.id}`}>{product.name}</Link></h3>
        <p className="product-description">{product.description || "Product information available in the full details."}</p>
        <div className="product-bottom">
          <div><strong>{formatMoney(product.price_cents)}</strong><small>Inclusive of taxes</small></div>
          <Link href={`/products/${product.id}`} className="round-action" aria-label={`View ${product.name}`}><Icon name="arrow" /></Link>
        </div>
      </div>
    </article>
  );
}
