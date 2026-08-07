import fitz, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=Path('/tmp/jst/1931.pdf')
SOURCE_ID='1EJ3TynEsnPA66rIS9dxOQ8vA-nMQSyUY'
FOLDER_ID='12zaAcEEHRXThKXNJdD3l0z7FrvqT-oF_'
SUPPLEMENT_ID='1K7OJsbp3uTIMXpKjv0PVJXtzgSbA2Ttd'
MONTHS={1:'janeiro',2:'fevereiro',3:'março',4:'abril',5:'maio',6:'junho',7:'julho',8:'agosto',9:'setembro',10:'outubro',11:'novembro',12:'dezembro'}
ED=[
 ('1931-01-03',382,1,4,'1FxewaNVjywdj40vt2ILJO-6Ui7U1CKtK'),
 ('1931-01-10',383,5,8,'1LD-zeckVTuzUcL9fluzLMgzUDHNEeb04'),
 ('1931-02-14',388,9,12,'1W1XF5mFe2SLC7AJ-HzU-M5Nrnqza9DxA'),
 ('1931-02-21',389,13,16,'111QWM6Fh_xK_RPuKUljrLyChzkJ7t90d'),
 ('1931-02-28',390,17,20,'1hZJkXS5fyR-V8cMWarsdZ09ge8SPqVM_'),
 ('1931-03-21',393,21,24,'1hZeA3wsWaxygJjte_kPb4DEI5_ECC_9t'),
 ('1931-05-02',398,25,28,'18hUfuqLeM8qP0qJyUj96mrPyFGS02WFL'),
 ('1931-05-09',399,29,32,'14HF94k-mTbfb7EC_zsFFkAl7ym54VjLP'),
 ('1931-05-16',400,33,36,'1G1xbDthhCMJ4JltXKdPaC4CNOAa9_De3'),
 ('1931-05-23',401,37,40,'1MqW3dvYpXPziQI5i9cJpMfNEp0jC9tnI'),
 ('1931-06-01',402,41,44,'1qPilC_ONNJHDioQAIx86zV40KBKf6bfE'),
]

def date_label(iso):
    y,m,d=map(int,iso.split('-'))
    return f'{d} de {MONTHS[m]} de {y}'

def clean(t):
    return re.sub(r'\s+',' ',t.replace('\x00',' ')).strip()

doc=fitz.open(SRC)
assert len(doc)==46, f'Esperadas 46 paginas, encontrado {len(doc)}'
index=[]
for seq,(iso,issue,a,b,pdfid) in enumerate(ED,1):
    label=date_label(iso)
    for gp in range(a,b+1):
        text=clean(doc[gp-1].get_text('text'))
        if len(text)<100: raise RuntimeError(f'OCR insuficiente na pagina {gp}')
        index.append({'year':1931,'edition':seq,'issue':issue,'date':label,'iso':iso,'page':gp-a+1,'globalPage':gp,'localPage':gp-a+1,'sourceStart':a,'pdf':pdfid,'original':SOURCE_ID,'title':f'JST 1931 - {label}','text':text})
for gp in (45,46):
    text=clean(doc[gp-1].get_text('text'))
    if len(text)<100: raise RuntimeError(f'OCR insuficiente na pagina {gp}')
    index.append({'year':1931,'supplement':True,'date':'Sem data impressa','iso':'','page':gp-44,'globalPage':gp,'localPage':gp-44,'sourceStart':45,'pdf':SUPPLEMENT_ID,'original':SOURCE_ID,'title':'JST 1931 - Suplemento final','text':text})
(ROOT/'search-index-1931.json').write_text(json.dumps(index,ensure_ascii=False,separators=(',',':')),encoding='utf-8')

