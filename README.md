# GeoAI — Faixa de Areia

Segmentação semântica da areia exposta no litoral norte de Salvador (BA) com GeoAI, em duas imagens:
CBERS-4A (8 m, 2021) e ortofoto CONDER (0,6 m, 2010).
Atividade da disciplina **PPEC083** (Prof. Mauro Alixandrini).

**Autor:** Felipe Reis da Cruz

## Desenho do estudo

1. **Experimento CBERS:** rótulos digitalizados apenas sobre a CBERS-4A, sem consultar a ortofoto, seguidos de treino e
   avaliação.
2. **Experimento CONDER:** o mesmo procedimento replicado sobre a ortofoto, com rótulos próprios.
3. **Comparação:** os dois experimentos usam a mesma definição de classe (toda areia exposta), a mesma área e as mesmas
   zonas de treino e teste. Cada modelo é avaliado contra a **referência da sua própria imagem**, e a comparação principal é
   entre as métricas. As áreas de areia extraídas não são comparadas diretamente como erro, porque as imagens têm 11 anos de
   diferença.

## Base metodológica

O projeto segue o livro *GeoAI* (Qiusheng Wu) e os notebooks da disciplina:

- [Aula Extra — WMS_to_geotiff](https://alixandrini.github.io/PPEC083/Notebooks/wms_to_geotiff.html): exportação de ortofotos de serviços WMS;
- [Aula 5 — preparação de dados](https://alixandrini.github.io/PPEC083/Notebooks/Aula_5.html): rasterização de rótulos e geração de blocos;
- [Aula 8 — segmentação semântica](https://alixandrini.github.io/PPEC083/Notebooks/semantic_segmentation.html): treinamento e inferência.

Cada notebook indica o que vem do material e o que foi ajustado para este projeto, com o motivo de cada ajuste.

## Notebooks

| # | Notebook | Conteúdo | Colab |
|---|---|---|---|
| 01 | [01_aquisicao_ortofoto_conder.ipynb](notebooks/01_aquisicao_ortofoto_conder.ipynb) | Ortofoto CONDER RMS/Recôncavo 2010 (segunda imagem do estudo) sobre a área do recorte CBERS: exportação WMS em blocos e mosaico | [![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/flipufba/geoai-faixa-areia/blob/main/notebooks/01_aquisicao_ortofoto_conder.ipynb) |
| 02 | [02_rotulos_e_tiles.ipynb](notebooks/02_rotulos_e_tiles.ipynb) | **CBERS:** protocolo de digitalização da areia, conversão para 8 bits, máscara (`vector_to_raster`), tiles de 128 px (`export_geotiff_tiles`) e separação espacial treino/teste | [![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/flipufba/geoai-faixa-areia/blob/main/notebooks/02_rotulos_e_tiles.ipynb) |
| 03 | *a fazer* | **CBERS:** treinamento U-Net, inferência e avaliação | — |
| — | *a fazer* | **CONDER:** replicação de rótulos, tiles, treino e avaliação | — |
| — | *a fazer* | **Comparação** entre os experimentos | — |

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
| CBERS-4A WPM, cena 195/129, 09/02/2021 | INPE, recortada no QGIS | imagem do experimento 1 e referência espacial (área e SRC) |
| Ortofoto RMS_Reconcavo_2010 | [CONDER — WMS](https://mapas.conder.ba.gov.br/arcgis/services/MOSAICO/RMS_Reconcavo_2010/ImageServer/WMSServer) | imagem do experimento 2; pixel nativo 0,6 m; **não é contemporânea da CBERS** |

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

- A ortofoto de 2010 e a CBERS de 2021 não são contemporâneas. Mudanças na costa, na maré e na ocupação impedem usar uma
  como referência da outra. Cada imagem tem os seus próprios rótulos, e os da CBERS são feitos sem consultar a ortofoto.
- A imagem RGB entregue pelo WMS não é uma máscara de classes. Os rótulos são produzidos à parte, na grade de cada imagem.
- O tamanho da área de estudo, o dos blocos de download e o dos *tiles* do modelo são coisas distintas. Os parâmetros
  dos exemplos de aula são contextualizados antes de serem aplicados.
