import React from "react";

import {SkillHubDetailPage} from "../../../components/skillhub/SkillHubDetailPage";
import {skillHubCatalogById} from "../../../generated/skillhubCatalog";

export default function SkillHubSongwritingAndAiMusicPage(): React.JSX.Element {
  return <SkillHubDetailPage entry={skillHubCatalogById["songwriting-and-ai-music"]} />;
}
