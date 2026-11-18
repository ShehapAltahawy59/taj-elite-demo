# -*- coding: utf-8 -*-
"""Cache-busting for a built copy: appends a content hash to every CSS/JS reference.

    python tools/fingerprint.py dist

assets/css/site.css → assets/css/site.css?v=<hash of its contents>
When a file changes, its URL changes, so browsers fetch the new version at once even
though CSS/JS are cached long-term. Unchanged files keep their URL and stay cached.
"""
import hashlib, os, re, sys

root = sys.argv[1]
hashes = {}
for sub in ("css", "js"):
    d = os.path.join(root, "assets", sub)
    for name in os.listdir(d):
        if name.endswith((".css", ".js")):
            hashes[f"assets/{sub}/{name}"] = hashlib.sha1(open(os.path.join(d, name), "rb").read()).hexdigest()[:10]

# a reference = the asset path directly followed by a closing quote
REF = re.compile(r"(assets/(?:css|js)/[\w.-]+\.(?:css|js))(?=[\"'])")
changed = 0
for dirpath, _, files in os.walk(root):
    for name in files:
        if not name.endswith((".html", ".js")):
            continue
        path = os.path.join(dirpath, name)
        text = open(path, encoding="utf-8").read()
        new = REF.sub(lambda m: f"{m.group(1)}?v={hashes[m.group(1)]}" if m.group(1) in hashes else m.group(1), text)
        if new != text:
            open(path, "w", encoding="utf-8").write(new); changed += 1
print(f"fingerprinted {len(hashes)} assets in {changed} files:", ", ".join(f"{k.split('/')[-1]}={v}" for k, v in hashes.items()))
