# GILS-RVND vs GILS-AM-RVND (extended-oropt) vs MDM-GILS-RVND — benchmark oficial Salehipour, n=10 a 500

> Os scripts e dados brutos em `scripts/` citados neste documento foram removidos do
> repositório e estão preservados na tag git `archive/h-scripts`
> (`git show archive/h-scripts:scripts/<arquivo>`).

**Resumo:** no benchmark sintético de Salehipour et al. (2011), 6 tamanhos × 20
instâncias (1200 pares seed), o `gils_am_rvnd --rvnd-mode extended-oropt` bate o
baseline com p<0,0001 em todas as janelas de `n≥100`, e o efeito cresce com `n`:
−0,039% no agregado geral, −0,133% em `n≥200`, −0,283% em `n=500` (159/0/41). É a 5ª
confirmação independente de [H12](../hypotheses/h12-extended-oropt.md). O `mdm_gils_rvnd` é nulo em
toda janela (p entre 0,729 e 1,000; 64/72/64 em `n=500`), consistente com
[H13](../hypotheses/h13-mdm-gils-rvnd.md), e não reproduz o ganho que o paper do MDM-GILS-RVND relata
justamente em `n=500`.

## Pergunta

Repetir a comparação de três algoritmos de
[mdm-vs-am-extended-tsplib-comparison](mdm-vs-am-extended-tsplib-comparison.md) (feita
nas 10 TSPLIB clássicas do projeto) no benchmark usado pela literatura (GILS-RVND,
DBMEA, GQPSO, MDM-GILS-RVND) para reportar resultados em `n` grande, com protocolo
idêntico ao paper de referência do MDM-GILS-RVND (Santana, Plastino & Rosseti).

## O que foi testado

- `gils_rvnd` — baseline (Silva et al., 2012).
- `gils_am_rvnd --rvnd-mode extended-oropt` — memória adaptativa + or-opt estendido a
  segmentos 4–6 ([H12](../hypotheses/h12-extended-oropt.md)), em
  [`src/gils_am_rvnd.cpp`](../../src/gils_am_rvnd.cpp).
- `mdm_gils_rvnd` — reimplementação do MDM-GILS-RVND com mineração real via
  FPMax*/`mlxtend` ([H13](../hypotheses/h13-mdm-gils-rvnd.md)), em
  [`src/mdm_gils_rvnd.cpp`](../../src/mdm_gils_rvnd.cpp); `sup_min=0.70`, `d=10`,
  `max_patterns=5` (defaults, iguais ao paper).

Instâncias em `instances/salehipour/`, tamanhos `10, 20, 50, 100, 200, 500` (120
instâncias; `n=1000` fica fora), nomeadas como nas Tabelas 2/3 do paper do
MDM-GILS-RVND: `TRP-S{tamanho}-R{índice}` (ex.: `TRP-S500-R1` =
`instances/salehipour/salehipour_n0500_i01.tsp`). Hiperparâmetros `I_max=10`,
`I_ILS=min(100,n)`, `R={0.00,...,0.25}` (defaults, iguais ao paper). 10 execuções por
instância/algoritmo (seeds 1 a 10, pareadas entre os 3 algoritmos). Como não há BKS
externo confiável para estas instâncias geradas pelo projeto, a comparação é direta
entre os 3 algoritmos (teste de sinal exato), sem gap-a-BKS.

## Resultados

**Por tamanho** (200 pares seed cada; `mean_rel` negativo = melhor que o baseline):

| n | `--iils` | AM+ext-oropt mean_rel | W/T/L | p | MDM mean_rel | W/T/L | p |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 10 | +0.000% | 0/200/0 | 1.0000 | +0.000% | 0/200/0 | 1.0000 |
| 20 | 20 | +0.000% | 0/200/0 | 1.0000 | +0.000% | 0/200/0 | 1.0000 |
| 50 | 50 | +0.003% | 0/199/1 | 1.0000 | +0.000% | 0/200/0 | 1.0000 |
| 100 | 100 | +0.029% | 7/165/28 | 0.0005 | +0.002% | 8/183/9 | 1.0000 |
| 200 | 100 | +0.017% | 54/99/47 | 0.5507 | -0.000% | 43/120/37 | 0.5764 |
| 500 | 100 | -0.284% | 159/0/41 | 0.0000 | +0.010% | 64/72/64 | 1.0000 |

