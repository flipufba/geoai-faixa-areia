"""Gera notebooks/02_rotulos_e_tiles.ipynb.

O conteúdo do notebook é mantido neste script para que as alterações fiquem legíveis no Git.
Uso (com o ambiente geoai ativado):  python scripts/gerar_notebook_02.py
"""
from pathlib import Path
import nbformat as nbf

C = []
md = lambda s: C.append(nbf.v4.new_markdown_cell(s.strip("\n")))
code = lambda s: C.append(nbf.v4.new_code_cell(s.strip("\n")))

REPO = "flipufba/geoai-faixa-areia"
NOME = "02_rotulos_e_tiles.ipynb"

md(f"""
# Segmentação da faixa de areia com GeoAI — CBERS-4A e ortofoto CONDER
## Notebook 02 — Rótulos de areia e pares imagem–máscara para treinamento

[![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/{REPO}/blob/main/notebooks/{NOME})

**Disciplina:** PPEC083 — Prof. Mauro Alixandrini
**Autor:** Felipe Reis da Cruz
**Base metodológica:** [Aula 5 — preparação de dados](https://alixandrini.github.io/PPEC083/Notebooks/Aula_5.html)
(rasterização de polígonos e geração de blocos) e livro *GeoAI* (Qiusheng Wu).

### Objetivo
Transformar os polígonos de areia, digitalizados sobre a CBERS-4A de 2021, numa máscara na grade da imagem e gerar os
pares imagem–máscara (*tiles*) que alimentarão o treinamento no notebook 03, com separação espacial entre treino e teste.

| Etapa | Onde | Situação |
|---|---|---|
| Recorte RGB da CBERS-4A | QGIS | concluído |
| Ortofoto CONDER 2010 (apoio à interpretação) | notebook 01 | concluído |
| **Rótulos e tiles** | **notebook 02 (este)** | **em andamento** |
| Treinamento, inferência e avaliação | notebook 03 | a fazer — Aula 8 |
""")

md("""
## 1. Procedimento da Aula 5 e ajustes deste projeto

Na Aula 5, os rótulos partem de **polígonos vetoriais**. Eles são convertidos em máscara binária (classe = 1, fundo = 0)
com `geoai.vector_to_raster(..., reference_raster=...)` e recortados em blocos com `geoai.export_geotiff_tiles`, que
grava as pastas `images/` e `labels/`. Este notebook segue esse caminho, com os ajustes abaixo.

| Item | Exemplos da aula | Neste notebook | Motivo |
|---|---|---|---|
| Imagem | NAIP/ortofotos de 8 bits, 0,6 m | CBERS-4A de 10 bits (DN 0–1023), 8 m | dado do projeto |
| Escala dos valores | já em 0–255 | conversão linear DN × 255/1023 para 8 bits | o `geoai` divide a imagem por 255 no treino e na inferência |
| Rótulos | edificações do OSM (prontos) | polígonos de areia digitalizados no QGIS | não há base pronta de areia para a cena de 2021 |
| `tile_size` / `stride` | 512 / 384 ou 256 / 128 | **128 / 128** | cena pequena (3019 × 2676 px) e feições estreitas; sem sobreposição (ver abaixo) |
| Divisão dos dados | `val_split=0.2` aleatório no treino; a Aula 5 **recomenda** divisão espacial, sem código | zona de **teste** separada ao longo da costa, com faixa de descarte | evitar que tiles vizinhos (quase iguais) estejam no treino e no teste |

**Sobre o tamanho do tile.** Um tile de 128 px cobre 1 km × 1 km na CBERS. Tiles de 512 px (4 km) dariam só cerca de
30 blocos na cena inteira, e a faixa de areia ocuparia uma fração mínima de cada um. 128 é múltiplo de 32, como exige a
U-Net com encoder ResNet.

**Sobre a sobreposição.** No notebook 03, o `geoai.train_segmentation_model` separa a validação **sorteando tiles**
(`val_split`). Se os tiles se sobrepusessem (`stride < tile_size`), os mesmos pixels poderiam cair no treino e na
validação. Com `stride = tile_size`, isso não acontece, exceto na última linha e na última coluna, que o `geoai` recua para
dentro da imagem. A autocorrelação espacial entre tiles vizinhos continua existindo. Por isso a avaliação final é feita
na zona de teste, separada espacialmente.
""")

