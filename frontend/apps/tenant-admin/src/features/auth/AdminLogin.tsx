"use client";

import { useEffect, useState } from "react";
import { Icon } from "@/components/Icon";
import { getAccessToken, getKeycloak, hasTenantAdminRole } from "@/lib/keycloak";
import { useTenantBrand } from "@/features/tenant/TenantBrandProvider";

export type AuthState = "checking" | "guest" | "authorized" | "denied" | "error";

export function AdminLogin({ onState }: { onState: (state: AuthState) => void }) {
  const tenantBrand = useTenantBrand();
  const [state, setState] = useState<AuthState>("checking");
  const [message, setMessage] = useState("");
  function update(next: AuthState) { setState(next); onState(next); }

  async function verifyTenantMembership(): Promise<AuthState> {
    if (!hasTenantAdminRole()) return "denied";
    const token = await getAccessToken();
    const response = await fetch("/api/tenant/identity/api/v1/me", {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (response.ok) return "authorized";
    if (response.status === 401 || response.status === 403 || response.status === 404) {
      return "denied";
    }
    throw new Error("Tenant membership verification is unavailable");
  }

  useEffect(() => {
    let active = true;
    try {
      void getKeycloak().init({ pkceMethod: "S256", checkLoginIframe: false })
        .then(async (authenticated) => {
          if (!active) return;
          if (!authenticated) { update("guest"); return; }
          const next = await verifyTenantMembership();
          if (active) update(next);
        })
        .catch(() => { if (active) { setMessage("Secure sign-in is unavailable. Please try again."); update("error"); } });
    } catch (error) { setMessage(error instanceof Error ? error.message : "Authentication is unavailable"); update("error"); }
    return () => { active = false; };
  }, []);

  async function signIn() {
    setMessage(""); update("checking");
    try { await getKeycloak().login({ redirectUri: window.location.origin }); }
    catch { setMessage("Unable to begin secure sign-in."); update("guest"); }
  }

  async function signOut() { await getKeycloak().logout({ redirectUri: window.location.origin }); }

  if (state === "authorized") return null;
  return <main className="login-page"><section className="login-panel"><div className="login-copy"><p className="badge"><Icon name="chart" /> OPERATIONS WORKSPACE</p><h1>Run your catalogue with <em>clarity.</em></h1><p>Manage products and customer-visible categories from one secure tenant workspace.</p><div className="login-points"><span>✓ Tenant-scoped access</span><span>✓ Secure Keycloak sign-in</span><span>✓ Catalogue publishing workflow</span></div></div><div className="login-card"><div className="admin-mark">{tenantBrand.fallbackInitials}</div><p className="eyebrow">TENANT ADMIN</p><h2>Welcome to {tenantBrand.displayName}</h2><p>Use your authorised staff account to manage this tenant’s catalogue.</p>{state === "denied" ? <><div className="auth-warning">This account is signed in but does not have the Tenant Admin role.</div><button className="secondary-button" onClick={() => void signOut()} type="button">Use another account</button></> : <button className="keycloak-button" type="button" onClick={() => void signIn()} disabled={state === "checking" || state === "error"}><span><Icon name="user" /></span><div><strong>{state === "checking" ? "Checking your session…" : "Continue with Keycloak"}</strong><small>Secure staff sign-in</small></div></button>}{message && <p className="auth-error" role="alert">{message}</p>}<p className="login-note">Your password is entered only on Keycloak—not in this admin application.</p></div></section></main>;
}
