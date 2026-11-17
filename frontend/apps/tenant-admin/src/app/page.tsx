"use client";
import Keycloak from "keycloak-js";
import { useEffect, useState } from "react";

const keycloak = new Keycloak({url: process.env.NEXT_PUBLIC_KEYCLOAK_URL!, realm: process.env.NEXT_PUBLIC_KEYCLOAK_REALM!, clientId: process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID!});
const api = process.env.NEXT_PUBLIC_CATALOGUE_API_URL!;
type Product={id:string;sku:string;name:string;description?:string;price_cents:number;published:boolean};
export default function Page() {
 const [ready,setReady]=useState(false); const [items,setItems]=useState<Product[]>([]); const [error,setError]=useState("");
 async function load(){try{await keycloak.updateToken(30);const r=await fetch(`${api}/api/v1/products`,{headers:{Authorization:`Bearer ${keycloak.token}`}});if(!r.ok)throw new Error((await r.json()).detail);setItems(await r.json())}catch(e){setError(e instanceof Error?e.message:"Unable to load products")}}
 useEffect(()=>{keycloak.init({onLoad:"login-required",pkceMethod:"S256",checkLoginIframe:false}).then(()=>{setReady(true);void load()}).catch(()=>setError("Login failed"))},[]);
 if(error)return <main><h1>Tenant Admin</h1><p className="error">{error}</p><button onClick={()=>keycloak.logout({redirectUri:window.location.origin})}>Sign out and try again</button></main>;
 if(!ready)return <main><p>Signing you in…</p></main>;
 return <main><header><div><span>Tenant workspace</span><h1>Catalogue</h1><p>Manage products for your store.</p></div><button onClick={()=>keycloak.logout({redirectUri:window.location.origin})}>Sign out</button></header><section><h2>Products</h2><button onClick={()=>void load()}>Refresh</button>{items.length===0?<p>No products yet.</p>:<ul>{items.map(p=><li key={p.id}><strong>{p.name}</strong><small>{p.sku} · ₹{(p.price_cents/100).toFixed(2)}</small></li>)}</ul>}</section></main>;
}