md("""
## 2. Ambiente

Mesmo ambiente do notebook 01. No VS Code, use o kernel do ambiente conda `geoai` **ativado**. No Colab, execute as duas
células abaixo. GPU não é necessária nesta etapa.
""")

code('''
# Instala apenas o que estiver faltando (no Colab, normalmente o geoai).
import sys, importlib.util, subprocess

IN_COLAB = importlib.util.find_spec("google.colab") is not None
pacotes = {"geoai": "geoai-py", "geopandas": "geopandas", "rasterio": "rasterio", "matplotlib": "matplotlib"}
faltando = [pip for modulo, pip in pacotes.items() if importlib.util.find_spec(modulo) is None]
if faltando:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", *faltando])
print("Executando no Colab:", IN_COLAB, "| instalados agora:", faltando or "nenhum")
''')

code('''
if IN_COLAB:
    from google.colab import drive
    drive.mount("/content/drive")
''')

md("""
## 3. Configuração

* `ROTULOS` — GeoPackage com os polígonos de areia digitalizados (protocolo na seção 4).
* `TAMANHO_TILE` e `PASSO` — tamanho dos tiles e deslocamento entre eles, em pixels (seção 1).
* `AZIMUTE_COSTA` — direção geral da linha de costa na cena. Medida entre as extremidades da praia no recorte,
  (569,6 km E; 8566,3 km N) e (591,5 km E; 8587,0 km N), dá cerca de 45°.
* `FRACAO_TESTE` — fração dos tiles com areia reservada para teste, contada a partir da extremidade `LADO_TESTE`.
* `FAIXA_DESCARTE` — largura, em metros, da faixa entre treino e teste cujos tiles são descartados.
""")

code('''
from pathlib import Path
import os, json, shutil

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from shapely.geometry import box
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import geoai

# --- Caminhos (mesma pasta de dados do notebook 01) ----------------------------
if IN_COLAB:
    PASTA_DADOS = Path("/content/drive/MyDrive/sensoriamento_remoto")
else:
    PASTA_DADOS = Path(os.environ.get("GEOAI_FAIXA_DADOS",
                                      Path.home() / "OneDrive" / "Mestrado" / "sensoriamento_remoto"))
TIFF = PASTA_DADOS / "cbers_recortado.tiff"                  # CBERS-4A RGB (3-2-1), DN de 10 bits
ROTULOS = PASTA_DADOS / "rotulos" / "areia_cbers_2021.gpkg"  # polígonos digitalizados no QGIS
CAMADA_AREIA = "areia"                                       # camada de polígonos de areia (class = 1)
CAMADA_EXCLUIR = "excluir"                                   # camada opcional: áreas sem interpretação segura

SAIDA = PASTA_DADOS / "preparacao"
CBERS_8BIT = SAIDA / "cbers_recortado_8bit.tif"
MASCARA = SAIDA / "mascara_areia.tif"

# --- Tiles e divisão espacial ---------------------------------------------------------
TAMANHO_TILE = 128     # px (1 km na CBERS)
PASSO = 128            # px; igual ao tamanho = sem sobreposição
PASTA_TILES = SAIDA / f"tiles_{TAMANHO_TILE}"
AZIMUTE_COSTA = 45     # graus a partir do norte; direção SO -> NE da linha de costa na cena
FRACAO_TESTE = 0.20    # 20% dos tiles com areia, na extremidade LADO_TESTE, para teste
LADO_TESTE = "nordeste"  # extremidade da costa usada como teste: "nordeste" ou "sudoeste"
FAIXA_DESCARTE = 1024  # m (= 1 tile) entre treino e teste

SAIDA.mkdir(parents=True, exist_ok=True)
print("Pasta de dados:", PASTA_DADOS)
''')

