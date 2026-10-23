# Aula 01 — Primeira janela interativa (M1)

Scaffold da primeira aula: uma janela que desenha primitivas 2D e responde a
teclado e mouse. Serve para introduzir **loop de eventos**, **primitivas** e a
ideia de que **a saida e visual** — um erro no codigo vira uma imagem errada.

## Rodar

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python primeira_janela.py
```

## Controles

| Tecla / acao | Efeito |
|---|---|
| `C` | cicla a cor do circulo |
| setas | move o quadrado |
| clique | adiciona um ponto |
| `ESC` | fecha |

## Roteiro de uso em aula (familias 2 e 3)

1. **Prever antes de rodar:** ler o codigo e desenhar no papel a tela esperada.
2. Rodar e **reconciliar** com o desenho.
3. Mexer nos pontos marcados `# >>> EXPERIMENTE` — sempre prevendo antes.

Sugestoes de modificacao (do facil ao desafiador):
- Trocar cores e posicoes das primitivas.
- No `on_key_press`, somar em `.y` em vez de `.x` — a que direcao a tela reage?
- Fazer o clique desenhar um `Rectangle` centrado no ponto (cuidado com a origem
  no canto vs. no centro — bug classico).
- Descobrir onde fica a origem (0,0): clicar nos quatro cantos e observar os
  valores impressos no terminal.

## Apendice opcional — OpenGL "cru" (contraste)

`apendice_opengl_triangulo.py` desenha o **mesmo triangulo**, mas com OpenGL
moderno explicito (shaders GLSL + VBO/VAO), para mostrar **quanta cerimonia** o
`shapes.Triangle(...)` de uma linha esconde. Nao e a atividade da aula — e uma
espiada no "como" da GPU, que so escrevemos de verdade em **M6**. Nao abre
janela: renderiza fora da tela e salva `triangulo_gpu.png`.

```bash
pip install -r requirements-apendice.txt
python apendice_opengl_triangulo.py     # gera triangulo_gpu.png
```
