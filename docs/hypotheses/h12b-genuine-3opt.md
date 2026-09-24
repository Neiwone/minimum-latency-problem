# H12b — 3-opt genuíno (reversão dupla independente)

> Os scripts e dados brutos em `scripts/` citados neste documento foram removidos do
> repositório e estão preservados na tag git `archive/h-scripts`
> (`git show archive/h-scripts:scripts/<arquivo>`).

**Veredito: refutada.** O diagnóstico mostrava sinal real mas esparso (5/15 ótimos
locais melhoráveis), mas o lote pareado (42 pares, interrompido com `att532` em 7/10) é
ruído: mean_rel 0,0318%, 21/5/16, p=0,511, a um custo de tempo de +170% agregado e até
+494% em `pr439`. Não adotado.

## Hipótese

Depois de o [H12](h12-extended-oropt.md) mostrar que fortalecer a vizinhança é produtivo,
o candidato seguinte era o 3-opt. Com 3 cortes (blocos A-B-C-D, A fixo por conter o
depósito), quase todas as reconexões já são alcançáveis por um 2-opt ou por or-opt. A
única genuinamente nova é reverter B e C independentemente, mantendo a ordem:
`A + rev(B) + rev(C) + D`.

## O que foi testado

A avaliação O(1) via T/C/Cr está em [`src/solution.cpp`](../../src/solution.cpp) e a
vizinhança em [`src/neighborhoods.cpp`](../../src/neighborhoods.cpp);
`gils_rvnd --rvnd-mode extended-oropt-3opt` roda as 8 vizinhanças do H12 mais esta.

**Diagnóstico** ([`src/diag_3opt.cpp`](../../src/diag_3opt.cpp)): a partir de ótimos
locais de `extended-oropt`, testa todos os O(n³) triplos (~30–170 ms por varredura).
Achou melhoria em 1/5 trials de `lin318` (−0,07%), 3/5 de `pr439` (uma grande: 122
movimentos simultâneos, −0,94%) e 1/5 de `att532` (−0,05%): menos consistente que o
12/15 do H12, mas longe do quase-zero de H9/H10.

**Calibração** (1 seed, `lin318`, `--imax 5 --iils 100`): `extended-oropt` 84,2 s vs
`extended-oropt-3opt` 343,5 s (4,1× mais lento), com empate exato em custo (5.562.365).

## Resultados

Lote pareado contra `extended-oropt`, na escala do H12 (`lin318` imax=5/N=20, `pr439`
imax=3/N=15, `att532` imax=2/N=10). Interrompido depois de `lin318` e `pr439` completos e
`att532` em 7/10: o sinal já estava claro e o custo escalava mal (seeds de `att532` de
15–34 min cada, parte inflada por contenção de CPU com outro lote em paralelo).

| instance | n | mean_rel% | w/t/l | sign_p | time+% |
|---|---:|---:|---:|---:|---:|
| lin318 | 20 | 0,0317 | 9/5/6 | 0,607 | 414,2 |
| pr439 | 15 | 0,0037 | 7/0/8 | 1,000 | 494,1 |
| att532 | 7 | 0,0923 | 5/0/2 | 0,453 | 37,8 |
| AGREGADO | 42 | 0,0318 | 21/5/16 | 0,511 | 169,8 |

`pr439` é quase uma moeda (7/0/8); o pior custo/benefício de todas as hipóteses
testadas.

## Por que não funcionou

A oportunidade crua existe e às vezes é grande, mas é rara e imprevisível. Espalhada por
um ILS com centenas de reconvergências, o ganho ocasional do 3-opt fica indistinguível
do que o double-bridge + `extended-oropt` já achariam por sorte, e o preço é varrer O(n³)
candidatos (contra O(n²) de todo o resto) em toda reconvergência, mesmo quando nenhum
melhora. No H12 a vizinhança extra pagava seu custo na maioria dos casos; aqui quase
nunca. Oportunidade rara e grande quando existe não justifica varrer sempre, ainda mais
quando a varredura é uma ordem de grandeza mais cara.

## Limitações

- Lote parcial: `att532` com 7 pares; `I_max` reduzido (5/3/2) por custo de tempo.
- Parte dos tempos de `att532` foi inflada por contenção de CPU.
