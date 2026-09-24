# H1 — Diversificação adaptativa

> Os scripts e dados brutos em `scripts/` citados neste documento foram removidos do
> repositório e estão preservados na tag git `archive/h-scripts`
> (`git show archive/h-scripts:scripts/<arquivo>`).

**Veredito: refutada.** O sintoma que motivou a hipótese é real: o ILS estagna muito
antes de esgotar o orçamento. Mas nenhum dos dois mecanismos testados transforma isso
em ganho. A escalada por estagnação perde; o controle por distância de arestas corrige
esse defeito, mas com poder estatístico (N=20/15/10) fica indistinguível de ruído
(p ≥ 0,30 em todas as instâncias, |efeito| < 0,1%). Não adotado.

## Hipótese

A perturbação do GILS-RVND tem intensidade fixa (um double-bridge). Controlar essa
intensidade pela estagnação — aumentar quando a busca trava, reduzir quando progride —
reduziria o gap médio sem custo de tempo relevante.

## Diagnóstico do sintoma

`gils_rvnd -v` imprime cada melhoria aceita dentro do ILS. Com `--imax 1` e orçamentos
muito acima do padrão do artigo (`--iils` 100):

| instância | n | melhorias | passo da última melhoria | orçamento | ganho total |
|---|---:|---:|---:|---:|---:|
| eil51 | 51 | 9 | 97 | 3000 | 7,82% |
| lin105 | 105 | 3 | 5 | 3000 | 6,59% |
| pr226 | 226 | 7 | 182 | 3000 | 2,12% |
| lin318 | 318 | 17 | 605 | 3000 | 5,80% |
| pr439 | 439 | 22 | 270 | 400 | 6,77% |
| att532 | 532 | 33 | 733 | 150 | 6,29% |

A última melhoria chega numa fração pequena do orçamento (em `lin105`, no passo 5 de
3000). O sintoma é real, o que justificou testar o remédio. (Também medidos, com o
mesmo padrão: st70, pr76, kroA100.)

## Mecanismos testados

Ambos em [`src/gils_rvnd.cpp`](../../src/gils_rvnd.cpp), escolhidos por
`--pert-mode fixed|stagnation|distance` (padrão `fixed`, o comportamento do artigo). A
força `s` é o número de double-bridges aplicados em sequência.

1. **Estagnação** (`stagnation`): `s = min(1 + iterILS / 5, 5)`. Como `iterILS` volta a
   0 a cada melhoria, a força sobe enquanto a busca trava e cai quando ela progride
   (`--stagnation-step 5`, `--max-strength 5`).
2. **Distância** (`distance`), no estilo do AILS-PR (Máximo & Nascimento, 2021): depois
   de cada RVND, mede `d` = número de nós cujo sucessor mudou em relação à rota
   perturbada. Se `d` < 5% de `n`, `s` sobe 1; se `d` > 15%, desce 1
   (`--target-min-pct 0.05`, `--target-max-pct 0.15`). É um controle de malha fechada:
   reage à diversidade de fato obtida, não ao tempo decorrido.

Comparação pareada: mesmo binário e mesma `--seed`, mudando só o modo de perturbação.

## Resultados

**Instâncias até n=226** (eil51, st70, pr76, kroA100, lin105, pr226; 98 pares): os três
modos empatam em 100% dos pares, sempre na mesma solução. Não há gap a recuperar, só
custo: a estagnação é 70–94% mais lenta, a distância 24–47%.

**`lin318`, amostra pequena** (4 pares, `I_max=5`): a estagnação perde nos 4
(−0,54%); a distância fica em 1/1/2 (−0,02%). Foi isso que motivou o segundo mecanismo.

**Lote final, com poder estatístico** (fixo vs. distância; diferença positiva = distância
melhor):

| instância | pares | `I_max`/`I_ILS` | diferença média | V/E/D | p (sinal) |
|---|---:|---:|---:|---:|---:|
| lin318 | 20 | 10/100 | +0,007% | 8/2/10 | 0,815 |
| pr439 | 15 | 5/100 | −0,082% | 5/0/10 | 0,302 |
| att532 | 10 | 3/100 | −0,038% | 5/0/5 | 1,000 |

