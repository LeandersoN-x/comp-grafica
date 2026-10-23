"""
CCB0941 — Computacao Grafica | Aula 04 (M3, 2/3)
Window <-> viewport, zoom/pan e picking — SCAFFOLD

Na Aula 03 o editor desenhava tudo direto em PIXELS: a coordenada de um ponto
da figura era a propria posicao dele na tela. Isso funciona ate o momento em
que voce quer ver a cena de mais perto (zoom) ou olhar para outro lugar (pan)
sem mexer nos objetos. Hoje separamos dois sistemas de coordenadas:

  - MUNDO: onde os objetos vivem (unidades que VOCE escolhe);
  - TELA:  pixels da janela do pyglet.

Um retangulo do mundo, a WINDOW, e mapeado num retangulo da tela, a VIEWPORT,
por uma matriz 3x3 em coordenadas homogeneas, montada por composicao de
translacoes e escala, exatamente como na Aula 03. Zoom e pan NAO mexem nos
objetos: mexem na window. O clique do mouse chega em pixels; para saber em que
ponto do MUNDO o usuario clicou (picking), usamos a matriz INVERSA.

Cuidado com o nome: a "window" deste arquivo (retangulo do mundo) NAO e a
`pyglet.window.Window` (a janela do sistema operacional). Aqui a janela do SO
se chama `janela`, e a window do mundo se chama `window_mundo`.

O esqueleto JA RODA: a window comeca IGUAL a viewport, entao o mapeamento e a
identidade e a cena aparece certa mesmo com os TODOs provisorios. O problema
so aparece quando voce tenta dar zoom/pan. Procure os blocos # TODO.

Conceitos de CG que voce vai exercitar
---------------------------------------
- Mundo x tela; window x viewport ........................... pronto (leitura)
- Pan: transladar a window (em unidades do mundo) ............ pronto (exemplo)
- Matriz window -> viewport (composicao T . S . T) ........... TODO 1
- Picking: tela -> mundo pela matriz INVERSA ................. TODO 2
- Zoom: escalar a window em torno do centro .................. TODO 3
- Zoom em torno do cursor .......................... TODO 4 (opcional)

Requisitos:  pip install pyglet numpy   (ver requirements.txt)
Controles (escolhidos para NAO colidir com as teclas do editor da Aula 03):
  botao direito + arrastar -> pan                        (ja funciona*)
  Ctrl (ou Alt/Option) + arrastar -> pan, para trackpad sem botao direito
  Shift + setas            -> pan pelo teclado           (ja funciona*)
  roda do mouse / Z / X    -> zoom in / out              (depois do TODO 3*)
  clique esquerdo          -> marca o ponto do MUNDO clicado (picking, TODO 2)
                              (sem Ctrl/Alt: com eles o clique e do pan)
  C                        -> apaga as marcas
  V                        -> volta a vista inicial
  ESC                      -> sai
  (*) a window muda (veja o texto no topo), mas a TELA so reage depois do
      TODO 1. Esse descompasso e o primeiro sintoma a observar.
"""

import numpy as np
import pyglet

# HiDPI/Retina: mesma linha das aulas anteriores; precisa vir ANTES da janela.
pyglet.options.dpi_scaling = "stretch"

from pyglet import shapes
from pyglet.window import key, mouse


# ======================================================================
# 1. A JANELA (do sistema operacional) e o BATCH  (pronto)
# ======================================================================
LARGURA, ALTURA = 640, 480
janela = pyglet.window.Window(LARGURA, ALTURA, caption="Aula 04: window <-> viewport")
batch = pyglet.graphics.Batch()

# Camadas de desenho: numero menor e desenhado primeiro (fica atras).
CAMADA_GRADE = pyglet.graphics.Group(order=0)
CAMADA_CENA = pyglet.graphics.Group(order=1)
CAMADA_MARCAS = pyglet.graphics.Group(order=2)
CAMADA_HUD = pyglet.graphics.Group(order=3)


