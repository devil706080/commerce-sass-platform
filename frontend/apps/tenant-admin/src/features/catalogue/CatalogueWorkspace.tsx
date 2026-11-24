"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { Icon } from "@/components/Icon";
import { catalogueApi, Category, deleteUploadedImage, formatMoney, mediaAssetId, mediaDisplayUrl, Product, ProductImage, slugify, uploadProductImage } from "@/lib/catalogue";
import { getKeycloak } from "@/lib/keycloak";
import { useTenantBrand } from "@/features/tenant/TenantBrandProvider";

type View = "overview" | "products" | "categories";
type MapOf<T> = Record<string, T>;
type ProductForm = { sku: string; name: string; description: string; price: string; published: boolean; categoryIds: string[]; image: File | null };
const blankProduct: ProductForm = { sku: "", name: "", description: "", price: "", published: false, categoryIds: [], image: null };
const blankCategory = { name: "", slug: "", description: "" };

export function CatalogueWorkspace() {
  const brand = useTenantBrand();
  const [view, setView] = useState<View>("overview");
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [assignments, setAssignments] = useState<MapOf<Category[]>>({});
  const [images, setImages] = useState<MapOf<ProductImage[]>>({});
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [productForm, setProductForm] = useState<ProductForm>(blankProduct);
  const [categoryForm, setCategoryForm] = useState(blankCategory);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);

  async function load() {
    setLoading(true); setError("");
    try {
      const [nextProducts, nextCategories] = await Promise.all([catalogueApi.products(), catalogueApi.categories()]);
      const details = await Promise.all(nextProducts.map(async (product) => ({ id: product.id, categories: await catalogueApi.productCategories(product.id), images: await catalogueApi.productImages(product.id) })));
      setProducts(nextProducts); setCategories(nextCategories);
      setAssignments(Object.fromEntries(details.map((item) => [item.id, item.categories])));
      setImages(Object.fromEntries(details.map((item) => [item.id, item.images])));
    } catch (cause) { setError(errorMessage(cause, "Unable to load catalogue")); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, []);

  async function execute(key: string, action: () => Promise<string>) {
    setBusy(key); setError(""); setNotice("");
    try { setNotice(await action()); await load(); }
    catch (cause) { setError(errorMessage(cause, "Catalogue operation failed")); }
    finally { setBusy(""); }
  }

  async function createProduct(event: FormEvent) {
    event.preventDefault();
    const price = priceCents(productForm.price);
    if (price === null) { setError("Enter a valid non-negative price."); return; }
    await execute("create-product", async () => {
      const product = await catalogueApi.createProduct({ sku: productForm.sku.trim(), name: productForm.name.trim(), description: productForm.description.trim() || undefined, price_cents: price, published: productForm.published });
      await Promise.all(productForm.categoryIds.map((id) => catalogueApi.attachCategory(product.id, id)));
      if (productForm.image) {
        const asset = await uploadProductImage(productForm.image);
        try { await catalogueApi.addProductImage(product.id, { url: asset.url, alt_text: product.name, sort_order: 0 }); }
        catch (cause) { await deleteUploadedImage(asset.id).catch(() => undefined); throw cause; }
      }
      setProductForm(blankProduct); return `${product.name} was created.`;
    });
  }

  async function saveProduct(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!editingProduct) return;
    const data = new FormData(event.currentTarget); const price = priceCents(String(data.get("price")));
    if (price === null) { setError("Enter a valid non-negative price."); return; }
    const selected = data.getAll("categories").map(String);
    await execute(`product-${editingProduct.id}`, async () => {
      const name = String(data.get("name")).trim();
      await catalogueApi.updateProduct(editingProduct.id, { name, description: String(data.get("description")).trim(), price_cents: price, published: data.get("published") === "on" });
      const existing = new Set((assignments[editingProduct.id] ?? []).map((item) => item.id));
      await Promise.all([...selected.filter((id) => !existing.has(id)).map((id) => catalogueApi.attachCategory(editingProduct.id, id)), ...[...existing].filter((id) => !selected.includes(id)).map((id) => catalogueApi.detachCategory(editingProduct.id, id))]);
      const file = data.get("image");
      if (file instanceof File && file.size) {
        const asset = await uploadProductImage(file);
        try { await catalogueApi.addProductImage(editingProduct.id, { url: asset.url, alt_text: name, sort_order: (images[editingProduct.id] ?? []).length }); }
        catch (cause) { await deleteUploadedImage(asset.id).catch(() => undefined); throw cause; }
      }
      setEditingProduct(null); return "Product changes saved.";
    });
  }

  async function removeProduct(product: Product) {
    if (!window.confirm(`Delete ${product.name}? This cannot be undone.`)) return;
    await execute(`delete-${product.id}`, async () => {
      const media = images[product.id] ?? []; await catalogueApi.deleteProduct(product.id);
      await Promise.all(media.map((image) => { const id = mediaAssetId(image.url); return id ? deleteUploadedImage(id).catch(() => undefined) : Promise.resolve(); }));
      setEditingProduct(null); return `${product.name} was deleted.`;
    });
  }

  async function removeImage(product: Product, image: ProductImage) {
    if (!window.confirm("Remove this image?")) return;
    await execute(`image-${image.id}`, async () => {
      await catalogueApi.deleteProductImage(product.id, image.id); const id = mediaAssetId(image.url); if (id) await deleteUploadedImage(id).catch(() => undefined);
      return "Product image removed.";
    });
  }

  async function createCategory(event: FormEvent) {
    event.preventDefault();
    await execute("create-category", async () => { const item = await catalogueApi.createCategory({ name: categoryForm.name.trim(), slug: categoryForm.slug.trim(), description: categoryForm.description.trim() || undefined }); setCategoryForm(blankCategory); return `${item.name} was created.`; });
  }
  async function saveCategory(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!editingCategory) return; const data = new FormData(event.currentTarget);
    await execute(`category-${editingCategory.id}`, async () => { await catalogueApi.updateCategory(editingCategory.id, { name: String(data.get("name")).trim(), description: String(data.get("description")).trim() }); setEditingCategory(null); return "Category changes saved."; });
  }
  async function removeCategory(category: Category) {
    if (!window.confirm(`Delete ${category.name}? Products remain but assignments are removed.`)) return;
    await execute(`delete-category-${category.id}`, async () => { await catalogueApi.deleteCategory(category.id); setEditingCategory(null); return `${category.name} was deleted.`; });
  }

  const published = useMemo(() => products.filter((item) => item.published).length, [products]);
  const nav: { id: View; label: string; icon: "chart" | "box" | "tag" }[] = [{ id: "overview", label: "Overview", icon: "chart" }, { id: "products", label: "Products", icon: "box" }, { id: "categories", label: "Categories", icon: "tag" }];
  return <div className="admin-shell"><aside className="admin-sidebar"><div className="sidebar-brand"><span className="admin-mark">{brand.fallbackInitials}</span><div><strong>{brand.displayName}</strong><small>Commerce operations</small></div></div><nav>{nav.map((item) => <button className={view === item.id ? "active" : ""} key={item.id} onClick={() => setView(item.id)} type="button"><Icon name={item.icon} />{item.label}</button>)}</nav><div className="sidebar-footer"><span><Icon name="user" /> Authorised tenant staff</span><button onClick={() => void getKeycloak().logout({ redirectUri: window.location.origin })} type="button"><Icon name="logout" /> Sign out</button></div></aside><main className="admin-main"><header className="admin-header"><div><p className="eyebrow">TENANT CATALOGUE</p><h1>{view === "overview" ? "Catalogue overview" : view === "products" ? "Products" : "Categories"}</h1><p>Manage only {brand.displayName}&apos;s customer-facing catalogue.</p></div><button className="refresh-button" onClick={() => void load()} disabled={loading || Boolean(busy)} type="button"><Icon name="refresh" /> Refresh</button></header>{error && <div className="banner error-banner" role="alert">{error}</div>}{notice && <div className="banner success-banner" role="status">{notice}</div>}{loading ? <div className="loading-state">Loading tenant catalogue...</div> : view === "overview" ? <Overview products={products.length} published={published} categories={categories.length} setView={setView} /> : view === "products" ? <Products products={products} categories={categories} assignments={assignments} images={images} form={productForm} setForm={setProductForm} submit={createProduct} edit={setEditingProduct} remove={removeProduct} busy={busy} /> : <Categories categories={categories} products={products} assignments={assignments} form={categoryForm} setForm={setCategoryForm} submit={createCategory} edit={setEditingCategory} busy={busy} />}</main>{editingProduct && <ProductEditor product={editingProduct} categories={categories} assigned={assignments[editingProduct.id] ?? []} images={images[editingProduct.id] ?? []} busy={busy} close={() => setEditingProduct(null)} save={saveProduct} remove={() => void removeProduct(editingProduct)} removeImage={(image) => void removeImage(editingProduct, image)} />}{editingCategory && <CategoryEditor category={editingCategory} busy={busy} close={() => setEditingCategory(null)} save={saveCategory} remove={() => void removeCategory(editingCategory)} />}</div>;
}

