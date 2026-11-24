"""Gera notebooks/01_aquisicao_ortofoto_conder.ipynb.

O conteúdo do notebook é mantido neste script para que as alterações fiquem legíveis no Git.
Uso (com o ambiente geoai ativado):  python scripts/gerar_notebook_01.py
"""
from pathlib import Path
import nbformat as nbf

C = []
md = lambda s: C.append(nbf.v4.new_markdown_cell(s.strip("\n")))
code = lambda s: C.append(nbf.v4.new_code_cell(s.strip("\n")))

REPO = "flipufba/geoai-faixa-areia"
NOME = "01_aquisicao_ortofoto_conder.ipynb"

md(f"""
# Segmentação da faixa de areia com GeoAI — CBERS-4A e ortofoto CONDER
## Notebook 01 — Aquisição da ortofoto CONDER na área de estudo

[![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/{REPO}/blob/main/notebooks/{NOME})

**Disciplina:** PPEC083 — Prof. Mauro Alixandrini
**Autor:** Felipe Reis da Cruz
**Base metodológica:** livro *GeoAI* (Qiusheng Wu) e notebooks da disciplina:
[Aula Extra — WMS_to_geotiff](https://alixandrini.github.io/PPEC083/Notebooks/wms_to_geotiff.html),
[Aula 5 — preparação de dados](https://alixandrini.github.io/PPEC083/Notebooks/Aula_5.html) e
[Aula 8 — segmentação semântica](https://alixandrini.github.io/PPEC083/Notebooks/semantic_segmentation.html).

### Objetivo
Obter, pelo serviço WMS da CONDER, a ortofoto **RMS/Recôncavo 2010** exatamente sobre a área do recorte CBERS-4A já
preparado, para apoiar a **interpretação e a conferência** dos rótulos da faixa de areia nas etapas seguintes.

### Onde este notebook se encaixa
| Etapa | Onde | Situação |
|---|---|---|
| Recorte RGB da CBERS-4A (bandas 3, 2, 1) | QGIS | concluído e conferido |
| **Aquisição da ortofoto CONDER** | **notebook 01 (este)** | **em andamento** |
| Rótulos (`vector_to_raster`) e blocos de treinamento (`export_geotiff_tiles`) | notebook 02 | a fazer — Aula 5 |
| Treinamento, inferência e avaliação | notebook 03 | a fazer — Aula 8 |
""")

md("""
## 1. Dados e cuidados metodológicos

**Imagem de trabalho (já disponível):** cena CBERS-4A/WPM de 09/02/2021, nível L4 (DN), bandas originais 3, 2 e 1, nessa
ordem, recortadas no QGIS (`cbers_recortado.tiff`). O recorte tem resolução de 8 m, SRC WGS 84 / UTM 24S (EPSG:32724) e
cerca de 24 × 21 km do litoral norte de Salvador. **Este TIFF é a única referência espacial do notebook.** Seu SRC e seus
limites são lidos diretamente do arquivo.

**Imagem de apoio (obtida aqui):** mosaico de ortofotos *RMS_Reconcavo_2010* da CONDER, publicado como serviço WMS
(ArcGIS ImageServer).

Cuidados que orientam o uso da ortofoto:
1. **Datas diferentes (2010 × 2021).** Erosão, progradação, maré e ocupação podem ter mudado a linha de costa. A ortofoto
   **não** é tratada automaticamente como verdade de referência da cena CBERS; ela é apoio à interpretação.
2. **Uma imagem RGB não é uma máscara de classes.** O WMS entrega uma imagem renderizada para visualização. Os rótulos da
   areia serão produzidos no notebook 02, como polígonos rasterizados na grade da CBERS (Aula 5).
3. **Área de estudo ≠ bloco do modelo.** Os blocos de 2048 px usados aqui só organizam a transferência de dados.
   Eles não têm relação com o tamanho dos *tiles* de treinamento, que será definido no notebook 02.
""")

