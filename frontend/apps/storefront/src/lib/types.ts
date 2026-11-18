export type CatalogueProduct = {
  id: string;
  sku: string;
  name: string;
  description: string | null;
  price_cents: number;
  published: boolean;
};

export type CatalogueCategory = {
  id: string;
  name: string;
  slug: string;
  description: string | null;
};

export type TenantBrand = {
  name: string;
  shortName: string;
  locationLabel: string;
  supportLine: string;
  primary: string;
  primaryDark: string;
  accent: string;
};
