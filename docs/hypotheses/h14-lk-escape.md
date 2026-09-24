# H14 — Escape sequencial estilo Lin-Kernighan

**Veredito: refutada.** Cadeias sequenciais de 2-opt escapam do ótimo local do RVND
estendido, mas raramente (0,5–2,5% dos starts). Integradas ao `gils_am_rvnd`
(`--rvnd-mode lk-escape`) contra `extended-oropt`, em `rand1000` com 20 seeds pareadas,
empatam em qualidade (10/0/10, p = 1,0000, +0,29% com desvio de 0,94%) e são +30,5% mais
lentas. Não adotado.

## Hipótese

Depois do or-opt estendido ([H12a](h12-extended-oropt.md)), a pergunta era se existe um
ganho categoricamente maior ou se ~1% é o teto do RVND com vizinhanças simples.
Lin-Kernighan, a busca local mais forte conhecida para o TSP, nunca foi adaptado a um
objetivo posicional como o MLP.

O critério clássico de LK (comparar comprimento da aresta removida com o da adicionada) é
aditivo e não vale no MLP, onde o custo é `Σ(n-i+1)·w(...)` e uma aresta cara no início
penaliza todos os clientes seguintes. Mas as tabelas T/C/Cr dão o custo exato de qualquer
concatenação de segmentos (retos ou revertidos) em O(1). E, ao contrário de
[H10](h10-dynasearch.md), que combinava reversões *simultâneas* e caiu numa fronteira de
Pareto, uma cadeia LK é *sequencial*: basta o estado corrente `(t, custo)`.

## O que foi testado

**Diagnóstico** ([`src/diag_lk.cpp`](../../src/diag_lk.cpp)): a partir de uma solução
convergida por `RVND_ExtendedOrOpt`, uma cadeia de reversões 2-opt sequenciais, guiada
por listas dos k vizinhos mais próximos, com profundidade limitada e cada passo aplicado
de fato (O(n²) por passo). Dada a ponta livre `freeEnd` (cidade c1) e o candidato c2 em
`posC2`, reverte `[freeEnd+1, posC2]` se `posC2 > freeEnd`, ou `[posC2, freeEnd-1]` caso
contrário. A aresta `(c1,c2)` aparece e a nova ponta livre é sempre `posC2`. Um bug foi
corrigido: o candidato mais próximo de c1 costuma ser seu vizinho atual, o que gera uma
reversão de 1 elemento e deixava a cadeia oscilando entre não-movimentos; candidatos com
`i>=j` passaram a ser excluídos.

**Integração** ([`src/rvnd_lk.cpp`](../../src/rvnd_lk.cpp), `--rvnd-mode lk-escape` no
`gils_am_rvnd`): converge com `RVND_ExtendedOrOpt`, dispara um lote de cadeias a partir de
posições aleatórias; se alguma acha um ponto estritamente melhor, adota e reconverge;
repete até um lote inteiro falhar.

## Resultados

**Diagnóstico** (escape = cadeia que bate o ótimo local do RVND estendido):

```
depth=8  cand-k=12  (5 trials × 40 starts cada, lin318/pr439/att532/rand1000/rand2000)
  lin318   0.5% escapes   best_delta_seen=-10436 (-0.18%)
  pr439    1.0% escapes   best_delta_seen=-34732 (-0.18%)
  att532   1.5% escapes   best_delta_seen=  -904 (-0.02%)
  rand1000 1.5% escapes   best_delta_seen=-51263 (-0.46%)
  rand2000 1.0% escapes   best_delta_seen= -5006 (-0.02%)

depth=15 cand-k=20  (lin318/pr439/att532)
  lin318   1.5% escapes   best_delta_seen=-11262 (-0.19%)
  pr439    2.5% escapes   best_delta_seen=-44555 (-0.23%)
  att532   1.5% escapes   best_delta_seen= -2679 (-0.05%)
```

Raros, mas não nulos, e crescem com profundidade e largura de candidatos.

**Calibração em `lin318`:** com `numProbes=40/depth=15/candK=20` uma chamada de
`RVND_LKEscape` foi 2,6x mais lenta que `RVND_ExtendedOrOpt` sozinho e pior em qualidade;
com `numProbes=10/depth=10/candK=12`, 1,6x.

**Teste pareado** (`rand1000.tsp`, `--imax 1 --iils 5`, 20 seeds, `numProbes=10 depth=10
candK=12`, `lk-escape` vs `extended-oropt`):

```
N=20  W/T/L = 10/0/10   sign_p = 1,0000
mean_rel% (lk melhor) = +0,29%   (desvio = 0,94% — dentro do ruído)
mean_time_rel% (lk mais lento) = +30,5%
```

A diferença por seed vai de -0,66% a +2,23%, e a de tempo de -47% a +263%.

## Por que não funcionou

O mecanismo existe: cadeias sequenciais alcançam pontos que nenhuma vizinhança simples
alcança. Mas com taxa de escape de ~1–2,5%, a maioria dos lotes paga o custo O(n²) por
passo, por sonda, sem achar nada, e isso acontece em toda convergência do RVND, não só na
final. Com o ILS limitado por iterações, o custo extra vira menos iterações reais.
Hipóteses não testadas:

1. **Frequência errada:** disparar sondas em toda convergência é caro demais para essa
   taxa de acerto; talvez funcionasse como diversificação ocasional, perto da estagnação.
2. **Trade-off de parâmetros:** a taxa "verdadeira" foi medida com parâmetros generosos
   (depth=15, candK=20); os parâmetros baratos que não dominam o tempo reduzem ainda mais
   a taxa de escape.
3. **O ganho pode não compor:** reconvergir depois do escape pode levar a um ótimo local
   só marginalmente diferente, sem chegar a uma bacia de atração melhor.

Mesmo o candidato teoricamente mais promissor para escapar de ótimos locais do RVND, LK
adaptado ao objetivo posicional do MLP, não superou o RVND estendido nesta integração.

## Limitações

- O teste pareado usou uma instância (`rand1000`) e um orçamento pequeno
  (`--imax 1 --iils 5`).
- Só uma configuração de parâmetros foi testada estatisticamente.