md("""
## 2. Base no material e melhorias adotadas

O notebook *WMS_to_geotiff* da disciplina (extraído da documentação do `leafmap`) mostra o caminho:
listar as camadas do serviço (`common.get_wms_layers`), visualizá-las num mapa (`add_wms_layer`), exportar com
`common.wms_to_geotiff` dentro de uma função auxiliar, cobrir a área com várias exportações num laço que desloca a `bbox`
e visualizar o resultado (`add_raster`).

Este notebook segue essa sequência e usa **a mesma função de exportação**, com correções e ajustes para a área e o serviço
deste projeto:

| Item | No material (Salvador_2006, Ilha de Maré) | Neste notebook (RMS_Reconcavo_2010) | Motivo |
|---|---|---|---|
| Área (`bbox`) | digitada em graus (EPSG:4326) | lida do TIFF CBERS, em metros (EPSG:32724) | coincidir com a imagem de trabalho |
| `bbox` na função auxiliar | recebida, mas não repassada a `wms_to_geotiff` | repassada explicitamente | sem isso, todos os blocos teriam a mesma extensão |
| `output_crs` | EPSG:3857 | EPSG:32724, o SRC do TIFF | comparar com a CBERS sem reprojetar |
| Resolução | `scale=0.5` | **0,6 m**, consultados no próprio serviço | pixel nativo; 0,5 m só reamostraria |
| Tamanho de cada pedido | calculado por `scale` | `width`/`height` explícitos (como no *Exemplo 2* do material) | pixels exatos e blocos contíguos |
| `format` | não informado | `image/tiff`, verificado no serviço | o PNG deste servidor vem RGBA e falha |
| Laço de blocos | incrementos fixos em graus | grade em pixels sobre a extensão do TIFF | cobrir 24 × 21 km sem lacunas nem sobreposição |
| Robustez | — | conferência de cada bloco e retomada após interrupção | centenas de requisições a um servidor externo |
| Cobertura | — | visão geral de 24 m antes do download | ~1/3 da área é mar fora do mosaico |
| Resultado | arquivos separados | mosaico único, escrito por janelas | imagem única sem estourar a memória |

As decisões que diferem do material são marcadas no texto com **➜ Ajuste**.
""")

md("""
## 3. Ambiente

**Computador (VS Code):** abra este notebook e selecione o kernel do ambiente conda `geoai`.
O ambiente precisa estar **ativado**: escolha-o na lista de ambientes conda do VS Code, e não apenas pelo caminho do
`python.exe`. Sem ativação, a biblioteca MKL desse ambiente carrega DLLs erradas no Windows e o kernel morre ao desenhar
figuras (erro `0xc06d007f`).

**Google Colab:** use o botão *Abrir no Colab*, execute a célula de instalação abaixo e a de montagem do Drive.
Os dados (TIFFs) ficam no Google Drive, nunca no repositório.

GPU não é necessária nesta etapa.
""")

code('''
# Instala apenas o que estiver faltando (no Colab, normalmente leafmap e owslib).
import sys, importlib.util, subprocess

IN_COLAB = importlib.util.find_spec("google.colab") is not None

pacotes = {             # módulo importado -> nome do pacote no pip
    "rasterio": "rasterio",
    "leafmap": "leafmap",
    "owslib": "owslib",
    "PIL": "Pillow",
    "matplotlib": "matplotlib",
    "pyproj": "pyproj",
}
faltando = [pip for modulo, pip in pacotes.items() if importlib.util.find_spec(modulo) is None]
if faltando:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", *faltando])

print("Python:", sys.executable)
print("Executando no Colab:", IN_COLAB)
print("Instalados agora:", faltando or "nenhum")
''')

code('''
# No Colab, monta o Google Drive para ler o TIFF CBERS e salvar a ortofoto.
if IN_COLAB:
    from google.colab import drive
    drive.mount("/content/drive")
''')

md("""
## 4. Configuração

Todos os parâmetros editáveis estão nesta célula.

* `PASTA_DADOS` — pasta com `cbers_recortado.tiff`. No Colab, aponta para o Drive. No computador, use a variável de
  ambiente `GEOAI_FAIXA_DADOS` ou edite o caminho padrão.
* `RESOLUCAO` — pixel da ortofoto exportada, em metros.
  **➜ Ajuste:** o material usa `scale=0.5`, para outro serviço (Salvador_2006). O RMS_Reconcavo_2010 informa pixel nativo de
  **0,6 m**, valor conferido na seção 6. Exportar a 0,5 m criaria cerca de 44% mais pixels por reamostragem, sem ganho de detalhe.
* `TAMANHO_BLOCO` — lado, em pixels, de cada requisição ao servidor. É um limite prático do WMS e não tem relação com o modelo.
* `BAIXAR_TUDO` — começa em `False`, e só um bloco de teste é baixado. Depois de conferi-lo, mude para `True`.
""")

