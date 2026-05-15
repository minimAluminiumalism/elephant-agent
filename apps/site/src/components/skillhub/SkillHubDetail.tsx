import React from "react";
import Link from "@docusaurus/Link";

import type {SkillHubSiteEntry} from "../../generated/skillhubCatalog";
import {skillHubCatalog} from "../../generated/skillhubCatalog";
import {useLandingEffects} from "../useLandingEffects";

type SkillHubDetailProps = {
  entry?: SkillHubSiteEntry;
};

export function SkillHubDetail({entry}: SkillHubDetailProps): React.JSX.Element {
  useLandingEffects();

  if (!entry) {
    return (
      <div className="skillhub-page">
        <section className="skillhub-empty-panel" data-reveal>
          <span className="label">Skills</span>
          <h1>Skill not found.</h1>
          <p className="skillhub-lede">
            This page is generated from the packaged Elephant Agent catalog. Return to the Skills index and
            browse a current entry.
          </p>
          <Link className="btn-pill" to="/skillhub/">
            Back to Skills
          </Link>
        </section>
      </div>
    );
  }

  const section = skillHubCatalog.sections.find((candidate) => candidate.section_id === entry.section_id);
  const siblingEntries =
    section?.entries.filter((candidate) => candidate.skill_id !== entry.skill_id).slice(0, 3) ?? [];
  const catalogIndex = skillHubCatalog.entries.findIndex(
    (candidate) => candidate.skill_id === entry.skill_id
  );
  const previousEntry = catalogIndex > 0 ? skillHubCatalog.entries[catalogIndex - 1] : undefined;
  const nextEntry =
    catalogIndex >= 0 && catalogIndex < skillHubCatalog.entries.length - 1
      ? skillHubCatalog.entries[catalogIndex + 1]
      : undefined;
  const metadataGroups = buildMetadataGroups(entry);
  const factRows = [
    {label: "Skill ID", value: entry.skill_id},
    {label: "Section", value: entry.section_display_name},
    {label: "Runtime posture", value: entry.default_enabled_label},
    {label: "Install command", value: entry.install_command},
    {label: "Trust posture", value: entry.trust_level},
  ];

  return (
    <div className="skillhub-page">
      <div className="skillhub-backlink" data-reveal>
        <Link to="/skillhub/">Skills</Link>
        {section ? (
          <>
            <span>/</span>
            <Link to={`/skillhub/#skillhub-section-${section.section_id}`}>{section.display_name}</Link>
          </>
        ) : null}
      </div>

      <section className="skillhub-hero-panel skillhub-detail-hero-panel" data-reveal>
        <div className="skillhub-detail-hero-copy">
          <span className="label">{entry.section_display_name}</span>
          <h1>{entry.display_name}</h1>
          <p className="skillhub-lede">{entry.summary}</p>
          <div className="skillhub-pill-row">
            <span className="info-pill">{entry.default_enabled_label}</span>
            <span className="info-pill">{entry.source_label}</span>
          </div>
        </div>

        <div className="skillhub-detail-install-strip">
          <div className="skillhub-command-group">
            <span className="card-kicker">CLI install command</span>
            <code className="skillhub-command-line skillhub-detail-command-line">
              {entry.install_command}
            </code>
          </div>
          <div className="skillhub-detail-actions">
            <Link className="btn-pill btn-pill-strong" to="/docs/capacities/skills/">
              Install guide
            </Link>
            {entry.source_detail_url ? (
              <a className="btn-pill" href={entry.source_detail_url} target="_blank" rel="noreferrer">
                Source detail
              </a>
            ) : null}
            {entry.source_repo_url ? (
              <a className="btn-pill" href={entry.source_repo_url} target="_blank" rel="noreferrer">
                Source repo
              </a>
            ) : null}
          </div>
        </div>
      </section>

      <div className="skillhub-detail-grid">
        <section className="skillhub-panel skillhub-detail-copy-panel" data-reveal>
          <span className="card-kicker">Overview</span>
          <div className="skillhub-detail-prose">
            <p>{entry.packaging_posture}</p>
            <p>{entry.install_posture}</p>
            {entry.source_id !== "builtin" ? <p>{entry.operator_install_posture}</p> : null}
          </div>

          {metadataGroups.length > 0 ? (
            <div className="skillhub-detail-tag-groups">
              {metadataGroups.map((group) => (
                <section key={group.label} className="skillhub-detail-tag-group">
                  <h2>{group.label}</h2>
                  <div className="skillhub-tag-list">
                    {group.values.map((value) => (
                      <span key={`${group.label}:${value}`} className="info-pill">
                        {value}
                      </span>
                    ))}
                  </div>
                </section>
              ))}
            </div>
          ) : null}
        </section>

        <aside className="skillhub-panel skillhub-facts-panel" data-reveal>
          <span className="card-kicker">Facts</span>
          <dl className="skillhub-fact-list">
            {factRows.map((row) => (
              <div key={row.label}>
                <dt>{row.label}</dt>
                <dd>{row.value}</dd>
              </div>
            ))}
          </dl>

          <div className="skillhub-detail-context-links">
            {section ? (
              <Link className="btn-pill" to={`/skillhub/#skillhub-section-${section.section_id}`}>
                Browse section
              </Link>
            ) : null}
            {previousEntry ? (
              <Link className="btn-pill" to={previousEntry.detail_path}>
                Previous
              </Link>
            ) : null}
            {nextEntry ? (
              <Link className="btn-pill" to={nextEntry.detail_path}>
                Next
              </Link>
            ) : null}
          </div>
        </aside>
      </div>

      {siblingEntries.length > 0 ? (
        <section className="skillhub-section-panel skillhub-related-panel" data-reveal>
          <div className="skillhub-section-head skillhub-related-head">
            <div className="skillhub-related-copy">
              <span className="card-kicker">Continue browsing</span>
              <h2>Also in {entry.section_display_name}</h2>
              {section ? <p>{section.summary}</p> : null}
            </div>
            {section ? (
              <Link className="btn-pill" to={`/skillhub/#skillhub-section-${section.section_id}`}>
                View full section
              </Link>
            ) : null}
          </div>

          <div className="skillhub-related-grid">
            {siblingEntries.map((sibling) => (
              <RelatedSkillCard key={sibling.skill_id} entry={sibling} />
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}

function RelatedSkillCard({entry}: {entry: SkillHubSiteEntry}): React.JSX.Element {
  return (
    <article className="skillhub-related-card">
      <div className="skillhub-related-card-copy">
        <Link className="skillhub-skill-row-title" to={entry.detail_path}>
          {entry.display_name}
        </Link>
        <p>{entry.summary}</p>
      </div>
      <div className="skillhub-related-card-footer">
        <code className="skillhub-inline-code">{entry.reference}</code>
        <Link className="btn-pill skillhub-row-link" to={entry.detail_path}>
          View skill
        </Link>
      </div>
    </article>
  );
}

function buildMetadataGroups(
  entry: SkillHubSiteEntry
): Array<{label: string; values: readonly string[]}> {
  return [
    {label: "Aliases", values: entry.aliases},
    {label: "Trigger phrases", values: entry.trigger_phrases},
    {label: "Keywords", values: entry.keywords},
    {label: "Platforms", values: entry.platforms},
    {label: "Required tools", values: entry.requires_tools},
    {label: "Required toolsets", values: entry.requires_toolsets},
    {
      label: "Required environment variables",
      values: entry.required_environment_variables,
    },
  ].filter((group) => group.values.length > 0);
}
