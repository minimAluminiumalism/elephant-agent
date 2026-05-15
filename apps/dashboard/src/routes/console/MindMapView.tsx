import React, { useCallback, useMemo, useState } from "react";
import ReactFlow, {
  type Node,
  type Edge,
  useNodesState,
  useEdgesState,
  MiniMap,
  Controls,
  Background,
  BackgroundVariant,
  Position,
  type NodeTypes,
  type NodeMouseHandler,
  Handle,
} from "reactflow";
import dagre from "@dagrejs/dagre";
import "reactflow/dist/style.css";

import type { DashboardJson, DashboardRow } from "../../types/dashboard";
import styles from "./MindMapView.module.css";

// --- Helpers ---

function asRows(value: DashboardJson | undefined): DashboardRow[] {
  return Array.isArray(value)
    ? value.filter((item): item is DashboardRow => item !== null && typeof item === "object" && !Array.isArray(item))
    : [];
}

function valueOf(row: DashboardRow | null | undefined, key: string, fallback = ""): string {
  if (!row) return fallback;
  const item = row[key];
  if (item === null || item === undefined || item === "") return fallback;
  if (typeof item === "string" || typeof item === "number" || typeof item === "boolean") return String(item);
  return JSON.stringify(item);
}

function jsonObject(value: DashboardJson | undefined): DashboardRow {
  return value !== null && typeof value === "object" && !Array.isArray(value) ? value : {};
}

// --- Constants ---

const LENS_COLORS: Record<string, string> = {
  identity: "#e8a87c",
  pulse:    "#85dcb0",
  journey:  "#9bb5e0",
  world:    "#d4a5d0",
};

// Each lens radiates in a different direction from center
const LENS_DIRECTIONS: Record<string, { rankdir: "TB" | "BT" | "LR" | "RL"; offsetX: number; offsetY: number }> = {
  world:    { rankdir: "RL", offsetX: -350, offsetY: -350 }, // top-left
  identity: { rankdir: "LR", offsetX: 350, offsetY: -350 }, // top-right
  pulse:    { rankdir: "LR", offsetX: 350, offsetY: 350 },  // bottom-right
  journey:  { rankdir: "RL", offsetX: -350, offsetY: 350 }, // bottom-left
};

const NODE_SIZES: Record<string, { w: number; h: number }> = {
  mindMapRoot: { w: 160, h: 50 },
  mindMapLens: { w: 130, h: 42 },
  mindMapDomain: { w: 120, h: 36 },
  mindMapEntity: { w: 130, h: 36 },
  mindMapQualifier: { w: 220, h: 56 },
};

// --- Graph Building ---

type FactEntry = {
  lens: string;
  domain: string;
  entity: string;
  qualifier: string;
  text: string;
};

function parseActiveFacts(model: DashboardRow | undefined): FactEntry[] {
  const facts = asRows(model?.personal_model_all_facts).length
    ? asRows(model?.personal_model_all_facts)
    : asRows(model?.personal_model_facts);

  const result: FactEntry[] = [];
  for (const fact of facts) {
    if (valueOf(fact, "status", "active") !== "active") continue;
    const metadata = jsonObject(fact.metadata);
    const topic = valueOf(metadata, "topic", valueOf(fact, "topic", ""));
    const parts = topic.split(".").filter(Boolean);
    // topic format: lens.domain.entity.qualifier[.more...]
    // Route by topic prefix (authoritative); fall back to stored lens field.
    const topicPrefix = parts[0] ?? "";
    const knownLenses = new Set(["identity", "world", "pulse", "journey"]);
    const storedLens = valueOf(fact, "lens", "");
    const lens = knownLenses.has(topicPrefix) ? topicPrefix : (knownLenses.has(storedLens) ? storedLens : "identity");
    const domain = parts[1] ?? parts[0] ?? "general";
    const entity = parts[2] ?? parts[1] ?? "general";
    const qualifier = parts.slice(3).join(".") || parts[2] || "detail";
    const text = valueOf(fact, "text", "");
    result.push({ lens, domain, entity, qualifier, text });
  }
  return result;
}

