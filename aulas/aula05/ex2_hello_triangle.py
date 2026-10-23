"""
CCB0941 - Computacao Grafica | Aula 05 - Exemplo 2
Hello Triangle em OpenGL puro: um triangulo (VBO + VAO) e um retangulo (VBO + EBO + VAO).

O que este arquivo mostra
-------------------------
O "esqueleto" de todo programa OpenGL moderno, na forma da aula:

  1. Inicializacao (uma vez) ... janela e contexto, shaders, VBO, VAO, EBO
  2. Loop (todo quadro) ........ tratar eventos, limpar, UseProgram, BindVertexArray, Draw, swap
  3. Encerramento .............. apagar os objetos, fechar a janela

Na tela aparecem DOIS objetos, de proposito:

  - o TRIANGULO (esquerda) usa um VBO e glDrawArrays: os vertices sao lidos em
    sequencia;
  - o RETANGULO (direita) usa um VBO e um EBO e glDrawElements: sao 4 posicoes
    distintas, e os INDICES dizem como montar os 2 triangulos.

Cada objeto tem seu proprio VAO. Regra pratica: um VAO para cada combinacao
distinta de layout + VBO + EBO. Aqui os VBOs sao diferentes, entao sao 2 VAOs.

Controles:   W = alterna wireframe (so as arestas)   |   ESC = fecha

>>> EXPERIMENTE (sempre PREVENDO antes de rodar) <<<
  a) Aperte W. Onde esta a diagonal do retangulo? O que ela prova?
  b) No vertex shader, troque `location = 0` por `location = 1` e NAO mexa no
     Python. O que aparece? Por que nao ha mensagem de erro?
     Depois conserte pelo lado do Python (slot 1 no ponteiro e no enable).
  c) Mude `3 * itemsize` (o STRIDE) para `2 * itemsize` no triangulo. O que
     acontece com a forma? O driver reclama?
  d) Em glDrawElements, troque 6 por 3. Qual metade do retangulo some?
  e) Chame glDeleteBuffers DENTRO do loop de desenho. O que acontece no
     segundo quadro?

Requisitos:  pip install glfw PyOpenGL numpy   (ver requirements.txt)
Rode:        python ex2_hello_triangle.py
"""

import ctypes
import sys

import glfw
import numpy as np
from OpenGL.GL import (
    GL_ARRAY_BUFFER, GL_COLOR_BUFFER_BIT, GL_COMPILE_STATUS,
    GL_ELEMENT_ARRAY_BUFFER, GL_FALSE, GL_FILL, GL_FLOAT, GL_FRAGMENT_SHADER,
    GL_FRONT_AND_BACK, GL_LINE, GL_LINK_STATUS, GL_STATIC_DRAW, GL_TRIANGLES,
    GL_UNSIGNED_INT, GL_VERTEX_SHADER,
    glAttachShader, glBindBuffer, glBindVertexArray, glBufferData, glClear,
    glClearColor, glCompileShader, glCreateProgram, glCreateShader,
    glDeleteBuffers, glDeleteProgram, glDeleteShader, glDeleteVertexArrays,
    glDrawArrays, glDrawElements, glEnableVertexAttribArray, glGenBuffers,
    glGenVertexArrays, glGetProgramInfoLog, glGetProgramiv, glGetShaderInfoLog,
    glGetShaderiv, glLinkProgram, glPolygonMode, glShaderSource, glUseProgram,
    glVertexAttribPointer, glViewport,
)

LARGURA, ALTURA = 800, 600


# ----------------------------------------------------------------------
# SHADERS. O menor programa possivel:
#   - o vertex shader RECEBE um atributo (posicao, pelo slot 0) e DEVOLVE
#     gl_Position (obrigatorio);
#   - o fragment shader DEVOLVE a cor. Aqui, laranja para todos os pixels.
# Os dois sao compilados e LINKADOS num unico programa.
# ----------------------------------------------------------------------
VERTEX_SHADER = """
#version 330 core
layout (location = 0) in vec3 aPos;      // o que chegar pelo slot 0
void main() {
    gl_Position = vec4(aPos, 1.0);       // w = 1: e uma posicao
}
"""