function Overview({ products, published, categories, setView }: { products: number; published: number; categories: number; setView: (view: View) => void }) { return <><section className="metric-grid"><Metric label="Products" value={products} note="Tenant catalogue items" icon="box" /><Metric label="Published" value={published} note="Customer-visible" icon="chart" /><Metric label="Drafts" value={products - published} note="Awaiting publication" icon="grid" /><Metric label="Categories" value={categories} note="Storefront collections" icon="tag" /></section><section className="admin-card workflow-card"><div><p className="eyebrow">PUBLISHING WORKFLOW</p><h2>Storefront-ready catalogue</h2><p>Categories appear only after a published product is assigned, preventing empty storefront navigation.</p></div><ol><li><span>1</span>Create category</li><li><span>2</span>Add product and media</li><li><span>3</span>Review and publish</li></ol><div className="workflow-actions"><button className="primary-button" onClick={() => setView("products")} type="button"><Icon name="plus" /> Add product</button><button className="secondary-button" onClick={() => setView("categories")} type="button">Categories</button></div></section></>; }
function Metric({ label, value, note, icon }: { label: string; value: number; note: string; icon: "box" | "chart" | "grid" | "tag" }) { return <article className="metric"><span><Icon name={icon} /></span><p>{label}</p><strong>{value}</strong><small>{note}</small></article>; }

