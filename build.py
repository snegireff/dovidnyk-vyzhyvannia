#!/usr/bin/env python3
"""Assemble chapters/*.html (alphabetical) into one HTML, auto-generate TOC, render PDF.

    python3 build.py             # book.html + dovidnyk_vyzhyvannia.pdf + docs/ (needs weasyprint)
    python3 build.py --web-only  # only book.html + docs/ (no weasyprint needed)
"""
import glob, re, os, sys, shutil

WEB_ONLY = '--web-only' in sys.argv
BASE = os.path.dirname(os.path.abspath(__file__))
files = sorted(glob.glob(os.path.join(BASE, 'chapters', '*.html')))
parts = [open(f, encoding='utf-8').read() for f in files]
body = '\n'.join(parts)

# 1) wrap chapter titles for running header string-set
def wrap_title(m):
    return f'{m.group(1)}<span class="chtitle">{m.group(2)}</span></h1>'
body = re.sub(r'(<h1 class="chapter" id="[^"]+"><span class="chnum">[^<]*</span>)([^<]+)</h1>', wrap_title, body)

# 2) auto ids for numbered h2 (sN-M) and lettered appendix h2 (sБ-1)
body = re.sub(r'<h2>(\d+)\.(\d+)\.', lambda m: f'<h2 id="s{m.group(1)}-{m.group(2)}">{m.group(1)}.{m.group(2)}.', body)
body = re.sub(r'<h2>([БВГ])\.(\d+)\.', lambda m: f'<h2 id="s{m.group(1)}-{m.group(2)}">{m.group(1)}.{m.group(2)}.', body)

# 3) build detailed TOC from h1.chapter + h2
toc = ['<ol class="detailed">']
for m in re.finditer(r'<h1 class="chapter" id="([^"]+)"><span class="chnum">([^<]*)</span><span class="chtitle">([^<]+)</span></h1>(.*?)(?=<h1 class="chapter"|<div class="cover back"|\Z)', body, re.S):
    cid, chnum, title, content = m.groups()
    num = chnum.replace('РОЗДІЛ ', '')
    label = f'{num}. {title}' if chnum.startswith('РОЗДІЛ') else f'{chnum.title()}: {title}'
    toc.append(f'<li class="l1"><a href="#{cid}">{label}</a></li>')
    for h in re.finditer(r'<h2 id="([^"]+)">([^<]+)</h2>', content):
        toc.append(f'<li class="l2"><a href="#{h.group(1)}">{h.group(2)}</a></li>')
toc.append('</ol>')
body = body.replace('<!--TOC-->', '\n'.join(toc))

html = ('<!DOCTYPE html><html lang="uk"><head><meta charset="utf-8"><title>Довідник виживання</title>'
        '<link rel="stylesheet" href="style.css"></head><body>' + body + '</body></html>')
out_html = os.path.join(BASE, 'book.html')
open(out_html, 'w', encoding='utf-8').write(html)

# ---- web version for GitHub Pages (docs/) ----
docs = os.path.join(BASE, 'docs'); os.makedirs(docs, exist_ok=True)
web_html = html.replace('<link rel="stylesheet" href="style.css">',
    '<meta name="viewport" content="width=device-width, initial-scale=1"><link rel="stylesheet" href="style.css"><link rel="stylesheet" href="web.css">')
open(os.path.join(docs, 'index.html'), 'w', encoding='utf-8').write(web_html)
shutil.copy(os.path.join(BASE, 'style.css'), os.path.join(docs, 'style.css'))
print('Web version -> docs/index.html')

if WEB_ONLY:
    sys.exit(0)

# ---- PDF ----
from weasyprint import HTML
doc = HTML(out_html).render()
pdf = os.path.join(BASE, 'dovidnyk_vyzhyvannia.pdf')
doc.write_pdf(pdf)
print(f'Pages: {len(doc.pages)}  ->  {pdf}')
