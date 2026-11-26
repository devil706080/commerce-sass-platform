"use client";

import { FormEvent, useEffect, useState } from "react";
import { Icon } from "@/components/Icon";
import { Modal } from "@/features/operations/Modal";
import {
  catalogueApi, Category, deleteUploadedImage, formatMoney, mediaAssetId,
  mediaDisplayUrl, Product, ProductImage, uploadProductImage,
} from "@/lib/catalogue";
import { idempotencyKey, inventoryApi, StockItem } from "@/lib/inventory";

type ProductForm = {
  name: string; sku: string; description: string; price: string; published: boolean;
  categoryIds: string[]; image: File | null; openingStock: string;
  trackingMode: "SIMPLE" | "BATCH_EXPIRY"; lotNumber: string; manufacturedOn: string;
  expiresOn: string; reference: string; lowStockThreshold: string;
};
const blankForm: ProductForm = {
  name: "", sku: "", description: "", price: "", published: false, categoryIds: [],
  image: null, openingStock: "0", trackingMode: "SIMPLE", lotNumber: "",
  manufacturedOn: "", expiresOn: "", reference: "", lowStockThreshold: "5",
};

export function ProductsWorkspace({ onOpenInventory }: { onOpenInventory: () => void }) {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [assignments, setAssignments] = useState<Record<string, Category[]>>({});
  const [images, setImages] = useState<Record<string, ProductImage[]>>({});
  const [stock, setStock] = useState<StockItem[]>([]);
  const [form, setForm] = useState<ProductForm>(blankForm);
  const [editing, setEditing] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function load() {
    setLoading(true);
    try {
      const [nextProducts, nextCategories, nextStock] = await Promise.all([
        catalogueApi.products(), catalogueApi.categories(), inventoryApi.stockItems(),
      ]);
      const detail = await Promise.all(nextProducts.map(async (product) => ({
        id: product.id,
        categories: await catalogueApi.productCategories(product.id),
        images: await catalogueApi.productImages(product.id),
      })));
      setProducts(nextProducts); setCategories(nextCategories); setStock(nextStock);
      setAssignments(Object.fromEntries(detail.map((item) => [item.id, item.categories])));
      setImages(Object.fromEntries(detail.map((item) => [item.id, item.images])));
    } catch (cause) { setError(message(cause)); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, []);

  async function execute(key: string, action: () => Promise<string>) {
    setBusy(key); setError(""); setNotice("");
    try { setNotice(await action()); }
    catch (cause) { setError(message(cause)); }
    finally { await load(); setBusy(""); }
  }

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const price = cents(form.price); const opening = Number(form.openingStock || 0);
    if (price === null || !Number.isInteger(opening) || opening < 0) { setError("Enter valid non-negative price and opening stock values."); return; }
    if (form.trackingMode === "BATCH_EXPIRY" && opening > 0 && !form.lotNumber.trim()) { setError("A lot number is required for batch-tracked opening stock."); return; }
    await execute("create-product", async () => {
      const product = await catalogueApi.createProduct({ sku: form.sku.trim().toUpperCase(), name: form.name.trim(), description: form.description.trim() || undefined, price_cents: price, published: form.published });
      await Promise.all(form.categoryIds.map((id) => catalogueApi.attachCategory(product.id, id)));
      if (form.image) await addImage(product, form.image, 0);
      try {
        const warehouses = await inventoryApi.warehouses();
        const main = warehouses.find((warehouse) => warehouse.code === "MAIN");
        if (!main) throw new Error("Main Location is unavailable");
        const item = await inventoryApi.createStockItem({ product_id: product.id, variant_id: null, sku: product.sku, warehouse_id: main.id, low_stock_threshold: Number(form.lowStockThreshold), tracking_mode: form.trackingMode });
        if (opening > 0 && form.trackingMode === "SIMPLE") await inventoryApi.receiveSimpleStock(item.id, { quantity: opening, source_reference: form.reference.trim() || undefined, idempotency_key: idempotencyKey("opening-stock") });
        if (opening > 0 && form.trackingMode === "BATCH_EXPIRY") await inventoryApi.createBatch(item.id, { lot_number: form.lotNumber.trim(), quantity: opening, manufactured_on: form.manufacturedOn || undefined, expires_on: form.expiresOn || undefined, source_reference: form.reference.trim() || undefined, idempotency_key: idempotencyKey("opening-batch") });
      } catch (cause) {
        throw new Error(`${product.name} was created, but inventory setup needs attention. Open Inventory to retry. ${message(cause)}`);
      }
      setForm(blankForm); return `${product.name} was created and inventory tracking is ready.`;
    });
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!editing) return; const data = new FormData(event.currentTarget); const price = cents(String(data.get("price")));
    if (price === null) { setError("Enter a valid price."); return; }
    await execute(`edit-${editing.id}`, async () => {
      const name = String(data.get("name")).trim();
      await catalogueApi.updateProduct(editing.id, { name, description: String(data.get("description")).trim(), price_cents: price, published: data.get("published") === "on" });
      const selected = data.getAll("categories").map(String); const existing = new Set((assignments[editing.id] ?? []).map((item) => item.id));
      await Promise.all([...selected.filter((id) => !existing.has(id)).map((id) => catalogueApi.attachCategory(editing.id, id)), ...[...existing].filter((id) => !selected.includes(id)).map((id) => catalogueApi.detachCategory(editing.id, id))]);
      const file = data.get("image"); if (file instanceof File && file.size) await addImage(editing, file, (images[editing.id] ?? []).length);
      setEditing(null); return "Product changes saved.";
    });
  }

  async function remove(product: Product) {
    if (stock.some((item) => item.product_id === product.id)) { setError("Stock-tracked products cannot be deleted. Unpublish the product instead so order and inventory history remain safe."); return; }
    if (!window.confirm(`Delete ${product.name}?`)) return;
    await execute(`delete-${product.id}`, async () => { const assets = images[product.id] ?? []; await catalogueApi.deleteProduct(product.id); await Promise.all(assets.map(cleanImage)); return `${product.name} was deleted.`; });
  }
  async function removeImage(product: Product, image: ProductImage) {
    await execute(`image-${image.id}`, async () => { await catalogueApi.deleteProductImage(product.id, image.id); await cleanImage(image); return "Image removed."; });
  }
  async function addImage(product: Product, file: File, order: number) {
    const asset = await uploadProductImage(file);
    try { await catalogueApi.addProductImage(product.id, { url: asset.url, alt_text: product.name, sort_order: order }); }
    catch (cause) { await deleteUploadedImage(asset.id).catch(() => undefined); throw cause; }
  }

  if (loading) return <div className="loading-state">Loading products...</div>;
  return <div className="content-stack">
    {error && <div className="banner error-banner" role="alert">{error}<button onClick={() => setError("")} type="button">×</button></div>}{notice && <div className="banner success-banner" role="status">{notice}</div>}
    <section className="admin-card product-create-card"><div className="card-heading"><div><p className="eyebrow">NEW PRODUCT</p><h2>Product and opening stock</h2><p className="card-supporting-copy">One form prepares the storefront product and its Main Location inventory.</p></div></div><form className="admin-form product-create-form" onSubmit={create}>
      <label>Product name<input required maxLength={255} value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label>
      <label>SKU<input required maxLength={100} value={form.sku} placeholder="PARA-500-10" onChange={(event) => setForm({ ...form, sku: event.target.value.toUpperCase() })} /><small>Unique product code used for stock and orders.</small></label>
      <label>Price (INR)<input required type="number" min="0" step="0.01" value={form.price} onChange={(event) => setForm({ ...form, price: event.target.value })} /></label>
      <label>Opening stock<input required type="number" min="0" step="1" value={form.openingStock} onChange={(event) => setForm({ ...form, openingStock: event.target.value })} /></label>
      <label>Stock tracking<select value={form.trackingMode} onChange={(event) => setForm({ ...form, trackingMode: event.target.value as ProductForm["trackingMode"] })}><option value="SIMPLE">Simple quantity</option><option value="BATCH_EXPIRY">Batch and expiry</option></select></label>
      <label>Low-stock alert<input required type="number" min="0" step="1" value={form.lowStockThreshold} onChange={(event) => setForm({ ...form, lowStockThreshold: event.target.value })} /></label>
      {form.trackingMode === "BATCH_EXPIRY" && <><label>Opening lot number<input required={Number(form.openingStock) > 0} maxLength={120} value={form.lotNumber} onChange={(event) => setForm({ ...form, lotNumber: event.target.value })} /></label><label>Manufactured <em>Optional</em><input type="date" value={form.manufacturedOn} onChange={(event) => setForm({ ...form, manufacturedOn: event.target.value })} /></label><label>Expiry date <em>Recommended</em><input type="date" value={form.expiresOn} onChange={(event) => setForm({ ...form, expiresOn: event.target.value })} /></label></>}
      <label>Supplier reference <em>Optional</em><input maxLength={160} value={form.reference} onChange={(event) => setForm({ ...form, reference: event.target.value })} /></label>
      <label className="full-width">Description <em>Optional</em><textarea maxLength={2000} value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} /></label>
      <fieldset className="full-width"><legend>Categories</legend><div className="checkbox-grid">{categories.map((category) => <label className="checkbox-label" key={category.id}><input type="checkbox" checked={form.categoryIds.includes(category.id)} onChange={() => setForm({ ...form, categoryIds: form.categoryIds.includes(category.id) ? form.categoryIds.filter((id) => id !== category.id) : [...form.categoryIds, category.id] })} />{category.name}</label>)}</div></fieldset>
      <label className="full-width image-picker"><span>Primary image <em>Optional · JPEG, PNG or WebP · max 5 MB</em></span><input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => setForm({ ...form, image: event.target.files?.[0] ?? null })} /></label>
      <label className="publish-toggle"><input type="checkbox" checked={form.published} onChange={(event) => setForm({ ...form, published: event.target.checked })} /> Publish to storefront</label>
      <button className="primary-button" disabled={busy === "create-product"} type="submit"><Icon name="plus" /> {busy === "create-product" ? "Creating..." : "Create product"}</button>
    </form></section>
    <section className="admin-card"><div className="card-heading"><div><p className="eyebrow">CATALOGUE</p><h2>Products</h2></div><span className="count-pill">{products.length}</span></div>{!products.length ? <p className="empty-copy">No products yet.</p> : <div className="product-admin-grid">{products.map((product) => { const item = stock.find((entry) => entry.product_id === product.id); return <article className="product-admin-card" key={product.id}>{images[product.id]?.[0] ? <img src={mediaDisplayUrl(images[product.id][0].url)} alt={images[product.id][0].alt_text ?? product.name} /> : <div className="product-placeholder"><Icon name="box" /></div>}<div className="product-card-copy"><div className="product-status-row"><span className={product.published ? "status published" : "status draft"}>{product.published ? "Published" : "Draft"}</span><span className={`stock-chip${item && item.available <= item.low_stock_threshold ? " low" : ""}`}>{item ? `${item.available} available` : "Inventory setup needed"}</span></div><h3>{product.name}</h3><small>{product.sku}</small><strong>{formatMoney(product.price_cents)}</strong><div className="tags">{(assignments[product.id] ?? []).map((category) => <span key={category.id}>{category.name}</span>)}</div><div className="card-actions"><button className="secondary-button" onClick={() => setEditing(product)} type="button">Manage</button><button className="table-action" onClick={onOpenInventory} type="button">Add stock</button></div></div></article>; })}</div>}</section>
    {editing && <ProductEditor product={editing} categories={categories} assigned={assignments[editing.id] ?? []} images={images[editing.id] ?? []} busy={busy} close={() => setEditing(null)} save={save} remove={() => void remove(editing)} removeImage={(image) => void removeImage(editing, image)} />}
  </div>;
}

