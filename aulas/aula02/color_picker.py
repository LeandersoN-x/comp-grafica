"""
CCB0941 — Computacao Grafica | Aula 02 (M2)
ColorPicker — SCAFFOLD INICIAL (a completar)

Este e um PONTO DE PARTIDA MINIMO para a Atividade 02. O "esqueleto" que voce ja
conhece da Aula 01 esta pronto: janela, batch, on_draw e o loop de eventos. O
MIOLO da aplicacao — os tres sliders R, G, B, a cor resultante e o botao de
reset, todos interativos — e o que VOCE vai implementar. Procure os blocos
marcados  # TODO.

O objetivo (ver o enunciado da atividade): construir uma cor RGB definindo, com o
mouse, as tres componentes. A cor na tela e a SOMA das tres intensidades
(processo ADITIVO); cada componente e 1 byte ([0,255] <-> [0,1]).

Conceitos de CG que voce vai exercitar
--------------------------------------
- Modelo de cor RGB e sintese ADITIVA (a cor resultante) .......... atualizar()
- Cada canal e 1 byte: [0,255] <-> [0,1] .......................... TODO 2
- Conversao de coordenada: pixel do mouse -> valor do slider ...... TODO 3
- Loop de eventos e ARRASTAR (press -> drag -> release) ........... TODO 3 e 4

Requisitos:  pip install pyglet   (ver requirements.txt)
Controles (depois de implementar): arraste/clique nos sliders | [ESC] sai
"""

import pyglet

# HiDPI/Retina: garante que a janela use coordenadas logicas iguais ao tamanho
# pedido em QUALQUER monitor (mesma linha da Aula 01). Precisa vir ANTES de
# criar a janela.
pyglet.options.dpi_scaling = "stretch"

from pyglet import shapes
from pyglet.gl import glClearColor


# ======================================================================
# 1. A JANELA e o BATCH  (pronto — como na Aula 01)
# ======================================================================
LARGURA, ALTURA = 520, 380
janela = pyglet.window.Window(LARGURA, ALTURA, caption="Aula 02: ColorPicker (a completar)")
batch = pyglet.graphics.Batch()

# COR DE FUNDO (livre — mude se quiser). glClearColor usa canais em [0,1].
glClearColor(0.16, 0.16, 0.18, 1.0)


# ======================================================================
# 2. HELPER pronto (fornecido)  ->  o clique caiu dentro de um retangulo?
# ======================================================================
# No pyglet, (px,py) do mouse ja vem no mesmo sistema do desenho (origem no
# canto inferior-esquerdo). Entao o teste de "clique dentro do retangulo" e so
# uma comparacao de caixa (bounding box). Use isto para saber se o clique caiu
# sobre um slider ou sobre o botao de reset.
def contem(px, py, x, y, w, h):
    return x <= px <= x + w and y <= py <= y + h


# ======================================================================
# 3. ESTADO da aplicacao
# ======================================================================
# As tres componentes da cor, cada uma em [0, 255]. Comece com um valor fixo; a
# interacao (que voce vai implementar) e quem muda isto.
r, g, b = 128, 128, 128

# TODO 1 — CRIE AS PRIMITIVAS DA CENA (shapes), guardando-as em variaveis/lista
# para poder atualiza-las depois. Voce vai precisar de:
#   * tres "trilhos" (retangulos) para R, G, B e uma "alca"/seletor sobre cada;
#   * um retangulo grande com a COR RESULTANTE (r, g, b);
#   * um "botao" de reset (um retangulo).
# Repare no esquema do enunciado: os retangulos tem uma BORDA CINZA. Como fazer?
# -> shapes.BorderedRectangle(x, y, w, h, border=2, color=..., border_color=...).
#
# Exemplo do PADRAO (para voce comecar — apague/ajuste): um retangulo com a cor
# resultante e borda cinza.


amostra = shapes.BorderedRectangle(190, 60, 140, 70, border=2,
                                   color=(r, g, b), border_color=(155, 155, 155),
                                   batch=batch)

x = 30 # posicao
largura = 457 # largura do retangulo
altura = 30 # altura do retangulo

shapeR = shapes.Rectangle(x, 300, largura, altura, color=(r, 0, 0))
shapeG = shapes.Rectangle(x, 250, largura, altura, color=(0, g, 0))
shapeB = shapes.Rectangle(x, 200, largura, altura, color=(0, 0, b))

