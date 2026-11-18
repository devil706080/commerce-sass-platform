import type { Metadata } from "next";
import Link from "next/link";
import { Icon } from "@/components/Icon";
import { KeycloakSignIn } from "@/components/KeycloakSignIn";
import { resolveTenantBrand } from "@/lib/tenant";

export const metadata: Metadata = { title: "Sign in" };

export default async function LoginPage() {
  const brand = await resolveTenantBrand();
  return (
    <section className="login-page">
      <div className="shell login-grid">
        <div className="login-story">
          <p className="hero-badge"><Icon name="spark" /> Welcome back</p>
          <h1>Your health journey,<br/><em>all in one place.</em></h1>
          <p>Sign in securely to prepare for customer account features as they become available.</p>
          <div className="login-benefits"><span><Icon name="shield" /> Tenant-scoped identity</span><span><Icon name="spark" /> Secure PKCE login</span><span><Icon name="bag" /> One trusted account entry</span></div>
        </div>
        <div className="login-card">
          <div className="login-card-header"><span className="brand-mark">{brand.shortName}</span><div><p>SECURE CUSTOMER ACCESS</p><h2>Sign in to {brand.name}</h2></div></div>
          <p className="login-intro">Continue to the trusted identity provider. We keep credentials outside the commerce application.</p>
          <KeycloakSignIn />
          <div className="login-divider"><span>or</span></div>
          <Link href="/products" className="guest-button">Continue browsing as guest</Link>
          <p className="login-terms">By continuing, you agree to the store’s terms and privacy notice.</p>
        </div>
      </div>
    </section>
  );
}
