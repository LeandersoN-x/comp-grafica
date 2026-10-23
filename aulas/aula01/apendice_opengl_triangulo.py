"""
CCB0941 — Computacao Grafica | Aula 01 (M1) — APENDICE OPCIONAL
Um triangulo "na GPU crua": o mesmo desenho, mas com OpenGL moderno explicito.

Para que serve este arquivo
---------------------------
NAO e a atividade da Aula 01 (essa e o primeira_janela.py, em pyglet). Isto e
um APENDICE para voce ver o CONTRASTE: no scaffold, uma unica linha

    shapes.Triangle(...)

desenha um triangulo. Aqui embaixo estao as ~7 etapas que essa linha esconde e
que a GPU realmente exige. E o "como" que so vamos escrever de verdade em M6,
depois do rasterizador em software. Ver de longe agora ajuda a valorizar por que
comecamos pelo alto nivel: OpenGL de GPU e poderoso, mas e MUITA cerimonia.

Cada etapa abaixo e um estagio do pipeline (ver o slide "pipeline grafico"):
  vertices -> (vertex shader) -> montagem -> rasterizacao -> (fragment shader) -> framebuffer

Diferenca de veiculo, nao de teoria: aqui NAO ha janela. Criamos um contexto
"standalone", desenhamos num framebuffer fora da tela e salvamos o resultado em
PNG. Isso e proposital: e mais robusto (nao depende de display) e reforca o tema
do curso — a saida e uma IMAGEM.

Requisitos:  pip install moderngl pillow   (ver requirements-apendice.txt)
Rode:        python apendice_opengl_triangulo.py   ->  gera triangulo_gpu.png
"""

import array
import moderngl
from PIL import Image

LARGURA, ALTURA = 400, 400
SAIDA = "triangulo_gpu.png"

# ----------------------------------------------------------------------
# 1. CONTEXTO OPENGL. No pyglet, a janela criava o contexto por nos. Aqui,
#    sem janela, pedimos um contexto "standalone" (offscreen).
# ----------------------------------------------------------------------
ctx = moderngl.create_standalone_context()

# ----------------------------------------------------------------------
# 2. OS SHADERS (em GLSL, a linguagem de shading do OpenGL). Sao dois
#    programinhas que RODAM NA GPU — a parte que o pyglet escondia de nos:
#
#    - VERTEX SHADER: executa uma vez POR VERTICE. Seu trabalho e definir a
#      posicao final do vertice (gl_Position). Aqui as posicoes ja chegam em
#      NDC (coordenadas normalizadas de dispositivo, de -1 a +1) para
#      simplificar; em 3D e aqui que entram as matrizes de transformacao (M5).
#      Ele tambem repassa a cor para o proximo estagio.
#
#    - FRAGMENT SHADER: executa uma vez POR FRAGMENTO (candidato a pixel gerado
#      pela rasterizacao). Seu trabalho e devolver a COR daquele pixel.
#
#    Detalhe bonito: a cor (v_color) e INTERPOLADA entre os tres vertices ao
#    longo do triangulo. Isso e, em essencia, o sombreamento de Gouraud (M6).
# ----------------------------------------------------------------------
VERTEX_SHADER = """
#version 330
in vec2 in_pos;      // entra: posicao do vertice (x, y) em NDC
in vec3 in_color;    // entra: cor do vertice (r, g, b)
out vec3 v_color;    // sai: cor a ser interpolada para os fragmentos
void main() {
    gl_Position = vec4(in_pos, 0.0, 1.0);  // z=0, w=1 (coord. homogeneas)
    v_color = in_color;
}
"""

FRAGMENT_SHADER = """
#version 330
in vec3 v_color;     // entra: cor ja interpolada neste fragmento
out vec4 f_color;    // sai: cor final do pixel (r, g, b, alfa)
void main() {
    f_color = vec4(v_color, 1.0);
}
"""

program = ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=FRAGMENT_SHADER)

# ----------------------------------------------------------------------
# 3. OS DADOS DOS VERTICES. Tres vertices; para cada um: posicao (x, y) e cor
#    (r, g, b) — 5 floats por vertice, "intercalados" (interleaved).
#    Compare: no scaffold isso era so tres pares de coordenadas num Triangle.
# ----------------------------------------------------------------------
vertices = array.array("f", [
    # x,     y,     r,   g,   b
    -0.6, -0.5,   1.0, 0.0, 0.0,   # vertice 0 (vermelho)
     0.6, -0.5,   0.0, 1.0, 0.0,   # vertice 1 (verde)
     0.0,  0.6,   0.0, 0.0, 1.0,   # vertice 2 (azul)
])

# ----------------------------------------------------------------------
# 4. VBO + VAO. O VBO (Vertex Buffer Object) copia os dados para a memoria da
#    GPU. O VAO (Vertex Array Object) DESCREVE o layout desses bytes para os
#    "in_" do shader: aqui, "2f 3f" = 2 floats (in_pos) + 3 floats (in_color).
#    Toda essa fiacao de layout tambem estava escondida no shapes.
# ----------------------------------------------------------------------
vbo = ctx.buffer(vertices.tobytes())
vao = ctx.vertex_array(program, [(vbo, "2f 3f", "in_pos", "in_color")])

# ----------------------------------------------------------------------
# 5. FRAMEBUFFER (fora da tela). E a matriz de pixels onde vamos desenhar —
#    o mesmo conceito de framebuffer da aula, agora explicito e nas nossas maos.
# ----------------------------------------------------------------------
fbo = ctx.simple_framebuffer((LARGURA, ALTURA))
fbo.use()
fbo.clear(0.1, 0.1, 0.12, 1.0)   # cor de fundo (equivale ao janela.clear())

# ----------------------------------------------------------------------
# 6. DESENHAR. So agora, depois de toda a preparacao, o triangulo e rasterizado
#    e sombreado pela GPU.
# ----------------------------------------------------------------------
vao.render(moderngl.TRIANGLES)

# ----------------------------------------------------------------------
# 7. LER OS PIXELS E SALVAR. fbo.read() devolve os bytes RGB com a origem no
#    canto INFERIOR-esquerdo (convencao OpenGL). Como um arquivo de imagem tem
#    a origem no TOPO, invertemos na vertical — exatamente a "pegadinha de
#    coordenadas" que discutimos na aula.
# ----------------------------------------------------------------------
dados = fbo.read(components=3)
imagem = Image.frombytes("RGB", (LARGURA, ALTURA), dados)
imagem = imagem.transpose(Image.FLIP_TOP_BOTTOM)
imagem.save(SAIDA)

print(f"Pronto: '{SAIDA}' ({LARGURA}x{ALTURA}).")
print("Repare quantas etapas a GPU exigiu para o que shapes.Triangle fez em 1 linha.")