# Alças
alcaR = shapes.Rectangle(x, 300, 10, altura, color=(255, 0, 0))
alcaG = shapes.Rectangle(x, 250, 10, altura, color=(0, 255, 0))
alcaB = shapes.Rectangle(x, 200, 10, altura, color=(0, 0, 255))

# Quadrado que mostra a cor
cor = shapes.Rectangle(190, 60, 140, 70, color=(r, g, b))

# Quadrado do reset
resetBTN = shapes.Rectangle(400, 60, 70, 70, color=(r, g, b))
texto_reset = pyglet.text.Label(
    "RESET",
    x=435,
    y=95,
    anchor_x="center",
    anchor_y="center",
    color=(255, 255, 255, 255),
    font_size=12
)

def atualizar(value1,value2,value3):
    """Reflete o ESTADO (r, g, b) na tela e no terminal.

    TODO 2 — faca esta funcao:
      * pintar o retangulo de resultado com (r, g, b);
      * reposicionar cada alca conforme o valor do seu canal
        (x_alca = x_trilho + (valor/255) * largura_trilho);
      * (se tiver textos) atualizar os numeros 0..255.
    Ja imprime no terminal (requisito do enunciado):
    """
    global r, g ,b

    amostra.color = (r, g, b)

    # Atualiza posição das alças
    alcaR.x = x + (r / 255) * largura
    alcaG.x = x + (g / 255) * largura
    alcaB.x = x + (b / 255) * largura
    cor.color = (r,g,b)

    print(f"RGB = ({r:3d}, {g:3d}, {b:3d})")


# ======================================================================
# 4. O LOOP DE EVENTOS
# ======================================================================
@janela.event
def on_draw():
    janela.clear()
    shapeR.draw()
    shapeG.draw()
    shapeB.draw()
    alcaR.draw() 
    alcaG.draw() 
    alcaB.draw() 
    batch.draw()
    cor.draw()
    resetBTN.draw()
    texto_reset.draw()


@janela.event
def on_mouse_press(x_mouse, y_mouse, botao, modificadores):
    # TODO 3 — TRATE O CLIQUE:
    #   * descubra em qual slider (ou no botao de reset) o clique caiu — use
    #     contem(x, y, ...);
    #   * se caiu num slider, converta o x do mouse no novo valor do canal
    #     (regra de tres: valor01 = (x - x_trilho) / largura_trilho, em [0,1];
    #      depois valor255 = int(valor01 * 255)) e atualize r/g/b;
    #   * se caiu no botao de reset, zere (ou branqueie) a cor;
    #   * chame atualizar() no fim.
    global r, g, b

    if contem(x_mouse, y_mouse, x, 300, largura, altura):

        r = int((x_mouse - x) / largura * 255)

        if r < 0:
            r = 0

        if r > 255:
            r = 255


    # --------------------------------------------------
    # G
    # --------------------------------------------------

    elif contem(x_mouse, y_mouse, x, 250, largura, altura):

        g = int((x_mouse - x) / largura * 255)

        if g < 0:
            g = 0

        if g > 255:
            g = 255


    # --------------------------------------------------
    # B
    # --------------------------------------------------

    elif contem(x_mouse, y_mouse, x, 200, largura, altura):

        b = int((x_mouse - x) / largura * 255)

        if b < 0:
            b = 0

        if b > 255:
            b = 255


    # --------------------------------------------------
    # RESET
    # --------------------------------------------------

    elif contem(x_mouse, y_mouse, 400, 60, 70, 70):

        r = 0
        g = 0
        b = 0

    atualizar(r,g,b)
    


# TODO 4 (OPCIONAL — arrastar): implemente on_mouse_drag para o seletor SEGUIR o
# mouse enquanto o botao esta pressionado. Guarde qual slider esta "ativo" no
# on_mouse_press e limpe-o no on_mouse_release. Consulte a doc do pyglet para as
# assinaturas de on_mouse_drag(x, y, dx, dy, botoes, mods) e on_mouse_release.


@janela.event
def on_key_press(simbolo, modificadores):
    if simbolo == pyglet.window.key.ESCAPE:
        janela.close()


# ======================================================================
# 5. INICIA O LOOP.
# ======================================================================
if __name__ == "__main__":
    atualizar(r,g,b)          # sincroniza o estado inicial (e imprime no terminal)
    pyglet.app.run()

