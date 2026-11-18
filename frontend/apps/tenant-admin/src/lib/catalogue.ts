import { getAccessToken } from "./keycloak";

export type Category = { id: string; name: string; slug: string; description: string | null };
export type Product = { id: string; sku: string; name: string; description: string | null; price_cents: number; published: boolean };
export type ProductInput = { sku: string; name: string; description?: string; price_cents: number; published: boolean };
export type CategoryInput = { name: string; slug: string; description?: string };
export type ProductImage = { id: string; url: string; alt_text: string | null; sort_order: number };

const baseUrl = process.env.NEXT_PUBLIC_CATALOGUE_API_URL;

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  if (!baseUrl) throw new Error("Catalogue API is not configured");
  const token = await getAccessToken();
  const response = await fetch(`${baseUrl}${path}`, { ...options, headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json", ...options.headers } });
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(body?.detail || "Catalogue request failed");
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const catalogueApi = {
  products: () => request<Product[]>("/api/v1/products?limit=100"),
  categories: () => request<Category[]>("/api/v1/categories"),
  createCategory: (input: CategoryInput) => request<Category>("/api/v1/categories", { method: "POST", body: JSON.stringify(input) }),
  createProduct: (input: ProductInput) => request<Product>("/api/v1/products", { method: "POST", body: JSON.stringify(input) }),
  updateProduct: (id: string, input: Partial<ProductInput>) => request<Product>(`/api/v1/products/${encodeURIComponent(id)}`, { method: "PATCH", body: JSON.stringify(input) }),
  deleteProduct: (id: string) => request<void>(`/api/v1/products/${encodeURIComponent(id)}`, { method: "DELETE" }),
  productCategories: (id: string) => request<Category[]>(`/api/v1/products/${encodeURIComponent(id)}/categories`),
  attachCategory: (productId: string, categoryId: string) => request<void>(`/api/v1/products/${encodeURIComponent(productId)}/categories/${encodeURIComponent(categoryId)}`, { method: "PUT" }),
  addProductImage: (productId: string, input: Omit<ProductImage, "id">) => request<ProductImage>(`/api/v1/products/${encodeURIComponent(productId)}/images`, { method: "POST", body: JSON.stringify(input) }),
};

export async function uploadProductImage(file: File): Promise<{ id: string; url: string; width: number; height: number }> {
  const base = process.env.NEXT_PUBLIC_MEDIA_API_URL;
  if (!base) throw new Error("Media upload is not configured for this tenant");
  if (!file.type.match(/^image\/(jpeg|png|webp)$/)) throw new Error("Choose a JPEG, PNG, or WebP image");
  if (file.size > 5 * 1024 * 1024) throw new Error("Image must be no larger than 5 MB");
  const token = await getAccessToken(); const body = new FormData(); body.append("file", file);
  const response = await fetch(`${base}/api/v1/media`, { method: "POST", headers: { Authorization: `Bearer ${token}` }, body });
  const payload = await response.json().catch(() => null) as { detail?: string; id?: string; url?: string; width?: number; height?: number } | null;
  if (!response.ok || !payload?.id || !payload.url) throw new Error(payload?.detail || "Image upload failed");
  return { id: payload.id, url: `${base}${payload.url}`, width: payload.width ?? 0, height: payload.height ?? 0 };
}

export function formatMoney(cents: number): string { return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(cents / 100); }
export function slugify(value: string): string { return value.trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "").slice(0, 120); }
