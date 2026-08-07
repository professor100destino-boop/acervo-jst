import json, re, html, unicodedata, statistics
from pathlib import Path
from datetime import date, timedelta

ROOT=Path(__file__).resolve().parents[1]
MONTHS={1:'janeiro',2:'fevereiro',3:'março',4:'abril',5:'maio',6:'junho',7:'julho',8:'agosto',9:'setembro',10:'outubro',11:'novembro',12:'dezembro'}
MONTH_NUM={'janeiro':1,'fevereiro':2,'marco':3,'abril':4,'maio':5,'junho':6,'julho':7,'agosto':8,'setembro':9,'outubro':10,'novembro':11,'dezembro':12}

def norm(s):
    s=unicodedata.normalize('NFD',str(s or ''))
    s=''.join(c for c in s if unicodedata.category(c)!='Mn')
    return s.lower().replace('\x00',' ')

def load_json(name):
    p=ROOT/name
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else []

def gp(p): return int(p.get('globalPage') or p.get('page') or 0)

def spaced(word): return r'\W*'.join(re.escape(c) for c in word)
def yearpat(y): return r'\W*'.join(str(y))

def header_info(raw,year):
    top=norm(raw)[:1500]
    squash=re.sub(r'[^a-z0-9]','',top)
    # Primeira página normalmente traz Anno + Campinas e o número da edição.
    front=(('anno' in squash and 'campinas' in squash) or ('anno' in squash and 'trindade' in squash and 'numero' in squash) or ('campinas' in squash and 'numero' in squash))
    if not front:
        return None

    issue=None
    issue_patterns=[r'n\W*u\W*m\W*e\W*r\W*o\W*[:.º°o-]*\W*(\d{1,4})',r'\bn\W*[º°o.]\W*(\d{1,4})\b']
    for pat in issue_patterns:
        m=re.search(pat,top)
        if m:
            n=int(m.group(1))
            if 1<=n<=9999: issue=n; break

    iso=None; hitpos=99999
    for mn,mi in MONTH_NUM.items():
        pat=rf'(?<!\d)(\d(?:\W*\d)?)\W*(?:d\W*e\W*)?({spaced(mn)})\W*(?:d\W*e\W*)?({yearpat(year)})(?!\d)'
        m=re.search(pat,top)
        if not m: continue
        ds=re.sub(r'\D','',m.group(1))
        if not ds: continue
        try:
            cand=f'{year:04d}-{mi:02d}-{int(ds):02d}'; date.fromisoformat(cand)
        except: continue
        if m.start()<hitpos: iso=cand; hitpos=m.start()

    if issue is None and iso is None: return None
    return {'issue':issue,'iso':iso}

def normalize_pages(raw):
    d={}
    for p in raw:
        k=gp(p)
        if not k: continue
        if k not in d or len(str(p.get('text','')))>len(str(d[k].get('text',''))): d[k]=p
    return [d[k] for k in sorted(d)]

def known_dates(pages,year):
    out={}
    for p in pages:
        iso=p.get('iso') or p.get('dateIso')
        if not iso and re.fullmatch(r'\d{4}-\d{2}-\d{2}',str(p.get('date') or '')): iso=p.get('date')
        if iso and str(iso).startswith(str(year)): out.setdefault(str(iso),gp(p))
    return out

def infer_missing_dates(starts,year):
    anchors=[]
    for s in starts:
        if s['issue'] is not None and s['iso']:
            anchors.append((s['issue'],date.fromisoformat(s['iso'])))
    ratios=[]
    anchors=sorted(set(anchors))
    for (n1,d1),(n2,d2) in zip(anchors,anchors[1:]):
        dn=n2-n1
        if 1<=dn<=12:
            r=(d2-d1).days/dn
            if 5<=r<=16: ratios.append(r)
    step=round(statistics.median(ratios)) if ratios else 7
    # jornais desse período eram em geral semanais ou quinzenais; arredonda para 7/14.
    step=14 if step>=11 else 7
    for s in starts:
        if s['iso'] or s['issue'] is None or not anchors: continue
        n=s['issue']
        an,ad=min(anchors,key=lambda x:abs(x[0]-n))
        cand=ad+timedelta(days=step*(n-an))
        if cand.year==year:
            s['iso']=cand.isoformat(); s['date_inferred']=True
    return step

