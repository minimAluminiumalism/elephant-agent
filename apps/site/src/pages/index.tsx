import React from "react";
import Head from "@docusaurus/Head";
import Layout from "@theme/Layout";
import Link from "@docusaurus/Link";

import {githubRepoUrl} from "../components/siteData";
import {useLandingEffects} from "../components/useLandingEffects";

const installCommand = "curl -fsSL https://elephant.agentic-in.ai/install.sh | bash";
const pageTitle = "Personal-model-first AI";
const pageTitleWithSite = `${pageTitle} | Elephant Agent`;
const pageDescription =
  "Elephant Agent is personal-model-first AI: it turns memory into correctable understanding, then gets curious at your pace.";
const pageKeywords = [
  "personal-model-first AI",
  "personal AI agent",
  "proactive curiosity",
  "CLI AI agent",
  "personal model",
  "elephant continuity",
  "claim-aware recall",
  "context recovery",
  "Elephant Agent",
].join(", ");
const homepageUrl = "https://elephant.agentic-in.ai/";
const structuredData = JSON.stringify({
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "Elephant Agent",
  alternateName: pageTitle,
  description: pageDescription,
  applicationCategory: "DeveloperApplication",
  operatingSystem: "macOS, Linux",
  url: homepageUrl,
  downloadUrl: "https://elephant.agentic-in.ai/install.sh",
  offers: {
    "@type": "Offer",
    price: "0",
    priceCurrency: "USD",
  },
});

const problemRows = [
  {
    name: "Forgetting",
    body:
      "You repeat the same people, projects, risks, and preferences every time.",
    note: "Elephant Agent carries the useful understanding forward.",
    vs: "Others add memory slots. Elephant Agent grows a Personal Model.",
  },
  {
    name: "Drift",
    body:
      "A strong answer today can still forget what mattered yesterday.",
    note: "Elephant Agent resumes from the right thread.",
    vs: "Others extend context windows. Elephant Agent picks up the right thread.",
  },
  {
    name: "Passivity",
    body:
      "Most agents wait for you to explain every missing piece.",
    note: "Elephant Agent can ask when the answer would change future help.",
    vs: "Others wait. Elephant Agent gets curious at your pace.",
  },
];

const thesisCards = [
  {
    kicker: "01 →",
    title: "Personal Model first",
    body: "Identity, World, Pulse, and Journey give the agent a typed way to understand one person.",
  },
  {
    kicker: "02 →",
    title: "Proactive curiosity",
    body: "Quiet, balanced, or active. Elephant Agent asks only when the answer would change how it helps.",
  },
  {
    kicker: "03",
    title: "Continuity you can trust",
    body: "Claims are correctable, inspectable, and tied back to evidence instead of hidden profiling.",
  },
];

