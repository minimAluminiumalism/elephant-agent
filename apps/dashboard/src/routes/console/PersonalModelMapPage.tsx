import React from "react";

import elephantLogo from "../../assets/brand/elephant-logo.png";
import {
  ActionButton,
  EmptyPanel,
  MetricCard,
  Panel,
  StatusBadge,
  ViewButton,
  type DetailListItem,
} from "../../components/primitives/DashboardPrimitives";
import { useDashboardSnapshot } from "../../hooks/useOperatorConsole";
import {
  deletePersonalModelClaim,
  disputePersonalModelClaim,
  forgetPersonalModelClaim,
  protectPersonalModelClaim,
  restorePersonalModelClaim,
  unprotectPersonalModelClaim,
} from "../../lib/dashboardApi";
import { compactText, formatTimestamp } from "../../lib/dashboardFormatting";
import type { DashboardJson, DashboardMetric, DashboardRow, HealthTone } from "../../types/dashboard";
import styles from "../RouteLayouts.module.css";
import { MindMapView } from "./MindMapView";

// --- Helpers ---

type TopicSlot = {
  topic: string;
  lens: string;
  domain: string;
  entity: string;
  active: number;
  retired: number;
  disputed: number;
  rows: DashboardRow[];
};

function asRows(value: DashboardJson | undefined): DashboardRow[] {
  return Array.isArray(value)
    ? value.filter((item): item is DashboardRow => item !== null && typeof item === "object" && !Array.isArray(item))
    : [];
}

function jsonObject(value: DashboardJson | undefined): DashboardRow {
  return value !== null && typeof value === "object" && !Array.isArray(value) ? value : {};
}

function valueOf(row: DashboardRow | null | undefined, key: string, fallback = ""): string {
  if (!row) return fallback;
  const item = row[key];
  if (item === null || item === undefined || item === "") return fallback;
  if (typeof item === "string" || typeof item === "number" || typeof item === "boolean") return String(item);
  return JSON.stringify(item);
}

function topicOf(row: DashboardRow): string {
  return valueOf(jsonObject(row.metadata), "topic", valueOf(row, "topic", ""));
}

function claimRef(row: DashboardRow): string {
  return valueOf(row, "ref", valueOf(row, "fact_id", ""));
}

function toneForStatus(statusLike: unknown): HealthTone {
  const normalized = String(statusLike ?? "").toLowerCase();
  if (["active", "ready", "healthy", "ok"].some((item) => normalized.includes(item))) return "healthy";
  if (["retired", "stale", "review"].some((item) => normalized.includes(item))) return "attention";
  if (["deleted", "disputed", "failed", "error"].some((item) => normalized.includes(item))) return "critical";
  return "neutral";
}

function isProtectedRow(row: DashboardRow): boolean {
  const metadata = jsonObject(row.metadata);
  return valueOf(metadata, "protected", "") === "true";
}

function isSkillFitSlot(slot: TopicSlot): boolean {
  return slot.topic.startsWith("world.skills.affinity.") || slot.topic.startsWith("skills.affinity.");
}

function detailItems(row: DashboardRow): DetailListItem[] {
  return Object.entries(row).map(([key, item]) => ({
    label: key,
    value: <code>{typeof item === "string" ? item : JSON.stringify(item, null, 2)}</code>,
  }));
}

function memoryPalaceOwner(model: DashboardRow | undefined): string {
  const card = jsonObject(model?.user_profile);
  const name = valueOf(card, "preferred_name", valueOf(model, "user_preferred_name", valueOf(model, "preferred_name", ""))).trim();
  return name && name !== "n/a" ? name : "Your";
}

// --- Data building ---

type PalaceData = {
  lenses: Map<string, TopicSlot[]>;
  metrics: DashboardMetric[];
  allSlots: TopicSlot[];
};

const KNOWN_LENSES = new Set(["identity", "world", "pulse", "journey"]);

