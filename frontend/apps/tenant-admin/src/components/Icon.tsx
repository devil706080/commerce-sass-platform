import type { SVGProps } from "react";
type IconName = "box" | "chart" | "grid" | "logout" | "plus" | "refresh" | "tag" | "user";
const paths: Record<IconName, React.ReactNode> = {
  box: <><path d="m12 2 8 4.5v9L12 20l-8-4.5v-9L12 2Z"/><path d="m4 6.5 8 4.5 8-4.5M12 11v9"/></>, chart: <><path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/></>, grid: <><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></>, logout: <><path d="M10 17l5-5-5-5M15 12H3"/><path d="M21 19V5a2 2 0 0 0-2-2h-6"/></>, plus: <path d="M12 5v14M5 12h14"/>, refresh: <><path d="M20 11a8 8 0 0 0-14.9-3M4 4v4h4M4 13a8 8 0 0 0 14.9 3M20 20v-4h-4"/></>, tag: <><path d="M20 13 13 20 3 10V3h7l10 10Z"/><circle cx="7.5" cy="7.5" r=".8"/></>, user: <><circle cx="12" cy="8" r="4"/><path d="M4 22a8 8 0 0 1 16 0"/></>,
};
export function Icon({ name, ...props }: SVGProps<SVGSVGElement> & { name: IconName }) { return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>{paths[name]}</svg>; }
