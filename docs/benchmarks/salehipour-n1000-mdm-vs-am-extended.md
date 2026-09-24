# GILS-RVND vs GILS-AM-RVND (extended-oropt) vs MDM-GILS-RVND — Salehipour n=1000

> Os scripts e dados brutos em `scripts/` citados neste documento foram removidos do
> repositório e estão preservados na tag git `archive/h-scripts`
> (`git show archive/h-scripts:scripts/<arquivo>`).

**Resumo:** no tier `n=1000` do benchmark de Salehipour (20 instâncias × 10 seeds),
`gils_am_rvnd --rvnd-mode extended-oropt` bate o `gils_rvnd` em 162/0/38 pares
(mean_rel −0,782%, p<0,0001), com 8 das 20 instâncias significativas individualmente
(p<0,05) e tempo +48,9%. É a confirmação mais forte de
[H12](../hypotheses/h12-extended-oropt.md). O braço `mdm_gils_rvnd` está **não concluído**: os
dados sob `--imax 1` são inválidos (a mineração nunca dispara) e a re-execução sob
`--imax 2` não tem resultados registrados aqui. Complementa
[salehipour-tsplib-mdm-vs-am-extended](salehipour-tsplib-mdm-vs-am-extended.md)
(mesma comparação em n=10 a 500).

## Protocolo

Instâncias `TRP-S1000-R1`...`TRP-S1000-R20`, 10 seeds, comparação pareada por seed.
O protocolo do artigo (`--imax 10`) custaria ~3,2h por execução em `n=1000` (~13–14
dias para o lote, mesmo com 6 núcleos). Por isso, seguindo o precedente de
[H12](../hypotheses/h12-extended-oropt.md) (lote em `rand1000`), `gils_rvnd` e
`gils_am_rvnd_extended_oropt` rodaram com `--imax 1 --iils 100` (~6 min por execução
na calibração; o lote real levou mais que as ~13–16h estimadas).

## Bug de protocolo: `mdm_gils_rvnd` com `--imax 1` nunca mina

[`src/mdm_gils_rvnd.cpp`](../../src/mdm_gils_rvnd.cpp) divide `I_max` em duas fases:
GILS-RVND puro (constrói o elite set) e construção guiada por padrões minerados, com
`phase1Iters = max(1, I_max / 2)`. Com `I_max=1`, `phase1Iters = 1` e a única iteração
(`i=0`) nunca satisfaz `i >= phase1Iters`: o algoritmo se reduz a `gils_rvnd`, sem
erro aparente. Os resultados coletados saíram bit a bit idênticos ao `gils_rvnd`
(W/T/L 0/200/0). É a mesma armadilha do path relinking do
[H2](../hypotheses/h2-elite-path-relinking.md) sob `--imax 1`: um parâmetro de orçamento que desliga
o mecanismo testado.

O menor orçamento que exercita a mineração é `--imax 2` (`i=0` fase 1, `i=1` fase 2),
ainda muito abaixo do `--imax 10` do artigo. `gils_rvnd` e
`gils_am_rvnd_extended_oropt` não têm divisão de fases e seus resultados sob
`--imax 1` continuam válidos.

## Resultados: `gils_rvnd` vs `gils_am_rvnd_extended_oropt`

