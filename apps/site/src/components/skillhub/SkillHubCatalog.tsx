import React from "react";
import Link from "@docusaurus/Link";

import type {
  SkillHubCatalogData,
  SkillHubSiteEntry,
  SkillHubSiteExternalSource,
} from "../../generated/skillhubCatalog";
import {useLandingEffects} from "../useLandingEffects";

type SkillHubCatalogProps = {
  catalog: SkillHubCatalogData;
};

type CatalogTab = "bundled" | "external";

export function SkillHubCatalog({catalog}: SkillHubCatalogProps): React.JSX.Element {
  useLandingEffects();

  const [activeTab, setActiveTab] = React.useState<CatalogTab>("bundled");
  const [query, setQuery] = React.useState("");
  const [sectionFilter, setSectionFilter] = React.useState("all");
  const deferredQuery = React.useDeferredValue(query);
  const normalizedQuery = deferredQuery.trim().toLowerCase();

  const visibleSections = catalog.sections
    .map((section) => {
      const entries = section.entries.filter((entry) =>
        matchesEntry(entry, {
          normalizedQuery,
          sectionFilter,
        })
      );
      return {
        section_id: section.section_id,
        display_name: section.display_name,
        summary: section.summary,
        entry_count: entries.length,
        entries,
      };
    })
    .filter((section) => section.entries.length > 0);

  const visibleEntryCount = visibleSections.reduce((total, section) => total + section.entries.length, 0);
  const selectedSection =
    sectionFilter === "all"
      ? null
      : catalog.sections.find((section) => section.section_id === sectionFilter) ?? null;
  const bundledCount = catalog.stats.entry_count ?? catalog.entries.length;
  const sectionCount = catalog.stats.section_count ?? catalog.sections.length;
  const externalCount = catalog.external_sources.length;

  return (
    <div className="skillhub-page">
      <section className="skillhub-hero-panel skillhub-hero-panel-compact" data-reveal>
        <div className="skillhub-hero-copy">
          <span className="label">Skills</span>
          <h1>Browse the Elephant Agent skill shelf.</h1>
          <p className="skillhub-lede">
            Bundled skills already ship with the CLI. External sources stay explicit and install-only.
          </p>
        </div>

        <div className="skillhub-pill-row skillhub-hero-pill-row">
          <span className="info-pill">{bundledCount} bundled</span>
          <span className="info-pill">{sectionCount} sections</span>
          <span className="info-pill">{externalCount} external lanes</span>
        </div>

        <div className="skillhub-hero-toolbar">
          <div className="skillhub-detail-actions">
            <Link className="btn-pill btn-pill-strong" to="#skillhub-results">
              Browse bundled
            </Link>
            <Link className="btn-pill" to="/docs/capacities/skills/">
              Install guide
            </Link>
            <a className="btn-pill" href="https://skills.sh/" target="_blank" rel="noreferrer">
              skills.sh
            </a>
          </div>
        </div>
      </section>

      <section className="skillhub-controls-panel" id="skillhub-results">
        <div className="skillhub-shelf-head">
          <div>
            <span className="card-kicker">Catalog</span>
            <h2>{activeTab === "bundled" ? "Bundled" : "External"}</h2>
          </div>
          <p>
            {activeTab === "bundled"
              ? "Packaged skills from the Elephant Agent CLI."
              : "Static source lanes. Search and install stay in the CLI."}
          </p>
        </div>

        <div className="skillhub-tab-row" role="tablist" aria-label="Skill catalog tabs">
          <TabButton
            label={`Bundled (${bundledCount})`}
            active={activeTab === "bundled"}
            onClick={() =>
              React.startTransition(() => {
                setActiveTab("bundled");
              })
            }
          />
          <TabButton
            label={`External (${catalog.external_sources.length})`}
            active={activeTab === "external"}
            onClick={() =>
              React.startTransition(() => {
                setActiveTab("external");
              })
            }
          />
        </div>

        {activeTab === "bundled" ? (
          <>
            <div className="skillhub-control-grid skillhub-control-grid-minimal">
              <label className="skillhub-field">
                <span>Search</span>
                <input
                  type="search"
                  name="skillhub-query"
                  placeholder="Search by name, alias, keyword, or command"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                />
              </label>
              <label className="skillhub-field">
                <span>Section</span>
                <select
                  name="skillhub-section"
                  value={sectionFilter}
                  onChange={(event) => setSectionFilter(event.target.value)}
                >
                  <option value="all">All sections ({bundledCount})</option>
                  {catalog.sections.map((section) => (
                    <option key={section.section_id} value={section.section_id}>
                      {section.display_name} ({section.entry_count})
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="skillhub-result-bar">
              <div className="skillhub-result-copy">
                <strong>{visibleEntryCount}</strong>
                <span>{visibleEntryCount === 1 ? "bundled skill" : "bundled skills"}</span>
                {selectedSection ? (
                  <span className="skillhub-filter-hint">in {selectedSection.display_name}</span>
                ) : null}
              </div>
              {(normalizedQuery || sectionFilter !== "all") && (
                <button
                  type="button"
                  className="btn-pill skillhub-clear-button"
                  onClick={() =>
                    React.startTransition(() => {
                      setQuery("");
                      setSectionFilter("all");
                    })
                  }
                >
                  Reset
                </button>
              )}
            </div>

            {visibleSections.length > 0 ? (
              <div className="skillhub-list-block">
                {visibleSections.map((section) => (
                  <section
                    key={section.section_id}
                    id={`skillhub-section-${section.section_id}`}
                    className="skillhub-list-section"
                  >
                    <div className="skillhub-list-section-head">
                      <h3>{section.display_name}</h3>
                      <span>{section.entry_count === 1 ? "1 skill" : `${section.entry_count} skills`}</span>
                    </div>
                    <div className="skillhub-list-rows">
                      {section.entries.map((entry) => (
                        <SkillListRow key={entry.skill_id} entry={entry} />
                      ))}
                    </div>
                  </section>
                ))}
              </div>
            ) : (
              <section className="skillhub-empty-panel">
                <span className="card-kicker">No match</span>
                <h2>No bundled skill matches the current filter.</h2>
                <p>Reset the current search or section filter and try again.</p>
              </section>
            )}
          </>
        ) : (
          <>
            <div className="skillhub-result-bar">
              <div className="skillhub-result-copy">
                <strong>{externalCount}</strong>
                <span>
                  {externalCount === 1
                    ? "external source"
                    : "external sources"}
                </span>
              </div>
              <span className="skillhub-filter-hint">{catalog.operator_install_posture}</span>
            </div>

            <div className="skillhub-list-block skillhub-source-list">
              {catalog.external_sources.map((source) => (
                <ExternalSourceRow key={source.source_id} source={source} />
              ))}
            </div>
          </>
        )}
      </section>
    </div>
  );
}

function SkillListRow({entry}: {entry: SkillHubSiteEntry}): React.JSX.Element {
  return (
    <article className="skillhub-skill-row">
      <div className="skillhub-skill-row-main">
        <div className="skillhub-skill-row-heading">
          <Link className="skillhub-skill-row-title" to={entry.detail_path}>
            {entry.display_name}
          </Link>
        </div>
        <p className="skillhub-skill-row-summary">{entry.summary}</p>
        <div className="skillhub-skill-row-meta">
          <span>{entry.default_enabled_label}</span>
        </div>
      </div>
      <details className="skillhub-row-disclosure" open>
        <summary>Install and details</summary>
        <dl className="skillhub-row-disclosure-grid skillhub-row-detail-list">
          <div className="skillhub-row-detail">
            <dt>Install</dt>
            <dd>
              <code className="skillhub-command-line skillhub-list-command-line">
                {entry.install_command}
              </code>
            </dd>
          </div>
          <div className="skillhub-row-detail">
            <dt>Reference</dt>
            <dd>{entry.reference}</dd>
          </div>
          <div className="skillhub-row-detail">
            <dt>Runtime posture</dt>
            <dd>{entry.default_enabled_label}</dd>
          </div>
        </dl>
      </details>
      <div className="skillhub-row-actions">
        <Link className="btn-pill skillhub-row-link" to={entry.detail_path}>
          Open details
        </Link>
      </div>
    </article>
  );
}

function ExternalSourceRow({
  source,
}: {
  source: SkillHubSiteExternalSource;
}): React.JSX.Element {
  return (
    <article className="skillhub-source-row">
      <div className="skillhub-skill-row-main">
        <div className="skillhub-skill-row-heading">
          <h3>{source.display_name}</h3>
          <span className="info-pill skillhub-row-pill">External</span>
        </div>
        <p className="skillhub-skill-row-summary">{source.summary}</p>
        <div className="skillhub-skill-row-meta">
          <span>{source.trust_posture}</span>
          <code className="skillhub-inline-code">{source.reference_pattern}</code>
        </div>
      </div>
      <details className="skillhub-row-disclosure">
        <summary>CLI commands</summary>
        <dl className="skillhub-row-disclosure-grid skillhub-row-detail-list">
          <div className="skillhub-row-detail">
            <dt>Search</dt>
            <dd>
              <code className="skillhub-command-line skillhub-list-command-line">
                {source.search_command}
              </code>
            </dd>
          </div>
          <div className="skillhub-row-detail">
            <dt>Install</dt>
            <dd>
              <code className="skillhub-command-line skillhub-list-command-line">
                {source.install_command}
              </code>
            </dd>
          </div>
        </dl>
      </details>
    </article>
  );
}

function TabButton({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}): React.JSX.Element {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={active}
      className={`skillhub-tab${active ? " skillhub-tab-active" : ""}`}
      onClick={onClick}
    >
      {label}
    </button>
  );
}

function matchesEntry(
  entry: SkillHubSiteEntry,
  {
    normalizedQuery,
    sectionFilter,
  }: {
    normalizedQuery: string;
    sectionFilter: string;
  }
): boolean {
  if (sectionFilter !== "all" && entry.section_id !== sectionFilter) {
    return false;
  }
  if (!normalizedQuery) {
    return true;
  }
  return searchableEntryText(entry).includes(normalizedQuery);
}

function searchableEntryText(entry: SkillHubSiteEntry): string {
  return [
    entry.display_name,
    entry.summary,
    entry.reference,
    entry.section_display_name,
    entry.install_reference,
    ...entry.aliases,
    ...entry.trigger_phrases,
    ...entry.keywords,
    ...entry.platforms,
    ...entry.requires_tools,
    ...entry.requires_toolsets,
    ...entry.required_environment_variables,
  ]
    .join(" ")
    .toLowerCase();
}
