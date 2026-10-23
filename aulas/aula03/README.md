# Aula 03 — Editor 2D: transformações via matriz homogênea (M3, 1/3)

**Scaffold inicial (a completar).** Primeiro passo do editor 2D que vai crescer
ao longo do bloco M3 — hoje: transformações geométricas 2D em coordenadas
homogêneas; aula 4: sistemas de coordenadas (window↔viewport) e *picking*/zoom;
aula 5: recorte.

Ao contrário da Aula 02 (janela quase vazia), aqui o esqueleto **já desenha a
figura e já translada** com as setas — a translação serve de **exemplo do
padrão** a seguir. O que falta é **rotação**, **escala** e a **composição**
dessas transformações ao apertar as teclas. Procure os blocos `# TODO` em
`editor2d.py`.

## Rodar

Trabalhe numa **cópia** deste scaffold, na pasta `solucoes/` (ignorada pelo
git), como nas aulas anteriores:

```bash
# a partir da raiz do repositorio, com o ambiente ja preparado:
cp aulas/aula03/editor2d.py solucoes/editor2d.py
python solucoes/editor2d.py
```

Se ainda não preparou o ambiente:

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r aulas/aula03/requirements.txt
```

## Controles

| Tecla | Efeito | Status |
|---|---|---|
| setas | translada a figura | já funciona |
| `Q` / `E` | rotaciona (anti-horário / horário) | depois dos TODOs 1 e 3 |
| `+` / `-` | escala (aumenta / diminui) | depois dos TODOs 2 e 3 |
| `R` | reset (volta à identidade) | já funciona |
| `ESC` | fecha | já funciona |

## O que implementar (resumo — ver o enunciado da atividade)

- **TODO 1** — `matriz_rotacao(theta_rad)`: matriz 3×3 de rotação em torno da
  origem, em coordenadas homogêneas.
- **TODO 2** — `matriz_escala(sx, sy)`: matriz 3×3 de escala em torno da
  origem.
- **TODO 3** — em `on_key_press`, monte a matriz elementar de `Q`/`E`/`+`/`-` e
  componha com a transformação acumulada — **siga a mesma ordem de
  multiplicação usada pela translação** (já pronta) e seja capaz de justificar
  a escolha.

`matriz_translacao` e `aplicar_transformacao` já vêm prontas — use-as como
**modelo** do padrão esperado (construção da matriz 3×3; aplicação via
coordenadas homogêneas).

## Roteiro sugerido (famílias 2 e 3)

1. **Prever antes de rodar:** com a figura na posição inicial, escreva no
   papel a matriz resultante de "rotacionar 10° e depois transladar 15px para
   a direita" — e a matriz de "transladar e depois rotacionar". São a mesma
   matriz? Por quê?
2. Implemente TODO 1 (rotação) e teste isoladamente antes de mexer em escala.
3. Implemente TODO 2 (escala).
4. Implemente TODO 3 (composição nas teclas) — rode e **reconcilie** com sua
   previsão do passo 1.
5. Depuração dirigida: troque a ordem da multiplicação em uma das teclas
   (`nova @ transformacao_usuario` → `transformacao_usuario @ nova`) e observe
   o que muda visualmente — é o sintoma clássico de "rotação em torno do ponto
   errado" que vai reaparecer nas próximas aulas.