FRAGMENT_SHADER = """
#version 330 core
out vec4 FragColor;
void main() {
    FragColor = vec4(1.0, 0.5, 0.2, 1.0);   // laranja
}
"""


def compilar_shader(tipo, fonte):
    """Compila um shader e CONSULTA O LOG. Sem isso, um erro de digitacao no
    GLSL vira so uma tela preta, sem explicacao."""
    shader = glCreateShader(tipo)
    glShaderSource(shader, fonte)
    glCompileShader(shader)
    if not glGetShaderiv(shader, GL_COMPILE_STATUS):
        raise RuntimeError(glGetShaderInfoLog(shader).decode())
    return shader


def criar_programa(fonte_vertex, fonte_fragment):
    """Compila os dois shaders e LINKA num PROGRAMA (checando o log do link)."""
    vs = compilar_shader(GL_VERTEX_SHADER, fonte_vertex)
    fs = compilar_shader(GL_FRAGMENT_SHADER, fonte_fragment)
    programa = glCreateProgram()
    glAttachShader(programa, vs)
    glAttachShader(programa, fs)
    glLinkProgram(programa)
    if not glGetProgramiv(programa, GL_LINK_STATUS):
        raise RuntimeError(glGetProgramInfoLog(programa).decode())
    glDeleteShader(vs)     # depois de linkados, os shaders soltos nao fazem falta
    glDeleteShader(fs)
    return programa


def redimensionar(janela, largura, altura):
    """Chamado pelo GLFW quando a janela muda de tamanho. glViewport faz o
    ultimo passo do pipeline: NDC [-1,1] -> pixels (a window -> viewport da
    Aula 04, com window = [-1,1]^2). Recebe tamanho em PIXELS do framebuffer,
    que em telas Retina e maior que o tamanho da janela."""
    glViewport(0, 0, largura, altura)


