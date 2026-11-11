#!/usr/bin/env python3
"""Generate clean book covers for every book that has no coverUrl, and point coverUrl at them.

  python tools/make_covers.py [--all]        # --all: also redo covers this script made earlier

Covers are our own design (subject colour + exact title/class/board/medium), saved as covers/<board>/class_N/<bookId>.webp.
Existing covers (Drive links) are left alone. Needs Microsoft Edge (headless) and Pillow.
"""
import glob
import html
import json
import os
import subprocess
import sys
import tempfile

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
RAW = 'https://raw.githubusercontent.com/pramodhshinde/ncert-data/2026/'
ALL = '--all' in sys.argv

PALETTE = [  # (keywords in subject/title, dark, light)
    (('physics', 'भौतिकी'), '#1E3A8A', '#3B82F6'),
    (('chemistry', 'रसायन'), '#9A3412', '#FB923C'),
    (('biotechnology',), '#14532D', '#34D399'),
    (('biology', 'जीव'), '#166534', '#4ADE80'),
    (('math', 'statistics', 'गणित', 'सांख्यिकी'), '#831843', '#F472B6'),
    (('computer', 'informatics', 'information technology'), '#0F172A', '#38BDF8'),
    (('accountancy', 'book-keeping', 'लेखा', 'पुस्तपालन'), '#1E40AF', '#818CF8'),
    (('economics', 'अर्थ'), '#7C2D12', '#FBBF24'),
    (('business', 'commerce', 'secretarial', 'co-operation', 'entrepreneurship', 'व्यवसाय', 'सहकार', 'चिटणीस'), '#115E59', '#2DD4BF'),
    (('english', 'hornbill', 'snapshots', 'woven', 'flamingo', 'vistas', 'yuvakbharati'), '#312E81', '#A78BFA'),
    (('hindi', 'हिंदी', 'अंतरा', 'अंतराल', 'आरोह', 'वितान'), '#9F1239', '#FB7185'),
    (('marathi', 'मराठी'), '#7F1D1D', '#F87171'),
    (('history', 'इतिहास'), '#78350F', '#F59E0B'),
    (('geography', 'भूगोल', 'भुगोल'), '#14532D', '#86EFAC'),
    (('political', 'politics', 'राजनी', 'संविधान'), '#831843', '#FDA4AF'),
    (('psychology', 'मनोविज्ञान', 'मानसशास्त्र'), '#581C87', '#D8B4FE'),
    (('sociology', 'society', 'समाज'), '#134E4A', '#5EEAD4'),
    (('philosophy', 'तत्त्वज्ञान'), '#3F3F46', '#A1A1AA'),
    (('art',), '#86198F', '#F0ABFC'),
    (('physical education', 'health'), '#0C4A6E', '#7DD3FC'),
    (('home science', 'परिवार'), '#9D174D', '#F9A8D4'),
]
EMOJI = [('biotechnology', '🧪'), ('physics', '🔬'), ('भौतिकी', '🔬'), ('chemistry', '⚗️'), ('रसायन', '⚗️'), ('biology', '🧬'), ('जीव', '🧬'),
         ('math', '➗'), ('statistics', '📊'), ('गणित', '➗'), ('सांख्यिकी', '📊'), ('computer', '💻'), ('informatics', '💻'), ('information technology', '💻'),
         ('accountancy', '📒'), ('book-keeping', '📒'), ('लेखा', '📒'), ('पुस्तपालन', '📒'), ('economics', '💹'), ('अर्थ', '💹'),
         ('business', '💼'), ('secretarial', '💼'), ('co-operation', '🤝'), ('entrepreneurship', '🚀'), ('commerce', '💼'), ('व्यवसाय', '💼'), ('सहकार', '🤝'), ('चिटणीस', '💼'),
         ('english', '📖'), ('hindi', '📖'), ('marathi', '📖'), ('हिंदी', '📖'), ('मराठी', '📖'), ('अंतरा', '📖'), ('आरोह', '📖'), ('वितान', '📖'), ('hornbill', '📖'), ('snapshots', '📖'), ('woven', '📖'), ('flamingo', '📖'), ('vistas', '📖'),
         ('history', '🏛️'), ('इतिहास', '🏛️'), ('geography', '🌍'), ('भूगोल', '🌍'), ('भुगोल', '🌍'), ('political', '⚖️'), ('politics', '⚖️'), ('संविधान', '⚖️'), ('राजनी', '⚖️'),
         ('psychology', '🧠'), ('मनोविज्ञान', '🧠'), ('sociology', '👥'), ('society', '👥'), ('समाज', '👥'), ('philosophy', '💭'), ('तत्त्वज्ञान', '💭'),
         ('art', '🎨'), ('physical', '⚽'), ('health', '⚽'), ('home science', '🏠'), ('परिवार', '🏠')]
MEDIUM = {'english': 'English Medium', 'hindi': 'Hindi Medium', 'marathi': 'Marathi Medium'}
BOARD = {'ncert': 'NCERT', 'maharastra': 'Maharashtra State Board'}


