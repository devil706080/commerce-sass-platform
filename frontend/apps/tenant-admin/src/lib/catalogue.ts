import { getAccessToken } from "./keycloak";

export type Category = { id: string; name: string; slug: string; description: string | null };
export type Product = { id: string; sku: string; name: string; description: string | null; price_cents: number; published: boolean };
export type ProductInput = { sku: string; name: string; description?: string; price_cents: number; published: boolean };
export type CategoryInput = { name: string; slug: string; description?: string };
export type ProductImage = { id: string; url: string; alt_text: string | null; sort_order: number };

const baseUrl = "/api/tenant/catalogue";

function apiErrorMessage(detail: unknown, fallback: string): string {
  if (typeof detail === "string" && detail.trim()) return detail;
  if (Array.isArray(detail)) {
    const messages = detail.flatMap((item) => {
      if (!item || typeof item !== "object") return [];
      const record = item as { msg?: unknown; loc?: unknown[] };
      if (typeof record.msg !== "string") return [];
      const field = Array.isArray(record.loc) ? record.loc.at(-1) : undefined;
      return [`${typeof field === "string" ? `${field}: ` : ""}${record.msg}`];
    });
    if (messages.length) return messages.join("; ");
  }
  if (detail && typeof detail === "object" && "msg" in detail) {
    const message = (detail as { msg?: unknown }).msg;
    if (typeof message === "string" && message.trim()) return message;
  }
  return fallback;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = await getAccessToken();
  const response = await fetch(`${baseUrl}${path}`, { ...options, headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json", ...options.headers } });
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: unknown } | null;
    throw new Error(apiErrorMessage(body?.detail, "Catalogue request failed"));
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const catalogueApi = {
  products: () => request<Product[]>("/api/v1/products?limit=100"),
  categories: () => request<Category[]>("/api/v1/categories"),
  createCategory: (input: CategoryInput) => request<Category>("/api/v1/categories", { method: "POST", body: JSON.stringify(input) }),
  updateCategory: (id: string, input: Pick<CategoryInput, "name" | "description">) => request<Category>(`/api/v1/categories/${encodeURIComponent(id)}`, { method: "PATCH", body: JSON.stringify(input) }),
  deleteCategory: (id: string) => request<void>(`/api/v1/categories/${encodeURIComponent(id)}`, { method: "DELETE" }),
  createProduct: (input: ProductInput) => request<Product>("/api/v1/products", { method: "POST", body: JSON.stringify(input) }),
  updateProduct: (id: string, input: Partial<ProductInput>) => request<Product>(`/api/v1/products/${encodeURIComponent(id)}`, { method: "PATCH", body: JSON.stringify(input) }),
  deleteProduct: (id: string) => request<void>(`/api/v1/products/${encodeURIComponent(id)}`, { method: "DELETE" }),
  productCategories: (id: string) => request<Category[]>(`/api/v1/products/${encodeURIComponent(id)}/categories`),
  attachCategory: (productId: string, categoryId: string) => request<void>(`/api/v1/products/${encodeURIComponent(productId)}/categories/${encodeURIComponent(categoryId)}`, { method: "PUT" }),
  detachCategory: (productId: string, categoryId: string) => request<void>(`/api/v1/products/${encodeURIComponent(productId)}/categories/${encodeURIComponent(categoryId)}`, { method: "DELETE" }),
  productImages: (productId: string) => request<ProductImage[]>(`/api/v1/products/${encodeURIComponent(productId)}/images`),
  addProductImage: (productId: string, input: Omit<ProductImage, "id">) => request<ProductImage>(`/api/v1/products/${encodeURIComponent(productId)}/images`, { method: "POST", body: JSON.stringify(input) }),
  updateProductImage: (productId: string, imageId: string, input: Partial<Omit<ProductImage, "id">>) => request<ProductImage>(`/api/v1/products/${encodeURIComponent(productId)}/images/${encodeURIComponent(imageId)}`, { method: "PATCH", body: JSON.stringify(input) }),
  deleteProductImage: (productId: string, imageId: string) => request<void>(`/api/v1/products/${encodeURIComponent(productId)}/images/${encodeURIComponent(imageId)}`, { method: "DELETE" }),
};

export async function uploadProductImage(file: File): Promise<{ id: string; url: string; width: number; height: number }> {
  const base = "/api/tenant/media";
  if (!file.type.match(/^image\/(jpeg|png|webp)$/)) throw new Error("Choose a JPEG, PNG, or WebP image");
  if (file.size > 5 * 1024 * 1024) throw new Error("Image must be no larger than 5 MB");
  const token = await getAccessToken(); const body = new FormData(); body.append("file", file);
  const response = await fetch(`${base}/api/v1/media`, { method: "POST", headers: { Authorization: `Bearer ${token}` }, body });
  const payload = await response.json().catch(() => null) as { detail?: unknown; id?: string; url?: string; width?: number; height?: number } | null;
  if (!response.ok || !payload?.id || !payload.url) throw new Error(apiErrorMessage(payload?.detail, "Image upload failed"));
  return { id: payload.id, url: payload.url, width: payload.width ?? 0, height: payload.height ?? 0 };
}

export async function deleteUploadedImage(assetId: string): Promise<void> {
  const token = await getAccessToken();
  const response = await fetch(`/api/tenant/media/api/v1/media/${encodeURIComponent(assetId)}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok && response.status !== 404) {
    const payload = await response.json().catch(() => null) as { detail?: unknown } | null;
    throw new Error(apiErrorMessage(payload?.detail, "Unable to clean up uploaded image"));
  }
}

export function mediaAssetId(url: string): string | null {
  const match = /^\/api\/v1\/media\/([0-9a-f-]{36})\/content$/i.exec(url);
  return match?.[1] ?? null;
}

export function mediaDisplayUrl(url: string): string {
  return url.startsWith("/api/v1/media/") ? `/api/tenant/media${url}` : url;
}

export function formatMoney(cents: number): string { return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(cents / 100); }
export function slugify(value: string): string { return value.trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "").slice(0, 120); }
