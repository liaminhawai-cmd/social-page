# Sharing words

Small, offline-capable tools for building English words from sounds, with Chinese (Traditional, Hong Kong usage)
alongside. Two word lists about sharing and being kind. No accounts; progress is saved on the device only.

| Page | What it does |
|---|---|
| `index.html` | launcher |
| `match.html` | match a word to its 中文, a picture, or a short meaning (two extra cards belong to words not in the round) |
| `elkonin.html` | **sound boxes**: one box for each sound. Clue on the left: *word shown*, *Chinese only*, *meaning*, or *sound only*. Letter tiles can be switched off. Check, Show, Clear. Print blank sheet. Report |
| `teacher.html` | not linked from the start page. One link per activity and clue, each **pinning** the tool on that device (the child can't switch English back on) until unlocked here; all printables; this device's report |
| `printables/` | per unit: sound-box sheets (word + 中文 to fold under; meaning + 中文; boxes only), match cards, rhyme sheets, drag-and-drop slides — editable Word / PowerPoint |
| `rhyme.html` | **make rhymes** (keep the ending, change the start; many right answers) and **rhyme or not?** (with near-misses that start the same or share a last letter) |

Words come from the vocabulary of two picture books about sharing (*Should I Share My Ice Cream?* by Mo Willems,
and a second book on being kind). No book text or images are reproduced here; definitions are original.

## Editing

`data/units.json` holds every word, its boxes, Chinese, picture (emoji), short meaning, and the rhyme families.

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