function buildLensSubgraph(
  lens: string,
  entries: FactEntry[],
  expandedEntities: Set<string>,
): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = [];
  const edges: Edge[] = [];

  const dir = LENS_DIRECTIONS[lens] ?? LENS_DIRECTIONS.identity;

  // For RL: parent outputs from Left, child receives on Right
  // For LR: parent outputs from Right, child receives on Left
  const sourceHandleId = dir.rankdir === "RL" ? "s-left" : dir.rankdir === "LR" ? "s-right" : dir.rankdir === "TB" ? "s-bottom" : "s-top";
  const targetHandleId = dir.rankdir === "RL" ? "t-right" : dir.rankdir === "LR" ? "t-left" : dir.rankdir === "TB" ? "t-top" : "t-bottom";

  // Lens root
  const lensId = `lens-${lens}`;
  nodes.push({
    id: lensId,
    type: "mindMapLens",
    data: { label: lens.charAt(0).toUpperCase() + lens.slice(1), lens },
    position: { x: 0, y: 0 },
  });

  const domainSet = new Set<string>();
  const entitySet = new Set<string>();
  const qualifierSet = new Set<string>();

  for (const entry of entries) {
    const domainId = `domain-${lens}-${entry.domain}`;
    const entityId = `entity-${lens}-${entry.domain}-${entry.entity}`;
    const qualifierId = `qual-${lens}-${entry.domain}-${entry.entity}-${entry.qualifier}`;

    // Domain
    if (!domainSet.has(entry.domain)) {
      domainSet.add(entry.domain);
      nodes.push({
        id: domainId,
        type: "mindMapDomain",
        data: { label: entry.domain, lens },
        position: { x: 0, y: 0 },
      });
      edges.push({
        id: `e-${lensId}-${domainId}`,
        source: lensId,
        target: domainId,
        sourceHandle: sourceHandleId,
        targetHandle: targetHandleId,
        style: { stroke: LENS_COLORS[lens] ?? "#888", strokeWidth: 1.5, opacity: 0.7 },
      });
    }

    // Entity (collapsible)
    const entityKey = `${entry.domain}-${entry.entity}`;
    if (!entitySet.has(entityKey)) {
      entitySet.add(entityKey);
      const isExpanded = expandedEntities.has(entityId);
      nodes.push({
        id: entityId,
        type: "mindMapEntity",
        data: { label: entry.entity, lens, expandable: true, expanded: isExpanded },
        position: { x: 0, y: 0 },
      });
      edges.push({
        id: `e-${domainId}-${entityId}`,
        source: domainId,
        target: entityId,
        sourceHandle: sourceHandleId,
        targetHandle: targetHandleId,
        style: { stroke: LENS_COLORS[lens] ?? "#888", strokeWidth: 1, opacity: 0.5 },
      });
    }

    // Qualifier (only if entity is expanded)
    if (expandedEntities.has(entityId)) {
      const qualKey = `${entry.domain}-${entry.entity}-${entry.qualifier}`;
      if (!qualifierSet.has(qualKey)) {
        qualifierSet.add(qualKey);
        nodes.push({
          id: qualifierId,
          type: "mindMapQualifier",
          data: { label: entry.qualifier, factText: entry.text, lens },
          position: { x: 0, y: 0 },
        });
        edges.push({
          id: `e-${entityId}-${qualifierId}`,
          source: entityId,
          target: qualifierId,
          sourceHandle: sourceHandleId,
          targetHandle: targetHandleId,
          style: { stroke: LENS_COLORS[lens] ?? "#888", strokeWidth: 1, opacity: 0.35 },
        });
      }
    }
  }

  return layoutSubgraph(nodes, edges, dir.rankdir);
}

function layoutSubgraph(
  nodes: Node[],
  edges: Edge[],
  rankdir: "TB" | "BT" | "LR" | "RL",
): { nodes: Node[]; edges: Edge[] } {
  if (!nodes.length) return { nodes: [], edges: [] };

  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir, nodesep: 40, ranksep: 110, edgesep: 20 });

  for (const node of nodes) {
    const size = NODE_SIZES[node.type ?? "mindMapEntity"] ?? { w: 140, h: 40 };
    g.setNode(node.id, { width: size.w, height: size.h });
  }
  for (const edge of edges) {
    g.setEdge(edge.source, edge.target);
  }

  dagre.layout(g);

  const sourcePos = rankdir === "RL" ? Position.Left : rankdir === "LR" ? Position.Right : rankdir === "TB" ? Position.Bottom : Position.Top;
  const targetPos = rankdir === "RL" ? Position.Right : rankdir === "LR" ? Position.Left : rankdir === "TB" ? Position.Top : Position.Bottom;

  const laidOut = nodes.map((node) => {
    const pos = g.node(node.id);
    const size = NODE_SIZES[node.type ?? "mindMapEntity"] ?? { w: 140, h: 40 };
    return {
      ...node,
      position: { x: pos.x - size.w / 2, y: pos.y - size.h / 2 },
      sourcePosition: sourcePos,
      targetPosition: targetPos,
    };
  });

  return { nodes: laidOut, edges };
}

