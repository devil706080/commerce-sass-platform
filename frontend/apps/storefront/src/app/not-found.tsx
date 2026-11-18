import Link from "next/link";
export default function NotFound() { return <div className="not-found shell"><span>404</span><h1>We could not find that product</h1><p>It may be unpublished or no longer available in this catalogue.</p><Link className="button button-primary" href="/products">Return to catalogue</Link></div>; }
