from pathlib import Path
import json
import html

index_path = Path('index.html')
s = index_path.read_text(encoding='utf-8')

# Cards de ano passam a abrir páginas internas do site.
old_year_link = '<a class="btn dark" href="https://drive.google.com/drive/folders/${y.folder}" target="_blank" rel="noopener">Abrir pasta do ano</a>'
new_year_link = '<a class="btn dark" href="ano-${y.year}.html">Abrir página do ano</a>'
if old_year_link in s:
    s = s.replace(old_year_link, new_year_link, 1)

# Leitor principal ganha abas Jornal / Texto OCR.
old_dialog = '<dialog id="dlg"><div class="dh"><strong id="ttl">Leitor</strong><button id="close">Fechar</button></div><iframe id="frame" title="Leitor do jornal"></iframe></dialog>'
new_dialog = '''<dialog id="dlg">
<div class="dh"><strong id="ttl">Leitor</strong><button id="close">Fechar</button></div>
<div class="reader-tabs"><button id="tabPdf" class="reader-tab active" type="button">Jornal</button><button id="tabOcr" class="reader-tab" type="button">Texto OCR</button><button id="copyOcr" class="reader-copy hidden" type="button">Copiar texto</button></div>
<div id="pdfPane" class="reader-pane"><iframe id="frame" title="Leitor do jornal"></iframe></div>
<div id="ocrPane" class="reader-pane hidden"><div id="ocrText" class="ocr-text" tabindex="0"></div></div>
</dialog>'''
if old_dialog in s:
    s = s.replace(old_dialog, new_dialog, 1)

reader_css = '''
.reader-tabs{display:flex;gap:.45rem;align-items:center;padding:.55rem .75rem;background:#efe7d8;border-bottom:1px solid #d8c9b2}.reader-tab,.reader-copy{border:0;border-radius:.45rem;padding:.55rem .8rem;font-weight:800;cursor:pointer;background:#fff;color:var(--vinho)}.reader-tab.active{background:var(--ouro);color:#fff}.reader-copy{margin-left:auto;background:var(--vinho);color:#fff}.reader-pane{height:calc(100% - 111px);overflow:auto;background:#1b1b1b}.reader-pane.hidden{display:none!important}#frame{width:100%;height:100%;border:0}.ocr-text{min-height:100%;padding:1.2rem;background:#faf7ef;color:#272018;line-height:1.65;font:17px/1.65 Georgia,serif;white-space:normal;user-select:text;-webkit-user-select:text;cursor:text}.ocr-page{max-width:850px;margin:0 auto 1rem;background:#fff;border:1px solid #ded3c0;border-radius:.55rem;padding:1rem 1.1rem}.ocr-page h3{margin:.1rem 0 .7rem;color:var(--vinho);font:700 1.15rem Georgia,serif}.ocr-page div{white-space:pre-wrap;user-select:text;-webkit-user-select:text}.ocr-empty{max-width:760px;margin:2rem auto;padding:1.2rem;background:#fff;border-radius:.6rem;color:#554a3c}
'''
if '.reader-tabs{' not in s:
    s = s.replace('@media(max-width:760px)', reader_css + '\n@media(max-width:760px)', 1)

helpers = r'''
function readerPageLabel(p){
  const y=Number(p.year||1922);
  if(y===1922&&p.n)return `Edição nº ${p.n} · página ${p.page}`;
  return `${y} · página ${p.globalPage||p.page||'?'}`;
}
function renderReaderOcr(id){
  const rel=pages.filter(p=>p.pdf===id).sort((a,b)=>Number(a.localPage||a.page||0)-Number(b.localPage||b.page||0));
  const box=$('ocrText');
  if(!rel.length){box.innerHTML='<div class="ocr-empty"><strong>Texto OCR ainda não disponível para este arquivo.</strong></div>';return}
  box.innerHTML=rel.map(p=>`<article class="ocr-page"><h3>${esc(readerPageLabel(p))}</h3><div>${esc(p.text||'')}</div></article>`).join('');
}
function readerTab(which){
  const ocr=which==='ocr';
  $('pdfPane').classList.toggle('hidden',ocr);
  $('ocrPane').classList.toggle('hidden',!ocr);
  $('tabPdf').classList.toggle('active',!ocr);
  $('tabOcr').classList.toggle('active',ocr);
  $('copyOcr').classList.toggle('hidden',!ocr);
  if(ocr)$('ocrText').focus({preventScroll:true});
}
'''
if 'function readerPageLabel(p)' not in s:
    s = s.replace('async function loadIndex(){', helpers + '\nasync function loadIndex(){', 1)

