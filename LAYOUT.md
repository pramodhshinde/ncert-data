# Data layout 2026 (branch `2026`) — board / class / stream / medium

`main` is untouched and keeps serving the already-published apps. This branch adds a resolved
view per combination so an app fetches **exactly one file** for what the student picked:

```
<board>/catalog.json                              board manifest: class -> stream -> medium -> book count
<board>/class_N/<stream>/<medium>/books.json      resolved books (own + common + shared across streams/mediums)
<board>/class_N/<stream>/<medium>/papers.json     resolved papers
<board>/class_N/<stream>|common/<subject>/...     content (chapters.json, mcqs/) — NOT moved, NOT duplicated
```
`<board>` = `ncert` (NCERT) or `maharastra`. Each resolved book has `contentPath` (folder holding its
chapters/mcqs), `streams` and `mediums`.

## Sharing rules
* Subjects in `catalog.rules.json -> crossMediumSubjects` (English, Hindi, Marathi) show in **every** medium
  (Hindi medium sees the English book, English medium sees the Hindi book).
* Everything in `class_N/common/` shows in every stream of that class.
* Per-book overrides in any `books.json` entry: `"streams": [...]`, `"mediums": [...]`.
* Mediums per board live in `catalog.rules.json`.

## Editing
Edit the source `books.json` files (stream/common), then run `python tools/build_catalog.py`.
Never hand-edit `<stream>/<medium>/*.json` — they are regenerated.

## De-duplication (board fallback)
Files that were byte-identical copies of NCERT in `maharastra/` (791 MCQ files) were removed. The app reads
`maharastra/...` first and falls back to the same path under `ncert/` (`FALLBACK_BOARD_ROOT`, default `ncert` for the Maharashtra board).

## Importing manifests
`tools/import_ncert_hindi.py "<folder>" --apply` turns Book/Notes/Solution `{name,url}` manifests of the NCERT Hindi medium into
`language=hindi` books + chapters (211 chapters class 11, 189 class 12). Run without `--apply` to preview. Afterwards run `tools/build_catalog.py`.
