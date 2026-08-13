#!/usr/bin/env python3
"""Build the A-Z Competition Law Dictionary.

Reads terms.json, writes a completely static site into docs/.
No dependencies beyond the Python standard library, no network access,
and nothing in the output phones home.

    python3 build.py            # build into docs/
    python3 build.py --serve    # build, then serve on http://localhost:8000
"""

from __future__ import annotations

import html
import json
import re
import shutil
import sys
import unicodedata
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
SRC = ROOT / "assets"
OUT = ROOT / "docs"

LETTERS = [chr(c) for c in range(ord("A"), ord("Z") + 1)]

# Tile colours, cycled so every letter and card gets its own personality.
PALETTE = ["--accent-a", "--accent-b", "--accent-c", "--accent-d", "--accent-e", "--accent-f"]

DOODLES = ["⚖️", "🔍", "📚", "🦘", "✨", "📎"]

# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def esc(text: object) -> str:
    """HTML-escape a value, including quotes, for safe attribute/text use."""
    return html.escape(str(text), quote=True)


def slugify(text: str) -> str:
    """'Section 46' -> 'section-46'. Stable, lowercase, URL-safe."""
    norm = unicodedata.normalize("NFKD", str(text))
    norm = norm.encode("ascii", "ignore").decode("ascii")
    norm = re.sub(r"[^a-zA-Z0-9]+", "-", norm).strip("-").lower()
    return norm or "term"


def topic_url(slug: str) -> str:
    return f"/topics/{slug}/"


def topic_label(name: str) -> str:
    """'regulator' -> 'Regulator', leaving 'ACCC' and 'eSafety' as written."""
    return name[0].upper() + name[1:] if name and name[0].islower() else name


def paragraphs(value: object) -> list[str]:
    """Accept a string or a list of strings; always return a list."""
    if value is None:
        return []
    if isinstance(value, str):
        return [p.strip() for p in value.split("\n\n") if p.strip()]
    return [str(p).strip() for p in value if str(p).strip()]


def plain(text: str, limit: int = 150) -> str:
    """A one-line, tag-free summary for meta descriptions and cards."""
    flat = re.sub(r"\s+", " ", str(text)).strip()
    if len(flat) <= limit:
        return flat
    return flat[: limit - 1].rsplit(" ", 1)[0] + "…"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# --------------------------------------------------------------------------
# load + validate
# --------------------------------------------------------------------------

def collect_topics(terms: list[dict]) -> list[dict]:
    """Group terms by tag into topics, one per distinct tag.

    Tags are matched on their slug, so 'Consumer' and 'consumer' are the same
    topic; the first spelling seen (alphabetically by term) becomes the label.
    """
    topics: dict[str, dict] = {}

    for t in terms:
        for tag in t["tags"]:
            slug = slugify(tag)
            topic = topics.get(slug)
            if topic is None:
                topic = topics[slug] = {
                    "name": topic_label(tag),
                    "slug": slug,
                    "url": topic_url(slug),
                    "terms": [],
                }
            if not any(seen is t for seen in topic["terms"]):
                topic["terms"].append(t)

    ordered = sorted(topics.values(), key=lambda x: x["name"].lower())

    for i, topic in enumerate(ordered):
        topic["tile"] = PALETTE[i % len(PALETTE)]
        topic["tilt"] = [-0.8, 0.6, -0.4, 0.9, -1.1, 0.35][i % 6]

    # Give each term its resolved topics, so tag chips can link to the pages.
    by_slug = {topic["slug"]: topic for topic in ordered}
    for t in terms:
        t["topicLinks"] = [by_slug[slugify(tag)] for tag in t["tags"]]

    return ordered