old_click = "document.addEventListener('click',e=>{const b=e.target.closest('.read');if(!b)return;ttl.textContent=b.dataset.title;frame.src=preview(b.dataset.id);dlg.showModal()});"
new_click = "document.addEventListener('click',e=>{const b=e.target.closest('.read');if(!b)return;const id=b.dataset.id;ttl.textContent=b.dataset.title;frame.src=preview(id);renderReaderOcr(id);readerTab('pdf');dlg.showModal()});"
if old_click in s:
    s = s.replace(old_click, new_click, 1)

old_close = "$('close').onclick=()=>{frame.src='about:blank';dlg.close()};"
new_close = "$('close').onclick=()=>{frame.src='about:blank';dlg.close()};\n$('tabPdf').onclick=()=>readerTab('pdf');\n$('tabOcr').onclick=()=>readerTab('ocr');\n$('copyOcr').onclick=async()=>{const text=$('ocrText').innerText;try{await navigator.clipboard.writeText(text);$('copyOcr').textContent='Copiado!';setTimeout(()=>$('copyOcr').textContent='Copiar texto',1400)}catch(e){const r=document.createRange();r.selectNodeContents($('ocrText'));const sel=getSelection();sel.removeAllRanges();sel.addRange(r)}};"
if old_close in s:
    s = s.replace(old_close, new_close, 1)

index_path.write_text(s, encoding='utf-8')

# Montar páginas próprias para cada ano.
manifest = json.loads(Path('fontes-pdf.json').read_text(encoding='utf-8'))
all_pages = json.loads(Path('search-index-all.json').read_text(encoding='utf-8'))
by_year = {int(x['year']): x for x in manifest}

groups_1922 = {}
for p in all_pages:
    if int(p.get('year', 1922)) != 1922:
        continue
    key = p.get('pdf')
    if not key:
        continue
    g = groups_1922.setdefault(key, {
        'id': key,
        'n': p.get('n'),
        'date': p.get('date') or p.get('iso') or '',
        'original': p.get('original'),
        'pages': 0,
        'title': ''
    })
    g['pages'] += 1
sources_1922 = sorted(groups_1922.values(), key=lambda x: int(x.get('n') or 999))
for g in sources_1922:
    g['title'] = f"Edição nº {g.get('n', '?')}"

def annual_sources(year):
    if year == 1922:
        return sources_1922
    item = by_year[year]
    out = []
    year_pages = [p for p in all_pages if int(p.get('year', 0)) == year]
    for src in item['sources']:
        rel = [p for p in year_pages if p.get('pdf') == src['id']]
        count = len(rel)
        end = int(src['start']) + count - 1 if count else int(src['start'])
        out.append({
            'id': src['id'],
            'title': f"Parte iniciada na página {src['start']}",
            'subtitle': f"Páginas {src['start']}–{end} do volume" if count else f"A partir da página {src['start']}",
            'pages': count,
            'original': None
        })
    return out

def q(value):
    return html.escape(str(value or ''), quote=True)

