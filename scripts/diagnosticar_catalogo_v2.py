#!/usr/bin/env python3
import argparse, html, json, re
from pathlib import Path
import processar_ano_ocr_v2 as base

ap=argparse.ArgumentParser();ap.add_argument('--year',type=int,required=True);a=ap.parse_args();year=a.year
s=Path(f'ano-{year}.html').read_text(encoding='utf-8',errors='ignore')
cards=[]
for art in re.findall(r'<article\b[^>]*class="[^"]*doc-card[^"]*"[^>]*>.*?</article>',s,re.I|re.S):
    hm=re.search(r'<h2[^>]*>(.*?)</h2>',art,re.I|re.S);pm=re.search(r'<p[^>]*>(.*?)</p>',art,re.I|re.S);im=re.search(r'data-id="([^"]+)"',art,re.I);sm=re.search(r'data-start="(\d+)"',art,re.I);em=re.search(r'data-end="(\d+)"',art,re.I)
    title=re.sub(r'<[^>]+>',' ',html.unescape(hm.group(1) if hm else '')).strip();date=re.sub(r'<[^>]+>',' ',html.unescape(pm.group(1) if pm else '')).strip()
    cards.append({'title':title,'date':date,'id':im.group(1) if im else None,'start':int(sm.group(1)) if sm else None,'end':int(em.group(1)) if em else None})
print('CARDS',json.dumps(cards,ensure_ascii=False,indent=2))
raw=base.load_pages(year)
print('PAGES',len(raw),'SOURCES',sorted({base.source_id(p) for p in raw if base.source_id(p)}))
if any(c['start'] is not None for c in cards):
    covered=set()
    for c in cards:
        if c['start'] is not None and c['end'] is not None:covered.update(range(c['start'],c['end']+1))
    gps=sorted(int(p['globalPage']) for p in raw if p.get('globalPage') is not None)
    print('GLOBAL_MINMAX',min(gps) if gps else None,max(gps) if gps else None)
    print('NAO_COBERTAS',[g for g in gps if g not in covered])
cardids={c['id'] for c in cards if c['id']}
sourceids={base.source_id(p) for p in raw if base.source_id(p)}
print('FONTES_FORA_DOS_CARDS',sorted(sourceids-cardids))
print('CARDS_SEM_FONTE',sorted(cardids-sourceids))