code('''
from pathlib import Path
import os, math, json, time, hashlib

import numpy as np
import requests
import rasterio
from rasterio.crs import CRS as RioCRS
from rasterio.warp import transform_bounds
from rasterio.transform import from_origin
from rasterio.windows import Window
import matplotlib.pyplot as plt
import leafmap.common as common          # mesmo módulo usado no material
from owslib.wms import WebMapService     # leitura do GetCapabilities (formatos e SRC aceitos)

# --- Caminhos -----------------------------------------------------------------
if IN_COLAB:
    PASTA_DADOS = Path("/content/drive/MyDrive/sensoriamento_remoto")   # ajuste se necessário
else:
    PASTA_DADOS = Path(os.environ.get("GEOAI_FAIXA_DADOS",
                                      Path.home() / "OneDrive" / "Mestrado" / "sensoriamento_remoto"))
TIFF = PASTA_DADOS / "cbers_recortado.tiff"     # recorte CBERS-4A RGB: referência espacial
SAIDA = PASTA_DADOS / "conder_rms_2010"         # blocos, visão geral e mosaico da ortofoto

# --- Serviço WMS (geoportal Geopolis / CONDER) ---------------------------------
URL = "https://mapas.conder.ba.gov.br/arcgis/services/MOSAICO/RMS_Reconcavo_2010/ImageServer/WMSServer"
CAMADA = None          # None = usa a única camada do serviço (conferido na seção 6)

# --- Exportação ------------------------------------------------------------------
RESOLUCAO = 0.6        # m/pixel — resolução nativa do RMS_Reconcavo_2010
TAMANHO_BLOCO = 2048   # pixels por requisição
ESCALA_VISAO = 24      # m/pixel da visão geral (apenas triagem e visualização)
BAIXAR_TUDO = False    # True somente depois de conferir o bloco de teste

if not TIFF.exists():
    raise FileNotFoundError(f"TIFF não encontrado: {TIFF}. Ajuste PASTA_DADOS.")
SAIDA.mkdir(parents=True, exist_ok=True)
print("Pasta de dados:", PASTA_DADOS)
''')

md("""
## 5. Área de estudo lida do TIFF CBERS

No material, a `bbox` é digitada em graus. **➜ Ajuste:** aqui ela é lida do próprio TIFF, no SRC projetado dele (UTM,
em metros). Pedir a ortofoto no mesmo SRC e com os mesmos limites evita transformar um envelope geográfico, o que alargaria
a área, e permite sobrepor as duas imagens sem reprojeção.
""")

code('''
with rasterio.open(TIFF) as src:
    limites = tuple(src.bounds)          # (oeste, sul, leste, norte), em metros
    crs_tiff = src.crs
    print(f"CBERS: {src.width} × {src.height} px, pixel {src.res[0]:g} m, {src.count} bandas ({src.dtypes[0]})")

# A grade de exportação é calculada em metros, então o SRC precisa ser projetado.
if not crs_tiff or not crs_tiff.is_projected or crs_tiff.linear_units != "metre":
    raise ValueError("Esta configuração requer TIFF em SRC projetado com unidade metro.")

CRS = crs_tiff.to_string()               # 'EPSG:32724'
oeste, sul, leste, norte = limites
print("SRC:", CRS)
print("Limites (m):", limites)
print(f"Extensão: {(leste - oeste)/1000:.1f} km × {(norte - sul)/1000:.1f} km")
# Apenas informativo: a mesma área em graus, forma usada no material.
print("Equivalente em EPSG:4326:", [round(v, 5) for v in transform_bounds(crs_tiff, "EPSG:4326", *limites)])
''')

