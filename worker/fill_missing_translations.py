#!/usr/bin/env python3
"""
Batch-fill missing AR/FA/FR translations for terms in data/terms.json.
Calls the deployed Cloudflare Worker (which proxies to Claude Haiku)
once per missing term. Does NOT overwrite any language already present.

Run:  python worker/fill_missing_translations.py
"""
import json, sys, time
import urllib.request, urllib.error

sys.stdout.reconfigure(encoding="utf-8")

WORKER = "https://cool-moon-d7ebitalk-translate.metlamari.workers.dev/"
TERMS = "C:/Users/italk/italk/data/terms.json"
LANGS = ["ar", "fa", "fr", "en"]  # languages we want to fill

def translate(el_text):
    body = json.dumps({"term": el_text, "sourceLang": "el"}).encode("utf-8")
    req = urllib.request.Request(WORKER, data=body, method="POST", headers={
        "Content-Type": "application/json",
        "Origin": "https://i-talk.gr",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    })
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))

def main():
    with open(TERMS, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Terms missing at least one of ar/fa/fr
    need = []
    for t in data["terms"]:
        missing = [l for l in LANGS if not t["translations"].get(l)]
        if missing:
            need.append((t, missing))

    print(f"Terms needing at least one translation: {len(need)}")
    if not need:
        print("Nothing to do.")
        return

    filled = 0
    failed = []
    for i, (t, missing_langs) in enumerate(need, 1):
        el = t["translations"].get("el")
        if not el:
            print(f"  [{i}/{len(need)}] SKIP {t['id']}: no EL text")
            continue
        print(f"  [{i}/{len(need)}] {t['id']}: missing {missing_langs} — asking Claude…")
        try:
            resp = translate(el)
        except Exception as e:
            print(f"    ERR: {e}")
            failed.append(t["id"])
            time.sleep(1.0)
            continue

        if not resp.get("translations"):
            print(f"    no translations returned: {resp.get('note') or resp.get('error')}")
            failed.append(t["id"])
            continue

        added = []
        for lang in missing_langs:
            v = resp["translations"].get(lang)
            if v and v.strip():
                t["translations"][lang] = v.strip()
                added.append(lang)
        if added:
            filled += 1
            print(f"    filled: {added}")
        else:
            print(f"    nothing new")
        time.sleep(0.4)

    # Write back
    with open(TERMS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print()
    print(f"Filled {filled} / {len(need)} terms")
    if failed:
        print(f"Failed ({len(failed)}):")
        for fid in failed:
            print(f"  - {fid}")

if __name__ == "__main__":
    main()