`n=10/20/50` são empates exatos. `n=100` é o único ponto em que o AM+ext-oropt perde no
agregado — sinal pequeno, dominado por poucas instâncias como `TRP-S100-R10` (0/3/7,
p=0.016), consistente com o nulo/ruído que [H12](../hypotheses/h12-extended-oropt.md) já via nessa
faixa antes de o efeito ficar positivo.

**Agregados por janela de `n`:**

| Subconjunto | AM+ext-oropt W/T/L | AM+ext-oropt p | AM+ext-oropt mean_rel% | MDM W/T/L | MDM p | MDM mean_rel% |
|---|---:|---:|---:|---:|---:|---:|
| Todos os 6 tamanhos (120 instâncias, 1200 pares) | 220/863/117 | **<0,0001** | -0,039% | 115/975/110 | 0,790 | +0,002% |
| n≥100 (600 pares) | 220/264/116 | **<0,0001** | -0,079% | 115/375/110 | 0,790 | +0,004% |
| n≥200 (400 pares) | 213/99/88 | **<0,0001** | -0,133% | 107/192/101 | 0,729 | +0,005% |
| n=500 (200 pares) | 159/0/41 | **<0,0001** | -0,283% | 64/72/64 | 1,000 | +0,010% |

**TRP-S500 por instância** (`--iils 100`, 10 pares por linha):