function buildFullGraph(
  model: DashboardRow | undefined,
  expandedEntities: Set<string>,
): { nodes: Node[]; edges: Edge[] } {
  const allFacts = parseActiveFacts(model);
  const allNodes: Node[] = [];
  const allEdges: Edge[] = [];

  // Root node at center
  allNodes.push({
    id: "root",
    type: "mindMapRoot",
    data: { label: "Personal Model" },
    position: { x: 0, y: 0 },
  });

  // Group facts by lens
  const byLens = new Map<string, FactEntry[]>();
  for (const f of allFacts) {
    byLens.set(f.lens, [...(byLens.get(f.lens) ?? []), f]);
  }

  for (const [lens, entries] of byLens) {
    const dir = LENS_DIRECTIONS[lens] ?? LENS_DIRECTIONS.identity;    const { nodes, edges } = buildLensSubgraph(lens, entries, expandedEntities);

    // Find the lens node to compute offset — the lens node is the anchor
    const lensNode = nodes.find((n) => n.id === `lens-${lens}`);
    if (!lensNode) continue;

    // Offset: place lens node at the direction offset, shift all nodes relative
    const dx = dir.offsetX - lensNode.position.x;
    const dy = dir.offsetY - lensNode.position.y;

    for (const node of nodes) {
      allNodes.push({ ...node, position: { x: node.position.x + dx, y: node.position.y + dy } });
    }
    allEdges.push(...edges);

    // Edge from root to lens — pick correct handle based on direction
    // Root outputs toward the lens; lens receives from root direction
    const rootSourceHandle = dir.rankdir === "RL" ? "s-left" : dir.rankdir === "LR" ? "s-right" : dir.rankdir === "BT" ? "s-top" : "s-bottom";
    const lensTargetHandle = dir.rankdir === "RL" ? "t-right" : dir.rankdir === "LR" ? "t-left" : dir.rankdir === "BT" ? "t-bottom" : "t-top";
    allEdges.push({
      id: `e-root-lens-${lens}`,
      source: "root",
      target: `lens-${lens}`,
      sourceHandle: rootSourceHandle,
      targetHandle: lensTargetHandle,
      style: { stroke: LENS_COLORS[lens] ?? "#888", strokeWidth: 2 },
      animated: true,
    });
  }

  return { nodes: allNodes, edges: allEdges };
}

// --- Custom Nodes ---
// Each node renders handles on all 4 sides. The edge's sourceHandle/targetHandle
// picks which one to connect. This avoids ReactFlow guessing wrong.

function RootNode({ data }: { data: { label: string } }) {
  return (
    <div className={styles.nodeRoot}>
      <Handle type="source" position={Position.Right} id="s-right" className={styles.handle} />
      <Handle type="source" position={Position.Left} id="s-left" className={styles.handle} />
      <Handle type="source" position={Position.Top} id="s-top" className={styles.handle} />
      <Handle type="source" position={Position.Bottom} id="s-bottom" className={styles.handle} />
      <span>{data.label}</span>
    </div>
  );
}

function LensNode({ data }: { data: { label: string; lens: string } }) {
  return (
    <div className={styles.nodeLens} style={{ borderColor: LENS_COLORS[data.lens] ?? "#888" }}>
      <Handle type="target" position={Position.Right} id="t-right" className={styles.handle} />
      <Handle type="target" position={Position.Left} id="t-left" className={styles.handle} />
      <Handle type="target" position={Position.Top} id="t-top" className={styles.handle} />
      <Handle type="target" position={Position.Bottom} id="t-bottom" className={styles.handle} />
      <Handle type="source" position={Position.Right} id="s-right" className={styles.handle} />
      <Handle type="source" position={Position.Left} id="s-left" className={styles.handle} />
      <Handle type="source" position={Position.Top} id="s-top" className={styles.handle} />
      <Handle type="source" position={Position.Bottom} id="s-bottom" className={styles.handle} />
      <span>{data.label}</span>
    </div>
  );
}