def year_page(year):
    sources = annual_sources(year)
    cards = []
    for src in sources:
        subtitle = q(src.get('date')) if year == 1922 else q(src.get('subtitle'))
        original = ''
        if src.get('original'):
            original = f'<a class="btn secondary" href="https://drive.google.com/file/d/{q(src.get("original"))}/view" target="_blank" rel="noopener">Original</a>'
        cards.append(f'''<article class="doc-card">
<div class="doc-head"><span class="badge">PDF</span><h2>{q(src['title'])}</h2><p>{subtitle}</p><small>{int(src.get('pages') or 0)} página(s) indexada(s)</small></div>
<div class="doc-actions"><button class="btn read" data-id="{q(src['id'])}" data-title="{q(src['title'])}">Ler</button><a class="btn secondary" href="https://drive.google.com/file/d/{q(src['id'])}/view" target="_blank" rel="noopener">Abrir arquivo</a>{original}</div>
</article>''')
    total = sum(int(x.get('pages') or 0) for x in sources)
    coverage = 'Ano completo em edições separadas.' if year == 1922 else ('Janeiro a maio — parte disponível em PDF.' if year == 1927 else 'Materiais disponíveis em PDF para o ano.')
    return f'''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>JST {year} — Acervo Digital</title>
<style>
:root{{--vinho:#591f22;--vinho2:#2d1719;--ouro:#9b7838;--papel:#f3ead6;--tinta:#2c241b;--fundo:#eee7da}}*{{box-sizing:border-box}}body{{margin:0;background:var(--fundo);color:var(--tinta);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}}a{{color:inherit}}.top{{background:linear-gradient(125deg,var(--vinho2),#68272b);color:#fff;padding:2rem 1rem}}.wrap{{max-width:1050px;margin:auto}}.back{{display:inline-block;color:#fff;text-decoration:none;border:1px solid #ffffff88;border-radius:.5rem;padding:.55rem .8rem;margin-bottom:1.3rem}}h1{{font:700 clamp(2.7rem,9vw,5.8rem)/.95 Georgia,serif;margin:.2rem 0}}.lead{{max-width:720px}}.stats{{display:flex;gap:1rem;flex-wrap:wrap;margin-top:1rem}}.stat{{background:#ffffff15;border:1px solid #ffffff33;border-radius:.6rem;padding:.65rem .9rem}}main{{max-width:1050px;margin:auto;padding:1.5rem 1rem 4rem}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:1rem}}.doc-card{{background:#fff;border-radius:.8rem;overflow:hidden;box-shadow:0 8px 24px #0001;border:1px solid #e7ddcd}}.doc-head{{padding:1.2rem;background:#fff}}.doc-head h2{{font:700 1.55rem Georgia,serif;margin:.45rem 0}}.doc-head p{{margin:.25rem 0;color:#665c50}}.doc-head small{{color:#766b5e}}.badge{{display:inline-block;background:#e5e3ef;color:#3e3861;padding:.2rem .55rem;border-radius:99px;font-weight:800}}.doc-actions{{display:flex;gap:.55rem;flex-wrap:wrap;padding:0 1.2rem 1.2rem}}.btn{{border:0;border-radius:.5rem;padding:.72rem 1rem;background:var(--ouro);color:#fff;text-decoration:none;font-weight:800;cursor:pointer}}.btn.secondary{{background:var(--vinho)}}dialog{{width:min(96vw,1000px);height:88vh;border:0;border-radius:.7rem;padding:0}}dialog::backdrop{{background:#000b}}.dh{{display:flex;justify-content:space-between;align-items:center;padding:.8rem;background:#2b1b19;color:#fff}}.dh button{{border:0;border-radius:.4rem;padding:.55rem .75rem;cursor:pointer}}.reader-tabs{{display:flex;gap:.45rem;align-items:center;padding:.55rem .75rem;background:#efe7d8;border-bottom:1px solid #d8c9b2}}.reader-tab,.reader-copy{{border:0;border-radius:.45rem;padding:.55rem .8rem;font-weight:800;cursor:pointer;background:#fff;color:var(--vinho)}}.reader-tab.active{{background:var(--ouro);color:#fff}}.reader-copy{{margin-left:auto;background:var(--vinho);color:#fff}}.reader-pane{{height:calc(100% - 111px);overflow:auto;background:#1b1b1b}}.hidden{{display:none!important}}#frame{{width:100%;height:100%;border:0}}.ocr-text{{min-height:100%;padding:1.1rem;background:#faf7ef;color:#272018;font:17px/1.65 Georgia,serif;user-select:text;-webkit-user-select:text;cursor:text}}.ocr-page{{max-width:850px;margin:0 auto 1rem;background:#fff;border:1px solid #ded3c0;border-radius:.55rem;padding:1rem 1.1rem}}.ocr-page h3{{margin:.1rem 0 .7rem;color:var(--vinho);font:700 1.15rem Georgia,serif}}.ocr-page div{{white-space:pre-wrap;user-select:text;-webkit-user-select:text}}.ocr-empty{{max-width:760px;margin:2rem auto;padding:1.2rem;background:#fff;border-radius:.6rem;color:#554a3c}}@media(max-width:620px){{.doc-actions .btn{{flex:1;text-align:center}}.reader-copy{{font-size:.82rem;padding:.5rem .6rem}}}}
</style></head><body>
<header class="top"><div class="wrap"><a class="back" href="index.html">← Voltar à pesquisa</a><div>ACERVO DIGITAL JST</div><h1>{year}</h1><p class="lead">{q(coverage)}</p><div class="stats"><div class="stat"><strong>{len(sources)}</strong> arquivo(s)/edição(ões)</div><div class="stat"><strong>{total}</strong> páginas indexadas</div></div></div></header>
<main><div class="grid">{''.join(cards)}</div></main>
<dialog id="dlg"><div class="dh"><strong id="ttl">Leitor</strong><button id="close">Fechar</button></div><div class="reader-tabs"><button id="tabPdf" class="reader-tab active" type="button">Jornal</button><button id="tabOcr" class="reader-tab" type="button">Texto OCR</button><button id="copyOcr" class="reader-copy hidden" type="button">Copiar texto</button></div><div id="pdfPane" class="reader-pane"><iframe id="frame" title="Leitor do jornal"></iframe></div><div id="ocrPane" class="reader-pane hidden"><div id="ocrText" class="ocr-text" tabindex="0"></div></div></dialog>
<script>
let pages=[];const $=id=>document.getElementById(id),dlg=$('dlg'),frame=$('frame'),ttl=$('ttl');const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));const preview=id=>`https://drive.google.com/file/d/${{id}}/preview`;
function label(p){{if(Number(p.year||1922)===1922&&p.n)return `Edição nº ${{p.n}} · página ${{p.page}}`;return `{year} · página ${{p.globalPage||p.page||'?'}}`;}}
function renderOcr(id){{const rel=pages.filter(p=>p.pdf===id).sort((a,b)=>Number(a.localPage||a.page||0)-Number(b.localPage||b.page||0));const box=$('ocrText');if(!rel.length){{box.innerHTML='<div class="ocr-empty"><strong>Texto OCR ainda não disponível para este arquivo.</strong></div>';return}}box.innerHTML=rel.map(p=>`<article class="ocr-page"><h3>${{esc(label(p))}}</h3><div>${{esc(p.text||'')}}</div></article>`).join('')}}
function tab(which){{const ocr=which==='ocr';$('pdfPane').classList.toggle('hidden',ocr);$('ocrPane').classList.toggle('hidden',!ocr);$('tabPdf').classList.toggle('active',!ocr);$('tabOcr').classList.toggle('active',ocr);$('copyOcr').classList.toggle('hidden',!ocr);if(ocr)$('ocrText').focus({{preventScroll:true}})}}
fetch('search-index-all.json',{{cache:'no-store'}}).then(r=>r.json()).then(x=>pages=x.map(p=>({{...p,year:Number(p.year||1922)}}))).catch(()=>{{}});
document.addEventListener('click',e=>{{const b=e.target.closest('.read');if(!b)return;const id=b.dataset.id;ttl.textContent=b.dataset.title;frame.src=preview(id);renderOcr(id);tab('pdf');dlg.showModal()}});$('close').onclick=()=>{{frame.src='about:blank';dlg.close()}};$('tabPdf').onclick=()=>tab('pdf');$('tabOcr').onclick=()=>tab('ocr');$('copyOcr').onclick=async()=>{{const text=$('ocrText').innerText;try{{await navigator.clipboard.writeText(text);$('copyOcr').textContent='Copiado!';setTimeout(()=>$('copyOcr').textContent='Copiar texto',1400)}}catch(e){{const r=document.createRange();r.selectNodeContents($('ocrText'));const sel=getSelection();sel.removeAllRanges();sel.addRange(r)}}}};
</script></body></html>'''

for year in range(1922, 1928):
    Path(f'ano-{year}.html').write_text(year_page(year), encoding='utf-8')
