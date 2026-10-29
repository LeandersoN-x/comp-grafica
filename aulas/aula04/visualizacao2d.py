"""
CCB0941 — Computacao Grafica | Aulas 03 + 04 combinadas
Editor 2D: mundo/tela, window/viewport, zoom/pan/picking e transformacoes.

Integra os dois esqueletos:
  - Aula 03: matrizes 2D (translacao, rotacao, escala), criacao de figuras
    (poligono, circulo, triangulo, retangulo), selecao por picking.
  - Aula 04: separacao MUNDO x TELA, window/viewport, zoom, pan,
    picking via matriz inversa e recorte (Cohen-Sutherland / Sutherland-Hodgman).

Todas as figuras vivem em coordenadas do MUNDO. A cada quadro o programa
transforma mundo -> tela pela matriz window->viewport. Zoom/pan alteram apenas
a window (os objetos nao mudam). O clique do mouse chega em pixels e e
convertido tela->mundo pela matriz inversa (para selecionar figuras ou criar
pontos no mundo).

--------------------------------------------------------------------------
Controles
--------------------------------------------------------------------------
Criacao (modo 0 = selecao):
  0               sai do modo de criacao (volta para selecao)
  1               poligono livre (clique p/ pontos; 1 de novo fecha)
  2               circulo (1o clique = centro, 2o = raio)
  3               triangulo (3 cliques)
  4               retangulo (2 cliques = cantos opostos)

Selecao e transformacao (aplicam-se as figuras selecionadas):
  clique esquerdo    seleciona a figura sob o cursor (modo 0)
  Shift + clique     adiciona/remove da selecao
  C                  limpa a selecao
  Delete             apaga as figuras selecionadas
  setas              transla (-15 px/tecla)
  Q / E              rotaciona (+/-10 graus, anti-horario/horario)
  + / -              escala (1.1x / 0.9x)

Zoom e pan:
  clique direito + arrastar   pan
  Ctrl / Alt  + arrastar      pan (trackpad)
  Shift + setas               pan pelo teclado
  roda do mouse / Z / X       zoom in / out (centrado no cursor)
  V                           volta a vista inicial (reset da window)

ESC                sai
"""

import math

import numpy as np
import pyglet

pyglet.options.dpi_scaling = "stretch"

from pyglet import shapes
from pyglet.window import key, mouse


# ======================================================================
# 1. A JANELA (do SO), O BATCH E AS CAMADAS  (pronto)
# ======================================================================
LARGURA, ALTURA = 640, 480
janela = pyglet.window.Window(LARGURA, ALTURA, caption="Aulas 03+04: mundo/tela + transformacoes")
batch = pyglet.graphics.Batch()

CAMADA_GRADE   = pyglet.graphics.Group(order=0)
CAMADA_CENA    = pyglet.graphics.Group(order=1)
CAMADA_SELECAO = pyglet.graphics.Group(order=2)
CAMADA_HUD     = pyglet.graphics.Group(order=3)


# ======================================================================
# 2. MATRIZES 2D EM COORDENADAS HOMOGENEAS  (Aula 03)
# ======================================================================
# Convencao: ponto = vetor coluna [x, y, 1]^T e p' = M @ p.

def matriz_identidade():
    return np.eye(3)


def matriz_translacao(tx, ty):
    return np.array([
        [1, 0, tx],
        [0, 1, ty],
        [0, 0,  1],
    ], dtype=float)


def matriz_rotacao(theta_rad):
    c, s = math.cos(theta_rad), math.sin(theta_rad)
    return np.array([
        [c, -s, 0],
        [s,  c, 0],
        [0,  0, 1],
    ], dtype=float)


def matriz_escala(sx, sy):
    return np.array([
        [sx, 0,  0],
        [0,  sy, 0],
        [0,  0,  1],
    ], dtype=float)


def aplicar_transformacao(pontos, matriz):
    """Aplica MATRIZ (3x3) a uma lista de pontos (x, y)."""
    pontos_h = np.array([[x, y, 1] for (x, y) in pontos], dtype=float).T   # 3 x N
    res = matriz @ pontos_h
    return [(float(px), float(py)) for (px, py, _) in res.T]


