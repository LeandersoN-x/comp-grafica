# Aula 02 — Color Picker (M2)

**Scaffold inicial (a completar).** Ponto de partida MÍNIMO para a Atividade 02:
implementar um seletor de cores RGB interativo em pyglet — três sliders R/G/B, a
cor resultante ao vivo e um botão de reset.

Aqui já vem pronto só o **esqueleto** que você conhece da Aula 01 (janela,
`batch`, `on_draw`, loop de eventos) + um helper `contem(...)`. O **miolo** é seu:
procure os blocos `# TODO` em `color_picker.py`.

## Rodar

Trabalhe numa **cópia** deste scaffold, na pasta `solucoes/` (ignorada pelo git),
para que atualizar o repositório com `git pull` nunca sobrescreva o seu trabalho
(ver o `README.md` do repositório):

```bash
# a partir da raiz do repositorio, com o ambiente ja preparado:
cp aulas/aula02/color_picker.py solucoes/color_picker.py
python solucoes/color_picker.py
```

Se ainda não preparou o ambiente:

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r aulas/aula02/requirements.txt
```

Abre uma janela quase vazia (com um retângulo de exemplo) — é esperado: o resto
você implementa. Fecha com `ESC`.

## O que implementar (resumo — ver o enunciado da atividade)

- Três **sliders** R, G, B com seletor arrastável/clicável.
- A **cor resultante** (soma aditiva das três componentes) num retângulo.
- Um **botão de reset** (retângulo) que zera/branqueia a cor.
- **Saída no terminal**: `RGB = (r, g, b)`.
- Retângulos com **borda cinza** (`shapes.BorderedRectangle`).
- Opcional: **arrastar** o seletor (`on_mouse_drag` / `on_mouse_release`).

## Roteiro sugerido

1. **Projete no papel** o layout (posições dos trilhos, alças, resultado, botão).
2. Desenhe as primitivas **estáticas** (TODO 1).
3. Faça o valor de cada slider **compor a cor** e reposicionar a alça (TODO 2).
4. Torne **interativo** no clique (TODO 3) e, como bônus, no arrasto (TODO 4).
