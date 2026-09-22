"use client";

import { DifferenceCard } from "@/components/DifferenceCard";
import { PageHeader } from "@/components/PageHeader";
import { api } from "@/lib/api";
import type { Difference } from "@/lib/types";
import { useEffect, useState } from "react";

export default function DifferencesPage() {
  const [differences, setDifferences] = useState<Difference[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .differences()
      .then((body) => setDifferences(body.differences))
      .catch((err: Error) => setError(err.message));
  }, []);

  return (
    <div>
      <PageHeader
        title="Differences & Perspectives"
        subtitle="Areas where experts place different emphasis or provide different views. Different emphasis is not automatically a contradiction."
      />
      {error ? <p className="text-conflict">{error}</p> : null}
      {!differences.length && !error ? (
        <p className="text-sm text-muted">Comparing perspectives across markets…</p>
      ) : null}
      <div className="grid w-full gap-4">
        {differences.map((item) => (
          <DifferenceCard
            key={item.topic}
            difference={item}
            expanded={expanded === item.topic}
            onToggle={() =>
              setExpanded((current) => (current === item.topic ? null : item.topic))
            }
          />
        ))}
      </div>
    </div>
  );
}