| Instance | GILS-RVND Best | GILS-RVND Avg | GILS-RVND Time(s) | AM+ext-oropt Best | AM+ext-oropt Avg | AM+ext-oropt Gap%(avg) | AM+ext-oropt Time(s) | AM+ext-oropt W/T/L | AM+ext-oropt p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| TRP-S1000-R1 | 5,121,975 | 5,209,123.4 | 1244.63 | 5,112,760 | 5,157,690.2 | -0.987% | 2290.46 | 8/0/2 | 0.109 |
| TRP-S1000-R2 | 5,175,987 | 5,233,157.3 | 1487.63 | 5,137,491 | 5,201,163.6 | -0.611% | 1902.22 | 7/0/3 | 0.344 |
| TRP-S1000-R3 | 5,204,384 | 5,259,816.3 | 1462.97 | 5,185,178 | 5,218,332.8 | -0.789% | 2290.48 | 8/0/2 | 0.109 |
| TRP-S1000-R4 | 5,176,277 | 5,226,389.1 | 1501.65 | 5,132,523 | 5,181,181.5 | -0.865% | 2292.44 | 8/0/2 | 0.109 |
| TRP-S1000-R5 | 5,132,246 | 5,180,131.7 | 1382.59 | 5,051,097 | 5,112,637.0 | -1.303% | 2063.54 | 10/0/0 | 0.002 |
| TRP-S1000-R6 | 5,169,054 | 5,198,725.5 | 1656.21 | 5,123,232 | 5,155,754.8 | -0.827% | 2360.32 | 9/0/1 | 0.021 |
| TRP-S1000-R7 | 5,125,080 | 5,179,786.2 | 1704.09 | 5,106,348 | 5,136,605.0 | -0.834% | 2156.18 | 9/0/1 | 0.021 |
| TRP-S1000-R8 | 5,237,335 | 5,295,837.8 | 1657.36 | 5,184,140 | 5,253,288.8 | -0.803% | 3103.19 | 8/0/2 | 0.109 |
| TRP-S1000-R9 | 5,101,719 | 5,150,357.3 | 2193.56 | 5,057,592 | 5,088,112.0 | -1.209% | 2852.46 | 10/0/0 | 0.002 |
| TRP-S1000-R10 | 5,057,085 | 5,154,548.9 | 1584.71 | 5,032,990 | 5,106,141.7 | -0.939% | 2094.73 | 7/0/3 | 0.344 |
| TRP-S1000-R11 | 5,250,743 | 5,301,919.9 | 1397.39 | 5,230,010 | 5,269,333.2 | -0.615% | 2059.95 | 7/0/3 | 0.344 |
| TRP-S1000-R12 | 5,123,264 | 5,161,613.1 | 1273.44 | 5,059,576 | 5,112,593.0 | -0.950% | 2252.96 | 9/0/1 | 0.021 |
| TRP-S1000-R13 | 5,156,169 | 5,200,331.9 | 1436.25 | 5,143,408 | 5,187,354.6 | -0.250% | 2481.81 | 6/0/4 | 0.754 |
| TRP-S1000-R14 | 5,129,048 | 5,175,292.0 | 1429.51 | 5,080,526 | 5,117,130.4 | -1.124% | 3223.89 | 9/0/1 | 0.021 |
| TRP-S1000-R15 | 5,133,713 | 5,175,527.0 | 2000.21 | 5,044,190 | 5,124,835.9 | -0.979% | 3169.43 | 9/0/1 | 0.021 |
| TRP-S1000-R16 | 5,115,428 | 5,162,480.5 | 2082.53 | 5,096,702 | 5,114,206.6 | -0.935% | 2654.20 | 9/0/1 | 0.021 |
| TRP-S1000-R17 | 5,144,703 | 5,199,027.2 | 1511.48 | 5,155,249 | 5,169,483.6 | -0.568% | 2047.46 | 7/0/3 | 0.344 |
| TRP-S1000-R18 | 5,171,111 | 5,212,510.4 | 1685.32 | 5,164,828 | 5,186,926.9 | -0.491% | 1965.54 | 8/0/2 | 0.109 |
| TRP-S1000-R19 | 5,071,631 | 5,107,013.7 | 1417.74 | 5,029,803 | 5,087,797.6 | -0.376% | 1913.49 | 8/0/2 | 0.109 |
| TRP-S1000-R20 | 5,115,585 | 5,155,043.5 | 1287.07 | 5,085,927 | 5,145,061.4 | -0.194% | 1566.72 | 6/0/4 | 0.754 |

**Agregado (200 pares):** mean_rel −0,782%, W/T/L 162/0/38, p<0,0001; tempo médio
1569,8 s (`gils_rvnd`) vs 2337,1 s (AM+ext-oropt), +48,9%.

Oito instâncias são significativas sozinhas com N=10 (`R5`, `R6`, `R7`, `R9`, `R12`,
`R14`, `R15`, `R16`), contra 6/20 em `n=500`. A magnitude também é a maior observada:
−0,78%, contra −0,28% em n=500 e −0,04% no agregado do tier anterior. O AM+ext-oropt
nunca perde no agregado por instância (o placar mais fraco é 6/0/4).

## Resultados: `mdm_gils_rvnd`

Não concluído. Os valores sob `--imax 1` não devem ser usados (ver acima), e não há
resultados sob `--imax 2` registrados neste documento.

## Limitações

- `--imax 1` em vez do `--imax 10` do artigo, por custo de tempo.
- O lote foi pausado e retomado duas vezes; o tempo decorrido total é maior que o de
  computação efetivo.
