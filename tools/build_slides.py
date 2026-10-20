#!/usr/bin/env python3
"""Drag-and-drop slides (PowerPoint, also opens in Google Slides / Keynote), from data/units.json.
   python3 tools/build_slides.py   -> printables/*.pptx  (linked from teacher.html)
Everything on a slide is a loose shape: drag tiles into boxes in EDIT view (the shapes do not move in Slide Show).
Answers are in each slide's notes."""
import random, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree
from sharing_lib import D, ROOT, icon_png, slots, key_parts, unit, EN_FONT, ZH_FONT, GREEN, GREY

OUT = ROOT / 'printables'; OUT.mkdir(exist_ok=True)
rgb = lambda h: RGBColor.from_string(h)

def text(shape, s, size=24, bold=False, zh=False, color='111111', align=PP_ALIGN.CENTER):
    tf = shape.text_frame; tf.clear(); tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    for m in ('margin_left', 'margin_right', 'margin_top', 'margin_bottom'): setattr(tf, m, Inches(0.05))
    p = tf.paragraphs[0]; p.alignment = align; r = p.add_run(); r.text = s
    r.font.size = Pt(size); r.font.bold = bold; r.font.color.rgb = rgb(color); r.font.name = EN_FONT
    rPr = r._r.get_or_add_rPr(); ea = etree.SubElement(rPr, qn('a:ea')); ea.set('typeface', ZH_FONT)

def shp(slide, kind, x, y, w, h, fill=None, line='111111', lw=2.0, name=None, dash=False):
    s = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill: s.fill.solid(); s.fill.fore_color.rgb = rgb(fill)
    else: s.fill.background()
    if line: s.line.color.rgb = rgb(line); s.line.width = Pt(lw)
    else: s.line.fill.background()
    if dash:
        from pptx.enum.dml import MSO_LINE
        s.line.dash_style = MSO_LINE.DASH
    st = s._element.find(qn('p:style'))
    if st is not None: s._element.remove(st)          # drop theme effects (shadows) so text stays crisp
    if name: s.name = name
    return s

def blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])

def new_prs():
    prs = Presentation(); prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    cp = prs.core_properties; cp.author = cp.last_modified_by = ''; cp.title = 'Sharing words'; cp.comments = ''
    return prs

def notes(slide, s): slide.notes_slide.notes_text_frame.text = s

def clue_panel(slide, wid, mode, x=0.5, y=0.5, w=12.3, h=1.5):
    """mode 'word' = English + Chinese + picture; 'meaning' = Chinese + definition."""
    wd = D['words'][wid]
    bg = shp(slide, MSO_SHAPE.RECTANGLE, x, y, w, h, fill=GREEN, line=None, name='clue panel')
    if mode == 'word':
        slide.shapes.add_picture(icon_png(wd['icon']), Inches(x + 0.3), Inches(y + 0.25), height=Inches(1.0)).name = 'picture'
        t = shp(slide, MSO_SHAPE.RECTANGLE, x + 2.4, y, 5.2, h, line=None, name='English word'); text(t, wid, 54, True)
        z = shp(slide, MSO_SHAPE.RECTANGLE, x + 7.8, y, 4.0, h, line=None, name='Chinese'); text(z, wd['zh'], 54)
    else:
        z = shp(slide, MSO_SHAPE.RECTANGLE, x + 0.3, y, 3.6, h, line=None, name='Chinese'); text(z, wd['zh'], 54)
        d = shp(slide, MSO_SHAPE.RECTANGLE, x + 4.2, y, 7.9, h, line=None, name='meaning'); text(d, wd['def'], 26, align=PP_ALIGN.LEFT)

def boxes_row(slide, chunk_slots, y, size=1.3, x0=0.5, fill=GREY, blank_idx=()):
    xs = []; x = x0
    for k, g in enumerate(chunk_slots):
        if g is not None:
            b = shp(slide, MSO_SHAPE.RECTANGLE, x, y, size, size, fill=('FFFFFF' if k in blank_idx else fill), lw=3, name=f'box {len(xs) + 1}')
            xs.append((x, y)); x += size
        else:
            x += 0.45                       # syllable / word gap
    return xs

def tile_row(slide, tiles, y, size=0.95, x0=0.5, gap=0.18, max_x=12.8):
    x = x0
    for g in tiles:
        w = size if len(g) < 3 else size * 1.3
        if x + w > max_x: x = x0; y += size + 0.2          # wrap to a second row
        t = shp(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, size, fill='FFFFFF', lw=2.5, name=f'tile {g}')
        text(t, g, 32, True); x += w + gap