# ======================================================================
# 2. MATRIZES 2D EM COORDENADAS HOMOGENEAS  (prontas, as mesmas da Aula 03)
# ======================================================================
# Convencao da Aula 03: ponto = vetor coluna [x, y, 1]^T e p' = M @ p.

def matriz_identidade():
    return np.eye(3)


def matriz_translacao(tx, ty):
    return np.array([
        [1, 0, tx],
        [0, 1, ty],
        [0, 0, 1],
    ], dtype=float)


def matriz_escala(sx, sy):
    # E o TODO 2 da Aula 03, ja resolvido: hoje ele e ferramenta, nao exercicio.
    return np.array([
        [sx, 0, 0],
        [0, sy, 0],
        [0, 0, 1],
    ], dtype=float)


def aplicar_transformacao(pontos, matriz):
    """Aplica MATRIZ (3x3) a uma lista de pontos (x, y). Igual a da Aula 03."""
    pontos_h = np.array([[x, y, 1] for (x, y) in pontos], dtype=float).T   # 3 x N
    resultado = matriz @ pontos_h                                          # 3 x N
    return [(float(px), float(py)) for (px, py, _) in resultado.T]


# ======================================================================
# 3. A CENA, em coordenadas do MUNDO  (pronta)
# ======================================================================
# A seta da Aula 03, ja posicionada no mundo (centro em (320, 240)). Nada nesta
# secao sabe que existe uma tela: sao so numeros no sistema do mundo.
SETA_MUNDO = [
    (260, 220), (340, 220), (340, 195), (390, 240),
    (340, 285), (340, 260), (260, 260),
]

# Um quadrado de lado 40 com um canto na origem do mundo: serve de referencia
# para ver onde (0, 0) foi parar depois de zoom/pan.
QUADRADO_MUNDO = [(0, 0), (40, 0), (40, 40), (0, 40)]

# Grade do mundo: uma linha a cada PASSO_GRADE unidades, cobrindo uma regiao
# bem maior que a vista inicial (para ter o que ver depois do pan/zoom out).
PASSO_GRADE = 40
GRADE_X = (-640, 1280)
GRADE_Y = (-480, 960)

# Pontos do MUNDO marcados pelo clique esquerdo (ver on_mouse_press).
marcas_mundo = []


# ======================================================================
# 4. WINDOW (no mundo) e VIEWPORT (na tela)
# ======================================================================
# Ambas sao retangulos alinhados aos eixos: (xmin, ymin, xmax, ymax).
#
# VIEWPORT: onde, NA TELA, a cena aparece. Aqui ocupa a janela inteira.
VIEWPORT = (0, 0, LARGURA, ALTURA)

# WINDOW: que pedaco do MUNDO aparece. Comeca IGUAL a viewport: por isso a
# matriz certa, no inicio, e a identidade, e a cena ja aparece no lugar certo
# antes mesmo do TODO 1. Repare que a razao de aspecto (largura/altura) da
# window e a mesma da viewport: 640/480 = 4/3.
WINDOW_INICIAL = (0.0, 0.0, float(LARGURA), float(ALTURA))
window_mundo = list(WINDOW_INICIAL)


def matriz_window_viewport(window, viewport):
    # TODO 1: devolva a matriz 3x3 que leva um ponto do MUNDO (dentro da
    # `window`) para a TELA (dentro da `viewport`). Monte-a por COMPOSICAO,
    # com as funcoes da secao 2, em tres passos:
    #
    #   1. transladar o canto (wxmin, wymin) da window ate a origem;
    #   2. escalar por sx = largura_viewport / largura_window
    #                 sy = altura_viewport  / altura_window;
    #   3. transladar a origem ate o canto (vxmin, vymin) da viewport.
    #
    # PREVEJA antes de escrever: em que ORDEM as tres matrizes aparecem no
    # produto, com a convencao p' = M @ p? (Qual e aplicada primeiro ao ponto?)
    wxmin, wymin, wxmax, wymax = window
    vxmin, vymin, vxmax, vymax = viewport
    sx = (vxmax-vxmin)/(wxmax-wxmin)
    sy = (vymax-vymin)/(wymax-wymin)
    return np.array([
        [sx, 0, vxmin-sx*(wxmin)],
        [0, sy, vymin-sy*(wymin)],
        [0, 0, 1],
    ], dtype=float)