css='''
:root{--vinho:#591f22;--vinho2:#2d1719;--ouro:#9b7838;--papel:#f3ead6;--tinta:#2c241b;--fundo:#eee7da}*{box-sizing:border-box}body{margin:0;background:var(--fundo);color:var(--tinta);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}a{color:inherit}.top{background:linear-gradient(125deg,var(--vinho2),#68272b);color:#fff;padding:2rem 1rem}.wrap{max-width:1050px;margin:auto}.back{display:inline-block;color:#fff;text-decoration:none;border:1px solid #ffffff88;border-radius:.5rem;padding:.55rem .8rem;margin-bottom:1.3rem}h1{font:700 clamp(2.7rem,9vw,5.8rem)/.95 Georgia,serif;margin:.2rem 0}.lead{max-width:720px}.stats{display:flex;gap:1rem;flex-wrap:wrap;margin-top:1rem}.stat{background:#ffffff15;border:1px solid #ffffff33;border-radius:.6rem;padding:.65rem .9rem}main{max-width:1050px;margin:auto;padding:1.5rem 1rem 4rem}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:1rem}.doc-card{background:#fff;border-radius:.8rem;overflow:hidden;box-shadow:0 8px 24px #0001;border:1px solid #e7ddcd}.doc-head{padding:1.2rem;background:#fff}.doc-head h2{font:700 1.55rem Georgia,serif;margin:.45rem 0}.doc-head p{margin:.25rem 0;color:#665c50}.doc-head small{color:#766b5e}.badge{display:inline-block;background:#e5e3ef;color:#3e3861;padding:.2rem .55rem;border-radius:99px;font-weight:800}.doc-actions{display:flex;gap:.55rem;flex-wrap:wrap;padding:0 1.2rem 1.2rem}.btn{border:0;border-radius:.5rem;padding:.72rem 1rem;background:var(--ouro);color:#fff;text-decoration:none;font-weight:800;cursor:pointer}.btn.secondary{background:var(--vinho)}.supplement{margin-top:1.25rem;border-top:2px solid #cbb995;padding-top:1.25rem}dialog{width:min(96vw,1000px);height:88vh;border:0;border-radius:.7rem;padding:0}dialog::backdrop{background:#000b}.dh{display:flex;justify-content:space-between;align-items:center;padding:.8rem;background:#2b1b19;color:#fff}.dh button{border:0;border-radius:.4rem;padding:.55rem .75rem;cursor:pointer}.reader-tabs{display:flex;gap:.45rem;align-items:center;padding:.55rem .75rem;background:#efe7d8;border-bottom:1px solid #d8c9b2}.reader-tab,.reader-copy{border:0;border-radius:.45rem;padding:.55rem .8rem;font-weight:800;cursor:pointer;background:#fff;color:var(--vinho)}.reader-tab.active{background:var(--ouro);color:#fff}.reader-copy{margin-left:auto;background:var(--vinho);color:#fff}.reader-pane{height:calc(100% - 111px);overflow:auto;background:#1b1b1b}.hidden{display:none!important}#frame{width:100%;height:100%;border:0}.ocr-text{min-height:100%;padding:1.1rem;background:#faf7ef;color:#272018;font:17px/1.65 Georgia,serif}.ocr-page{max-width:850px;margin:0 auto 1rem;background:#fff;border:1px solid #ded3c0;border-radius:.55rem;padding:1rem 1.1rem}.ocr-page h3{margin:.1rem 0 .7rem;color:var(--vinho);font:700 1.15rem Georgia,serif}.ocr-page div{white-space:pre-wrap}@media(max-width:620px){.doc-actions .btn{flex:1;text-align:center}}
'''
cards=[]
for seq,(iso,issue,a,b,pdfid) in enumerate(ED,1):
    label=date_label(iso); extra=' - Último numero do jornal' if issue==402 else ''
    cards.append(f'''<article class="doc-card"><div class="doc-head"><span class="badge">PDF</span><h2>Edicao n. {seq}</h2><p>{label}</p><small>4 pagina(s) indexada(s) - numero impresso {issue}{extra}</small></div><div class="doc-actions"><button class="btn read" data-id="{pdfid}" data-title="Edicao n. {seq} - {label}">Ler</button><a class="btn secondary" href="https://drive.google.com/file/d/{pdfid}/view" target="_blank" rel="noopener">Abrir arquivo</a><a class="btn secondary" href="https://drive.google.com/file/d/{SOURCE_ID}/view" target="_blank" rel="noopener">Original</a></div></article>''')
