"use client";

import { BrandMark } from "@/components/BrandMark";
import { Icon } from "@/components/Icon";
import { ThemeToggle } from "@/components/ThemeToggle";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

export function TopBar() {
  const router = useRouter();
  const [query, setQuery] = useState("");

  function onSearch(event: FormEvent) {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) {
      router.push("/ask");
      return;
    }
    router.push(`/ask?q=${encodeURIComponent(trimmed)}`);
  }

  return (
    <header className="fixed inset-x-0 top-0 z-40 flex h-14 items-center gap-4 border-b border-line bg-surface px-4 md:px-6">
      <Link href="/" className="flex items-center gap-2.5">
        <BrandMark className="h-7 w-7" />
        <span>
          <span className="block text-[13px] font-semibold tracking-[0.14em]">HASAMEX</span>
          <span className="block text-[11px] text-muted">Expert Call Intelligence</span>
        </span>
      </Link>
      <form onSubmit={onSearch} className="mx-auto hidden w-full max-w-xl flex-1 items-center md:flex">
        <label className="relative w-full">
          <Icon name="search" className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search or ask the calls..."
            className="w-full rounded-full border border-line bg-bg py-2 pl-9 pr-4 text-sm outline-none placeholder:text-muted focus:border-accent"
          />
        </label>
      </form>
      <div className="ml-auto flex items-center gap-3">
        <span className="hidden items-center gap-1.5 text-xs text-ink-secondary sm:inline-flex">
          <span className="h-2 w-2 rounded-full bg-support" />
          Analysis ready
        </span>
        <ThemeToggle />
        <span className="grid h-8 w-8 place-items-center rounded-full bg-accent-soft text-xs font-semibold text-accent">
          AV
        </span>
      </div>
    </header>
  );
}