function ProductEditor({ product, categories, assigned, images, busy, close, save, remove, removeImage }: { product: Product; categories: Category[]; assigned: Category[]; images: ProductImage[]; busy: string; close: () => void; save: (event: FormEvent<HTMLFormElement>) => void; remove: () => void; removeImage: (image: ProductImage) => void }) {
  return <Modal title={`Manage ${product.name}`} eyebrow="PRODUCT DETAILS" close={close}><form className="admin-form editor-form" onSubmit={save}><label>Name<input name="name" required defaultValue={product.name} /></label><label>SKU<input value={product.sku} disabled /></label><label>Price (INR)<input name="price" required type="number" min="0" step="0.01" defaultValue={(product.price_cents / 100).toFixed(2)} /></label><label className="full-width">Description<textarea name="description" defaultValue={product.description ?? ""} /></label><fieldset className="full-width"><legend>Categories</legend><div className="checkbox-grid">{categories.map((category) => <label className="checkbox-label" key={category.id}><input name="categories" type="checkbox" value={category.id} defaultChecked={assigned.some((item) => item.id === category.id)} />{category.name}</label>)}</div></fieldset><label className="full-width image-picker"><span>Add another image</span><input name="image" type="file" accept="image/jpeg,image/png,image/webp" /></label>{images.length > 0 && <div className="full-width image-manager">{images.map((image) => <figure key={image.id}><img src={mediaDisplayUrl(image.url)} alt={image.alt_text ?? product.name} /><figcaption>{image.alt_text || "Product image"}</figcaption><button className="danger-button" type="button" onClick={() => removeImage(image)}>Remove</button></figure>)}</div>}<label className="publish-toggle"><input name="published" type="checkbox" defaultChecked={product.published} /> Published</label><div className="editor-actions"><button className="danger-button" onClick={remove} type="button">Delete product</button><span /><button className="secondary-button" onClick={close} type="button">Cancel</button><button className="primary-button" disabled={busy === `edit-${product.id}`} type="submit">Save changes</button></div></form></Modal>;
}

function cents(value: string): number | null { const amount = Math.round(Number(value) * 100); return Number.isFinite(amount) && amount >= 0 ? amount : null; }
function message(cause: unknown): string { return cause instanceof Error ? cause.message : "Product operation failed"; }
async function cleanImage(image: ProductImage): Promise<void> { const id = mediaAssetId(image.url); if (id) await deleteUploadedImage(id).catch(() => undefined); }
