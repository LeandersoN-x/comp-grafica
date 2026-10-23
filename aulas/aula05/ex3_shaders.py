"""
CCB0941 - Computacao Grafica | Aula 05 - Exemplo 3
Shaders em OpenGL puro: os tres canais de dados (atributo, uniform, interpolado).

O que este arquivo mostra
-------------------------
Um triangulo com uma cor diferente em cada vertice (vermelho, verde, azul).
Os shaders recebem dados por TRES canais:

  canal                    muda a cada...                  neste exemplo
  ---------------------    ------------------------------  -------------------
  `in` (atributo)          VERTICE (vem do VBO)            posicao e cor
  `out` -> `in`            INTERPOLADO no triangulo        vColor
  `uniform`                DRAW CALL (igual para todos)    uFator (brilho)

O ponto central: o VBO tem so 3 cores, mas o fragment shader roda para
milhares de pixels e cada um recebe uma cor DIFERENTE. Quem calcula e o
RASTERIZADOR, que interpola o `out` dos 3 vertices (pesos baricentricos).
O fragment shader NAO interpola nada: ele so recebe o resultado.

Ja o `uniform` e uma variavel global do programa, enviada pela CPU e IGUAL
para todos os vertices e fragmentos de uma draw call. Aqui ele pulsa o brilho
da imagem inteira.

Controles:   ESPACO = liga/desliga a pulsacao do uniform   |   ESC = fecha

>>> EXPERIMENTE (sempre PREVENDO antes de rodar) <<<
  a) Aperte ESPACO. O que muda: a cor de cada vertice, ou o brilho do
     triangulo inteiro? Por que um uniform nao consegue fazer o triangulo
     ficar "meio vermelho, meio azul"?
  b) No fragment shader, troque `vColor * uFator` por `vec3(vPos.x + 0.5, 0, 0)`
     (declare `in vec3 vPos` e repasse a posicao no vertex shader). Por que o
     canto inferior esquerdo fica preto?
  c) Renomeie `vColor` so no fragment shader (ex.: `corX`). O que o log de
     compilacao/link diz? E se mudar o TIPO (vec3 -> vec4)?
  d) Troque o nome do uniform no Python (`"uFator"` por `"uFactor"`). Nao ha
     erro, mas a pulsacao some. Leia o aviso impresso no terminal.
  e) Mude o stride de `6 * itemsize` para `5 * itemsize`. O que acontece com as
     cores? O driver reclama?

Requisitos:  pip install glfw PyOpenGL numpy   (ver requirements.txt)
Rode:        python ex3_shaders.py
"""

import ctypes
import math
import sys

import glfw
import numpy as np
from OpenGL.GL import (
    GL_ARRAY_BUFFER, GL_COLOR_BUFFER_BIT, GL_COMPILE_STATUS, GL_FALSE,
    GL_FLOAT, GL_FRAGMENT_SHADER, GL_LINK_STATUS, GL_STATIC_DRAW, GL_TRIANGLES,
    GL_VERTEX_SHADER,
    glAttachShader, glBindBuffer, glBindVertexArray, glBufferData, glClear,
    glClearColor, glCompileShader, glCreateProgram, glCreateShader,
    glDeleteBuffers, glDeleteProgram, glDeleteShader, glDeleteVertexArrays,
    glDrawArrays, glEnableVertexAttribArray, glGenBuffers, glGenVertexArrays,
    glGetProgramInfoLog, glGetProgramiv, glGetShaderInfoLog, glGetShaderiv,
    glGetUniformLocation, glLinkProgram, glShaderSource, glUniform1f,
    glUseProgram, glVertexAttribPointer, glViewport,
)

LARGURA, ALTURA = 800, 600


