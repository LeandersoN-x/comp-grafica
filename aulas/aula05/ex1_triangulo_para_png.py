"""
CCB0941 - Computacao Grafica | Aula 05 - Exemplo 1
Um triangulo "na GPU crua" em OpenGL puro, sem biblioteca por cima.

O que e este arquivo
--------------------
E a mesma ideia do apendice da Aula 01 (aulas/aula01/apendice_opengl_triangulo.py),
so que agora escrita com as chamadas do OpenGL, uma a uma, exatamente como
aparecem na aula. Naquele apendice, a biblioteca `moderngl` escondia varias
etapas; aqui NADA esta escondido. Compare os dois arquivos.

Este exemplo NAO abre janela para voce olhar: ele desenha FORA DA TELA e salva
o resultado em um arquivo PNG (triangulo_gpu_puro.png). A saida e uma IMAGEM.
(A janela do GLFW existe, mas fica escondida: o OpenGL so funciona dentro de
um "contexto", e e a janela que cria o contexto.)

As 7 etapas (cada uma e um pedaco da aula)
------------------------------------------
  1. Contexto OpenGL ........ janela escondida + contexto 3.3 core profile
  2. Shaders ................ vertex shader e fragment shader, compilados e linkados
  3. Dados dos vertices ..... um array numpy, 5 floats por vertice (x y r g b)
  4. VBO e VAO .............. Gen -> Bind -> Data, e a receita de leitura (slots)
  5. Framebuffer ............ onde o desenho vai parar (fora da tela)
  6. Desenho ................ UseProgram, BindVertexArray, DrawArrays
  7. Ler os pixels e salvar . glReadPixels -> PNG

Pipeline que a GPU percorre (lembre do diagrama da aula):
  vertices -> vertex shader -> montagem e recorte -> rasterizacao
           -> fragment shader -> testes e mistura -> framebuffer

>>> EXPERIMENTE (sempre PREVENDO antes de rodar) <<<
  a) Troque a cor de um vertice no array `vertices`. Qual e o efeito no meio
     do triangulo? (lembre: o que chega ao fragment shader e INTERPOLADO)
  b) Mova um vertice para fora de [-1, 1]. O que e recortado?
  c) No vertex shader, troque `location = 1` por `location = 2` e rode SEM
     mexer no Python. O que aparece? Por que nao ha mensagem de erro?
  d) Mude o 2o argumento de um glVertexAttribPointer (o numero de componentes).

Requisitos:  pip install glfw PyOpenGL numpy pillow   (ver requirements.txt)
Rode:        python ex1_triangulo_para_png.py   ->  gera triangulo_gpu_puro.png
"""

import ctypes
import sys

import glfw
import numpy as np
from OpenGL.GL import (
    GL_ARRAY_BUFFER, GL_COLOR_ATTACHMENT0, GL_COLOR_BUFFER_BIT,
    GL_COMPILE_STATUS, GL_FALSE, GL_FLOAT, GL_FRAGMENT_SHADER, GL_FRAMEBUFFER,
    GL_FRAMEBUFFER_COMPLETE, GL_LINK_STATUS, GL_PACK_ALIGNMENT, GL_RENDERBUFFER,
    GL_RGB, GL_RGBA8, GL_STATIC_DRAW, GL_TRIANGLES, GL_UNSIGNED_BYTE,
    GL_VERTEX_SHADER,
    glAttachShader, glBindBuffer, glBindFramebuffer, glBindRenderbuffer,
    glBindVertexArray, glBufferData, glCheckFramebufferStatus, glClear,
    glClearColor, glCompileShader, glCreateProgram, glCreateShader,
    glDeleteBuffers, glDeleteFramebuffers, glDeleteProgram,
    glDeleteRenderbuffers, glDeleteShader, glDeleteVertexArrays, glDrawArrays,
    glEnableVertexAttribArray, glFramebufferRenderbuffer, glGenBuffers,
    glGenFramebuffers, glGenRenderbuffers, glGenVertexArrays, glGetProgramInfoLog,
    glGetProgramiv, glGetShaderInfoLog, glGetShaderiv, glLinkProgram,
    glPixelStorei, glReadPixels, glRenderbufferStorage, glShaderSource,
    glUseProgram, glVertexAttribPointer, glViewport,
)
from PIL import Image

LARGURA, ALTURA = 400, 400
SAIDA = "triangulo_gpu_puro.png"


# ----------------------------------------------------------------------
# 1. CONTEXTO OPENGL. O OpenGL e uma maquina de estados: todo o estado (qual
#    buffer esta ligado, qual programa esta em uso...) mora num CONTEXTO, e o
#    contexto e criado junto com uma janela. No pyglet, a janela criava o
#    contexto por nos. Aqui pedimos tudo explicitamente.
#
#    Pedimos o CORE PROFILE 3.3: so a API moderna, sem as funcoes classicas
#    (glBegin/glEnd, glRotatef...), que foram REMOVIDAS nesse perfil.
#
#    No macOS, a Apple so oferece o core profile se pedirmos tambem o modo
#    "forward compatible". Sem essa linha, a janela falha na criacao.
# ----------------------------------------------------------------------
if not glfw.init():
    sys.exit("Falha ao inicializar o GLFW")

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
if sys.platform == "darwin":
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
glfw.window_hint(glfw.VISIBLE, glfw.FALSE)   # janela escondida: so queremos o contexto

