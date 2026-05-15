import React from "react";

import {SkillHubDetailPage} from "../../../components/skillhub/SkillHubDetailPage";
import {skillHubCatalogById} from "../../../generated/skillhubCatalog";

export default function SkillHubP5jsPage(): React.JSX.Element {
  return <SkillHubDetailPage entry={skillHubCatalogById["p5js"]} />;
}
