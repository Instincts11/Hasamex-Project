"use client";

import { Icon } from "@/components/Icon";
import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Overview", icon: "overview" as const },
  { href: "/guide", label: "Guide", icon: "guide" as const },
  { href: "/transcripts", label: "Sources", icon: "transcripts" as const },
  { href: "/ask", label: "Ask", icon: "ask" as const },
  { href: "/themes", label: "Themes", icon: "themes" as const },
];

export function MobileNav() {
  const pathname = usePathname();
  return (
    <nav className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-5 border-t border-line bg-surface px-1 py-2 lg:hidden">
      {LINKS.map((link) => {
        const active =
          link.href === "/" ? pathname === "/" : pathname.startsWith(link.href);
        return (
          <Link
            key={link.href}
            href={link.href}
            className={`flex flex-col items-center gap-1 rounded-lg py-1 text-[11px] font-semibold ${
              active ? "text-accent" : "text-muted"
            }`}
          >
            <Icon name={link.icon} className="h-5 w-5" strokeWidth={1.9} />
            {link.label}
          </Link>
        );
      })}
    </nav>
  );
}
