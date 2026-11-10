#!/usr/bin/env python3
"""Import NCERT Hindi-medium manifests (Book / Notes / Solution JSON of {name,url}) into ncert/class_N.

  python tools/import_ncert_hindi.py "<folder holding 'Ncert 11 Hindi ...' and 'Ncert 12 Hindi ...'>" [--apply]

Every Hindi book becomes a language=hindi book registered in its stream's books.json; chapters go into the
same subject folder as the English counterpart (chapters.json is keyed by bookId), so nothing is moved.
Without --apply it only prints the plan.
"""
import difflib
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = sys.argv[1]
APPLY = '--apply' in sys.argv


def norm(s):
    s = s.replace('. json', '').replace('.json', '').replace('भाग', '')
    s = re.sub(r'[\s.\-–]+', '', s)
    return s.replace('ू', 'ु').replace('ी', 'ि').replace('ृ', 'ि')


def J(p, d=None):
    try:
        return json.load(open(p, encoding='utf-8-sig'))
    except Exception:
        return d


def W(p, d):
    json.dump(d, open(p, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)


# canonical Hindi Book names -> (English counterpart book id,)  or  (None, stream, folder, English subject)
C11 = {
    'अंतरा भाग 1': (None, 'common', 'hindi', 'Hindi'), 'अंतराल भाग 1': (None, 'common', 'hindi', 'Hindi'),
    'आरोह भाग 1': (None, 'common', 'hindi', 'Hindi'), 'वितान भाग 1': (None, 'common', 'hindi', 'Hindi'),
    'अर्थशास्त्र में सांख्यिकी': (1124,), 'गणित': (1106,), 'जीव विज्ञान': (1105,),
    'भारत का संविधान सिद्धांत और व्यवहार': (1144,), 'भारत भौतिक पर्यावरण': (None, 'common', 'geography', 'Geography'),
    'भारतीय अर्थव्यवस्था का विकास': (1125,), 'भुगोल में प्रयोगात्मक कार्य': (1143,), 'भौतिक भुगोल के मूल सिद्धांत': (1142,),
    'भौतिकी भाग 1': (1101,), 'भौतिकी भाग 2': (1102,), 'मनोविज्ञान': (1148,),
    'मानव पारिस्थितिकी एवं परिवार विज्ञान भाग 1': (None, 'common', 'home_science', 'Home Science'),
    'मानव पारिस्थितिकी एवं परिवार विज्ञान भाग 2': (None, 'common', 'home_science', 'Home Science'),
    'रसायन विज्ञान भाग 1': (1103,), 'रसायन विज्ञान भाग 2': (1104,), 'राजनीतिक सिद्धांत': (1145,),
    'लेखाशास्त्र भाग 1': (1121,), 'लेखाशास्त्र भाग 2': (1122,), 'विश्व इतिहास के कुछ विषय': (1141,),
    'व्यवसाय अध्ययन': (1123,), 'समाज का बोध': (1147,), 'समाजशास्त्र परिचय': (1146,),
}
C12 = {
    'अंतरा 2': (None, 'common', 'hindi', 'Hindi'), 'अंतराल 2': (None, 'common', 'hindi', 'Hindi'),
    'आरोह 2': (None, 'common', 'hindi', 'Hindi'), 'वितान 2': (None, 'common', 'hindi', 'Hindi'),
    'गणित 1': (1206,), 'गणित 2': (1207,), 'जीव विज्ञान': (1205,), 'भारत में सामाजिक परिवर्तन एव विकास': (1247,),
    'भारत लोग और अर्थव्यवस्था': (1252,), 'भारतीय इतिहास की कुछ विषय 1': (1241,), 'भारतीय इतिहास के कुछ विषय 2': (1242,),
    'भारतीय इतिहास के कुछ विषय 3': (1243,), 'भारतीय समाज': (1246,), 'भूगोल मे प्रयोगात्मक कार्य 2': (1253,),
    'भौतिकी 1': (1201,), 'भौतिकी 2': (1202,), 'मनोविज्ञान': (1248,), 'मानव भूगोल के मूल सिद्धांत': (1251,),
    'रसायन विज्ञान 1': (1203,), 'रसायन विज्ञान 2': (1204,), 'लेखाशास्त्र 1': (1221,), 'लेखाशास्त्र 2': (1222,),
    'व्यवसाय अध्ययन 1': (1223,), 'व्यवसाय अध्ययन 2': (1227,), 'व्यष्टी अर्थशास्त्र एक परिचय': (1225,),
    'समकालीन विश्व राजनीती': (1244,), 'समष्टी अर्थशास्त्र एक परिचय': (1224,), 'स्वतंत्र भारत मे राजनीति 2': (1245,),
}
# empty placeholder Hindi books (no links at all) that the new books replace
OLD_HINDI = {11: {1133, 1134, 1116}, 12: {1233, 1234}}


def digits(s):
    return ''.join(re.findall(r'\d', s))


def match_kinds(folder):
    """Book file -> {Notes: file, Solution: file}: exact normalised name first, then best fuzzy match with equal digits."""
    files = {k: sorted(os.listdir(os.path.join(folder, k))) for k in ('Book', 'Notes', 'Solution')}
    out = {b: {} for b in files['Book']}
    for kind in ('Notes', 'Solution'):
        left = list(files[kind])
        for b in files['Book']:
            ex = [f for f in left if norm(f) == norm(b)]
            if ex:
                out[b][kind] = ex[0]
                left.remove(ex[0])
        for f in list(left):
            cand = [(difflib.SequenceMatcher(None, norm(f), norm(b)).ratio(), b) for b in files['Book']
                    if kind not in out[b] and digits(f) == digits(b)]
            if cand:
                r, b = max(cand)
                if r >= 0.6:
                    out[b][kind] = f
                    left.remove(f)
        missing = [b for b in files['Book'] if kind not in out[b]]
        if len(missing) == 1 and len(left) == 1:      # one book and one file left: they belong together
            out[missing[0]][kind] = left.pop()
        for f in left:
            print('  UNMATCHED', kind, f)
    return out


def items(path):
    d = J(path, [])
    res = {}
    for i, x in enumerate(d):
        m = re.match(r'\s*(\d+)\s*[.\-]?\s*(.*)', x['name'])
        n = int(m.group(1)) if m else i + 1
        t = re.sub(r'\.pdf$', '', (m.group(2) if m else x['name']), flags=re.I).strip(' .')
        res.setdefault(n, (t or x['name'], x['url']))
    return res


def main():
    for cls, table in ((11, C11), (12, C12)):
        folder = next(os.path.join(SRC, d) for d in os.listdir(SRC) if d.startswith(f'Ncert {cls} Hindi'))
        base = os.path.join(ROOT, 'ncert', f'class_{cls}')
        stream_of, books_in = {}, {}
        for bp in glob.glob(os.path.join(base, '*', 'books.json')):
            st = os.path.basename(os.path.dirname(bp))
            for b in J(bp)['books']:
                stream_of[b['id']] = st
                books_in[b['id']] = b
        chap_folder = {}
        for cf in sorted(glob.glob(os.path.join(base, '*', '*', 'chapters.json'))):
            st, sub = cf.split(os.sep)[-3], cf.split(os.sep)[-2]
            for c in J(cf)['chapters']:
                if (st, sub) not in chap_folder.setdefault(c['bookId'], []):
                    chap_folder[c['bookId']].append((st, sub))
        mt = match_kinds(folder)
        canon = {norm(k): (k, v) for k, v in table.items()}
        order = list(table)
        plan = []
        nid = 1160 if cls == 11 else 1260
        for bfile in sorted(mt, key=lambda f: order.index(canon[norm(f)][0]) if norm(f) in canon else 999):
            if norm(bfile) not in canon:
                print('  NO META for', bfile)
                continue
            name, meta = canon[norm(bfile)]
            nid += 1
            if meta[0]:
                eng = books_in[meta[0]]
                st = stream_of[meta[0]]
                folders = chap_folder.get(meta[0], [])
                fol = next((f for f in folders if f[0] == st), folders[0] if folders else (st, eng['subject'].lower().replace(' ', '_')))
                subject, cover = eng['subject'], eng.get('coverUrl', '')
            else:
                st, fol, subject, cover = meta[1], (meta[1], meta[2]), meta[3], ''
            ch = items(os.path.join(folder, 'Book', bfile))
            no = items(os.path.join(folder, 'Notes', mt[bfile]['Notes'])) if 'Notes' in mt[bfile] else {}
            so = items(os.path.join(folder, 'Solution', mt[bfile]['Solution'])) if 'Solution' in mt[bfile] else {}
            plan.append(dict(id=nid, title=re.sub(r'\s+', ' ', name), stream=st, folder=fol, subject=subject, cover=cover, ch=ch, no=no, so=so))
        print(f'--- class {cls}: {len(plan)} books')
        for p in plan:
            print(f"  {p['id']} {p['title'][:30]:30} -> {p['stream']}/{p['folder'][1]:26} ch={len(p['ch']):2} notes={len(p['no']):2} sol={len(p['so']):2}")
        if not APPLY:
            continue
        old = OLD_HINDI[cls]
        for bp in glob.glob(os.path.join(base, '*', 'books.json')):
            d = J(bp)
            d['books'] = [b for b in d['books'] if b['id'] not in old]
            W(bp, d)
        for cf in glob.glob(os.path.join(base, '*', '*', 'chapters.json')):
            d = J(cf)
            d['chapters'] = [c for c in d['chapters'] if c['bookId'] not in old]
            d['books'] = [b for b in (d.get('books') or []) if b['id'] not in old]
            W(cf, d)
        for p in plan:
            bk = {'id': p['id'], 'title': p['title'], 'subtitle': f'Class {cls} NCERT Hindi Medium Textbook', 'coverUrl': p['cover'],
                  'language': 'hindi', 'classNumber': f'Class {cls}', 'subject': p['subject'], 'chapterCount': len(p['ch']), 'parts': 1}
            bp = os.path.join(base, p['stream'], 'books.json')
            d = J(bp, {'books': []})
            d['books'].append(bk)
            W(bp, d)
            cdir = os.path.join(base, p['folder'][0], p['folder'][1])
            os.makedirs(cdir, exist_ok=True)
            cf = os.path.join(cdir, 'chapters.json')
            d = J(cf, {'books': [], 'chapters': []})
            d.setdefault('books', []).append(bk)
            for n in sorted(p['ch']):
                t, url = p['ch'][n]
                d['chapters'].append({
                    'id': p['id'] * 100 + n, 'bookId': p['id'], 'chapterNumber': n, 'title': t, 'topicCount': 0, 'questionCount': 0,
                    'progressPercent': 0, 'status': 'NOT_STARTED', 'estimatedMinutes': 0, 'pageCount': 0, 'hasRead': True,
                    'hasSolutions': n in p['so'], 'hasNotes': n in p['no'], 'hasMCQ': False, 'pdfUrl': url,
                    'solutionsUrl': p['so'][n][1] if n in p['so'] else '', 'notesUrl': p['no'][n][1] if n in p['no'] else ''})
            W(cf, d)


main()
