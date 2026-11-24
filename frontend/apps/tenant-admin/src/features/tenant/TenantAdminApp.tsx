"use client";

import { useState } from "react";
import { AdminLogin, AuthState } from "@/features/auth/AdminLogin";
import { CatalogueWorkspace } from "@/features/catalogue/CatalogueWorkspace";
import { TenantBrand, TenantBrandProvider } from "@/features/tenant/TenantBrandProvider";

export function TenantAdminApp({ brand }: { brand: TenantBrand }) {
  const [state, setState] = useState<AuthState>("checking");
  const theme = {
    "--brand": brand.palette.primary,
    "--brand-dark": brand.palette.primary_dark,
    "--mint": brand.palette.accent,
    "--brand-surface": brand.palette.surface,
  } as React.CSSProperties;
  return <TenantBrandProvider brand={brand}><div style={theme}>{state === "authorized" ? <CatalogueWorkspace /> : <AdminLogin onState={setState} />}</div></TenantBrandProvider>;
}
