# GeoAI — Faixa de Areia

Segmentação semântica da faixa de areia no litoral norte de Salvador (BA) com imagens CBERS-4A e GeoAI,
com apoio da ortofoto CONDER para interpretação e conferência.
Atividade da disciplina **PPEC083** (Prof. Mauro Alixandrini).

**Autor:** Felipe Reis da Cruz

## Base metodológica

O projeto segue o livro *GeoAI* (Qiusheng Wu) e os notebooks da disciplina:

- [Aula Extra — WMS_to_geotiff](https://alixandrini.github.io/PPEC083/Notebooks/wms_to_geotiff.html): exportação de ortofotos de serviços WMS;
- [Aula 5 — preparação de dados](https://alixandrini.github.io/PPEC083/Notebooks/Aula_5.html): rasterização de rótulos e geração de blocos;
- [Aula 8 — segmentação semântica](https://alixandrini.github.io/PPEC083/Notebooks/semantic_segmentation.html): treinamento e inferência.

Cada notebook indica o que vem do material e o que foi ajustado para este projeto, com o motivo de cada ajuste.

## Notebooks

| # | Notebook | Conteúdo | Colab |
|---|---|---|---|
| 01 | [01_aquisicao_ortofoto_conder.ipynb](notebooks/01_aquisicao_ortofoto_conder.ipynb) | Ortofoto CONDER RMS/Recôncavo 2010 sobre a área do recorte CBERS: exportação WMS em blocos e mosaico | [![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/flipufba/geoai-faixa-areia/blob/main/notebooks/01_aquisicao_ortofoto_conder.ipynb) |
| 02 | [02_rotulos_e_tiles.ipynb](notebooks/02_rotulos_e_tiles.ipynb) | Protocolo de digitalização da areia, CBERS em 8 bits, máscara (`vector_to_raster`), tiles de 128 px (`export_geotiff_tiles`) e separação espacial treino/teste | [![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/flipufba/geoai-faixa-areia/blob/main/notebooks/02_rotulos_e_tiles.ipynb) |
| 03 | *a fazer* | Treinamento U-Net, inferência e avaliação | — |

## Dados

As imagens **não** ficam no repositório. Elas ficam numa pasta de dados local ou no Google Drive. A exceção são os
rótulos vetoriais ([rotulos/](rotulos/)), que são pequenos e versionados para garantir a reprodutibilidade.



```
sensoriamento_remoto/
├── cbers_recortado.tiff        # CBERS-4A/WPM 09/02/2021, L4 (DN), RGB = bandas 3-2-1, 8 m, EPSG:32724
├── conder_rms_2010/            # criada pelo notebook 01 (blocos, visão geral e mosaico)
└── preparacao/                 # criada pelo notebook 02 (CBERS 8 bits, máscara e tiles treino/teste)
```

| Dado | Origem | Observação |
|---|---|---|
| CBERS-4A WPM, cena 195/129, 09/02/2021 | INPE, recortada no QGIS | imagem de trabalho e referência espacial |
| Ortofoto RMS_Reconcavo_2010 | [CONDER — WMS](https://mapas.conder.ba.gov.br/arcgis/services/MOSAICO/RMS_Reconcavo_2010/ImageServer/WMSServer) | apoio à interpretação; pixel nativo 0,6 m; **não é contemporânea da CBERS** |

## Como executar

### Google Colab
Abra o notebook pelo botão *Abrir no Colab*, execute a célula de instalação, monte o Drive e ajuste `PASTA_DADOS`
na seção de configuração.

### Computador (VS Code)
```bash
conda env create -f environment.yml   # ou use um ambiente geoai já existente
conda activate geoai
```
No VS Code, selecione o ambiente conda `geoai` como kernel. O ambiente precisa estar **ativado**: no Windows, um kernel
iniciado sem ativação pode morrer ao desenhar figuras (conflito de DLL do MKL).

A pasta de dados é indicada pela variável de ambiente `GEOAI_FAIXA_DADOS`. Sem ela, o padrão é
`~/OneDrive/Mestrado/sensoriamento_remoto`.

## Estrutura

```
├── notebooks/        # notebooks de entrega, publicados sem saídas
├── rotulos/          # polígonos de areia (GeoPackage) — pequenos, por isso versionados
├── environment.yml
└── README.md
```

## Cuidados metodológicos

- A ortofoto de 2010 e a CBERS de 2021 não são contemporâneas. Mudanças na costa, na maré e na ocupação impedem usar a
  ortofoto automaticamente como verdade de referência.
- A imagem RGB entregue pelo WMS não é uma máscara de classes. Os rótulos são produzidos à parte, na grade da CBERS.
- O tamanho da área de estudo, o dos blocos de download e o dos *tiles* do modelo são coisas distintas. Os parâmetros
  dos exemplos de aula são contextualizados antes de serem aplicados.