md("""
## 4. Protocolo de digitalização dos rótulos (QGIS)

A Aula 5 parte de polígonos prontos (edificações do OSM). Para a areia na data da cena, eles precisam ser **digitalizados**.
O protocolo abaixo torna o rótulo reproduzível.

**Definição da classe.** Classe 1 = **toda areia exposta**: faixa de praia (da linha d'água no momento da imagem até o
início da vegetação ou da ocupação), dunas sem cobertura vegetal (por exemplo, Abaeté) e outros areais.
Todo o resto é fundo (0): água, vegetação (inclusive sobre dunas fixadas), áreas urbanas, solo exposto não arenoso,
estradas e nuvens.

**Referência de data.** Os polígonos descrevem a **CBERS de 09/02/2021**. A ortofoto de 2010 só ajuda a reconhecer
feições e limites. Se as duas divergirem, por exemplo numa linha de costa diferente ou num areal que virou loteamento,
**vale o que se vê na CBERS**.

**Passo a passo:**
1. No QGIS, abra `cbers_recortado.tiff` e o mosaico `conder_rms_2010/conder_rms_2010_*.tif` (notebook 01).
2. *Camada ▸ Criar camada ▸ Nova camada GeoPackage*: arquivo `rotulos/areia_cbers_2021.gpkg`, camada `areia`, geometria
   **Polígono**, SRC **EPSG:32724**, campo **`class`** do tipo número inteiro.
3. Digitalize sobre a CBERS em escala próxima de 1:10 000, ligando o *snapping* entre feições para evitar sobreposições.
   Preencha `class = 1` em todos os polígonos.
4. **Rotule toda a areia da cena.** O que ficar sem polígono vira fundo (0) e ensina ao modelo que aquilo **não** é areia.
5. Opcional: crie no mesmo GeoPackage a camada **`excluir`** (polígonos), para áreas sem interpretação segura, como
   nuvens ou sombras sobre possíveis dunas. Tiles que tocarem essas áreas são descartados.
6. Salve as edições e execute as células abaixo.
""")

md("""
## 5. Conversão da CBERS para 8 bits

**➜ Ajuste:** o `geoai` normaliza a imagem dividindo por 255, tanto no treinamento (`train_segmentation_model`) quanto
na inferência (`semantic_segmentation`), o que pressupõe dados de 8 bits. A CBERS deste projeto tem DN de 10 bits
(máximo 1023). A conversão usada é **linear e global**: DN × 255/1023, igual para as três bandas.

Não se usa realce por percentis. Ele saturaria nuvens, telhados e areia no mesmo valor e apagaria justamente a diferença
de brilho que separa essas feições. A grade, o SRC e os limites são mantidos.
""")

code('''
with rasterio.open(TIFF) as src:
    dn = src.read()
    perfil = src.profile
    print(f"CBERS original: {src.width} × {src.height} px | {src.dtypes[0]} | DN {dn.min()}–{dn.max()} | {src.crs}")

if dn.max() > 1023:
    raise ValueError("Valores acima de 1023: a conversão 10 → 8 bits não se aplica a este arquivo.")

img8 = np.round(dn.astype("float32") * 255 / 1023).astype("uint8")
perfil.update(dtype="uint8", nodata=None, compress="deflate", tiled=True, blockxsize=256, blockysize=256)
with rasterio.open(CBERS_8BIT, "w", **perfil) as dst:
    dst.write(img8)
print("CBERS 8 bits salva:", CBERS_8BIT.name, "| valores", img8.min(), "–", img8.max())
''')

md("""
## 6. Leitura e conferência dos rótulos

Antes de rasterizar, o arquivo é verificado: SRC, geometrias válidas, valor de `class`, posição dentro da cena e
sobreposições. Se o GeoPackage ainda não existir, a execução para aqui com uma mensagem.
""")

