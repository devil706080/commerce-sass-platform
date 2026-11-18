const HEX = /^#[0-9a-f]{6}$/i;

function color(value: string | undefined, fallback: string): string { return value && HEX.test(value) ? value : fallback; }

export const tenantAdminBrand = {
  name: process.env.NEXT_PUBLIC_TENANT_ADMIN_NAME?.trim() || "Tenant workspace",
  primary: color(process.env.NEXT_PUBLIC_TENANT_ADMIN_PRIMARY, "#176e8c"),
  primaryDark: color(process.env.NEXT_PUBLIC_TENANT_ADMIN_PRIMARY_DARK, "#104c67"),
  accent: color(process.env.NEXT_PUBLIC_TENANT_ADMIN_ACCENT, "#65d0ab"),
};
