# Aula 05 — OpenGL moderno, "puro" (M1/M5: transição para a GPU)

Até aqui o `pyglet` desenhou por nós: `shapes.Triangle(...)` era **uma linha**.
Hoje abrimos a caixa e usamos o **OpenGL moderno** (*core profile* 3.3),
chamada por chamada, **sem biblioteca por cima**. A estrutura é a mesma de
Vulkan, Metal e WebGPU.

São **três exemplos independentes**: cada arquivo roda sozinho e traz comentários
no vocabulário da aula (VBO, VAO, *slot*, *stride*, *offset*, `location`,
*uniform*, *draw call*). A ideia é **ler de cima a baixo, prever o resultado,
rodar e modificar**, não completar TODOs.

| Arquivo | O que mostra | Saída |
|---|---|---|
| `ex1_triangulo_para_png.py` | As **7 etapas** do triângulo na GPU (a mesma ideia do apêndice da Aula 01, agora sem nada escondido): contexto, shaders, dados, VBO e VAO, framebuffer, desenho, leitura dos pixels | gera `triangulo_gpu_puro.png` (sem janela visível) |
| `ex2_hello_triangle.py` | O esqueleto de todo programa: inicialização, loop, encerramento. Um **triângulo** (VBO + `glDrawArrays`) e um **retângulo** (VBO + **EBO** + `glDrawElements`), cada um com seu VAO | janela; `W` alterna *wireframe* |
| `ex3_shaders.py` | Os **três canais** de dados dos shaders: atributo (`in`), **interpolado** (`out` → `in`) e `uniform` | janela; `ESPAÇO` liga/desliga a pulsação |

Cada arquivo começa com uma lista **EXPERIMENTE**. Faça-os **prevendo antes de
rodar** (anote o que previu e o que aconteceu).

## Rodar

```bash
# a partir da raiz do repositorio, com o ambiente ja preparado:
cp aulas/aula05/ex2_hello_triangle.py solucoes/ex2_hello_triangle.py
python solucoes/ex2_hello_triangle.py
```

Se ainda não preparou o ambiente (este usa **bibliotecas diferentes** das aulas
anteriores):

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r aulas/aula05/requirements.txt
```

> O `moderngl` do apêndice da Aula 01 **não** é usado aqui. O objetivo é ver as
> chamadas do OpenGL que ele esconde.

## Notas de plataforma

- **macOS:** a Apple deixou o OpenGL obsoleto e o congelou na versão **4.1**. Ele
  funciona, mas só com contexto *core* 3.3 **mais** `OPENGL_FORWARD_COMPAT`. Os
  exemplos já trazem isso; sem essa linha, a janela falha na criação.
- **Tela Retina/HiDPI:** o tamanho do *framebuffer* (em pixels) é maior que o da
  janela. Os exemplos passam `glfw.get_framebuffer_size` ao `glViewport`.
- **Sem mensagem de erro:** o OpenGL quase nunca reclama. Quando algo falha, o
  sintoma costuma ser **tela preta** ou uma imagem errada; leia o resultado
  visual como pista da causa.

## Checklist de bugs silenciosos (para os experimentos)

| Sintoma | Causa provável |
|---|---|
| Nada aparece, sem erro | `location` do shader ≠ slot do VAO; slot sem `glEnableVertexAttribArray`; *draw* fora do loop |
| Cor ou posição embaralhada | *stride* ou *offset* errados |
| Uniform não muda a imagem | `glGetUniformLocation` devolveu `-1` (nome errado ou uniform não usado) |
| `1282 invalid operation` no 2º quadro | objetos apagados dentro do loop |
| Erro de link confuso | `out` do vertex ≠ `in` do fragment (nome ou tipo) |
