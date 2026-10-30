#!/usr/bin/env python3
"""Generates the Art House materials mini-site from data.json (stdlib only)."""
import json
import re
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT.parent
DATA = json.loads((ROOT / "data.json").read_text(encoding="utf-8"))

SHORT = ("Ð²", "Ð¸", "Ð°", "Ñ", "Ðº", "Ð¾", "Ñƒ", "Ð½Ð°", "Ð½Ðµ", "Ð¿Ð¾", "Ð·Ð°", "Ð¸Ð·", "Ð´Ð¾",
         "Ð¾Ñ‚", "Ð´Ð»Ñ", "Ð¿Ñ€Ð¸", "Ð½Ð¾", "Ñ‚Ð¾", "Ð¶Ðµ", "Ð»Ð¸", "Ð±Ñ‹")
SHORT_RE = re.compile(r"(?<![\w])(" + "|".join(SHORT) + r")[ \t]+", re.I)
DASH_RE = re.compile(r"\s+â€”\s+")

T = {
    "en": {
        "title": "Project Materials",
        "home_title": "Art House â€” Project Materials",
        "lead": "Sales kits, price lists, layouts and&nbsp;photos â€”&nbsp;for&nbsp;agents.",
        "desc": "Sales kits, price lists, layouts and photos of Art House projects â€” for real estate agents.",
        "og_desc": "Sales kits, price lists, layouts and photos â€” for agents.",
        "open": "Open materials â†’",
        "back": "â† All projects",
        "wa": "Questions?",
        "hints": {"pdf": "PDF", "folder": "Folder", "image": "Image", "video": "Video"},
    },
    "ru": {
        "title": "ÐœÐ°Ñ‚ÐµÑ€Ð¸Ð°Ð»Ñ‹ Ð¿Ð¾ Ð¾Ð±ÑŠÐµÐºÑ‚Ð°Ð¼",
        "home_title": "Art House â€” ÐœÐ°Ñ‚ÐµÑ€Ð¸Ð°Ð»Ñ‹ Ð¿Ð¾ Ð¾Ð±ÑŠÐµÐºÑ‚Ð°Ð¼",
        "lead": "Sales kit, Ð¿Ñ€Ð°Ð¹ÑÑ‹, Ð¿Ð»Ð°Ð½Ð¸Ñ€Ð¾Ð²ÐºÐ¸ Ð¸ Ñ„Ð¾Ñ‚Ð¾ â€” Ð´Ð»Ñ Ð°Ð³ÐµÐ½Ñ‚Ð¾Ð².",
        "desc": "Sales kit, Ð¿Ñ€Ð°Ð¹ÑÑ‹, Ð¿Ð»Ð°Ð½Ð¸Ñ€Ð¾Ð²ÐºÐ¸ Ð¸ Ñ„Ð¾Ñ‚Ð¾ Ð¾Ð±ÑŠÐµÐºÑ‚Ð¾Ð² Art House â€” Ð´Ð»Ñ Ð°Ð³ÐµÐ½Ñ‚Ð¾Ð² Ð¿Ð¾ Ð½ÐµÐ´Ð²Ð¸Ð¶Ð¸Ð¼Ð¾ÑÑ‚Ð¸.",
        "og_desc": "Sales kit, Ð¿Ñ€Ð°Ð¹ÑÑ‹, Ð¿Ð»Ð°Ð½Ð¸Ñ€Ð¾Ð²ÐºÐ¸ Ð¸ Ñ„Ð¾Ñ‚Ð¾ â€” Ð´Ð»Ñ Ð°Ð³ÐµÐ½Ñ‚Ð¾Ð².",
        "open": "ÐžÑ‚ÐºÑ€Ñ‹Ñ‚ÑŒ Ð¼Ð°Ñ‚ÐµÑ€Ð¸Ð°Ð»Ñ‹ â†’",
        "back": "â† Ð’ÑÐµ Ð¾Ð±ÑŠÐµÐºÑ‚Ñ‹",
        "wa": "Ð’Ð¾Ð¿Ñ€Ð¾ÑÑ‹?",
        "hints": {"pdf": "PDF", "folder": "ÐŸÐ°Ð¿ÐºÐ°", "image": "ÐšÐ°Ñ€Ñ‚Ð¸Ð½ÐºÐ°", "video": "Ð’Ð¸Ð´ÐµÐ¾"},
    },
}

