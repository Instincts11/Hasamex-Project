type IconName =
  | "overview"
  | "guide"
  | "themes"
  | "differences"
  | "transcripts"
  | "ask"
  | "settings"
  | "search"
  | "arrow"
  | "spark"
  | "users"
  | "globe"
  | "file"
  | "quote"
  | "cap"
  | "bars"
  | "pulse"
  | "clock"
  | "check"
  | "close"
  | "sun"
  | "moon";

export function Icon({
  name,
  className = "h-4 w-4",
  strokeWidth = 1.6,
}: {
  name: IconName;
  className?: string;
  strokeWidth?: number;
}) {
  const props = {
    className,
    fill: "none",
    stroke: "currentColor",
    strokeWidth,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    viewBox: "0 0 24 24",
  };
  switch (name) {
    case "overview":
      return (
        <svg {...props}>
          <rect x="3.5" y="3.5" width="7" height="7" rx="1.5" />
          <rect x="13.5" y="3.5" width="7" height="7" rx="1.5" />
          <rect x="3.5" y="13.5" width="7" height="7" rx="1.5" />
          <rect x="13.5" y="13.5" width="7" height="7" rx="1.5" />
        </svg>
      );
    case "guide":
      return (
        <svg {...props}>
          <path d="M7 4.5h10a1.5 1.5 0 0 1 1.5 1.5v13l-3-1.5-3 1.5-3-1.5-3 1.5V6A1.5 1.5 0 0 1 7 4.5Z" />
          <path d="M9 9h6M9 12.5h6" />
        </svg>
      );
    case "themes":
      return (
        <svg {...props}>
          <circle cx="8" cy="8" r="3" />
          <circle cx="16" cy="9" r="2.4" />
          <circle cx="12" cy="16" r="2.8" />
        </svg>
      );
    case "differences":
      return (
        <svg {...props}>
          <path d="M5 19V6.5M12 19V10M19 19V4.5" />
        </svg>
      );
    case "transcripts":
      return (
        <svg {...props}>
          <path d="M6 5h12v14H6z" />
          <path d="M9 9h6M9 12h6M9 15h4" />
        </svg>
      );
    case "ask":
      return (
        <svg {...props}>
          <path d="M5 7.5A3.5 3.5 0 0 1 8.5 4h7A3.5 3.5 0 0 1 19 7.5v5A3.5 3.5 0 0 1 15.5 16H12l-4 3.2V16H8.5A3.5 3.5 0 0 1 5 12.5v-5Z" />
        </svg>
      );
    case "settings":
      return (
        <svg {...props}>
          <circle cx="12" cy="12" r="3" />
          <path d="M12 4.5v2M12 17.5v2M4.5 12h2M17.5 12h2M6.4 6.4l1.4 1.4M16.2 16.2l1.4 1.4M17.6 6.4l-1.4 1.4M7.8 16.2l-1.4 1.4" />
        </svg>
      );
    case "search":
      return (
        <svg {...props}>
          <circle cx="11" cy="11" r="6" />
          <path d="m16 16 3.5 3.5" />
        </svg>
      );
    case "arrow":
      return (
        <svg {...props}>
          <path d="M7 12h10M13 8l4 4-4 4" />
        </svg>
      );
    case "spark":
      return (
        <svg {...props}>
          <path d="M12 4.5 13.4 9 18 10.4 13.4 11.8 12 16.5 10.6 11.8 6 10.4 10.6 9 12 4.5Z" />
        </svg>
      );
    case "users":
      return (
        <svg {...props}>
          <circle cx="9" cy="8" r="2.4" />
          <path d="M4.5 17.5c.6-2.6 2.4-4 4.5-4s3.9 1.4 4.5 4" />
          <circle cx="16" cy="8.5" r="2" />
          <path d="M15 13.6c1.7.3 3.1 1.4 3.6 3.4" />
        </svg>
      );
    case "globe":
      return (
        <svg {...props}>
          <circle cx="12" cy="12" r="7.5" />
          <path d="M4.5 12h15M12 4.5c2.2 2.4 3.3 5 3.3 7.5S14.2 17.1 12 19.5C9.8 17.1 8.7 14.5 8.7 12S9.8 6.9 12 4.5Z" />
        </svg>
      );
    case "file":
      return (
        <svg {...props}>
          <path d="M7 4.5h7l3.5 3.5V19.5H7z" />
          <path d="M14 4.5v3.5h3.5" />
        </svg>
      );
    case "quote":
      return (
        <svg {...props}>
          <path d="M6 16.5c0-4 2-7 5-8.2V6.5C7.2 7.6 4.5 11 4.5 16.5H6Zm8.5 0c0-4 2-7 5-8.2V6.5c-3.8 1.1-6.5 4.5-6.5 10H14.5Z" />
        </svg>
      );
    case "cap":
      return (
        <svg {...props}>
          <path d="M3.5 10 12 6l8.5 4L12 14 3.5 10Z" />
          <path d="M7 12v3.5c1.6 1.2 3.3 1.8 5 1.8s3.4-.6 5-1.8V12" />
        </svg>
      );
    case "bars":
      return (
        <svg {...props}>
          <path d="M5 17V10M12 17V7M19 17v-4" />
        </svg>
      );
    case "pulse":
      return (
        <svg {...props}>
          <path d="M3.5 12h4l2-5 3 10 2-5h6" />
        </svg>
      );
    case "clock":
      return (
        <svg {...props}>
          <circle cx="12" cy="12" r="7.5" />
          <path d="M12 8v4.5l3 2" />
        </svg>
      );
    case "check":
      return (
        <svg {...props}>
          <circle cx="12" cy="12" r="7.5" />
          <path d="m8.5 12.2 2.4 2.3 4.6-5" />
        </svg>
      );
    case "close":
      return (
        <svg {...props}>
          <path d="M7 7l10 10M17 7 7 17" />
        </svg>
      );
    case "sun":
      return (
        <svg {...props}>
          <circle cx="12" cy="12" r="3.5" />
          <path d="M12 4.5v1.5M12 18v1.5M4.5 12h1.5M18 12h1.5M6.4 6.4l1.1 1.1M16.5 16.5l1.1 1.1M17.6 6.4l-1.1 1.1M7.5 16.5l-1.1 1.1" />
        </svg>
      );
    case "moon":
      return (
        <svg {...props}>
          <path d="M15.5 4.8A7.5 7.5 0 1 0 19.2 15 6 6 0 0 1 15.5 4.8Z" />
        </svg>
      );
  }
}