def load() -> tuple[dict, list[dict], list[dict]]:
    data = json.loads((ROOT / "terms.json").read_text(encoding="utf-8"))
    site = data.get("site", {})
    site.setdefault("title", "A–Z Competition Law Dictionary")
    site.setdefault("tagline", "")
    site.setdefault("description", site["tagline"])
    site.setdefault("baseUrl", "")
    site.setdefault("lang", "en-AU")
    site["baseUrl"] = site["baseUrl"].rstrip("/")

    terms: list[dict] = []
    seen: dict[str, str] = {}

    for raw in data.get("terms", []):
        name = str(raw.get("term", "")).strip()
        if not name:
            raise SystemExit("A term is missing its 'term' field in terms.json")

        letter = name[0].upper()
        if letter not in LETTERS:
            raise SystemExit(f"Term {name!r} does not start with a letter A–Z")

        slug = slugify(raw.get("slug") or name)
        url = f"/{letter.lower()}/{slug}/"
        if url in seen:
            raise SystemExit(f"Two terms produce the same URL {url!r}: {seen[url]!r} and {name!r}")
        seen[url] = name

        body = paragraphs(raw.get("definition"))
        if not body:
            raise SystemExit(f"Term {name!r} has no 'definition'")

        terms.append(
            {
                "term": name,
                "aka": str(raw.get("aka", "")).strip(),
                "emoji": str(raw.get("emoji", "")).strip(),
                "definition": body,
                "plainly": str(raw.get("plainly", "")).strip(),
                "tags": [str(t).strip() for t in raw.get("tags", []) if str(t).strip()],
                "seeAlso": [str(t).strip() for t in raw.get("seeAlso", []) if str(t).strip()],
                "letter": letter,
                "slug": slug,
                "url": url,
                "blurb": plain(body[-1] if len(body) > 1 else body[0]),
            }
        )

    terms.sort(key=lambda t: (t["letter"], t["term"].lower()))

    # Resolve see-also names into links, warning rather than failing on typos.
    by_name = {t["term"].lower(): t for t in terms}
    for t in terms:
        links = []
        for ref in t["seeAlso"]:
            target = by_name.get(ref.lower())
            if target and target["url"] != t["url"]:
                links.append(target)
            elif not target:
                print(f"  ! see-also '{ref}' on '{t['term']}' has no matching term yet — skipped")
        t["seeAlsoLinks"] = links

    # Give each term a stable colour and a stable little tilt.
    for i, t in enumerate(terms):
        t["tile"] = PALETTE[i % len(PALETTE)]
        t["tilt"] = [-0.9, 0.7, -0.5, 1.0, -1.2, 0.4][i % 6]

    topics = collect_topics(terms)

    return site, terms, topics


# --------------------------------------------------------------------------
# page shell
# --------------------------------------------------------------------------

def shell(*, site: dict, depth: int, title: str, description: str, body: str,
          canonical: str = "", nav_current: str = "") -> str:
    up = "../" * depth
    base = site["baseUrl"]
    doodles = "".join(f'<span class="doodle">{d}</span>' for d in DOODLES)
    canon = f'\n  <link rel="canonical" href="{esc(base + canonical)}">' if base and canonical else ""
    current = ' aria-current="page"' if nav_current == "topics" else ""
    nav = f'<a class="pill" href="{up}topics/"{current}>🏷️ Topics</a>'

    return f"""<!doctype html>
<html lang="{esc(site['lang'])}" data-root="{esc(up)}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <meta name="color-scheme" content="light">
  <meta name="theme-color" content="#ff5a33">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:type" content="website">{canon}
  <link rel="icon" href="{up}icon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="{up}style.css">
</head>
<body>
  <a class="skip" href="#main">Skip to content</a>
  <div class="doodles" aria-hidden="true">{doodles}</div>

  <div class="shell">
    <header class="site-head">
      <a class="brand" href="{up or './'}"><span aria-hidden="true">⚖️</span> A–Z Competition Law</a>
      <nav class="head-nav" aria-label="Site">
        {nav}
        <button class="pill" type="button" data-random hidden>🎲 Surprise me</button>
      </nav>
    </header>

    <main id="main">
{body}
    </main>
  </div>

  <script src="{up}terms-index.js"></script>
  <script src="{up}app.js"></script>
</body>
</html>
"""


