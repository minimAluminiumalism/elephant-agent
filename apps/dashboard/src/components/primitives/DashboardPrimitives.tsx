import React from "react";
import { createPortal } from "react-dom";

import type { DashboardMetric, HealthTone } from "../../types/dashboard";
import { cx } from "../../lib/classNames";
import styles from "./Primitives.module.css";

const statusToneClass = {
  attention: styles.statusAttention,
  critical: styles.statusCritical,
  healthy: styles.statusHealthy,
  neutral: styles.statusNeutral,
} as const;

export type DetailListItem = {
  label: string;
  value: React.ReactNode;
};

function DetailModal({
  title,
  items,
  onClose,
}: {
  title: string;
  items: readonly DetailListItem[];
  onClose: () => void;
}): React.JSX.Element {
  React.useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return createPortal(
    <div className={styles.detailModalBackdrop} role="presentation" onMouseDown={onClose}>
      <section
        aria-label={title}
        aria-modal="true"
        className={styles.detailModal}
        role="dialog"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className={styles.detailModalHeader}>
          <strong>{title}</strong>
          <button className={styles.detailModalClose} type="button" onClick={onClose}>
            Close
          </button>
        </header>
        <div className={styles.detailModalBody}>
          {items.map((item) => (
            <article key={item.label} className={styles.detailModalItem}>
              <span>{item.label}</span>
              <div>{item.value}</div>
            </article>
          ))}
        </div>
      </section>
    </div>,
    document.body,
  );
}

export function ViewButton({
  title,
  items,
  className,
  variant = "pill",
  children = "Details",
}: {
  title: string;
  items: readonly DetailListItem[];
  className?: string;
  variant?: "pill" | "ghost";
  children?: React.ReactNode;
}): React.JSX.Element {
  const [open, setOpen] = React.useState(false);

  return (
    <>
      <button
        className={cx(
          variant === "ghost" ? styles.actionButton : styles.viewButton,
          variant === "ghost" && styles.actionButtonGhost,
          className,
        )}
        type="button"
        onClick={() => setOpen(true)}
      >
        {children}
      </button>
      {open ? <DetailModal title={title} items={items} onClose={() => setOpen(false)} /> : null}
    </>
  );
}

export function Panel({
  eyebrow,
  title,
  detail,
  children,
  className,
}: {
  eyebrow: string;
  title: string;
  detail: string;
  children: React.ReactNode;
  className?: string;
}): React.JSX.Element {
  return (
    <section aria-label={`${eyebrow}: ${title}`} className={cx(styles.surfaceCard, className)} data-detail={detail}>
      <header className={styles.surfaceCardHeader}>
        <h3>{title}</h3>
      </header>
      <div className={styles.surfaceCardBody}>{children}</div>
    </section>
  );
}

export function StatusBadge({
  tone,
  children,
  className,
}: {
  tone: HealthTone;
  children: React.ReactNode;
  className?: string;
}): React.JSX.Element {
  return <span className={cx(styles.statusBadge, statusToneClass[tone], className)}>{children}</span>;
}

export function MetricCard({
  metric,
  compact = false,
}: {
  metric: DashboardMetric;
  compact?: boolean;
}): React.JSX.Element {
  return (
    <article className={cx(styles.statCard, compact && styles.statCardCompact)}>
      <div className={styles.statCardTopline}>
        <span>{metric.label}</span>
        <i className={cx(styles.statToneDot, styles[`statTone${metric.tone}`])} aria-label={metric.tone} />
      </div>
      <strong>{metric.value}</strong>
      <p>{metric.note}</p>
    </article>
  );
}

export function EmptyPanel({
  title,
  detail,
}: {
  title: string;
  detail: string;
}): React.JSX.Element {
  return (
    <article className={styles.emptyState}>
      <strong>{title}</strong>
      <p>{detail}</p>
    </article>
  );
}

export function ActionButton({
  children,
  className,
  type = "button",
  variant = "default",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "ghost";
}): React.JSX.Element {
  return (
    <button
      {...props}
      className={cx(styles.actionButton, variant === "ghost" && styles.actionButtonGhost, className)}
      type={type}
    >
      {children}
    </button>
  );
}