def main():
    # ==================================================================
    # 1. INICIALIZACAO (uma vez)
    # ==================================================================
    # Janela e contexto. Pedimos o CORE PROFILE 3.3 (so a API moderna).
    # No macOS e obrigatorio pedir tambem "forward compatible", senao a
    # criacao da janela falha.
    if not glfw.init():
        print("Falha ao inicializar o GLFW", file=sys.stderr)
        return 1
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    if sys.platform == "darwin":
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)

    janela = glfw.create_window(LARGURA, ALTURA, "Aula 05 - Hello Triangle", None, None)
    if not janela:
        print("Falha ao criar a janela GLFW", file=sys.stderr)
        glfw.terminate()
        return 1
    glfw.make_context_current(janela)
    glfw.set_framebuffer_size_callback(janela, redimensionar)
    redimensionar(janela, *glfw.get_framebuffer_size(janela))   # tamanho inicial

    programa = criar_programa(VERTEX_SHADER, FRAGMENT_SHADER)

    # ------------------------------------------------------------------
    # OBJETO 1: O TRIANGULO.  VBO (dados) + VAO (receita).
    #
    # Ciclo de cada objeto: Gen (reserva o nome) -> Bind (liga ao alvo) ->
    # Data (age no objeto LIGADO). As funcoes de Data NAO recebem o nome do
    # objeto; elas agem no que estiver ligado. A ordem importa.
    # ------------------------------------------------------------------
    triangulo = np.array([
        # x,    y,   z
        -0.9, -0.5, 0.0,     # vertice 0
        -0.1, -0.5, 0.0,     # vertice 1
        -0.5,  0.5, 0.0,     # vertice 2
    ], dtype=np.float32)

    vao_tri = glGenVertexArrays(1)               # Gen: nome do VAO
    glBindVertexArray(vao_tri)                   # Bind: o VAO passa a "gravar"

    vbo_tri = glGenBuffers(1)                    # Gen: nome do buffer
    glBindBuffer(GL_ARRAY_BUFFER, vbo_tri)       # Bind: vira o VBO atual
    glBufferData(GL_ARRAY_BUFFER, triangulo.nbytes,
                 triangulo, GL_STATIC_DRAW)      # Data: aloca na GPU e copia

    # slot 0: 3 floats por vertice. STRIDE = bytes de um vertice inteiro
    # (3 floats * 4 bytes = 12). OFFSET = onde o atributo comeca dentro do
    # vertice (0). O offset precisa ser um c_void_p, nao um int puro.
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE,
                          3 * triangulo.itemsize, ctypes.c_void_p(0))
    glEnableVertexAttribArray(0)
    # O slot 0 casa com `layout (location = 0)` do vertex shader.

    # ------------------------------------------------------------------
    # OBJETO 2: O RETANGULO.  VBO + EBO + VAO.
    #
    # Um retangulo sao 2 triangulos = 6 vertices, mas so 4 posicoes
    # distintas. O EBO guarda INDICES: cada vertice compartilhado e guardado
    # (e processado) uma vez so. O EBO fica gravado no VAO.
    #
    #     3 ----- 2
    #     |  \     |        triangulo A: indices 0, 1, 3
    #     |    \   |        triangulo B: indices 1, 2, 3
    #     0 ----- 1
    # ------------------------------------------------------------------
    retangulo = np.array([
        # x,   y,   z
         0.1, -0.5, 0.0,    # 0: inferior esquerdo
         0.9, -0.5, 0.0,    # 1: inferior direito
         0.9,  0.5, 0.0,    # 2: superior direito
         0.1,  0.5, 0.0,    # 3: superior esquerdo
    ], dtype=np.float32)
    indices = np.array([0, 1, 3,
                        1, 2, 3], dtype=np.uint32)

    vao_ret = glGenVertexArrays(1)
    glBindVertexArray(vao_ret)                   # outro VAO: outra receita

    vbo_ret = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo_ret)
    glBufferData(GL_ARRAY_BUFFER, retangulo.nbytes, retangulo, GL_STATIC_DRAW)

    ebo_ret = glGenBuffers(1)                    # EBO e um buffer como o VBO;
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo_ret)   # so muda o ALVO (o papel)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
    # ATENCAO: o EBO e gravado no VAO que esta ligado. NAO desligue o EBO
    # (glBindBuffer(..., 0)) enquanto o VAO ainda estiver ligado.

    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE,
                          3 * retangulo.itemsize, ctypes.c_void_p(0))
    glEnableVertexAttribArray(0)

    glBindVertexArray(0)    # desliga o VAO: nada mais sera gravado por engano

    wireframe = False

    # ==================================================================
    # 2. LOOP (todo quadro)
    # ==================================================================
    w_estava_apertada = False
    while not glfw.window_should_close(janela):
        # --- eventos (teclado) ---
        if glfw.get_key(janela, glfw.KEY_ESCAPE) == glfw.PRESS:
            glfw.set_window_should_close(janela, True)
        w_apertada = glfw.get_key(janela, glfw.KEY_W) == glfw.PRESS
        if w_apertada and not w_estava_apertada:        # so na borda de subida
            wireframe = not wireframe
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE if wireframe else GL_FILL)
        w_estava_apertada = w_apertada

        # --- limpar o framebuffer ---
        glClearColor(0.2, 0.3, 0.3, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)

        # --- desenhar: o loop e curto porque o VAO religa a receita inteira ---
        glUseProgram(programa)                   # "use estes shaders"

        glBindVertexArray(vao_tri)               # receita do triangulo
        glDrawArrays(GL_TRIANGLES, 0, 3)         # draw call 1: 3 vertices em sequencia

        glBindVertexArray(vao_ret)               # receita do retangulo (VBO + EBO)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT,
                       ctypes.c_void_p(0))       # draw call 2: 6 indices do EBO

        # --- trocar os buffers (swap) e processar eventos ---
        glfw.swap_buffers(janela)
        glfw.poll_events()

    # ==================================================================
    # 3. ENCERRAMENTO. Apagar os objetos DEPOIS do loop. Apagar dentro do
    # loop causa erro (1282 invalid operation) no segundo quadro.
    # ==================================================================
    glDeleteVertexArrays(2, [vao_tri, vao_ret])
    glDeleteBuffers(3, [vbo_tri, vbo_ret, ebo_ret])
    glDeleteProgram(programa)
    glfw.terminate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
