# -*- coding: utf-8 -*-
"""Re-points every site-absolute URL in a built copy at a sub-path.

    python tools/rebase.py dist /taj-elite-demo

The site is written for the domain root (/assets/..., /dental-implants/).
On the shared server it lives at https://173.212.251.191.sslip.io/taj-elite-demo/,
so the deploy copy needs every "/..." link prefixed. Full URLs (https://...),
in-page anchors (#...) and protocol-relative URLs (//...) are left alone.
"""
import os, re, sys

root, base = sys.argv[1], sys.argv[2].rstrip("/")
assert base.startswith("/"), "base path must start with /"

ATTR = re.compile(r'(\s(?:href|src|action|poster|data-src)=")/(?!/)')   # href="/x" → href="/base/x"
REFRESH = re.compile(r'(content="\d+;\s*url=)/(?!/)')                    # meta refresh
REPLACE = re.compile(r'(location\.replace\(")/(?!/)')                      # JS redirect stubs
QUOTED_ASSETS = re.compile(r'''(['"])/assets/''')                         # '/assets/...' in inline/JS code

counts = {}
for dirpath, _, files in os.walk(root):
    for name in files:
        if not name.endswith((".html", ".js")):
            continue
        path = os.path.join(dirpath, name)
        text = open(path, encoding="utf-8").read()
        new = text
        if name.endswith(".html"):
            new = ATTR.sub(rf"\1{base}/", new)
            new = REFRESH.sub(rf"\1{base}/", new)
            new = REPLACE.sub(rf"\1{base}/", new)
        new = QUOTED_ASSETS.sub(rf"\1{base}/assets/", new)
        if new != text:
            open(path, "w", encoding="utf-8").write(new)
            counts[os.path.relpath(path, root)] = 1

# nothing site-absolute may remain (except the prefix itself)
leftover = []
for dirpath, _, files in os.walk(root):
    for name in files:
        if name.endswith(".html"):
            t = open(os.path.join(dirpath, name), encoding="utf-8").read()
            for m in re.finditer(r'\s(?:href|src)="(/(?!/)[^"]*)"', t):
                if not m.group(1).startswith(base + "/"):
                    leftover.append(f"{name}: {m.group(1)}")
print(f"rebased {len(counts)} files to {base}/")
if leftover:
    print("unexpected root links:", leftover[:10]); sys.exit(1)
