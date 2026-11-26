"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { Icon } from "@/components/Icon";
import { Modal } from "@/features/operations/Modal";
import { catalogueApi, Product } from "@/lib/catalogue";
import { Batch, idempotencyKey, inventoryApi, InventorySummary, StockItem, Warehouse } from "@/lib/inventory";

type Row = { product: Product; stock?: StockItem; batches: Batch[] };
const emptySummary: InventorySummary = { tracked_products: 0, available_units: 0, reserved_units: 0, damaged_units: 0, low_stock_products: 0, out_of_stock_products: 0, expiring_within_60_days: 0, blocked_batches: 0 };

export function InventoryWorkspace() {
  const [products, setProducts] = useState<Product[]>([]);
  const [stock, setStock] = useState<StockItem[]>([]);
  const [batches, setBatches] = useState<Record<string, Batch[]>>({});
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [summary, setSummary] = useState(emptySummary);
  const [selected, setSelected] = useState<Row | null>(null);
  const [setupProduct, setSetupProduct] = useState<Product | null>(null);
  const [advanced, setAdvanced] = useState(false);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<"ALL" | "LOW" | "OUT" | "EXPIRING">("ALL");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function load() {
    setLoading(true);
    try {
      const [nextProducts, nextStock, nextWarehouses, nextSummary] = await Promise.all([catalogueApi.products(), inventoryApi.stockItems(), inventoryApi.warehouses(), inventoryApi.summary()]);
      const batchEntries = await Promise.all(nextStock.filter((item) => item.tracking_mode === "BATCH_EXPIRY").map(async (item) => [item.id, await inventoryApi.batches(item.id)] as const));
      setProducts(nextProducts); setStock(nextStock); setWarehouses(nextWarehouses); setSummary(nextSummary); setBatches(Object.fromEntries(batchEntries));
    } catch (cause) { setError(message(cause)); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, []);

  async function execute(key: string, action: () => Promise<string>) {
    setBusy(key); setError(""); setNotice("");
    try { setNotice(await action()); setSelected(null); setSetupProduct(null); }
    catch (cause) { setError(message(cause)); }
    finally { await load(); setBusy(""); }
  }

  const rows = useMemo<Row[]>(() => products.map((product) => { const item = stock.find((entry) => entry.product_id === product.id); return { product, stock: item, batches: item ? batches[item.id] ?? [] : [] }; }), [products, stock, batches]);
  const visibleRows = rows.filter((row) => {
    const textMatch = `${row.product.name} ${row.product.sku}`.toLowerCase().includes(query.toLowerCase());
    if (!textMatch) return false;
    if (filter === "LOW") return Boolean(row.stock && row.stock.available <= row.stock.low_stock_threshold);
    if (filter === "OUT") return Boolean(row.stock && row.stock.available === 0);
    if (filter === "EXPIRING") return row.batches.some((batch) => isExpiring(batch.expires_on));
    return true;
  });
  const main = warehouses.find((warehouse) => warehouse.code === "MAIN");

  if (loading) return <div className="loading-state">Loading inventory...</div>;
  return <div className="simple-inventory">
    {error && <div className="banner error-banner" role="alert">{error}<button onClick={() => setError("")} type="button">×</button></div>}{notice && <div className="banner success-banner" role="status">{notice}</div>}
    <section className="metric-grid inventory-metrics"><Metric label="Available units" value={summary.available_units} note={`${summary.reserved_units} reserved`} /><Metric label="Low stock" value={summary.low_stock_products} note="Needs attention" warning={summary.low_stock_products > 0} /><Metric label="Out of stock" value={summary.out_of_stock_products} note="Unavailable to customers" warning={summary.out_of_stock_products > 0} /><Metric label="Expiring soon" value={summary.expiring_within_60_days} note="Within 60 days" warning={summary.expiring_within_60_days > 0} /></section>
    <section className="admin-card inventory-list-card">
      <div className="inventory-list-heading"><div><p className="eyebrow">MAIN LOCATION</p><h2>Product stock</h2><p>Use Add stock when new goods arrive. Batch rules appear only for expiry-tracked products.</p></div><div className="location-pill"><span>✓</span><div><strong>{main?.name ?? "Main Location"}</strong><small>Default stock location</small></div></div></div>
      <div className="inventory-controls"><div className="inventory-search"><Icon name="refresh" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search product or SKU" /></div><div className="filter-pills">{(["ALL", "LOW", "OUT", "EXPIRING"] as const).map((item) => <button className={filter === item ? "active" : ""} onClick={() => setFilter(item)} type="button" key={item}>{item === "ALL" ? "All" : item === "LOW" ? "Low stock" : item === "OUT" ? "Out of stock" : "Expiring"}</button>)}</div><button className="refresh-button" onClick={() => void load()} type="button"><Icon name="refresh" /> Refresh</button></div>
      {!visibleRows.length ? <div className="inventory-empty"><Icon name="box" /><h3>No matching products</h3><p>Create a product first or change the current filter.</p></div> : <div className="inventory-product-list">{visibleRows.map((row) => <article key={row.product.id} className="inventory-product-row"><div className="product-identity"><span>{row.product.name.slice(0, 2).toUpperCase()}</span><div><strong>{row.product.name}</strong><small>{row.product.sku} · {row.stock?.tracking_mode === "BATCH_EXPIRY" ? "Batch & expiry" : row.stock ? "Simple stock" : "Setup needed"}</small></div></div><div className="quantity-cell"><small>Available</small><strong>{row.stock?.available ?? "—"}</strong></div><div className="quantity-cell"><small>Reserved</small><strong>{row.stock?.reserved ?? "—"}</strong></div><StockStatus row={row} /><button className="primary-button add-stock-button" onClick={() => row.stock ? setSelected(row) : setSetupProduct(row.product)} type="button">{row.stock ? "Add stock" : "Set up stock"}</button></article>)}</div>}
    </section>
    <section className="advanced-inventory-card"><button onClick={() => setAdvanced((value) => !value)} type="button"><div><span className="eyebrow">ADVANCED INVENTORY</span><strong>Batch holds, recalls and lot details</strong><small>Use only when quality or expiry control requires it.</small></div><b>{advanced ? "Hide" : "Open"}</b></button>{advanced && <div className="advanced-content">{rows.filter((row) => row.batches.length).map((row) => <div className="advanced-product" key={row.product.id}><h3>{row.product.name}<small>{row.product.sku}</small></h3>{row.batches.map((batch) => <div className="advanced-batch" key={batch.id}><span><strong>{batch.lot_number}</strong><small>{batch.expires_on ? `Expires ${dateLabel(batch.expires_on)}` : "No expiry date"}</small></span><span>{batch.available} available</span><i className={`batch-status ${batch.status.toLowerCase()}${batch.expired ? " expired" : ""}`}>{batch.expired ? "EXPIRED" : batch.status}</i><div>{batch.status === "AVAILABLE" ? <><button onClick={() => void changeStatus(row.stock!, batch, "HOLD", execute)} type="button">Hold</button><button onClick={() => void changeStatus(row.stock!, batch, "RECALLED", execute)} type="button">Recall</button></> : <button onClick={() => void changeStatus(row.stock!, batch, "AVAILABLE", execute)} type="button">Make available</button>}</div></div>)}</div>)}{!rows.some((row) => row.batches.length) && <p>No batch-tracked stock has been received.</p>}</div>}</section>
    <section className="coming-soon-location"><div><span>COMING SOON</span><h3>Multiple warehouses and stock transfers</h3><p>The current release keeps every tenant on one reliable Main Location. Branches and transfers will be introduced as a separate controlled workflow.</p></div></section>
    {selected?.stock && <AddStockModal row={{ ...selected, stock: selected.stock }} close={() => setSelected(null)} busy={busy} execute={execute} />}
    {setupProduct && main && <SetupStockModal product={setupProduct} warehouse={main} close={() => setSetupProduct(null)} busy={busy} execute={execute} />}
  </div>;
}

function AddStockModal({ row, close, busy, execute }: { row: Row & { stock: StockItem }; close: () => void; busy: string; execute: (key: string, action: () => Promise<string>) => Promise<void> }) {
  async function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const data = new FormData(event.currentTarget); const quantity = Number(data.get("quantity")); await execute(`receive-${row.stock.id}`, async () => { if (row.stock.tracking_mode === "SIMPLE") await inventoryApi.receiveSimpleStock(row.stock.id, { quantity, source_reference: String(data.get("reference")).trim() || undefined, idempotency_key: idempotencyKey("receipt") }); else await inventoryApi.createBatch(row.stock.id, { lot_number: String(data.get("lot_number")).trim(), quantity, manufactured_on: String(data.get("manufactured_on")) || undefined, expires_on: String(data.get("expires_on")) || undefined, source_reference: String(data.get("reference")).trim() || undefined, idempotency_key: idempotencyKey("batch-receipt") }); return `${quantity} units were added to ${row.product.name}.`; }); }
  return <Modal title={`Add stock · ${row.product.name}`} eyebrow="STOCK RECEIPT" close={close} small><form className="stack-form modal-stock-form" onSubmit={submit}><label>Quantity received<input name="quantity" required min="1" type="number" /></label>{row.stock.tracking_mode === "BATCH_EXPIRY" && <><label>Batch / lot number<input name="lot_number" required maxLength={120} /></label><div className="form-pair"><label>Manufactured <em>Optional</em><input name="manufactured_on" type="date" /></label><label>Expiry date <em>Recommended</em><input name="expires_on" type="date" /></label></div></>}<label>Supplier reference <em>Optional</em><input name="reference" maxLength={160} placeholder="Invoice or GRN" /></label><p className="form-help">Stock is added to Main Location. The operation is protected against accidental duplicate submission.</p><div className="modal-actions"><button className="secondary-button" onClick={close} type="button">Cancel</button><button className="primary-button" disabled={busy === `receive-${row.stock.id}`} type="submit">Add stock</button></div></form></Modal>;
}

