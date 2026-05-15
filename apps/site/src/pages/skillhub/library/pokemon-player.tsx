import React from "react";

import {SkillHubDetailPage} from "../../../components/skillhub/SkillHubDetailPage";
import {skillHubCatalogById} from "../../../generated/skillhubCatalog";

export default function SkillHubPokemonPlayerPage(): React.JSX.Element {
  return <SkillHubDetailPage entry={skillHubCatalogById["pokemon-player"]} />;
}