janela = glfw.create_window(LARGURA, ALTURA, "ex1", None, None)
if not janela:
    glfw.terminate()
    sys.exit("Falha ao criar a janela/contexto OpenGL")
glfw.make_context_current(janela)            # este contexto passa a ser o "atual"


# ----------------------------------------------------------------------
# 2. OS SHADERS (em GLSL). Dois programinhas que RODAM NA GPU.
#
#    - VERTEX SHADER: roda UMA VEZ POR VERTICE. Seu trabalho e entregar
#      `gl_Position` (a posicao do vertice em clip space; depois a GPU divide
#      por w e cai no NDC, o cubo [-1, 1]).
#      Aqui as posicoes ja chegam em NDC, entao so repassamos.
#      Em 3D e aqui que entram as matrizes model, view e projection.
#
#    - FRAGMENT SHADER: roda UMA VEZ POR FRAGMENTO (candidato a pixel que a
#      rasterizacao gerou). Seu trabalho e devolver a COR.
#
#    Repare nos tres canais de dados:
#      `in`  com layout(location = N)  -> ATRIBUTO de vertice (vem do VBO)
#      `out` do vertex = `in` do fragment (mesmo nome e tipo) -> valor
#            INTERPOLADO pelo rasterizador entre os 3 vertices
#      (`uniform` nao aparece aqui; ele esta no exemplo 3)
#
#    O numero do `location` e a PONTE para o slot configurado no VAO (etapa 4).
# ----------------------------------------------------------------------
VERTEX_SHADER = """
#version 330 core
layout (location = 0) in vec2 aPos;     // atributo: o que chegar pelo slot 0
layout (location = 1) in vec3 aColor;   // atributo: o que chegar pelo slot 1
out vec3 vColor;                        // sai: sera INTERPOLADO
void main() {
    gl_Position = vec4(aPos, 0.0, 1.0); // z = 0, w = 1 (coordenadas homogeneas)
    vColor = aColor;
}
"""

FRAGMENT_SHADER = """
#version 330 core
in vec3 vColor;                         // entra: cor ja interpolada neste fragmento
out vec4 FragColor;                     // sai: cor final (r, g, b, alfa)
void main() {
    FragColor = vec4(vColor, 1.0);
}
"""


def compilar_shader(tipo, fonte):
    """Compila UM shader. SEMPRE consulte o log: sem isso, um erro de digitacao
    no GLSL vira so uma imagem vazia, sem explicacao."""
    shader = glCreateShader(tipo)
    glShaderSource(shader, fonte)
    glCompileShader(shader)
    if not glGetShaderiv(shader, GL_COMPILE_STATUS):
        raise RuntimeError(glGetShaderInfoLog(shader).decode())
    return shader


def criar_programa(fonte_vertex, fonte_fragment):
    """Compila os dois shaders e LINKA num unico PROGRAMA."""
    vs = compilar_shader(GL_VERTEX_SHADER, fonte_vertex)
    fs = compilar_shader(GL_FRAGMENT_SHADER, fonte_fragment)
    programa = glCreateProgram()
    glAttachShader(programa, vs)
    glAttachShader(programa, fs)
    glLinkProgram(programa)
    if not glGetProgramiv(programa, GL_LINK_STATUS):
        raise RuntimeError(glGetProgramInfoLog(programa).decode())
    glDeleteShader(vs)    # depois de linkado, os shaders soltos nao fazem mais falta
    glDeleteShader(fs)
    return programa


programa = criar_programa(VERTEX_SHADER, FRAGMENT_SHADER)


# ----------------------------------------------------------------------
# 3. OS DADOS DOS VERTICES. Um vertice e um PACOTE DE ATRIBUTOS. Aqui, tres
#    vertices; cada um com posicao (x, y) e cor (r, g, b): 5 floats por
#    vertice, INTERCALADOS (interleaved) num unico vetor float32.
#
#      byte:    0    4  |  8   12   16 | 20 ...
#              x0   y0  | r0   g0   b0 | x1 ...
#
#    O `dtype=np.float32` importa: o OpenGL espera floats de 32 bits.
# ----------------------------------------------------------------------
vertices = np.array([
    # x,     y,     r,   g,   b
    -0.6, -0.5,   1.0, 0.0, 0.0,   # vertice 0 (vermelho)
     0.6, -0.5,   0.0, 1.0, 0.0,   # vertice 1 (verde)
     0.0,  0.6,   0.0, 0.0, 1.0,   # vertice 2 (azul)
], dtype=np.float32)


