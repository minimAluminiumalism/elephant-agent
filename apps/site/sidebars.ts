import type {SidebarsConfig} from "@docusaurus/plugin-content-docs";

const sidebars: SidebarsConfig = {
  docs: [
    "intro",
    {
      type: "category",
      label: "Getting Started",
      collapsible: false,
      collapsed: false,
      items: [
        "getting-started/quickstart",
        "getting-started/installation",
        "getting-started/providers",
      ],
    },
    {
      type: "category",
      label: "Philosophy",
      collapsible: false,
      collapsed: false,
      items: [
        "philosophy/overview",
        "philosophy/design-principles",
        "philosophy/system-model",
      ],
    },
    {
      type: "category",
      label: "User Interface",
      collapsible: false,
      collapsed: false,
      items: [
        "user-interface/cli-tui",
        "user-interface/dashboard",
      ],
    },
    {
      type: "category",
      label: "Capacities",
      collapsible: false,
      collapsed: false,
      items: [
        "capacities/skills",
        "capacities/tools",
        "capacities/messaging",
        "capacities/embeddings",
        "capacities/memory",
        "capacities/continuity",
      ],
    },
    {
      type: "category",
      label: "Learning",
      collapsible: false,
      collapsed: false,
      items: [
        "learning/proactive",
        "learning/background",
        "learning/correctable",
      ],
    },
    {
      type: "category",
      label: "Reference",
      collapsible: false,
      collapsed: false,
      items: ["reference/cli"],
    },
    {
      type: "category",
      label: "Help",
      collapsible: false,
      collapsed: false,
      items: ["help/troubleshooting"],
    },
  ],
};

export default sidebars;
