import React from "react";

import {SkillHubCatalog} from "../../components/skillhub/SkillHubCatalog";
import {SkillHubPageFrame} from "../../components/skillhub/SkillHubPageFrame";
import {skillHubCatalog} from "../../generated/skillhubCatalog";

export default function SkillHubIndexPage(): React.JSX.Element {
  return (
    <SkillHubPageFrame title="Skills" description={skillHubCatalog.summary}>
      <div className="skillhub-container">
        <SkillHubCatalog catalog={skillHubCatalog} />
      </div>
    </SkillHubPageFrame>
  );
}
