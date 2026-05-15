import React from "react";
import Head from "@docusaurus/Head";
import Layout from "@theme/Layout";

type SkillHubPageFrameProps = {
  title: string;
  description: string;
  children: React.ReactNode;
};

const pageKeywords = [
  "Elephant Agent Skills",
  "bundled skills",
  "external skills",
  "CLI skills",
  "agent skills",
  "static skill catalog",
].join(", ");

export function SkillHubPageFrame({
  title,
  description,
  children,
}: SkillHubPageFrameProps): React.JSX.Element {
  const pageTitle = `${title} | Elephant Agent`;

  return (
    <Layout title={title} description={description} wrapperClassName="skillhub-route">
      <Head>
        <meta name="keywords" content={pageKeywords} />
        <meta property="og:title" content={pageTitle} />
        <meta property="og:description" content={description} />
        <meta name="twitter:title" content={pageTitle} />
        <meta name="twitter:description" content={description} />
      </Head>
      <canvas id="dither-canvas" aria-hidden="true" />
      <main className="skillhub-shell">{children}</main>
    </Layout>
  );
}