function SetupStockModal({ product, warehouse, close, busy, execute }: { product: Product; warehouse: Warehouse; close: () => void; busy: string; execute: (key: string, action: () => Promise<string>) => Promise<void> }) {
  const [mode, setMode] = useState<StockItem["tracking_mode"]>("SIMPLE");
  async function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const data = new FormData(event.currentTarget); await execute(`setup-${product.id}`, async () => { await inventoryApi.createStockItem({ product_id: product.id, variant_id: null, sku: product.sku, warehouse_id: warehouse.id, low_stock_threshold: Number(data.get("threshold")), tracking_mode: mode }); return `${product.name} inventory is ready. Use Add stock to receive quantity.`; }); }
  return <Modal title={`Set up stock · ${product.name}`} eyebrow="ONE-TIME SETUP" close={close} small><form className="stack-form modal-stock-form" onSubmit={submit}><label>Tracking method<select value={mode} onChange={(event) => setMode(event.target.value as StockItem["tracking_mode"])}><option value="SIMPLE">Simple quantity</option><option value="BATCH_EXPIRY">Batch and expiry</option></select></label><label>Low-stock alert<input name="threshold" required type="number" min="0" defaultValue="5" /></label><p className="form-help">Location: {warehouse.name}. Multi-location inventory is coming soon.</p><div className="modal-actions"><button className="secondary-button" onClick={close} type="button">Cancel</button><button className="primary-button" disabled={busy === `setup-${product.id}`} type="submit">Set up stock</button></div></form></Modal>;
}