function lensFromTopic(topic: string, storedLens: string): string {
  // Topic prefix is authoritative; fall back to stored lens for pre-migration rows.
  const prefix = topic.split(".")[0] ?? "";
  if (KNOWN_LENSES.has(prefix)) return prefix;
  return KNOWN_LENSES.has(storedLens) ? storedLens : "identity";
}

function buildPalaceData(model: DashboardRow | undefined): PalaceData {
  const facts = asRows(model?.personal_model_all_facts).length ? asRows(model?.personal_model_all_facts) : asRows(model?.personal_model_facts);
  const slotMap = new Map<string, TopicSlot>();

  facts.forEach((fact) => {
    const storedLens = valueOf(fact, "lens", "identity");
    const topic = topicOf(fact);
    const lens = lensFromTopic(topic, storedLens);
    const parts = topic.split(".").filter(Boolean);
    // Topic format: lens.facet.entity[.qualifier...]
    const domain = parts[1] ?? parts[0] ?? "general";
    const entity = parts[2] ?? parts[1] ?? "general";

    const key = `${lens}:${topic}`;
    const slot = slotMap.get(key) ?? { topic, lens, domain, entity, active: 0, retired: 0, disputed: 0, rows: [] };
    const status = valueOf(fact, "status", "active");
    if (status === "retired") slot.retired += 1;
    else if (status === "disputed") slot.disputed += 1;
    else slot.active += 1;
    slot.rows.push(fact);
    slotMap.set(key, slot);
  });

  const allSlots = [...slotMap.values()].sort((a, b) => a.lens.localeCompare(b.lens) || a.domain.localeCompare(b.domain) || a.topic.localeCompare(b.topic));
  const lenses = new Map<string, TopicSlot[]>();
  for (const slot of allSlots) {
    lenses.set(slot.lens, [...(lenses.get(slot.lens) ?? []), slot]);
  }

  const active = facts.filter((f) => valueOf(f, "status", "active") === "active").length;
  const retired = facts.filter((f) => valueOf(f, "status") === "retired").length;
  const disputed = facts.filter((f) => valueOf(f, "status") === "disputed").length;
  const metrics: DashboardMetric[] = [
    { label: "Topics", value: String(slotMap.size), note: "Distinct topic slots.", tone: slotMap.size ? "healthy" : "neutral" },
    { label: "Live", value: String(active), note: "Active claims.", tone: active ? "healthy" : "neutral" },
    { label: "Archived", value: String(retired), note: "Retired claims.", tone: retired ? "attention" : "neutral" },
    { label: "Review", value: String(disputed), note: "Disputed claims.", tone: disputed ? "critical" : "neutral" },
  ];

  return { lenses, metrics, allSlots };
}

// --- Components ---

function ClaimRow({ row, refresh }: { row: DashboardRow; refresh: () => Promise<void> }): React.JSX.Element {
  const ref = claimRef(row);
  const text = valueOf(row, "text", "");
  const status = valueOf(row, "status", "active");
  const isProtected = isProtectedRow(row);

  return (
    <div className={styles.palaceClaimRow}>
      <div className={styles.palaceClaimText}>
        <span className={styles.palaceClaimStatus}>
          <StatusBadge tone={toneForStatus(status)}>{status}</StatusBadge>
          {isProtected && <StatusBadge tone="neutral">protected</StatusBadge>}
        </span>
        <p>{compactText(text, 200)}</p>
      </div>
      {ref && (
        <div className={styles.palaceClaimActions}>
          {status === "active" && !isProtected && (
            <ActionButton variant="ghost" onClick={() => void runAction(ref, row, "retire", refresh)}>Archive</ActionButton>
          )}
          {status === "retired" && (
            <ActionButton variant="ghost" onClick={() => void runAction(ref, row, "restore", refresh)}>Restore</ActionButton>
          )}
          <ViewButton title={ref} items={detailItems(row)} variant="ghost">Inspect</ViewButton>
        </div>
      )}
    </div>
  );
}

