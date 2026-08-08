#!/usr/bin/env python3
import argparse, csv, glob, json, os, re, shutil, subprocess, sys, zipfile
from pathlib import Path

EXPECTED_ISSUES={1922:14,1923:26,1924:54,1925:49,1926:40,1927:27,1928:48,1929:48,1930:32,1931:11}

def year_of(p):
    try:
        if p.get('year'): return int(p['year'])
    except Exception: pass
    iso=str(p.get('iso',''))
    if re.match(r'^19\d\d-',iso): return int(iso[:4])
    m=re.search(r'\b(19\d\d)\b',str(p.get('date','')))
    return int(m.group(1)) if m else None

def load_pages(year):
    files=[]
    for f in ['search-index.json','search-index-all.json']:
        if Path(f).exists(): files.append(f)
    extra=sorted(f for f in glob.glob('search-index-*.json') if f not in files and '-v2-' not in f and 'summary' not in f)
    files += extra
    found={}
    for fn in files:
        try: data=json.load(open(fn,encoding='utf-8'))
        except Exception: continue
        if not isinstance(data,list): continue
        for p in data:
            if year_of(p)!=year: continue
            gp=p.get('globalPage')
            if gp is not None:
                key=('g',int(gp))
            else:
                key=('i',str(p.get('iso','')),str(p.get('n','')),int(p.get('page',0) or 0))
            q=dict(p);q['year']=year;found[key]=q
    pages=list(found.values())
    def sk(p):
        gp=p.get('globalPage')
        if gp is not None:return (0,int(gp))
        return (1,str(p.get('iso','')),int(p.get('n',0) or 0),int(p.get('page',0) or 0))
    pages.sort(key=sk)
    return pages

def issue_key(p):
    return (str(p.get('iso','')), str(p.get('n','')))

def source_id(p):
    for k in ('sourcePdf','source','pdf'):
        v=p.get(k)
        if isinstance(v,str) and v.strip():return v.strip()
    return None

def local_page(p):
    for k in ('localPage','page'):
        try:
            v=int(p.get(k,0) or 0)
            if v>0:return v
        except Exception: pass
    return None

def safe_name(s):
    return re.sub(r'[^A-Za-z0-9._-]+','_',str(s)).strip('_')

def metadata(year,pages):
    issues={issue_key(p) for p in pages}
    sources={source_id(p) for p in pages if source_id(p)}
    bad=[p for p in pages if not source_id(p) or not local_page(p)]
    print(json.dumps({'year':year,'pages':len(pages),'issues':len(issues),'expected_issues':EXPECTED_ISSUES.get(year),'sources':len(sources),'bad_page_mappings':len(bad),'source_ids':sorted(sources)},ensure_ascii=False,indent=2))
    if len(issues)!=EXPECTED_ISSUES.get(year):
        print(f'AVISO: quantidade de edicoes {len(issues)} difere do esperado {EXPECTED_ISSUES.get(year)}',file=sys.stderr)
    return len(bad)==0

def download_sources(pages,cache):
    cache.mkdir(parents=True,exist_ok=True)
    ids=sorted({source_id(p) for p in pages if source_id(p)})
    paths={}
    for i,sid in enumerate(ids,1):
        out=cache/f'{safe_name(sid)}.pdf'
        paths[sid]=out
        if out.exists() and out.stat().st_size>10000:
            print(f'[{i}/{len(ids)}] cache {sid}',flush=True);continue
        print(f'[{i}/{len(ids)}] baixando {sid}',flush=True)
        subprocess.run(['gdown',sid,'-O',str(out)],check=True)
    return paths

def prep(gray,cv2):
    bg=cv2.GaussianBlur(gray,(0,0),22)
    norm=cv2.divide(gray,bg,scale=255)
    c=cv2.createCLAHE(clipLimit=1.8,tileGridSize=(8,8)).apply(norm)
    b=cv2.GaussianBlur(c,(0,0),.8)
    return cv2.addWeighted(c,1.35,b,-.35,0)

def ocr_data(img,lang,psm,pytesseract,np,Output):
    d=pytesseract.image_to_data(img,lang=lang,config=f'--oem 1 --psm {psm} -c preserve_interword_spaces=1',output_type=Output.DICT,timeout=120)
    lines={};cf=[];words=[]
    for i,t in enumerate(d['text']):
        t=(t or '').strip()
        try:c=float(d['conf'][i])
        except Exception:c=-1
        if t and c>=0:
            key=(int(d['block_num'][i]),int(d['par_num'][i]),int(d['line_num'][i]))
            lines.setdefault(key,[]).append(t);cf.append(c);words.append(t)
    text='\n'.join(' '.join(lines[k]) for k in sorted(lines))
    a=np.array(cf) if cf else np.array([])
    return {'text':text,'mean_conf':round(float(a.mean()) if len(a) else 0,2),'median_conf':round(float(np.median(a)) if len(a) else 0,2),'low_conf_pct':round(float((a<50).mean()*100) if len(a) else 100,2),'words':len(words),'chars':len(text)}

