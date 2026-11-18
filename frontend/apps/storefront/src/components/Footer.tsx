import Link from "next/link";
import type { TenantBrand } from "@/lib/types";
import { Icon } from "./Icon";

export function Footer({ brand }: { brand: TenantBrand }) {
  return (
    <footer className="site-footer">
      <div className="shell footer-grid">
        <div><div className="brand footer-brand"><span className="brand-mark">{brand.shortName}</span><span>{brand.name}</span></div><p>A tenant-specific digital storefront powered by Commerce Cloud.</p></div>
        <div><h2>Shop</h2><Link href="/products">All products</Link><Link href="/products?q=wellness">Wellness</Link><Link href="/products?q=care">Personal care</Link></div>
        <div><h2>Trust</h2><span><Icon name="shield" /> Secure sign-in</span><span>Published catalogue only</span><span>Transparent pricing</span></div>
      </div>
      <div className="shell footer-bottom"><span>© {new Date().getFullYear()} {brand.name}</span><span>Privacy · Terms · Accessibility</span></div>
    </footer>
  );
}
