import "server-only";
import { headers } from "next/headers";
import { notFound } from "next/navigation";
import type { TenantBrand } from "./types";

type ResolvedTenant = {
  tenant_id: string;
  hostname: string;
  display_name: string;
  tenant_status: "PENDING" | "PROVISIONING" | "ACTIVE";
  domain_status: "VERIFIED";
};

function initials(name: string): string {
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join("").toUpperCase() || "ST";
}

export async function resolveTenantBrand(): Promise<TenantBrand> {
  const headerStore = await headers();
  const forwarded = headerStore.get("x-forwarded-host");
  const host = (forwarded ?? headerStore.get("host") ?? "").split(",", 1)[0].trim().split(":", 1)[0].toLowerCase();
  if (!host || !/^[a-z0-9.-]+$/i.test(host)) throw new Error("Invalid storefront hostname");
  const controlPlane = process.env.CONTROL_PLANE_INTERNAL_URL?.replace(/\/$/, "");
  if (!controlPlane) throw new Error("Tenant resolution is not configured");
  const response = await fetch(`${controlPlane}/_local/tenant`, { headers: { "X-Forwarded-Host": host }, cache: "no-store" });
  if (response.status === 404) notFound();
  if (!response.ok) throw new Error("Tenant resolution is temporarily unavailable");
  const tenant = await response.json() as ResolvedTenant;
  if (tenant.hostname !== host || tenant.domain_status !== "VERIFIED") throw new Error("Tenant domain resolution failed");
  return {
    name: tenant.display_name,
    shortName: initials(tenant.display_name),
    locationLabel: "Local delivery",
    supportLine: "Trusted commerce · Secure tenant storefront",
    primary: "#176e8c",
    primaryDark: "#104c67",
    accent: "#12b889",
  };
}

export function brandStyle(brand: TenantBrand): React.CSSProperties {
  return { "--brand": brand.primary, "--brand-dark": brand.primaryDark, "--accent": brand.accent } as React.CSSProperties;
}