md("""
## 6. Explorar o serviço WMS

Como no material, as camadas são listadas com `common.get_wms_layers`. Além disso:
* o *GetCapabilities* é lido com `owslib` para conferir os **formatos** e os **SRC** aceitos;
* o metadado REST do mesmo ImageServer informa a **resolução nativa**.

O download continua sendo feito pelo WMS.

Resultado obtido em 24/11/2026:
* camada única `RMS_Reconcavo_2010`, com 3 bandas de 8 bits;
* pixel nativo de 0,6 m e SRC nativo EPSG:31984 (SIRGAS 2000 / UTM 24S);
* SRC anunciados pelo WMS: apenas EPSG:4326 e EPSG:31984.

**➜ Ajuste (SRC):** o EPSG:32724 do TIFF não é anunciado. Para o PROJ, a transformação entre WGS 84 / UTM 24S e
SIRGAS 2000 / UTM 24S é nula (0 m). O servidor aceita o pedido em EPSG:32724 e devolve GeoTIFF com esse SRC e conteúdo
idêntico ao pedido em 31984. Por isso, o pedido fica no SRC do TIFF e cada bloco recebido é conferido. Se o servidor um
dia recusar, basta usar `CRS_PEDIDO = "EPSG:31984"`.

**➜ Ajuste (formato):** o material não informa `format`. Este servidor devolve PNG com 4 canais (RGBA), mesmo sem
transparência, e o `wms_to_geotiff` grava apenas 3 bandas nesse caso, o que gera erro. O `image/tiff` vem com 3 bandas,
já georreferenciado e sem compressão com perdas.
""")

code('''
# 6.1 Camadas disponíveis — mesma chamada do material
camadas = common.get_wms_layers(URL)
print("Camadas disponíveis:", camadas)
if CAMADA is None:
    if len(camadas) != 1:
        raise ValueError("Mais de uma camada: defina CAMADA na configuração.")
    CAMADA = camadas[0]
if CAMADA not in camadas:
    raise ValueError(f"Camada {CAMADA} não encontrada.")
''')

code('''
# 6.2 Resolução nativa declarada pelo ImageServer (endpoint REST do mesmo serviço)
url_rest = URL.replace("/services/", "/rest/services/").replace("/WMSServer", "")
meta = requests.get(url_rest, params={"f": "json"}, timeout=60).json()
print(f"Pixel nativo: {meta['pixelSizeX']:.2f} × {meta['pixelSizeY']:.2f} m | "
      f"{meta['bandCount']} bandas {meta['pixelType']} | SRC nativo: EPSG:{meta['spatialReference']['wkid']}")
if not math.isclose(RESOLUCAO, meta["pixelSizeX"], abs_tol=0.01):
    print(f"Atenção: RESOLUCAO = {RESOLUCAO} m difere da nativa; o servidor vai reamostrar.")
''')

code('''
# 6.3 SRC e formatos aceitos pelo GetMap (GetCapabilities via owslib)
wms = WebMapService(URL, version="1.1.1", timeout=60)
sistemas = sorted(s.upper() for s in wms[CAMADA].crsOptions)
formatos = wms.getOperationByName("GetMap").formatOptions
print("SRC anunciados:", sistemas)
print("Formatos:", formatos)

CRS_PEDIDO = CRS
if CRS.upper() not in sistemas:
    # Aceita o SRC do TIFF apenas se for numericamente equivalente a um SRC anunciado.
    from pyproj import Transformer
    equivalente = "EPSG:31984"
    t = Transformer.from_crs(CRS, equivalente, always_xy=True)
    desvio = max(abs(a - b) for a, b in zip(t.transform(oeste, sul), (oeste, sul)))
    if equivalente not in sistemas or desvio >= 1:
        raise ValueError(f"WMS não anuncia {CRS} nem um SRC equivalente: {sistemas}")
    print(f"{CRS} não anunciado; desvio até {equivalente} = {desvio:.3f} m -> pedido mantido em {CRS}.")

FORMATO = next((f for f in ["image/tiff", "image/geotiff"] if f in formatos), None)
if FORMATO is None:
    raise ValueError("O servidor não oferece GeoTIFF.")
print("Usando:", CAMADA, "|", CRS_PEDIDO, "|", FORMATO)
''')

md("""
### 6.4 Visualizar a camada no mapa

Como no material, a camada WMS é sobreposta a um mapa base, agora com o contorno da área do TIFF em vermelho.
O material usa `leafmap.maplibregl`. No ambiente `geoai` local esse módulo falha por incompatibilidade com `ipyvuetify`;
nesse caso, usa-se o `leafmap.Map` padrão, que oferece o mesmo `add_wms_layer`.
""")

