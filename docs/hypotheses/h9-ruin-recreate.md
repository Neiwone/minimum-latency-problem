# H9 — Large Neighborhood Search / ruin-and-recreate

> Os scripts e dados brutos em `scripts/` citados neste documento foram removidos do
> repositório e estão preservados na tag git `archive/h-scripts`
> (`git show archive/h-scripts:scripts/<arquivo>`).

**Veredito: refutada, só no diagnóstico barato (nada implementado em C++).** A versão
gulosa não perturba: 299 dos 300 trials voltam ao custo idêntico ao de partida (hit% = 0,0
nas 3 instâncias, contra 58–68% do double-bridge). As duas correções (reinserção
randomizada top-3, H9b; Shaw removal, H9c) destravam parcialmente o mecanismo, mas
perdem de forma consistente para o double-bridge em hit%. Não adotado.

## Hipótese

[H5](h5-regret-perturbation.md) mostrou que escolher *onde* o double-bridge corta não
ajuda, provavelmente porque ele não controla *com o que* reconectar: a reconexão segue a
ordem dos segmentos, não a proximidade. Ruin-and-recreate (Ropke & Pisinger 2006)
controlaria as duas pontas: remove `k` clientes e reinsere cada um na posição de menor
custo por inserção regret-2.

## O que foi testado

Diagnóstico em Python (`scripts/h9_ruin_recreate_test.py`, mesmo método de H5): a
partir de um ótimo local convergido pelo RVND, perturbar com `double_bridge` (baseline)
ou com a variante, reconvergir ambos com `./bin/local_search` e comparar o custo final
com o de antes da perturbação. `hit%` = trials que terminam melhores; `identical%` =
trials que voltam ao custo idêntico. 5 ótimos locais × 20 trials × 2 modos por
instância.

1. **H9** (`ruin_recreate`): remove `k=8` clientes ao acaso e reinsere por regret-2
   gulosa, pelo custo total da rota. Em `att532`, `lin318`, `pr439`.
2. **H9b** (`ruin_recreate_v2`): sorteia uniformemente entre as `TOP_M=3` posições mais
   baratas (randomized best insertion do ALNS). Em `eil51`, `kroA100`, `rat195`.
3. **H9c** (`shaw_removal`): remove um cliente semente e os `k-1` mais próximos dele
   (Shaw 1998), para que os removidos sejam mutuamente substituíveis; mesmo repair de
   H9b, mesmas 3 instâncias.

## Resultados

**H9** (600 trials):

| instância | modo | n | hit% | mean_delta | mean_rel% |
|---|---|---:|---:|---:|---:|
| att532 | double_bridge | 100 | 68.0 | 39912.68 | 0.6577 |
| att532 | ruin_recreate | 100 | 0.0 | -51.56 | -0.0008 |
| lin318 | double_bridge | 100 | 67.0 | 59953.17 | 0.9551 |
| lin318 | ruin_recreate | 100 | 0.0 | 0.00 | 0.0000 |
| pr439 | double_bridge | 100 | 58.0 | 95478.83 | 0.4680 |
| pr439 | ruin_recreate | 100 | 0.0 | 0.00 | 0.0000 |

299 dos 300 trials de `ruin_recreate` retornam um custo idêntico bit a bit ao de antes
da perturbação; o único diferente (`att532`) é ligeiramente *pior*.

**H9b** (reinserção randomizada):

| instância | modo | n | hit% | mean_delta | mean_rel% | identical% |
|---|---|---:|---:|---:|---:|---:|
| eil51 | double_bridge | 100 | 48.0 | 131.98 | 1.2469 | 27.0 |
| eil51 | ruin_recreate_v2 | 100 | 46.0 | 111.93 | 1.0795 | 38.0 |
| kroA100 | double_bridge | 100 | 56.0 | 8906.44 | 0.8614 | 13.0 |
| kroA100 | ruin_recreate_v2 | 100 | 23.0 | 1725.71 | 0.1707 | 68.0 |
| rat195 | double_bridge | 100 | 65.0 | 1206.47 | 0.5259 | 4.0 |
| rat195 | ruin_recreate_v2 | 100 | 36.0 | 662.08 | 0.2876 | 54.0 |

`identical%` cai de ~99,7% para 27–68%, mas a variante perde nas 3 instâncias em hit%
(23–46% vs 48–65%) e em ganho médio (0,17–1,08% vs 0,53–1,25%).

**H9c** (Shaw removal):

| instância | modo | n | hit% | mean_delta | mean_rel% | identical% |
|---|---|---:|---:|---:|---:|---:|
| eil51 | double_bridge | 100 | 37.0 | 10.54 | 0.0945 | 26.0 |
| eil51 | shaw_removal | 100 | 36.0 | 5.08 | 0.0397 | 30.0 |
| kroA100 | double_bridge | 100 | 41.0 | 1200.37 | 0.1080 | 33.0 |
| kroA100 | shaw_removal | 100 | 25.0 | 1373.38 | 0.1319 | 63.0 |
| rat195 | double_bridge | 100 | 49.0 | 174.53 | 0.0717 | 5.0 |
| rat195 | shaw_removal | 100 | 27.0 | 112.01 | 0.0486 | 39.0 |

Empata em `eil51` e perde claramente em hit% em `kroA100` e `rat195`; `identical%`
continua alto (30–63%).

## Por que não funcionou

Não é o padrão nulo de [H1](h1-adaptive-diversification.md)/[H2](h2-elite-path-relinking.md)/[H4](h4-multi-improvement.md)/[H6](h6-lookahead-construction.md),
em que o mecanismo funciona e o RVND absorve a vantagem. Aqui o mecanismo não perturba.
Partindo de um ótimo local do RVND, que já inclui a vizinhança de reinserção/or-opt, a
posição de custo mínimo de cada cliente removido é justamente a posição de onde ele saiu.
"Remover `k` clientes e reinserir cada um na melhor posição" sobre uma rota já localmente
ótima para reinserção desfaz a remoção. Por isso o teste de corretude em `eil51`, que
reconstruiu a rota original, não era peculiaridade de instância pequena.

A randomização top-3 e a remoção correlacionada reduzem o colapso, mas o repair continua
guloso: o top-3 tende a incluir a posição de origem ou vizinhas equivalentes, e o repair
puxa de volta para o mesmo vale com mais força do que o corte cego do double-bridge
escapa dele. O double-bridge funciona porque força uma reconexão topológica que a busca
local e um repair guloso de movimento único não desfazem trivialmente. Retomar essa linha
exigiria um repair qualitativamente diferente (por exemplo, 2-opt/or-opt completo em vez
de só inserção), o que reinventaria parte do RVND.

## Limitações

- Só diagnóstico de escape a partir de ótimos locais; nada rodou dentro do GILS-RVND.
- Parâmetros não variados: `k=8`, `TOP_M=3`, métrica de seleção de cliente/posição.
- H9 usou instâncias grandes; H9b/H9c, só instâncias pequenas (n=51/100/195).

## Referências

- Ropke, S., Pisinger, D. (2006). An adaptive large neighborhood search heuristic for
  the pickup and delivery problem with time windows.
  https://www.researchgate.net/publication/220413334
- Shaw, P. (1998). Using Constraint Programming and Local Search Methods to Solve
  Vehicle Routing Problems. *CP-98*, LNCS 1520.
