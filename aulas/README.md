# aulas/

Um diretório por aula, publicado ao longo do semestre. Cada *scaffold* é um
script simples e comentado — para **ler, prever, rodar e modificar**.

- **`aula01/`** — M1: primeira janela interativa em pyglet (primitivas, loop de
  eventos), com um apêndice opcional de OpenGL "cru" (moderngl) para contraste.
- **`aula02/`** — M2: **scaffold inicial** do Color Picker (a completar) — esqueleto
  em pyglet + helper; o aluno implementa sliders R/G/B, cor aditiva e reset.
- **`aula03/`** — M3 (1/3): **scaffold inicial** do editor 2D (a completar) —
  translação já funciona (exemplo); o aluno implementa rotação, escala e a
  composição de transformações via matriz homogênea (numpy).
- **`aula04/`** — M3 (2/3): **scaffold** de window ↔ viewport: cena em
  coordenadas do mundo, pan pronto; o aluno implementa a matriz
  window→viewport, o *picking* pela inversa e o zoom. O README traz o passo a
  passo para levar essas peças ao editor da Atividade 03.
- **`aula05/`** — OpenGL moderno "puro" (GLFW + PyOpenGL): **três exemplos
  independentes** para ler, prever, rodar e modificar: o triângulo na GPU em 7
  etapas (gera um PNG), *Hello Triangle* (VBO, VAO, EBO) e *shaders* (atributo,
  interpolado e `uniform`). Usa um ambiente diferente (`requirements.txt` próprio).

Stack: **pyglet** (módulos interativos) + **numpy** (rasterizador em software, nos
módulos de 3D); **OpenGL moderno "puro"** (`glfw` + `PyOpenGL`) a partir da
aula 05, em exemplos para ler e rodar. Cada pasta tem seu `requirements.txt` (uso
via `pip` num `venv`).
