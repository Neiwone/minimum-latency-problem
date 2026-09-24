# H3 — Vizinhança específica de MLP no prefixo

> Os scripts e dados brutos em `scripts/` citados neste documento foram removidos do
> repositório e estão preservados na tag git `archive/h-scripts`
> (`git show archive/h-scripts:scripts/<arquivo>`).

**Veredito: refutada.** Os ótimos locais do RVND já são ótimos de janela (k até 8) no
prefixo, no meio e no fim da rota: em ~200 janelas testadas houve uma única melhoria
(`pr76`, k=6, Δ=0,02%), sem tendência com `n` e sem diferença entre regiões. Não há
ponto cego no início da rota para uma vizinhança específica explorar.

## Hipótese

No MLP, um arco no início da rota afeta a latência de todos os vértices seguintes. Se o
custo é dominado pelas primeiras posições, as vizinhanças herdadas do TSP (swap, 2-opt,
reinsertion, or-opt2, or-opt3) deveriam deixar escapar mais melhorias no prefixo que no
meio ou no fim, com o gap residual concentrado no início e crescendo com `n`.

## O que foi testado

Sem ótimos provados para a maioria das instâncias, o teste mede se há um ponto cego de
vizinhança: dado um ótimo local do RVND (construção `--alpha 0.15` + `local_search`, as
5 vizinhanças do artigo), existe uma permutação conjunta de `k` clientes consecutivos
que melhora o custo? Esse movimento está fora do alcance das vizinhanças que mexem em
1–3 elementos quando a melhoria exige reordenar os `k` juntos. Busca exaustiva (`k!`
permutações) em três janelas: **prefix** (posições `[1, 1+k)`), **middle** (centro,
controle) e **suffix** (últimas `k`, controle).

Instâncias `eil51`, `st70`, `pr76`, `kroA100`, `lin105`, `pr226`, `lin318`, `pr439`,
`att532`, 10 trials cada, k ∈ {4, 6}; k=8 em `eil51`/`pr226`/`att532` (5 trials).

## Resultados

| n range | k | prefix hit% | middle hit% | suffix hit% |
|---|---|---|---|---|
| 51–532 | 4 | 0% (0/90) | 0% (0/90) | 0% (0/90) |
| 51–532 | 6 | ~1% (1/90, pr76, Δ=0.02%) | 0% (0/90) | 0% (0/90) |
| 51/226/532 | 8 | 0% (0/15) | 0% (0/15) | 0% (0/15) |

## Por que não funcionou

A busca *best improvement* do RVND escolhe a cada passo o movimento de maior ganho
absoluto. Como um arco no início da rota pesa em muito mais latências futuras do que o
mesmo arco perto do fim, os defeitos do prefixo são os que mais ganho dão ao corrigir,
e por isso são corrigidos primeiro e com prioridade. O prefixo é a região mais
escrutinada pela busca, não um ponto cego.

## Limitações

- Só reordena os `k` clientes que já estão na janela; não testa se clientes de fora
  deveriam entrar no prefixo (coberto em parte por reinsertion/or-opt).
- Um único RVND por trial, não o GILS-RVND completo.
- Não mede o gap contra o ótimo por posição. Um teste mais direto do sintoma seria
  comparar, onde o ótimo é conhecido (ex.: conjunto de Abeledo et al., até 107
  clientes), a posição das divergências entre a solução do GILS-RVND e o ótimo.
