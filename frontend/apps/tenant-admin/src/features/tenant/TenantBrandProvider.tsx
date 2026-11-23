"use client";

import { createContext, useContext } from "react";

export type TenantBrand = {
  tenantId: string;
  hostname: string;
  displayName: string;
  fallbackInitials: string;
  themeKey: string;
  palette: { primary: string; primary_dark: string; accent: string; surface: string };
};

const TenantBrandContext = createContext<TenantBrand | null>(null);

export function TenantBrandProvider({ brand, children }: { brand: TenantBrand; children: React.ReactNode }) {
  return <TenantBrandContext.Provider value={brand}>{children}</TenantBrandContext.Provider>;
}

export function useTenantBrand(): TenantBrand {
  const brand = useContext(TenantBrandContext);
  if (!brand) throw new Error("Tenant branding context is unavailable");
  return brand;
}
