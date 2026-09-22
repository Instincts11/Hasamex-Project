"use client";

import { Icon } from "@/components/Icon";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, useSyncExternalStore, type MouseEvent } from "react";

const LINKS = [
  { href: "/", label: "Overview", icon: "overview" as const },
  { href: "/guide", label: "Interview Guide", icon: "guide" as const },
  { href: "/themes", label: "Themes", icon: "themes" as const },
  { href: "/differences", label: "Differences", icon: "differences" as const },
  { href: "/transcripts", label: "Transcripts", icon: "transcripts" as const },
  { href: "/ask", label: "Ask the Calls", icon: "ask" as const },
  { href: "/settings", label: "Settings", icon: "settings" as const },
];

function subscribeCompact(onChange: () => void) {
  const media = window.matchMedia("(max-width: 1200px)");
  media.addEventListener("change", onChange);
  return () => media.removeEventListener("change", onChange);
}

function useCompactSidebar() {
  return useSyncExternalStore(
    subscribeCompact,
    () => window.matchMedia("(max-width: 1200px)").matches,
    () => false,
  );
}

export function Sidebar() {
  const pathname = usePathname();
  const compact = useCompactSidebar();
  const [expanded, setExpanded] = useState(false);
  const showLabels = !compact || expanded;

  useEffect(() => {
    setExpanded(false);
  }, [pathname]);

  useEffect(() => {
    if (!compact) setExpanded(false);
  }, [compact]);

  function expandIfCollapsed(event: MouseEvent) {
    if (!compact || expanded) return;
    event.preventDefault();
    setExpanded(true);
  }

  return (
    <>
      <div
        className={`fixed inset-0 z-30 bg-ink/20 transition min-[1201px]:hidden ${
          expanded ? "opacity-100" : "pointer-events-none opacity-0"
        }`}
        onClick={() => setExpanded(false)}
      />
      <aside
        className={`sidebar fixed bottom-0 left-0 top-14 z-40 flex flex-col border-r border-line bg-surface transition-[width] duration-200 ${
          showLabels ? "w-[252px]" : "w-[68px] max-[510px]:w-14"
        }`}
        aria-expanded={showLabels}
        onClick={expandIfCollapsed}
      >
        <nav className={`flex flex-1 flex-col gap-0.5 pt-4 ${showLabels ? "px-3" : "px-2"}`}>
          {LINKS.map((link) => {
            const active =
              link.href === "/"
                ? pathname === "/"
                : pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                title={showLabels ? undefined : link.label}
                onClick={expandIfCollapsed}
                className={`sidebar-link flex items-center rounded-lg py-2.5 text-base font-semibold ${
                  showLabels ? "gap-3 px-3" : "justify-center px-0"
                } ${
                  active
                    ? "bg-accent-soft text-accent"
                    : "text-ink-secondary hover:bg-bg-subtle"
                }`}
              >
                <Icon
                  name={link.icon}
                  className={`h-5 w-5 shrink-0 ${active ? "text-accent" : "text-muted"}`}
                  strokeWidth={1.9}
                />
                {showLabels ? <span className="truncate">{link.label}</span> : <span className="sr-only">{link.label}</span>}
              </Link>
            );
          })}
        </nav>
        {showLabels ? (
          <div className="sidebar-foot border-t border-line px-5 py-5">
            <p className="text-base font-semibold text-ink-secondary">3 Expert Calls</p>
            <p className="mt-1 text-base font-semibold text-ink-secondary">3 Markets</p>
            <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-bg-subtle">
              <div className="h-full w-full rounded-full bg-accent" />
            </div>
            <p className="mt-3 inline-flex items-center gap-2 text-base font-semibold text-support">
              <Icon name="check" className="h-5 w-5" strokeWidth={1.9} />
              Ready for Analysis
            </p>
            <p className="mt-4 text-base font-medium leading-relaxed text-muted">
              “Turning expert conversation into clarity.”
            </p>
            <p className="mt-2 text-sm font-semibold tracking-[0.16em] text-muted">HASAMEX</p>
          </div>
        ) : null}
      </aside>
    </>
  );
}