# ----------------------------------------------------------------------
# SHADERS. Repare nos tres canais:
#
#   `layout (location = N) in ...`  ATRIBUTO: um valor POR VERTICE, vindo do
#       VBO pelo slot N. O numero do location e a ponte para o slot do VAO.
#
#   `out vec3 vColor` (vertex)  ->  `in vec3 vColor` (fragment): o mesmo NOME
#       e o mesmo TIPO nos dois lados. E assim que um estagio passa dado ao
#       seguinte. O valor chega ao fragment shader INTERPOLADO.
#
#   `uniform float uFator`: variavel global do programa, igual para todos os
#       vertices e fragmentos da draw call, preenchida pela CPU.
# ----------------------------------------------------------------------
VERTEX_SHADER = """
#version 330 core
layout (location = 0) in vec3 aPos;     // slot 0: posicao
layout (location = 1) in vec3 aColor;   // slot 1: cor
out vec3 vColor;                        // sai: sera INTERPOLADO pelo rasterizador
void main() {
    gl_Position = vec4(aPos, 1.0);
    vColor = aColor;                    // sem esta linha, vColor nunca e atribuido
}
"""

FRAGMENT_SHADER = """
#version 330 core
in vec3 vColor;                         // entra: a cor ja INTERPOLADA neste fragmento
uniform float uFator;                   // entra: o mesmo valor para todos os fragmentos
out vec4 FragColor;
void main() {
    FragColor = vec4(vColor * uFator, 1.0);
}
"""


def compilar_shader(tipo, fonte):
    """Compila um shader e CONSULTA O LOG (erro de digitacao no GLSL vira so
    tela preta se voce nao olhar)."""
    shader = glCreateShader(tipo)
    glShaderSource(shader, fonte)
    glCompileShader(shader)
    if not glGetShaderiv(shader, GL_COMPILE_STATUS):
        raise RuntimeError(glGetShaderInfoLog(shader).decode())
    return shader


def criar_programa(fonte_vertex, fonte_fragment):
    """Compila os dois shaders e LINKA num PROGRAMA. E no link que o OpenGL
    confere se o `out` do vertex casa com o `in` do fragment."""
    vs = compilar_shader(GL_VERTEX_SHADER, fonte_vertex)
    fs = compilar_shader(GL_FRAGMENT_SHADER, fonte_fragment)
    programa = glCreateProgram()
    glAttachShader(programa, vs)
    glAttachShader(programa, fs)
    glLinkProgram(programa)
    if not glGetProgramiv(programa, GL_LINK_STATUS):
        raise RuntimeError(glGetProgramInfoLog(programa).decode())
    glDeleteShader(vs)
    glDeleteShader(fs)
    return programa


def localizar_uniform(programa, nome):
    """Pergunta ao programa o ENDERECO (location) de um uniform.

    PEGADINHA CLASSICA: se o nome estiver errado, ou se o compilador removeu o
    uniform por ele nao ser usado, o endereco e -1 e NENHUM erro e lancado.
    A cor simplesmente nao muda. Por isso avisamos aqui."""
    endereco = glGetUniformLocation(programa, nome)
    if endereco == -1:
        print(f"AVISO: uniform '{nome}' nao encontrado (endereco -1). "
              "Nome errado, ou nao usado no shader?")
    return endereco


def redimensionar(janela, largura, altura):
    """glViewport: NDC [-1,1] -> pixels (a window -> viewport da Aula 04).
    Recebe o tamanho em PIXELS do framebuffer (em Retina, maior que a janela)."""
    glViewport(0, 0, largura, altura)


