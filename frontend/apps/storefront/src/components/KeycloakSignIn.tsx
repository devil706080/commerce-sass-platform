"use client";

import Keycloak from "keycloak-js";
import { useEffect, useRef, useState } from "react";
import { Icon } from "./Icon";

type Status = "checking" | "guest" | "authenticated" | "error";

export function KeycloakSignIn() {
  const client = useRef<Keycloak | null>(null);
  const [status, setStatus] = useState<Status>("checking");

  useEffect(() => {
    const url = process.env.NEXT_PUBLIC_KEYCLOAK_URL;
    const realm = process.env.NEXT_PUBLIC_KEYCLOAK_REALM;
    const clientId = process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID;
    if (!url || !realm || !clientId) { setStatus("error"); return; }
    const keycloak = new Keycloak({ url, realm, clientId });
    client.current = keycloak;
    void keycloak.init({ onLoad: "check-sso", pkceMethod: "S256", checkLoginIframe: false })
      .then((authenticated) => setStatus(authenticated ? "authenticated" : "guest"))
      .catch(() => setStatus("error"));
    return () => { client.current = null; };
  }, []);

  async function signIn() {
    setStatus("checking");
    try { await client.current?.login({ redirectUri: `${window.location.origin}/login` }); }
    catch { setStatus("error"); }
  }

  async function signOut() {
    try { await client.current?.logout({ redirectUri: `${window.location.origin}/` }); }
    catch { setStatus("error"); }
  }

  if (status === "authenticated") {
    return <div className="auth-success"><span>✓</span><h2>You are signed in</h2><p>Your Keycloak session is active for this browser.</p><a className="button button-primary" href="/">Continue shopping</a><button type="button" className="text-button" onClick={signOut}>Sign out</button></div>;
  }

  return (
    <div className="auth-actions">
      <button className="keycloak-button" type="button" onClick={signIn} disabled={status === "checking" || status === "error"}>
        <span className="keycloak-mark"><Icon name="shield" /></span>
        <span><strong>{status === "checking" ? "Checking secure sign-in…" : "Continue with Keycloak"}</strong><small>Authorization Code + PKCE</small></span>
        <Icon name="arrow" />
      </button>
      {status === "error" && <p className="auth-error" role="alert">Secure sign-in is not configured or is temporarily unavailable.</p>}
      <p className="auth-privacy"><Icon name="shield" /> Your password is entered only on the identity provider page, never in this storefront.</p>
    </div>
  );
}
