import { getAccessToken } from "./keycloak";

export type Warehouse = { id: string; code: string; name: string; active: boolean };
export type StockItem = {
  id: string;
  product_id: string;
  variant_id: string | null;
  sku: string;
  warehouse_id: string;
  on_hand: number;
  reserved: number;
  damaged: number;
  available: number;
  low_stock_threshold: number;
  tracking_mode: "SIMPLE" | "BATCH_EXPIRY";
  version: number;
  updated_at: string;
};
export type Batch = {
  id: string;
  stock_item_id: string;
  lot_number: string;
  manufactured_on: string | null;
  expires_on: string | null;
  status: "AVAILABLE" | "HOLD" | "RECALLED";
  on_hand: number;
  reserved: number;
  available: number;
  expired: boolean;
  created_at: string;
  updated_at: string;
};
export type InventorySummary = {
  tracked_products: number;
  available_units: number;
  reserved_units: number;
  damaged_units: number;
  low_stock_products: number;
  out_of_stock_products: number;
  expiring_within_60_days: number;
  blocked_batches: number;
};
export type InventoryAlert = {
  type: "LOW_STOCK" | "OUT_OF_STOCK" | "EXPIRING";
  stock_item_id: string;
  sku: string;
  available: number;
  low_stock_threshold: number | null;
  batch_id: string | null;
  lot_number: string | null;
  expires_on: string | null;
};

function detailMessage(detail: unknown): string {
  if (typeof detail === "string" && detail.trim()) return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => (item && typeof item === "object" && "msg" in item ? String(item.msg) : ""))
      .filter(Boolean)
      .join("; ");
  }
  return "Inventory request failed";
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = await getAccessToken();
  const response = await fetch(`/api/tenant/inventory${path}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: unknown } | null;
    throw new Error(detailMessage(body?.detail));
  }
  return response.status === 204 ? (undefined as T) : (response.json() as Promise<T>);
}

export const inventoryApi = {
  warehouses: () => request<Warehouse[]>("/api/v1/warehouses"),
  stockItems: () => request<StockItem[]>("/api/v1/stock-items"),
  createStockItem: (input: {
    product_id: string;
    variant_id: string | null;
    sku: string;
    warehouse_id: string;
    low_stock_threshold: number;
    tracking_mode: StockItem["tracking_mode"];
  }) => request<StockItem>("/api/v1/stock-items", { method: "POST", body: JSON.stringify(input) }),
  receiveSimpleStock: (
    stockItemId: string,
    input: {
      quantity: number;
      source_reference?: string;
      idempotency_key: string;
    },
  ) =>
    request(`/api/v1/stock-items/${encodeURIComponent(stockItemId)}/receipts`, {
      method: "POST",
      body: JSON.stringify(input),
    }),
  batches: (stockItemId: string) =>
    request<Batch[]>(`/api/v1/stock-items/${encodeURIComponent(stockItemId)}/batches`),
  createBatch: (
    stockItemId: string,
    input: {
      lot_number: string;
      quantity: number;
      manufactured_on?: string;
      expires_on?: string;
      source_reference?: string;
      idempotency_key: string;
    },
  ) =>
    request<Batch>(`/api/v1/stock-items/${encodeURIComponent(stockItemId)}/batches`, {
      method: "POST",
      body: JSON.stringify(input),
    }),
  updateBatchStatus: (
    stockItemId: string,
    batchId: string,
    input: { status: Batch["status"]; reason: string; idempotency_key: string },
  ) =>
    request<Batch>(
      `/api/v1/stock-items/${encodeURIComponent(stockItemId)}/batches/${encodeURIComponent(batchId)}/status`,
      { method: "PATCH", body: JSON.stringify(input) },
    ),
  summary: () => request<InventorySummary>("/api/v1/dashboard/summary"),
  alerts: (type: InventoryAlert["type"], limit = 10) =>
    request<InventoryAlert[]>(`/api/v1/alerts?type=${type}&limit=${limit}`),
};

export function idempotencyKey(prefix: string): string {
  return `${prefix}-${crypto.randomUUID()}`;
}
