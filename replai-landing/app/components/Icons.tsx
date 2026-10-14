// Icones au trait, coherentes entre elles (remplacent les emojis).
type P = { className?: string };
const base = {
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.7,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  viewBox: "0 0 24 24",
  "aria-hidden": true,
};

export const Icon = {
  catalog: ({ className }: P) => (
    <svg className={className} {...base}><path d="M4 7l8-4 8 4-8 4-8-4z" /><path d="M4 12l8 4 8-4" /><path d="M4 17l8 4 8-4" /></svg>
  ),
  size: ({ className }: P) => (
    <svg className={className} {...base}><path d="M3 8h18v8H3z" /><path d="M7 8v3M11 8v4M15 8v3M19 8v4" /></svg>
  ),
  link: ({ className }: P) => (
    <svg className={className} {...base}><path d="M10 14a4 4 0 005.66 0l3-3a4 4 0 00-5.66-5.66l-1 1" /><path d="M14 10a4 4 0 00-5.66 0l-3 3a4 4 0 005.66 5.66l1-1" /></svg>
  ),
  lead: ({ className }: P) => (
    <svg className={className} {...base}><path d="M4 6h16v12H4z" /><path d="M4 7l8 6 8-6" /></svg>
  ),
  dashboard: ({ className }: P) => (
    <svg className={className} {...base}><path d="M4 4h7v7H4zM13 4h7v4h-7zM13 10h7v10h-7zM4 13h7v7H4z" /></svg>
  ),
  brand: ({ className }: P) => (
    <svg className={className} {...base}><circle cx="12" cy="12" r="8.5" /><circle cx="9" cy="9.5" r="1.2" /><circle cx="14.5" cy="8.5" r="1.2" /><circle cx="16" cy="13" r="1.2" /><path d="M11 16.5a2 2 0 01-2-2" /></svg>
  ),
  bolt: ({ className }: P) => (
    <svg className={className} {...base}><path d="M13 3L5 14h6l-1 7 8-11h-6l1-7z" /></svg>
  ),
  bag: ({ className }: P) => (
    <svg className={className} {...base}><path d="M5 8h14l-1 12H6L5 8z" /><path d="M9 8V6a3 3 0 016 0v2" /></svg>
  ),
  clock: ({ className }: P) => (
    <svg className={className} {...base}><circle cx="12" cy="12" r="8.5" /><path d="M12 7.5V12l3 2" /></svg>
  ),
  check: ({ className }: P) => (
    <svg className={className} {...base} strokeWidth={2.2}><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>
  ),
  arrow: ({ className }: P) => (
    <svg className={className} {...base} strokeWidth={2}><path d="M5 12h14M13 6l6 6-6 6" /></svg>
  ),
  mail: ({ className }: P) => (
    <svg className={className} {...base}><path d="M4 6h16v12H4z" /><path d="M4 7l8 6 8-6" /></svg>
  ),
  send: ({ className }: P) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden><path d="M3.4 20.4l17.45-7.48a1 1 0 000-1.84L3.4 3.6a.99.99 0 00-1.39.91L2 9.12c0 .5.37.93.87.99L17 12 2.87 13.88c-.5.07-.87.5-.87 1l.01 4.61c0 .71.73 1.2 1.39.91z" /></svg>
  ),
};

export type IconName = keyof typeof Icon;
