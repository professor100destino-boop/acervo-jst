#!/usr/bin/env python3
import argparse, html, json, re, sys
from pathlib import Path
import processar_ano_ocr_v2 as base

EXPECTED=base.EXPECTED_ISSUES

def all_cards(year):
    s=Path(f'ano-{year}.html').read_text(encoding='utf-8',errors='ignore')
    out=[]
    for art in re.findall(r'<article\b[^>]*class="[^"]*doc-card[^"]*"[^>]*>.*?</article>',s,re.I|re.S):
        hm=re.search(r'<h2[^>]*>(.*?)</h2>',art,re.I|re.S);pm=re.search(r'<p[^>]*>(.*?)</p>',art,re.I|re.S);im=re.search(r'data-id="([^"]+)"',art,re.I)
        if not (hm and pm and im):continue
        title=re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',html.unescape(hm.group(1)))).strip();date=re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',html.unescape(pm.group(1)))).strip()
        nm=re.search(r'Edi[cç][aã]o\s+n[ºo.]?\s*(\d+)',title,re.I)
        out.append({'title':title,'date':date,'id':im.group(1),'n':int(nm.group(1)) if nm else None,'iso':base.date_to_iso(date,year),'kind':'issue' if nm else 'supplement'})
    return out

def load_pages(year):
    pages=base.load_pages(year)
    exclusions=[]
    if year==1926:
        kept=[]
        for p in pages:
            if int(p.get('globalPage',0) or 0)==1:
                exclusions.append({'globalPage':1,'reason':'Página duplicada: idêntica à última página do conjunto de 1925; preservada no original anual, não republicada em 1926.'})
                continue
            if str(p.get('n'))=='40' and not p.get('iso'):
                p['iso']='1926-sem-data-n040';p['date']='Data não identificada pelo OCR';p['date_status']='não identificada'
            kept.append(p)
        pages=kept
    if year==1931:
        cards={c['id']:c for c in all_cards(year)}
        for p in pages:
            sid=base.source_id(p);c=cards.get(sid)
            if not c:continue
            if c['kind']=='issue':
                p['n']=c['n'];p['date']=c['date'];p['iso']=c['iso'];p['kind']='issue'
            else:
                p['n']='SUP';p['date']=c['date'];p['iso']='1931-suplemento-final';p['kind']='supplement';p['title']='Suplemento final'
            p['page']=int(p.get('sourceLocalPage') or p.get('localPage') or p.get('page') or 0)
    return pages,exclusions

def metadata(year,pages):
    nums={int(p['n']) for p in pages if str(p.get('n','')).isdigit()}
    supplements={str(p.get('iso')) for p in pages if p.get('kind')=='supplement' or str(p.get('n'))=='SUP'}
    sources={base.source_id(p) for p in pages if base.source_id(p)}
    bad=[p for p in pages if not base.source_id(p) or not base.local_page(p) or not p.get('n') or not p.get('iso')]
    report={'year':year,'pages':len(pages),'issues':len(nums),'expected_issues':EXPECTED.get(year),'supplements':len(supplements),'sources':len(sources),'bad_page_mappings':len(bad),'source_ids':sorted(sources)}
    print(json.dumps(report,ensure_ascii=False,indent=2))
    ok=len(nums)==EXPECTED.get(year) and not bad
    if not ok:print('ERRO: catalogação não fechou com segurança.',file=sys.stderr)
    return ok

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--year',type=int,required=True);ap.add_argument('--metadata-only',action='store_true');ap.add_argument('--out',default='saida_v2');a=ap.parse_args()
    pages,exclusions=load_pages(a.year)
    if not pages:raise SystemExit(f'Nenhuma página encontrada para {a.year}')
    if not metadata(a.year,pages):raise SystemExit('Processamento interrompido por segurança.')
    if a.metadata_only:sys.exit(0)
    cache=Path(a.out)/f'cache_{a.year}';sources=base.download_sources(pages,cache);outdir=Path(a.out)/str(a.year);base.process(a.year,pages,sources,outdir)
    if exclusions:
        (outdir/f'exclusoes-{a.year}.json').write_text(json.dumps(exclusions,ensure_ascii=False,indent=2),encoding='utf-8')