async function runAction(ref: string, row: DashboardRow, action: "retire" | "restore" | "dispute" | "delete", refresh: () => Promise<void>): Promise<void> {
  const payload = { lens: valueOf(row, "lens", "identity"), topic: topicOf(row), reason: "dashboard action" };
  if (action === "retire") await forgetPersonalModelClaim(ref, payload);
  if (action === "restore") await restorePersonalModelClaim(ref, payload);
  if (action === "dispute") await disputePersonalModelClaim(ref, payload);
  if (action === "delete") await deletePersonalModelClaim(ref, payload);
  await refresh();
}

function TopicGroup({ slot, refresh }: { slot: TopicSlot; refresh: () => Promise<void> }): React.JSX.Element {
  const topicLabel = slot.topic.split(".").slice(2).join(".") || slot.topic;
  return (
    <details className={styles.palaceTopicGroup} open={slot.active > 0}>
      <summary className={styles.palaceTopicSummary}>
        <strong>{topicLabel}</strong>
        <span className={styles.palaceTopicCount}>{slot.active} active{slot.retired ? `, ${slot.retired} archived` : ""}</span>
      </summary>
      <div className={styles.palaceTopicClaims}>
        {slot.rows.map((row, i) => <ClaimRow key={claimRef(row) || `${slot.topic}-${i}`} row={row} refresh={refresh} />)}
      </div>
    </details>
  );
}

function DomainGroup({ domain, slots, refresh }: { domain: string; slots: TopicSlot[]; refresh: () => Promise<void> }): React.JSX.Element {
  return (
    <div className={styles.palaceDomainGroup}>
      <h4 className={styles.palaceDomainTitle}>{domain}</h4>
      {slots.map((slot) => <TopicGroup key={slot.topic} slot={slot} refresh={refresh} />)}
    </div>
  );
}

const LENS_DESCRIPTIONS: Record<string, string> = {
  identity: "Core character, values, style, and body — the stable person underneath.",
  world: "People, places, projects, tools, and assets in their life.",
  pulse: "Current chapter, mood, focus, blockers, and intent.",
  journey: "Lessons learned, patterns noticed, key decisions, and milestones.",
};

function LensQuadrant({ lens, slots, refresh }: { lens: string; slots: TopicSlot[]; refresh: () => Promise<void> }): React.JSX.Element {
  // Group by domain
  const domains = new Map<string, TopicSlot[]>();
  for (const slot of slots) {
    if (isSkillFitSlot(slot)) continue; // Skills shown separately
    domains.set(slot.domain, [...(domains.get(slot.domain) ?? []), slot]);
  }
  const lensLabel = lens.charAt(0).toUpperCase() + lens.slice(1);
  const claimCount = slots.filter((s) => !isSkillFitSlot(s)).reduce((sum, s) => sum + s.active, 0);

  return (
    <section className={styles.palaceLensQuadrant} data-lens={lens}>
      <header className={styles.palaceLensHeader}>
        <h3>{lensLabel}</h3>
        <span className={styles.palaceLensBadge} data-lens={lens}>{claimCount} claims</span>
      </header>
      <p className={styles.palaceLensDescription}>{LENS_DESCRIPTIONS[lens] ?? ""}</p>
      <div className={styles.palaceLensBody}>
        {[...domains.entries()].map(([domain, domainSlots]) => (
          <DomainGroup key={domain} domain={domain} slots={domainSlots} refresh={refresh} />
        ))}
        {!domains.size && <p className={styles.palaceEmpty}>No claims yet.</p>}
      </div>
    </section>
  );
}

