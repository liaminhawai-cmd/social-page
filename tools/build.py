#!/usr/bin/env python3
"""Builds the self-contained pages in the repo root from src/*.html + src/base.css +
src/core.js + data/units.json, and lists printables/ on teacher.html.
Run from anywhere:  python3 tools/build.py            (pages only)
                    python3 tools/build.py --all      (printables and slides first, then pages)
It also validates data/units.json (boxes must spell the word; rhymes must end in the rime)."""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
data = json.loads((ROOT / 'data' / 'units.json').read_text(encoding='utf-8'))

def validate(d):
    errs = []
    for wid, w in d['words'].items():
        spelled = ''.join(''.join(p) for p in w['parts'])
        if spelled != wid.replace(' ', ''):
            errs.append(f'{wid}: boxes spell "{spelled}"')
        for g in (g for p in w['parts'] for g in p):
            if len(g) > 1 and g not in d['tips']:
                errs.append(f'{wid}: multi-letter box "{g}" has no entry in tips')
        for k in ('zh', 'icon', 'def'):
            if not w.get(k):
                errs.append(f'{wid}: missing {k}')
    for u in d['units']:
        for wid in u['words']:
            if wid not in d['words']:
                errs.append(f'unit {u["id"]}: unknown word {wid}')
    for r in d['rhymes']:
        for w in r['words']:
            if not w.endswith(r['rime']):
                errs.append(f'rhyme {r["id"]}: {w} does not end in -{r["rime"]}')
            if w not in r['gloss']:
                errs.append(f'rhyme {r["id"]}: {w} has no Chinese gloss')
        if r['key'] not in r['words']:
            errs.append(f'rhyme {r["id"]}: key {r["key"]} not in words')
        for n in r['near']:
            if n['w'].endswith(r['rime']):
                errs.append(f'rhyme {r["id"]}: near-miss {n["w"]} actually ends in -{r["rime"]}')
            if not n['w'].endswith(n['rime']):
                errs.append(f'rhyme {r["id"]}: near-miss {n["w"]} does not end in -{n["rime"]}')
    return errs

errs = validate(data)
if errs:
    print('DATA ERRORS:\n  ' + '\n  '.join(errs)); sys.exit(1)

if '--all' in sys.argv:
    import subprocess
    for script in ('build_printables.py', 'build_slides.py'):
        subprocess.run([sys.executable, str(ROOT / 'tools' / script)], check=True)

printables = sorted(p.name for p in (ROOT / 'printables').glob('*') if p.suffix in ('.docx', '.pptx'))
base_css = (ROOT / 'src' / 'base.css').read_text(encoding='utf-8')
core_js = (ROOT / 'src' / 'core.js').read_text(encoding='utf-8')
data_js = 'const D = ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';'
assert '</script' not in data_js and '</script' not in core_js

built = []
for src in sorted((ROOT / 'src').glob('*.html')):
    html = src.read_text(encoding='utf-8')
    html = html.replace('{{BASE_CSS}}', base_css).replace('{{CORE_JS}}', core_js).replace('{{DATA}}', data_js).replace('{{PRINTABLES}}', json.dumps(printables))
    (ROOT / src.name).write_text(html, encoding='utf-8')
    built.append(src.name)
print('built:', ', '.join(built))