def search_block(*, placeholder: str) -> str:
    return f"""      <form class="searchbox panel" data-search hidden role="search">
        <label class="sr-only" for="q">Search the dictionary</label>
        <span class="glass" aria-hidden="true">🔍</span>
        <input id="q" type="search" autocomplete="off" placeholder="{esc(placeholder)}">
        <p class="sr-only" data-search-status role="status" aria-live="polite"></p>
      </form>
      <div class="results" data-results></div>
"""


def term_card(t: dict, up: str) -> str:
    aka = f'<span class="aka">{esc(t["aka"])}</span>' if t["aka"] else ""
    emoji = f'<span aria-hidden="true">{esc(t["emoji"])}</span> ' if t["emoji"] else ""
    return f"""          <li>
            <a class="term-card" href="{up}{t['url'].lstrip('/')}" style="--tile: var({t['tile']}); --tilt: {t['tilt']}deg;">
              <h3>{emoji}{esc(t['term'])}</h3>
              {aka}
              <p>{esc(t['blurb'])}</p>
            </a>
          </li>
"""


def topic_card(topic: dict, up: str) -> str:
    n = len(topic["terms"])
    return f"""          <li>
            <a class="topic" href="{up}{topic['url'].lstrip('/')}" style="--tile: var({topic['tile']}); --tilt: {topic['tilt']}deg;">
              <span class="name">{esc(topic['name'])}</span>
              <span class="count">{n} word{"s" if n != 1 else ""}</span>
            </a>
          </li>
"""


# --------------------------------------------------------------------------
# pages
# --------------------------------------------------------------------------

def page_home(site: dict, terms: list[dict], topics: list[dict]) -> str:
    by_letter: dict[str, list[dict]] = {}
    for t in terms:
        by_letter.setdefault(t["letter"], []).append(t)

    live = [l for l in LETTERS if by_letter.get(l)]

    tiles = []
    for i, letter in enumerate(LETTERS):
        got = by_letter.get(letter, [])
        if got:
            n = len(got)
            tiles.append(
                f'        <li><a class="letter" href="{letter.lower()}/" '
                f'style="--tile: var({PALETTE[i % len(PALETTE)]});">{letter}'
                f'<span class="count">{n} word{"s" if n != 1 else ""}</span></a></li>'
            )
        else:
            tiles.append(
                f'        <li><span class="letter soon" aria-label="{letter} — coming soon">'
                f'{letter}<span class="count" aria-hidden="true">soon</span></span></li>'
            )

    newest = "".join(term_card(t, "") for t in terms)

    topic_panel = ""
    if topics:
        topic_panel = f"""
        <section class="panel">
          <h2 class="panel-title"><span class="emoji" aria-hidden="true">🏷️</span> Browse by topic</h2>
          <ul class="topics">
{"".join(topic_card(topic, "") for topic in topics)}          </ul>
        </section>
"""

    body = f"""      <section class="hero">
        <div class="ribbon">
          <h1>{esc(site['title'])}<span class="tag">{esc(site['tagline'])}</span></h1>
        </div>
      </section>

{search_block(placeholder='Search a word… (press / to jump here)')}

      <div data-browse>
        <section class="panel">
          <h2 class="panel-title"><span class="emoji" aria-hidden="true">✏️</span> Browse the alphabet</h2>
          <ul class="alphabet">
{chr(10).join(tiles)}
          </ul>
        </section>
{topic_panel}
        <section class="panel">
          <h2 class="panel-title"><span class="emoji" aria-hidden="true">📖</span> Every word so far</h2>
          <ul class="terms">
{newest}          </ul>
        </section>
      </div>

      <aside class="callout">
        <span class="emoji" aria-hidden="true">🌱</span>
        <p>New letters land here as they are written. Nothing to subscribe to, nothing tracking you — just pop back whenever you like.</p>
      </aside>
"""
    return shell(
        site=site, depth=0, title=site["title"], description=site["description"],
        body=body, canonical="/",
    )


