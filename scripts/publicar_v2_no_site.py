#!/usr/bin/env python3
import json, re
from pathlib import Path
from urllib.parse import quote

REPO='professor100destino-boop/acervo-jst'
YEARS=range(1922,1932)

def load_manifest(year):
    candidates=[Path(f'manifest-v2-{year}.json'),Path('metadados')/f'manifest-v2-{year}.json']
    for p in candidates:
        if p.exists():
            return json.loads(p.read_text(encoding='utf-8'))
    return []

def release_url(year,filename):
    return f'https://github.com/{REPO}/releases/download/ocr-v2-{year}/{quote(filename)}'

def clean_text(s):
    return re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',s)).strip()

def patch_card(year,article,manifest):
    h=re.search(r'<h2[^>]*>(.*?)</h2>',article,re.I|re.S)
    if not h:return article
    title=clean_text(h.group(1))
    item=None
    m=re.search(r'Edi[cç][aã]o\s+n[ºo.]?\s*(\d+)',title,re.I)
    if m:
        n=int(m.group(1))
        item=next((x for x in manifest if str(x.get('n','')).isdigit() and int(x['n'])==n),None)
    elif 'suplemento' in title.lower():
        item=next((x for x in manifest if str(x.get('n','')).upper()=='SUP' or 'suplement' in str(x.get('iso','')).lower()),None)
    if not item or not item.get('pdf_file'):return article
    url=release_url(year,item['pdf_file'])
    # Troca somente o primeiro link de arquivo derivado; links de "Original" ficam intactos.
    pat=re.compile(r'<a\s+class="btn secondary"\s+href="[^"]+"([^>]*)>\s*Abrir arquivo\s*</a>',re.I|re.S)
    repl=f'<a class="btn secondary" href="{url}"\\1>PDF individual OCR V2</a>'
    article2,nsub=pat.subn(repl,article,count=1)
    if not nsub:
        # páginas em que o texto do botão já tenha sido alterado numa execução anterior
        pat2=re.compile(r'<a\s+class="btn secondary"\s+href="[^"]+"([^>]*)>\s*PDF individual OCR V2\s*</a>',re.I|re.S)
        article2=pat2.sub(repl,article,count=1)
    return article2

def patch_year(year,manifest):
    path=Path(f'ano-{year}.html')
    if not path.exists():return
    s=path.read_text(encoding='utf-8')
    v2=f'search-index-v2-{year}.json'
    # Páginas anuais 1922-1930: troca a lista de índices pela versão V2.
    if 'const DATAFILES=' in s:
        s=re.sub(r'const DATAFILES=\[[^\]]*\]',f'const DATAFILES=["{v2}"]',s,count=1)
    # 1931 usa um único fetch por ID do PDF.
    s=re.sub(r"fetch\('search-index-1931\.json'",f"fetch('{v2}'",s,count=1)
    # Também cobre eventual versão V2 anterior.
    s=re.sub(r"fetch\('search-index-v2-1931\.json'",f"fetch('{v2}'",s,count=1)
    s=re.sub(r'<article\b[^>]*class="[^"]*doc-card[^"]*"[^>]*>.*?</article>',lambda m:patch_card(year,m.group(0),manifest),s,flags=re.I|re.S)
    path.write_text(s,encoding='utf-8')

for year in YEARS:
    manifest=load_manifest(year)
    if not manifest:
        print('Sem manifesto',year);continue
    patch_year(year,manifest)
    print('Página anual atualizada',year,'itens',len(manifest))
