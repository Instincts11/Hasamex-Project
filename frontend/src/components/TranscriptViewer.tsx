"use client";

import { TranscriptSegment } from "@/components/TranscriptSegment";
import { transcriptAnchor } from "@/lib/ui";
import type { Segment, TranscriptDetail } from "@/lib/types";
import { useEffect, useState } from "react";

export function TranscriptViewer({
  transcript,
  onSelect,
}: {
  transcript: TranscriptDetail;
  onSelect?: (segment: Segment) => void;
}) {
  const [activeId, setActiveId] = useState<string | null>(null);

  useEffect(() => {
    function applyHash() {
      const hash = window.location.hash.slice(1);
      if (!hash) return;
      setActiveId(hash);
      document.getElementById(hash)?.scrollIntoView({ behavior: "smooth", block: "center" });
    }
    applyHash();
    window.addEventListener("hashchange", applyHash);
    return () => window.removeEventListener("hashchange", applyHash);
  }, [transcript.transcript_id]);

  return (
    <div className="space-y-2">
      {transcript.segments.map((segment) => {
        const anchor = segment.timestamp ? transcriptAnchor(segment.timestamp) : segment.segment_id;
        return (
          <TranscriptSegment
            key={segment.segment_id}
            segment={segment}
            active={activeId === anchor}
            onSelect={() => {
              setActiveId(anchor);
              onSelect?.(segment);
            }}
          />
        );
      })}
    </div>
  );
}