def page_topics(site: dict, topics: list[dict]) -> str:
    if topics:
        cards = "".join(topic_card(topic, "../") for topic in topics)
        n = len(topics)
        listing = f"""      <p class="hero-sub" style="margin-left:0;text-align:left">{n} topic{"s" if n != 1 else ""} so far — pick one to see every word filed under it.</p>

      <section class="panel">
        <ul class="topics">
{cards}        </ul>
      </section>
"""
        desc = "Browse the dictionary by topic: " + ", ".join(t["name"] for t in topics) + "."
    else:
        listing = """      <div class="card panel">
        <p class="empty"><span class="big" aria-hidden="true">🏷️</span>
        No topics yet — they appear as soon as a word is given some tags.</p>
      </div>
"""
        desc = "Browse the dictionary by topic."

    body = f"""      <section class="term-head">
        <a class="eyebrow" href="../">← Home</a>
        <h1>🏷️ Topics</h1>
      </section>

{listing}
      <nav class="pager" aria-label="Topics">
        <a href="../">← Home</a>
      </nav>
"""
    return shell(
        site=site, depth=1, title=f"Topics — {site['title']}",
        description=plain(desc, 155), body=body, canonical="/topics/",
        nav_current="topics",
    )


def page_topic(site: dict, topic: dict, topics: list[dict]) -> str:
    i = topics.index(topic)
    prev_t = topics[i - 1] if i > 0 else None
    next_t = topics[i + 1] if i < len(topics) - 1 else None

    items = topic["terms"]
    cards = "".join(term_card(t, "../../") for t in items)
    word = "word" if len(items) == 1 else "words"

    pager = []
    pager.append(
        f'<a href="../{prev_t["slug"]}/">← {esc(prev_t["name"])}</a>'
        if prev_t else '<a href="../">← All topics</a>'
    )
    if next_t:
        pager.append(f'<a href="../{next_t["slug"]}/">{esc(next_t["name"])} →</a>')

    body = f"""      <section class="term-head">
        <a class="eyebrow" href="../">← All topics</a>
        <h1>{esc(topic['name'])}</h1>
      </section>

      <p class="hero-sub" style="margin-left:0;text-align:left">{len(items)} {word} tagged “{esc(topic['name'])}”.</p>

{search_block(placeholder='Search the whole dictionary…')}

      <div data-browse>
        <section class="panel">
          <ul class="terms">
{cards}          </ul>
        </section>
      </div>

      <nav class="pager" aria-label="Topics">
        {''.join(pager)}
      </nav>
"""
    return shell(
        site=site, depth=2,
        title=f"{topic['name']} — {site['title']}",
        description=f"Australian competition law words tagged “{topic['name']}”: "
                    + ", ".join(t["term"] for t in items) + ".",
        body=body, canonical=topic["url"], nav_current="topics",
    )


def page_letter(site: dict, letter: str, items: list[dict], live: list[str]) -> str:
    idx = live.index(letter)
    prev_l = live[idx - 1] if idx > 0 else None
    next_l = live[idx + 1] if idx < len(live) - 1 else None

    cards = "".join(term_card(t, "../") for t in items)
    word = "word" if len(items) == 1 else "words"

    pager = []
    pager.append(
        f'<a href="../{prev_l.lower()}/">← {prev_l}</a>' if prev_l else '<a href="../">← All letters</a>'
    )
    if next_l:
        pager.append(f'<a href="../{next_l.lower()}/">{next_l} →</a>')

    body = f"""      <section class="term-head">
        <a class="eyebrow" href="../">← All letters</a>
        <h1>{letter}</h1>
      </section>

      <p class="hero-sub" style="margin-left:0;text-align:left">{len(items)} {word} under {letter}.</p>

{search_block(placeholder='Search the whole dictionary…')}

      <div data-browse>
        <section class="panel">
          <ul class="terms">
{cards}          </ul>
        </section>
      </div>

      <nav class="pager" aria-label="Letters">
        {''.join(pager)}
      </nav>
"""
    return shell(
        site=site, depth=1,
        title=f"{letter} — {site['title']}",
        description=f"Australian competition law words beginning with {letter}: "
                    + ", ".join(t["term"] for t in items) + ".",
        body=body, canonical=f"/{letter.lower()}/",
    )