supp=f'''<section class="supplement"><h2>Material complementar</h2><article class="doc-card"><div class="doc-head"><span class="badge">PDF</span><h2>Suplemento final</h2><p>Sem data impressa</p><small>2 pagina(s) indexada(s) - material anexado apos o ultimo numero; nao contado como edicao</small></div><div class="doc-actions"><button class="btn read" data-id="{SUPPLEMENT_ID}" data-title="Suplemento final - sem data impressa">Ler</button><a class="btn secondary" href="https://drive.google.com/file/d/{SUPPLEMENT_ID}/view" target="_blank" rel="noopener">Abrir arquivo</a><a class="btn secondary" href="https://drive.google.com/file/d/{SOURCE_ID}/view" target="_blank" rel="noopener">Original</a></div></article></section>'''
page=f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>JST 1931 - Acervo Digital</title><style>{css}</style></head><body><header class="top"><div class="wrap"><a class="back" href="index.html">← Voltar a pesquisa</a><div>ACERVO DIGITAL JST</div><h1>1931</h1><p class="lead">Ano final do periodico, organizado em edicoes separadas.</p><div class="stats"><div class="stat"><strong>11</strong> arquivo(s)/edicao(oes)</div><div class="stat"><strong>46</strong> paginas indexadas</div></div></div></header><main><div class="grid">{''.join(cards)}</div>{supp}</main><dialog id="dlg"><div class="dh"><strong id="ttl">Leitor</strong><button id="close">Fechar</button></div><div class="reader-tabs"><button id="tabPdf" class="reader-tab active" type="button">Jornal</button><button id="tabOcr" class="reader-tab" type="button">Texto OCR</button><button id="copyOcr" class="reader-copy hidden" type="button">Copiar texto</button></div><div id="pdfPane" class="reader-pane"><iframe id="frame" title="Leitor do jornal"></iframe></div><div id="ocrPane" class="reader-pane hidden"><div id="ocrText" class="ocr-text" tabindex="0"></div></div></dialog><script>
let pages=[];const $=id=>document.getElementById(id),dlg=$('dlg'),frame=$('frame'),ttl=$('ttl');const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));const preview=id=>`https://drive.google.com/file/d/${{id}}/preview`;
function renderOcr(id){{const rel=pages.filter(p=>p.pdf===id).sort((a,b)=>Number(a.localPage||a.page||0)-Number(b.localPage||b.page||0));const box=$('ocrText');box.innerHTML=rel.length?rel.map(p=>`<article class="ocr-page"><h3>${{esc(p.title||'1931')}} - pagina ${{p.localPage||p.page}}</h3><div>${{esc(p.text||'')}}</div></article>`).join(''):'<div class="ocr-page">Texto OCR indisponivel.</div>'}}
function tab(w){{const o=w==='ocr';$('pdfPane').classList.toggle('hidden',o);$('ocrPane').classList.toggle('hidden',!o);$('tabPdf').classList.toggle('active',!o);$('tabOcr').classList.toggle('active',o);$('copyOcr').classList.toggle('hidden',!o)}}
fetch('search-index-1931.json',{{cache:'no-store'}}).then(r=>r.json()).then(x=>pages=x).catch(()=>{{}});document.addEventListener('click',e=>{{const b=e.target.closest('.read');if(!b)return;ttl.textContent=b.dataset.title;frame.src=preview(b.dataset.id);renderOcr(b.dataset.id);tab('pdf');dlg.showModal()}});$('close').onclick=()=>{{frame.src='about:blank';dlg.close()}};$('tabPdf').onclick=()=>tab('pdf');$('tabOcr').onclick=()=>tab('ocr');$('copyOcr').onclick=async()=>{{try{{await navigator.clipboard.writeText($('ocrText').innerText)}}catch(e){{}}}};
</script></body></html>'''
(ROOT/'ano-1931.html').write_text(page,encoding='utf-8')

# Atualiza pagina inicial
p=ROOT/'index.html'; s=p.read_text(encoding='utf-8')
s=s.replace('entre 1922 e 1930','entre 1922 e 1931').replace('Pesquisa 1922–1930','Pesquisa 1922–1931')
s=s.replace('Acervo Digital do Jornal Santuário da Trindade (1920–1970)','Acervo Digital do Jornal Santuário da Trindade - periódico goiano, 1922–1931')
s=s.replace('<strong>9</strong>anos em PDF','<strong>10</strong>anos em PDF')
s=s.replace('<strong>1922–1930</strong>período disponível','<strong>1922–1931</strong>período disponível')
s=s.replace('<option>1930</option>','<option>1930</option><option>1931</option>')
if 'year:1931' not in s:
    s=s.replace("{year:1930,label:'Ano organizado em edições separadas',files:32,folder:'1ZqEuO-Gckq-694HzA3VpBBbEa40nqPO-'}];", "{year:1930,label:'Ano organizado em edições separadas',files:32,folder:'1ZqEuO-Gckq-694HzA3VpBBbEa40nqPO-'},\n{year:1931,label:'Ano final - edições separadas',files:11,folder:'12zaAcEEHRXThKXNJdD3l0z7FrvqT-oF_'}];")
s=s.replace("'search-index-1929.json','search-index-1930.json'", "'search-index-1929.json','search-index-1930.json','search-index-1931.json'")
s=s.replace('Entram na busca os materiais disponíveis em PDF de 1922 a 1930. As edições de 1929 e 1930 foram separadas pelas datas impressas nos jornais e incorporadas com OCR pesquisável. Lacunas de publicação presentes nos arquivos-fonte são preservadas, sem criação de edições inexistentes.', 'O Jornal Santuário da Trindade circulou em Goiás entre 1922 e 1931. Esta coleção digital disponibiliza o período 1922-1931, organizado por ano e edição, com OCR pesquisável. O último número localizado é o n. 402, de 1 de junho de 1931, que anuncia o encerramento do periódico. Lacunas presentes nos arquivos-fonte são preservadas, sem criação de edições inexistentes.')
# cobre no site a legenda antiga gravada na imagem do banner, sem alterar o arquivo historico da arte
if '.banner-period-fix' not in s:
    s=s.replace('</style>', '.banner-wrap{position:relative;line-height:0}.banner-period-fix{position:absolute;left:0;right:0;bottom:0;height:20%;display:flex;align-items:center;justify-content:center;text-align:center;padding:.5rem 1rem;background:linear-gradient(180deg,#ead9b5 0%,#ead9b5 72%,#e7d3aa 100%);color:#18130d;font:700 clamp(.75rem,2vw,1.55rem)/1.2 Georgia,serif;letter-spacing:.01em;border-top:1px solid #8c7048}.banner-period-fix span{line-height:1.2}@media(max-width:760px){.banner-period-fix{font-size:clamp(.62rem,2.5vw,1rem);height:21%}}\n</style>')
    s=s.replace('<header class="hero hero-image">\n  <img class="hero-banner" src="assets/banner_acervo_jst.png" alt="Santuário da Trindade — Órgam do Santuário da Trindade — Acervo Digital do Jornal Santuário da Trindade - periódico goiano, 1922–1931">\n</header>', '<header class="hero hero-image">\n  <div class="banner-wrap"><img class="hero-banner" src="assets/banner_acervo_jst.png" alt="Santuário da Trindade — Órgam do Santuário da Trindade"><div class="banner-period-fix"><span>ACERVO DIGITAL DO JORNAL SANTUÁRIO DA TRINDADE (1922–1931)</span></div></div>\n</header>')
p.write_text(s,encoding='utf-8')

# README atualizado
readme='''# Acervo Digital JST - Jornal Santuário de Trindade\n\nSite público de consulta ao **Jornal Santuário de Trindade**, periódico católico que circulou em Goiás entre **1922 e 1931**. A coleção digital disponibilizada neste projeto cobre esse período, com organização por edição e pesquisa no texto reconhecido por OCR.\n\n## Site\n\nhttps://professor100destino-boop.github.io/acervo-jst/\n\n## Cobertura da coleção\n\n- **1922 a 1930:** anos organizados em páginas anuais e edições pesquisáveis.\n- **1931:** 11 edições localizadas entre 3 de janeiro e 1 de junho, mais um suplemento final de 2 páginas sem data impressa.\n- O **n. 402, de 1 de junho de 1931**, anuncia no próprio jornal que se trata do último número e que o periódico deixaria de aparecer.\n- Lacunas existentes nos arquivos-fonte são mantidas; não são criadas edições inexistentes.\n\n## Busca\n\nA busca consulta um índice OCR página por página. Grafia antiga, manchas, colunas e letras apagadas podem produzir erros de reconhecimento. Para citações acadêmicas, confira sempre a imagem do jornal.\n\n## Preservação\n\nAs imagens originais não são clareadas, recortadas, retocadas ou alteradas. Quando o PDF já possui camada OCR, ela é preservada e validada; o índice textual serve apenas para localização e pesquisa.\n'''
(ROOT/'README.md').write_text(readme,encoding='utf-8')

citar='''MODELO SUGERIDO DE CITAÇÃO\n\nJORNAL SANTUÁRIO DE TRINDADE. Campinas, GO, ano [ano do jornal], n. [número impresso], [data], p. [página]. Acervo Digital JST - coleção 1922-1931. Disponível em: https://professor100destino-boop.github.io/acervo-jst/. Acesso em: [data de acesso].\n\nExemplo:\nJORNAL SANTUÁRIO DE TRINDADE. Campinas, GO, ano I, n. 1, 1 jul. 1922, p. 1. Acervo Digital JST - coleção 1922-1931. Disponível em: https://professor100destino-boop.github.io/acervo-jst/. Acesso em: [data de acesso].\n\nNota histórica: o periódico circulou em Goiás entre 1922 e 1931. O n. 402, de 1 jun. 1931, anuncia o encerramento do jornal.\n'''
(ROOT/'documentacao'/'COMO_CITAR.txt').write_text(citar,encoding='utf-8')
print('1931 integrado: 11 edicoes, 46 paginas indexadas (incluindo suplemento final).')