# ======================================================================
# 3. VIEWPORT (tela) e WINDOW (mundo)  (Aula 04)
# ======================================================================
# VIEWPORT: retangulo NA TELA onde a cena aparece. Aqui ocupa uma regiao
# central da janela (deixa uma moldura visivel).
VIEWPORT = (80, 60, 560, 420)

# WINDOW: pedaco do MUNDO exibido. Comeca igual a "razao de aspecto" da
# viewport (640/480 = 4/3), entao no inicio a matriz e a identidade.
WINDOW_INICIAL = (0.0, 0.0, float(LARGURA), float(ALTURA))
window_mundo   = list(WINDOW_INICIAL)


# ======================================================================
# 4. MATRIZ WINDOW -> VIEWPORT  e  TELA <-> MUNDO  (Aula 04)
# ======================================================================
# Ordem (com p' = M @ p):  p_tela = T(vmin) . S . T(-wmin) . p_mundo
#                          (a mais a direita aplica primeiro)

def matriz_window_viewport(window, viewport):
    wxmin, wymin, wxmax, wymax = window
    vxmin, vymin, vxmax, vymax = viewport
    sx = (vxmax - vxmin) / (wxmax - wxmin)
    sy = (vymax - vymin) / (wymax - wymin)
    return np.array([
        [sx, 0, vxmin - sx * wxmin],
        [0, sy, vymin - sy * wymin],
        [0,  0,                     1],
    ], dtype=float)


def mundo_para_tela(pontos):
    return aplicar_transformacao(pontos, matriz_window_viewport(window_mundo, VIEWPORT))


def tela_para_mundo(x, y):
    M  = matriz_window_viewport(window_mundo, VIEWPORT)
    Mi = np.linalg.inv(M)
    return aplicar_transformacao([(x, y)], Mi)[0]


# ======================================================================
# 5. PAN E ZOOM (Aula 04)  — alteram apenas a WINDOW
# ======================================================================
def pan_mundo(dx, dy):
    """Desloca a window por (dx, dy) em unidades do MUNDO."""
    window_mundo[0] += dx
    window_mundo[2] += dx
    window_mundo[1] += dy
    window_mundo[3] += dy


def zoom(fator):
    """Zoom em torno do CENTRO da window. fator>1 aproxima, <1 afasta."""
    wxmin, wymin, wxmax, wymax = window_mundo
    cx = (wxmin + wxmax) / 2.0
    cy = (wymin + wymax) / 2.0
    largura = (wxmax - wxmin) / fator
    altura  = (wymax - wymin) / fator
    window_mundo[0] = cx - largura / 2.0
    window_mundo[2] = cx + largura / 2.0
    window_mundo[1] = cy - altura  / 2.0
    window_mundo[3] = cy + altura  / 2.0


def zoom_no_ponto(fator, x_tela, y_tela):
    """Zoom mantendo fixo o ponto do MUNDO que esta sob o cursor."""
    p_antes = tela_para_mundo(x_tela, y_tela)
    zoom(fator)
    p_depois = tela_para_mundo(x_tela, y_tela)
    # Compensa o "escorrego" do ponto durante o zoom centrado.
    pan_mundo(p_antes[0] - p_depois[0], p_antes[1] - p_depois[1])


# ======================================================================
# 6. RECORTE — Cohen-Sutherland (segmentos) e Sutherland-Hodgman (poligonos)
# ======================================================================
def _codigo_reta(p, window):
    xmin, ymin, xmax, ymax = window
    x, y = p
    code = 0
    if   x < xmin: code |= 1
    elif x > xmax: code |= 2
    if   y < ymin: code |= 4
    elif y > ymax: code |= 8
    return code


def _interseccao_borda(p0, p1, borda, window):
    """Intersecao do segmento p0-p1 com a borda indicada da window."""
    xmin, ymin, xmax, ymax = window
    x0, y0 = p0
    x1, y1 = p1
    if   borda == "left":
        x = xmin; y = y0 + (y1 - y0) * (xmin - x0) / (x1 - x0)
    elif borda == "right":
        x = xmax; y = y0 + (y1 - y0) * (xmax - x0) / (x1 - x0)
    elif borda == "bottom":
        y = ymin; x = x0 + (x1 - x0) * (ymin - y0) / (y1 - y0)
    else:  # top
        y = ymax; x = x0 + (x1 - x0) * (ymax - y0) / (y1 - y0)
    return (x, y)


