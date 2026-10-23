# Aula 04 — Window ↔ viewport, zoom/pan e picking (M3, 2/3)

**Scaffold (a completar).** Até a Aula 03, o editor desenhava direto em
**pixels**: a coordenada de um ponto era a própria posição dele na tela. Hoje
separamos o **mundo** (onde os objetos vivem) da **tela** (pixels da janela). Um
retângulo do mundo, a **window**, é mapeado num retângulo da tela, a
**viewport**, por uma matriz 3×3 montada por composição, como na Aula 03.

- **Zoom e pan mexem na window, não nos objetos.**
- **Picking** (saber em que ponto do mundo o usuário clicou) usa a **inversa**
  dessa matriz.

> Atenção ao nome: a *window* do mundo **não** é a `pyglet.window.Window` (a
> janela do sistema operacional). No código, a janela do SO é `janela` e a
> window do mundo é `window_mundo`.

O esqueleto **já roda**: a window começa igual à viewport, então o mapeamento é
a identidade e a cena aparece certa mesmo com os TODOs provisórios. Os problemas
aparecem quando você tenta dar zoom ou pan, e observá-los é parte do exercício.

## Rodar

```bash
# a partir da raiz do repositorio, com o ambiente ja preparado:
cp aulas/aula04/visualizacao2d.py solucoes/visualizacao2d.py
python solucoes/visualizacao2d.py
```

Se ainda não preparou o ambiente:

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r aulas/aula04/requirements.txt
```

## Controles

Escolhidos para **não colidir** com as teclas do editor da Aula 03 (setas,
`Q`/`E`, `+`/`-`, `R`).

| Entrada | Efeito | Status |
|---|---|---|
| botão direito + arrastar | pan | window já muda; tela reage depois do TODO 1 |
| `Ctrl` (ou `Alt`/`Option`) + arrastar | pan, para **trackpad** sem botão direito | idem |
| `Shift` + setas | pan pelo teclado | idem |
| roda do mouse / `Z` / `X` | zoom in / out | depois dos TODOs 1 e 3 |
| clique esquerdo (sem `Ctrl`/`Alt`) | marca o ponto do **mundo** clicado | certo de verdade depois do TODO 2 |
| `C` | apaga as marcas | já funciona |
| `V` | volta à vista inicial | já funciona |
| `ESC` | fecha | já funciona |

O texto no topo da janela mostra a window atual e a posição do mouse na tela e
no mundo.

## O que implementar

- **TODO 1**: `matriz_window_viewport(window, viewport)`. Composição de três
  passos: transladar o canto da window até a origem, escalar pela razão
  viewport/window, transladar até o canto da viewport. **Preveja a ordem do
  produto** antes de escrever.
- **TODO 2**: `tela_para_mundo(x, y)`. Aplique a **inversa** da matriz do TODO 1
  (`np.linalg.inv`) ao ponto do mouse.
- **TODO 3**: `zoom(fator)`. Altere só `window_mundo`: escale a window em torno
  do **centro** dela, pelo mesmo fator em x e y.
- **TODO 4 (opcional)**: `zoom_no_ponto(fator, x, y)`. O ponto do mundo sob o
  cursor continua sob o cursor depois do zoom (roda do mouse).

`pan_mundo` e o pan com o botão direito já vêm prontos, como **exemplo**: repare
como o deslocamento do mouse, em pixels, é convertido para unidades do mundo.

## Roteiro sugerido

1. **Prever:** com window = (−10, −7.5, 10, 7.5) e viewport = (0, 0, 640, 480),
   para onde vai o ponto (0, 0) do mundo? E o ponto (5, 0)?
2. Rode o scaffold **sem mexer em nada** e arraste com o botão direito. O texto
   da window muda, a tela não. Explique o descompasso.
3. Implemente o TODO 1 e repita. Arrastar para a direita move a window para
   onde?
4. Clique no canto superior direito do quadrado laranja (mundo (40, 40)). Faça
   o TODO 3, dê zoom e clique de novo no mesmo canto. Com o TODO 2 ainda
   provisório, onde a marca nova cai? Depois implemente o TODO 2 e confira.
5. **Experimento** (ponte para a Aula 05): troque `VIEWPORT` por
   `(80, 60, 560, 420)`. O que aparece **fora** do retângulo cinza? Por que isso
   é um problema? (É o assunto da próxima aula: recorte.)
6. **Experimento**: troque `VIEWPORT` por `(0, 0, 640, 240)`, sem mudar a window.
   O que acontece com a seta? Por quê?

## Levando para a Atividade 03

Você **não** precisa recomeçar o seu editor. As peças desta aula foram escritas
para serem copiadas para ele:

1. **Copie a seção 4** (`VIEWPORT`, `WINDOW_INICIAL`, `window_mundo`,
   `matriz_window_viewport`, `mundo_para_tela`, `tela_para_mundo`, `pan_mundo`,
   `zoom`). Como a window começa igual à viewport, **nada muda na tela** ao
   colar: os objetos que você já criou (em pixels) passam a estar em unidades do
   mundo com os mesmos números.
2. **Desenho:** no ponto em que você cria os `shapes` de cada objeto, aplique a
   window→viewport **por último**: pontos locais → matriz do objeto →
   `mundo_para_tela` → `shapes`. (Ou uma matriz só: `M_wv @ M_objeto`.)
3. **Mouse:** no **início** de cada handler de mouse, converta `(x, y)` com
   `tela_para_mundo` **antes** de criar um objeto, testar ponto-em-polígono ou
   escolher o pivô. Todo o resto do editor passa a pensar só no mundo.
4. **Arrastos:** se você move objetos arrastando o mouse, o `(dx, dy)` do
   `on_mouse_drag` está em **pixels**. Converta para o mundo pela escala (como
   no pan pronto daqui), senão, com zoom, o objeto anda mais rápido ou mais
   devagar que o mouse.
5. **Teclas:** os controles daqui não usam as teclas da Aula 03; se você já
   usou `Z`, `X`, `C` ou `V` no seu editor, troque uma delas.

Teste de aceitação: depois de dar zoom e pan, clicar num objeto ainda deve
selecioná-lo, e um objeto novo deve nascer exatamente sob o cursor.
