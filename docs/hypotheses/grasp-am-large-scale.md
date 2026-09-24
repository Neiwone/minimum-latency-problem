# GRASP-AM em escala — achado, correção e veredito final

> Os scripts e dados brutos em `scripts/` citados neste documento foram removidos do
> repositório e estão preservados na tag git `archive/h-scripts`
> (`git show archive/h-scripts:scripts/<arquivo>`).

**Veredito: refutada quanto à qualidade.** O `grasp_am` original perde para o
GILS-RVND em 100% das 90 execuções (gaps de 1,1% a 2,0%, todo p ≤ 0,002), mas por não
ter laço de ILS. Com o ILS restaurado (`gils_am_rvnd`), a construção por memória
adaptativa empata em qualidade (nenhum p significativo, |efeito| < 0,1%, mesmo perfil
de ruído de [H1](h1-adaptive-diversification.md)/[H2](h2-elite-path-relinking.md)).
Efeito colateral não previsto: chega ao mesmo resultado ~20-26% mais rápido em
`lin318` e `att532`, com significância (p = 0,0004 e 0,012 em `lin318`; p = 0,022 no
modo `pool` em `att532`); `pr439` não mostra efeito de tempo. O binário
`gils_am_rvnd` passou a ser a base das hipóteses seguintes.

## Hipótese

Construir cada ponto de partida enviesado pela frequência de arestas de um pool de
soluções de elite (memória adaptativa) levaria a busca a soluções melhores que a
construção gulosa aleatorizada do GILS-RVND.

## O que foi testado

- **`grasp_am`** ([`src/grasp_am.cpp`](../../src/grasp_am.cpp)): cada iteração é uma
  construção enviesada por memória seguida de **uma única** convergência de RVND, sem
  perturbação. A frequência vem do pool inteiro (`--parent-mode pool`) ou de um par de
  pais (`--parent-mode pair`).
- **`gils_am_rvnd`** ([`src/gils_am_rvnd.cpp`](../../src/gils_am_rvnd.cpp)):
  literalmente o laço do `gils_rvnd` (`I_max` reinícios, cada um com até `I_ILS`
  ciclos de double-bridge + RVND), trocando só a construção pela construção por
  memória, com a frequência recalculada a cada reinício e a melhor solução do
  reinício adicionada ao pool. O double-bridge é o de intensidade fixa, sem os modos
  adaptativos de H1, para isolar o efeito da construção. Flags: `--imax`, `--iils`,
  `--pool`, `--lambda`, `--parent-mode pool|pair`, `--seed`.

Comparação pareada por seed contra o GILS-RVND em `lin318` (`I_max`=10, 20 seeds),
`pr439` (`I_max`=5, 15 seeds) e `att532` (`I_max`=3, 10 seeds), com `--pool 20
--lambda 0.5`; os mesmos `I_max`/`I_ILS` do lote de H1/H2.

## Resultados

Em instâncias pequenas (`eil51`/`st70`/`pr76`/`kroA100`/`lin105`, 15 seeds), o
`grasp_am` empata exatamente em 100% dos 75 trios, apenas mais rápido em `kroA100`
(~1,5s vs ~2,6s) e `lin105` (~1,9s vs ~2,1s).

**`grasp_am` em escala** (diferença negativa = pior que o GILS-RVND):

| instância | n | `grasp_iter`/`pool` | pool: diff média | pool w/t/l | pair: diff média | pair w/t/l |
|---|---|---|---|---|---|---|
| lin318 | 20 | 800/20 | **−1,12%** | 0/0/20 | **−0,44%** | 0/0/20 |
| pr439 | 15 | 500/20 | **−1,68%** | 0/0/15 | **−1,43%** | 0/0/15 |
| att532 | 10 | 300/20 | **−1,33%** | 0/0/10 | **−2,04%** | 0/0/10 |

Todos os `p` ≤ 0,002, na direção contrária à esperada; o `grasp_am` também gasta
menos tempo total (ex. `lin318`: ~70-84s vs ~159-179s).

**`gils_am_rvnd`, qualidade:**

| instância | n | pool: diff média | pool w/t/l | pool p | pair: diff média | pair w/t/l | pair p |
|---|---|---|---|---|---|---|---|
| lin318 | 20 | −0,081% | 8/3/9 | 1,000 | −0,068% | 8/2/10 | 0,815 |
| pr439 | 15 | +0,039% | 6/0/9 | 0,607 | +0,091% | 8/0/7 | 1,000 |
| att532 | 10 | +0,054% | 6/0/4 | 0,754 | +0,069% | 5/0/5 | 1,000 |

Nenhum `p` significativo, o sinal troca entre instâncias e a magnitude fica abaixo de
0,1%: ruído em torno de zero.

**`gils_am_rvnd`, tempo** (teste de sinal pareado por seed):

| instância | n | pool: mais rápido/empate/mais lento | pool p | pool tempo médio | pair: mais rápido/empate/mais lento | pair p | pair tempo médio |
|---|---|---|---|---|---|---|---|
| lin318 | 20 | 18/0/2 | **0,0004** | **−21,9%** | 16/0/4 | **0,012** | **−19,9%** |
| pr439 | 15 | 8/0/7 | 1,000 | −2,6% | 8/0/7 | 1,000 | −3,0% |
| att532 | 10 | 9/0/1 | **0,022** | **−26,4%** | 7/0/3 | 0,344 | −19,9% |

Em `att532` o modo `pair` vai na mesma direção e com magnitude parecida, mas sem
significância (provavelmente falta de poder com n=10).

## Por que não funcionou

- **`grasp_am`:** o experimento não testava construção por memória contra construção
  gulosa, e sim busca sem intensificação contra busca com intensificação. O GILS-RVND
  usa ~10 pontos de partida, cada um refinado por até ~100 ciclos de perturbação +
  RVND; o `grasp_am`, ~800/500/300 pontos de partida com exatamente 1 convergência de
  RVND cada. Como o ILS com double-bridge é a peça central do GILS-RVND, a perda de
  1-2% é plausivelmente explicada pela ausência desse refino, e mascara qualquer
  efeito da memória.
- **`gils_am_rvnd`:** com a mesma profundidade de refino, a construção enviesada não
  acha ótimos melhores. A hipótese mecânica para o ganho de tempo (não verificada
  diretamente) é que ela produz tours mais próximos dos padrões de boas soluções
  anteriores, e o RVND gasta menos trabalho para convergir a cada reinício: a busca
  não explora mais nem acha ótimos melhores, só chega ao mesmo ótimo com menos ciclos.

Continua em aberto por que `pr439` foge do padrão de tempo; isso precisa ser entendido
antes de generalizar a alegação de velocidade.

## Limitações

- Hiperparâmetros da memória não tunados (`lambda=0.5`, `pool=20`).
- `I_max` reduzido em `pr439` e `att532` (5 e 3) por custo de tempo, e amostras de
  15 e 10 seeds nessas instâncias.
- Comparação por iterações fixas, não por tempo fixo.
