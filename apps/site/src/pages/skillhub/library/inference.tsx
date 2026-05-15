import React from "react";

import {SkillHubDetailPage} from "../../../components/skillhub/SkillHubDetailPage";
import {skillHubCatalogById} from "../../../generated/skillhubCatalog";

export default function SkillHubInferencePage(): React.JSX.Element {
  return <SkillHubDetailPage entry={skillHubCatalogById["inference"]} />;
}
