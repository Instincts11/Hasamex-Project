import type { Metadata } from "next";
import { Caveat, Inter } from "next/font/google";
import { AppShell } from "@/components/AppShell";
import { ThemeProvider } from "@/lib/theme";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const caveat = Caveat({
  variable: "--font-caveat",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "HASAMEX — Expert Call Intelligence",
  description:
    "AI-powered expert interview analysis with evidence-grounded Q&A across France, Germany, and the UK.",
};

const THEME_BOOTSTRAP = `(function(){try{var stored=localStorage.getItem("hasamex-theme");var theme=stored==="light"||stored==="dark"?stored:(window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light");document.documentElement.setAttribute("data-theme",theme);}catch(e){document.documentElement.setAttribute("data-theme","light");}})();`;

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${caveat.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_BOOTSTRAP }} />
      </head>
      <body className="min-h-full bg-bg font-sans text-ink">
        <ThemeProvider>
          <AppShell>{children}</AppShell>
        </ThemeProvider>
      </body>
    </html>
  );
}
