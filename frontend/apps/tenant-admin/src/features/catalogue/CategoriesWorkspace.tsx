"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { Icon } from "@/components/Icon";
import { Modal } from "@/features/operations/Modal";
import { catalogueApi, Category, Product, slugify } from "@/lib/catalogue";

const blankForm = { name: "", description: "" };

export function CategoriesWorkspace() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [assignments, setAssignments] = useState<Record<string, Category[]>>({});
  const [form, setForm] = useState(blankForm);
  const [editing, setEditing] = useState<Category | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function load() {
    setLoading(true); setError("");
    try {
      const [nextCategories, nextProducts] = await Promise.all([catalogueApi.categories(), catalogueApi.products()]);
      const productCategories = await Promise.all(nextProducts.map(async (product) => [product.id, await catalogueApi.productCategories(product.id)] as const));
      setCategories(nextCategories); setProducts(nextProducts); setAssignments(Object.fromEntries(productCategories));
    } catch (cause) { setError(message(cause)); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, []);
  const visible = useMemo(() => new Set(products.filter((item) => item.published).flatMap((item) => (assignments[item.id] ?? []).map((category) => category.id))), [products, assignments]);

  async function execute(key: string, action: () => Promise<string>) {
    setBusy(key); setError(""); setNotice("");
    try { setNotice(await action()); await load(); }
    catch (cause) { setError(message(cause)); }
    finally { setBusy(""); }
  }
  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const name = form.name.trim(); const slug = slugify(name);
    if (!slug) { setError("Enter a category name containing letters or numbers."); return; }
    await execute("create", async () => { const category = await catalogueApi.createCategory({ name, slug, description: form.description.trim() || undefined }); setForm(blankForm); return `${category.name} was created.`; });
  }
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!editing) return; const data = new FormData(event.currentTarget);
    await execute(`edit-${editing.id}`, async () => { await catalogueApi.updateCategory(editing.id, { name: String(data.get("name")).trim(), description: String(data.get("description")).trim() }); setEditing(null); return "Category changes saved."; });
  }
  async function remove() {
    if (!editing || !window.confirm(`Delete ${editing.name}? Product assignments will be removed.`)) return;
    await execute(`delete-${editing.id}`, async () => { await catalogueApi.deleteCategory(editing.id); const name = editing.name; setEditing(null); return `${name} was deleted.`; });
  }

  if (loading) return <div className="loading-state">Loading categories...</div>;
  const preview = slugify(form.name);
  return <div className="content-stack">
    {error && <div className="banner error-banner" role="alert">{error}</div>}{notice && <div className="banner success-banner" role="status">{notice}</div>}
    <section className="admin-card simple-create-card"><div className="card-heading"><div><p className="eyebrow">NEW COLLECTION</p><h2>Create category</h2><p className="card-supporting-copy">The customer-facing URL is generated automatically from the name.</p></div></div><form className="admin-form simplified-category-form" onSubmit={create}><label>Category name<input required maxLength={120} value={form.name} placeholder="Baby Wellness" onChange={(event) => setForm({ ...form, name: event.target.value })} /><small className="generated-url-note">Store URL: /categories/{preview || "category-name"}</small></label><label className="full-width">Description <em>Optional</em><textarea maxLength={2000} value={form.description} placeholder="Help customers understand what they will find here." onChange={(event) => setForm({ ...form, description: event.target.value })} /></label><button className="primary-button" disabled={busy === "create"} type="submit"><Icon name="plus" /> Create category</button></form></section>
    <section className="admin-card"><div className="card-heading"><div><p className="eyebrow">STOREFRONT NAVIGATION</p><h2>Categories</h2></div><span className="count-pill">{categories.length}</span></div>{!categories.length ? <p className="empty-copy">No categories yet.</p> : <div className="category-admin-grid">{categories.map((category) => <article key={category.id}><span className="category-initial">{category.name.slice(0, 2).toUpperCase()}</span><div><h3>{category.name}</h3><p>{category.description || "No description"}</p><small>/categories/{category.slug}</small></div><span className={visible.has(category.id) ? "visibility live" : "visibility hidden"}>{visible.has(category.id) ? "Visible in storefront" : "Hidden until a published product is assigned"}</span><button className="table-action category-edit" onClick={() => setEditing(category)} type="button">Edit</button></article>)}</div>}</section>
    {editing && <Modal title={`Edit ${editing.name}`} eyebrow="CATEGORY DETAILS" close={() => setEditing(null)} small><p className="editor-url-note">Store URL: /categories/{editing.slug}</p><form className="admin-form editor-form" onSubmit={save}><label className="full-width">Category name<input name="name" required maxLength={120} defaultValue={editing.name} /></label><label className="full-width">Description <em>Optional</em><textarea name="description" maxLength={2000} defaultValue={editing.description ?? ""} /></label><div className="editor-actions"><button className="danger-button" onClick={() => void remove()} type="button">Delete category</button><span /><button className="secondary-button" onClick={() => setEditing(null)} type="button">Cancel</button><button className="primary-button" disabled={busy === `edit-${editing.id}`} type="submit">Save changes</button></div></form></Modal>}
  </div>;
}

function message(cause: unknown): string { return cause instanceof Error ? cause.message : "Category operation failed"; }
