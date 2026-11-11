#!/usr/bin/env python3
"""Синхронизация id файлов Google Drive в data.json.

Если файл на диске заменили (новый id при том же имени в той же папке),
находит замену по списку из Apps Script и правит id в data.json, затем
пересобирает сайт. Память «где лежал файл» — _src/paths.json,
число файлов в прошлом списке — _src/sync-state.json.

Коды выхода: 0 — всё в порядке (в том числе предупреждения о пропавших
файлах), 1 — ошибка или сработала защита, ничего не изменено.
"""
import json
import os
import re
import subprocess
import sys
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data.json"
PATHS_PATH = ROOT / "paths.json"
STATE_PATH = ROOT / "sync-state.json"
MIN_ITEMS = 500
MIN_RATIO = 0.8        # новый список не меньше 80% прошлого
MAX_REPLACED = 5       # замен за один прогон
FOLDER_MIME = "application/vnd.google-apps.folder"


def norm(s):
    s = unicodedata.normalize("NFC", s or "")
    return re.sub(r"\s+", " ", s.strip().lower())


def fetch_index(url, key):
    full = url + ("&" if "?" in url else "?") + urllib.parse.urlencode({"key": key})
    req = urllib.request.Request(full, headers={"User-Agent": "arthouse-sync"})
    with urllib.request.urlopen(req, timeout=120) as r:
        raw = r.read().decode("utf-8")
    return json.loads(raw)


def read_text(p):
    return p.read_text(encoding="utf-8").replace("\r\n", "\n")


def write_text(p, s):
    p.write_text(s, encoding="utf-8", newline="\n")


def dump_json(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=1) + "\n"


def fail(msg):
    print(f"::error::sync: {msg}")
    return 1


def rec_of(c):
    return {"obj": c.get("objectFolder"), "parent": c.get("parentId"),
            "name": c.get("name"), "mime": c.get("mimeType")}


def main():
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding="utf-8")
        except Exception:
            pass
    url = os.environ.get("DRIVE_INDEX_URL", "").strip()
    key = os.environ.get("DRIVE_INDEX_KEY", "").strip()
    if not url or not key:
        return fail("DRIVE_INDEX_URL / DRIVE_INDEX_KEY не заданы")
    try:
        idx = fetch_index(url, key)
    except Exception as e:
        return fail(f"не удалось получить список с диска ({type(e).__name__})")
    if not isinstance(idx, dict):
        return fail("ответ списка — не JSON-объект")
    if idx.get("error"):
        return fail(f"сервер вернул ошибку: {repr(idx.get('error'))[:200]}")
    items = idx.get("items")
    if not isinstance(items, list):
        return fail("в ответе нет списка items")
    items = [c for c in items if isinstance(c, dict) and c.get("id")]
    if len(items) < MIN_ITEMS:
        return fail(f"в списке слишком мало файлов ({len(items)} < {MIN_ITEMS}), ничего не меняю")

    state = {}
    if STATE_PATH.exists():
        try:
            state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            state = {}
    prev_n = state.get("items")
    if isinstance(prev_n, int) and len(items) < prev_n * MIN_RATIO:
        return fail(f"список сильно уменьшился ({prev_n} -> {len(items)}), ничего не меняю")

    by_id = {c["id"]: c for c in items}

    crlf = b"\r\n" in DATA_PATH.read_bytes()
    text = read_text(DATA_PATH)
    data = json.loads(text)
    paths = json.loads(PATHS_PATH.read_text(encoding="utf-8")) if PATHS_PATH.exists() else {}

    # все ссылки: (slug, k, lang|None, id)
    refs = []
    for pr in data["projects"]:
        for it in pr.get("items", []):
            v = it.get("id")
            if isinstance(v, dict):
                for lang, i in v.items():
                    refs.append((pr["slug"], it["k"], lang, i))
            elif isinstance(v, str):
                refs.append((pr["slug"], it["k"], None, v))

    checked = len(refs)
    used = {r[3] for r in refs}
    new_paths = dict(paths)
    missing = []       # (slug, k, id) — по первому упоминанию id
    seen = set()
    for slug, k, lang, fid in refs:
        if fid in seen:
            continue
        seen.add(fid)
        cur = by_id.get(fid)
        if cur:
            new_paths[fid] = rec_of(cur)
        else:
            missing.append((slug, k, fid))

    # защита от массовой пропажи (сбой диска или списка)
    limit = max(3, checked // 10)
    if len(missing) > limit:
        return fail(f"пропало {len(missing)} ссылок из {checked} (порог {limit}) — похоже на сбой, ничего не меняю")

    # поиск замен
    proposals = {}   # old -> candidate
    warn_lines = []
    for slug, k, fid in missing:
        rec = paths.get(fid)
        cand = None
        if rec:
            rmime = rec.get("mime")
            rfolder = rmime == FOLDER_MIME
            cands = [c for c in items
                     if c.get("objectFolder") == rec.get("obj")
                     and norm(c.get("name")) == norm(rec.get("name"))
                     and bool(c.get("isFolder")) == rfolder
                     and c.get("mimeType") == rmime
                     and c["id"] not in used]
            same = [c for c in cands if c.get("parentId") == rec.get("parent")]
            if same:
                if len(same) == 1:
                    cand = same[0]
            elif len(cands) == 1:
                cand = cands[0]
        if cand:
            proposals[fid] = cand
        else:
            warn_lines.append(f"::warning::{slug} {k}: файл {fid} пропал с диска, замену не нашёл")

    # два старых id не могут стать одним новым (например, en и ru)
    targets = {}
    for old, c in proposals.items():
        targets.setdefault(c["id"], []).append(old)
    mapping = {}
    where = {fid: (slug, k) for slug, k, fid in missing}
    for new, olds in targets.items():
        if len(olds) > 1:
            for old in olds:
                slug, k = where[old]
                warn_lines.append(f"::warning::{slug} {k}: файл {old} пропал с диска, замена {new} спорная (подходит нескольким ссылкам), не меняю")
        else:
            mapping[olds[0]] = proposals[olds[0]]

    if len(mapping) > MAX_REPLACED:
        return fail(f"замен за прогон {len(mapping)} > {MAX_REPLACED} — похоже на сбой, ничего не меняю")

    # правка data.json
    new_text = text
    for old, c in mapping.items():
        new_text = new_text.replace(f'"{old}"', f'"{c["id"]}"')
    changed = new_text != text
    if changed:
        try:
            json.loads(new_text)
        except Exception:
            return fail("после замен data.json не разбирается, не записываю")
        for old, c in mapping.items():
            if f'"{old}"' in new_text or f'"{c["id"]}"' not in new_text:
                return fail(f"проверка замены {old} -> {c['id']} не прошла, не записываю")
        for old, c in mapping.items():
            new_paths[c["id"]] = rec_of(c)
            new_paths.pop(old, None)
        write_text(DATA_PATH, new_text.replace("\n", "\r\n") if crlf else new_text)

    for line in warn_lines:
        print(line)

    write_text(PATHS_PATH, dump_json(new_paths))
    write_text(STATE_PATH, dump_json({"items": len(items)}))

    if changed:
        subprocess.run([sys.executable, str(ROOT / "build.py")], check=True, cwd=str(ROOT.parent))

    print(f"sync: проверено ссылок {checked}, заменено {len(mapping)}, предупреждений {len(warn_lines)}")
    for old, c in mapping.items():
        print(f"  {old} -> {c['id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
