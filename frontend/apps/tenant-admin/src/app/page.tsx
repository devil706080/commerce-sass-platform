import { headers } from "next/headers";
import { TenantAdminApp } from "@/features/tenant/TenantAdminApp";
import { TenantBrand } from "@/features/tenant/TenantBrandProvider";

type TenantContextResponse = {
  tenant_id: string;
  hostname: string;
  display_name: string;
  fallback_initials: string;
  theme_key: string;
  palette: TenantBrand["palette"];
};

async function resolveTenantBrand(): Promise<TenantBrand> {
  const requestHeaders = await headers();
  const host = requestHeaders.get("host");
  const controlPlane = process.env.CONTROL_PLANE_INTERNAL_URL;
  if (!host || !controlPlane) throw new Error("Tenant routing is unavailable");
  const response = await fetch(`${controlPlane}/_local/tenant-admin`, {
    headers: { "X-Forwarded-Host": host },
    cache: "no-store",
  });
  if (!response.ok) throw new Error("Tenant admin domain is unavailable");
  const context = await response.json() as TenantContextResponse;
  return {
    tenantId: context.tenant_id,
    hostname: context.hostname,
    displayName: context.display_name,
    fallbackInitials: context.fallback_initials,
    themeKey: context.theme_key,
    palette: context.palette,
  };
}

export default async function Page() {
  try {
    return <TenantAdminApp brand={await resolveTenantBrand()} />;
  } catch {
    return <main className="tenant-unavailable"><section><p className="eyebrow">TENANT ADMIN</p><h1>This admin domain is unavailable</h1><p>Use an active tenant’s verified Tenant Admin hostname. Unknown, unverified, and inactive domains are blocked.</p></section></main>;
  }
}
