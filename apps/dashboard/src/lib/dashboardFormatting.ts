export function formatDetailSummary(
  details: readonly {
    label: string;
    value: string;
  }[],
  options: {
    maxItems?: number;
    maxValueLength?: number;
  } = {},
): string {
  const maxItems = options.maxItems ?? 3;
  const maxValueLength = options.maxValueLength ?? 72;
  const visibleDetails = details.slice(0, maxItems);
  const hiddenCount = Math.max(0, details.length - visibleDetails.length);
  const summary = visibleDetails
    .map((detail) => `${detail.label}: ${compactText(detail.value, maxValueLength)}`)
    .join(" · ");

  return hiddenCount ? `${summary} · +${hiddenCount} more` : summary;
}

export function compactText(value: string, maxLength = 140): string {
  const normalized = value.replace(/\s+/g, " ").trim();
  const repeatedInterruptionIndex = normalized.indexOf(" after interruption: ");
  const deduped =
    repeatedInterruptionIndex >= 0
      ? `${normalized.slice(0, repeatedInterruptionIndex)} after interruption`
      : normalized;

  if (deduped.length <= maxLength) {
    return deduped;
  }

  return `${deduped.slice(0, Math.max(0, maxLength - 1)).trimEnd()}…`;
}

export function formatTimestamp(value: string): string {
  return new Date(value).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZoneName: "short",
  });
}

export function formatPollMs(value: number): string {
  return `${Math.floor(value / 1000)}s`;
}
