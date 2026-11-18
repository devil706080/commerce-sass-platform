import "server-only";
import type { CatalogueCategory, CatalogueProduct } from "./types";

export class CatalogueUnavailableError extends Error {}

function apiBase(): string {
  const value = process.env.CATALOGUE_API_INTERNAL_URL;
  if (!value) throw new CatalogueUnavailableError("Catalogue API is not configured");
  return value.replace(/\/$/, "");
}

async function request<T>(path: string): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000);
  try {
    const response = await fetch(`${apiBase()}${path}`, {
      headers: { Accept: "application/json" },
      signal: controller.signal,
      cache: "no-store",
    });
    if (!response.ok) {
      if (response.status === 404) throw new Error("Product not found");
      throw new CatalogueUnavailableError(`Catalogue API returned ${response.status}`);
    }
    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof CatalogueUnavailableError || (error instanceof Error && error.message === "Product not found")) {
      throw error;
    }
    throw new CatalogueUnavailableError("Catalogue API is temporarily unavailable");
  } finally {
    clearTimeout(timeout);
  }
}

export async function listProducts(search?: string, limit = 20, category?: string): Promise<CatalogueProduct[]> {
  const params = new URLSearchParams({ limit: String(Math.min(Math.max(limit, 1), 100)), offset: "0" });
  if (search?.trim()) params.set("search", search.trim().slice(0, 100));
  if (category && /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(category)) params.set("category", category);
  return request<CatalogueProduct[]>(`/api/v1/store/products?${params.toString()}`);
}

export async function listCategories(): Promise<CatalogueCategory[]> {
  return request<CatalogueCategory[]>("/api/v1/store/categories");
}

export async function getProduct(id: string): Promise<CatalogueProduct> {
  if (!/^[0-9a-f-]{36}$/i.test(id)) throw new Error("Product not found");
  return request<CatalogueProduct>(`/api/v1/store/products/${encodeURIComponent(id)}`);
}

export function formatMoney(cents: number): string {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 2 }).format(cents / 100);
}
