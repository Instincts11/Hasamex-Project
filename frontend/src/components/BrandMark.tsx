export function BrandMark({ className = "h-8 w-8" }: { className?: string }) {
  return (
    <svg className={`text-accent ${className}`} viewBox="0 0 32 32" fill="none" aria-hidden>
      <path
        d="M8.2 4.8h15.6L28 10.2v11.6L23.8 27.2H8.2L4 21.8V10.2L8.2 4.8Z"
        stroke="currentColor"
        strokeWidth="1.7"
      />
      <path d="M12 10.5v11M20 10.5v11M12 16h8" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    </svg>
  );
}
