import json
import re
import html
import unicodedata
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
MONTHS = {1:'janeiro',2:'fevereiro',3:'março',4:'abril',5:'maio',6:'junho',7:'julho',8:'agosto',9:'setembro',10:'outubro',11:'novembro',12:'dezembro'}
MONTH_NUM = {'janeiro':1,'fevereiro':2,'marco':3,'abril':4,'maio':5,'junho':6,'julho':7,'agosto':8,'setembro':9,'outubro':10,'novembro':11,'dezembro':12}


def norm(s):
    s = unicodedata.normalize('NFD', str(s or ''))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return s.lower().replace('\x00',' ')


def load_json(name):
    p = ROOT / name
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else []


def gpage(p):
    return int(p.get('globalPage') or p.get('page') or 0)


def date_label(iso):
    d = date.fromisoformat(iso)
    return f'{d.day} de {MONTHS[d.month]} de {d.year}'


def spaced_word(word):
    return r'\W*'.join(re.escape(ch) for ch in word)


def year_pattern(year):
    return r'\W*'.join(str(year))


def find_date_in_header(raw, year):
    top = norm(raw)[:1400]
    squash = re.sub(r'[^a-z0-9]', '', top)
    cues = sum(k in squash for k in ('anno','campinas','santuario','trindade'))
    if cues < 2:
        return None

    best = None
    for name, month in MONTH_NUM.items():
        mp = spaced_word(name)
        yp = year_pattern(year)
        # Aceita 7, 15 e também OCR do tipo 1 5; aceita 'd e', 'J a n e ir o' e '1 9 2 8'.
        pat = rf'(?<!\d)(\d(?:\W*\d)?)\W*(?:d\W*e\W*)?({mp})\W*(?:d\W*e\W*)?({yp})(?!\d)'
        m = re.search(pat, top)
        if not m:
            continue
        daytxt = re.sub(r'\D', '', m.group(1))
        if not daytxt:
            continue
        day = int(daytxt)
        try:
            iso = f'{year:04d}-{month:02d}-{day:02d}'
            date.fromisoformat(iso)
        except ValueError:
            continue
        if best is None or m.start() < best[0]:
            best = (m.start(), m.end(), iso, top)
    return best


def find_issue_number(raw, year):
    hit = find_date_in_header(raw, year)
    top = norm(raw)[:1600]
    if hit:
        _, end, _, _ = hit
        areas = [top[end:end+500], top[:1200]]
    else:
        areas = [top[:1200]]
    patterns = [
        r'n\W*u\W*m\W*e\W*r\W*o\W*[:.º°o-]*\W*(\d{1,4})',
        r'\bn\W*[º°o.]\W*(\d{1,4})\b',
    ]
    for area in areas:
        for pat in patterns:
            m = re.search(pat, area)
            if m:
                n = int(m.group(1))
                if 1 <= n <= 9999:
                    return n
    return None


def detect_header(p, year):
    hit = find_date_in_header(p.get('text',''), year)
    if not hit:
        return None
    return {'iso': hit[2], 'issue': find_issue_number(p.get('text',''), year)}


def normalize_pages(pages):
    ded = {}
    for p in pages:
        k = gpage(p)
        if not k:
            continue
        if k not in ded or len(str(p.get('text',''))) > len(str(ded[k].get('text',''))):
            ded[k] = p
    return [ded[k] for k in sorted(ded)]


