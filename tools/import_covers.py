#!/usr/bin/env python3
"""Copy the supplied real book covers into covers/<board>/class_N/<bookId>.jpg and point coverUrl at them.

  python tools/import_covers.py "<folder holding the 6 cover folders>"

File name -> book id is spelled out below (checked against each board's books.json); anything not listed keeps its current cover.
"""
import glob
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = sys.argv[1]
RAW = 'https://raw.githubusercontent.com/pramodhshinde/ncert-data/2026/'

# folder prefix -> (board, class, {file stem: book id})
MAP = {
    'HSC 11 English': ('maharastra', 11, {
        'Book kep acountcy': 1121, 'English yuvak Bharti': 1131, 'Health and physical education': 1150, 'I T': 1301, 'biology': 1105,
        'chemistry': 1103, 'co opretion': 1300, 'economic': 1124, 'geography': 1142, 'history': 1141, 'math & stat com 1': 1303,
        'math & stat com 2': 1304, 'math & stat sci-art 1': 1106, 'math & stat sci-art 2': 1302, 'organisation of commerce': 1305,
        'philosophy': 1306, 'physics': 1101, 'politics science': 1144, 'psychology': 1148, 'secritail practice': 1307, 'sociology': 1146}),
    'HSC 11 Marathi': ('maharastra', 11, {
        'अर्थशास्त्र': 1424, 'इतिहास': 1441, 'चिटणीसाची कार्यपद्धती': 1607, 'तत्त्वज्ञान': 1606, 'पुस्तपालन आणि लेखाकर्म': 1421,
        'भूगोल': 1442, 'मराठी युवक भारती': 1151, 'मानसशास्त्र': 1448, 'राज्यशास्त्र': 1444, 'वाणिज्य संघटन व व्यवस्थापन': 1605,
        'समाजशास्त्र': 1446, 'सहकार': 1600, 'हिंदी युवक भारती': 1133}),
    'HSC 12 English': ('maharastra', 12, {
        'English yuvak Bharti': 1325, 'biology': 1330, 'bookkeeping accounts': 1314, 'chemistry': 1331, 'corporation': 1316,
        'economics': 1323, 'geography': 1301, 'history': 1303, 'information technology arts': 1305, 'information technology science': 1332,
        'math and stat 1 comm': 1317, 'math and stat 2 comm': 1318, 'math stat art science 1': 1328, 'math stat art science 2': 1329,
        'organisation of commerce': 1319, 'philosophy': 1306, 'physics': 1333, 'political science': 1308, 'psychology': 1310,
        'securitel and practice': 1321, 'sociology': 1312}),
    'HSC 12 Marathi': ('maharastra', 12, {
        'अर्थशास्त्र': 1324, 'इतिहास': 1304, 'चिटणीसाची कार्यपद्धती': 1322, 'तत्त्वज्ञान': 1307, 'पुस्तपालन आणि लेखा': 1315,
        'भूगोल': 1302, 'मराठी युवक भारती': 1327, 'मानसशास्त्र': 1311, 'राज्यशास्त्र': 1309, 'वाणिज्य संघटन व्यवस्थापन': 1320,
        'समाजशास्त्र': 1313, 'हिंदी युवक भारती': 1326}),
    'Ncert 11 Hindi': ('ncert', 11, {
        'अंतरा भाग 1': 1161, 'अंतराल': 1162, 'आरोह': 1163, 'वितान 1': 1164, 'अर्थशास्त्र में सांख्यिकी': 1165, 'गणित': 1166,
        'जीवविज्ञान': 1167, 'भारत का संविधान सिद्धांत और व्यवहार': 1168, 'भारत भौतिक पर्यावरण': 1169, 'भारतीय अर्थव्यवस्था का विकास': 1170,
        'भूगोल में प्रयोगात्मक कार्य १': 1171, 'भौतिक भूगोल के मूल सिद्धांत': 1172, 'भौतिक भाग १': 1173, 'भौतिकी भाग २': 1174,
        'मनोविज्ञान': 1175, 'मानव पारिस्थितिकी और परिवार विज्ञान १': 1176, 'मानव पारिस्थितिकी और परिवार विज्ञान २': 1177,
        'रसायन १': 1178, 'रसायन २': 1179, 'राजनीतिक सिद्धांत': 1180, 'लेखाशास्त्र १': 1181, 'लेखाशास्त्र २': 1182,
        'विश्व इतिहास के कुछ विषय': 1183, 'व्यवसाय अध्ययन': 1184, 'समाज का बोध': 1185, 'समाजशास्त्र का परिचय': 1186}),
    'Ncert 12 hindi': ('ncert', 12, {
        'अंतरा': 1261, 'अंतराळ': 1262, 'आरोह 2': 1263, 'वितान 2': 1264, 'गणित 1': 1265, 'गणित 2': 1266, 'जीव विज्ञान': 1267,
        'भारत मे सामाजिक यवं परिवर्तन विकास': 1268, 'भारत लोग और अर्थव्यवस्था': 1269, 'भारतीय इतिहास के कुछ विषय 1': 1270,
        'भारतीय इतिहास के कुछ विषय 2': 1271, 'भारतीय इतिहास के कुछ विषय 3': 1272, 'भारतीय समाज': 1273,
        'भूगोल मे प्रयोगात्मक कार्य 2': 1274, 'भौतिकी 1': 1275, 'भौतिकी 2': 1276, 'मनोविज्ञान': 1277, 'मानव भूगोल के मूल सिद्धांत': 1278,
        'रसायन 1': 1279, 'रसायन 2': 1280, 'लेखाशास्त्र 1': 1281, 'लेखाशास्त्र 2': 1282, 'व्यवसाय अध्ययन 1': 1283, 'व्यवसाय अध्ययन 2': 1284,
        'व्यष्टी अर्थशास्त्र एक परिचय': 1285, 'समकालीन विश्व राजनीती': 1286, 'समष्टी अर्थशास्त्र एक परिचय': 1287, 'स्वतंत्र भारत मे राजनीति': 1288}),
}


