# Rótulos

`areia_cbers_2021.gpkg` — polígonos de referência digitalizados no QGIS sobre a CBERS-4A de 09/02/2021
(protocolo na seção 4 do notebook 02).

| Camada | Geometria | Campos | Conteúdo |
|---|---|---|---|
| `areia` | polígono | `class` (inteiro) = 1 | toda areia exposta: faixa de praia, dunas sem vegetação e outros areais |
| `excluir` (opcional) | polígono | livre | áreas sem interpretação segura (nuvens, sombras); os tiles que as tocam são descartados |

- SRC: EPSG:32724 (WGS 84 / UTM 24S), o mesmo do recorte CBERS.
- A ortofoto CONDER 2010 serve apenas de apoio. Quando ela diverge da imagem, vale a CBERS de 2021.