code('''
if not ROTULOS.exists():
    raise FileNotFoundError(f"Rótulos ainda não digitalizados: {ROTULOS}\\nSiga o protocolo da seção 4.")

areia = gpd.read_file(ROTULOS, layer=CAMADA_AREIA)
with rasterio.open(CBERS_8BIT) as ref:
    crs_ref, limites_ref, transform_ref, forma_ref = ref.crs, ref.bounds, ref.transform, (ref.height, ref.width)

problemas = []
if areia.crs is None or areia.crs.to_epsg() != crs_ref.to_epsg():
    problemas.append(f"SRC dos rótulos ({areia.crs}) diferente da CBERS ({crs_ref}).")
if "class" not in areia.columns:
    problemas.append("Campo 'class' ausente.")
elif set(areia["class"].dropna().unique()) != {1}:
    problemas.append(f"Valores de 'class' diferentes de 1: {sorted(areia['class'].unique())}")
if areia.empty:
    problemas.append("Camada sem polígonos.")
if problemas:
    raise ValueError("\\n".join(problemas))

# Geometrias inválidas (autointerseção etc.) são corrigidas com make_valid
invalidas = (~areia.is_valid).sum()
if invalidas:
    areia["geometry"] = areia.make_valid()
area_total = areia.union_all().area
sobreposicao = areia.area.sum() - area_total
fora = (~areia.within(box(*limites_ref))).sum()   # polígonos que saem do retângulo da cena

print(f"Polígonos: {len(areia)} | área total: {area_total/1e6:.2f} km² ({area_total/64:.0f} pixels CBERS)")
print(f"Geometrias corrigidas: {invalidas} | área sobreposta entre polígonos: {sobreposicao:.0f} m²")
print(f"Polígonos que ultrapassam a cena: {fora}")

excluir = None
try:
    excluir = gpd.read_file(ROTULOS, layer=CAMADA_EXCLUIR)
    print(f"Áreas excluídas: {len(excluir)} polígonos, {excluir.union_all().area/1e6:.2f} km²")
except Exception:
    print("Camada 'excluir' não encontrada (opcional).")
''')

md("""
## 7. Rasterização: máscara binária na grade da CBERS

Mesma função da Aula 5: `geoai.vector_to_raster`, usando a CBERS de 8 bits como `reference_raster`. Assim, a máscara
herda exatamente a grade (pixel de 8 m, origem e SRC) da imagem. O valor gravado vem do campo `class` (1), e o fundo é 0.
A função recebe a camada de areia já conferida na seção 6, em vez do caminho do arquivo, para que a camada opcional
`excluir` nunca seja rasterizada por engano.

Com `all_touched=False` (padrão), um pixel só é marcado se o seu centro estiver dentro do polígono. Isso evita "engordar"
uma faixa de areia que, em muitos trechos, tem só alguns pixels de largura.
""")

code('''
mascara = geoai.vector_to_raster(
    areia,                     # camada 'areia' conferida (GeoDataFrame)
    str(MASCARA),
    reference_raster=str(CBERS_8BIT),
    attribute_field="class",
)
# Conferência: a máscara deve ter a grade exata da imagem e apenas os valores 0 e 1
with rasterio.open(MASCARA) as m:
    assert m.crs == crs_ref and m.transform == transform_ref and (m.height, m.width) == forma_ref
    mascara = m.read(1)
assert set(np.unique(mascara)) <= {0, 1}, np.unique(mascara)
print(f"Máscara: {mascara.shape[1]} × {mascara.shape[0]} px | areia = {mascara.mean():.2%} da cena "
      f"({mascara.sum()} pixels, {mascara.sum()*64/1e6:.2f} km²)")
''')

code('''
# Visualização: CBERS (realce só para exibir) com a máscara sobreposta
realce = np.clip((img8.astype("float32") - np.percentile(img8, 2)) /
                 (np.percentile(img8, 98) - np.percentile(img8, 2)), 0, 1)
fig, eixos = plt.subplots(1, 2, figsize=(16, 7))
eixos[0].imshow(np.moveaxis(realce, 0, -1))
eixos[0].set_title("CBERS-4A 2021 (8 bits, realce para exibição)")
eixos[1].imshow(np.moveaxis(realce, 0, -1))
eixos[1].imshow(np.ma.masked_equal(mascara, 0), cmap=ListedColormap(["#ffde00"]), alpha=0.8)
if excluir is not None and len(excluir):
    ex = rasterize(excluir.geometry, out_shape=forma_ref, transform=transform_ref)
    eixos[1].imshow(np.ma.masked_equal(ex, 0), cmap=ListedColormap(["#ff0000"]), alpha=0.4)
eixos[1].set_title("Máscara de areia (amarelo) e áreas excluídas (vermelho)")
for e in eixos:
    e.axis("off")
plt.show()
''')

md("""
## 8. Geração dos pares imagem–máscara

Mesma função da Aula 5: `geoai.export_geotiff_tiles`, recebendo a máscara **raster** já conferida como `in_class_data`,
a forma "máscaras raster prontas" mostrada na aula. Ela grava `images/tile_XXXXXX.tif` e `labels/tile_XXXXXX.tif` com
a mesma numeração. Todos os tiles são exportados, inclusive os sem areia: mar, cidade, vegetação e dunas vegetadas
ensinam ao modelo o que **não** é areia.
""")

