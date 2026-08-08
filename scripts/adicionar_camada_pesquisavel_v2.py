#!/usr/bin/env python3
import argparse, json, os
from pathlib import Path
import fitz

ap=argparse.ArgumentParser();ap.add_argument('--year',type=int,required=True);ap.add_argument('--out',default='saida_v2');a=ap.parse_args()
root=Path(a.out)/str(a.year);idx=json.load(open(root/f'search-index-v2-{a.year}.json',encoding='utf-8'));manifest=json.load(open(root/f'manifest-v2-{a.year}.json',encoding='utf-8'))

def key(x):return (str(x.get('iso','')),str(x.get('n','')))
groups={}
for p in idx:groups.setdefault(key(p),[]).append(p)
for g in groups.values():g.sort(key=lambda p:int(p.get('page',0) or 0))

ok=0;fail=0
for m in manifest:
    pdf=root/'EDICOES_PDF'/m['pdf_file'];pages=groups.get((str(m.get('iso','')),str(m.get('n',''))),[])
    doc=fitz.open(pdf)
    if len(doc)!=len(pages):
        print('AVISO contagem divergente',pdf.name,len(doc),len(pages));fail+=1;doc.close();continue
    for i,p in enumerate(pages):
        text=(p.get('text') or '').strip()
        if not text:continue
        pg=doc[i];rect=fitz.Rect(pg.rect.x0+4,pg.rect.y0+4,pg.rect.x1-4,pg.rect.y1-4);inserted=False
        for fs in (1.0,0.8,0.6,0.45,0.3):
            r=pg.insert_textbox(rect,text,fontsize=fs,fontname='helv',render_mode=3,overlay=True,align=0)
            if r>=0:
                inserted=True;break
        if not inserted:
            # Último recurso: texto invisível em linhas muito pequenas; não altera a imagem.
            y=6.0
            for line in text.splitlines():
                if line.strip():pg.insert_text((6,y),line[:1000],fontsize=0.25,fontname='helv',render_mode=3,overlay=True)
                y+=0.32
                if y>pg.rect.height-5:break
    meta=doc.metadata or {};meta.update({'title':f'Jornal Santuário da Trindade — {a.year}','keywords':'Acervo Digital JST; OCR V2; jornal histórico','producer':'Acervo Digital JST — camada OCR V2 invisível'})
    doc.set_metadata(meta);tmp=pdf.with_suffix('.v2.tmp.pdf');doc.save(tmp,garbage=3,deflate=True);doc.close();os.replace(tmp,pdf);ok+=1
print(f'CAMADA_PESQUISAVEL: {ok} PDFs atualizados; {fail} falhas')
if fail:raise SystemExit(1)
