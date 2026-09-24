# Documentação

**Por onde começar:**

- [results-tables.md](results-tables.md) — os resultados finais, gerados dos
  checkpoints por `scripts/make_result_tables.py`.
- [concepts/method-explained.md](concepts/method-explained.md) — o problema, o
  GILS-RVND e cada ideia acrescentada, explicados do zero.
- [concepts/proposal-vs-gils-rvnd.md](concepts/proposal-vs-gils-rvnd.md) — o que
  exatamente mudou em relação ao GILS-RVND publicado.

Em resumo: a configuração atual, `gils_am_rvnd --rvnd-mode candidate-dlb --cand-k 12
--iils 300` ([H16](hypotheses/h16-candidate-neighborhoods.md) +
[H19](hypotheses/h19-dlb-fast-regime.md)), bate o MDM-GILS-RVND a 100 s por execução em
toda instância TSPLIB com n ≥ 200 (custo 1,249% menor, 60/10/0 em 70 pares). Com a
mesma busca local, MDM, GILS-AM e GILS-RVND empatam: o ganho vem da busca local, não da
estratégia de memória.

## Conceitos

| doc | assunto |
|---|---|
| [method-explained](concepts/method-explained.md) | o método explicado do zero |
| [mlp-overview](concepts/mlp-overview.md) | o problema, o artigo de referência e onde cada peça está no código |
| [proposal-vs-gils-rvnd](concepts/proposal-vs-gils-rvnd.md) | diferenças componente a componente em relação ao GILS-RVND |
| [grasp-am](concepts/grasp-am.md) | pseudocódigo do GRASP com memória adaptativa |
| [distance-types](concepts/distance-types.md) | os cinco `EDGE_WEIGHT_TYPE` suportados |
| [cost-64-bit](concepts/cost-64-bit.md) | por que o custo é 64 bits |
| [return-to-depot](concepts/return-to-depot.md) | a flag `--closed`: latência com ou sem volta ao depósito |

## Hipóteses

Cada hipótese tem um doc em [hypotheses/](hypotheses/) que abre com o veredito. Custos
comparados contra o GILS-RVND, salvo indicação.

| | ideia | veredito | resultado principal | adotada? |
|---|---|---|---|---|
| [H1](hypotheses/h1-adaptive-diversification.md) | força do double-bridge adaptada à estagnação ou à distância de arestas | refutada | ruído: p ≥ 0,30, efeito < 0,1% | não |
| [H2](hypotheses/h2-elite-path-relinking.md) | path relinking entre soluções elite | refutada | ruído: p ≥ 0,30, efeito < 0,1% | não |
| [H3](hypotheses/h3-prefix-neighborhood.md) | vizinhança específica para o início da rota | refutada | 1 melhoria em ~200 janelas | não |
| [H4](hypotheses/h4-multi-improvement.md) | busca local multi-improvement | refutada | 1,3× a 2,3× mais lenta | opção `--rvnd-mode multi` |
| [H5](hypotheses/h5-regret-perturbation.md) | perturbação guiada por regret de aresta | refutada no diagnóstico | não supera o corte aleatório | não |
| [H6](hypotheses/h6-lookahead-construction.md) | construção com lookahead | refutada | empate no pipeline completo (23/0/22, p = 1,000) | não |
| H7 | — | sem registro | — | — |
| [H8](hypotheses/h8-dbmea-population.md) | algoritmo memético populacional (DBMEA-lite) | refutada na escala testada | custo ~2,7–2,9% maior em `rand1000` | não |
| [H9](hypotheses/h9-ruin-recreate.md) | ruin-and-recreate (LNS) | refutada no diagnóstico | 299 de 300 trials voltam ao mesmo custo | não |
| [H10](hypotheses/h10-dynasearch.md) | dynasearch: combinar 2-opts simultâneos | refutada no diagnóstico | 3 melhorias em ~258 mil pares | não |
| [H11](hypotheses/h11-guided-local-search.md) | guided local search | refutada (1 seed) | custo ~1,6% maior em `lin318` | não |
| [H12](hypotheses/h12-extended-oropt.md) | or-opt com segmentos de 4 a 6 | confirmada | custo 0,33% menor em `pr439`, 0,39% em `att532`, 1,17% em `rand1000` | opção `--rvnd-mode extended-oropt` |
| [H12b](hypotheses/h12b-genuine-3opt.md) | 3-opt genuíno | refutada | ruído (21/5/16, p = 0,511), +170% de tempo | não |
| [H13](hypotheses/h13-mdm-gils-rvnd.md) | mineração de padrões (MDM-GILS-RVND) | refutada | custo 0,02% maior (12/12/21, p = 0,163) | não; usado como baseline |
| [H14](hypotheses/h14-lk-escape.md) | escape sequencial estilo Lin-Kernighan | refutada | empate (10/0/10), +30,5% de tempo | não |
| [H15](hypotheses/h15-adaptive-oropt.md) | or-opt com `k_max` adaptativo | não concluída | só calibração com 1 seed | não |
| [H16](hypotheses/h16-candidate-neighborhoods.md) | vizinhanças podadas por lista de candidatos | confirmada | contra o MDM: custo 0,649% menor (27/0/3) | sim, base do H19 |
| H17 | double-bridge com blocos limitados (`--db-maxseg-div`) | refutada, em triagem | melhora a média mas piora a taxa de vitórias; neutro no H19 | não; ver H16 e H19 |
| H18 | cortes do double-bridge enviesados para o início (`--db-front-bias`) | refutada, em triagem | sem ganho | não; ver H19 |
| [H19](hypotheses/h19-dlb-fast-regime.md) | *don't-look bits* + `I_ILS` = 300 | confirmada | contra o MDM: custo 1,249% menor (60/10/0 em 70 pares) | sim, configuração atual |
| [GRASP-AM em escala](hypotheses/grasp-am-large-scale.md) | construção com memória adaptativa | refutada em qualidade | empate, mas ~20–26% mais rápido | vira o `gils_am_rvnd` |
| [GRASP+VND](hypotheses/h-salehipour-grasp-vnd.md) | implementação de Salehipour et al. (2011) | não concluída | or-opt estendido: custo 0,3351% menor que o GRASP+VND original | não |