// Profile facts derived directly from PM claims (no separate user_profile needed)
// Topics follow the canonical four-lens schema: identity/world/pulse/journey.<facet>.<sub>
const TOPIC_DISPLAY: readonly { topic: string; label: string; full?: boolean }[] = [
  { topic: "identity.anchor.name.preferred", label: "Name" },
  { topic: "identity.anchor.gender.self_description", label: "Gender" },
  { topic: "world.places.city.current", label: "City" },
  { topic: "identity.anchor.birth.date", label: "Birth date" },
  { topic: "identity.style.language.first", label: "Speaks" },
  { topic: "pulse.chapter.work.role", label: "Working on", full: true },
  { topic: "identity.character.mbti.type", label: "MBTI", full: true },
  { topic: "identity.style.hobbies.personal", label: "Hobbies", full: true },
  { topic: "identity.style.companion.posture", label: "Relationship mode", full: true },
  { topic: "identity.body.allergy.medication", label: "Medication allergies", full: true },
  { topic: "identity.body.condition.chronic", label: "Health notes", full: true },
  { topic: "identity.body.allergy.food", label: "Food allergies", full: true },
  { topic: "identity.body.history.trauma", label: "Care context", full: true },
  { topic: "identity.body.boundary.personal", label: "Safety boundaries", full: true },
];

type ProfileFact = { label: string; value: string; full?: boolean };
type ProfileFactRow = { left: ProfileFact; right?: ProfileFact; full?: boolean };

// Strip label prefixes from fact text for display (init stores "称呼：zoey。" but we just want "zoey")
function stripFactPrefix(text: string): string {
  // Remove patterns like "称呼：", "性别/自我描述：", "城市或时区语境：", "出生日期：", etc.
  const cleaned = text
    .replace(/^[^:：]+[：:]\s*/, "")  // Remove everything up to first colon
    .replace(/[。．.]$/, "")          // Remove trailing period
    .trim();
  return cleaned || text.trim();
}

function buildProfileFacts(model: DashboardRow | undefined): ProfileFact[] {
  const facts = asRows(model?.personal_model_facts);
  const result: ProfileFact[] = [];
  const seen = new Set<string>();
  for (const { topic, label, full } of TOPIC_DISPLAY) {
    const match = facts.find((f) => {
      const meta = jsonObject(f.metadata);
      return valueOf(meta, "topic", "") === topic && valueOf(f, "status", "active") === "active";
    });
    if (match && !seen.has(label)) {
      seen.add(label);
      result.push({ label, value: stripFactPrefix(valueOf(match, "text", "")), full });
    }
  }
  return result;
}

function buildFactRows(facts: ProfileFact[]): ProfileFactRow[] {
  const rows: ProfileFactRow[] = [];
  const used = new Set<number>();
  const byLabel = (label: string) => {
    const idx = facts.findIndex((f, i) => !used.has(i) && f.label === label);
    return idx >= 0 ? { idx, fact: facts[idx] } : undefined;
  };
  const pushPair = (l: string, r: string) => {
    const left = byLabel(l);
    const right = byLabel(r);
    if (!left && !right) return;
    if (left) used.add(left.idx);
    if (right) used.add(right.idx);
    rows.push({ left: left?.fact ?? right!.fact, right: left ? right?.fact : undefined });
  };
  pushPair("Name", "Gender");
  pushPair("City", "Birth date");
  pushPair("Speaks", "Medication allergies");
  facts.forEach((fact, index) => {
    if (used.has(index)) return;
    rows.push({ left: fact, full: fact.full ?? true });
  });
  return rows;
}