code('''
lon_min, lat_min, lon_max, lat_max = transform_bounds(crs_tiff, "EPSG:4326", *limites)
centro = [(lat_min + lat_max) / 2, (lon_min + lon_max) / 2]
contorno = {"type": "FeatureCollection", "features": [{
    "type": "Feature", "properties": {"nome": "recorte CBERS"},
    "geometry": {"type": "Polygon", "coordinates": [[[lon_min, lat_min], [lon_max, lat_min],
                 [lon_max, lat_max], [lon_min, lat_max], [lon_min, lat_min]]]}}]}

try:
    import leafmap.maplibregl as leafmap_ml          # forma usada no material
    m = leafmap_ml.Map(center=[centro[1], centro[0]], zoom=11, style="positron")
    m.add_wms_layer(URL, layers=CAMADA, name="Ortofoto RMS 2010", before_id=m.first_symbol_layer_id)
    m.add_geojson(contorno, layer_type="line", paint={"line-color": "#ff0000", "line-width": 2})
except Exception as erro:
    print(f"maplibregl indisponível ({type(erro).__name__}); usando leafmap.Map.")
    import leafmap
    m = leafmap.Map(center=centro, zoom=11)
    m.add_wms_layer(URL, layers=CAMADA, name="Ortofoto RMS 2010", format="image/png", transparent=True)
    m.add_geojson(contorno, layer_name="Recorte CBERS", style={"color": "red", "fillOpacity": 0})
m
''')

md("""
## 7. Função de exportação

Como no material, a exportação fica numa função auxiliar (`wms_2_geotif`) que chama `common.wms_to_geotiff`. Ajustes:

* **➜ Correção:** a `bbox` é efetivamente repassada a `wms_to_geotiff`. No material ela é recebida pela função, mas não
  é usada.
* **➜ Ajuste:** no lugar de `scale`, a função recebe `width` e `height`, como no *Exemplo 2* do material. Assim cada bloco
  tem exatamente o número de pixels previsto, e os blocos se encaixam sem lacunas no mosaico.

Cada bloco é gravado primeiro como `.part.tif` e só recebe o nome final depois de conferido: dimensões, SRC, limites e
número de bandas. Uma interrupção nunca deixa um arquivo incompleto passar por válido. Ao executar de novo, os blocos
existentes são reaproveitados.
""")

code('''
def wms_2_geotif(url, layers, bbox, output, width, height):
    """Exporta um GeoTIFF do WMS dentro da bbox (mesma ideia da função do material)."""
    common.wms_to_geotiff(
        url=url,
        layers=layers,
        bbox=bbox,                    # [minx, miny, maxx, maxy] em CRS_PEDIDO (metros)
        output=output,
        width=width, height=height,   # dimensões exatas do bloco, em pixels
        bbox_crs=CRS_PEDIDO,          # SRC em que a bbox foi informada
        output_crs=CRS_PEDIDO,        # SRC pedido ao servidor e gravado no GeoTIFF
        version="1.1.1",
        format=FORMATO,               # image/tiff (ver seção 6)
        transparent=False,
        quiet=True,
    )


def conferir_bloco(caminho, item):
    """Verifica se o GeoTIFF recebido corresponde exatamente ao bloco pedido."""
    with rasterio.open(caminho) as ds:
        if (ds.width, ds.height) != (item["largura"], item["altura"]):
            raise ValueError(f"{caminho.name}: dimensões {ds.width}×{ds.height} diferentes do pedido.")
        if ds.crs != RioCRS.from_string(CRS_PEDIDO):
            raise ValueError(f"{caminho.name}: SRC {ds.crs} diferente de {CRS_PEDIDO}.")
        if not np.allclose(tuple(ds.bounds), item["bbox"], rtol=0, atol=0.01):
            raise ValueError(f"{caminho.name}: limites diferentes do pedido.")
        if ds.count != 3:
            raise ValueError(f"{caminho.name}: esperado RGB, recebidas {ds.count} bandas.")
        ds.read(window=Window(0, 0, 1, 1))   # força uma leitura: detecta arquivo truncado


def caminho_bloco(item):
    return PASTA_BLOCOS / f"r{item['linha']:06d}_c{item['coluna']:06d}.tif"


def baixar(item):
    """Baixa um bloco (ou reaproveita o existente, se válido) e devolve seu caminho."""
    final = caminho_bloco(item)
    if final.exists():
        conferir_bloco(final, item)
        return final
    temporario = final.with_name(final.stem + ".part.tif")
    wms_2_geotif(URL, CAMADA, item["bbox"], str(temporario), item["largura"], item["altura"])
    conferir_bloco(temporario, item)
    temporario.replace(final)
    return final
''')

