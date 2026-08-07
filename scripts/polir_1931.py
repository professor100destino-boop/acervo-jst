from pathlib import Path
p=Path('ano-1931.html')
s=p.read_text(encoding='utf-8')
repl={
'Voltar a pesquisa':'Voltar à pesquisa',
'Ano final do periodico, organizado em edicoes separadas.':'Ano final do periódico, organizado em edições separadas.',
'arquivo(s)/edicao(oes)':'arquivo(s)/edição(ões)',
'paginas indexadas':'páginas indexadas',
'Edicao n. ':'Edição nº ',
'Edicao n.':'Edição nº',
'pagina(s) indexada(s)':'página(s) indexada(s)',
'numero impresso':'número impresso',
'Último numero do jornal':'Último número do jornal',
'material anexado apos o ultimo numero; nao contado como edicao':'material anexado após o último número; não contado como edição',
'Texto OCR indisponivel.':'Texto OCR indisponível.',
' - pagina ':' - página '
}
for a,b in repl.items(): s=s.replace(a,b)
p.write_text(s,encoding='utf-8')