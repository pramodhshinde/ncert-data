#!/usr/bin/env python3
"""Build the stream x medium catalog views from the content folders.

Source of truth (edit these, then run `python tools/build_catalog.py`):
  <board>/class_N/<stream>/books.json     books that belong to that stream folder
  <board>/class_N/common/books.json       books shared by every stream
  catalog.rules.json                      mediums per board + cross-medium subjects

Per-book optional overrides (add to the book entry):
  "streams": ["science","commerce"]   -> also show in these streams (default: its folder; common = all streams)
  "mediums": ["english","hindi"]      -> show in these mediums (default: its language; cross-medium subjects = all)

Output (generated, do not edit by hand):
  <board>/class_N/<stream>/<medium>/books.json    resolved list for that exact combination
  <board>/class_N/<stream>/<medium>/papers.json
  <board>/catalog.json                            board manifest: classes -> streams -> mediums
Each resolved book carries "contentPath" = folder holding its chapters.json / mcqs/.
Content folders themselves are never moved or duplicated.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rules = json.load(open(os.path.join(ROOT, 'catalog.rules.json'), encoding='utf-8'))
CROSS = {s.lower() for s in rules['crossMediumSubjects']}


def load(p, default):
    try:
        return json.load(open(p, encoding='utf-8'))
    except FileNotFoundError:
        return default


def norm(s):
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')


def book_folders(board, cls):
    """bookId -> content folder, read from where the book's chapters actually live."""
    m = {}
    base = os.path.join(ROOT, board, cls)
    for st in sorted(os.listdir(base)):
        sd = os.path.join(base, st)
        if not os.path.isdir(sd):
            continue
        for sub in sorted(os.listdir(sd)):
            cf = os.path.join(sd, sub, 'chapters.json')
            if os.path.exists(cf):
                d = load(cf, {})
                for c in (d.get('chapters') if isinstance(d, dict) else d) or []:
                    m.setdefault(c.get('bookId'), f'{cls}/{st}/{sub}')
    return m


def find_folder(board, cls, folders, subject):
    """subject -> content folder (first of the given stream folders that has it)."""
    want = norm(subject)
    for st in folders:
        base = os.path.join(ROOT, board, cls, st)
        if not os.path.isdir(base):
            continue
        for d in sorted(os.listdir(base)):
            if os.path.isdir(os.path.join(base, d)) and (norm(d) == want or norm(d).replace('_', '') == want.replace('_', '')):
                return f'{cls}/{st}/{d}'
    return None


def main():
    problems = []
    for board, cfg in rules['boards'].items():
        mediums = cfg['mediums']
        manifest = {'board': board, 'label': cfg.get('label', board), 'mediums': mediums, 'classes': {}}
        for cls in sorted(d for d in os.listdir(os.path.join(ROOT, board)) if d.startswith('class_')):
            streams = [d for d in sorted(os.listdir(os.path.join(ROOT, board, cls)))
                       if os.path.isdir(os.path.join(ROOT, board, cls, d)) and d != 'common'
                       and os.path.exists(os.path.join(ROOT, board, cls, d, 'books.json'))]
            if not streams:
                streams = ['common']
            bmap = book_folders(board, cls)
            all_books = {}
            for folder in streams + (['common'] if 'common' not in streams else []):
                for b in load(os.path.join(ROOT, board, cls, folder, 'books.json'), {'books': []})['books']:
                    b = dict(b)
                    b['_home'] = folder
                    all_books[b['id']] = b
            manifest['classes'][cls] = {}
            for st in streams:
                for med in mediums:
                    out = []
                    for b in all_books.values():
                        home = b['_home']
                        in_stream = (st in b['streams']) if 'streams' in b else (home == st or home == 'common')
                        if not in_stream:
                            continue
                        if 'mediums' in b:
                            ok = med in b['mediums']
                        elif b['subject'].lower() in CROSS:
                            ok = True
                        else:
                            ok = b.get('language', mediums[0]).lower() == med
                        if not ok:
                            continue
                        e = {k: v for k, v in b.items() if k != '_home'}
                        folders = [home] + [s for s in streams + ['common'] if s != home]
                        e['contentPath'] = bmap.get(b['id']) or find_folder(board, cls, folders, b['subject'])
                        if not e['contentPath']:
                            problems.append(f'{board}/{cls} book {b["id"]} {b["title"]}: no content folder for "{b["subject"]}"')
                        e['streams'] = [s for s in streams if (s in b['streams'] if 'streams' in b else (home == s or home == 'common'))]
                        e['mediums'] = b.get('mediums') or (mediums if b['subject'].lower() in CROSS else [b.get('language', med).lower()])
                        out.append(e)
                    out.sort(key=lambda x: (x['subject'].lower(), x['title'].lower()))
                    d = os.path.join(ROOT, board, cls, st, med)
                    os.makedirs(d, exist_ok=True)
                    json.dump({'books': out}, open(os.path.join(d, 'books.json'), 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
                    # papers: stream + common
                    papers = []
                    for folder in {st, 'common'}:
                        papers += load(os.path.join(ROOT, board, cls, folder, 'papers.json'), {'papers': []}).get('papers', [])
                    seen, uniq = set(), []
                    for p in papers:
                        if p.get('id') in seen and p.get('id') is not None:
                            continue
                        seen.add(p.get('id'))
                        pl = str(p.get('language', '')).lower()
                        if not pl or pl == med or str(p.get('subject', '')).lower() in CROSS:
                            uniq.append(p)
                    json.dump({'papers': uniq}, open(os.path.join(d, 'papers.json'), 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
                    manifest['classes'][cls].setdefault(st, {})[med] = len(out)
        json.dump(manifest, open(os.path.join(ROOT, board, 'catalog.json'), 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    for p in problems:
        print('WARN', p)
    print('ok', len(problems), 'warnings')
    return 1 if problems and '--strict' in sys.argv else 0


if __name__ == '__main__':
    sys.exit(main())
