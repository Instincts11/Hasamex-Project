"use client";

import { useTheme, type ThemePreference } from "@/lib/theme";

const OPTIONS: { id: ThemePreference; label: string; hint: string }[] = [
  { id: "light", label: "Light", hint: "Bright workspace" },
  { id: "dark", label: "Dark", hint: "Low-glare workspace" },
  { id: "system", label: "System", hint: "Match device setting" },
];

export function ThemeSettings() {
  const { preference, setPreference } = useTheme();

  return (
    <section className="card p-6">
      <h3 className="font-semibold tracking-tight">Appearance</h3>
      <p className="mt-1 text-sm text-ink-secondary">Choose light, dark, or follow the system theme.</p>
      <div className="mt-4 grid gap-2 sm:grid-cols-3">
        {OPTIONS.map((option) => {
          const selected = preference === option.id;
          return (
            <button
              key={option.id}
              type="button"
              onClick={() => setPreference(option.id)}
              aria-pressed={selected}
              className={`rounded-xl border px-4 py-3 text-left ${
                selected
                  ? "border-accent bg-accent-soft"
                  : "border-line bg-bg hover:border-accent"
              }`}
            >
              <p className="text-sm font-medium">{option.label}</p>
              <p className="mt-1 text-xs text-muted">{option.hint}</p>
            </button>
          );
        })}
      </div>
    </section>
  );
}
