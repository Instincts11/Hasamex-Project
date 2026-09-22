import { EuropeMap } from "@/components/EuropeMap";
import { ExpertCard } from "@/components/ExpertCard";
import { Icon } from "@/components/Icon";
import { MetricCard } from "@/components/MetricCard";
import { PageHeader } from "@/components/PageHeader";
import { api } from "@/lib/api";
import { coverageTone } from "@/lib/ui";
import type { Segment, Theme } from "@/lib/types";
import Link from "next/link";

export const dynamic = "force-dynamic";

const RECENT = [
  {
    href: "/ask?q=What%20are%20the%20main%20barriers%20to%20adoption%3F",
    title: "Main barriers to adoption",
    meta: "3 expert sources",
    icon: "ask" as const,
  },
  {
    href: "/ask?q=How%20do%20purchase%20timelines%20differ%20across%20markets%3F",
    title: "Purchase timeline comparison",
    meta: "3 expert sources",
    icon: "bars" as const,
  },
  {
    href: "/ask?q=What%20are%20the%20experts%27%20growth%20expectations%3F",
    title: "Growth expectations",
    meta: "3 expert sources",
    icon: "pulse" as const,
  },
];

function themeIcon(name: string) {
  const key = name.toLowerCase();
  if (key.includes("train")) return "cap" as const;
  if (key.includes("util") || key.includes("volume")) return "bars" as const;
  if (key.includes("clinic")) return "pulse" as const;
  if (key.includes("econom") || key.includes("cost")) return "globe" as const;
  return "spark" as const;
}

function themeCoverage(theme: Theme) {
  if (theme.single_expert) return { covered: 1, total: 3 };
  const covered = new Set(theme.supporting.map((item) => item.market)).size || 1;
  return { covered, total: 3 };
}

function firstExpertTurn(segments: Segment[]) {
  return segments.find((segment) => segment.speaker !== "Interviewer" && segment.text);
}

function lastExpertTurn(segments: Segment[]) {
  return [...segments].reverse().find((segment) => segment.speaker !== "Interviewer" && segment.text);
}

