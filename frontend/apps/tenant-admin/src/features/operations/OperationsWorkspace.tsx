"use client";

import { useState } from "react";
import { Icon } from "@/components/Icon";
import { CategoriesWorkspace } from "@/features/catalogue/CategoriesWorkspace";
import { ProductsWorkspace } from "@/features/catalogue/ProductsWorkspace";
import { DashboardWorkspace } from "@/features/dashboard/DashboardWorkspace";
import { InventoryWorkspace } from "@/features/inventory/InventoryWorkspace";
import { useTenantBrand } from "@/features/tenant/TenantBrandProvider";
import { getKeycloak } from "@/lib/keycloak";

type View = "dashboard" | "products" | "categories" | "inventory";
const navigation: { id: View; label: string; icon: "chart" | "box" | "tag" | "grid" }[] = [
  { id: "dashboard", label: "Dashboard", icon: "chart" },
  { id: "products", label: "Products", icon: "box" },
  { id: "categories", label: "Categories", icon: "tag" },
  { id: "inventory", label: "Inventory", icon: "grid" },
];

export function OperationsWorkspace() {
  const brand = useTenantBrand();
  const [view, setView] = useState<View>("dashboard");
  const titles: Record<View, [string, string]> = {
    dashboard: ["Business overview", "Real catalogue and stock information for today."],
    products: ["Products", "Create products and prepare them for sale in one workflow."],
    categories: ["Categories", "Organise products into customer-friendly storefront collections."],
    inventory: ["Inventory", "Add stock, review availability and manage expiry exceptions."],
  };

  return <div className="admin-shell">
    <aside className="admin-sidebar">
      <div className="sidebar-brand"><span className="admin-mark">{brand.fallbackInitials}</span><div><strong>{brand.displayName}</strong><small>Commerce operations</small></div></div>
      <nav>{navigation.map((item) => <button className={view === item.id ? "active" : ""} key={item.id} onClick={() => setView(item.id)} type="button"><Icon name={item.icon} />{item.label}</button>)}</nav>
      <div className="sidebar-coming-soon"><span>COMING SOON</span><p>Orders, customers and payments will appear as their services are completed.</p></div>
      <div className="sidebar-footer"><span><Icon name="user" /> Authorised tenant staff</span><button onClick={() => void getKeycloak().logout({ redirectUri: window.location.origin })} type="button"><Icon name="logout" /> Sign out</button></div>
    </aside>
    <main className="admin-main">
      <header className="admin-header"><div><p className="eyebrow">TENANT OPERATIONS</p><h1>{titles[view][0]}</h1><p>{titles[view][1]}</p></div></header>
      {view === "dashboard" && <DashboardWorkspace onNavigate={setView} />}
      {view === "products" && <ProductsWorkspace onOpenInventory={() => setView("inventory")} />}
      {view === "categories" && <CategoriesWorkspace />}
      {view === "inventory" && <InventoryWorkspace />}
    </main>
  </div>;
}
