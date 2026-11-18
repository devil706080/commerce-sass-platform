"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { Icon } from "@/components/Icon";
import { catalogueApi, Category, formatMoney, Product, slugify, uploadProductImage } from "@/lib/catalogue";
import { getKeycloak } from "@/lib/keycloak";
import { tenantAdminBrand } from "@/lib/brand";

type View = "overview" | "products" | "categories";
type ProductCategories = Record<string, Category[]>;
const blankProduct = { sku: "", name: "", description: "", price: "", published: false, categoryIds: [] as string[], image: null as File | null };

export function CatalogueWorkspace() {
  const [view, setView] = useState<View>("overview");
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [productCategories, setProductCategories] = useState<ProductCategories>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [productForm, setProductForm] = useState(blankProduct);
  const [categoryForm, setCategoryForm] = useState({ name: "", slug: "", description: "" });

  async function load() {
    setLoading(true); setError("");
    try {
      const [loadedProducts, loadedCategories] = await Promise.all([catalogueApi.products(), catalogueApi.categories()]);
      const assignments = await Promise.all(loadedProducts.map(async (product) => [product.id, await catalogueApi.productCategories(product.id)] as const));
      setProducts(loadedProducts); setCategories(loadedCategories); setProductCategories(Object.fromEntries(assignments));
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to load catalogue data"); }
    finally { setLoading(false); }
  }

  useEffect(() => { void load(); }, []);
  const published = useMemo(() => products.filter((product) => product.published).length, [products]);

  async function createProduct(event: FormEvent) {
    event.preventDefault(); setError(""); setNotice("");
    const priceCents = Math.round(Number(productForm.price) * 100);
    if (!Number.isFinite(priceCents) || priceCents < 0) { setError("Enter a valid non-negative price."); return; }
    try {
      const product = await catalogueApi.createProduct({ sku: productForm.sku.trim(), name: productForm.name.trim(), description: productForm.description.trim() || undefined, price_cents: priceCents, published: productForm.published });
      await Promise.all(productForm.categoryIds.map((categoryId) => catalogueApi.attachCategory(product.id, categoryId)));
      if (productForm.image) {
        const uploaded = await uploadProductImage(productForm.image);
        await catalogueApi.addProductImage(product.id, { url: uploaded.url, alt_text: product.name, sort_order: 0 });
      }
      setProductForm(blankProduct); setNotice(`“${product.name}” was created.`); await load();
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to create product"); }
  }

  async function togglePublication(product: Product) {
    setError(""); setNotice("");
    try { await catalogueApi.updateProduct(product.id, { published: !product.published }); setNotice(`“${product.name}” is now ${product.published ? "a draft" : "published"}.`); await load(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to update product"); }
  }

  async function createCategory(event: FormEvent) {
    event.preventDefault(); setError(""); setNotice("");
    try { const category = await catalogueApi.createCategory({ name: categoryForm.name.trim(), slug: categoryForm.slug.trim(), description: categoryForm.description.trim() || undefined }); setCategoryForm({ name: "", slug: "", description: "" }); setNotice(`“${category.name}” was created. It becomes visible in the storefront after a published product is assigned.`); await load(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to create category"); }
  }

  async function signOut() { await getKeycloak().logout({ redirectUri: window.location.origin }); }
  const navigation: { id: View; label: string; icon: "chart" | "box" | "tag" }[] = [{ id: "overview", label: "Overview", icon: "chart" }, { id: "products", label: "Products", icon: "box" }, { id: "categories", label: "Categories", icon: "tag" }];

  return <div className="admin-shell"><aside className="admin-sidebar"><div className="sidebar-brand"><span className="admin-mark">A</span><div><strong>{tenantAdminBrand.name}</strong><small>Catalogue workspace</small></div></div><nav>{navigation.map((item) => <button className={view === item.id ? "active" : ""} key={item.id} onClick={() => setView(item.id)} type="button"><Icon name={item.icon} />{item.label}</button>)}</nav><div className="sidebar-footer"><span><Icon name="user" /> Authorised tenant staff</span><button onClick={() => void signOut()} type="button"><Icon name="logout" /> Sign out</button></div></aside><main className="admin-main"><header className="admin-header"><div><p className="eyebrow">TENANT CATALOGUE</p><h1>{view === "overview" ? "Good to see you" : view === "products" ? "Products" : "Categories"}</h1><p>{view === "overview" ? "Keep customer-facing catalogue data accurate and published." : view === "products" ? "Create, publish, and assign products to categories." : "Create custom collections for your storefront."}</p></div><button className="refresh-button" onClick={() => void load()} type="button" disabled={loading}><Icon name="refresh" /> Refresh</button></header>{error && <div className="banner error-banner" role="alert">{error}</div>}{notice && <div className="banner success-banner">{notice}</div>}{loading ? <div className="loading-state">Loading tenant catalogue…</div> : view === "overview" ? <Overview products={products} categories={categories} published={published} setView={setView} /> : view === "products" ? <Products products={products} categories={categories} assignments={productCategories} form={productForm} setForm={setProductForm} onSubmit={createProduct} onToggle={togglePublication} /> : <Categories categories={categories} products={products} assignments={productCategories} form={categoryForm} setForm={setCategoryForm} onSubmit={createCategory} />}</main></div>;
}

function Overview({ products, categories, published, setView }: { products: Product[]; categories: Category[]; published: number; setView: (view: View) => void }) { return <><section className="metric-grid"><Metric label="Products" value={products.length} note="Created in this tenant" icon="box" /><Metric label="Published" value={published} note="Visible through public API" icon="chart" /><Metric label="Drafts" value={products.length - published} note="Not customer-visible" icon="grid" /><Metric label="Categories" value={categories.length} note="Custom collections" icon="tag" /></section><section className="admin-card workflow-card"><div><p className="eyebrow">HOW STOREFRONT VISIBILITY WORKS</p><h2>Publish with confidence</h2><p>A category reaches the storefront only when it contains at least one published product. This prevents empty navigation links and lets every tenant design its own catalogue.</p></div><ol><li><span>1</span>Create a category</li><li><span>2</span>Add a product and assign it</li><li><span>3</span>Publish the product</li></ol><div className="workflow-actions"><button className="primary-button" onClick={() => setView("categories")} type="button"><Icon name="plus" /> New category</button><button className="secondary-button" onClick={() => setView("products")} type="button">Add product</button></div></section></> }
function Metric({ label, value, note, icon }: { label: string; value: number; note: string; icon: "box" | "chart" | "grid" | "tag" }) { return <article className="metric"><span><Icon name={icon} /></span><p>{label}</p><strong>{value}</strong><small>{note}</small></article>; }
function Products({ products, categories, assignments, form, setForm, onSubmit, onToggle }: { products: Product[]; categories: Category[]; assignments: ProductCategories; form: typeof blankProduct; setForm: (value: typeof blankProduct) => void; onSubmit: (event: FormEvent) => void; onToggle: (product: Product) => void }) { return <div className="content-stack"><section className="admin-card"><div className="card-heading"><div><p className="eyebrow">NEW CATALOGUE ITEM</p><h2>Add product</h2></div></div><form className="admin-form" onSubmit={onSubmit}><label>Product name<input required maxLength={255} value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="e.g. Daily wellness supplement" /></label><label>SKU<input required maxLength={100} value={form.sku} onChange={(event) => setForm({ ...form, sku: event.target.value })} placeholder="e.g. WELL-001" /></label><label>Price (INR)<input required type="number" min="0" step="0.01" value={form.price} onChange={(event) => setForm({ ...form, price: event.target.value })} placeholder="0.00" /></label><label className="full-width image-picker"><span>Product image <em>Optional · JPEG, PNG, or WebP · max 5 MB</em></span><input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => setForm({ ...form, image: event.target.files?.[0] ?? null })} />{form.image && <strong>Ready to upload: {form.image.name}</strong>}</label><label className="full-width">Description<textarea maxLength={2000} value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} placeholder="Customer-facing product information" /></label><fieldset className="full-width"><legend>Categories</legend><div className="checkbox-grid">{categories.length === 0 ? <p>Create a category first.</p> : categories.map((category) => <label key={category.id} className="checkbox-label"><input type="checkbox" checked={form.categoryIds.includes(category.id)} onChange={() => setForm({ ...form, categoryIds: form.categoryIds.includes(category.id) ? form.categoryIds.filter((id) => id !== category.id) : [...form.categoryIds, category.id] })} />{category.name}</label>)}</div></fieldset><label className="publish-toggle"><input type="checkbox" checked={form.published} onChange={(event) => setForm({ ...form, published: event.target.checked })} /> Publish now <small>Only published products can reach the storefront.</small></label><button className="primary-button" type="submit"><Icon name="plus" /> Create product</button></form></section><section className="admin-card"><div className="card-heading"><div><p className="eyebrow">CATALOGUE</p><h2>All products</h2></div><span className="count-pill">{products.length}</span></div>{products.length === 0 ? <p className="empty-copy">No products yet. Create your first product above.</p> : <div className="table-wrap"><table><thead><tr><th>Product</th><th>Categories</th><th>Price</th><th>Storefront</th><th /></tr></thead><tbody>{products.map((product) => <tr key={product.id}><td><strong>{product.name}</strong><small>{product.sku}</small></td><td><div className="tags">{(assignments[product.id] ?? []).map((category) => <span key={category.id}>{category.name}</span>)}{(assignments[product.id] ?? []).length === 0 && <small>Unassigned</small>}</div></td><td>{formatMoney(product.price_cents)}</td><td><span className={product.published ? "status published" : "status draft"}>{product.published ? "Published" : "Draft"}</span></td><td><button className="table-action" type="button" onClick={() => void onToggle(product)}>{product.published ? "Unpublish" : "Publish"}</button></td></tr>)}</tbody></table></div>}</section></div> }
function Categories({ categories, products, assignments, form, setForm, onSubmit }: { categories: Category[]; products: Product[]; assignments: ProductCategories; form: { name: string; slug: string; description: string }; setForm: (value: { name: string; slug: string; description: string }) => void; onSubmit: (event: FormEvent) => void }) { const visibleCategoryIds = new Set(products.filter((product) => product.published).flatMap((product) => (assignments[product.id] ?? []).map((category) => category.id))); return <div className="content-stack"><section className="admin-card"><div className="card-heading"><div><p className="eyebrow">STOREFRONT COLLECTION</p><h2>Create category</h2></div></div><form className="admin-form category-form" onSubmit={onSubmit}><label>Category name<input required maxLength={120} value={form.name} onChange={(event) => { const name = event.target.value; setForm({ ...form, name, slug: form.slug || slugify(name) }); }} placeholder="e.g. Women's wellness" /></label><label>URL slug<input required maxLength={120} pattern="[a-z0-9]+(-[a-z0-9]+)*" value={form.slug} onChange={(event) => setForm({ ...form, slug: slugify(event.target.value) })} placeholder="womens-wellness" /></label><label className="full-width">Description<textarea maxLength={2000} value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} placeholder="Optional collection description" /></label><button className="primary-button" type="submit"><Icon name="plus" /> Create category</button></form></section><section className="admin-card"><div className="card-heading"><div><p className="eyebrow">YOUR CATEGORY SYSTEM</p><h2>Customer visibility</h2></div></div>{categories.length === 0 ? <p className="empty-copy">No custom categories yet.</p> : <div className="category-admin-grid">{categories.map((category) => <article key={category.id}><span className="category-initial">{category.name.slice(0, 2).toUpperCase()}</span><div><h3>{category.name}</h3><p>{category.description || "No description"}</p><small>/{category.slug}</small></div><span className={visibleCategoryIds.has(category.id) ? "visibility live" : "visibility hidden"}>{visibleCategoryIds.has(category.id) ? "Visible in storefront" : "Hidden until published product assigned"}</span></article>)}</div>}</section></div> }