def build_editions(year, rawpages, annual_original):
    pages = normalize_pages(rawpages)
    bypage = {gpage(p): p for p in pages}

    known = {}
    for p in pages:
        iso = p.get('iso') or p.get('dateIso')
        if not iso and re.fullmatch(r'\d{4}-\d{2}-\d{2}', str(p.get('date') or '')):
            iso = p.get('date')
        if iso and str(iso).startswith(str(year)):
            known.setdefault(str(iso), gpage(p))

    starts = []
    if year in (1929, 1930) and known:
        # Nesses dois anos já conferimos manualmente as datas; não acrescentar falsos positivos do OCR.
        for iso, pg in sorted(known.items(), key=lambda x:x[1]):
            p = bypage[pg]
            starts.append((pg, {'iso': iso, 'issue': find_issue_number(p.get('text',''), year)}, p))
    else:
        for p in pages:
            h = detect_header(p, year)
            if h:
                starts.append((gpage(p), h, p))

    # Deduplica por data e por página inicial.
    starts.sort(key=lambda x:x[0])
    uniq=[]; seen_dates=set(); seen_pages=set()
    for x in starts:
        if x[0] in seen_pages or x[1]['iso'] in seen_dates:
            continue
        seen_pages.add(x[0]); seen_dates.add(x[1]['iso']); uniq.append(x)
    starts=uniq

    maxpg=max([gpage(p) for p in pages], default=0)
    editions=[]
    for i,(start,h,p0) in enumerate(starts):
        end=starts[i+1][0]-1 if i+1<len(starts) else maxpg
        rel=[p for p in pages if start <= gpage(p) <= end]
        if not rel:
            continue
        editions.append({
            'iso':h['iso'], 'issue':h['issue'], 'start':start, 'end':end,
            'pages':len(rel), 'pdf':rel[0].get('pdf') or '',
            'original':rel[0].get('original') or annual_original.get(year) or ''
        })
    return editions,pages


STYLE = r'''
:root{--vinho:#591f22;--vinho2:#2d1719;--ouro:#9b7838;--papel:#f3ead6;--tinta:#2c241b;--fundo:#eee7da}*{box-sizing:border-box}body{margin:0;background:var(--fundo);color:var(--tinta);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}a{color:inherit}.top{background:linear-gradient(125deg,var(--vinho2),#68272b);color:#fff;padding:2rem 1rem}.wrap{max-width:1050px;margin:auto}.back{display:inline-block;color:#fff;text-decoration:none;border:1px solid #ffffff88;border-radius:.5rem;padding:.55rem .8rem;margin-bottom:1.3rem}h1{font:700 clamp(2.7rem,9vw,5.8rem)/.95 Georgia,serif;margin:.2rem 0}.lead{max-width:720px}.stats{display:flex;gap:1rem;flex-wrap:wrap;margin-top:1rem}.stat{background:#ffffff15;border:1px solid #ffffff33;border-radius:.6rem;padding:.65rem .9rem}main{max-width:1050px;margin:auto;padding:1.5rem 1rem 4rem}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:1rem}.doc-card{background:#fff;border-radius:.8rem;overflow:hidden;box-shadow:0 8px 24px #0001;border:1px solid #e7ddcd}.doc-head{padding:1.2rem;background:#fff}.doc-head h2{font:700 1.55rem Georgia,serif;margin:.45rem 0}.doc-head p{margin:.25rem 0;color:#665c50}.doc-head small{color:#766b5e}.badge{display:inline-block;background:#e5e3ef;color:#3e3861;padding:.2rem .55rem;border-radius:99px;font-weight:800}.doc-actions{display:flex;gap:.55rem;flex-wrap:wrap;padding:0 1.2rem 1.2rem}.btn{border:0;border-radius:.5rem;padding:.72rem 1rem;background:var(--ouro);color:#fff;text-decoration:none;font-weight:800;cursor:pointer}.btn.secondary{background:var(--vinho)}dialog{width:min(96vw,1000px);height:88vh;border:0;border-radius:.7rem;padding:0}dialog::backdrop{background:#000b}.dh{display:flex;justify-content:space-between;align-items:center;padding:.8rem;background:#2b1b19;color:#fff}.dh button{border:0;border-radius:.4rem;padding:.55rem .75rem;cursor:pointer}.reader-tabs{display:flex;gap:.45rem;align-items:center;padding:.55rem .75rem;background:#efe7d8;border-bottom:1px solid #d8c9b2}.reader-tab,.reader-copy{border:0;border-radius:.45rem;padding:.55rem .8rem;font-weight:800;cursor:pointer;background:#fff;color:var(--vinho)}.reader-tab.active{background:var(--ouro);color:#fff}.reader-copy{margin-left:auto;background:var(--vinho);color:#fff}.reader-pane{height:calc(100% - 111px);overflow:auto;background:#1b1b1b}.hidden{display:none!important}#frame{width:100%;height:100%;border:0}.ocr-text{min-height:100%;padding:1.1rem;background:#faf7ef;color:#272018;font:17px/1.65 Georgia,serif;user-select:text;-webkit-user-select:text;cursor:text}.ocr-page{max-width:850px;margin:0 auto 1rem;background:#fff;border:1px solid #ded3c0;border-radius:.55rem;padding:1rem 1.1rem}.ocr-page h3{margin:.1rem 0 .7rem;color:var(--vinho);font:700 1.15rem Georgia,serif}.ocr-page div{white-space:pre-wrap;user-select:text;-webkit-user-select:text}.ocr-empty{max-width:760px;margin:2rem auto;padding:1.2rem;background:#fff;border-radius:.6rem;color:#554a3c}@media(max-width:620px){.doc-actions .btn{flex:1;text-align:center}.reader-copy{font-size:.82rem;padding:.5rem .6rem}}
'''


