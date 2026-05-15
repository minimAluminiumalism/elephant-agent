---
name: Nano PDF
skill_id: nano-pdf
description: Extract, inspect, and summarize PDFs quickly with lightweight tooling before escalating to heavier OCR or layout workflows.
version: 1.0.0
source_kind: elephant-builtin
---

# Nano PDF

Use this skill for lightweight PDF reading, extraction, and summarization.

## Preferred Flow

1. Start with direct text extraction.
2. If the PDF is image-heavy or scanned, switch to OCR instead of pretending the text is available.
3. Quote page or section anchors when the user needs traceable citations.

## Guardrails

- Do not over-quote copyrighted PDFs.
- Be explicit when extraction quality is weak.
