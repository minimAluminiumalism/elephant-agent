import React from "react";

import type {SkillHubSiteEntry} from "../../generated/skillhubCatalog";
import {SkillHubDetail} from "./SkillHubDetail";
import {SkillHubPageFrame} from "./SkillHubPageFrame";

type SkillHubDetailPageProps = {
  entry?: SkillHubSiteEntry;
};

const missingEntryDescription =
  "This Skills page is generated from the canonical Elephant Agent skill catalog. The requested packaged skill is not present in the current export.";

export function SkillHubDetailPage({entry}: SkillHubDetailPageProps): React.JSX.Element {
  const title = entry ? `${entry.display_name} | Skills` : "Skill not found | Skills";
  const description = entry?.summary ?? missingEntryDescription;

  return (
    <SkillHubPageFrame title={title} description={description}>
      <div className="skillhub-container">
        <SkillHubDetail entry={entry} />
      </div>
    </SkillHubPageFrame>
  );
}
