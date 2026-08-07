import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

for year in range(1923,1931):
    path=ROOT/f'ano-{year}.html'
    text=path.read_text(encoding='utf-8')
    counter=[0]

    def card_repl(m):
        counter[0]+=1
        n=counter[0]
        card=m.group(0)
        card=re.sub(r'<h2>Edição nº [^<]+</h2>',f'<h2>Edição nº {n}</h2>',card,count=1)
        card=re.sub(r'data-title="Edição nº [^"]+"',f'data-title="Edição nº {n}"',card,count=1)
        # Deixa o rodapé do cartão limpo, como em 1922; detalhes de reconstrução ficam no relatório técnico.
        card=re.sub(r'(<small>\d+ página\(s\) indexada\(s\))[^<]*(</small>)',r'\1\2',card,count=1)
        return card

    text=re.sub(r'<article class="doc-card">.*?</article>',card_repl,text,flags=re.S)
    path.write_text(text,encoding='utf-8')
    print(year,counter[0])
