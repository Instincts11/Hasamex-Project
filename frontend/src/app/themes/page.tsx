"use client";

import { PageHeader } from "@/components/PageHeader";
import { ThemeCard } from "@/components/ThemeCard";
import { api } from "@/lib/api";
import type { Theme } from "@/lib/types";
import { useEffect, useState } from "react";

export default function ThemesPage() {
  const [themes, setThemes] = useState<Theme[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .themes()
      .then((body) => setThemes(body.themes))
      .catch((err: Error) => setError(err.message));
  }, []);

  return (
    <div>
      <PageHeader
        title="Themes"
        subtitle="Recurring topics identified across the expert interviews. Coverage shows how many experts spoke to the theme — not consensus."
      />
      {error ? <p className="text-conflict">{error}</p> : null}
      {!themes.length && !error ? <p className="text-sm text-muted">Identifying recurring topics…</p> : null}
      <div className="grid w-full gap-4">
        {themes.map((theme) => (
          <ThemeCard
            key={theme.name}
            theme={theme}
            expanded={expanded === theme.name}
            onToggle={() =>
              setExpanded((current) => (current === theme.name ? null : theme.name))
            }
          />
        ))}
      </div>
    </div>
  );
}