def page_term(site: dict, t: dict, siblings: list[dict]) -> str:
    i = siblings.index(t)
    prev_t = siblings[i - 1] if i > 0 else None
    next_t = siblings[i + 1] if i < len(siblings) - 1 else None

    defs = t["definition"]
    aka = f'<p class="aka">Otherwise known as <b>{esc(t["aka"])}</b>.</p>' if t["aka"] else ""
    # If the author already wrote an "Otherwise known as" line, do not repeat it.
    rest = [p for p in defs if not (t["aka"] and p.lower().startswith("otherwise known as"))]
    if not rest:
        rest = defs
        aka = ""

    paras = "".join(f"          <p>{esc(p)}</p>\n" for p in rest)

    plainly = ""
    if t["plainly"]:
        plainly = f"""        <div class="plainly">
          <span class="emoji" aria-hidden="true">💡</span>
          <p><strong>In plain English</strong>{esc(t['plainly'])}</p>
        </div>
"""

    meta = []
    if t["topicLinks"]:
        chips = "".join(
            f'<a class="tagchip" href="../../topics/{topic["slug"]}/">{esc(topic["name"])}</a>'
            for topic in t["topicLinks"]
        )
        meta.append(f'          <div class="meta-row"><span class="label">Topics</span>{chips}</div>')
    if t["seeAlsoLinks"]:
        chips = "".join(
            f'<a class="tagchip" href="../../{o["url"].lstrip("/")}">{esc(o["term"])} →</a>'
            for o in t["seeAlsoLinks"]
        )
        meta.append(f'          <div class="meta-row"><span class="label">See also</span>{chips}</div>')

    pager = []
    pager.append(
        f'<a href="../../{prev_t["url"].lstrip("/")}">← {esc(prev_t["term"])}</a>'
        if prev_t else f'<a href="../">← All of {t["letter"]}</a>'
    )
    if next_t:
        pager.append(f'<a href="../../{next_t["url"].lstrip("/")}">{esc(next_t["term"])} →</a>')

    emoji = f'<span aria-hidden="true">{esc(t["emoji"])}</span> ' if t["emoji"] else ""

    body = f"""      <article>
        <header class="term-head">
          <a class="eyebrow" href="../">← {t['letter']}</a>
          <h1>{emoji}{esc(t['term'])}</h1>
        </header>

        <div class="card definition panel">
{aka and '          ' + aka + chr(10)}{paras}{plainly}{chr(10).join(meta)}
        </div>
      </article>

      <nav class="pager" aria-label="Words">
        {''.join(pager)}
      </nav>

{search_block(placeholder='Look up another word…')}
      <div data-browse></div>
"""
    desc = plain(f"{t['aka'] + '. ' if t['aka'] else ''}{' '.join(rest)}", 155)
    return shell(
        site=site, depth=2,
        title=f"{t['term']} — {site['title']}",
        description=desc, body=body, canonical=t["url"],
    )


def page_404(site: dict) -> str:
    body = """      <section class="hero">
        <div class="ribbon"><h1>404<span class="tag">This page went to market and never came back</span></h1></div>
      </section>

      <div class="card panel">
        <p class="empty"><span class="big" aria-hidden="true">🔍</span>
        We could not find that one. It might be a letter we have not reached yet.</p>
      </div>

      <nav class="pager"><a href="/">← Back to A</a></nav>
"""
    return shell(site=site, depth=0, title=f"Not found — {site['title']}",
                 description="Page not found.", body=body)


# --------------------------------------------------------------------------
# assets
# --------------------------------------------------------------------------

ICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#ff3b2f"/><stop offset="1" stop-color="#ffb057"/>
  </linearGradient></defs>
  <rect width="64" height="64" rx="16" fill="url(#g)"/>
  <circle cx="28" cy="27" r="13" fill="#fffbf4" stroke="#2a2320" stroke-width="4"/>
  <path d="M38 37 L50 50" stroke="#2a2320" stroke-width="7" stroke-linecap="round"/>
  <text x="28" y="34" font-family="Verdana,DejaVu Sans,sans-serif" font-size="15"
        font-weight="bold" fill="#2a2320" text-anchor="middle">AZ</text>
</svg>
"""

def build() -> None:
    site, terms, topics = load()

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    by_letter: dict[str, list[dict]] = {}
    for t in terms:
        by_letter.setdefault(t["letter"], []).append(t)
    live = [l for l in LETTERS if by_letter.get(l)]

    # Pages
    write(OUT / "index.html", page_home(site, terms, topics))
    write(OUT / "404.html", page_404(site))

    for letter in live:
        items = by_letter[letter]
        write(OUT / letter.lower() / "index.html", page_letter(site, letter, items, live))
        for t in items:
            write(OUT / letter.lower() / t["slug"] / "index.html", page_term(site, t, items))

    write(OUT / "topics" / "index.html", page_topics(site, topics))
    for topic in topics:
        write(OUT / "topics" / topic["slug"] / "index.html", page_topic(site, topic, topics))

    # Static assets
    shutil.copyfile(SRC / "style.css", OUT / "style.css")
    shutil.copyfile(SRC / "app.js", OUT / "app.js")
    # Copies the fonts and their OFL.txt, which lives beside them in assets/.
    shutil.copytree(SRC / "fonts", OUT / "fonts")
    write(OUT / "icon.svg", ICON)
    write(OUT / ".nojekyll", "")

    # Search index, inlined as a script so it also works from file://
    index = [
        {"term": t["term"], "aka": t["aka"], "url": t["url"].lstrip("/"),
         "blurb": t["blurb"], "tags": t["tags"]}
        for t in terms
    ]
    write(
        OUT / "terms-index.js",
        "window.AZ_TERMS=" + json.dumps(index, ensure_ascii=False, separators=(",", ":")) + ";\n",
    )

    write(OUT / "robots.txt", "User-agent: *\nAllow: /\n"
          + (f"Sitemap: {site['baseUrl']}/sitemap.xml\n" if site["baseUrl"] else ""))

    if site["baseUrl"]:
        urls = (["/"] + [f"/{l.lower()}/" for l in live] + [t["url"] for t in terms]
                + ["/topics/"] + [topic["url"] for topic in topics])
        today = date.today().isoformat()
        entries = "".join(
            f"  <url><loc>{esc(site['baseUrl'] + u)}</loc><lastmod>{today}</lastmod></url>\n"
            for u in urls
        )
        write(OUT / "sitemap.xml",
              '<?xml version="1.0" encoding="UTF-8"?>\n'
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
              f"{entries}</urlset>\n")

    pages = sum(1 for _ in OUT.rglob("*.html"))
    print(f"✅ Built {len(terms)} words across {len(live)} letter(s) "
          f"and {len(topics)} topic(s) → {pages} pages in {OUT.relative_to(ROOT)}/")
    print(f"   Letters live: {', '.join(live) or '(none yet)'}")
    print(f"   Topics: {', '.join(t['name'] for t in topics) or '(none yet)'}")


def serve() -> None:
    import http.server
    import socketserver

    handler = type(
        "Handler", (http.server.SimpleHTTPRequestHandler,),
        {"__init__": lambda self, *a, **k: http.server.SimpleHTTPRequestHandler.__init__(
            self, *a, directory=str(OUT), **k)},
    )
    with socketserver.TCPServer(("", 8000), handler) as httpd:
        print("🌏 Serving http://localhost:8000  (Ctrl+C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Bye")


if __name__ == "__main__":
    build()
    if "--serve" in sys.argv:
        serve()