code('''
TODOS = PASTA_TILES / "todos"
if TODOS.exists():
    shutil.rmtree(TODOS)       # gera de novo para refletir a versão atual dos rótulos

resumo = geoai.export_geotiff_tiles(
    in_raster=str(CBERS_8BIT),
    out_folder=str(TODOS),
    in_class_data=str(MASCARA),
    tile_size=TAMANHO_TILE,
    stride=PASSO,
    buffer_radius=0,
    quiet=True,
)
print(f"Tiles gerados: {resumo['total_tiles']} | com areia: {resumo['tiles_with_features']}")
''')

md("""
## 9. Separação espacial entre treino e teste

A Aula 5 recomenda separar os dados por região, mas o material não traz código para isso. **➜ Ajuste:**
1. cada tile recebe uma coordenada **ao longo da costa**, que é a posição do seu centro projetada na direção
   `AZIMUTE_COSTA`;
2. a cena fica dividida em faixas **perpendiculares à costa**, cada uma com seu trecho de praia, o interior e o mar
   correspondentes;
3. a extremidade `LADO_TESTE`, com `FRACAO_TESTE` dos tiles **com areia**, vira a zona de **teste**;
4. tiles a menos de `FAIXA_DESCARTE` da fronteira entre as zonas são **descartados**, assim como os que tocam áreas
   excluídas.

Um azimute fixo, medido sobre a cena, é preferível a calculá-lo a partir dos rótulos: as dunas interiores puxariam a
direção para longe da linha de costa.

O treino e a validação ficam juntos em `treino/`. O `train_segmentation_model` sorteia a validação dentro dessa pasta
(notebook 03). O `teste/` só é usado na avaliação final.
""")

code('''
# 9.1 Posição de cada tile, lida do próprio arquivo
registros = []
for img in sorted((TODOS / "images").glob("*.tif")):
    with rasterio.open(img) as t:
        b = t.bounds
    with rasterio.open(TODOS / "labels" / img.name) as l:
        frac_areia = l.read(1).mean()
    registros.append(dict(tile=img.name, xmin=b.left, ymin=b.bottom, xmax=b.right, ymax=b.top,
                          cx=(b.left + b.right) / 2, cy=(b.bottom + b.top) / 2, frac_areia=frac_areia))
tiles = pd.DataFrame(registros)

# 9.2 Coordenada ao longo da costa: projeção do centro do tile na direção AZIMUTE_COSTA
az = np.radians(AZIMUTE_COSTA)
eixo = np.array([np.sin(az), np.cos(az)])            # vetor unitário (leste, norte)
centro = np.array([(limites_ref.left + limites_ref.right) / 2, (limites_ref.bottom + limites_ref.top) / 2])
tiles["s"] = (tiles[["cx", "cy"]].values - centro) @ eixo   # metros; cresce de SO para NE

# 9.3 Fronteira treino | teste a partir dos tiles com areia
com_areia = tiles[tiles.frac_areia > 0]
if LADO_TESTE == "nordeste":
    corte = np.quantile(com_areia.s, 1 - FRACAO_TESTE)
    no_teste = tiles.s >= corte + FAIXA_DESCARTE / 2
    no_treino = tiles.s <= corte - FAIXA_DESCARTE / 2
else:
    corte = np.quantile(com_areia.s, FRACAO_TESTE)
    no_teste = tiles.s <= corte - FAIXA_DESCARTE / 2
    no_treino = tiles.s >= corte + FAIXA_DESCARTE / 2
tiles["conjunto"] = np.select([no_teste, no_treino], ["teste", "treino"], "descartado")

# 9.4 Tiles que tocam áreas excluídas
if excluir is not None and len(excluir):
    caixas = gpd.GeoSeries([box(r.xmin, r.ymin, r.xmax, r.ymax) for r in tiles.itertuples()], crs=crs_ref)
    toca = caixas.intersects(excluir.union_all())
    tiles.loc[toca.values, "conjunto"] = "descartado"

print(tiles.groupby("conjunto").agg(tiles=("tile", "size"), com_areia=("frac_areia", lambda f: (f > 0).sum()),
                                    areia_media=("frac_areia", "mean")).round(4))
''')

