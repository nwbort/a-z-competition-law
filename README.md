# A–Z Competition Law Dictionary

A cheerful, plain-English dictionary of Australian competition law — published one
letter at a time, from A towards Z.

It is a completely static site. **No analytics, no cookies, no trackers, and no
third-party requests at all** — even the fonts are served from this repo rather than
from a font CDN.

---

## Adding a word (the only thing you need to know)

1. Open **`terms.json`**.
2. Add an object to the `terms` list.
3. Commit and push. That's it — GitHub Actions builds the site and deploys it.

There is no generated output to commit: `docs/` is git-ignored and rebuilt by the
workflow on every push. Run `python3 build.py` if you want to preview the site
locally first, but you never have to.

Everything else — the letter pages, the A–Z grid, the topic pages, the search index,
the sitemap, the "next / previous word" links, the progress bar — is generated for
you. Terms are sorted alphabetically automatically, so you can add them in any order.

### A word, in full

```json
{
  "term": "Cartel",
  "aka": "Cartel conduct",
  "emoji": "🤝",
  "definition": [
    "First paragraph.",
    "Second paragraph."
  ],
  "plainly": "A casual one-liner for the 'In plain English' box.",
  "tags": ["conduct", "enforcement"],
  "seeAlso": ["ACCC"]
}
```

| Field | Required | What it does |
| --- | --- | --- |
| `term` | **yes** | The headword. Its first letter decides which letter page it lands on. |
| `definition` | **yes** | A string, or a list of paragraphs. |
| `aka` | no | The expansion, shown as *"Otherwise known as …"*. |
| `emoji` | no | A little mascot for the word. |
| `plainly` | no | The dashed **In plain English** box — the friendly, informal take. |
| `tags` | no | Topic chips at the bottom of the page, each linking to its topic page. |
| `seeAlso` | no | Other terms, by exact name. Unknown names are skipped with a warning. |
| `slug` | no | Override the URL. Defaults to a slug of `term`. |

Opening a whole new letter needs no extra work: add a `B` word and the `B` tile on
the home page turns from a dashed "soon" tile into a live, coloured one.

### Topics

Every distinct `tags` value gets its own page at `/topics/<tag>/`, listing every word
filed under it, plus an index of them all at `/topics/`. Nothing to declare: tag a
word and the topic appears — on the home page, in the **Topics** nav pill, and in the
sitemap.

Tags are matched on their slug, so `Consumer` and `consumer` land on the same page.
The first spelling seen wins as the label, and an all-lowercase tag is shown
capitalised (`enforcement` → **Enforcement**) while acronyms keep their case.

---

## Running it locally

No dependencies — just Python 3.9+.

```bash
python3 build.py            # build into docs/
python3 build.py --serve    # build, then serve on http://localhost:8000
```

`docs/` is generated and git-ignored. Never edit it by hand; edit `terms.json` or
`assets/` instead. Deleting it is harmless — the next build recreates it.

---

## Layout

```
terms.json          all the content — the file you edit
build.py            the generator (standard library only)
assets/
  style.css         all styling
  app.js            search, theme toggle, "surprise me" — all optional
  fonts/            self-hosted Fredoka + Quicksand (OFL)
docs/               generated output, git-ignored — CI builds it and Pages serves it
```

## Deploying

`.github/workflows/deploy.yml` rebuilds and publishes to GitHub Pages on every push
to the default branch, so editing `terms.json` directly in the GitHub web UI is
enough to publish a new word.

The workflow enables Pages itself and points it at Actions, so there is normally
nothing to click. If the site shows this README instead of the dictionary, Pages is
set to **Deploy from a branch** with the folder `/ (root)` — that makes Jekyll render
`README.md` as the home page and never looks inside `docs/`. Fix it at
**Settings → Pages → Build and deployment → Source: GitHub Actions**, then re-run the
*Build and deploy* workflow.

Because `docs/` is git-ignored, Actions is the only source that works: there is no
generated output in the repository for a *Deploy from a branch* setting to serve. If
you ever do want to serve from the branch instead, stop ignoring `docs/`, run
`python3 build.py`, and commit the result.

Set `site.baseUrl` in `terms.json` to the site's real address so the sitemap and
canonical links point to the right place.

---

## Accessibility & privacy notes

- Fully browsable with JavaScript disabled — search and "surprise me" are
  enhancements that hide themselves when JS is off.
- Respects `prefers-reduced-motion`.
- Nothing is ever written to your browser: no cookies, no local storage.
- Press `/` anywhere to jump to the search box.

## Licence

Site code: do as you like with it. Fonts: SIL Open Font License 1.1 — see
`assets/fonts/OFL.txt`. Dictionary content: © the author.