def clip_segmento_cohen_sutherland(p0, p1, window):
    code0 = _codigo_reta(p0, window)
    code1 = _codigo_reta(p1, window)
    while True:
        if code0 == 0 and code1 == 0:
            return [p0, p1]
        if code0 & code1:
            return []
        code = code0 if code0 else code1
        borda = ("left"   if code & 1 else
                 "right"  if code & 2 else
                 "bottom" if code & 4 else "top")
        if code == code0:
            p0 = _interseccao_borda(p0, p1, borda, window)
            code0 = _codigo_reta(p0, window)
        else:
            p1 = _interseccao_borda(p0, p1, borda, window)
            code1 = _codigo_reta(p1, window)


def _clip_pelo_limite(pontos, window, borda):
    xmin, ymin, xmax, ymax = window
    resultado = []
    n = len(pontos)
    for i in range(n):
        a, b = pontos[i], pontos[(i + 1) % n]
        ax, ay = a
        bx, by = b
        if   borda == "left":   inside_a, inside_b = ax >= xmin, bx >= xmin
        elif borda == "right":  inside_a, inside_b = ax <= xmax, bx <= xmax
        elif borda == "bottom": inside_a, inside_b = ay >= ymin, by >= ymin
        else:                   inside_a, inside_b = ay <= ymax, by <= ymax

        if inside_a and inside_b:
            resultado.append(b)
        elif inside_a and not inside_b:
            resultado.append(_interseccao_borda(a, b, borda, window))
        elif not inside_a and inside_b:
            resultado.append(_interseccao_borda(a, b, borda, window))
            resultado.append(b)
    return resultado


def clip_poligono_sutherland_hodgman(pontos, window):
    if not pontos:
        return []
    poligono = list(pontos)
    for borda in ("left", "right", "bottom", "top"):
        poligono = _clip_pelo_limite(poligono, window, borda)
        if not poligono:
            return []
    return poligono


# ======================================================================
# 7. MODELO DE FIGURAS — tudo em coordenadas do MUNDO  (funde Aula 03 + 04)
# ======================================================================
# Cada figura e um dict:
#   {"tipo": "poligono", "pontos": [(x, y), ...], "cor": (r, g, b)}
#   {"tipo": "circulo",  "centro": (x, y), "raio": r, "cor": (r, g, b)}
#
# Guardar as figuras como dados no MUNDO (e nao como shapes do pyglet) e o que
# permite que zoom/pan/transformacoes funcionem juntos: a cada quadro elas sao
# reconstruidas em pixels depois de passarem pela matriz window->viewport.

figuras              = []   # lista de dicts
figuras_selecionadas = []   # referencias (identidade) a itens de `figuras`

COR_POLIGONO = (240, 140, 40)
COR_CIRCULO  = (46, 204, 113)
COR_TRIANG   = (155, 89, 182)
COR_RETANG   = (52, 152, 219)


def criar_poligono(pontos, cor=COR_POLIGONO):
    figuras.append({"tipo": "poligono", "pontos": list(pontos), "cor": cor})


def criar_circulo(centro, raio, cor=COR_CIRCULO):
    figuras.append({"tipo": "circulo", "centro": tuple(centro), "raio": float(raio), "cor": cor})


