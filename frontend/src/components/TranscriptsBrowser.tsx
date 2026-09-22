"use client";

import { ExpertCard } from "@/components/ExpertCard";
import { Icon } from "@/components/Icon";
import { TranscriptWorkspace } from "@/components/TranscriptWorkspace";
import type { TranscriptDetail } from "@/lib/types";
import { useEffect, useRef, useState } from "react";

export function TranscriptsBrowser({ transcripts }: { transcripts: TranscriptDetail[] }) {
  const initialId =
    transcripts.find((item) => item.expert.toLowerCase().includes("jean martin"))?.transcript_id ??
    transcripts.find((item) => item.market === "France")?.transcript_id ??
    transcripts[0]?.transcript_id ??
    null;
  const [openId, setOpenId] = useState<string | null>(initialId);
  const panelRef = useRef<HTMLDivElement>(null);
  const skipInitialScroll = useRef(true);
  const open = transcripts.find((item) => item.transcript_id === openId) ?? null;

  useEffect(() => {
    if (!open) return;
    if (skipInitialScroll.current) {
      skipInitialScroll.current = false;
      return;
    }
    panelRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [open]);

  function toggle(id: string) {
    setOpenId((current) => (current === id ? null : id));
  }

  return (
    <div>
      <div className="grid gap-4 md:grid-cols-3">
        {transcripts.map((transcript) => (
          <ExpertCard
            key={transcript.transcript_id}
            transcript={transcript}
            selected={openId === transcript.transcript_id}
            onOpen={() => toggle(transcript.transcript_id)}
          />
        ))}
      </div>
      {open ? (
        <div ref={panelRef} className="mt-6 scroll-mt-20">
          <div className="mb-3 flex items-center justify-between gap-3">
            <p className="text-sm text-ink-secondary">
              Showing the {open.market} interview with {open.expert}.
            </p>
            <button
              type="button"
              onClick={() => setOpenId(null)}
              className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-line bg-surface text-ink-secondary hover:bg-surface-hover hover:text-ink"
              aria-label="Close transcript"
            >
              <Icon name="close" className="h-4 w-4" strokeWidth={2} />
            </button>
          </div>
          <TranscriptWorkspace transcript={open} />
        </div>
      ) : null}
    </div>
  );
}
