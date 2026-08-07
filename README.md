# Acervo Digital JST — Jornal Santuário de Trindade

Site público de consulta ao **Jornal Santuário de Trindade**, com preservação das cópias digitalizadas e pesquisa no texto reconhecido por OCR.

## Site

https://professor100destino-boop.github.io/acervo-jst/

## Cobertura atual

- **1922:** 14 edições separadas, com PDF pesquisável e acesso ao original.
- **1923:** 5 partes em PDF.
- **1924:** 11 partes em PDF.
- **1925:** 14 partes em PDF.
- **1926:** 8 partes em PDF.
- **1927:** janeiro a maio em 4 partes PDF.
- **Junho de 1927 a 1931:** arquivos em JPG, ainda fora do índice textual desta etapa.

## Busca

O site consulta um índice OCR organizado por página. Os resultados informam:

- ano;
- edição, quando identificada;
- página do volume;
- página dentro do arquivo PDF;
- trecho reconhecido pelo OCR;
- acesso direto ao PDF original no Google Drive.

A grafia antiga, manchas, colunas e letras apagadas podem produzir erros. Para citações acadêmicas, o pesquisador deve sempre conferir a imagem original.

## Arquivos principais

- `index.html` — interface pública de consulta;
- `search-index.json` — índice das 56 páginas de 1922;
- `search-index-all.json` — índice consolidado dos anos em PDF;
- `fontes-pdf.json` — catálogo das partes PDF de 1923 a 1927;
- `.github/workflows/build-search-index.yml` — processamento automatizado do OCR e atualização da busca.

## Preservação

Os arquivos originais não são alterados. O OCR é gerado como índice textual para localização de palavras. As cópias digitalizadas permanecem armazenadas no Google Drive.