md("""
## 8. Grade de blocos

No material, a área é coberta deslocando a `bbox` por incrementos fixos em graus (`bbox[1] += 0.009`, `bbox[0] += 0.017`).
**➜ Ajuste:** aqui a grade é calculada em pixels sobre a extensão do TIFF. Ela parte do canto superior esquerdo
(oeste, norte) e avança de `TAMANHO_BLOCO` em `TAMANHO_BLOCO` pixels. Os blocos ficam contíguos, sem lacunas nem
sobreposição, e os da última linha e da última coluna apenas são menores.

Como a largura (24 152 m) não é múltipla de 0,6 m, o número de pixels é arredondado para cima. O mosaico ultrapassa a
borda leste em 0,4 m, menos de um pixel da ortofoto e desprezível diante do pixel CBERS de 8 m.

Os blocos ficam numa subpasta cujo nome é uma assinatura da configuração (serviço, camada, área, SRC, resolução, bloco e
formato). Se algum parâmetro mudar, os blocos de outra configuração não são reaproveitados por engano.
""")

code('''
largura = math.ceil((leste - oeste) / RESOLUCAO - 1e-6)   # pixels do mosaico
altura = math.ceil((norte - sul) / RESOLUCAO - 1e-6)
transform = from_origin(oeste, norte, RESOLUCAO, RESOLUCAO)
limites_mosaico = (oeste, norte - altura * RESOLUCAO, oeste + largura * RESOLUCAO, norte)

plano = []
for linha in range(0, altura, TAMANHO_BLOCO):          # papel do laço "j" do material
    for coluna in range(0, largura, TAMANHO_BLOCO):    # papel do laço "i" do material
        w = min(TAMANHO_BLOCO, largura - coluna)
        h = min(TAMANHO_BLOCO, altura - linha)
        x0 = oeste + coluna * RESOLUCAO
        y1 = norte - linha * RESOLUCAO
        plano.append(dict(linha=linha, coluna=coluna, largura=w, altura=h,
                          bbox=[x0, y1 - h * RESOLUCAO, x0 + w * RESOLUCAO, y1]))

config = dict(url=URL, camada=CAMADA, limites=limites, crs=CRS, crs_pedido=CRS_PEDIDO,
              resolucao=RESOLUCAO, bloco=TAMANHO_BLOCO, formato=FORMATO)
assinatura = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:12]
PASTA_BLOCOS = SAIDA / assinatura
PASTA_BLOCOS.mkdir(exist_ok=True)
(PASTA_BLOCOS / "manifesto.json").write_text(json.dumps(dict(config=config, blocos=plano), indent=2),
                                             encoding="utf-8")

print(f"Mosaico: {largura} × {altura} px a {RESOLUCAO} m")
print(f"Excedente da grade: leste {limites_mosaico[2] - leste:.2f} m | sul {sul - limites_mosaico[1]:.2f} m")
print(f"Blocos: {len(plano)} de até {TAMANHO_BLOCO} px | pasta: {PASTA_BLOCOS.name}")
print(f"Volume RGB sem compressão (área inteira): {largura * altura * 3 / 1e9:.2f} GB")
''')

md("""
## 9. Visão geral e triagem de cobertura

O mosaico de 2010 não cobre toda a área do recorte: parte do mar fica fora dele, e o serviço devolve preto (0, 0, 0) nesses
pontos. Uma única exportação de baixa resolução (24 m), feita com a mesma função, serve para:
1. conferir visualmente a cobertura da costa;
2. marcar os blocos totalmente vazios, que não serão pedidos e ficarão com `nodata = 0` no mosaico.

**➜ Ajuste:** o material não faz essa triagem. Ela não altera nenhum pixel baixado; só poupa cerca de um terço das
requisições. Por segurança, a janela de cada bloco na visão geral é ampliada em 2 pixels.
""")

