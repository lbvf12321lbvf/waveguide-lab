"""Render the complete English theory. Optional dependency: Markdown==3.8.2.

The generated HTML is committed so deploying the app does not require this tool.
Formula source is protected before Markdown parsing to preserve every TeX token.
"""
from pathlib import Path
import html
import json
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'qa/build-deps'))
import markdown

source=(ROOT/'assets/theory.md').read_text(encoding='utf-8-sig')
source=re.sub(r'^---\n.*?\n---\n','',source,flags=re.S)
references=json.loads((ROOT/'assets/references.json').read_text(encoding='utf-8'))
for ref in references: source=source.replace(']('+ref['file']+')',']('+ref['url']+')')

def render(text):
    math=[]
    def protect(match):
        math.append(match.group(0))
        return f'MATHPLACEHOLDER{len(math)-1}END'
    text=re.sub(r'\$\$[\s\S]*?\$\$|\\\([\s\S]*?\\\)|(?<!\$)\$(?!\$)[^\n$]+\$',protect,text)
    out=markdown.markdown(text,extensions=['tables','fenced_code','sane_lists'])
    for i,tex in enumerate(math):
        token=f'MATHPLACEHOLDER{i}END'
        if tex.startswith('$$'):
            out=out.replace('<p>'+token+'</p>','<div class="math-block">'+html.escape(tex)+'</div>')
        out=out.replace(token,html.escape(tex))
    return out

parts=re.split(r'^## (.+)$',source,flags=re.M)
toc=[];sections=[]
for index in range(1,len(parts),2):
    heading,body=parts[index:index+2];key=f'section-{(index-1)//2}'
    label=re.sub(r'\\[()]','',heading).replace('\\gamma','γ')
    toc.append(f'<a href="#{key}">{html.escape(label)}</a>')
    title=render('## '+heading).removeprefix('<h2>').removesuffix('</h2>')
    sections.append(f'<details class="chapter" id="{key}"'+(' open' if key=='section-0' else '')+f'><summary>{title}</summary><div class="chapter-body">{render(body)}</div></details>')
page='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Waveguide Lab — Full theory</title><link rel="icon" href="./assets/icon.svg"><link rel="stylesheet" href="./theory.css"><script defer src="./theory.js"></script></head><body>
<header><a href="./" target="_top">Waveguide Lab</a><span>Theory of a hollow cylindrical waveguide</span><a href="./assets/theory.md" download>Download Markdown</a></header>
<div class="reader"><aside><h2>Contents</h2><input id="chapter-search" type="search" placeholder="Find a chapter…" aria-label="Find a chapter"><nav>TOC</nav></aside><main>
<div class="reader-tools"><button id="expand-all">Expand all</button><button id="collapse-all">Collapse all</button><button id="print-theory">Print / PDF</button><span id="math-status" role="status">Loading equations…</span></div>
INTRO
SECTIONS
<p class="endnote">Dmitry Shchigarev · Waveguide Lab · <a href="mailto:dima.shigarev@yandex.ru">dima.shigarev@yandex.ru</a></p>
</main></div></body></html>'''
page=page.replace('TOC',''.join(toc)).replace('INTRO',render(parts[0])).replace('SECTIONS','\n'.join(sections))
(ROOT/'theory.html').write_text(page,encoding='utf-8')
formula_count=source.count('\n$$')//2
print(f'Rendered {len(sections)} complete chapters; {formula_count} display formula blocks in source.')
