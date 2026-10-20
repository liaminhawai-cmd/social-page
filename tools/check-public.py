#!/usr/bin/env python3
"""Public-repo check. Fails loudly (exit 1) instead of relying on memory.
   PUBLIC_DENY="word1,word2" python3 tools/check-public.py
The deny list comes from the environment on purpose: never commit the names you are protecting.
Checks: denied words in any text file or path; no network calls or external loads in the pages;
no images, PDFs or office documents in the repo (no book scans, no planning documents)."""
import os, re, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
files = subprocess.run(['git', 'ls-files', '-co', '--exclude-standard'], cwd=ROOT, capture_output=True, text=True).stdout.split('\n')
files = [f for f in files if f and (ROOT / f).is_file()]
deny = [d.strip() for d in os.environ.get('PUBLIC_DENY', '').split(',') if d.strip()]
bad = []
if not deny:
    print('note: PUBLIC_DENY is empty — set it to the names that must never appear.')
BLOCKED_EXT = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.docx', '.doc', '.pptx', '.xlsx', '.mp3', '.mp4', '.wav'}
NET = re.compile(r'fetch\s*\(|XMLHttpRequest|sendBeacon|WebSocket|importScripts|<script[^>]+src=|<link[^>]+href=|@import|https?://', re.I)
for f in files:
    p = ROOT / f; ext = p.suffix.lower()
    if ext in BLOCKED_EXT: bad.append(f'{f}: file type not allowed in this repo'); continue
    for d in deny:
        if re.search(re.escape(d), f, re.I): bad.append(f'{f}: path contains a denied word')
    try: t = p.read_text(encoding='utf-8')
    except Exception: continue
    for d in deny:
        for m in re.finditer(re.escape(d), t, re.I):
            bad.append(f'{f}:{t[:m.start()].count(chr(10)) + 1}: denied word "{d}"'); break
    if ext in ('.html', '.js', '.css') and not f.startswith('tools/'):
        for m in NET.finditer(t):
            bad.append(f'{f}:{t[:m.start()].count(chr(10)) + 1}: network call or external load: {m.group(0)[:40]}'); break
print(f'checked {len(files)} files' + (f' for {len(deny)} denied words' if deny else ''))
if bad:
    print('FAIL\n  ' + '\n  '.join(bad)); sys.exit(1)
print('ok')