export default function HomePage(): React.JSX.Element {
  useLandingEffects();

  return (
    <Layout
      title={pageTitle}
      description={pageDescription}
    >
      <Head>
        <meta name="keywords" content={pageKeywords} />
        <meta property="og:title" content={pageTitleWithSite} />
        <meta property="og:description" content={pageDescription} />
        <meta property="og:url" content={homepageUrl} />
        <meta name="twitter:title" content={pageTitleWithSite} />
        <meta name="twitter:description" content={pageDescription} />
        <script type="application/ld+json">{structuredData}</script>
      </Head>
      <canvas id="dither-canvas" aria-hidden="true" />

      <main id="top" className="page-shell">
        <section className="manifesto-section">
          <div className="container">
            <div className="grid manifesto-grid">
              <div className="manifesto-title-wrap">
                <span className="label" data-reveal>
                  Warm personal AI
                </span>
                <h1 className="manifesto-title" data-reveal>
                  <span>Elephant Agent</span>
                </h1>
              </div>

              <div className="manifesto-copy" data-reveal>
                <p className="manifesto-hook">
                  Elephants never forget.
                </p>
                <p>
                  Memory is the beginning. Elephant Agent grows a Personal
                  Model so the right people, risks, rhythms, and decisions can
                  guide what happens next.
                </p>
                <div className="pill-row">
                  <span className="info-pill info-pill-highlight">Warm memory</span>
                  <span className="info-pill info-pill-highlight">PM-first</span>
                  <span className="info-pill info-pill-highlight">Gentle curiosity</span>
                </div>
                <div className="cta-row">
                  <a className="btn-pill btn-pill-strong" href="#quickstart">
                    Create yours
                  </a>
                  <a
                    className="btn-pill"
                    href={githubRepoUrl}
                    target="_blank"
                    rel="noreferrer"
                  >
                    GitHub
                  </a>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="why" className="section section-rule">
          <div className="container">
            <div className="elephant-narrative">
              <div className="elephant-narrative-copy" data-reveal>
                <h2>Why Elephant</h2>
                <p>
                  “Elephants never forget” sounds like folklore, but it points
                  to something real and beautiful. Elephants recognize members
                  of their <strong className="memory-key">herd</strong> by sight and smell, remember{" "}
                  <strong className="memory-key">danger cues</strong>, and
                  return to important places long after the last visit. Their
                  memory is not a giant hard drive. It is a{" "}
                  <strong className="memory-key">living map</strong> of who is
                  close, where safety may be found, and what experience has
                  already taught the herd.
                </p>
                <p>
                  The most moving memories are not only about survival.
                  Elephants remember other elephants, other animals, and humans
                  who left a deep impression, sometimes after decades apart.
                  Their hippocampus is strongly tied to{" "}
                  <strong className="memory-key">emotion</strong>, helping
                  important experiences become{" "}
                  <strong className="memory-key">long-term memory</strong> instead of
                  noise. That is why memory can become care: a remembered bond,
                  a remembered danger, a remembered route through a dry season.
                </p>
                <p>
                  Elephant intelligence is gentle, social, and practical.
                  Older matriarchs can help a herd read the warning signs of
                  drought because they have lived through them before. Elephants
                  solve problems alone and together, communicate through body
                  signals, calls, and low-frequency rumbles, and show a rare
                  tenderness around grief, protection, comfort, and fairness.
                  Their memory becomes{" "}
                  <strong className="memory-key">judgment</strong> because it is joined to{" "}
                  <strong className="memory-key">relationship</strong>.
                </p>
                <p>
                  That is the inspiration behind Elephant Agent. A personal AI
                  should not archive every transcript and call it memory. It
                  should turn memory into a{" "}
                  <strong className="memory-key">correctable Personal Model</strong>:
                  episodic traces, social context, risk signals, current
                  rhythms, and long-term lessons that help tomorrow feel
                  continuous. Not more storage. A living understanding that can
                  ask, learn, and be corrected.
                </p>
              </div>
            </div>

            <div className="problem-list">
              {problemRows.map((problem) => (
                <article key={problem.name} className="problem-row" data-reveal>
                  <div className="problem-name">{problem.name}</div>
                  <p className="problem-text">{problem.body}</p>
                  <p className="problem-note">{problem.note}</p>
                  {problem.vs && <p className="problem-vs">{problem.vs}</p>}
                </article>
              ))}
            </div>
          </div>
        </section>

        <section id="quickstart" className="section section-rule">
          <div className="container">
            <div className="quickstart-panel" data-reveal>
              <div className="quickstart-head">
                <span className="label">CLI-first quickstart</span>
                <h2>Install. Create. Return.</h2>
                <p>
                  Start with a local elephant, then come back through wake when
                  the same path should continue.
                </p>
              </div>

              <div className="quickstart-command-card">
                <span className="card-kicker">One-line install</span>
                <span className="command-snippet">{installCommand}</span>
              </div>

              <div className="quickstart-steps">
                <article>
                  <span>01</span>
                  <strong>Install the launcher</strong>
                  <p>
                    The installer writes <code>elephant</code> and prepares the
                    durable home at <code>~/.elephant</code>.
                  </p>
                </article>
                <article>
                  <span>02</span>
                  <strong>Shape the first elephant</strong>
                  <p>
                    Run <code>elephant init</code> to choose provider, recall,
                    curiosity, and the first Personal Model anchors.
                  </p>
                </article>
                <article>
                  <span>03</span>
                  <strong>Wake the same path</strong>
                  <p>
                    Use <code>elephant wake</code> for chat, or open the
                    Dashboard to inspect what it carries forward.
                  </p>
                </article>
              </div>

              <div className="quickstart-links">
                <Link to="/docs/getting-started/installation/">Install guide</Link>
                <Link to="/docs/getting-started/quickstart/">Quickstart</Link>
                <Link to="/docs/getting-started/providers/">Provider setup</Link>
                <Link to="/docs/reference/cli/">CLI reference</Link>
              </div>
            </div>
          </div>
        </section>

        <section id="thesis" className="section section-rule">
          <div className="container">
            <div className="section-head">
              <div>
                <span className="label" data-reveal>
                  What makes it different
                </span>
                <h2 data-reveal>Small core. Real continuity.</h2>
              </div>
              <p data-reveal>
                Tools, skills, models, cron, messaging, TUI, and Dashboard sit
                around the Personal Model instead of replacing it.
              </p>
            </div>

            <div className="card-grid card-grid-3">
              {thesisCards.map((card) => (
                <article key={card.title} className="manifesto-card thesis-card" data-reveal>
                  <span className="card-kicker">{card.kicker}</span>
                  <h3>{card.title}</h3>
                  <p>{card.body}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="section section-rule">
          <div className="container">
            <div className="closing-grid">
              <div>
                <span className="label" data-reveal>
                  Open source
                </span>
                <h2 data-reveal>Personal AI should be inspectable.</h2>
              </div>
              <div className="closing-copy" data-reveal>
                <p>
                  Elephant Agent keeps the personal layer visible: claims, questions,
                  evidence, providers, cron, logs, tools, skills, and local
                  semantic recall.
                </p>
                <div className="cta-row">
                  <a className="btn-pill" href="#quickstart">
                    Install
                  </a>
                  <Link className="btn-pill" to="/docs/">
                    Documentation
                  </Link>
                  <a
                    className="btn-pill btn-pill-strong"
                    href={githubRepoUrl}
                    target="_blank"
                    rel="noreferrer"
                  >
                    GitHub
                  </a>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}