def main():
    new = {}   # (board, id) -> url
    missing = []
    for prefix, (board, cls, table) in MAP.items():
        folder = next(os.path.join(SRC, d) for d in os.listdir(SRC) if d.startswith(prefix))
        have = {os.path.splitext(f)[0].strip(): f for f in os.listdir(folder)}
        for stem, bid in table.items():
            f = have.pop(stem, None)
            if not f:
                missing.append((prefix, stem))
                continue
            rel = f'covers/{board}/class_{cls}/{bid}.jpg'
            os.makedirs(os.path.join(ROOT, os.path.dirname(rel)), exist_ok=True)
            shutil.copyfile(os.path.join(folder, f), os.path.join(ROOT, rel))
            old = os.path.join(ROOT, rel[:-4] + '.webp')       # replace our generated placeholder cover
            if os.path.exists(old):
                os.remove(old)
            new[(board, cls, bid)] = RAW + rel
        for left in have:
            print('NOT MAPPED (file has no entry):', prefix, left)
    for m in missing:
        print('MISSING FILE for entry:', m)

    def fix(books, board, cls):
        n = 0
        for b in books:
            u = new.get((board, cls, b['id']))
            if u and b.get('coverUrl') != u:
                b['coverUrl'] = u
                n += 1
        return n

    total = 0
    for pat, key in (('*/class_*/*/books.json', 'books'), ('*/class_*/*/*/chapters.json', 'books')):
        for p in glob.glob(os.path.join(ROOT, pat)):
            parts = p.replace(os.sep, '/').split('/')
            board = parts[-4] if parts[-1] == 'books.json' else parts[-5]
            if board not in ('ncert', 'maharastra'):
                continue
            d = json.load(open(p, encoding='utf-8'))
            cls = int(parts[-3 if parts[-1] == 'books.json' else -4].replace('class_', ''))
            n = fix(d.get(key) or [], board, cls)
            if n:
                total += n
                json.dump(d, open(p, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    print('covers copied:', len(new), '| book entries updated:', total)


main()