# ----------------------------------------------------------------------
# 4. VBO E VAO.
#
#    VBO = os DADOS (bytes crus na memoria da GPU; nao sabem o que significam).
#    VAO = a RECEITA de leitura (o que cada slot le, e como).
#
#    O ciclo de cada objeto e sempre o mesmo:
#      Gen  -> reserva um NOME (um inteiro); ainda nao ha memoria
#      Bind -> liga o nome ao ALVO; ele vira "o objeto atual" daquele alvo
#      Data -> age no objeto LIGADO (as funcoes nao recebem o nome do objeto!)
#
#    Por isso a ORDEM importa: o VAO precisa estar ligado ANTES de configurar
#    os slots, porque o glVertexAttribPointer GRAVA a configuracao no VAO
#    que estiver ligado naquele instante.
# ----------------------------------------------------------------------
vao = glGenVertexArrays(1)                    # Gen: reserva o nome do VAO
glBindVertexArray(vao)                        # Bind: a partir daqui, o VAO "grava"

vbo = glGenBuffers(1)                         # Gen: reserva o nome do buffer
glBindBuffer(GL_ARRAY_BUFFER, vbo)            # Bind: vbo vira o VBO atual (o alvo da o papel)
glBufferData(GL_ARRAY_BUFFER, vertices.nbytes,
             vertices, GL_STATIC_DRAW)        # Data: aloca na GPU e copia os bytes

# STRIDE = bytes de um vertice INTEIRO (5 floats * 4 bytes = 20); e o mesmo
# para todos os slots deste VBO. OFFSET = onde o atributo comeca DENTRO do
# vertice (posicao em 0, cor em 2 floats = 8 bytes).
stride = 5 * vertices.itemsize

# slot 0: 2 floats a partir do offset 0 (posicao) -> casa com location = 0
glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
glEnableVertexAttribArray(0)

# slot 1: 3 floats a partir do offset 8 (cor) -> casa com location = 1
# (o offset precisa ser um c_void_p, nao um int puro)
glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride,
                      ctypes.c_void_p(2 * vertices.itemsize))
glEnableVertexAttribArray(1)

# Pronto: a "ponte" esta gravada no VAO. Nao existe uma chamada "ligue o shader
# aos dados"; o que casa os dois lados e o NUMERO do slot = o `location`.


# ----------------------------------------------------------------------
# 5. FRAMEBUFFER (fora da tela). E a matriz de pixels onde o desenho vai
#    parar. A janela tem um framebuffer proprio, mas como a nossa esta
#    escondida criamos um nosso: um FBO com um renderbuffer de cor.
# ----------------------------------------------------------------------
fbo = glGenFramebuffers(1)
glBindFramebuffer(GL_FRAMEBUFFER, fbo)

rbo = glGenRenderbuffers(1)
glBindRenderbuffer(GL_RENDERBUFFER, rbo)
glRenderbufferStorage(GL_RENDERBUFFER, GL_RGBA8, LARGURA, ALTURA)  # aloca os pixels
glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0,
                          GL_RENDERBUFFER, rbo)                    # encaixa no FBO

if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
    sys.exit("Framebuffer incompleto")

# glViewport faz o ultimo passo do pipeline: NDC [-1,1] -> pixels. E a mesma
# window -> viewport da Aula 04, com window = [-1,1]^2.
glViewport(0, 0, LARGURA, ALTURA)


# ----------------------------------------------------------------------
# 6. DESENHAR. So agora, depois de toda a preparacao, o triangulo e
#    rasterizado e sombreado pela GPU. Repare como o desenho e curto: o VAO
#    religa de uma vez a receita inteira (VBO, layout e slots).
# ----------------------------------------------------------------------
glClearColor(0.1, 0.1, 0.12, 1.0)             # cor de fundo
glClear(GL_COLOR_BUFFER_BIT)

glUseProgram(programa)                        # "use estes shaders"
glBindVertexArray(vao)                        # "e esta receita de dados"
glDrawArrays(GL_TRIANGLES, 0, 3)              # a draw call: 3 vertices, 1 triangulo


# ----------------------------------------------------------------------
# 7. LER OS PIXELS E SALVAR. glReadPixels devolve os bytes com a origem no
#    canto INFERIOR esquerdo (convencao do OpenGL). Um arquivo de imagem tem a
#    origem no TOPO; por isso invertemos na vertical.
# ----------------------------------------------------------------------
glPixelStorei(GL_PACK_ALIGNMENT, 1)           # linhas sem preenchimento extra
dados = glReadPixels(0, 0, LARGURA, ALTURA, GL_RGB, GL_UNSIGNED_BYTE)
imagem = Image.frombytes("RGB", (LARGURA, ALTURA), bytes(dados))
imagem = imagem.transpose(Image.FLIP_TOP_BOTTOM)
imagem.save(SAIDA)
print(f"Pronto: '{SAIDA}' ({LARGURA}x{ALTURA}).")
print("Compare com o apendice da Aula 01: a mesma imagem, sem nada escondido.")


# ----------------------------------------------------------------------
# Limpeza: apague os objetos DEPOIS de usar (nunca dentro de um loop de
# desenho, onde isso causa erro no quadro seguinte).
# ----------------------------------------------------------------------
glDeleteVertexArrays(1, [vao])
glDeleteBuffers(1, [vbo])
glDeleteFramebuffers(1, [fbo])
glDeleteRenderbuffers(1, [rbo])
glDeleteProgram(programa)
glfw.terminate()