def mundo_para_tela(pontos):
    """Pronto. Aplica a matriz window->viewport atual a uma lista de pontos."""
    return aplicar_transformacao(pontos, matriz_window_viewport(window_mundo, VIEWPORT))


def tela_para_mundo(x, y):
    # TODO 2: PICKING: o mouse entrega (x, y) em PIXELS da tela; devolva o
    # ponto (x, y) correspondente no MUNDO. E o caminho de volta do TODO 1:
    # use a INVERSA da matriz window->viewport (np.linalg.inv) e aplique-a ao
    # ponto (reaproveite aplicar_transformacao).
    #
    # PREVEJA: o provisorio abaixo parece funcionar. Ate quando? Clique num
    # canto do quadrado laranja, de zoom (depois do TODO 3) e clique de novo
    # no MESMO canto. Onde a marca vai parar, e por que?
    M = matriz_window_viewport(window_mundo, VIEWPORT)
    Minversa = np.linalg.inv(M)
    result = aplicar_transformacao([(x,y)], Minversa)
    return result[0]   


def pan_mundo(dx, dy):
    """PRONTO: desloca a WINDOW por (dx, dy) em unidades do MUNDO.

    Os objetos nao mudam: quem anda e a window. Por isso, mover a window para a
    DIREITA faz a cena parecer andar para a ESQUERDA na tela.
    """
    window_mundo[0] += dx
    window_mundo[2] += dx
    window_mundo[1] += dy
    window_mundo[3] += dy


def zoom(fator):
    # TODO 3: ZOOM em torno do CENTRO da window. `fator` > 1 aproxima (a cena
    # parece MAIOR na tela); `fator` < 1 afasta. Altere `window_mundo` (4
    # valores, em unidades do mundo) e mais nada: os objetos nao mudam.
    #
    # Perguntas-guia: para APROXIMAR, a window cresce ou encolhe? O centro da
    # window deve mudar? Por que dividir largura e altura pelo MESMO fator
    # preserva a razao de aspecto (e os objetos nao se deformam)?
    wxmin, wymin, wxmax, wymax = window_mundo
    cx = (wxmin + wxmax) / 2.0
    cy = (wymin + wymax) / 2.0
    largura = (wxmax - wxmin) / fator
    altura = (wymax - wymin) / fator
    
    window_mundo[0] = cx - largura / 2.0
    window_mundo[2] = cx + largura / 2.0
    window_mundo[1] = cy - altura / 2.0
    window_mundo[3] = cy + altura / 2.0

    #print(f"TODO 3: zoom({fator:.2f}) ainda nao implementado")


def zoom_no_ponto(fator, x_tela, y_tela):
    # TODO 4 (OPCIONAL): zoom em torno do ponto sob o CURSOR, como em mapas
    # e editores: o ponto do mundo que estava sob o mouse continua sob o mouse
    # depois do zoom. Dica: e a mesma ideia do "pivo" da rotacao (transladar
    # o pivo para a origem, escalar, transladar de volta), aplicada a window.
    # Precisa do TODO 2 (tela_para_mundo). Enquanto nao fizer, cai no TODO 3.
    zoom(fator)


# ======================================================================
# 5. DESENHO: todo quadro, MUNDO -> (window->viewport) -> TELA -> shapes
# ======================================================================
formas = []   # shapes recriados a cada atualizacao (como na Aula 03)

