# H12b — 3-opt genuíno (reversão dupla independente)

Status: **ENCERRADA — nula.** Diagnóstico mostrava sinal real mas esparso;
o lote pareado (parcial, interrompido por decisão do usuário depois de
`lin318` completo + `pr439` completo + `att532` parcial, 42 pares no
total) confirma **ruído puro** (p=0,511 agregado) a um custo de tempo
enorme (+170% agregado, até +494% em `pr439`).

## 1. Motivação

Depois de H12a confirmar que fortalecer a vizinhança (não só escapar
melhor do RVND) é um eixo produtivo, o próximo candidato natural era
3-opt completo. Das reconexões de 3-opt sobre 3 cortes (blocos A-B-C-D,
A fixo por conter o depósito), a maioria já é alcançável por um único
2-opt (reversão de um span contíguo) ou por Or-opt (H12a, realocação de
segmento). A única reconexão genuinamente nova é reverter B e C
**independentemente**, mantendo a ordem: `A + rev(B) + rev(C) + D` — ver
`Solution::evaluateThreeOptDoubleReversal` (`solution.cpp`).

## 2. Diagnóstico (read-only)

`bin/diag_3opt`: a partir de ótimos locais de `extended-oropt` (a base
mais forte disponível), testar todos os O(n³) triplos `(i,j,k)` — rápido
o suficiente (~30-170ms por varredura completa, O(1) por candidato via
T/C/Cr) para ser exaustivo em `lin318`/`pr439`/`att532`.

```
lin318: 1/5 trials com alguma melhoria (pequena, -0,07%)
pr439:  3/5 trials com melhoria (uma grande: 122 movimentos simultâneos, -0,94%)
att532: 1/5 trials com melhoria (pequena, -0,05%)
```

Sinal real mas esparso (5/15 ótimos locais) — bem diferente do quase-zero
de H9/H10, mas também bem menos consistente que o "12/15" de H12a.

## 3. Implementação

`Solution::evaluateThreeOptDoubleReversal(i,j,k)` (append/appendReversed
encadeados em 4 blocos, mesmo padrão de `evaluate2Opt`),
`neighborhood_3opt_double_reversal` (aplica via 2 `reverse()` diretos no
array), `RVND_ExtendedOrOpt3Opt` (as 8 vizinhanças de H12a + esta),
`--rvnd-mode extended-oropt-3opt`. Tudo aditivo.

## 4. Calibração de tempo — já preocupante

1 seed, `lin318`, `--imax 5 --iils 100`: `extended-oropt` 84,2s vs
`extended-oropt-3opt` 343,5s (**4,1x mais lento**) — e **empate exato** em
custo (5.562.365 nos dois). O scan em si é rápido (~35ms), mas o custo se
acumula muito dentro do ILS completo (muitas reconvergências).

## 5. Lote pareado (parcial, interrompido)

`scripts/h12b_3opt_test.py` (dados brutos: `scripts/h12b_3opt_results.json`),
mesma escala de H12a (`lin318` imax=5/N=20,
`pr439` imax=3/N=15, `att532` imax=2/N=10). Interrompido após `lin318` completo, `pr439` completo e
`att532` parcial (7/10) por decisão do usuário — o sinal já estava claro
o suficiente e o custo de tempo escalando mal (alguns seeds de `att532`
levaram 15-34 minutos *cada*, alguns claramente inflados por contenção de
CPU com outro lote rodando em paralelo, mas mesmo descontando isso o
padrão já estava visível antes da contenção piorar):

```
instance      n  mean_rel%      w/t/l   sign_p   time+%
lin318       20     0,0317 9/5/6          0,607    414,2
pr439        15     0,0037 7/0/8          1,000    494,1
att532        7     0,0923 5/0/2          0,453     37,8
AGREGADO     42     0,0318 21/5/16        0,511    169,8
```

**Ruído puro.** `pr439` é quase uma moeda (7W/8L), `lin318` também
(9W/5T/6L), agregado p=0,511 — não dá pra distinguir de sorte. Custo de
tempo: +170% agregado, chegando a +494% em `pr439` — o pior custo/
benefício de qualquer hipótese testada nesta sessão.

## 6. Interpretação

O diagnóstico não estava errado (a oportunidade "crua" existe, e às vezes
é grande) — mas ela é rara e imprevisível o suficiente que, espalhada por
um ILS completo com centenas de reconvergências, o ganho ocasional que o
3-opt encontra é estatisticamente indistinguível do que o `double-bridge`
+ `extended-oropt` já encontrariam de qualquer jeito por sorte, ao custo
de escanear O(n³) candidatos (vs O(n²) de tudo mais) em toda reconvergência,
mesmo quando nenhum vai melhorar. Diferente de H12a (or-opt maior), onde a
vizinhança extra pagava seu custo computacional na maioria dos casos, aqui
o custo praticamente nunca compensa.

## 7. Recomendação

Não adotar `--rvnd-mode extended-oropt-3opt`. Encerrada. O código fica no
projeto (aditivo, não interfere em nada) mas não é recomendado para uso.
Diferente de H9/H10 (mecanismo fraco desde o diagnóstico), aqui o
diagnóstico foi genuinamente promissor — a lição é que "oportunidade rara
e grande quando existe" não é o mesmo que "vale a pena escanear sempre",
especialmente quando o custo do scan é uma ordem de grandeza maior
(O(n³) vs O(n²)).