function StockStatus({ row }: { row: Row }) { if (!row.stock) return <span className="inventory-state setup">Setup needed</span>; if (row.stock.available === 0) return <span className="inventory-state out">Out of stock</span>; if (row.stock.available <= row.stock.low_stock_threshold) return <span className="inventory-state low">Low stock</span>; if (row.batches.some((batch) => isExpiring(batch.expires_on))) return <span className="inventory-state expiry">Expiry attention</span>; return <span className="inventory-state healthy">In stock</span>; }
function Metric({ label, value, note, warning }: { label: string; value: number; note: string; warning?: boolean }) { return <article className={`metric${warning ? " metric-warning" : ""}`}><span><Icon name="box" /></span><p>{label}</p><strong>{value}</strong><small>{note}</small></article>; }
async function changeStatus(item: StockItem, batch: Batch, status: Batch["status"], execute: (key: string, action: () => Promise<string>) => Promise<void>) { const reason = window.prompt(`Reason for changing ${batch.lot_number} to ${status.toLowerCase()}?`); if (!reason?.trim()) return; await execute(`batch-${batch.id}`, async () => { await inventoryApi.updateBatchStatus(item.id, batch.id, { status, reason: reason.trim(), idempotency_key: idempotencyKey("batch-status") }); return `${batch.lot_number} is now ${status.toLowerCase()}.`; }); }
function isExpiring(value: string | null): boolean { if (!value) return false; const days = Math.ceil((new Date(`${value}T00:00:00`).getTime() - Date.now()) / 86_400_000); return days <= 60; }
function dateLabel(value: string): string { return new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(`${value}T00:00:00`)); }
function message(cause: unknown): string { return cause instanceof Error ? cause.message : "Inventory operation failed"; }
