"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useSyncExternalStore,
} from "react";

export type ThemePreference = "light" | "dark" | "system";
export type ResolvedTheme = "light" | "dark";

const STORAGE_KEY = "hasamex-theme";
const CHANGE_EVENT = "hasamex-theme";

type ThemeContextValue = {
  preference: ThemePreference;
  theme: ResolvedTheme;
  setPreference: (preference: ThemePreference) => void;
  toggle: () => void;
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

function systemTheme(): ResolvedTheme {
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function readPreference(): ThemePreference {
  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (stored === "light" || stored === "dark" || stored === "system") return stored;
  return "system";
}

function resolveTheme(preference: ThemePreference): ResolvedTheme {
  return preference === "system" ? systemTheme() : preference;
}

function applyTheme(theme: ResolvedTheme) {
  document.documentElement.setAttribute("data-theme", theme);
}

function emitThemeChange() {
  window.dispatchEvent(new Event(CHANGE_EVENT));
}

function subscribe(onStoreChange: () => void) {
  const media = window.matchMedia("(prefers-color-scheme: dark)");
  window.addEventListener(CHANGE_EVENT, onStoreChange);
  window.addEventListener("storage", onStoreChange);
  media.addEventListener("change", onStoreChange);
  return () => {
    window.removeEventListener(CHANGE_EVENT, onStoreChange);
    window.removeEventListener("storage", onStoreChange);
    media.removeEventListener("change", onStoreChange);
  };
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const preference = useSyncExternalStore(subscribe, readPreference, () => "system" as const);
  const theme = useSyncExternalStore(
    subscribe,
    () => resolveTheme(readPreference()),
    () => "light" as const,
  );

  const setPreference = useCallback((next: ThemePreference) => {
    window.localStorage.setItem(STORAGE_KEY, next);
    applyTheme(resolveTheme(next));
    emitThemeChange();
  }, []);

  const toggle = useCallback(() => {
    const current = document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
    setPreference(current === "dark" ? "light" : "dark");
  }, [setPreference]);

  const value = useMemo(
    () => ({ preference, theme, setPreference, toggle }),
    [preference, theme, setPreference, toggle],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within ThemeProvider");
  }
  return context;
}