def build(year,raw,annual_original):
    pages=normalize_pages(raw); bypg={gp(p):p for p in pages}; starts=[]
    kd=known_dates(pages,year)
    if year in (1929,1930) and kd:
        for iso,pg in sorted(kd.items(),key=lambda x:x[1]):
            p=bypg[pg]; hi=header_info(p.get('text',''),year) or {}
            starts.append({'page':pg,'iso':iso,'issue':hi.get('issue'),'p':p})
    else:
        for p in pages:
            hi=header_info(p.get('text',''),year)
            if hi: starts.append({'page':gp(p),'iso':hi.get('iso'),'issue':hi.get('issue'),'p':p})

    # deduplicar por página e, quando houver, pelo número impresso.
    clean=[]; seenp=set(); seenn=set()
    for s in sorted(starts,key=lambda x:x['page']):
        if s['page'] in seenp: continue
        if s['issue'] is not None and s['issue'] in seenn: continue
        seenp.add(s['page'])
        if s['issue'] is not None: seenn.add(s['issue'])
        clean.append(s)
    starts=clean
    step=infer_missing_dates(starts,year)

    # Caso uma data continue ausente, não inventa: o cartão indicará data não identificada.
    maxpg=max([gp(p) for p in pages],default=0); eds=[]
    for i,s in enumerate(starts):
        end=starts[i+1]['page']-1 if i+1<len(starts) else maxpg
        rel=[p for p in pages if s['page']<=gp(p)<=end]
        if not rel: continue
        eds.append({'issue':s['issue'],'iso':s['iso'],'date_inferred':s.get('date_inferred',False),'start':s['page'],'end':end,'pages':len(rel),'pdf':rel[0].get('pdf') or '','original':rel[0].get('original') or annual_original.get(year) or ''})
    return eds,pages,step

STYLE=r''':root{--vinho:#591f22;--vinho2:#2d1719;--ouro:#9b7838;--papel:#f3ead6;--tinta:#2c241b;--fundo:#eee7da}*{box-sizing:border-box}body{margin:0;background:var(--fundo);color:var(--tinta);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}a{color:inherit}.top{background:linear-gradient(125deg,var(--vinho2),#68272b);color:#fff;padding:2rem 1rem}.wrap{max-width:1050px;margin:auto}.back{display:inline-block;color:#fff;text-decoration:none;border:1px solid #ffffff88;border-radius:.5rem;padding:.55rem .8rem;margin-bottom:1.3rem}h1{font:700 clamp(2.7rem,9vw,5.8rem)/.95 Georgia,serif;margin:.2rem 0}.lead{max-width:720px}.stats{display:flex;gap:1rem;flex-wrap:wrap;margin-top:1rem}.stat{background:#ffffff15;border:1px solid #ffffff33;border-radius:.6rem;padding:.65rem .9rem}main{max-width:1050px;margin:auto;padding:1.5rem 1rem 4rem}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:1rem}.doc-card{background:#fff;border-radius:.8rem;overflow:hidden;box-shadow:0 8px 24px #0001;border:1px solid #e7ddcd}.doc-head{padding:1.2rem;background:#fff}.doc-head h2{font:700 1.55rem Georgia,serif;margin:.45rem 0}.doc-head p{margin:.25rem 0;color:#665c50}.doc-head small{color:#766b5e}.badge{display:inline-block;background:#e5e3ef;color:#3e3861;padding:.2rem .55rem;border-radius:99px;font-weight:800}.doc-actions{display:flex;gap:.55rem;flex-wrap:wrap;padding:0 1.2rem 1.2rem}.btn{border:0;border-radius:.5rem;padding:.72rem 1rem;background:var(--ouro);color:#fff;text-decoration:none;font-weight:800;cursor:pointer}.btn.secondary{background:var(--vinho)}dialog{width:min(96vw,1000px);height:88vh;border:0;border-radius:.7rem;padding:0}dialog::backdrop{background:#000b}.dh{display:flex;justify-content:space-between;align-items:center;padding:.8rem;background:#2b1b19;color:#fff}.dh button{border:0;border-radius:.4rem;padding:.55rem .75rem;cursor:pointer}.reader-tabs{display:flex;gap:.45rem;align-items:center;padding:.55rem .75rem;background:#efe7d8;border-bottom:1px solid #d8c9b2}.reader-tab,.reader-copy{border:0;border-radius:.45rem;padding:.55rem .8rem;font-weight:800;cursor:pointer;background:#fff;color:var(--vinho)}.reader-tab.active{background:var(--ouro);color:#fff}.reader-copy{margin-left:auto;background:var(--vinho);color:#fff}.reader-pane{height:calc(100% - 111px);overflow:auto;background:#1b1b1b}.hidden{display:none!important}#frame{width:100%;height:100%;border:0}.ocr-text{min-height:100%;padding:1.1rem;background:#faf7ef;color:#272018;font:17px/1.65 Georgia,serif}.ocr-page{max-width:850px;margin:0 auto 1rem;background:#fff;border:1px solid #ded3c0;border-radius:.55rem;padding:1rem 1.1rem}.ocr-page h3{margin:.1rem 0 .7rem;color:var(--vinho);font:700 1.15rem Georgia,serif}.ocr-page div{white-space:pre-wrap}.ocr-empty{max-width:760px;margin:2rem auto;padding:1.2rem;background:#fff;border-radius:.6rem;color:#554a3c}@media(max-width:620px){.doc-actions .btn{flex:1;text-align:center}}'''

