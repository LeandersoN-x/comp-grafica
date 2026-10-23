"""
CCB0941 — Computacao Grafica | Aula 03 (M3, 1/3)
Editor 2D — transformacoes geometricas via matriz homogenea — SCAFFOLD INICIAL

Este e o PONTO DE PARTIDA do editor 2D que vai crescer ao longo do bloco M3
(hoje: transformacoes; aula 4: sistemas de coordenadas/picking/zoom-pan; aula 5:
recorte). O "esqueleto" (janela, batch, loop de eventos, translacao) esta
PRONTO e FUNCIONA de cara — rode e use as SETAS para mover a figura. O MIOLO que
falta — rotacao, escala e a composicao das transformacoes ao apertar as teclas —
e o que VOCE implementa. Procure os blocos marcados # TODO.

Ideia central (ver o enunciado da atividade): uma figura e uma lista de pontos
(x, y). Para mover/girar/escalar a figura, NAO editamos os pontos um a um — em
vez disso, construimos uma MATRIZ 3x3 (coordenadas homogeneas: cada ponto vira
(x, y, 1)) e multiplicamos a matriz por cada ponto. Varias transformacoes se
COMPOEM multiplicando as matrizes — e a ORDEM da multiplicacao importa (matrizes
nao comutam). A translacao abaixo (`matriz_translacao` + `aplicar_transformacao`)
ja esta pronta como EXEMPLO do padrao a seguir.

Conceitos de CG que voce vai exercitar
---------------------------------------
- Coordenadas homogeneas: (x, y) -> (x, y, 1) ................ pronto (exemplo)
- Matriz de translacao ........................................ pronto (exemplo)
- Matriz de rotacao (em torno da origem) ...................... TODO 1
- Matriz de escala (em torno da origem) ....................... TODO 2
- Composicao de transformacoes (ordem da multiplicacao!) ...... TODO 3

Requisitos:  pip install pyglet numpy   (ver requirements.txt)
Controles:
  setas       -> translada a figura                (ja funciona)
  Q / E       -> rotaciona (anti-horario / horario) (depois do TODO 1 e 3)
  + / -       -> escala (aumenta / diminui)         (depois do TODO 2 e 3)
  R           -> reset (volta a identidade)         (ja funciona)
  ESC         -> sai
"""

import math

import numpy as np
import pyglet

# HiDPI/Retina: mesma linha das Aulas 01 e 02 — precisa vir ANTES da janela.
pyglet.options.dpi_scaling = "stretch"

from pyglet import shapes


# ======================================================================
# 1. A JANELA e o BATCH  (pronto — como nas aulas anteriores)
# ======================================================================
LARGURA, ALTURA = 640, 480
janela = pyglet.window.Window(LARGURA, ALTURA, caption="Aula 03: Editor 2D (transformacoes)")
batch = pyglet.graphics.Batch()


# ======================================================================
# 2. A FIGURA (pronta) — pontos no SISTEMA LOCAL da figura, origem em (0,0)
# ======================================================================
# Uma seta simples, DE PROPOSITO assimetrica: numa figura simetrica (quadrado,
# circulo) uma rotacao errada pode passar despercebida — a seta deixa claro
# "para onde" a figura esta apontando.
PONTOS_LOCAIS = [
    (-60, -20), (20, -20), (20, -45), (70, 0), (20, 45), (20, 20), (-60, 20),
]

# Onde a figura fica NO MUNDO antes de qualquer transformacao do usuario.
CENTRO_MUNDO = (LARGURA / 2, ALTURA / 2)
centro_pendente = None
pontos_pendentes = [] # Lista para acumular pontos de figuras com multiplos cliques
circulos = []
retangulos = []
poligonosNC = []
triangulos = []

dados_poligonos = []
# ======================================================================
# 3. MATRIZES DE TRANSFORMACAO 2D EM COORDENADAS HOMOGENEAS
# ======================================================================
# Cada funcao devolve uma matriz numpy 3x3. Convencao: o ponto e um VETOR
# COLUNA [x, y, 1]^T, e a transformacao e p' = M @ p (M multiplica pela
# esquerda). Angulos em RADIANOS.

def matriz_identidade():
    return np.eye(3)


def matriz_translacao(tx, ty):
    """PRONTO — use como MODELO para as matrizes que faltam (TODO 1 e 2).

    Aplicada a um ponto (x, y, 1), devolve (x + tx, y + ty, 1):

        [ 1  0  tx ]
        [ 0  1  ty ]
        [ 0  0  1  ]
    """
    return np.array([
        [1, 0, tx],
        [0, 1, ty],
        [0, 0, 1],
    ], dtype=float)