Nenhum p perto de significância, o sinal troca entre instâncias e a magnitude fica
abaixo de 0,1%: é ruído em torno de zero. Uma amostra intermediária (12/5/3 pares) já
mostrava o mesmo, com perdas isoladas de até −1,6% em `pr439` e `att532`.

## Por que não funcionou

- **Estagnação:** a regra olha só o tempo sem melhoria, nunca o efeito da perturbação.
  Em ~20 iterações paradas chega a 5 double-bridges empilhados, que destroem mais
  estrutura do que o RVND reconstrói no orçamento restante, e não há como recuar. É o
  defeito que a literatura aponta no escalonamento cego (VNS clássico, e principalmente
  o controle por distância do AILS-PR, desenhado para evitá-lo).
- **Distância:** elimina esse defeito — nunca degrada de forma sistemática — mas a
  diversidade extra não vira solução melhor. O sintoma (estagnação cedo) existe, mas
  não é o que limita a qualidade nestas instâncias.

Continuam não testados, e não foram descartados por este resultado: escolher a força
por recompensa histórica (Reactive GRASP, Prais & Ribeiro 2000; ALNS, Ropke & Pisinger
2006), variar o *tipo* de kick e não só a força (Benlic & Hao 2013), ou escolher *onde*
cortar (XKICK). A combinação com path relinking, como no AILS-PR, foi testada em
[H2](h2-elite-path-relinking.md).

## Limitações

- Parâmetros não tunados: passo de estagnação 5, força máxima 5, banda-alvo 5%–15%.
- Em `pr439` e `att532` o lote usou `I_max` reduzido (5 e 3) por custo de tempo.
- Um tempo medido (`lin318`, seed 11, modo distância: 7 956 882 ms) é artefato de
  relógio do WSL2 e foi descartado do agregado de tempo; o custo não é afetado.

## Referências

- Mladenović, N., Hansen, P. (1997). Variable neighborhood search. *Computers &
  Operations Research*, 24(11), 1097–1100.
- Martin, O., Otto, S.W., Felten, E.W. (1991). Large-step Markov chains for the TSP.
  *Complex Systems*, 5(3), 299–326.
- Benlic, U., Hao, J.K. (2013). A Study of Adaptive Perturbation Strategy for Iterated
  Local Search. *EvoCOP 2013*, LNCS 7832.
  https://link.springer.com/chapter/10.1007/978-3-642-37198-1_6
- XKICK, an intelligent kick perturbation for the traveling salesman problem.
  https://www.researchgate.net/publication/317370678
- Prais, M., Ribeiro, C.C. (2000). Reactive GRASP: An application to a matrix
  decomposition problem in TDMA traffic assignment. *INFORMS Journal on Computing*,
  12(3). https://www.semanticscholar.org/paper/989a3b09ce28d7463ebcbe4e15dc57d0290d4f27
- Ropke, S., Pisinger, D. (2006). An adaptive large neighborhood search heuristic for
  the pickup and delivery problem with time windows.
  https://www.researchgate.net/publication/220413334
- Máximo, V.R., Nascimento, M.C.V. (2021). A hybrid adaptive Iterated Local Search with
  diversification control to the Capacitated Vehicle Routing Problem. *European Journal
  of Operational Research*, 294, 1108–1119. https://arxiv.org/abs/2012.11021 ·
  https://www.sciencedirect.com/science/article/abs/pii/S037722172100117X
- Máximo, V.R., Cordeau, J.-F., Nascimento, M.C.V. (2024). AILS-II: An Adaptive Iterated
  Local Search Heuristic for the Large-Scale Capacitated Vehicle Routing Problem.
  *INFORMS Journal on Computing*, 36(4), 974–986. https://arxiv.org/abs/2205.12082
- Salehipour, A., Sörensen, K., Goos, P., Bräysy, O. (2011). Efficient GRASP+VND and
  GRASP+VNS metaheuristics for the traveling repairman problem. *4OR*, 9(2), 189–209.
