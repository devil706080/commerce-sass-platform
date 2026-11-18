import type { SVGProps } from "react";

export type IconName = "arrow" | "bag" | "cart" | "heart" | "location" | "menu" | "search" | "shield" | "spark" | "user";

const paths: Record<IconName, React.ReactNode> = {
  arrow: <><path d="M5 12h14"/><path d="m13 6 6 6-6 6"/></>,
  bag: <><path d="M6 8h12l-1 12H7L6 8Z"/><path d="M9 8a3 3 0 0 1 6 0"/></>,
  cart: <><path d="M3 4h2l2.2 10.2a2 2 0 0 0 2 1.6h7.8a2 2 0 0 0 2-1.6L20 8H6"/><circle cx="10" cy="20" r="1"/><circle cx="18" cy="20" r="1"/></>,
  heart: <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8l1.1 1.1L12 21l7.8-7.5 1.1-1.1a5.5 5.5 0 0 0-.1-7.8Z"/>,
  location: <><path d="M20 10c0 5-8 12-8 12S4 15 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/></>,
  menu: <><path d="M4 7h16"/><path d="M4 12h16"/><path d="M4 17h16"/></>,
  search: <><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></>,
  shield: <><path d="M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11Z"/><path d="m9 12 2 2 4-5"/></>,
  spark: <><path d="m12 3 1.4 4.1L17.5 8.5l-4.1 1.4L12 14l-1.4-4.1-4.1-1.4 4.1-1.4L12 3Z"/><path d="m19 14 .8 2.2L22 17l-2.2.8L19 20l-.8-2.2L16 17l2.2-.8L19 14Z"/></>,
  user: <><circle cx="12" cy="8" r="4"/><path d="M4 22a8 8 0 0 1 16 0"/></>,
};

export function Icon({ name, ...props }: SVGProps<SVGSVGElement> & { name: IconName }) {
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>{paths[name]}</svg>;
}