function ProfileFactsPanel({ model }: { model: DashboardRow | undefined }): React.JSX.Element | null {
  const facts = buildProfileFacts(model);
  const factRows = buildFactRows(facts);
  if (!facts.length) return null;
  return (
    <Panel eyebrow="Your facts" title="What I know so far" detail="Drawn directly from your Personal Model claims. Update a claim and this view updates too.">
      <div className={styles.youFactsLayout}>
        <dl className={styles.youFactsGrid}>
          {factRows.map((row, index) => (
            <div
              key={`${row.left.label}-${row.right?.label ?? "full"}-${index}`}
              className={`${styles.youFactRow} ${row.full ? styles.youFactRowFull : ""}`}
            >
              <div className={styles.youFactPair}>
                <dt>{row.left.label}</dt>
                <dd>{row.left.value}</dd>
              </div>
              {row.right && (
                <div className={styles.youFactPair}>
                  <dt>{row.right.label}</dt>
                  <dd>{row.right.value}</dd>
                </div>
              )}
            </div>
          ))}
        </dl>
      </div>
    </Panel>
  );
}

function SkillsPanel({ slots, refresh }: { slots: TopicSlot[]; refresh: () => Promise<void> }): React.JSX.Element | null {
  const skillSlots = slots.filter(isSkillFitSlot);
  if (!skillSlots.length) return null;
  return (
    <Panel eyebrow="Skills" title="Skill fit" detail="Visible skill-fit signals from background learning.">
      <div className={styles.palaceSkillGrid}>
        {skillSlots.map((slot) => {
          const newest = slot.rows[0];
          const metadata = jsonObject(newest?.metadata);
          const skillId = valueOf(metadata, "skill_id", slot.topic.replace(/^(?:world\.)?skills\.affinity\./, "").replaceAll("_", "-"));
          return (
            <div key={slot.topic} className={styles.palaceSkillCard}>
              <StatusBadge tone="healthy">{skillId}</StatusBadge>
              <p>{compactText(valueOf(newest, "text", ""), 120)}</p>
            </div>
          );
        })}
      </div>
    </Panel>
  );
}

// --- Main Page ---

export function PersonalModelMapPage(): React.JSX.Element {
  const { dashboard, loading, error, refresh } = useDashboardSnapshot("personal-models");
  const model = dashboard?.personal_models[0];
  const palace = React.useMemo(() => buildPalaceData(model), [model]);
  const owner = memoryPalaceOwner(model);

  return (
    <div className={styles.pageStack}>
      <header className={styles.pageHeader} data-dashboard-page>
        <div className={styles.personalModelMapHeaderTop}>
          <div className={styles.pageHeaderCopy}>
            <div className={styles.pageHeaderBadges}>
              <span className={styles.pageHeaderBrandBadge}>
                <img src={elephantLogo} alt="" />
                <strong>Elephant Agent</strong>
              </span>
              <span className={styles.pageHeaderEyebrow}>Personal Model</span>
            </div>
            <h1>{owner === "Your" ? "Your Personal Model" : `${owner}'s Personal Model`}</h1>
            <p>What Elephant Agent understands about {owner === "Your" ? "you" : owner}, organized by lens.</p>
          </div>
          <div className={styles.personalModelMapMetricGrid}>
            {palace.metrics.map((metric) => <MetricCard key={metric.label} metric={metric} compact />)}
          </div>
        </div>
      </header>

      {error && (
        <Panel eyebrow="API" title="Unavailable" detail="Could not load Personal Model data.">
          <EmptyPanel title="Load failed" detail={error} />
        </Panel>
      )}

      {!dashboard && !error && (
        <Panel eyebrow="API" title="Loading" detail="Fetching Personal Model data.">
          <EmptyPanel title="Loading" detail="Preparing your personal model view." />
        </Panel>
      )}

      {dashboard && (
        <>
          <ProfileFactsPanel model={model} />
          <MindMapView model={model} />
          <div className={styles.palaceGrid}>
            {["identity", "world", "pulse", "journey"].map((lens) => (
              <LensQuadrant key={lens} lens={lens} slots={palace.lenses.get(lens) ?? []} refresh={refresh} />
            ))}
          </div>
          <SkillsPanel slots={palace.allSlots} refresh={refresh} />
          {loading && <p className={styles.routeHint}>Refreshing…</p>}
        </>
      )}
    </div>
  );
}
