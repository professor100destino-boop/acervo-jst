from pathlib import Path
import json
import re
import subprocess
import sys

import fitz
import gdown

ROOT = Path(__file__).resolve().parents[1]
TMP = Path('/tmp/jst_1927_1928')
TMP.mkdir(parents=True, exist_ok=True)

SOURCES = [
    {
        'year': 1927,
        'drive_id': '1rTFTBK7OQg9gSXv16aCkJkKMR0e9Nz1M',
        'path': TMP / '1927.pdf',
        'start': 1,
        'outfile': ROOT / 'search-index-1927.json',
        'title': 'JST 1927 - ano completo',
        'expected_pages': 107,
    },
    {
        'year': 1928,
        'drive_id': '18P2FN0W5-QopXNabTdJJM0M5ioc7rwBU',
        'path': TMP / '1928-p1.pdf',
        'start': 1,
        'outfile': ROOT / 'search-index-1928-p1.json',
        'title': 'JST 1928 - páginas 1-69',
        'expected_pages': 69,
    },
    {
        'year': 1928,
        'drive_id': '1F72p2WT4nzzfSs8kjD9eaP4VHnOzmqoE',
        'path': TMP / '1928-p70.pdf',
        'start': 70,
        'outfile': ROOT / 'search-index-1928-p70.json',
        'title': 'JST 1928 - páginas 70-152',
        'expected_pages': 83,
    },
    {
        'year': 1928,
        'drive_id': '1fiK7v18EJMDkTZWtuYBLsB-3PErl-Eqh',
        'path': TMP / '1928-p153.pdf',
        'start': 153,
        'outfile': ROOT / 'search-index-1928-p153.json',
        'title': 'JST 1928 - páginas 153-194',
        'expected_pages': 42,
    },
]


def clean_text(text: str) -> str:
    text = text.replace('\x00', ' ')
    text = re.sub(r'[\t\r\f\v]+', ' ', text)
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def download_sources():
    for src in SOURCES:
        print(f"Baixando {src['year']} - página inicial {src['start']}...")
        result = gdown.download(id=src['drive_id'], output=str(src['path']), quiet=False)
        if not result or not src['path'].exists():
            raise RuntimeError(f"Falha ao baixar {src['drive_id']}")


def build_indexes():
    totals = {}
    for src in SOURCES:
        doc = fitz.open(src['path'])
        if doc.page_count != src['expected_pages']:
            raise RuntimeError(
                f"{src['path'].name}: esperado {src['expected_pages']} páginas, encontrado {doc.page_count}"
            )
        rows = []
        for i, page in enumerate(doc):
            global_page = src['start'] + i
            rows.append({
                'year': src['year'],
                'globalPage': global_page,
                'page': global_page,
                'localPage': i + 1,
                'sourceStart': src['start'],
                'pdf': src['drive_id'],
                'title': src['title'],
                'text': clean_text(page.get_text('text')),
            })
        src['outfile'].write_text(
            json.dumps(rows, ensure_ascii=False, separators=(',', ':')),
            encoding='utf-8',
        )
        totals[src['year']] = totals.get(src['year'], 0) + len(rows)
        print(f"{src['outfile'].name}: {len(rows)} páginas")

    if totals.get(1927) != 107:
        raise RuntimeError(f"Total de 1927 incorreto: {totals.get(1927)}")
    if totals.get(1928) != 194:
        raise RuntimeError(f"Total de 1928 incorreto: {totals.get(1928)}")


def patch_site():
    path = ROOT / 'index.html'
    s = path.read_text(encoding='utf-8')

    replacements = [
        ('com busca no texto reconhecido por OCR entre 1922 e 1927.',
         'com busca no texto reconhecido por OCR entre 1922 e 1928.'),
        ('<title>Acervo Digital JST — Pesquisa 1922–1927</title>',
         '<title>Acervo Digital JST — Pesquisa 1922–1928</title>'),
        ('<div><strong>6</strong>anos em PDF</div>',
         '<div><strong>7</strong>anos em PDF</div>'),
        ('<div><strong>1922–1927</strong>período disponível</div>',
         '<div><strong>1922–1928</strong>período disponível</div>'),
    ]
    for old, new in replacements:
        if old in s:
            s = s.replace(old, new, 1)

    if '<option>1928</option>' not in s:
        s = s.replace('<option>1927</option>', '<option>1927</option><option>1928</option>', 1)

    old_year = "{year:1927,label:'Janeiro a maio em quatro partes PDF',files:4,folder:'1yyAZHT_y_VqjNWxMoRh5Qr5J0VZJrv3m'}];"
    new_year = "{year:1927,label:'Ano completo em PDF',files:1,folder:'1yyAZHT_y_VqjNWxMoRh5Qr5J0VZJrv3m'},\n{year:1928,label:'Ano completo em três partes PDF',files:3,folder:'1yNHV6vMW9c14rmuBa1xD1pKK9UnzGBdW'}];"
    if old_year in s:
        s = s.replace(old_year, new_year, 1)
    elif "{year:1928,label:'Ano completo em três partes PDF'" not in s:
        raise RuntimeError('Não foi possível atualizar o cadastro dos anos')

    old_load = "    pages=await r.json();\n    pages=pages.map(p=>({...p,year:Number(p.year||1922)}));"
    new_load = """    let base=await r.json();
    base=base.map(p=>({...p,year:Number(p.year||1922)}));
    const extraFiles=['search-index-1927.json','search-index-1928-p1.json','search-index-1928-p70.json','search-index-1928-p153.json'];
    const extras=[];
    for(const f of extraFiles){
      const x=await fetch(`${f}?v=${Date.now()}`,{cache:'no-store'});
      if(!x.ok)throw new Error(`índice adicional indisponível: ${f}`);
      extras.push(await x.json());
    }
    pages=base.filter(p=>Number(p.year||1922)!==1927).concat(...extras);
    pages=pages.map(p=>({...p,year:Number(p.year||1922)}));"""
    if old_load in s:
        s = s.replace(old_load, new_load, 1)
    elif "const extraFiles=['search-index-1927.json'" not in s:
        raise RuntimeError('Não foi possível atualizar o carregamento dos índices')

    old_coverage = ('Entram na busca os materiais que já estavam em PDF: 1922, 1923, 1924, 1925, 1926 e a primeira parte de 1927. '
                    'A documentação de junho de 1927 até 1931 está em JPG e ainda não integra este índice.')
    new_coverage = ('Entram na busca os materiais disponíveis em PDF de 1922 a 1928. O ano de 1927 agora está completo, '
                    'e 1928 foi incorporado integralmente em três partes. Os anos posteriores serão acrescentados conforme '
                    'forem convertidos para PDF e indexados.')
    if old_coverage in s:
        s = s.replace(old_coverage, new_coverage, 1)

    path.write_text(s, encoding='utf-8')


def main():
    download_sources()
    build_indexes()
    patch_site()
    print('Integração preparada com sucesso.')


if __name__ == '__main__':
    main()
