import "./globals.css";
import { tenantAdminBrand } from "@/lib/brand";

export default function Layout({children}:{children:React.ReactNode}) {
  const theme = { "--brand": tenantAdminBrand.primary, "--brand-dark": tenantAdminBrand.primaryDark, "--mint": tenantAdminBrand.accent } as React.CSSProperties;
  return <html lang="en" style={theme}><body>{children}</body></html>;
}
