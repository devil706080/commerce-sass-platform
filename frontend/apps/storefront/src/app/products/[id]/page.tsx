import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Icon } from "@/components/Icon";
import { formatMoney, getProduct } from "@/lib/catalogue";

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  try { const product = await getProduct((await params).id); return { title: product.name, description: product.description || "Published product details" }; }
  catch { return { title: "Product" }; }
}

export default async function ProductDetailPage({ params }: { params: Promise<{ id: string }> }) {
  let product;
  try { product = await getProduct((await params).id); }
  catch (error) { if (error instanceof Error && error.message === "Product not found") notFound(); throw error; }
  const initials = product.name.split(/\s+/).slice(0, 2).map((word) => word[0]).join("").toUpperCase();
  return (
    <div className="product-page shell">
      <nav className="breadcrumbs" aria-label="Breadcrumb"><Link href="/">Home</Link><span>/</span><Link href="/products">Catalogue</Link><span>/</span><span>{product.name}</span></nav>
      <div className="product-detail">
        <div className="product-detail-art"><span>{initials}</span><small>Product imagery will come from the public media contract</small></div>
        <div className="product-detail-copy">
          <p className="eyebrow">PUBLISHED PRODUCT · {product.sku}</p>
          <h1>{product.name}</h1>
          <p className="detail-description">{product.description || "Additional product information has not been published yet."}</p>
          <div className="detail-price"><strong>{formatMoney(product.price_cents)}</strong><span>Inclusive of applicable taxes</span></div>
          <div className="notice"><Icon name="shield" /><p><strong>Catalogue information</strong><span>Availability and purchase actions will be enabled after the Inventory and Cart services are connected.</span></p></div>
          <div className="detail-actions"><Link href="/products" className="button button-primary">Continue shopping</Link><Link href="/login" className="button button-secondary"><Icon name="user" /> Sign in</Link></div>
        </div>
      </div>
    </div>
  );
}