rotulo = pyglet.text.Label(
    "", x=8, y=ALTURA - 8, anchor_y="top", font_size=11, color=(230, 230, 230, 255),
    batch=batch, group=CAMADA_HUD,
)


def linha_mundo(p, q, largura, cor, camada):
    """Desenha o segmento p-q (em coordenadas do MUNDO)."""
    (x1, y1), (x2, y2) = mundo_para_tela([p, q])
    formas.append(shapes.Line(x1, y1, x2, y2, largura, color=cor, batch=batch, group=camada))


def atualizar():
    """Reconstroi todos os shapes a partir do estado atual (cena + window)."""
    for f in formas:
        f.delete()
    formas.clear()

    # Grade e eixos do mundo.
    for gx in range(GRADE_X[0], GRADE_X[1] + 1, PASSO_GRADE):
        cor = (200, 70, 70) if gx == 0 else (55, 55, 60)     # eixo y em vermelho
        linha_mundo((gx, GRADE_Y[0]), (gx, GRADE_Y[1]), 2 if gx == 0 else 1, cor, CAMADA_GRADE)
    for gy in range(GRADE_Y[0], GRADE_Y[1] + 1, PASSO_GRADE):
        cor = (70, 170, 70) if gy == 0 else (55, 55, 60)     # eixo x em verde
        linha_mundo((GRADE_X[0], gy), (GRADE_X[1], gy), 2 if gy == 0 else 1, cor, CAMADA_GRADE)

    # Objetos da cena: so aqui os pontos do mundo viram pixels.
    formas.append(shapes.Polygon(*mundo_para_tela(QUADRADO_MUNDO), color=(240, 140, 40),
                                 batch=batch, group=CAMADA_CENA))
    formas.append(shapes.Polygon(*mundo_para_tela(SETA_MUNDO), color=(70, 140, 230),
                                 batch=batch, group=CAMADA_CENA))

    # Marcas do picking: guardadas no MUNDO, entao acompanham a cena no zoom/pan.
    # O raio (5) e em PIXELS: marcador de interface nao cresce com o zoom.
    if marcas_mundo:
        for (mx, my) in mundo_para_tela(marcas_mundo):
            formas.append(shapes.Circle(mx, my, 5, color=(255, 230, 60), batch=batch, group=CAMADA_MARCAS))

    # Contorno da viewport (na TELA, fora do pipeline do mundo).
    vxmin, vymin, vxmax, vymax = VIEWPORT
    formas.append(shapes.Box(vxmin, vymin, vxmax - vxmin, vymax - vymin, 2,
                             color=(160, 160, 160), batch=batch, group=CAMADA_HUD))

    atualizar_rotulo()


ultimo_mouse = None   # ultima posicao conhecida do mouse, em pixels da TELA


def atualizar_rotulo(x_tela=None, y_tela=None):
    """HUD em coordenadas de TELA: nao passa pela matriz window->viewport."""
    global ultimo_mouse
    if x_tela is not None:
        ultimo_mouse = (x_tela, y_tela)
    wxmin, wymin, wxmax, wymax = window_mundo
    texto = f"window: x [{wxmin:.0f}, {wxmax:.0f}]  y [{wymin:.0f}, {wymax:.0f}]"
    if ultimo_mouse is not None:
        tx, ty = ultimo_mouse
        mx, my = tela_para_mundo(tx, ty)
        texto += f"   |   mouse: tela ({tx}, {ty})  mundo ({mx:.1f}, {my:.1f})"
    rotulo.text = texto


# ======================================================================
# 6. O LOOP DE EVENTOS
# ======================================================================
FATOR_ZOOM = 1.2      # por tecla / por "clique" da roda
PASSO_PAN = 0.1       # fracao da largura/altura da window por tecla

# Teclas que transformam o arrasto com o botao ESQUERDO em pan. Existem para
# trackpads sem botao direito (notebooks): Ctrl, ou Alt/Option no Mac.
MODS_PAN = key.MOD_CTRL | key.MOD_ALT | key.MOD_OPTION


