"use client";

import { useEffect, useState } from "react";
import { Icon } from "@/components/Icon";
import { catalogueApi, Product } from "@/lib/catalogue";
import { InventoryAlert, InventorySummary, inventoryApi } from "@/lib/inventory";

const emptySummary: InventorySummary = {
  tracked_products: 0,
  available_units: 0,
  reserved_units: 0,
  damaged_units: 0,
  low_stock_products: 0,
  out_of_stock_products: 0,
  expiring_within_60_days: 0,
  blocked_batches: 0,
};

export function DashboardWorkspace({ onNavigate }: { onNavigate: (view: "products" | "inventory") => void }) {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState(0);
  const [summary, setSummary] = useState(emptySummary);
  const [alerts, setAlerts] = useState<InventoryAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true); setError("");
    try {
      const [nextProducts, nextCategories, nextSummary, low, expiring] = await Promise.all([
        catalogueApi.products(), catalogueApi.categories(), inventoryApi.summary(),
        inventoryApi.alerts("LOW_STOCK", 5), inventoryApi.alerts("EXPIRING", 5),
      ]);
      setProducts(nextProducts); setCategories(nextCategories.length); setSummary(nextSummary);
      setAlerts([...low, ...expiring].slice(0, 8));
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to load dashboard"); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, []);

  if (loading) return <div className="loading-state">Preparing your business overview...</div>;
  return <div className="dashboard-workspace">
    {error && <div className="banner error-banner" role="alert">{error}</div>}
    <section className="metric-grid dashboard-metrics">
      <Metric label="Products" value={products.length} note={`${products.filter((item) => item.published).length} published`} icon="box" />
      <Metric label="Available units" value={summary.available_units} note={`${summary.reserved_units} reserved`} icon="grid" />
      <Metric label="Low stock" value={summary.low_stock_products} note={`${summary.out_of_stock_products} out of stock`} icon="chart" warning={summary.low_stock_products > 0} />
      <Metric label="Expiry attention" value={summary.expiring_within_60_days} note={`${summary.blocked_batches} held or recalled`} icon="tag" warning={summary.expiring_within_60_days > 0} />
    </section>
    <section className="dashboard-grid">
      <article className="admin-card quick-start-card">
        <p className="eyebrow">QUICK ACTIONS</p><h2>Keep the store moving</h2>
        <p>Create customer-visible products, then add stock without handling technical inventory setup.</p>
        <div className="workflow-actions"><button className="primary-button" onClick={() => onNavigate("products")} type="button"><Icon name="plus" /> Add product</button><button className="secondary-button" onClick={() => onNavigate("inventory")} type="button">Add stock</button></div>
        <div className="dashboard-facts"><span><strong>{categories}</strong> categories</span><span><strong>{summary.tracked_products}</strong> stock-tracked products</span></div>
      </article>
      <article className="admin-card alerts-card">
        <div className="card-heading"><div><p className="eyebrow">ATTENTION NEEDED</p><h2>Inventory alerts</h2></div><button className="table-action" onClick={() => onNavigate("inventory")} type="button">View inventory</button></div>
        {!alerts.length ? <div className="all-clear"><span>✓</span><div><strong>Everything looks healthy</strong><p>No low-stock or expiry alerts.</p></div></div> : <div className="alert-list">{alerts.map((alert, index) => <div key={`${alert.type}-${alert.stock_item_id}-${alert.batch_id ?? index}`}><span className={`alert-icon ${alert.type.toLowerCase()}`}>{alert.type === "EXPIRING" ? "!" : alert.available}</span><div><strong>{alert.sku}</strong><p>{alert.type === "EXPIRING" ? `${alert.lot_number} expires ${formatDate(alert.expires_on)}` : alert.type === "OUT_OF_STOCK" ? "Out of stock" : `${alert.available} available · threshold ${alert.low_stock_threshold}`}</p></div></div>)}</div>}
      </article>
    </section>
    <section className="future-strip"><div><span>COMING SOON</span><strong>Orders, customers, payments and revenue</strong><p>These cards will use real service data when each backend is completed—never placeholder numbers.</p></div></section>
  </div>;
}

function Metric({ label, value, note, icon, warning }: { label: string; value: number; note: string; icon: "box" | "chart" | "grid" | "tag"; warning?: boolean }) {
  return <article className={`metric${warning ? " metric-warning" : ""}`}><span><Icon name={icon} /></span><p>{label}</p><strong>{value}</strong><small>{note}</small></article>;
}
function formatDate(value: string | null): string {
  if (!value) return "soon";
  return new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(`${value}T00:00:00`));
}