def matriz_rotacao(theta_rad):
    # TODO 1 — devolva a matriz 3x3 de rotacao por theta_rad (radianos), em
    # torno da ORIGEM (0,0), sentido anti-horario para theta positivo. Siga o
    # MODELO de matriz_translacao acima.
    #
    #     [ cos θ  -sin θ  0 ]
    #     [ sin θ   cos θ  0 ]
    #     [   0       0    1 ]
    return np.array([
        [math.cos(theta_rad), -math.sin(theta_rad), 0],
        [math.sin(theta_rad), math.cos(theta_rad), 0],
        [0, 0, 1],
    ], dtype=float)


def matriz_escala(sx, sy):
    # TODO 2 — devolva a matriz 3x3 de escala por (sx, sy), em torno da
    # ORIGEM (0,0). Siga o MODELO de matriz_translacao acima.
    #
    #     [ sx  0   0 ]
    #     [ 0   sy  0 ]
    #     [ 0   0   1 ]
    return np.array([
        [sx, 0, 0],
        [0, sy, 0],
        [0, 0, 1],
    ], dtype=float)

# ======================================================================
# 4. Criar figuras
# ======================================================================
# Bloco responsavel pela criação de figuras

def criar_poligonoNC(pontos):
    if len(pontos) >= 3:
        pontos_copia = list(pontos)

        poligono = shapes.Polygon(
            *pontos_copia,
            color=(240, 140, 40),
            batch=batch
        )

        poligonosNC.append(poligono)
        dados_poligonos.append(pontos_copia)


def criar_circulo(cx, cy, raio):
    circulo = shapes.Circle(
        x=cx,
        y=cy,
        radius=raio,
        segments=36,
        color=(46, 204, 113),
        batch=batch
    )
    circulos.append(circulo)

def aplicar_transformacao(pontos, matriz):
    """PRONTO — aplica MATRIZ (3x3) a uma lista de pontos (x, y) 2D.

    Para cada (x, y): monta o vetor homogeneo [x, y, 1], calcula
    matriz @ vetor, e descarta a terceira coordenada do resultado (permanece 1
    numa transformacao afim como estas). Use esta funcao como esta —
    entende-la e o objetivo, nao reescreve-la.
    """
    pontos_h = np.array([[x, y, 1] for (x, y) in pontos]).T   # 3 x N
    resultado = matriz @ pontos_h                              # 3 x N
    return [(px, py) for (px, py, _) in resultado.T]


# ======================================================================
# 5. ESTADO da aplicacao
# ======================================================================
# A transformacao ACUMULADA ate agora. Comeca na identidade (nenhuma
# transformacao do usuario ainda).
transformacao_usuario = matriz_identidade()

poligono = None  # criado em atualizar(), na primeira chamada


def figura_atual():
    """Aplica a transformacao do usuario aos pontos locais, depois posiciona
    a figura no centro da janela. Devolve a lista de pontos no MUNDO."""
    pontos = aplicar_transformacao(PONTOS_LOCAIS, transformacao_usuario)
    cx, cy = CENTRO_MUNDO
    return [(x + cx, y + cy) for (x, y) in pontos]

def determinar_figura(x, y):
    for circulo in reversed(circulos):
        if ponto_no_circulo(
            x, y,
            circulo.x,
            circulo.y,
            circulo.radius
        ):
            print("Caiu em um círculo")
            return circulo
    for poligono, pontos in zip(
        reversed(poligonosNC),
        reversed(dados_poligonos)
    ):
        if ponto_no_poligono(x, y, pontos):
            print("Caiu em um polígono")
            return poligono

    for triangulo in reversed(triangulos):
        if isinstance(triangulo, shapes.Triangle):
            pontos = [
                (triangulo.x, triangulo.y),
                (triangulo.x2, triangulo.y2),
                (triangulo.x3, triangulo.y3)
            ]
            if ponto_no_poligono(x, y, pontos):
                print("Caiu em um triângulo")
                return triangulo
    for retangulo in reversed(retangulos):
        if isinstance(retangulo, shapes.BorderedRectangle):
            if (
                retangulo.x <= x <= retangulo.x + retangulo.width
                and
                retangulo.y <= y <= retangulo.y + retangulo.height
            ):
                print("Caiu em um retângulo")
                return retangulo
    print("Nenhuma figura selecionada")
    return None


