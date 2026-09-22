import type { Evidence } from "./types";

export const MARKET_META: Record<string, { code: string; flag: string; icon: string }> = {
  France: { code: "FR", flag: "🇫🇷", icon: "/france_icon.png" },
  Germany: { code: "DE", flag: "🇩🇪", icon: "/germany_icon.png" },
  "United Kingdom": { code: "UK", flag: "🇬🇧", icon: "/united-kingdom_icon.png" },
};

export function marketMeta(market: string) {
  return MARKET_META[market] ?? { code: market.slice(0, 2).toUpperCase(), flag: "•", icon: "" };
}

export function transcriptAnchor(timestamp: string) {
  return `ts-${timestamp.replaceAll(":", "-").replaceAll(" ", "-")}`;
}

export function transcriptHref(transcriptId: string, timestamp?: string) {
  if (!timestamp || timestamp === "Timestamp unavailable.") {
    return `/transcripts/${transcriptId}`;
  }
  return `/transcripts/${transcriptId}#${transcriptAnchor(timestamp)}`;
}

export function evidenceHref(evidence: Evidence) {
  return transcriptHref(evidence.transcript_id, evidence.timestamp);
}

export function coverageTone(covered: number, total: number) {
  if (covered <= 1) return "single" as const;
  if (covered < total) return "partial" as const;
  return "full" as const;
}

export const PAGE_META: Record<string, { title: string; crumb: string }> = {
  "/": { title: "Overview", crumb: "Workspace" },
  "/guide": { title: "Interview Guide", crumb: "Analysis" },
  "/themes": { title: "Themes", crumb: "Analysis" },
  "/differences": { title: "Differences", crumb: "Analysis" },
  "/transcripts": { title: "Transcripts", crumb: "Sources" },
  "/transcripts/": { title: "Transcript explorer", crumb: "Sources" },
  "/ask": { title: "Ask the Calls", crumb: "Analysis" },
  "/settings": { title: "Settings", crumb: "Workspace" },
};