def datafiles(year):
    if year <= 1926: return ['search-index-all.json']
    if year == 1927: return ['search-index-1927.json']
    if year == 1928: return ['search-index-1928-p1.json','search-index-1928-p70.json','search-index-1928-p153.json']
    return [f'search-index-{year}.json']


def make_page(year, editions, pages):
    cards=[]
    for seq,e in enumerate(editions,1):
        dlab=date_label(e['iso'])
        title=f"Edição nº {e['issue']}" if e['issue'] is not None else f"Edição nº {seq}"
        pdf=str(e.get('pdf') or '')
        buttons=['<button class="btn read" data-id="'+html.escape(pdf)+'" data-start="'+str(e['start'])+'" data-end="'+str(e['end'])+'" data-title="'+html.escape(title)+'">Ler</button>']
        if pdf:
            buttons.append('<a class="btn secondary" href="https://drive.google.com/file/d/'+html.escape(pdf)+'/view" target="_blank" rel="noopener">Abrir arquivo</a>')
        original=str(e.get('original') or '')
        if original:
            buttons.append('<a class="btn secondary" href="https://drive.google.com/file/d/'+html.escape(original)+'/view" target="_blank" rel="noopener">Original</a>')
        cards.append('<article class="doc-card"><div class="doc-head"><span class="badge">PDF</span><h2>'+html.escape(title)+'</h2><p>'+html.escape(dlab)+'</p><small>'+str(e['pages'])+' página(s) indexada(s)</small></div><div class="doc-actions">'+''.join(buttons)+'</div></article>')

    page=r'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>JST __YEAR__ — Acervo Digital</title><style>__STYLE__</style></head><body>