ICONS = {
    "pdf": '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4"/><path d="M9 13h6M9 17h6"/>',
    "folder": '<path d="M3 6h6l2 2h10v11H3z"/>',
    "image": '<rect x="3" y="4" width="18" height="16"/><circle cx="9" cy="10" r="1.6"/><path d="M3 18l6-5 4 3 3-2 5 4"/>',
    "video": '<rect x="3" y="5" width="18" height="14"/><path d="M10 9l5 3-5 3z"/>',
}


def typo(text, lang):
    """Escape + non-breaking spaces. Short-word joining only for RU; dash for both."""
    s = html.escape(text, quote=False)
    if lang == "ru":
        # two passes so that consecutive short words ("Ð¸ Ð½Ð° ...") are all joined
        s = SHORT_RE.sub(lambda m: m.group(1) + "&nbsp;", s)
        s = SHORT_RE.sub(lambda m: m.group(1) + "&nbsp;", s)
    return DASH_RE.sub("&nbsp;â€” ", s)


def esc(s):
    return html.escape(s, quote=True)


def pick_id(item, lang):
    i = item["id"]
    if isinstance(i, dict):
        other = "ru" if lang == "en" else "en"
        return i.get(lang) or i.get(other)
    return i


def drive_url(item, lang):
    fid = pick_id(item, lang)
    if item["t"] == "folder":
        return f"https://drive.google.com/drive/folders/{fid}"
    return f"https://drive.google.com/file/d/{fid}/view"


def lang_switch(lang, other_href):
    if lang == "en":
        return f'<nav class="lang" aria-label="Language"><b>EN</b> Â· <a href="{other_href}" hreflang="ru" lang="ru">RU</a></nav>'
    return f'<nav class="lang" aria-label="Language"><a href="{other_href}" hreflang="en" lang="en">EN</a> Â· <b>RU</b></nav>'


def head(lang, base, title, desc=None, og=None):
    out = [
        "<!DOCTYPE html>",
        f'<html lang="{lang}">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{esc(title)}</title>",
    ]
    if desc:
        out.append(f'<meta name="description" content="{desc}">')
    out += [
        '<meta name="theme-color" content="#F3EEE6">',
        '<meta name="color-scheme" content="light">',
        f'<link rel="icon" href="{base}favicon.svg" type="image/svg+xml">',
        f'<link rel="apple-touch-icon" href="{base}icon.png">',
    ]
    if og:
        out += [
            '<meta property="og:type" content="website">',
            f'<meta property="og:title" content="{esc(og[0])}">',
            f'<meta property="og:description" content="{esc(og[1])}">',
            '<meta property="og:image" content="https://all.arthouse.asia/img/above-condominium.webp">',
        ]
    out += [
        '<link rel="preconnect" href="https://fonts.googleapis.com">',
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
        '<link href="https://fonts.googleapis.com/css2?family=Jost:wght@600&family=Manrope:wght@400;500;600&display=swap" rel="stylesheet">',
        f'<link rel="stylesheet" href="{base}style.css">',
        "</head>",
        "<body>",
    ]
    return out


def header_top(lang, base, home_href, switch_href):
    return [
        "<header>",
        '<div class="wrap">',
        '<div class="top">',
        f'<a href="{home_href}"><img class="logo" src="{base}logo.svg" alt="Art House Group" width="745" height="628"></a>',
        lang_switch(lang, switch_href),
        "</div>",
    ]


