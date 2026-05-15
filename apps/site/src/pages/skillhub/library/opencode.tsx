import React from "react";

import {SkillHubDetailPage} from "../../../components/skillhub/SkillHubDetailPage";
import {skillHubCatalogById} from "../../../generated/skillhubCatalog";

export default function SkillHubOpencodePage(): React.JSX.Element {
  return <SkillHubDetailPage entry={skillHubCatalogById["opencode"]} />;
}