## Benchmarks

| doc | o que mede |
|---|---|
| [fixed-time-protocol](benchmarks/fixed-time-protocol.md) | o protocolo de tempo fixo usado em todos os resultados principais |
| [fixed-time-100s-4inst-results](benchmarks/fixed-time-100s-4inst-results.md) | 100 s, 4 instâncias: `cand` contra o MDM, custo 0,405% menor (26/10/4) |
| [fixed-time-100s-tsplib](benchmarks/fixed-time-100s-tsplib.md) | 100 s, 10 instâncias TSPLIB; superado (binários anteriores à otimização da busca local) |
| [mdm-vs-am-extended-tsplib-comparison](benchmarks/mdm-vs-am-extended-tsplib-comparison.md) | protocolo do artigo do MDM: `extended-oropt` ganha (27/61/12, p = 0,024), MDM nulo |
| [salehipour-tsplib-mdm-vs-am-extended](benchmarks/salehipour-tsplib-mdm-vs-am-extended.md) | benchmark de Salehipour, n = 10 a 500: `extended-oropt` com custo 0,283% menor em n = 500, MDM nulo |
| [salehipour-n1000-mdm-vs-am-extended](benchmarks/salehipour-n1000-mdm-vs-am-extended.md) | Salehipour n = 1000: `extended-oropt` com custo 0,782% menor (162/0/38); braço MDM não concluído |

## Guias e relatórios

- [guides/running-salehipour-batches](guides/running-salehipour-batches.md) — como rodar os lotes de 100 s
  de Salehipour n = 500 e n = 1000.
- [reports/local-search-speedup-report](reports/local-search-speedup-report.md) — relatório autocontido
  da busca local podada e dos *don't-look bits*: o que mudou, como foi medido e o que os
  números permitem afirmar.

## Artigos

- [papers/silva-2012-gils-rvnd.pdf](papers/silva-2012-gils-rvnd.pdf) — Silva,
  Subramanian, Vidal & Ochi (2012), *A simple and effective metaheuristic for the
  Minimum Latency Problem*, EJOR 221, 513–520. O GILS-RVND.
- [papers/salehipour-2011-grasp-vnd-vns.pdf](papers/salehipour-2011-grasp-vnd-vns.pdf) —
  Salehipour, Sörensen, Goos & Bräysy (2011), *Efficient GRASP+VND and GRASP+VNS
  metaheuristics for the traveling repairman problem*, 4OR 9(2), 189–209.