export default async function OverviewPage() {
  let corpus;
  let themes: Theme[] = [];
  let highlights: Record<string, { quote: string; timestamp?: string }> = {};
  let projectQuote: { quote: string; expert: string; timestamp?: string; transcriptId: string } | null =
    null;

  try {
    const health = await api.health();
    corpus = health;
    const [themeBody, details] = await Promise.all([
      api.themes(),
      Promise.all(health.transcripts.map((item) => api.transcript(item.transcript_id))),
    ]);
    themes = themeBody.themes;
    for (const detail of details) {
      const opening = firstExpertTurn(detail.segments);
      if (opening) {
        highlights[detail.transcript_id] = {
          quote: opening.text,
          timestamp: opening.timestamp ?? undefined,
        };
      }
      if (detail.market === "United Kingdom") {
        const closing = lastExpertTurn(detail.segments);
        if (closing) {
          projectQuote = {
            quote: closing.text,
            expert: detail.expert,
            timestamp: closing.timestamp ?? undefined,
            transcriptId: detail.transcript_id,
          };
        }
      }
    }
  } catch {
    return (
      <div>
        <PageHeader title="From conversation to clarity" subtitle="The analysis API is not reachable." />
        <p className="text-caution">Start the backend on port 8000, then refresh.</p>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="relative">
      <section className="relative">
        <div className="relative z-30 max-w-2xl">
          <p className="text-[11px] font-semibold tracking-[0.2em] text-muted">
            EXPERT CALL INTELLIGENCE
          </p>
          <h2 className="page-title mt-1 text-4xl font-semibold tracking-tight md:text-[42px] md:leading-tight">
            From conversation to <span className="text-accent">clarity</span>
          </h2>
          <p className="page-subtitle mt-2 text-ink-secondary">
            Analyze expert interviews, compare perspectives, and trace every insight back to its source.
          </p>
        </div>
      </section>
      <div className="pointer-events-none absolute right-0 top-0 z-20 hidden lg:block max-[1460px]:right-0">
        <EuropeMap />
      </div>

      <div className="relative z-10 mt-4 grid w-full grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          icon="users"
          value="3"
          label="Experts"
          hint="France, Germany, United Kingdom"
        />
        <MetricCard icon="globe" value="3" label="Markets" hint="One interview per market" />
        <MetricCard
          icon="file"
          value={String(corpus.transcript_count)}
          label="Transcripts"
          hint="Original source files"
        />
        <MetricCard
          icon="quote"
          value={String(corpus.evidence_count)}
          label="Evidence units"
          hint="Available for citation"
        />
      </div>
      </div>

      <div className="mt-8 flex items-end justify-between gap-4">
        <h3 className="text-lg font-semibold tracking-tight">Our Experts</h3>
        <Link href="/transcripts" className="text-sm font-medium text-accent hover:text-accent-hover">
          View all transcripts
        </Link>
      </div>
      <div className="mt-4 grid w-full grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 min-[1441px]:grid-cols-4">
        {corpus.transcripts.map((transcript) => (
          <ExpertCard
            key={transcript.transcript_id}
            transcript={transcript}
            quote={highlights[transcript.transcript_id]?.quote}
            timestamp={highlights[transcript.transcript_id]?.timestamp}
          />
        ))}
        <article className="flex min-w-0 w-full flex-col overflow-hidden rounded-[14px] bg-[#17453f] text-white shadow-[var(--shadow)] lg:col-span-3 min-[1441px]:col-span-1">
          <div className="relative h-48 overflow-hidden bg-[#17453f] min-[1281px]:h-80">
            <img
              src="/home_hemax.png"
              alt="Robotic surgery in an operating room"
              className="absolute inset-0 h-full w-full object-contain object-center opacity-90 [filter:hue-rotate(18deg)_saturate(0.9)] min-[1281px]:object-cover min-[1281px]:object-[center_35%]"
            />
            <div className="absolute inset-0 bg-gradient-to-r from-[#17453f] via-[#17453f]/70 to-[#17453f]/15" />
            <div className="absolute inset-0 bg-[#0f6b63]/20" />
            <div className="absolute inset-x-0 bottom-0 p-4">
              <p className="text-[10px] font-semibold tracking-[0.18em] text-white/70">PROJECT FOCUS</p>
              <p className="mt-1 text-lg font-semibold leading-snug">
                Robotic surgery adoption in Europe
              </p>
            </div>
          </div>
          <div className="flex flex-1 flex-col p-5">
            <p className="text-sm text-white/75">
              Expert perspectives on barriers, opportunities and outlook.
            </p>
            <Link
              href="/themes"
              className="mt-4 inline-flex w-fit items-center gap-1 self-start rounded-full bg-accent px-3 py-1.5 text-sm font-medium text-white hover:bg-accent-hover"
            >
              Explore insights
              <Icon name="arrow" className="h-3.5 w-3.5" />
            </Link>
            {projectQuote ? (
              <blockquote className="mt-auto border-t border-white/10 pt-4 text-sm leading-relaxed text-white/85">
                “{projectQuote.quote}”
                <footer className="mt-2 text-xs text-white/55">
                  {projectQuote.expert} · UK
                </footer>
              </blockquote>
            ) : null}
          </div>
        </article>
      </div>

      <div className="mt-5 flex items-end justify-between gap-4">
        <h3 className="text-lg font-semibold tracking-tight">Key Themes</h3>
        <Link href="/themes" className="text-sm font-medium text-accent hover:text-accent-hover">
          View all themes
        </Link>
      </div>
      <div className="mt-4 grid w-full grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 min-[1441px]:grid-cols-5">
        {themes.map((theme) => {
          const { covered, total } = themeCoverage(theme);
          const tone = coverageTone(covered, total);
          const bar =
            tone === "full" ? "bg-support" : tone === "partial" ? "bg-caution" : "bg-caution";
          return (
            <Link key={theme.name} href="/themes" className="card block min-w-0 w-full p-5 hover:bg-surface-hover">
              <span className="grid h-9 w-9 place-items-center rounded-full bg-accent-soft text-accent min-[1501px]:h-12 min-[1501px]:w-12">
                <Icon name={themeIcon(theme.name)} className="h-4 w-4 min-[1501px]:h-6 min-[1501px]:w-6" strokeWidth={2.4} />
              </span>
              <h4 className="mt-4 font-semibold tracking-tight">{theme.name}</h4>
              <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-bg-subtle">
                <div
                  className={`h-full rounded-full ${bar}`}
                  style={{ width: `${Math.max((covered / total) * 100, 18)}%` }}
                />
              </div>
              <p className="mt-2 text-xs text-muted">
                {theme.single_expert ? "Single-expert observation" : `${covered} / ${total} experts`}
              </p>
              <p className="mt-3 line-clamp-3 text-sm text-ink-secondary">{theme.summary}</p>
            </Link>
          );
        })}
        <section className="card min-w-0 w-full p-5 sm:col-span-2 lg:col-span-2 min-[1441px]:col-span-1">
          <div className="flex items-center justify-between gap-3">
            <h3 className="font-semibold tracking-tight">Recent Insights</h3>
            <Link href="/ask" className="text-sm font-medium text-accent hover:text-accent-hover">
              View all
            </Link>
          </div>
          <ul className="mt-4 space-y-4">
            {RECENT.map((item) => (
              <li key={item.href}>
                <Link href={item.href} className="flex items-start gap-3 hover:text-accent">
                  <span className="mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-full bg-accent-soft text-accent min-[1501px]:h-12 min-[1501px]:w-12">
                    <Icon name={item.icon} className="h-4 w-4 min-[1501px]:h-6 min-[1501px]:w-6" strokeWidth={2.4} />
                  </span>
                  <span>
                    <span className="block text-sm font-medium">{item.title}</span>
                    <span className="mt-0.5 block text-xs text-muted">{item.meta}</span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