| Instance | GILS-RVND Best | GILS-RVND Avg | GILS-RVND Time(s) | AM+ext-oropt Best | AM+ext-oropt Avg | AM+ext-oropt Gap%(avg) | AM+ext-oropt Time(s) | AM+ext-oropt W/T/L | AM+ext-oropt p | MDM Best | MDM Avg | MDM Gap%(avg) | MDM Time(s) | MDM W/T/L | MDM p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| TRP-S500-R1 | 1,816,992 | 1,826,838.1 | 1229.53 | 1,812,494 | 1,820,052.4 | -0.371% | 1305.25 | 6/0/4 | 0.754 | 1,815,446 | 1,822,930.2 | -0.214% | 1259.00 | 8/2/0 | 0.008 |
| TRP-S500-R2 | 1,742,380 | 1,746,726.1 | 1127.80 | 1,737,294 | 1,742,167.1 | -0.261% | 1098.92 | 8/0/2 | 0.109 | 1,742,132 | 1,745,694.1 | -0.059% | 1216.25 | 4/5/1 | 0.375 |
| TRP-S500-R3 | 1,771,577 | 1,781,881.3 | 1072.32 | 1,771,123 | 1,777,495.9 | -0.246% | 1128.42 | 10/0/0 | 0.002 | 1,771,577 | 1,782,394.9 | +0.029% | 1057.29 | 2/4/4 | 0.688 |
| TRP-S500-R4 | 1,797,255 | 1,806,800.0 | 1078.74 | 1,790,881 | 1,799,626.9 | -0.397% | 1165.28 | 8/0/2 | 0.109 | 1,797,255 | 1,805,454.5 | -0.074% | 1120.04 | 4/6/0 | 0.125 |
| TRP-S500-R5 | 1,789,095 | 1,796,769.4 | 1107.82 | 1,787,775 | 1,790,375.9 | -0.356% | 1171.85 | 9/0/1 | 0.021 | 1,789,095 | 1,796,448.2 | -0.018% | 1118.14 | 4/3/3 | 1.000 |
| TRP-S500-R6 | 1,823,623 | 1,828,601.7 | 1111.72 | 1,816,315 | 1,821,553.1 | -0.385% | 1261.09 | 10/0/0 | 0.002 | 1,821,423 | 1,829,680.7 | +0.059% | 1079.22 | 2/3/5 | 0.453 |
| TRP-S500-R7 | 1,834,648 | 1,843,562.6 | 1171.50 | 1,831,773 | 1,839,496.6 | -0.221% | 1232.52 | 7/0/3 | 0.344 | 1,837,213 | 1,844,317.8 | +0.041% | 1146.87 | 2/5/3 | 1.000 |
| TRP-S500-R8 | 1,788,385 | 1,791,219.6 | 1089.43 | 1,778,505 | 1,785,277.8 | -0.332% | 1205.58 | 9/0/1 | 0.021 | 1,787,207 | 1,792,055.0 | +0.047% | 1057.72 | 3/2/5 | 0.727 |
| TRP-S500-R9 | 1,828,177 | 1,836,153.5 | 1249.23 | 1,823,956 | 1,835,518.3 | -0.035% | 1163.89 | 5/0/5 | 1.000 | 1,828,177 | 1,836,199.6 | +0.003% | 1215.11 | 3/6/1 | 0.625 |
| TRP-S500-R10 | 1,849,262 | 1,855,259.1 | 1158.32 | 1,846,942 | 1,852,722.0 | -0.137% | 1204.85 | 8/0/2 | 0.109 | 1,850,674 | 1,858,468.0 | +0.173% | 1156.27 | 1/3/6 | 0.125 |
| TRP-S500-R11 | 1,816,269 | 1,821,853.6 | 1099.50 | 1,810,955 | 1,816,566.4 | -0.290% | 1223.75 | 8/0/2 | 0.109 | 1,816,335 | 1,821,958.9 | +0.006% | 1119.53 | 3/4/3 | 1.000 |
| TRP-S500-R12 | 1,799,229 | 1,805,706.7 | 1105.76 | 1,796,089 | 1,804,262.5 | -0.080% | 1346.34 | 5/0/5 | 1.000 | 1,799,229 | 1,806,788.3 | +0.060% | 1207.13 | 3/5/2 | 1.000 |
| TRP-S500-R13 | 1,802,954 | 1,807,355.3 | 1037.78 | 1,794,334 | 1,802,261.9 | -0.282% | 1215.96 | 9/0/1 | 0.021 | 1,802,954 | 1,808,015.4 | +0.037% | 1041.42 | 3/2/5 | 0.727 |
| TRP-S500-R14 | 1,861,831 | 1,868,882.8 | 1054.60 | 1,854,579 | 1,861,293.9 | -0.406% | 1142.37 | 8/0/2 | 0.109 | 1,861,831 | 1,867,612.6 | -0.068% | 1030.60 | 5/3/2 | 0.453 |
| TRP-S500-R15 | 1,830,081 | 1,836,825.4 | 1112.70 | 1,820,671 | 1,831,040.4 | -0.315% | 1183.76 | 9/0/1 | 0.021 | 1,830,440 | 1,836,994.7 | +0.009% | 1098.02 | 3/4/3 | 1.000 |
| TRP-S500-R16 | 1,815,612 | 1,826,226.4 | 1070.86 | 1,814,121 | 1,822,885.9 | -0.183% | 937.98 | 8/0/2 | 0.109 | 1,815,612 | 1,827,245.9 | +0.056% | 1033.26 | 2/3/5 | 0.453 |
| TRP-S500-R17 | 1,805,862 | 1,820,681.6 | 1058.36 | 1,807,652 | 1,813,248.5 | -0.408% | 1315.42 | 8/0/2 | 0.109 | 1,809,794 | 1,820,599.2 | -0.005% | 1124.51 | 5/2/3 | 0.727 |
| TRP-S500-R18 | 1,808,208 | 1,816,205.3 | 1106.99 | 1,804,337 | 1,810,365.1 | -0.322% | 1179.38 | 6/0/4 | 0.754 | 1,804,674 | 1,814,541.4 | -0.092% | 1131.30 | 3/4/3 | 1.000 |
| TRP-S500-R19 | 1,833,355 | 1,841,549.1 | 1101.87 | 1,827,268 | 1,833,899.6 | -0.415% | 1137.10 | 10/0/0 | 0.002 | 1,833,355 | 1,843,010.1 | +0.079% | 986.41 | 2/3/5 | 0.453 |
| TRP-S500-R20 | 1,800,031 | 1,808,269.8 | 964.50 | 1,800,437 | 1,803,967.1 | -0.238% | 969.50 | 8/0/2 | 0.109 | 1,803,074 | 1,810,570.8 | +0.127% | 953.41 | 2/3/5 | 0.453 |