def main():
    # ==================================================================
    # 1. INICIALIZACAO (uma vez)
    # ==================================================================
    if not glfw.init():
        print("Falha ao inicializar o GLFW", file=sys.stderr)
        return 1
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    if sys.platform == "darwin":                 # obrigatorio no macOS
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)

    janela = glfw.create_window(LARGURA, ALTURA, "Aula 05 - Shaders", None, None)
    if not janela:
        print("Falha ao criar a janela GLFW", file=sys.stderr)
        glfw.terminate()
        return 1
    glfw.make_context_current(janela)
    glfw.set_framebuffer_size_callback(janela, redimensionar)
    redimensionar(janela, *glfw.get_framebuffer_size(janela))

    programa = criar_programa(VERTEX_SHADER, FRAGMENT_SHADER)

    # O endereco do uniform e buscado UMA vez, fora do loop.
    end_fator = localizar_uniform(programa, "uFator")

    # ------------------------------------------------------------------
    # DADOS: um vertice e um PACOTE DE ATRIBUTOS, aqui posicao + cor
    # (6 floats por vertice, INTERCALADOS num unico vetor float32).
    #
    #   byte:   0    4    8  |  12   16   20  |  24 ...
    #          x0   y0   z0  |  r0   g0   b0  |  x1 ...
    # ------------------------------------------------------------------
    vertices = np.array([
        # x,    y,   z,     r,   g,   b
        -0.5, -0.5, 0.0,   1.0, 0.0, 0.0,   # vermelho
         0.5, -0.5, 0.0,   0.0, 1.0, 0.0,   # verde
         0.0,  0.5, 0.0,   0.0, 0.0, 1.0,   # azul
    ], dtype=np.float32)

    # ------------------------------------------------------------------
    # VBO (dados) e VAO (receita). Ciclo: Gen -> Bind -> Data. As funcoes de
    # Data agem no objeto LIGADO; por isso o VAO precisa estar ligado ANTES de
    # configurar os slots (o glVertexAttribPointer grava no VAO atual).
    # ------------------------------------------------------------------
    vao = glGenVertexArrays(1)
    glBindVertexArray(vao)

    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

    # STRIDE = bytes de um vertice INTEIRO (6 floats * 4 bytes = 24); e o mesmo
    # para todos os slots do VBO. OFFSET = onde o atributo comeca DENTRO do
    # vertice: posicao em 0, cor em 3 floats = 12 bytes.
    stride = 6 * vertices.itemsize

    # slot 0 = posicao (casa com `location = 0` no vertex shader)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
    glEnableVertexAttribArray(0)

    # slot 1 = cor (casa com `location = 1`)
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride,
                          ctypes.c_void_p(3 * vertices.itemsize))
    glEnableVertexAttribArray(1)

    pulsando = True
    espaco_estava_apertado = False

    # ==================================================================
    # 2. LOOP (todo quadro)
    # ==================================================================
    while not glfw.window_should_close(janela):
        # --- eventos ---
        if glfw.get_key(janela, glfw.KEY_ESCAPE) == glfw.PRESS:
            glfw.set_window_should_close(janela, True)
        espaco_apertado = glfw.get_key(janela, glfw.KEY_SPACE) == glfw.PRESS
        if espaco_apertado and not espaco_estava_apertado:
            pulsando = not pulsando
        espaco_estava_apertado = espaco_apertado

        glClearColor(0.2, 0.3, 0.3, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)

        # --- o UNIFORM: a CPU calcula o valor e envia ---
        # sin(t) vai de -1 a 1; (sin(t) + 1) / 2 vai de 0 a 1.
        fator = (math.sin(glfw.get_time() * 2.0) + 1.0) / 2.0 if pulsando else 1.0

        glUseProgram(programa)        # ANTES do glUniform*: o uniform e enviado
                                      # ao programa ATIVO
        glUniform1f(end_fator, fator) # um valor so; vale para a draw call inteira

        glBindVertexArray(vao)        # religa a receita (VBO, layout, slots)
        glDrawArrays(GL_TRIANGLES, 0, 3)

        glfw.swap_buffers(janela)
        glfw.poll_events()

    # ==================================================================
    # 3. ENCERRAMENTO (depois do loop)
    # ==================================================================
    glDeleteVertexArrays(1, [vao])
    glDeleteBuffers(1, [vbo])
    glDeleteProgram(programa)
    glfw.terminate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
