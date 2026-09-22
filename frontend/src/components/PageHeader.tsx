export function PageHeader({
  eyebrow,
  title,
  subtitle,
  action,
}: {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div className="max-w-3xl">
        {eyebrow ? (
          <p className="text-[11px] font-semibold tracking-[0.18em] text-accent">{eyebrow}</p>
        ) : null}
        <h2 className="page-title mt-1 text-3xl font-semibold tracking-tight">{title}</h2>
        {subtitle ? <p className="page-subtitle mt-2 text-ink-secondary">{subtitle}</p> : null}
      </div>
      {action}
    </div>
  );
}