code('''
VISAO = PASTA_BLOCOS / "visao_geral_24m.tif"
if not VISAO.exists():
    wms_2_geotif(URL, CAMADA, list(limites_mosaico), str(VISAO),
                 width=math.ceil(largura * RESOLUCAO / ESCALA_VISAO),
                 height=math.ceil(altura * RESOLUCAO / ESCALA_VISAO))

with rasterio.open(VISAO) as ds:
    visao = ds.read()
    fx, fy = ds.width / largura, ds.height / altura   # pixels da visão geral por pixel do mosaico
coberto = visao.sum(axis=0) > 0                       # True onde o serviço tem imagem


def tem_cobertura(item, margem=2):
    r0 = max(int(item["linha"] * fy) - margem, 0)
    r1 = math.ceil((item["linha"] + item["altura"]) * fy) + margem
    c0 = max(int(item["coluna"] * fx) - margem, 0)
    c1 = math.ceil((item["coluna"] + item["largura"]) * fx) + margem
    return bool(coberto[r0:r1, c0:c1].any())


plano_baixar = [p for p in plano if tem_cobertura(p)]
print(f"Área sem cobertura: {1 - coberto.mean():.1%}")
print(f"Blocos a baixar: {len(plano_baixar)} de {len(plano)}")

fig, ax = plt.subplots(figsize=(10, 9))
ax.imshow(np.moveaxis(visao, 0, -1), extent=(0, largura, altura, 0))
for p in plano:
    cor = "yellow" if p in plano_baixar else "red"
    ax.add_patch(plt.Rectangle((p["coluna"], p["linha"]), p["largura"], p["altura"],
                               fill=False, ec=cor, lw=0.4))
ax.set_title("Visão geral (24 m) — amarelo: blocos a baixar | vermelho: sem cobertura")
ax.axis("off")
plt.show()
''')

md("""
## 10. Bloco de teste

Antes do download completo, baixa-se **um** bloco com cobertura, o mais próximo do centro da área, para confirmar o
acesso, o georreferenciamento e a aparência da imagem.
""")

code('''
cx, cy = largura / 2, altura / 2
teste = min(plano_baixar, key=lambda p: (p["coluna"] + p["largura"] / 2 - cx) ** 2
                                        + (p["linha"] + p["altura"] / 2 - cy) ** 2)
arquivo_teste = baixar(teste)

with rasterio.open(arquivo_teste) as ds:
    print(f"{arquivo_teste.name}: {ds.width}×{ds.height} px | {ds.crs} | pixel {ds.res[0]:.2f} m | {ds.dtypes[0]}")
    imagem_teste = ds.read(out_shape=(3, ds.height // 4, ds.width // 4))   # leitura reduzida, só para exibir

plt.figure(figsize=(8, 8))
plt.imshow(np.moveaxis(imagem_teste, 0, -1))
plt.title("Bloco de teste — confira a cobertura e a aparência")
plt.axis("off")
plt.show()
''')

md("""
## 11. Download completo

Mude `BAIXAR_TUDO` para `True` na seção 4 e execute novamente as células a partir dela.
* Uma pausa curta entre requisições evita sobrecarregar o servidor da CONDER.
* Se a execução for interrompida (rede, servidor, notebook fechado), basta executar de novo: os blocos já conferidos são
  reaproveitados, e só os faltantes são pedidos.
* Volume esperado: cerca de 230 requisições e de 2 a 3 GB em disco (blocos + mosaico).
""")

code('''
if BAIXAR_TUDO:
    inicio = time.time()
    for n, item in enumerate(plano_baixar, 1):
        baixar(item)
        print(f"{n}/{len(plano_baixar)} blocos | {(time.time() - inicio) / 60:.1f} min", end="\\r")
        time.sleep(0.25)
    print("\\nDownload completo.")
else:
    print("Somente o bloco de teste foi baixado. Para baixar tudo, defina BAIXAR_TUDO = True.")
''')

md("""
## 12. Mosaico

Os blocos são reunidos num único GeoTIFF, escrito **por janelas** (um bloco por vez), para não carregar gigabytes na
memória. O arquivo é *tiled* 256 × 256 e tem compressão sem perdas (`deflate`). As áreas sem cobertura ficam com valor 0,
declarado como `nodata`. O arquivo só recebe o nome final depois de conferidos o SRC e os limites.
""")

code('''
faltantes = [p for p in plano_baixar if not caminho_bloco(p).exists()]
MOSAICO = SAIDA / f"conder_rms_2010_{assinatura}.tif"

if faltantes:
    print(f"Mosaico adiado: faltam {len(faltantes)} blocos.")
elif MOSAICO.exists():
    print("Mosaico já existe:", MOSAICO)
else:
    perfil = dict(driver="GTiff", dtype="uint8", count=3, width=largura, height=altura,
                  crs=CRS_PEDIDO, transform=transform, nodata=0,
                  tiled=True, blockxsize=256, blockysize=256, compress="deflate", BIGTIFF="YES")
    parcial = MOSAICO.with_name(MOSAICO.stem + ".part.tif")
    with rasterio.open(parcial, "w", **perfil) as destino:
        for item in plano_baixar:
            conferir_bloco(caminho_bloco(item), item)
            with rasterio.open(caminho_bloco(item)) as origem:
                destino.write(origem.read(),
                              window=Window(item["coluna"], item["linha"], item["largura"], item["altura"]))
    with rasterio.open(parcial) as resultado:
        assert resultado.crs == RioCRS.from_string(CRS_PEDIDO)
        assert np.allclose(tuple(resultado.bounds), limites_mosaico, rtol=0, atol=0.01)
    parcial.replace(MOSAICO)
    print("Mosaico salvo:", MOSAICO)
''')