def pontos_figura(fig):
    """Lista de pontos (x, y) no MUNDO representando a figura.
    Circulo e aproximado por um poligono de 36 lados (permite recorte e
    transformacao uniformes; gira/escala/pane como qualquer outra figura)."""
    if fig["tipo"] == "poligono":
        return fig["pontos"]
    cx, cy = fig["centro"]
    r = fig["raio"]
    n = 36
    return [(cx + r * math.cos(2 * math.pi * i / n),
             cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def centro_figura(fig):
    if fig["tipo"] == "circulo":
        return fig["centro"]
    pontos = fig["pontos"]
    return (sum(p[0] for p in pontos) / len(pontos),
            sum(p[1] for p in pontos) / len(pontos))


def transformar_figura(fig, M):
    """Aplica M in-place aos dados da figura (em coords. do MUNDO)."""
    if fig["tipo"] == "poligono":
        fig["pontos"] = aplicar_transformacao(fig["pontos"], M)
    else:
        cx, cy = fig["centro"]
        cx2, cy2 = aplicar_transformacao([(cx, cy)], M)[0]
        # Fator de escala linear = sqrt(|det(M_2x2)|)
        det = M[0, 0] * M[1, 1] - M[0, 1] * M[1, 0]
        fig["centro"] = (cx2, cy2)
        fig["raio"]  *= math.sqrt(abs(det))


def ponto_em_figura(px, py, fig):
    if fig["tipo"] == "circulo":
        cx, cy = fig["centro"]
        return math.hypot(px - cx, py - cy) <= fig["raio"]
    # poligono: ray casting
    pontos = fig["pontos"]
    dentro = False
    j = len(pontos) - 1
    for i in range(len(pontos)):
        xi, yi = pontos[i]
        xj, yj = pontos[j]
        if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi) + xi:
            dentro = not dentro
        j = i
    return dentro


def figura_sob_cursor(px, py):
    """Retorna a figura mais recente (top-most) sob o ponto do MUNDO."""
    for fig in reversed(figuras):
        if ponto_em_figura(px, py, fig):
            return fig
    return None


# ======================================================================
# 8. DESENHO — reconstroi tudo a cada atualizacao (mundo -> tela)
# ======================================================================
formas = []   # shapes do pyglet recriados a cada atualizar()


def desenhar_figura(fig):
    """Recorta os pontos da figura na window, converte para tela e cria Polygon."""
    pontos_mundo   = pontos_figura(fig)
    pontos_visiveis = clip_poligono_sutherland_hodgman(pontos_mundo, window_mundo)
    if len(pontos_visiveis) < 3:
        return
    pontos_tela = mundo_para_tela(pontos_visiveis)
    formas.append(shapes.Polygon(*pontos_tela, color=fig["cor"],
                                 batch=batch, group=CAMADA_CENA))


def desenhar_caixa_selecao(fig):
    """Desenha a bounding box da figura em coords. de tela."""
    pontos = pontos_figura(fig)
    if not pontos:
        return
    xs = [p[0] for p in pontos]
    ys = [p[1] for p in pontos]
    (x1, y1), (x2, y2) = mundo_para_tela([(min(xs), min(ys)), (max(xs), max(ys))])
    w, h = x2 - x1, y2 - y1
    formas.append(shapes.Box(x1, y1, w, h, 2, color=(255, 230, 60),
                             batch=batch, group=CAMADA_SELECAO))


def desenhar_pendentes():
    """Marca visual dos cliques em andamento (modos de criacao)."""
    pontos = list(pontos_pendentes)
    if centro_pendente is not None:
        pontos.append(centro_pendente)
    if not pontos:
        return
    for (sx, sy) in mundo_para_tela(pontos):
        formas.append(shapes.Circle(sx, sy, 3, color=(255, 255, 255),
                                    batch=batch, group=CAMADA_SELECAO))
    # Linhas entre pontos consecutivos, somente no modo poligono
    if modo == 1 and len(pontos_pendentes) >= 2:
        for i in range(len(pontos_pendentes) - 1):
            (x1, y1), (x2, y2) = mundo_para_tela(pontos_pendentes[i:i + 2])
            formas.append(shapes.Line(x1, y1, x2, y2, 1, color=(255, 200, 100),
                                      batch=batch, group=CAMADA_SELECAO))


def linha_mundo(p, q, largura, cor, camada):
    """Desenha o segmento p-q do MUNDO, recortado pela window."""
    seg = clip_segmento_cohen_sutherland(p, q, window_mundo)
    if not seg or len(seg) < 2:
        return
    (x1, y1), (x2, y2) = mundo_para_tela(seg)
    formas.append(shapes.Line(x1, y1, x2, y2, largura, color=cor,
                              batch=batch, group=camada))


# Grade do mundo (referencia visual para pan/zoom)
PASSO_GRADE = 40
GRADE_X = (-640, 1280)
GRADE_Y = (-480, 960)


def atualizar():
    """Reconstroi os shapes a partir do estado atual (figuras + window)."""
    for f in formas:
        f.delete()
    formas.clear()

    # Grade
    for gx in range(GRADE_X[0], GRADE_X[1] + 1, PASSO_GRADE):
        cor = (200, 70, 70) if gx == 0 else (55, 55, 60)
        linha_mundo((gx, GRADE_Y[0]), (gx, GRADE_Y[1]),
                    2 if gx == 0 else 1, cor, CAMADA_GRADE)
    for gy in range(GRADE_Y[0], GRADE_Y[1] + 1, PASSO_GRADE):
        cor = (70, 170, 70) if gy == 0 else (55, 55, 60)
        linha_mundo((GRADE_X[0], gy), (GRADE_X[1], gy),
                    2 if gy == 0 else 1, cor, CAMADA_GRADE)

    # Figuras (no MUNDO -> recorte -> tela)
    for fig in figuras:
        desenhar_figura(fig)

    # Selecao (bounding box)
    for fig in figuras_selecionadas:
        desenhar_caixa_selecao(fig)

    # Pontos em andamento
    desenhar_pendentes()

    # Contorno da viewport
    vxmin, vymin, vxmax, vymax = VIEWPORT
    formas.append(shapes.Box(vxmin, vymin, vxmax - vxmin, vymax - vymin, 2,
                             color=(160, 160, 160), batch=batch, group=CAMADA_HUD))

    atualizar_rotulo()


# ======================================================================
# 9. HUD
# ======================================================================
NOME_MODO = {0: "seleção", 1: "polígono", 2: "círculo",
             3: "triângulo", 4: "retângulo"}

rotulo = pyglet.text.Label(
    "", x=8, y=ALTURA - 8, anchor_y="top", font_size=11,
    color=(230, 230, 230, 255), multiline=True, width=LARGURA - 16,
    batch=batch, group=CAMADA_HUD,
)

ultimo_mouse = None


def atualizar_rotulo(x_tela=None, y_tela=None):
    global ultimo_mouse
    if x_tela is not None:
        ultimo_mouse = (x_tela, y_tela)
    wxmin, wymin, wxmax, wymax = window_mundo
    texto = (
        f"window: x [{wxmin:.0f}, {wxmax:.0f}]  y [{wymin:.0f}, {wymax:.0f}]   "
        f"modo: {NOME_MODO.get(modo, '?')}   selecionadas: {len(figuras_selecionadas)}"
    )
    if ultimo_mouse is not None:
        tx, ty = ultimo_mouse
        mx, my = tela_para_mundo(tx, ty)
        texto += f"\nmouse: tela ({tx}, {ty}) -> mundo ({mx:.1f}, {my:.1f})"
    rotulo.text = texto


# ======================================================================
# 10. ESTADO DE INTERACAO (criacao / selecao / transformacao)
# ======================================================================
modo             = 0   # 0 = selecao; 1..4 = modos de criacao
pontos_pendentes = []  # pontos ja clicados (em coords. do MUNDO)
centro_pendente  = None

PASSO_TRANSLACAO = 15
PASSO_ROTACAO    = math.radians(10)
FATOR_ESCALA     = 1.1
FATOR_ZOOM       = 1.2
PASSO_PAN        = 0.1
MODS_PAN         = key.MOD_CTRL | key.MOD_ALT | key.MOD_OPTION


def esta_selecionada(fig):
    return any(f is fig for f in figuras_selecionadas)


def toggle_selecao(fig):
    for i, f in enumerate(figuras_selecionadas):
        if f is fig:
            del figuras_selecionadas[i]
            return
    figuras_selecionadas.append(fig)


def aplicar_a_selecao(M_relativa, usar_pivo=True):
    """Aplica M_relativa a cada figura selecionada. Se usar_pivo, a
    transformacao e composta em torno do centro da propria figura
    (T(c) . M . T(-c)), preservando posicao relativa entre figuras."""
    if not figuras_selecionadas:
        print("Nenhuma figura selecionada.")
        return
    for fig in figuras_selecionadas:
        if usar_pivo:
            cx, cy = centro_figura(fig)
            M = matriz_translacao(cx, cy) @ M_relativa @ matriz_translacao(-cx, -cy)
        else:
            M = M_relativa
        transformar_figura(fig, M)
    atualizar()


# ======================================================================
# 11. EVENTOS
# ======================================================================
@janela.event
def on_draw():
    janela.clear()
    batch.draw()


@janela.event
def on_key_press(simbolo, modificadores):
    global modo, centro_pendente, pontos_pendentes, window_mundo

    # -------- Pan por teclado: Shift + setas ---------------------------
    if modificadores & key.MOD_SHIFT and simbolo in (key.LEFT, key.RIGHT, key.UP, key.DOWN):
        largura = window_mundo[2] - window_mundo[0]
        altura  = window_mundo[3] - window_mundo[1]
        dx = {key.LEFT: -1, key.RIGHT: 1}.get(simbolo, 0) * PASSO_PAN * largura
        dy = {key.DOWN: -1, key.UP:    1}.get(simbolo, 0) * PASSO_PAN * altura
        pan_mundo(dx, dy)
        atualizar()
        return

    # -------- Modos de criacao ----------------------------------------
    if simbolo == key._0:
        modo = 0
        pontos_pendentes.clear()
        centro_pendente = None
        print("Modo: seleção")
        return

    if simbolo == key._1:
        if modo == 1 and len(pontos_pendentes) >= 3:
            criar_poligono(pontos_pendentes)
            pontos_pendentes = []
            modo = 0
            atualizar()
        else:
            modo = 1
            figuras_selecionadas.clear()
            pontos_pendentes = []
            centro_pendente  = None
            print("Modo polígono: clique para adicionar vértices; 1 de novo fecha.")
        return

    if simbolo == key._2:
        modo = 2
        figuras_selecionadas.clear()
        centro_pendente = None
        print("Modo círculo: 1º clique = centro, 2º clique = raio.")
        return

    if simbolo == key._3:
        modo = 3
        figuras_selecionadas.clear()
        pontos_pendentes = []
        print("Modo triângulo: clique em 3 pontos.")
        return

    if simbolo == key._4:
        modo = 4
        figuras_selecionadas.clear()
        centro_pendente = None
        print("Modo retângulo: 2 cliques (cantos opostos).")
        return

    # -------- Zoom / reset de vista -----------------------------------
    if simbolo == key.Z:
        zoom(FATOR_ZOOM);           atualizar(); return
    if simbolo == key.X:
        zoom(1.0 / FATOR_ZOOM);     atualizar(); return
    if simbolo == key.V:
        window_mundo = list(WINDOW_INICIAL); atualizar(); return

    # -------- Selecao --------------------------------------------------
    if simbolo == key.C:
        figuras_selecionadas.clear(); atualizar(); return
    if simbolo == key.DELETE:
        figuras[:] = [f for f in figuras if not esta_selecionada(f)]
        figuras_selecionadas.clear()
        atualizar()
        return

    if simbolo == key.ESCAPE:
        janela.close()
        return

    # -------- Transformacoes (aplicam-se a selecao) -------------------
    nova, pivo = None, True
    if simbolo == key.LEFT:
        nova, pivo = matriz_translacao(-PASSO_TRANSLACAO, 0), False
    elif simbolo == key.RIGHT:
        nova, pivo = matriz_translacao(PASSO_TRANSLACAO, 0), False
    elif simbolo == key.UP:
        nova, pivo = matriz_translacao(0, PASSO_TRANSLACAO), False
    elif simbolo == key.DOWN:
        nova, pivo = matriz_translacao(0, -PASSO_TRANSLACAO), False
    elif simbolo == key.Q:
        nova = matriz_rotacao(PASSO_ROTACAO)
    elif simbolo == key.E:
        nova = matriz_rotacao(-PASSO_ROTACAO)
    elif simbolo in (key.PLUS, key.EQUAL):
        nova = matriz_escala(FATOR_ESCALA, FATOR_ESCALA)
    elif simbolo == key.MINUS:
        nova = matriz_escala(1 / FATOR_ESCALA, 1 / FATOR_ESCALA)

    if nova is not None:
        aplicar_a_selecao(nova, usar_pivo=pivo)


@janela.event
def on_mouse_press(x, y, botao, modificadores):
    global modo, centro_pendente, pontos_pendentes

    if botao != mouse.LEFT:
        return
    # Clique esquerdo + Ctrl/Alt: e para pan (tratado no drag), nao seleciona/cria
    if modificadores & MODS_PAN:
        return

    # Picking: converte pixel -> MUNDO pela matriz INVERSA
    wx, wy = tela_para_mundo(x, y)
    print(f"clique: tela ({x}, {y}) -> mundo ({wx:.2f}, {wy:.2f})")

    # -------- Modo 0: selecao -----------------------------------------
    if modo == 0:
        fig = figura_sob_cursor(wx, wy)
        if modificadores & key.MOD_SHIFT:
            if fig is not None:
                toggle_selecao(fig)
        else:
            figuras_selecionadas.clear()
            if fig is not None:
                figuras_selecionadas.append(fig)
        atualizar()
        return

    # -------- Modos de criacao ----------------------------------------
    if modo == 1:  # poligono livre
        pontos_pendentes.append((wx, wy))
        atualizar()

    elif modo == 2:  # circulo
        if centro_pendente is None:
            centro_pendente = (wx, wy)
        else:
            raio = math.hypot(wx - centro_pendente[0], wy - centro_pendente[1])
            criar_circulo(centro_pendente, raio)
            centro_pendente = None
        atualizar()

    elif modo == 3:  # triangulo
        pontos_pendentes.append((wx, wy))
        if len(pontos_pendentes) == 3:
            criar_poligono(pontos_pendentes, cor=COR_TRIANG)
            pontos_pendentes = []
            modo = 0
        atualizar()

    elif modo == 4:  # retangulo (2 cantos opostos)
        if centro_pendente is None:
            centro_pendente = (wx, wy)
        else:
            x1, y1 = centro_pendente
            x2, y2 = wx, wy
            criar_poligono([(x1, y1), (x2, y1), (x2, y2), (x1, y2)], cor=COR_RETANG)
            centro_pendente = None
        atualizar()


@janela.event
def on_mouse_drag(x, y, dx, dy, botoes, modificadores):
    """Pan pelo mouse: botao direito OU esquerdo + Ctrl/Alt."""
    pan_com_esquerdo = (botoes & mouse.LEFT) and (modificadores & MODS_PAN)
    if (botoes & mouse.RIGHT) or pan_com_esquerdo:
        vxmin, vymin, vxmax, vymax = VIEWPORT
        # (dx, dy) e um vetor em PIXELS: converte-se so pela escala
        unid_por_px_x = (window_mundo[2] - window_mundo[0]) / (vxmax - vxmin)
        unid_por_px_y = (window_mundo[3] - window_mundo[1]) / (vymax - vymin)
        pan_mundo(-dx * unid_por_px_x, -dy * unid_por_px_y)
        atualizar()
    atualizar_rotulo(x, y)


@janela.event
def on_mouse_scroll(x, y, scroll_x, scroll_y):
    if scroll_y:
        passo = max(-1.0, min(1.0, scroll_y))
        zoom_no_ponto(FATOR_ZOOM ** passo, x, y)
        atualizar()


@janela.event
def on_mouse_motion(x, y, dx, dy):
    atualizar_rotulo(x, y)


# ======================================================================
# 12. FIGURAS INICIAIS + LOOP PRINCIPAL
# ======================================================================
# A seta "classica" da Aula 03 (agora em coords. do MUNDO) e o quadrado de
# referencia em (0, 0) — visiveis de imediato, para testar zoom/pan/selecao.
figuras.append({
    "tipo": "poligono",
    "pontos": [(260, 220), (340, 220), (340, 195), (390, 240),
               (340, 285), (340, 260), (260, 260)],
    "cor": (70, 140, 230),
})
figuras.append({
    "tipo": "poligono",
    "pontos": [(0, 0), (40, 0), (40, 40), (0, 40)],
    "cor": (240, 140, 40),
})


if __name__ == "__main__":
    atualizar()
    pyglet.app.run()