function DomainNode({ data }: { data: { label: string; lens: string } }) {
  return (
    <div className={styles.nodeDomain} style={{ borderColor: `${LENS_COLORS[data.lens] ?? "#888"}80` }}>
      <Handle type="target" position={Position.Right} id="t-right" className={styles.handle} />
      <Handle type="target" position={Position.Left} id="t-left" className={styles.handle} />
      <Handle type="target" position={Position.Top} id="t-top" className={styles.handle} />
      <Handle type="target" position={Position.Bottom} id="t-bottom" className={styles.handle} />
      <Handle type="source" position={Position.Right} id="s-right" className={styles.handle} />
      <Handle type="source" position={Position.Left} id="s-left" className={styles.handle} />
      <Handle type="source" position={Position.Top} id="s-top" className={styles.handle} />
      <Handle type="source" position={Position.Bottom} id="s-bottom" className={styles.handle} />
      <span>{data.label}</span>
    </div>
  );
}

function EntityNode({ data }: { data: { label: string; lens: string; expandable?: boolean; expanded?: boolean } }) {
  return (
    <div className={`${styles.nodeEntity} ${data.expanded ? styles.nodeEntityExpanded : ""}`} style={{ borderColor: `${LENS_COLORS[data.lens] ?? "#888"}60` }}>
      <Handle type="target" position={Position.Right} id="t-right" className={styles.handle} />
      <Handle type="target" position={Position.Left} id="t-left" className={styles.handle} />
      <Handle type="target" position={Position.Top} id="t-top" className={styles.handle} />
      <Handle type="target" position={Position.Bottom} id="t-bottom" className={styles.handle} />
      <Handle type="source" position={Position.Right} id="s-right" className={styles.handle} />
      <Handle type="source" position={Position.Left} id="s-left" className={styles.handle} />
      <Handle type="source" position={Position.Top} id="s-top" className={styles.handle} />
      <Handle type="source" position={Position.Bottom} id="s-bottom" className={styles.handle} />
      <span>{data.label}</span>
      {data.expandable && <span className={styles.expandIcon}>{data.expanded ? "−" : "+"}</span>}
    </div>
  );
}

function QualifierNode({ data }: { data: { label: string; factText?: string; lens: string } }) {
  return (
    <div className={styles.nodeQualifier} style={{ borderColor: `${LENS_COLORS[data.lens] ?? "#888"}40` }}>
      <Handle type="target" position={Position.Right} id="t-right" className={styles.handle} />
      <Handle type="target" position={Position.Left} id="t-left" className={styles.handle} />
      <Handle type="target" position={Position.Top} id="t-top" className={styles.handle} />
      <Handle type="target" position={Position.Bottom} id="t-bottom" className={styles.handle} />
      <Handle type="source" position={Position.Right} id="s-right" className={styles.handle} />
      <Handle type="source" position={Position.Left} id="s-left" className={styles.handle} />
      <Handle type="source" position={Position.Top} id="s-top" className={styles.handle} />
      <Handle type="source" position={Position.Bottom} id="s-bottom" className={styles.handle} />
      <strong>{data.label}</strong>
      {data.factText && <p className={styles.nodeQualifierText}>{data.factText.slice(0, 100)}{data.factText.length > 100 ? "…" : ""}</p>}
    </div>
  );
}

const nodeTypes: NodeTypes = {
  mindMapRoot: RootNode,
  mindMapLens: LensNode,
  mindMapDomain: DomainNode,
  mindMapEntity: EntityNode,
  mindMapQualifier: QualifierNode,
};

// --- Main Component ---

export function MindMapView({ model }: { model: DashboardRow | undefined }): React.JSX.Element {
  const [expandedEntities, setExpandedEntities] = useState<Set<string>>(new Set());

  const { nodes: initialNodes, edges: initialEdges } = useMemo(
    () => buildFullGraph(model, expandedEntities),
    [model, expandedEntities],
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Sync when graph rebuilds (expand/collapse)
  React.useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  const onNodeClick: NodeMouseHandler = useCallback((_event, node) => {
    if (node.type !== "mindMapEntity") return;
    setExpandedEntities((prev) => {
      const next = new Set(prev);
      if (next.has(node.id)) {
        next.delete(node.id);
      } else {
        next.add(node.id);
      }
      return next;
    });
  }, []);

  return (
    <div className={styles.canvas}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
        minZoom={0.2}
        maxZoom={2.5}
        proOptions={{ hideAttribution: true }}
        nodesDraggable
        nodesConnectable={false}
      >
        <Background variant={BackgroundVariant.Dots} gap={24} size={1} color="rgba(244,239,231,0.06)" />
        <Controls showInteractive={false} className={styles.controls} />
        <MiniMap
          nodeColor={(node) => LENS_COLORS[(node.data as { lens?: string })?.lens ?? ""] ?? "rgba(244,239,231,0.2)"}
          maskColor="rgba(9,10,10,0.85)"
          className={styles.minimap}
        />
      </ReactFlow>
    </div>
  );
}