function Products({ products, categories, assignments, images, form, setForm, submit, edit, remove, busy }: { products: Product[]; categories: Category[]; assignments: MapOf<Category[]>; images: MapOf<ProductImage[]>; form: ProductForm; setForm: (value: ProductForm) => void; submit: (event: FormEvent) => void; edit: (item: Product) => void; remove: (item: Product) => void; busy: string }) { return <div className="content-stack"><section className="admin-card"><div className="card-heading"><div><p className="eyebrow">NEW CATALOGUE ITEM</p><h2>Add product</h2></div></div><form className="admin-form" onSubmit={submit}><label>Name<input required maxLength={255} value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label><label>SKU<input required maxLength={100} value={form.sku} onChange={(event) => setForm({ ...form, sku: event.target.value })} /></label><label>Price (INR)<input required type="number" min="0" step="0.01" value={form.price} onChange={(event) => setForm({ ...form, price: event.target.value })} /></label><label className="full-width image-picker"><span>Product image <em>Optional - JPEG, PNG or WebP - max 5 MB</em></span><input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => setForm({ ...form, image: event.target.files?.[0] ?? null })} /></label><label className="full-width">Description<textarea maxLength={2000} value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} /></label><CategoryChecks categories={categories} selected={form.categoryIds} change={(ids) => setForm({ ...form, categoryIds: ids })} /><label className="publish-toggle"><input type="checkbox" checked={form.published} onChange={(event) => setForm({ ...form, published: event.target.checked })} /> Publish now</label><button className="primary-button" disabled={busy === "create-product"} type="submit"><Icon name="plus" />{busy === "create-product" ? "Creating..." : "Create product"}</button></form></section><section className="admin-card"><div className="card-heading"><div><p className="eyebrow">CATALOGUE</p><h2>All products</h2></div><span className="count-pill">{products.length}</span></div>{products.length === 0 ? <p className="empty-copy">No products yet.</p> : <div className="product-admin-grid">{products.map((product) => <article className="product-admin-card" key={product.id}>{images[product.id]?.[0] ? <img src={mediaDisplayUrl(images[product.id][0].url)} alt={images[product.id][0].alt_text ?? product.name} /> : <div className="product-placeholder"><Icon name="box" /></div>}<div className="product-card-copy"><span className={product.published ? "status published" : "status draft"}>{product.published ? "Published" : "Draft"}</span><h3>{product.name}</h3><small>{product.sku}</small><strong>{formatMoney(product.price_cents)}</strong><div className="tags">{(assignments[product.id] ?? []).map((category) => <span key={category.id}>{category.name}</span>)}</div><div className="card-actions"><button className="secondary-button" onClick={() => edit(product)} type="button">Edit</button><button className="danger-button" onClick={() => void remove(product)} type="button">Delete</button></div></div></article>)}</div>}</section></div>; }

function Categories({ categories, products, assignments, form, setForm, submit, edit, busy }: { categories: Category[]; products: Product[]; assignments: MapOf<Category[]>; form: typeof blankCategory; setForm: (value: typeof blankCategory) => void; submit: (event: FormEvent) => void; edit: (item: Category) => void; busy: string }) { const live = new Set(products.filter((item) => item.published).flatMap((item) => (assignments[item.id] ?? []).map((category) => category.id))); return <div className="content-stack"><section className="admin-card"><div className="card-heading"><div><p className="eyebrow">STOREFRONT COLLECTION</p><h2>Create category</h2></div></div><form className="admin-form category-form" onSubmit={submit}><label>Name<input required maxLength={120} value={form.name} onChange={(event) => { const name = event.target.value; setForm({ ...form, name, slug: form.slug || slugify(name) }); }} /></label><label>URL slug<input required maxLength={120} pattern="[a-z0-9]+(-[a-z0-9]+)*" value={form.slug} onChange={(event) => setForm({ ...form, slug: slugify(event.target.value) })} /></label><label className="full-width">Description<textarea maxLength={2000} value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} /></label><button className="primary-button" disabled={busy === "create-category"} type="submit"><Icon name="plus" /> Create category</button></form></section><section className="admin-card"><div className="category-admin-grid">{categories.map((category) => <article key={category.id}><span className="category-initial">{category.name.slice(0, 2).toUpperCase()}</span><div><h3>{category.name}</h3><p>{category.description || "No description"}</p><small>/{category.slug}</small></div><span className={live.has(category.id) ? "visibility live" : "visibility hidden"}>{live.has(category.id) ? "Visible in storefront" : "Hidden until product is published"}</span><button className="table-action category-edit" onClick={() => edit(category)} type="button">Edit</button></article>)}</div></section></div>; }