<header class="top"><div class="wrap"><a class="back" href="index.html">← Voltar à pesquisa</a><div>ACERVO DIGITAL JST</div><h1>__YEAR__</h1><p class="lead">Ano completo em edições separadas.</p><div class="stats"><div class="stat"><strong>__COUNT__</strong> arquivo(s)/edição(ões)</div><div class="stat"><strong>__PAGES__</strong> páginas indexadas</div></div></div></header>
<main><div class="grid">__CARDS__</div></main>
<dialog id="dlg"><div class="dh"><strong id="ttl">Leitor</strong><button id="close">Fechar</button></div><div class="reader-tabs"><button id="tabPdf" class="reader-tab active" type="button">Jornal</button><button id="tabOcr" class="reader-tab" type="button">Texto OCR</button><button id="copyOcr" class="reader-copy hidden" type="button">Copiar texto</button></div><div id="pdfPane" class="reader-pane"><iframe id="frame" title="Leitor do jornal"></iframe></div><div id="ocrPane" class="reader-pane hidden"><div id="ocrText" class="ocr-text" tabindex="0"></div></div></dialog>
<script>
let pages=[];const DATAFILES=__FILES__;const YEAR=__YEAR__;const $=id=>document.getElementById(id),dlg=$('dlg'),frame=$('frame'),ttl=$('ttl');const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));const preview=id=>'https://drive.google.com/file/d/'+id+'/preview';const gp=p=>Number(p.globalPage||p.page||0);
Promise.all(DATAFILES.map(f=>fetch(f+'?v='+Date.now(),{cache:'no-store'}).then(r=>r.ok?r.json():[]).catch(()=>[]))).then(xs=>{pages=xs.flat().filter(p=>Number(p.year||YEAR)===YEAR).sort((a,b)=>gp(a)-gp(b));});
function renderOcr(start,end){const rel=pages.filter(p=>gp(p)>=start&&gp(p)<=end);const box=$('ocrText');if(!rel.length){box.innerHTML='<div class="ocr-empty"><strong>Texto OCR ainda não disponível para esta edição.</strong></div>';return}box.innerHTML=rel.map((p,i)=>'<article class="ocr-page"><h3>Página '+(i+1)+' da edição · página '+gp(p)+' do volume</h3><div>'+esc(p.text||'')+'</div></article>').join('')}
function tab(which){const ocr=which==='ocr';$('pdfPane').classList.toggle('hidden',ocr);$('ocrPane').classList.toggle('hidden',!ocr);$('tabPdf').classList.toggle('active',!ocr);$('tabOcr').classList.toggle('active',ocr);$('copyOcr').classList.toggle('hidden',!ocr);if(ocr)$('ocrText').focus({preventScroll:true})}
document.addEventListener('click',e=>{const b=e.target.closest('.read');if(!b)return;const id=b.dataset.id;ttl.textContent=b.dataset.title;frame.src=id?preview(id):'about:blank';renderOcr(Number(b.dataset.start),Number(b.dataset.end));tab('pdf');dlg.showModal()});$('close').onclick=()=>{frame.src='about:blank';dlg.close()};$('tabPdf').onclick=()=>tab('pdf');$('tabOcr').onclick=()=>tab('ocr');$('copyOcr').onclick=async()=>{const text=$('ocrText').innerText;try{await navigator.clipboard.writeText(text);$('copyOcr').textContent='Copiado!';setTimeout(()=>$('copyOcr').textContent='Copiar texto',1400)}catch(e){const r=document.createRange();r.selectNodeContents($('ocrText'));const sel=getSelection();sel.removeAllRanges();sel.addRange(r)}};
</script></body></html>'''
    return (page.replace('__YEAR__',str(year)).replace('__STYLE__',STYLE).replace('__COUNT__',str(len(editions))).replace('__PAGES__',str(len(pages))).replace('__CARDS__','\n'.join(cards)).replace('__FILES__',json.dumps(datafiles(year),ensure_ascii=False)))


def main():
    base=load_json('search-index-all.json')
    allpages={y:[] for y in range(1923,1931)}
    for p in base:
        y=int(p.get('year') or 1922)
        if 1923 <= y <= 1926:
            allpages[y].append(p)
    extras={1927:['search-index-1927.json'],1928:['search-index-1928-p1.json','search-index-1928-p70.json','search-index-1928-p153.json'],1929:['search-index-1929.json'],1930:['search-index-1930.json']}
    for y,files in extras.items():
        for f in files: allpages[y].extend(load_json(f))

    annual_original={1929:'18ZmFkQPkRL5dSXhwXDbiXr34ifXDR0uo',1930:'1Ye6iDuiBClCLLSBhnpyV3lvoEcsKWHbk'}
    summary={}; editions_by_year={}
    for y in range(1923,1931):
        eds,pages=build_editions(y,allpages[y],annual_original)
        editions_by_year[y]=eds
        summary[str(y)]={'edicoes_identificadas':len(eds),'paginas_indexadas':len(pages),'com_numero_impresso':sum(e['issue'] is not None for e in eds),'primeira_data':eds[0]['iso'] if eds else None,'ultima_data':eds[-1]['iso'] if eds else None}
        (ROOT/f'ano-{y}.html').write_text(make_page(y,eds,pages),encoding='utf-8')

    out=ROOT/'documentacao'/'PADRONIZACAO_ANOS_1923_1930.json'
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')

    ip=ROOT/'index.html'
    if ip.exists():
        s=ip.read_text(encoding='utf-8')
        for y in range(1923,1931):
            n=len(editions_by_year[y])
            pat=rf"\{{year:{y},label:'[^']*',files:\d+,folder:'([^']+)'\}}"
            m=re.search(pat,s)
            if m:
                s=re.sub(pat,f"{{year:{y},label:'Ano organizado em edições separadas',files:{n},folder:'{m.group(1)}'}}",s,count=1)
        ip.write_text(s,encoding='utf-8')

    bad=[y for y,v in summary.items() if v['paginas_indexadas'] and not v['edicoes_identificadas']]
    if bad: raise SystemExit('Anos sem edicoes identificadas: '+', '.join(bad))
    for y in range(1923,1931):
        t=(ROOT/f'ano-{y}.html').read_text(encoding='utf-8')
        if 'doc-card' not in t or 'Edição' not in t or 'Abrir arquivo' not in t: raise SystemExit(f'Falha na pagina {y}')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