def counters(slide, n, y, x0=0.5):
    for i in range(n):
        shp(slide, MSO_SHAPE.OVAL, x0 + i * 0.75, y, 0.6, 0.6, fill='2F6FB0', line='1B4A7C', lw=1.5, name=f'counter {i + 1}')

def tiles_for(rnd, answer, pool, extra=4, cap=11):
    ans = list(answer); decoys = [g for g in pool if g not in ans]   # a sound used twice (elephant: e, e) gets two tiles; rnd.shuffle(decoys)
    t = ans + decoys[:max(0, min(extra, cap - len(ans)))]; rnd.shuffle(t); return t

def deck(u):
    prs = new_prs(); rnd = random.Random(u['id']); ids = u['words']
    pool = sorted({g for w in ids for g in D['words'][w]['parts'][0]} | {g for w in ids for p in D['words'][w]['parts'] for g in p})
    # ---- match: drag each Chinese/picture tile next to its word ----
    size = -(-len(ids) // -(-len(ids) // 6)); groups = [ids[i:i + size] for i in range(0, len(ids), size)]
    for gi, grp in enumerate(groups):
        s = blank(prs); order = rnd.sample(grp, len(grp)); ans = []
        for i, wid in enumerate(grp):
            y = 0.5 + i * 1.3; wd = D['words'][wid]
            t = shp(s, MSO_SHAPE.ROUNDED_RECTANGLE, 0.6, y, 3.4, 1.05, fill=GREEN, name=f'word {wid}'); text(t, wid, 36, True)
            shp(s, MSO_SHAPE.RECTANGLE, 4.4, y, 3.4, 1.05, fill=None, line='808080', lw=2, dash=True, name=f'place {i + 1}')
        for i, wid in enumerate(order):
            y = 0.5 + i * 1.3; wd = D['words'][wid]
            t = shp(s, MSO_SHAPE.ROUNDED_RECTANGLE, 8.6, y, 2.3, 1.05, fill='FFFFFF', lw=2.5, name=f'中文 {wid}'); text(t, wd['zh'], 34)
            s.shapes.add_picture(icon_png(wd['icon']), Inches(11.25), Inches(y + 0.1), height=Inches(0.85)).name = f'picture {wid}'
        notes(s, 'Answers: ' + '; '.join(f"{w} = {D['words'][w]['zh']} {D['words'][w]['icon']}" for w in grp) + '. Drag a 中文 tile (and its picture) into the dotted box next to its word.')
    # ---- sound boxes: word shown, then Chinese + meaning ----
    for mode in ('word', 'meaning'):
        for wid in ids:
            s = blank(prs); sl = slots(wid); n = sum(1 for g in sl if g)
            clue_panel(s, wid, mode); boxes_row(s, sl, 2.4)
            counters(s, n, 4.0)
            allg = [g for p in D['words'][wid]['parts'] for g in p]
            tile_row(s, tiles_for(rnd, allg, pool), 5.15)
            wd = D['words'][wid]
            notes(s, f"Answer: {'  /  '.join(' · '.join(p) for p in wd['parts'])}" + (f"\n{wd['tip']}" if wd.get('tip') else '') +
                  '\nCounters first: say the word slowly and slide one counter into each box for each sound. Then swap the counters for letter tiles.')
    # ---- rhyme: change the start, keep the ending ----
    for f in [f for f in D['rhymes'] if f['unit'] == u['id']]:
        s = blank(prs); onset, rime = key_parts(f); wd = D['words'][f['key']]
        clue_panel(s, f['key'], 'word')
        sl = list(onset + rime); boxes_row(s, sl, 2.4, blank_idx=range(len(onset)))
        for k, g in enumerate(rime):       # the ending is printed in its boxes
            t = [sh for sh in s.shapes if sh.name == f'box {len(onset) + k + 1}'][0]; text(t, g, 40, True)
        starts = sorted({w[:len(w) - len(f['rime'])] for w in f['words'] if w != f['key']})
        pool_on = [g for g in 'b c d f g h j k l m n p r s t w y z bl cr gl gr qu sh sn tr'.split() if g not in starts]; rnd.shuffle(pool_on)
        tile_row(s, starts + pool_on[:max(0, 11 - len(starts))], 4.3)
        notes(s, f"Rhymes with {f['key']}: " + ', '.join(f"{w} {f['gloss'][w]}" for w in f['words'] if w != f['key']) +
              f"\nSome tiles make words that are not in the list; ask whether it is a real word.")
    return prs

if __name__ == '__main__':
    for i, u in enumerate(D['units'], 1):
        deck(u).save(OUT / f'U{i}_drag-and-drop-slides.pptx')
    print('wrote', len(D['units']), 'decks to', OUT)
