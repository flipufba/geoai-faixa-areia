# Rótulos

Polígonos de referência de **areia exposta** (classe 1: faixa de praia, dunas sem vegetação e outros areais), um arquivo
por imagem do estudo. Os rótulos de uma imagem **não** são usados para a outra, porque as datas são diferentes.

| Arquivo | Imagem | Digitalizado sobre | Situação |
|---|---|---|---|
| `areia_cbers_2021.gpkg` | CBERS-4A, 09/02/2021, 8 m | somente a CBERS (sem consultar a ortofoto) | a fazer (protocolo: notebook 02, seção 4) |
| `areia_conder_2010.gpkg` | ortofoto CONDER RMS/Recôncavo 2010, 0,6 m | somente a ortofoto | etapa futura |

Camadas de cada GeoPackage:

| Camada | Geometria | Campos | Conteúdo |
|---|---|---|---|
| `areia` | polígono | `class` (inteiro) = 1 | toda areia exposta visível na imagem |
| `excluir` (opcional) | polígono | livre | áreas sem interpretação segura (nuvens, sombras); os tiles que as tocam são descartados |

SRC: EPSG:32724 (WGS 84 / UTM 24S), o mesmo das duas imagens.
