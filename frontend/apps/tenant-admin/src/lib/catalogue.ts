import { getAccessToken } from "./keycloak";

export type Category = { id: string; name: string; slug: string; description: string | null };
export type Product = { id: string; sku: string; name: string; description: string | null; price_cents: number; published: boolean };
export type ProductInput = { sku: string; name: string; description?: string; price_cents: number; published: boolean };
export type CategoryInput = { name: string; slug: string; description?: string };

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
};

export function formatMoney(cents: number): string { return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(cents / 100); }
export function slugify(value: string): string { return value.trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "").slice(0, 120); }