def datafiles(y):
    if y<=1926:return ['search-index-all.json']
    if y==1927:return ['search-index-1927.json']
    if y==1928:return ['search-index-1928-p1.json','search-index-1928-p70.json','search-index-1928-p153.json']
    return [f'search-index-{y}.json']

def dl(iso):
    if not iso:return 'Data não identificada pelo OCR'
    d=date.fromisoformat(iso); return f'{d.day} de {MONTHS[d.month]} de {d.year}'

def make_page(y,eds,pages):
    cards=[]
    for seq,e in enumerate(eds,1):
        title=f"Edição nº {e['issue']}" if e['issue'] is not None else f"Edição nº {seq}"
        pdf=str(e.get('pdf') or ''); orig=str(e.get('original') or '')
        b=['<button class="btn read" data-id="'+html.escape(pdf)+'" data-start="'+str(e['start'])+'" data-end="'+str(e['end'])+'" data-title="'+html.escape(title)+'">Ler</button>']
        if pdf:b.append('<a class="btn secondary" href="https://drive.google.com/file/d/'+html.escape(pdf)+'/view" target="_blank" rel="noopener">Abrir arquivo</a>')
        if orig:b.append('<a class="btn secondary" href="https://drive.google.com/file/d/'+html.escape(orig)+'/view" target="_blank" rel="noopener">Original</a>')
        note=' · data inferida pela sequência editorial' if e.get('date_inferred') else ''
        cards.append('<article class="doc-card"><div class="doc-head"><span class="badge">PDF</span><h2>'+html.escape(title)+'</h2><p>'+html.escape(dl(e['iso']))+'</p><small>'+str(e['pages'])+' página(s) indexada(s)'+note+'</small></div><div class="doc-actions">'+''.join(b)+'</div></article>')
    template=r'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>JST __Y__ — Acervo Digital</title><style>__STYLE__</style></head><body><header class="top"><div class="wrap"><a class="back" href="index.html">← Voltar à pesquisa</a><div>ACERVO DIGITAL JST</div><h1>__Y__</h1><p class="lead">Ano completo em edições separadas.</p><div class="stats"><div class="stat"><strong>__N__</strong> arquivo(s)/edição(ões)</div><div class="stat"><strong>__P__</strong> páginas indexadas</div></div></div></header><main><div class="grid">__CARDS__</div></main><dialog id="dlg"><div class="dh"><strong id="ttl">Leitor</strong><button id="close">Fechar</button></div><div class="reader-tabs"><button id="tabPdf" class="reader-tab active" type="button">Jornal</button><button id="tabOcr" class="reader-tab" type="button">Texto OCR</button><button id="copyOcr" class="reader-copy hidden" type="button">Copiar texto</button></div><div id="pdfPane" class="reader-pane"><iframe id="frame"></iframe></div><div id="ocrPane" class="reader-pane hidden"><div id="ocrText" class="ocr-text"></div></div></dialog><script>let pages=[];const DATAFILES=__FILES__,YEAR=__Y__,$=id=>document.getElementById(id),dlg=$('dlg'),frame=$('frame'),ttl=$('ttl'),gp=p=>Number(p.globalPage||p.page||0),esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));Promise.all(DATAFILES.map(f=>fetch(f+'?v='+Date.now(),{cache:'no-store'}).then(r=>r.ok?r.json():[]))).then(xs=>pages=xs.flat().filter(p=>Number(p.year||YEAR)===YEAR));function tab(o){$('pdfPane').classList.toggle('hidden',o);$('ocrPane').classList.toggle('hidden',!o);$('tabPdf').classList.toggle('active',!o);$('tabOcr').classList.toggle('active',o);$('copyOcr').classList.toggle('hidden',!o)}function render(s,e){let r=pages.filter(p=>gp(p)>=s&&gp(p)<=e);$('ocrText').innerHTML=r.map((p,i)=>'<article class="ocr-page"><h3>Página '+(i+1)+' da edição · página '+gp(p)+' do volume</h3><div>'+esc(p.text||'')+'</div></article>').join('')}document.addEventListener('click',e=>{let b=e.target.closest('.read');if(!b)return;ttl.textContent=b.dataset.title;frame.src=b.dataset.id?'https://drive.google.com/file/d/'+b.dataset.id+'/preview':'about:blank';render(+b.dataset.start,+b.dataset.end);tab(false);dlg.showModal()});$('close').onclick=()=>{frame.src='about:blank';dlg.close()};$('tabPdf').onclick=()=>tab(false);$('tabOcr').onclick=()=>tab(true);$('copyOcr').onclick=()=>navigator.clipboard&&navigator.clipboard.writeText($('ocrText').innerText);</script></body></html>'''
    return template.replace('__Y__',str(y)).replace('__STYLE__',STYLE).replace('__N__',str(len(eds))).replace('__P__',str(len(pages))).replace('__CARDS__','\n'.join(cards)).replace('__FILES__',json.dumps(datafiles(y)))

