"use client";

import { TranscriptViewer } from "@/components/TranscriptViewer";
import { marketMeta, transcriptAnchor } from "@/lib/ui";
import type { Segment, TranscriptDetail } from "@/lib/types";
import { useEffect, useState } from "react";

function panelImage(transcript: TranscriptDetail) {
  const expert = transcript.expert.toLowerCase();
  const market = transcript.market.toLowerCase();
  if (expert.includes("anna keller") || market === "germany") {
    return {
      src: "/german_panel.png",
      alt: "Operating theatre with robotic surgery system in Germany",
    };
  }
  if (expert.includes("emily carter") || market.includes("kingdom") || market === "uk") {
    return {
      src: "/unitedkingdom_panel.png",
      alt: "Clinician looking out over a city from a UK hospital",
    };
  }
  return {
    src: "/transcripts_robot_portrait.png",
    alt: "Robotic surgery arms in an operating theatre",
  };
}

export function TranscriptWorkspace({ transcript }: { transcript: TranscriptDetail }) {
  const [selected, setSelected] = useState<Segment | null>(null);
  const meta = marketMeta(transcript.market);
  const image = panelImage(transcript);

  useEffect(() => {
    setSelected(null);
  }, [transcript.transcript_id]);

  useEffect(() => {
    function applyHash() {
      const hash = window.location.hash.slice(1);
      if (!hash) return;
      const match = transcript.segments.find((segment) =>
        segment.timestamp
          ? transcriptAnchor(segment.timestamp) === hash
          : segment.segment_id === hash,
      );
      if (match) setSelected(match);
    }
    applyHash();
    window.addEventListener("hashchange", applyHash);
    return () => window.removeEventListener("hashchange", applyHash);
  }, [transcript]);

  return (
    <div className="grid items-stretch gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(280px,0.85fr)]">
      <section className="card min-h-[70vh] p-5">
        <div className="mb-4 flex items-baseline justify-between gap-3">
          <div>
            <p className="text-[11px] font-semibold tracking-[0.16em] text-muted">TRANSCRIPT</p>
            <h3 className="mt-1 text-lg font-semibold tracking-tight">{transcript.expert}</h3>
          </div>
          <p className="text-xs text-muted">
            {meta.flag} {transcript.market}
          </p>
        </div>
        <TranscriptViewer transcript={transcript} onSelect={setSelected} />
      </section>
      <aside className="card flex h-full min-h-[70vh] flex-col overflow-hidden">
        <div className="shrink-0 p-5">
          <p className="text-[11px] font-semibold tracking-[0.16em] text-muted">AI ANALYSIS</p>
          <h3 className="mt-1 text-lg font-semibold tracking-tight">Selected Evidence</h3>
          {selected ? (
            <div className="mt-4">
              <p className="text-xs text-muted">
                {transcript.market} · {selected.timestamp_display}
              </p>
              <blockquote className="quote mt-3 text-sm leading-relaxed">
                “{selected.text}”
              </blockquote>
              <p className="mt-3 text-xs text-muted">
                This text is the original transcript turn. It can be used in analysis without rewriting the quote.
              </p>
            </div>
          ) : (
            <p className="mt-4 text-sm text-ink-secondary">
              Click a timestamped turn to inspect the source. Citations from other pages land on the matching moment.
            </p>
          )}
        </div>
        <div className="relative min-h-48 w-full flex-1 overflow-hidden bg-[#17453f]">
          <img
            src={image.src}
            alt={image.alt}
            className="absolute inset-0 h-full w-full object-cover object-center"
          />
        </div>
      </aside>
    </div>
  );
}