code('''
# 9.5 Cópia para as pastas finais (images/ e labels/ com nomes pareados) e registro
for conjunto in ["treino", "teste"]:
    for sub in ["images", "labels"]:
        pasta = PASTA_TILES / conjunto / sub
        if pasta.exists():
            shutil.rmtree(pasta)
        pasta.mkdir(parents=True)
    for nome in tiles.loc[tiles.conjunto == conjunto, "tile"]:
        for sub in ["images", "labels"]:
            shutil.copy2(TODOS / sub / nome, PASTA_TILES / conjunto / sub / nome)

tiles.to_csv(PASTA_TILES / "tiles.csv", index=False)
(PASTA_TILES / "parametros.json").write_text(json.dumps(dict(
    tamanho_tile=TAMANHO_TILE, passo=PASSO, fracao_teste=FRACAO_TESTE, lado_teste=LADO_TESTE,
    faixa_descarte_m=FAIXA_DESCARTE, azimute_costa=AZIMUTE_COSTA, corte_m=float(corte),
    conversao_8bit="DN * 255 / 1023", rotulos=ROTULOS.name), indent=2), encoding="utf-8")
for conjunto in ["treino", "teste"]:
    n = len(list((PASTA_TILES / conjunto / "images").glob("*.tif")))
    print(f"{conjunto}: {n} pares em {(PASTA_TILES / conjunto).relative_to(PASTA_DADOS)}")
''')

code('''
# 9.6 Mapa da divisão espacial
cores = {"treino": "#1f77b4", "teste": "#d62728", "descartado": "#7f7f7f"}
fig, ax = plt.subplots(figsize=(10, 9))
ax.imshow(np.moveaxis(realce, 0, -1),
          extent=(limites_ref.left, limites_ref.right, limites_ref.bottom, limites_ref.top))
ax.imshow(np.ma.masked_equal(mascara, 0), cmap=ListedColormap(["#ffde00"]),
          extent=(limites_ref.left, limites_ref.right, limites_ref.bottom, limites_ref.top))
for r in tiles.itertuples():
    ax.add_patch(plt.Rectangle((r.xmin, r.ymin), r.xmax - r.xmin, r.ymax - r.ymin, fill=False,
                               ec=cores[r.conjunto], lw=1.2 if r.frac_areia > 0 else 0.3))
for nome, cor in cores.items():
    ax.plot([], [], color=cor, label=nome)
ax.legend(loc="lower right")
ax.set_title("Divisão espacial dos tiles (contorno grosso = tile com areia)")
ax.axis("off")
plt.show()
''')

md("""
## 10. Conferência visual dos pares (como na Aula 5)

`geoai.display_training_tiles` mostra pares imagem–máscara sorteados. Confira se a areia rotulada coincide com a imagem.
""")

code('''
geoai.display_training_tiles(str(PASTA_TILES / "treino"), num_tiles=6);
''')

md("""
## 11. Considerações e próximas etapas

**Resultado:** a máscara binária de areia na grade da CBERS (`preparacao/mascara_areia.tif`) e os pares imagem–máscara de
128 px em `preparacao/tiles_128/treino` e `preparacao/tiles_128/teste`. O registro de cada tile, com posição,
fração de areia e conjunto, fica em `tiles.csv`.

**Pontos de atenção:**
* **Desbalanceamento:** a areia ocupa uma fração pequena da cena, e a maioria dos tiles não tem areia. No notebook 03 isso
  deve ser considerado, por exemplo com `class_weights` do `train_segmentation_model` e métricas por classe (IoU e F1 da
  areia), e não só a acurácia global.
* **Validação × teste:** a validação sorteada pelo `geoai` tem autocorrelação espacial com o treino. A medida de
  desempenho a reportar é a do conjunto de **teste**, que é espacialmente separado.
* **Mudança de rótulos:** basta salvar o GeoPackage e executar de novo as seções 6 a 10. As pastas de tiles são
  recriadas do zero.

**Notebook 03 — segmentação (Aula 8):** `geoai.train_segmentation_model` (U-Net, encoder ResNet34, `num_channels=3`,
`num_classes=2`) sobre `tiles_128/treino`, inferência com `geoai.semantic_segmentation` na CBERS de 8 bits e avaliação na
zona de teste.
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
nbf.write(nb, destino)
print("Gerado:", destino)