def atualizar():
    """Reconstroi o poligono desenhado a partir do estado atual.

    Repare que RECRIAR o Polygon a cada atualizacao (em vez de tentar mover um
    shape existente) e o jeito mais simples de refletir uma transformacao de
    matriz — o preco e recompor os pontos toda vez. Nas proximas aulas
    discutimos alternativas mais eficientes.
    """
    global poligono
    pontos = figura_atual()
    if poligono is not None:
        poligono.delete()
    poligono = shapes.Polygon(*pontos, color=(240, 140, 40), batch=batch)

def ponto_no_circulo(px, py, cx, cy, raio):
    distancia = math.hypot(px - cx, py - cy)

    return distancia <= raio

def ponto_no_poligono(px, py, pontos):

    dentro = False

    j = len(pontos) - 1

    for i in range(len(pontos)):

        xi, yi = pontos[i]
        xj, yj = pontos[j]

        cruza = (
            (yi > py) != (yj > py)
            and
            px < (xj - xi) * (py - yi) / (yj - yi) + xi
        )

        if cruza:
            dentro = not dentro

        j = i

    return dentro




# ======================================================================
# 6. O LOOP DE EVENTOS
# ======================================================================
PASSO_TRANSLACAO = 15              # pixels por tecla
PASSO_ROTACAO = math.radians(10)   # radianos por tecla
FATOR_ESCALA = 1.1                 # multiplicador por tecla


@janela.event
def on_draw():
    janela.clear()
    batch.draw()

figura = -1
@janela.event
def on_key_press(simbolo, modificadores):
    global transformacao_usuario, figura, centro_pendente, pontos_pendentes
    K = pyglet.window.key

    nova = None  # a transformacao ELEMENTAR desta tecla, se houver

    # Translacao — PRONTA, como EXEMPLO do padrao de composicao.
    if simbolo == K.LEFT:
        nova = matriz_translacao(-PASSO_TRANSLACAO, 0)
    elif simbolo == K.RIGHT:
        nova = matriz_translacao(PASSO_TRANSLACAO, 0)
    elif simbolo == K.UP:
        nova = matriz_translacao(0, PASSO_TRANSLACAO)
    elif simbolo == K.DOWN:
        nova = matriz_translacao(0, -PASSO_TRANSLACAO)

    # TODO 3 — ROTACAO e ESCALA: monte `nova` com matriz_rotacao/matriz_escala
    # (depois de implementar os TODOs 1 e 2) para as teclas abaixo.
    elif simbolo == K.Q:
        nova = matriz_rotacao(PASSO_ROTACAO)         
    elif simbolo == K.E:
        nova = matriz_rotacao(-PASSO_ROTACAO)         
    elif simbolo == K.PLUS or simbolo == K.EQUAL:
        nova = matriz_escala(FATOR_ESCALA, FATOR_ESCALA)
    elif simbolo == K.MINUS:
        nova = matriz_escala(1 / FATOR_ESCALA, 1 / FATOR_ESCALA)

    elif simbolo == K._0:
        figura = -1
        print("Saindo do modo de seleção.")

    elif simbolo == K._1:
        if figura == 1:
            if len(pontos_pendentes) >= 3:
                criar_poligonoNC(pontos_pendentes)
                print("Polígono fechado!")
                figura = -1
                pontos_pendentes.clear()

            else:
                print("É necessário colocar pelo menos 3 pontos.")
        else:
            figura = 1
            pontos_pendentes.clear()

            print("Modo polígono ativado.")
            print("Clique na tela para adicionar os pontos.")
            print("Pressione 1 novamente para fechar.")

    elif simbolo == K._2: # Cria circulo
        figura = 2
        centro_pendente = None
        print("Modo 2: Circulo (1º clique centro, 2º clique raio)")
    elif simbolo == K._3: # Cria triangulo
        figura = 3
        pontos_pendentes.clear()
        print("Modo 3: Triangulo (clique em 3 pontos)")
    elif simbolo == K._4: # Cria retangulo
        figura = 4
        centro_pendente = None
        print("Modo 4: Retangulo (1º clique canto inicial, 2º clique canto oposto)")

    elif simbolo == K.R:
        transformacao_usuario = matriz_identidade()
        atualizar()
        return
    elif simbolo == K.ESCAPE:
        janela.close()
        return

    if nova is not None:
        # ATENCAO A ORDEM: `nova @ transformacao_usuario` NAO e o mesmo que
        # `transformacao_usuario @ nova`. Antes de testar Q/E depois de
        # implementa-los, PREVEJA no papel: girar a seta e DEPOIS translada-la
        # da o mesmo resultado que translada-la e DEPOIS girar? (nao — e por
        # isso que a ordem importa). A translacao acima ja usa uma ordem fixa;
        # ao adicionar rotacao/escala, siga a MESMA convencao e justifique na
        # atividade.
        transformacao_usuario = nova @ transformacao_usuario
        atualizar()
        print("M =\n", transformacao_usuario)

