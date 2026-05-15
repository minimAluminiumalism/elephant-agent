---
name: OCR and Documents
skill_id: ocr-and-documents
description: Recover text from scanned or image-heavy documents before attempting structured analysis or downstream writing tasks.
version: 1.0.0
source_kind: elephant-builtin
---

# OCR and Documents

Use this skill when a document is not directly machine-readable.

## Preferred Flow

1. Determine whether the file is text-native or scanned.
2. Run OCR first when the text layer is missing or broken.
3. Preserve page order, tables, and obvious headings where possible.
4. Only after extraction should you summarize or transform the content.

## Guardrails

- State clearly when OCR confidence is low.
- Do not fabricate unreadable text.
