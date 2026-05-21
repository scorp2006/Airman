// Inline SVG icons - keeping the bundle tiny (no icon library).

type IconProps = { className?: string };

const base = "stroke-current";

export const IconGrid = ({ className = "w-5 h-5" }: IconProps) => (
  <svg viewBox="0 0 24 24" fill="none" className={`${base} ${className}`} strokeWidth="1.7">
    <rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" />
    <rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" />
  </svg>
);
export const IconPlane = ({ className = "w-5 h-5" }: IconProps) => (
  <svg viewBox="0 0 24 24" fill="none" className={`${base} ${className}`} strokeWidth="1.7" strokeLinejoin="round" strokeLinecap="round">
    <path d="M3 12l8-2 2-7 2 7 6 2-6 2-2 7-2-7-8-2z" />
  </svg>
);
export const IconBook = ({ className = "w-5 h-5" }: IconProps) => (
  <svg viewBox="0 0 24 24" fill="none" className={`${base} ${className}`} strokeWidth="1.7">
    <path d="M4 5a2 2 0 0 1 2-2h12v18H6a2 2 0 0 1-2-2V5z" /><path d="M4 17h14" />
  </svg>
);
export const IconWrench = ({ className = "w-5 h-5" }: IconProps) => (
  <svg viewBox="0 0 24 24" fill="none" className={`${base} ${className}`} strokeWidth="1.7" strokeLinejoin="round" strokeLinecap="round">
    <path d="M14.7 6.3a4 4 0 0 1 5 5l-9.1 9.1a2 2 0 0 1-2.8 0l-2.2-2.2a2 2 0 0 1 0-2.8l9.1-9.1z" />
    <path d="M14.7 6.3l3 3" />
  </svg>
);
export const IconClipboard = ({ className = "w-5 h-5" }: IconProps) => (
  <svg viewBox="0 0 24 24" fill="none" className={`${base} ${className}`} strokeWidth="1.7" strokeLinejoin="round" strokeLinecap="round">
    <rect x="6" y="4" width="12" height="18" rx="2" /><path d="M9 4h6v3H9z" />
  </svg>
);
export const IconSearch = ({ className = "w-5 h-5" }: IconProps) => (
  <svg viewBox="0 0 24 24" fill="none" className={`${base} ${className}`} strokeWidth="1.7" strokeLinecap="round">
    <circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" />
  </svg>
);
export const IconBell = ({ className = "w-5 h-5" }: IconProps) => (
  <svg viewBox="0 0 24 24" fill="none" className={`${base} ${className}`} strokeWidth="1.7" strokeLinejoin="round" strokeLinecap="round">
    <path d="M6 16V10a6 6 0 0 1 12 0v6l1.5 2H4.5L6 16z" /><path d="M10 20a2 2 0 0 0 4 0" />
  </svg>
);
export const IconLogout = ({ className = "w-5 h-5" }: IconProps) => (
  <svg viewBox="0 0 24 24" fill="none" className={`${base} ${className}`} strokeWidth="1.7" strokeLinejoin="round" strokeLinecap="round">
    <path d="M10 4H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h4" /><path d="m16 8 4 4-4 4" /><path d="M20 12H10" />
  </svg>
);
export const IconCheck = ({ className = "w-4 h-4" }: IconProps) => (
  <svg viewBox="0 0 24 24" fill="none" className={`${base} ${className}`} strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
    <path d="m5 12 5 5L20 7" />
  </svg>
);
export const IconX = ({ className = "w-4 h-4" }: IconProps) => (
  <svg viewBox="0 0 24 24" fill="none" className={`${base} ${className}`} strokeWidth="2.2" strokeLinecap="round">
    <path d="M6 6l12 12M18 6 6 18" />
  </svg>
);
export const IconChevron = ({ className = "w-4 h-4" }: IconProps) => (
  <svg viewBox="0 0 24 24" fill="none" className={`${base} ${className}`} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="m9 6 6 6-6 6" />
  </svg>
);