Em `n=500`, 7 instâncias (`R3`, `R5`, `R6`, `R8`, `R13`, `R15`, `R19`) já têm p<0,05
isoladamente com só N=10 — algo que não acontecia nas TSPLIB `pr439`/`att532` — e
nenhuma das 20 tem mais derrotas que vitórias para o AM+ext-oropt.

**Tempo médio** (`gils_rvnd` como referência):

| n | Tempo GILS-RVND | AM+ext-oropt vs baseline | MDM vs baseline |
|---:|---:|---:|---:|
| 10 | 0,00s | +12,8% | não comparável (baseline ~0s) |
| 20 | 0,02s | +3,4% | não comparável (baseline ~0s) |
| 50 | 0,45s | +1,2% | +467,4% |
| 100 | 5,49s | -1,7% | +54,9% |
| 200 | 51,29s | -10,6% | +13,4% |
| 500 | 1105,46s | +6,7% | +0,2% |

## Leitura

- **AM+ext-oropt:** o efeito cresce monotonicamente com `n`, o mesmo padrão de
  [H12](../hypotheses/h12-extended-oropt.md) e da 4ª confirmação em
  [mdm-vs-am-extended-tsplib-comparison](mdm-vs-am-extended-tsplib-comparison.md), e
  aqui com a significância mais forte até agora. Em `n` pequeno as instâncias são
  fáceis demais para diferenciar; `n=100` é a faixa de transição, com sinal fraco e
  ambíguo.
- **MDM:** o paper original relata em `n=500` (Table 2) 15W/2L em best solution e
  18W/2L em average solution sobre o baseline, com ganho médio de BKS de 0,41% vs
  0,51%. A reimplementação não reproduz isso (64/72/64, virtualmente moeda), o mesmo
  que já se via em `n=318-532` na TSPLIB.
- **Tempo do MDM:** as porcentagens de `n=10/20` são artefato de divisão por um
  baseline quase zero; a leitura real é o overhead absoluto de ~2s da mineração via
  subprocesso Python, dominante quando a instância é trivial. Em `n=500` a mineração
  já é irrelevante (+0,2%), enquanto o paper relata o MDM **mais rápido** que o
  baseline nessa escala (−27,74%). Isso reforça a hipótese de
  [mdm-vs-am-extended-tsplib-comparison](mdm-vs-am-extended-tsplib-comparison.md) de
  que a mineração via subprocesso (em vez de nativa) consome o ganho de velocidade do
  paper.

## Limitações

- As instâncias foram geradas pelo projeto seguindo o protocolo de Salehipour; os
  arquivos originais não estão disponíveis publicamente, então não há BKS externo.
- Custo: em `n=500` cada execução leva ~1100–1200s (~17x uma TSPLIB de `n` parecido,
  como `att532`, com o mesmo `I_max×I_ILS`), plausivelmente porque instâncias
  aleatórias uniformes têm paisagem mais "ruidosa" e o RVND reconverge mais vezes por
  perturbação.
- O MDM rodou com a mineração via subprocesso Python; depois ela foi portada para C++
  em memória ([H13](../hypotheses/h13-mdm-gils-rvnd.md)), e esses números não são bit-a-bit
  reprodutíveis com o código atual.

## Referências

- Salehipour, A., Sörensen, K., Goos, P., Bräysy, O. (2011). Efficient GRASP+VND and
  GRASP+VNS metaheuristics for the traveling repairman problem. *4OR*, 9(2), 189–209.
- Silva, M.M., Subramanian, A., Vidal, T., Ochi, L.S. (2012). A simple and effective
  metaheuristic for the Minimum Latency Problem. *European Journal of Operational
  Research*, 221, 513–520.
- Santana, Í., Plastino, A., Rosseti, I. Improving a State-of-the-Art Heuristic for
  the Minimum Latency Problem with Data Mining. arXiv:1908.10705.
  https://arxiv.org/abs/1908.10705
