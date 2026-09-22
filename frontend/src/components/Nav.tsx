"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Dashboard" },
  { href: "/guide", label: "Interview Guide" },
  { href: "/themes", label: "Themes & Differences" },
  { href: "/ask", label: "Ask the Transcripts" },
  { href: "/explorer", label: "Transcript Explorer" },
];

export function Nav() {
  const pathname = usePathname();
  return (
    <aside className="flex w-full flex-col gap-8 border-b border-line bg-panel px-5 py-6 md:h-full md:w-64 md:border-b-0 md:border-r">
      <div>
        <p className="text-xs uppercase tracking-[0.18em] text-accent">Hasamex</p>
        <h1 className="mt-1 text-xl font-semibold">AI Analyzer</h1>
        <p className="mt-2 text-sm text-muted">
          Evidence-first expert-call analysis. Quotes come from the transcripts.
        </p>
      </div>
      <nav className="flex flex-col gap-1">
        {LINKS.map((link) => {
          const active =
            link.href === "/"
              ? pathname === "/"
              : pathname.startsWith(link.href);
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`rounded-md px-3 py-2 text-sm ${
                active
                  ? "bg-accent-soft font-medium text-accent"
                  : "text-foreground hover:bg-accent-soft/60"
              }`}
            >
              {link.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