function ProductEditor({ product, categories, assigned, images, busy, close, save, remove, removeImage }: { product: Product; categories: Category[]; assigned: Category[]; images: ProductImage[]; busy: string; close: () => void; save: (event: FormEvent<HTMLFormElement>) => void; remove: () => void; removeImage: (image: ProductImage) => void }) { return <Modal close={close}><div className="editor-heading"><div><p className="eyebrow">PRODUCT DETAILS</p><h2>Edit {product.name}</h2></div><button className="close-button" onClick={close} type="button" aria-label="Close">x</button></div><form className="admin-form editor-form" onSubmit={save}><label>Name<input name="name" required defaultValue={product.name} /></label><label>SKU<input value={product.sku} disabled /></label><label>Price (INR)<input name="price" required type="number" min="0" step="0.01" defaultValue={(product.price_cents / 100).toFixed(2)} /></label><label className="full-width">Description<textarea name="description" defaultValue={product.description ?? ""} /></label><fieldset className="full-width"><legend>Categories</legend><div className="checkbox-grid">{categories.map((category) => <label className="checkbox-label" key={category.id}><input name="categories" type="checkbox" value={category.id} defaultChecked={assigned.some((item) => item.id === category.id)} />{category.name}</label>)}</div></fieldset><label className="full-width image-picker"><span>Add image</span><input name="image" type="file" accept="image/jpeg,image/png,image/webp" /></label>{images.length > 0 && <div className="full-width image-manager">{images.map((image) => <figure key={image.id}><img src={mediaDisplayUrl(image.url)} alt={image.alt_text ?? product.name} /><figcaption>{image.alt_text || "Product image"}</figcaption><button className="danger-button" type="button" onClick={() => removeImage(image)}>Remove</button></figure>)}</div>}<label className="publish-toggle"><input name="published" type="checkbox" defaultChecked={product.published} /> Published</label><div className="editor-actions"><button className="danger-button" onClick={remove} type="button">Delete product</button><span /><button className="secondary-button" onClick={close} type="button">Cancel</button><button className="primary-button" disabled={busy === `product-${product.id}`} type="submit">Save changes</button></div></form></Modal>; }
function CategoryEditor({ category, busy, close, save, remove }: { category: Category; busy: string; close: () => void; save: (event: FormEvent<HTMLFormElement>) => void; remove: () => void }) { return <Modal close={close} small><div className="editor-heading"><div><p className="eyebrow">CATEGORY DETAILS</p><h2>Edit category</h2></div><button className="close-button" onClick={close} type="button">x</button></div><form className="admin-form editor-form" onSubmit={save}><label>Name<input name="name" required defaultValue={category.name} /></label><label>URL slug<input value={category.slug} disabled /></label><label className="full-width">Description<textarea name="description" defaultValue={category.description ?? ""} /></label><div className="editor-actions"><button className="danger-button" onClick={remove} type="button">Delete category</button><span /><button className="secondary-button" onClick={close} type="button">Cancel</button><button className="primary-button" disabled={busy === `category-${category.id}`} type="submit">Save changes</button></div></form></Modal>; }
function Modal({ close, small, children }: { close: () => void; small?: boolean; children: React.ReactNode }) { return <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) close(); }}><section className={`editor-panel${small ? " small-editor" : ""}`} role="dialog" aria-modal="true">{children}</section></div>; }
function CategoryChecks({ categories, selected, change }: { categories: Category[]; selected: string[]; change: (ids: string[]) => void }) { return <fieldset className="full-width"><legend>Categories</legend><div className="checkbox-grid">{categories.map((category) => <label className="checkbox-label" key={category.id}><input type="checkbox" checked={selected.includes(category.id)} onChange={() => change(selected.includes(category.id) ? selected.filter((id) => id !== category.id) : [...selected, category.id])} />{category.name}</label>)}</div></fieldset>; }
function priceCents(value: string): number | null { const amount = Math.round(Number(value) * 100); return Number.isFinite(amount) && amount >= 0 ? amount : null; }
function errorMessage(cause: unknown, fallback: string) { return cause instanceof Error ? cause.message : fallback; }