figuras_selecionadas = []
@janela.event
def on_mouse_press(x, y, botao, modificadores):
    """Chamado quando um botao do mouse e apertado."""
    global centro_pendente, figura, pontos_pendentes

    if botao == pyglet.window.mouse.LEFT and figura == -1:
        selecionada = determinar_figura(x, y)

        if modificadores & pyglet.window.key.MOD_SHIFT:

            if selecionada is not None:

                if selecionada in figuras_selecionadas:
                    figuras_selecionadas.remove(selecionada)
                    print("Figura removida da seleção.")

                else:
                    figuras_selecionadas.append(selecionada)
                    print("Figura adicionada à seleção.")

        else:
            figuras_selecionadas.clear()

            if selecionada is not None:
                figuras_selecionadas.append(selecionada)
                print("Figura selecionada.")

        print("Total de figuras selecionadas:", len(figuras_selecionadas))

        return



    print(f"clique em ({x}, {y})")

    if figura == 1:

        # Adiciona o ponto clicado
        pontos_pendentes.append((x, y))

        # Desenha o ponto
        marcador = shapes.Circle(
            x=x,
            y=y,
            radius=3,
            color=(255, 255, 255),
            batch=batch
        )

        poligonosNC.append(marcador)

        if len(pontos_pendentes) > 1:

            x_ant, y_ant = pontos_pendentes[-2]

            reta = shapes.Line(
                x_ant,
                y_ant,
                x,
                y,
                2,
                color=(240, 140, 40),
                batch=batch
            )
            poligonosNC.append(reta)

        print(
            f"Ponto {len(pontos_pendentes)} "
            f"adicionado em ({x}, {y})"
    )


    elif figura == 2:
        # Primeiro clique: guarda o centro
        if centro_pendente is None:
            centro_pendente = (x, y)

            # marca visual do centro 
            marcador = shapes.Circle(
                x=x, y=y,
                radius=4,
                color=(255, 255, 255),
                batch=batch
            )
            circulos.append(marcador)
        # Segundo clique: calcula o raio e cria o círculo
        else:
            cx, cy = centro_pendente
            raio = math.hypot(x - cx, y - cy)

            criar_circulo(cx, cy, raio)
            centro_pendente = None

    elif figura == 3:
        # Acumula 3 pontos para criar o triangulo
        pontos_pendentes.append((x, y))
        marcador = shapes.Circle(x=x, y=y, radius=3, color=(255, 255, 255), batch=batch)
        triangulos.append(marcador)

        if len(pontos_pendentes) == 3:
            (x1, y1), (x2, y2), (x3, y3) = pontos_pendentes
            triangulo = shapes.Triangle(x1, y1, x2, y2, x3, y3, color=(155, 89, 182), batch=batch)
            triangulos.append(triangulo)
            pontos_pendentes.clear()

    elif figura == 4:
        # 1º clique: canto inicial | 2º clique: canto oposto
        if centro_pendente is None:
            centro_pendente = (x, y)
            marcador = shapes.Circle(x=x, y=y, radius=3, color=(255, 255, 255), batch=batch)
            retangulos.append(marcador)
        else:
            x1, y1 = centro_pendente
            rx = min(x1, x)
            ry = min(y1, y)
            w = abs(x - x1)
            h = abs(y - y1)

            retangulo = shapes.BorderedRectangle(
                rx, ry, w, h, border=2,
                color=(52, 152, 219), border_color=(155, 155, 155),
                batch=batch
            )
            retangulos.append(retangulo)
            centro_pendente = None

    else: 
        print("Nenhuma opção selecionada, opções: \n [1] Poligono \n [2] Circulo \n [3] Triangulo \n [4] Retangulo\n ")

# ======================================================================
# 7. INICIA O LOOP.
# ======================================================================
if __name__ == "__main__":
    atualizar()          # desenha o estado inicial (identidade)
    pyglet.app.run()