md("""
## 13. Visualizar o resultado

O material confere o resultado no mapa (`add_raster`). Aqui também é feita uma leitura reduzida do mosaico ao lado da
CBERS, que não depende do servidor de *tiles* (`localtileserver`).
""")

code('''
if MOSAICO.exists():
    with rasterio.open(MOSAICO) as ds:
        fator = 40   # 0,6 m × 40 = 24 m por pixel na exibição
        orto = ds.read(out_shape=(3, ds.height // fator, ds.width // fator))
    with rasterio.open(TIFF) as ds:
        cbers = ds.read().astype("float32")
    # Realce linear entre os percentis 2 e 98, apenas para exibir a CBERS em DN.
    p2, p98 = np.percentile(cbers[cbers > 0], (2, 98))
    cbers = np.clip((cbers - p2) / (p98 - p2), 0, 1)

    fig, eixos = plt.subplots(1, 2, figsize=(16, 7))
    eixos[0].imshow(np.moveaxis(cbers, 0, -1))
    eixos[0].set_title("CBERS-4A 09/02/2021 — RGB 3-2-1, 8 m")
    eixos[1].imshow(np.moveaxis(orto, 0, -1))
    eixos[1].set_title("Ortofoto CONDER 2010 — 0,6 m (exibida a 24 m)")
    for e in eixos:
        e.axis("off")
    plt.show()

    # Visualização interativa, como no material (opcional; requer localtileserver).
    try:
        import leafmap
        m2 = leafmap.Map()
        m2.add_raster(str(MOSAICO), layer_name="Ortofoto CONDER 2010")
        display(m2)
    except Exception as erro:
        print(f"Mapa interativo indisponível ({type(erro).__name__}); abra o mosaico no QGIS.")
else:
    print("Mosaico ainda não criado.")
''')

md("""
## 14. Considerações e próximas etapas

**Resultado desta etapa:** a ortofoto CONDER 2010 a 0,6 m, no mesmo SRC (EPSG:32724) e com a mesma origem do recorte
CBERS, cobrindo toda a faixa costeira da área de estudo.

**Conferência recomendada (QGIS):** abrir o mosaico e o TIFF CBERS juntos e verificar o alinhamento em feições estáveis,
como vias, edificações e as pistas do aeroporto. Diferenças **na linha de costa** podem ser mudanças reais entre 2010 e
2021, ou efeito de maré, e não devem ser tomadas como erro de registro.

**Notebook 02 — rótulos e blocos de treinamento (Aula 5):**
1. delimitar polígonos da faixa de areia **sobre a CBERS de 2021**, usando a ortofoto apenas como apoio à interpretação;
2. rasterizá-los com `geoai.vector_to_raster(..., reference_raster=cbers_recortado.tiff)`, com areia = 1 e fundo = 0;
3. gerar pares imagem–máscara com `geoai.export_geotiff_tiles`, com o tamanho dos *tiles* escolhido para a CBERS
   (3019 × 2676 px), e não copiado dos exemplos (512 px sobre imagens NAIP de 0,6 m);
4. separar treino, validação e teste **espacialmente**. A Aula 5 recomenda essa separação, mas o material não traz código
   para ela; será um ajuste declarado.

**Notebook 03 — segmentação (Aula 8):** `geoai.train_segmentation_model` (U-Net) e `geoai.semantic_segmentation`,
com avaliação sobre o conjunto de teste.
""")

nb = nbf.v4.new_notebook()
nb["cells"] = C
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3 (geoai)", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
    "colab": {"provenance": []},
}
nbf.validate(nb)
destino = Path(__file__).resolve().parents[1] / "notebooks" / NOME
destino.parent.mkdir(exist_ok=True)
nbf.write(nb, destino)
print("Gerado:", destino)