def colours(book):
    key = (book['subject'] + ' ' + book['title']).lower()
    for words, a, b in PALETTE:
        if any(w in key for w in words):
            return a, b
    return '#4338CA', '#818CF8'


def emoji(book):
    key = (book['subject'] + ' ' + book['title']).lower()
    return next((e for w, e in EMOJI if w in key), '📘')


def page(book, board, cls):
    a, b = colours(book)
    t = book['title']
    size = 64 if len(t) <= 14 else 52 if len(t) <= 28 else 42 if len(t) <= 48 else 34
    subj = '' if book['subject'].lower() in t.lower() else book['subject']
    return f'''<!doctype html><meta charset="utf-8"><style>
html,body{{margin:0;width:600px;height:800px;overflow:hidden}}
.c{{position:relative;width:600px;height:800px;background:linear-gradient(155deg,{a},{b});color:#fff;font-family:"Segoe UI","Nirmala UI",Arial,sans-serif;overflow:hidden}}
.o1{{position:absolute;right:-140px;top:-120px;width:420px;height:420px;border-radius:50%;background:rgba(255,255,255,.13)}}
.o2{{position:absolute;left:-160px;bottom:-140px;width:460px;height:460px;border-radius:50%;background:rgba(255,255,255,.10)}}
.o3{{position:absolute;right:60px;bottom:150px;width:120px;height:120px;border-radius:50%;background:rgba(255,255,255,.12)}}
.top{{position:absolute;left:44px;right:44px;top:44px;font-size:22px;letter-spacing:2px;font-weight:700;opacity:.92;text-transform:uppercase}}
.top small{{display:block;margin-top:8px;font-size:18px;letter-spacing:1px;font-weight:600;opacity:.85}}
.t{{position:absolute;left:44px;right:44px;top:210px;font-size:{size}px;line-height:1.14;font-weight:800;letter-spacing:-.5px;text-shadow:0 2px 12px rgba(0,0,0,.22)}}
.bar{{width:84px;height:8px;border-radius:4px;background:#fff;opacity:.9;margin-top:28px}}
.s{{margin-top:20px;font-size:26px;font-weight:600;opacity:.92}}
.ico{{position:absolute;right:50px;bottom:120px;font-size:190px;line-height:1;filter:drop-shadow(0 8px 18px rgba(0,0,0,.25))}}
.bot{{position:absolute;left:44px;bottom:44px;font-size:20px;font-weight:700;letter-spacing:1.5px;background:rgba(255,255,255,.2);padding:10px 20px;border-radius:999px;text-transform:uppercase}}
</style><div class="c"><i class="o1"></i><i class="o2"></i><i class="o3"></i>
<div class="top">Class {cls} · {BOARD[board]}<small>{MEDIUM.get(book["language"], book["language"].title())}</small></div>
<div class="t">{html.escape(t)}<div class="bar"></div>{f'<div class="s">{html.escape(subj)}</div>' if subj else ''}</div>
<div class="ico">{emoji(book)}</div>
<div class="bot">Textbook · Class {cls}</div></div>'''


def render(book, board, cls, out):
    d = tempfile.mkdtemp()
    f = os.path.join(d, 'c.html')
    png = os.path.join(d, 'c.png')
    open(f, 'w', encoding='utf-8').write(page(book, board, cls))
    subprocess.run([EDGE, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--window-size=600,800', f'--screenshot={png}',
                    'file:///' + f.replace(os.sep, '/')], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    Image.open(png).convert('RGB').save(out, 'WEBP', quality=86, method=6)


def main():
    made = 0
    for bp in sorted(glob.glob(os.path.join(ROOT, '*', 'class_*', '*', 'books.json'))):
        parts = bp.replace(os.sep, '/').split('/')
        board, cls = parts[-4], parts[-3].replace('class_', '')
        if board not in BOARD:
            continue
        data = json.load(open(bp, encoding='utf-8'))
        changed = False
        for b in data['books']:
            own = (b.get('coverUrl') or '').startswith(RAW + 'covers/')
            if b.get('coverUrl') and not (own and ALL):
                continue
            rel = f'covers/{board}/class_{cls}/{b["id"]}.webp'
            render(b, board, cls, os.path.join(ROOT, rel))
            b['coverUrl'] = RAW + rel
            changed = True
            made += 1
        if changed:
            json.dump(data, open(bp, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    # keep the books embedded in chapters.json in step
    url = {}
    for bp in glob.glob(os.path.join(ROOT, '*', 'class_*', '*', 'books.json')):
        board = bp.replace(os.sep, '/').split('/')[-4]
        for b in json.load(open(bp, encoding='utf-8'))['books']:
            url[(board, b['id'])] = b.get('coverUrl', '')
    for cf in glob.glob(os.path.join(ROOT, '*', 'class_*', '*', '*', 'chapters.json')):
        board = cf.replace(os.sep, '/').split('/')[-5]
        d = json.load(open(cf, encoding='utf-8'))
        ch = False
        for b in d.get('books') or []:
            u = url.get((board, b['id']))
            if u and b.get('coverUrl') != u:
                b['coverUrl'] = u
                ch = True
        if ch:
            json.dump(d, open(cf, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    print('covers made:', made)


main()
