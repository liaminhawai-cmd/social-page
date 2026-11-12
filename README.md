# Sharing words

Small, offline-capable tools for building English words from sounds, with Chinese (Traditional, Hong Kong usage)
alongside. Word lists from picture books about sharing, being kind and cheering up a sad friend. No accounts; progress is saved on the device only.

| Page | What it does |
|---|---|
| `index.html` | launcher |
| `match.html` | match a word to its 中文, a picture, or a short meaning (two extra cards belong to words not in the round) |
| `elkonin.html` | **sound boxes**: one box for each sound. Clue on the left: *word shown*, *Chinese only*, *meaning*, or *sound only*. Letter tiles can be switched off. **Box sounds**: a 🔊 under each box plays the recorded sound for that box, and ▶ all plays them in order, lighting each box; switch off for a dictation without help. Check, Show, Clear. Print blank sheet. Report |
| `teacher.html` | not linked from the start page. One link per activity and clue, each **pinning** the tool on that device (the child can't switch English back on) until unlocked here; all printables; this device's report |
| `printables/` | per unit: sound-box sheets (word + 中文 to fold under; meaning + 中文; boxes only), match cards, rhyme sheets, drag-and-drop slides — editable Word / PowerPoint |
| `rhyme.html` | **make rhymes** (keep the ending, change the start; many right answers) and **rhyme or not?** (with near-misses that start the same or share a last letter) |

Words come from the vocabulary of two picture books about sharing (*Should I Share My Ice Cream?* by Mo Willems,
a second book on being kind, and *My Friend Is Sad* by Mo Willems). No book text or images are reproduced here; definitions are original.

## Editing

`data/units.json` holds every word, its boxes, Chinese, picture (emoji), short meaning, and the rhyme families. Each word lists one recorded sound per box (`sounds`), and `boxTips` gives the rule for a box whose letter makes an unusual sound in that word (the o in *to*). Names and calls from the books (gerald, piggie, yee, haw, ohhh, um) are left out, and so are *i* (one box) and *anyone* (the o in one is two sounds, /w/ + /u/).

`data/phonemes.json` is generated: the human recordings of each sound, copied as base64 from the Phonics repo (`recordings/au/phonemes`) so the page needs no network and the repo holds no audio files. Re-run `python3 tools/import-phonemes.py` after a recording changes there.

```bash
python3 tools/build.py --all    # validates the data, writes printables/, then the .html pages
python3 tools/build.py          # pages only
PUBLIC_DENY="a,b" python3 tools/check-public.py   # before every push — see AGENTS.md
```

The generated `.html` files are committed so GitHub Pages can serve them directly (Settings → Pages → Deploy from
branch → `main` / root). Do not edit them by hand. Printables need `python-docx`, `python-pptx` and `Pillow`;
the pictures are emoji drawn from Noto Color Emoji.

## Privacy

No analytics, no network calls, no external fonts or scripts. Saved data is in `localStorage` on the device
(`sharing-tools-v1`) and can be deleted from the Report window. The pictures are emoji drawn by the device.
