import React from "react";

import {SkillHubDetailPage} from "../../../components/skillhub/SkillHubDetailPage";
import {skillHubCatalogById} from "../../../generated/skillhubCatalog";

export default function SkillHubPlanPage(): React.JSX.Element {
  return <SkillHubDetailPage entry={skillHubCatalogById["plan"]} />;
}
