# NCERT Maharashtra — Relabeled Content

This directory mirrors the `data/` NCERT content set (Class 11 & Class 12, all streams:
science, commerce, arts, common) but is relabeled for **Maharashtra State Board** display
purposes in the app.

- Underlying chapter/book/MCQ **content is unchanged** — it is the same NCERT-based material
  found in `data/`.
- Board-facing labels have been updated: `subtitle`, `boardName`, and `displayName` fields
  now read "Maharashtra State Board" instead of "NCERT" / "NCERT / CBSE".
- Folder layout and JSON schema are identical to `data/` — see `data/class_11/README.md`
  for the full data contract (books.json, chapters.json, mcqs/, papers.json, etc.).

## Structure

```
ncert-maharastra/
├── app_config.json
├── index.json
├── class_11/
│   ├── index.json
│   ├── science/  commerce/  arts/  common/
└── class_12/
    ├── index.json
    ├── science/  commerce/  arts/  common/
```

> Note: This is a relabeled copy, not distinct Maharashtra State Board curriculum content.
> If genuine Maharashtra Board syllabus/MCQs are needed later, this folder is the place to
> replace the underlying chapter and MCQ data while keeping the same schema.