def process(year,pages,source_paths,outdir):
    import fitz, cv2, numpy as np, pytesseract
    from pytesseract import Output
    outdir.mkdir(parents=True,exist_ok=True)
    textdir=outdir/'OCR_TEXTOS';pdfdir=outdir/'EDICOES_PDF';textdir.mkdir(exist_ok=True);pdfdir.mkdir(exist_ok=True)
    langs=set(pytesseract.get_languages(config=''))
    fallback_lang='por+Latin' if 'Latin' in langs else ('por+eng' if 'eng' in langs else 'por')
    docs={}
    def doc_for(sid):
        if sid not in docs: docs[sid]=fitz.open(source_paths[sid])
        return docs[sid]
    rows=[]
    print(f'OCR de {len(pages)} paginas...',flush=True)
    for i,p in enumerate(pages,1):
        sid=source_id(p);lp=local_page(p);doc=doc_for(sid)
        if lp<1 or lp>doc.page_count: raise RuntimeError(f'pagina local invalida: {sid} p{lp}/{doc.page_count}')
        pg=doc[lp-1]
        pix=pg.get_pixmap(matrix=fitz.Matrix(150/72,150/72),colorspace=fitz.csGRAY,alpha=False)
        gray=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width)
        img=prep(gray,cv2)
        best=ocr_data(img,'por',4,pytesseract,np,Output);method='por psm4'
        if best['mean_conf']<50:
            alt=ocr_data(img,fallback_lang,3,pytesseract,np,Output)
            if alt['mean_conf']>best['mean_conf']+2 and alt['words']>=best['words']*.80:
                best=alt;method=f'{fallback_lang} psm3'
        q=dict(p);q['text']=best['text'];q['ocr_v2']=True;q['confidence']=best['mean_conf'];q['low_conf_pct']=best['low_conf_pct'];q['ocr_method']=method
        rows.append((q,best))
        if i%5==0 or i==len(pages):print(f'  {i}/{len(pages)} paginas',flush=True)
    # PDFs individuais: copia as paginas originais sem rasterizar/recomprimir.
    groups={}
    for q,b in rows: groups.setdefault(issue_key(q),[]).append((q,b))
    manifest=[]
    for pos,(key,items) in enumerate(sorted(groups.items(),key=lambda kv:min(int(x[0].get('globalPage',10**9) or 10**9) for x in kv[1])),1):
        items.sort(key=lambda x:int(x[0].get('globalPage',x[0].get('page',0)) or 0))
        first=items[0][0];iso=str(first.get('iso') or f'{year}-00-00');n=first.get('n')
        ns=f'n{int(n):03d}' if str(n).isdigit() else f'e{pos:03d}'
        fn=f'JST_{year}_{iso}_{ns}.pdf'
        nd=fitz.open()
        for q,b in items:
            sd=doc_for(source_id(q));lp=local_page(q);nd.insert_pdf(sd,from_page=lp-1,to_page=lp-1)
        nd.save(pdfdir/fn,garbage=3,deflate=False);nd.close()
        txt='\n\n'.join(f"===== PAGINA {x[0].get('page','?')} =====\n{x[0]['text']}" for x in items)
        txtfn=fn[:-4]+'_OCR_V2.txt';(textdir/txtfn).write_text(txt,encoding='utf-8')
        manifest.append({'year':year,'n':n,'date':first.get('date'),'iso':iso,'pages':len(items),'pdf_file':fn,'ocr_file':txtfn,'source_ids':sorted({source_id(x[0]) for x in items})})
    index=[q for q,b in rows]
    json.dump(index,open(outdir/f'search-index-v2-{year}.json','w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
    json.dump(manifest,open(outdir/f'manifest-v2-{year}.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    with open(outdir/f'metricas-{year}.csv','w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['edicao','data','pagina','confianca_media','mediana','abaixo_50_pct','palavras','caracteres','metodo'])
        for q,b in rows:w.writerow([q.get('n'),q.get('iso'),q.get('page'),b['mean_conf'],b['median_conf'],b['low_conf_pct'],b['words'],b['chars'],q['ocr_method']])
    with zipfile.ZipFile(outdir/f'JST_{year}_OCR_V2_TEXTOS.zip','w',zipfile.ZIP_DEFLATED) as z:
        for f in textdir.glob('*.txt'):z.write(f,f.name)
        z.write(outdir/f'metricas-{year}.csv',f'metricas-{year}.csv')
        z.write(outdir/f'manifest-v2-{year}.json',f'manifest-v2-{year}.json')
    print(f'Concluido: {len(manifest)} edicoes, {len(index)} paginas',flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--year',type=int,required=True);ap.add_argument('--metadata-only',action='store_true');ap.add_argument('--out',default='saida_v2');a=ap.parse_args()
    pages=load_pages(a.year)
    if not pages:raise SystemExit(f'Nenhuma pagina encontrada para {a.year}')
    ok=metadata(a.year,pages)
    if not ok:raise SystemExit('Mapeamento incompleto; processamento interrompido por seguranca.')
    if a.metadata_only:sys.exit(0)
    cache=Path(a.out)/f'cache_{a.year}';sources=download_sources(pages,cache)
    process(a.year,pages,sources,Path(a.out)/str(a.year))
