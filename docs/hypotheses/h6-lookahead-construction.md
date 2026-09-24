# H6 — Construção com lookahead cumulativo

> Os scripts e dados brutos em `scripts/` citados neste documento foram removidos do
> repositório e estão preservados na tag git `archive/h-scripts`
> (`git show archive/h-scripts:scripts/<arquivo>`).

**Veredito: refutada.** Na construção pura, o lookahead com `k=3` entrega pontos de
partida melhores (+0,83%, 127/0/83, p=0,0029). No pipeline completo com RVND a vantagem
desaparece: com N=45 pares o resultado é empate (+0,033%, 23/0/22, p=1,000). Não
adotado.

## Hipótese

A construção gulosa escolhe o próximo cliente só por `dist(r,c)`, um lookahead de 1
passo. Como o custo do MLP é cumulativo, pontuar cada candidato pelo custo cumulativo de
um rollout guloso de `k` passos daria pontos de partida melhores e, deles, soluções
finais melhores. Motivação: a estrutura matroidal cumulativa de Fischetti, Laporte &
Martello (1993), usada só como inspiração para um critério guloso mais informado.

## O que foi testado

Cada candidato `c` (partindo de `r`) é pontuado pelo custo cumulativo do segmento
hipotético `r → c → (k-1 saltos gulosos adicionais)`, em vez de `dist(r,c)`; a mecânica
de RCL/alpha fica igual por cima. Implementado de forma aditiva em
[`src/construction_impl.cpp`](../../src/construction_impl.cpp), com
`--construction-mode greedy|lookahead --lookahead-k N` em `gils_rvnd` e em
`construction` (padrão `greedy`, o comportamento do artigo). Com `alpha=0` a versão C++
dá exatamente o mesmo custo que a réplica Python validada (`lin318`: 6.588.331).

## Resultados

**Construção pura, sem RVND** (réplica Python, 30 trials × 7 instâncias, pareado por
seed): `k=2` não mostra sinal (105 vitórias/105 derrotas, `p=1.000`). Com `k=3`:

| instância | n | win/tie/loss | p (sinal) | ganho médio |
|---|---|---|---|---|
| eil51 | 51 | 17/0/13 | 0,585 | +0,86% |
| st70 | 70 | 23/0/7 | **0,005** | +2,09% |
| pr76 | 76 | 18/0/12 | 0,362 | +1,04% |
| kroA100 | 100 | 18/0/12 | 0,362 | +0,59% |
| lin105 | 105 | 15/0/15 | 1,000 | +0,21% |
| pr226 | 226 | 18/0/12 | 0,362 | +1,02% |
| lin318 | 318 | 18/0/12 | 0,362 | +0,02% |
| **agregado (todas)** | | **127/0/83** | **0,0029** | **+0,83%** |

A direção favorece o lookahead nas 7 instâncias. O custo da construção é pequeno
(`att532`: 1,14 s em Python com k=3).

**Pipeline completo** (`gils_rvnd --imax 5 --iils 100`, greedy vs.
`--construction-mode lookahead --lookahead-k 3`, pareado por seed). Uma amostra inicial
de 6 seeds em `lin318` deu 3 vitórias/3 derrotas (−0,06%). O lote com poder
estatístico:

| instância | pares | diff média | win/tie/loss | p (sinal) | overhead de tempo |
|---|---|---|---|---|---|
| lin318 | 20 | −0,056% | 10/0/10 | 1,000 | −1,6% |
| pr439 | 15 | +0,199% | 8/0/7 | 1,000 | +17,8% |
| att532 | 10 | −0,037% | 5/0/5 | 1,000 | −3,4% |
| **agregado** | **45** | **+0,033%** | **23/0/22** | **1,000** | +4,3% |

O tempo não mostra direção consistente (−3,4% a +17,8%); o custo extra `O(n²·k)` da
construção é uma fração pequena e variável do tempo total, dominado pelo ILS.

## Por que não funcionou

O diagnóstico era real: a construção com lookahead entrega pontos de partida
sistematicamente melhores. Mas essa vantagem é inteiramente absorvida pelo RVND, que
converge os dois pontos de partida para qualidade equivalente. O argumento original da
hipótese (um ponto de partida melhor levaria a uma bacia de atração que o RVND não
alcançaria a partir do míope) não se confirma. `k=2` não mostrar nada nem na construção
pura sugere que o efeito precisa de uma profundidade mínima de sondagem; com 1 salto de
sondagem a informação extra em relação ao critério original é pequena.

É o mesmo padrão de [H1](h1-adaptive-diversification.md),
[H2](h2-elite-path-relinking.md), [H3](h3-prefix-neighborhood.md) e
[H4](h4-multi-improvement.md): o GILS-RVND é robusto a variações nos pontos de entrada
(perturbação, recombinação, construção, busca local em lote), e o gargalo não parece
estar em nenhum deles. Continua em aberto *por que* o RVND apaga tão bem as diferenças
de ponto de partida; `k=4`/`k=5` ou combinar lookahead com a memória adaptativa do
GRASP-AM esbarram na mesma ressalva.

## Limitações

- O teste da construção pura usou uma réplica Python, não o binário C++ (as duas batem
  em `alpha=0`).
- Só `k=2` e `k=3` foram testados.
- `pr439` e `att532` têm N menor (15 e 10) que `lin318` (20).

## Referências

- Fischetti, M., Laporte, G., Martello, S. (1993). The Delivery Man Problem and
  Cumulative Matroids.
