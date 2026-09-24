# Comparação com tempo fixo (100 s/execução) — GILS-RVND vs AM+extended-oropt vs MDM-GILS-RVND

> Superado: medido com binários anteriores à otimização da busca local (os dados de
> subsequência em O(n) de [h16-candidate-neighborhoods](../hypotheses/h16-candidate-neighborhoods.md), que acelerou os três
> binários em 2,4–2,9x), e por isso não comparável com lotes de 100 s posteriores. Os
> números atuais, remedidos do zero nas instâncias com n > 200, estão em
> [h16-candidate-neighborhoods](../hypotheses/h16-candidate-neighborhoods.md) e
> [h19-dlb-fast-regime](../hypotheses/h19-dlb-fast-regime.md).

**Resumo.** 300 execuções (10 instâncias TSPLIB, *Hamiltonian Path*, n = 70..532 × 3
algoritmos × 10 seeds), 100 s de wall-clock por execução, sequenciais e pareadas por seed,
protocolo de [fixed-time-protocol](fixed-time-protocol.md). Todas as instâncias até `pr226`,
exceto `rat195`, saturam
(empates `0/10/0`, exceto uma derrota do `mdm` em `pr226`, `0/9/1`). Contra o `gils_rvnd`, o `gils_am_rvnd --rvnd-mode
extended-oropt` vence a tempo igual: −0,118% agregado, 33/61/6, p < 0,0001, gap médio de
BKS de 0,474% para 0,354%, significativo em `rat195` (−0,348%), `lin318` (−0,400%) e
`att532` (−0,427%). O `mdm_gils_rvnd` é nulo: −0,001%, 12/75/13, p = 1,0. O protocolo é
válido: mesmo em `att532` há 15–16 restarts por execução, e a mineração do `mdm` disparou
em 100/100 execuções.

## Pergunta

É a comparação de "running time as stopping criterion" do artigo do MDM-GILS-RVND
(arXiv:1908.10705, Seção 5.3.3), complementando
[mdm-vs-am-extended-tsplib-comparison](mdm-vs-am-extended-tsplib-comparison.md), que
compara os mesmos três algoritmos a iterações fixas: as vantagens se mantêm com o mesmo
orçamento de tempo (`--max-time 100`, `I_max` efetivamente ilimitado)?

## Resultados

Custo mínimo (`Best`) e médio (`Avg`) das 10 seeds, e gap médio em relação ao BKS.

| Instância | n | BKS | GILS-RVND Best | GILS-RVND Avg | GILS-RVND Gap% | AM+extended-oropt Best | AM+extended-oropt Avg | AM+extended-oropt Gap% | MDM-GILS-RVND Best | MDM-GILS-RVND Avg | MDM-GILS-RVND Gap% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| st70 | 70 | 19 215 | 19 215 | 19 215.0 | 0.000 | 19 215 | 19 215.0 | 0.000 | 19 215 | 19 215.0 | 0.000 |
| rat99 | 99 | 54 984 | 54 984 | 54 984.0 | 0.000 | 54 984 | 54 984.0 | 0.000 | 54 984 | 54 984.0 | 0.000 |
| kroD100 | 100 | 949 594 | 949 594 | 949 594.0 | 0.000 | 949 594 | 949 594.0 | 0.000 | 949 594 | 949 594.0 | 0.000 |
| lin105 | 105 | 585 823 | 585 823 | 585 823.0 | 0.000 | 585 823 | 585 823.0 | 0.000 | 585 823 | 585 823.0 | 0.000 |
| pr107 | 107 | 1 980 767 | 1 980 767 | 1 980 767.0 | 0.000 | 1 980 767 | 1 980 767.0 | 0.000 | 1 980 767 | 1 980 767.0 | 0.000 |
| rat195 | 195 | 210 191 | 210 305 | 211 005.0 | 0.387 | 210 191 | 210 271.3 | 0.038 | 210 305 | 210 918.8 | 0.346 |
| pr226 | 226 | 7 100 308 | 7 100 308 | 7 100 308.0 | 0.000 | 7 100 308 | 7 100 308.0 | 0.000 | 7 100 308 | 7 100 335.3 | 0.000 |
| lin318 | 318 | 5 560 679 | 5 565 187 | 5 601 310.1 | 0.731 | 5 562 365 | 5 578 865.6 | 0.327 | 5 565 187 | 5 598 699.6 | 0.684 |
| pr439 | 439 | 17 688 561 | 17 886 301 | 17 955 310.8 | 1.508 | 17 876 876 | 17 953 476.8 | 1.498 | 17 886 301 | 17 960 847.8 | 1.539 |
| att532 | 532 | 5 589 568 | 5 688 768 | 5 707 473.3 | 2.109 | 5 666 399 | 5 683 097.2 | 1.673 | 5 688 768 | 5 709 905.9 | 2.153 |
| **Média** | | | | | **0.474** | | | **0.354** | | | **0.472** |

`pr439` é a exceção do AM (5/0/5, −0,009%): é onde ele teve menos restarts (15, contra 34
do baseline). O estouro de tempo sobre os 100 s foi de ~3,5 a 4 s e praticamente igual
nos três algoritmos.