def footer(lang):
    t = T[lang]
    return [
        "<footer>",
        '<div class="wrap">',
        '<p class="slogan">Build. Manage. Trust<i>.</i></p>',
        f'<p>{typo(t["wa"], lang)} <a href="https://wa.me/66935844499" target="_blank" rel="noopener">WhatsApp +66&nbsp;93&nbsp;584&nbsp;4499</a></p>',
        '<p class="copy">Â© Art&nbsp;House Group</p>',
        "</div>",
        "</footer>",
        "</body>",
        "</html>",
    ]


def write(rel, lines):
    p = SITE / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


PROJECTS = {p["slug"]: p for p in DATA["projects"]}


def build_home(lang):
    t = T[lang]
    base = "" if lang == "en" else "../"
    switch = "ru/" if lang == "en" else "../"
    lead = t["lead"] if lang == "en" else typo(t["lead"], lang)
    out = head(lang, base, t["home_title"], esc(t["desc"]),
               (t["home_title"], t["og_desc"]))
    out += header_top(lang, base, "./", switch)
    out += [f"<h1>{typo(t['title'], lang)}</h1>", f'<p class="lead">{lead}</p>', "</div>", "</header>", "",
            '<main class="wrap">', ""]
    for g in DATA["groups"]:
        out += ["<section>", f"<h2>{typo(g['name'], lang)}</h2>", '<div class="grid">']
        for slug in g["projects"]:
            p = PROJECTS[slug]
            out.append(
                f'<a class="tile" href="{slug}/"><span class="ph"><img src="{base}img/thumb/{slug}.webp" alt="" width="192" height="192"></span>'
                f'<span class="tx"><span class="name">{typo(p["name"], lang)}</span><span class="open">{typo(t["open"], lang)}</span></span></a>')
        out += ["</div>", "</section>", ""]
    out += ["</main>", ""] + footer(lang)
    write("index.html" if lang == "en" else "ru/index.html", out)


def build_project(lang, p):
    t = T[lang]
    slug = p["slug"]
    base = "../" if lang == "en" else "../../"
    home = "../"  # EN: site root; RU: site/ru/
    switch = f"../ru/{slug}/" if lang == "en" else f"../../{slug}/"
    title = f"{p['name']} â€” Art House"
    out = head(lang, base, title)
    out += header_top(lang, base, home, switch)
    out += [
        f'<a class="back" href="{home}">{typo(t["back"], lang)}</a>',
        f'<div class="ptitle"><span class="ph"><img src="{base}img/thumb/{slug}.webp" alt="" width="192" height="192"></span>'
        f'<h1>{typo(p["name"], lang)}</h1></div>',
        "</div>", "</header>", "", '<main class="wrap">', "",
    ]
    for gk in ("docs", "plans", "media"):
        items = [i for i in p["items"] if DATA["labels"][i["k"]]["g"] == gk]
        if not items:
            continue
        out += ["<section>", f"<h2>{typo(DATA['groupLabels'][gk][lang], lang)}</h2>", '<div class="grid">']
        for i in items:
            lab = DATA["labels"][i["k"]]
            icon = ICONS[i["t"]]
            out.append(
                f'<a class="row" href="{drive_url(i, lang)}" target="_blank" rel="noopener">'
                f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round" aria-hidden="true">{icon}</svg>'
                f'<span class="lb">{typo(lab[lang], lang)}</span><span class="hint">{t["hints"][i["t"]]}</span></a>')
        out += ["</div>", "</section>", ""]
    out += ["</main>", ""] + footer(lang)
    write(f"{slug}/index.html" if lang == "en" else f"ru/{slug}/index.html", out)


def main():
    n_home = n_proj = 0
    for lang in ("en", "ru"):
        build_home(lang)
        n_home += 1
        for p in DATA["projects"]:
            build_project(lang, p)
            n_proj += 1
    print(f"OK: {n_home} home pages, {n_proj} project pages")


if __name__ == "__main__":
    main()
