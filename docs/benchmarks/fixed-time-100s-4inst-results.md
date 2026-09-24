# Resultados — comparação a tempo fixo de 100 s (4 instâncias, n = 226..532)

> O mesmo confronto (`gils_am_rvnd --rvnd-mode candidate --cand-k 12` vs
> `mdm_gils_rvnd`, 100 s) é remedido em outro lote, só em `lin318`/`pr439`/`att532`, em
> [h16-candidate-neighborhoods](../hypotheses/h16-candidate-neighborhoods.md), que é a referência
> principal. Este documento acrescenta o `gils_rvnd` e a instância `pr226`.

**Resumo:** a 100 s por execução (4 instâncias × 3 algoritmos × 10 seeds, 120
execuções pareadas), o GILS-AM-RVND com vizinhanças podadas por candidatos
(`gils_am_rvnd_cand`) bate o MDM-GILS-RVND em −0,405% agregado (26/10/4, p = 0,00006) e
o GILS-RVND em −0,465% (26/10/4, p = 0,00006). O MDM continua nulo contra o GILS-RVND
(−0,060%, 13/19/8, p = 0,38331). O ganho vem da vazão: o `cand` completa de 3,1× a
4,7× mais reinícios que o MDM no mesmo tempo.

## O que foi testado

`gils_am_rvnd_cand` = `./bin/gils_am_rvnd --rvnd-mode candidate --cand-k 12`, o
algoritmo de [H16](../hypotheses/h16-candidate-neighborhoods.md): swap, 2-opt, or-opt direto 1–6 e
or-opt invertido 2–6, cada varredura restrita aos 12 vizinhos mais próximos, sobre
dados de subsequência em O(n). Contra `gils_rvnd` e `mdm_gils_rvnd`, 100 s de
wall-clock por execução, execuções sequenciais, pareadas por seed, em `pr226`,
`lin318`, `pr439` e `att532`.

## Resultados

Gap médio de BKS (`instances/solutions/best_solutions.json`) sobre as 10 seeds:

| instância | GILS-RVND | MDM-GILS-RVND | GILS-AM-RVND-cand |
|---|---:|---:|---:|
| `pr226` | **0.000%** | **0.000%** | **0.000%** |
| `lin318` | 0.575% | 0.363% | **0.268%** |
| `pr439` | 1.269% | 1.323% | **0.776%** |
| `att532` | 1.953% | 1.866% | **0.861%** |
| **média** | 0.949% | 0.888% | **0.476%** |

Comparação pareada (`mean_rel%` = média de `(custo_A − custo_B)/custo_B`, negativo = A
melhor; `p` = teste dos sinais bilateral exato):

| instância | cand vs MDM | W/T/L | p | cand vs GILS | W/T/L | p | MDM vs GILS | W/T/L | p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `pr226` | +0.000 | 0/10/0 | 1.000 | +0.000 | 0/10/0 | 1.000 | +0.000 | 0/10/0 | 1.000 |
| `lin318` | -0.095 | 8/0/2 | 0.109 | -0.305 | 9/0/1 | **0.021** | -0.210 | 7/3/0 | **0.016** |
| `pr439` | -0.539 | 8/0/2 | 0.109 | -0.486 | 7/0/3 | 0.344 | +0.053 | 2/4/4 | 0.688 |
| `att532` | -0.986 | 10/0/0 | **0.002** | -1.071 | 10/0/0 | **0.002** | -0.085 | 4/2/4 | 1.000 |
| **AGREGADO** | **-0.405** | **26/10/4** | **0.00006** | **-0.465** | **26/10/4** | **0.00006** | **-0.060** | **13/19/8** | 0.38331 |

Reinícios completados em 100 s:

| instância | GILS-RVND | MDM-GILS-RVND | GILS-AM-RVND-cand | fator vs MDM |
|---|---:|---:|---:|---:|
| `pr226` | 622 | 633 | 1946 | 3.1× |
| `lin318` | 189 | 184 | 869 | 4.7× |
| `pr439` | 97 | 94 | 304 | 3.2× |
| `att532` | 51 | 50 | 217 | 4.4× |

O tempo médio gasto foi 100,0 s nos três (máximo 100,1 s): `--max-time` só é checado
entre iterações de ILS e entre reinícios, mas o estouro ficou desprezível.

## Por que funcionou

O mecanismo é vazão de reinícios, não profundidade do ótimo local: a tempo fixo, vence
quem visita mais ótimos locais. Por isso o efeito cresce com `n`: `pr226` está saturada
a 100 s (os três empatam) e a vantagem aparece de `lin318` em diante, com o máximo em
`att532`. O MDM, nulo contra o GILS-RVND, é consistente com [H13](../hypotheses/h13-mdm-gils-rvnd.md)
e com o próprio artigo do MDM, que também não achou diferença estatística no conjunto
de 10 instâncias TSPLIB.

## Limitações

- A poda por candidatos poderia ser portada para o `mdm_gils_rvnd`, que aqui ainda
  varre O(n²) completo: parte da vantagem é engenharia de vizinhança, não estratégia de
  busca. Os dados de subsequência em O(n) já beneficiam os três binários neste lote.
- Os dados brutos foram gravados em `results/fixed-time/fixed_time_100s.json`, mas esse
  checkpoint hoje contém o lote do [H16](../hypotheses/h16-candidate-neighborhoods.md) (sem
  `gils_rvnd` e sem `pr226`); as execuções deste documento não estão mais nele.
