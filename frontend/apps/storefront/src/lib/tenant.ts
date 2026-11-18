import "server-only";
import { headers } from "next/headers";
import type { TenantBrand } from "./types";

const HEX = /^#[0-9a-f]{6}$/i;
const HOST = /^[a-z0-9.-]+$/i;

function text(value: unknown, field: string, max = 80): string {
  if (typeof value !== "string" || value.trim().length === 0 || value.length > max) {
    throw new Error(`Invalid storefront tenant configuration: ${field}`);
  }
  return value.trim();
}

function color(value: unknown, field: string): string {
  const parsed = text(value, field, 7);
  if (!HEX.test(parsed)) throw new Error(`Invalid storefront tenant configuration: ${field}`);
  return parsed;
}

function parseBrand(value: unknown): TenantBrand {
  if (!value || typeof value !== "object") throw new Error("Invalid storefront tenant configuration");
  const candidate = value as Record<string, unknown>;
  return {
    name: text(candidate.name, "name"),
    shortName: text(candidate.shortName, "shortName", 3).toUpperCase(),
    locationLabel: text(candidate.locationLabel, "locationLabel"),
    supportLine: text(candidate.supportLine, "supportLine", 120),
    primary: color(candidate.primary, "primary"),
    primaryDark: color(candidate.primaryDark, "primaryDark"),
    accent: color(candidate.accent, "accent"),
  };
}

function loadTenantMap(): Record<string, TenantBrand> {
  const raw = process.env.STOREFRONT_TENANT_CONFIG;
  if (!raw) throw new Error("STOREFRONT_TENANT_CONFIG is required");
  const source = JSON.parse(raw) as unknown;
  if (!source || typeof source !== "object" || Array.isArray(source)) {
    throw new Error("STOREFRONT_TENANT_CONFIG must be a host map");
  }
  return Object.fromEntries(
    Object.entries(source).map(([host, value]) => {
      const normalized = host.trim().toLowerCase();
      if (!HOST.test(normalized)) throw new Error("Invalid storefront hostname");
      return [normalized, parseBrand(value)];
    }),
  );
}

export async function resolveTenantBrand(): Promise<TenantBrand> {
  const headerStore = await headers();
  const forwarded = headerStore.get("x-forwarded-host");
  const host = (forwarded ?? headerStore.get("host") ?? process.env.STOREFRONT_DEFAULT_HOST ?? "")
    .split(",", 1)[0]
    .trim()
    .split(":", 1)[0]
    .toLowerCase();
  const tenantMap = loadTenantMap();
  const brand = tenantMap[host];
  if (!brand) throw new Error("This storefront hostname is not configured");
  return brand;
}

export function brandStyle(brand: TenantBrand): React.CSSProperties {
  return {
    "--brand": brand.primary,
    "--brand-dark": brand.primaryDark,
    "--accent": brand.accent,
  } as React.CSSProperties;
}