@janela.event
def on_draw():
    janela.clear()
    batch.draw()


@janela.event
def on_key_press(simbolo, modificadores):
    global window_mundo
    largura = window_mundo[2] - window_mundo[0]
    altura = window_mundo[3] - window_mundo[1]

    # Pan pelo teclado (Shift + setas): passo proporcional ao tamanho da window,
    # para o pan ter a mesma "velocidade" aparente com qualquer zoom.
    if modificadores & key.MOD_SHIFT and simbolo in (key.LEFT, key.RIGHT, key.UP, key.DOWN):
        dx = {key.LEFT: -1, key.RIGHT: 1}.get(simbolo, 0) * PASSO_PAN * largura
        dy = {key.DOWN: -1, key.UP: 1}.get(simbolo, 0) * PASSO_PAN * altura
        pan_mundo(dx, dy)
    elif simbolo == key.Z:
        zoom(FATOR_ZOOM)
    elif simbolo == key.X:
        zoom(1 / FATOR_ZOOM)
    elif simbolo == key.C:
        marcas_mundo.clear()
    elif simbolo == key.V:
        window_mundo = list(WINDOW_INICIAL)
    elif simbolo == key.ESCAPE:
        janela.close()
        return
    else:
        return
    atualizar()


@janela.event
def on_mouse_press(x, y, botao, modificadores):
    # Clique esquerdo "puro" marca um ponto. Com Ctrl/Alt ele inicia um pan
    # (ver on_mouse_drag), entao nao marca nada.
    if botao == mouse.LEFT and not (modificadores & MODS_PAN):
        p = tela_para_mundo(x, y)
        marcas_mundo.append(p)
        print(f"clique: tela ({x}, {y})  ->  mundo ({p[0]:.2f}, {p[1]:.2f})")
        atualizar()


@janela.event
def on_mouse_drag(x, y, dx, dy, botoes, modificadores):
    # PRONTO: pan arrastando com o botao direito (ou com o esquerdo +
    # Ctrl/Alt, para trackpad). O mouse andou (dx, dy)
    # PIXELS; a window deve andar o equivalente em unidades do MUNDO, e no
    # sentido CONTRARIO (arrastar a cena para a direita = mover a window para
    # a esquerda). Repare: (dx, dy) e um DESLOCAMENTO (vetor), nao um ponto:
    # converte-se so pela escala, sem a translacao. E o "vetor usa 0 na
    # terceira coordenada" da Aula 03.
    pan_com_esquerdo = (botoes & mouse.LEFT) and (modificadores & MODS_PAN)
    if (botoes & mouse.RIGHT) or pan_com_esquerdo:
        vxmin, vymin, vxmax, vymax = VIEWPORT
        unid_por_px_x = (window_mundo[2] - window_mundo[0]) / (vxmax - vxmin)
        unid_por_px_y = (window_mundo[3] - window_mundo[1]) / (vymax - vymin)
        pan_mundo(-dx * unid_por_px_x, -dy * unid_por_px_y)
        atualizar()
    atualizar_rotulo(x, y)


@janela.event
def on_mouse_scroll(x, y, scroll_x, scroll_y):
    # Roda de mouse entrega passos inteiros (+1/-1); trackpad entrega muitos
    # passos pequenos e fracionarios. Elevar o fator ao passo (limitado a 1)
    # da um zoom proporcional nos dois casos.
    if scroll_y:
        passo = max(-1.0, min(1.0, scroll_y))
        zoom_no_ponto(FATOR_ZOOM ** passo, x, y)
        atualizar()


@janela.event
def on_mouse_motion(x, y, dx, dy):
    atualizar_rotulo(x, y)


# ======================================================================
# 7. INICIA O LOOP.
# ======================================================================
if __name__ == "__main__":
    atualizar()
    pyglet.app.run()