def main():
    base=load_json('search-index-all.json'); allp={y:[] for y in range(1923,1931)}
    for p in base:
        y=int(p.get('year') or 1922)
        if 1923<=y<=1926:allp[y].append(p)
    extra={1927:['search-index-1927.json'],1928:['search-index-1928-p1.json','search-index-1928-p70.json','search-index-1928-p153.json'],1929:['search-index-1929.json'],1930:['search-index-1930.json']}
    for y,fs in extra.items():
        for f in fs:allp[y]+=load_json(f)
    annual={1929:'18ZmFkQPkRL5dSXhwXDbiXr34ifXDR0uo',1930:'1Ye6iDuiBClCLLSBhnpyV3lvoEcsKWHbk'}
    summary={}; byyear={}
    for y in range(1923,1931):
        eds,pages,step=build(y,allp[y],annual);byyear[y]=eds
        summary[str(y)]={'edicoes_identificadas':len(eds),'paginas_indexadas':len(pages),'com_numero_impresso':sum(e['issue'] is not None for e in eds),'com_data':sum(e['iso'] is not None for e in eds),'datas_inferidas':sum(bool(e.get('date_inferred')) for e in eds),'intervalo_editorial_estimado_dias':step,'primeira_data':next((e['iso'] for e in eds if e['iso']),None),'ultima_data':next((e['iso'] for e in reversed(eds) if e['iso']),None)}
        (ROOT/f'ano-{y}.html').write_text(make_page(y,eds,pages),encoding='utf-8')
    out=ROOT/'documentacao'/'PADRONIZACAO_ANOS_1923_1930.json';out.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    ip=ROOT/'index.html'
    s=ip.read_text(encoding='utf-8')
    for y in range(1923,1931):
        m=re.search(rf"\{{year:{y},label:'[^']*',files:\d+,folder:'([^']+)'\}}",s)
        if m:s=re.sub(rf"\{{year:{y},label:'[^']*',files:\d+,folder:'[^']+'\}}",f"{{year:{y},label:'Ano organizado em edições separadas',files:{len(byyear[y])},folder:'{m.group(1)}'}}",s,count=1)
    ip.write_text(s,encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
