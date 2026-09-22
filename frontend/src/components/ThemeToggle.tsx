"use client";

import { Icon } from "@/components/Icon";
import { useTheme } from "@/lib/theme";

export function ThemeToggle() {
  const { theme, toggle } = useTheme();
  const next = theme === "dark" ? "light" : "dark";

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={`Switch to ${next} mode`}
      title={`Switch to ${next} mode`}
      className="grid h-8 w-8 place-items-center rounded-full border border-line bg-bg text-ink-secondary hover:border-accent hover:text-accent"
    >
      <Icon name={theme === "dark" ? "sun" : "moon"} className="h-4 w-4" />
    </button>
  );
}
