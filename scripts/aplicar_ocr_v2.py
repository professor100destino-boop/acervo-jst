from pathlib import Path

INDEX = Path('index.html')
text = INDEX.read_text(encoding='utf-8')
needle = "pages=base.filter(p=>Number(p.year||1922)!==1927).concat(...extras);"
patch = """pages=base.filter(p=>Number(p.year||1922)!==1927).concat(...extras);
    // Camadas OCR V2: quando um ano já foi reprocessado, substitui somente
    // o texto OCR daquele ano, preservando metadados e PDFs publicados.
    for(const y of [1922,1923,1924,1925,1926,1927,1928,1929,1930,1931]){
      try{
        const vr=await fetch(`search-index-v2-${y}.json?v=${Date.now()}`,{cache:'no-store'});
        if(vr.ok){
          const v=(await vr.json()).map(p=>({...p,year:Number(p.year||y)}));
          pages=pages.filter(p=>Number(p.year||1922)!==y).concat(v);
        }
      }catch(e){}
    }"""
if 'search-index-v2-${y}.json' not in text:
    if needle not in text:
        raise SystemExit('Ponto de insercao nao encontrado em index.html')
    text = text.replace(needle, patch, 1)
    INDEX.write_text(text, encoding='utf-8')

p = Path('ano-1922.html')
s = p.read_text(encoding='utf-8')
old = "fetch('search-index-all.json',{cache:'no-store'}).then(r=>r.json()).then(x=>pages=x.map(p=>({...p,year:Number(p.year||1922)}))).catch(()=>{});"
new = "fetch('search-index-v2-1922.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error('v2');return r.json()}).then(x=>pages=x.map(p=>({...p,year:1922}))).catch(()=>fetch('search-index-all.json',{cache:'no-store'}).then(r=>r.json()).then(x=>pages=x.map(p=>({...p,year:Number(p.year||1922)}))).catch(()=>{}));"
if 'search-index-v2-1922.json' not in s:
    if old not in s:
        raise SystemExit('Ponto de insercao nao encontrado em ano-1922.html')
    s = s.replace(old, new, 1)
    p.write_text(s, encoding='utf-8')

print('OCR V2 integrado ao site.')
