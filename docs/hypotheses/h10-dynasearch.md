# H10 — Dynasearch (DP sobre T/C/Cr para combinar 2-opts simultâneos)

**Veredito: refutada (encerrada no diagnóstico).** A premissa mecânica é real: 0,90–1,22%
dos pares de 2-opts disjuntos são não-aditivos, ao contrário do TSP clássico. Mas em ~258
mil pares testados (24 ótimos locais de `lin318`/`pr439`/`att532`) só 3 combinações melhoram, com
ganho de ~0,11–0,12%. A DP completa não foi construída.

## Hipótese

Dynasearch (Potts & van de Velde, 1995; Congram, Potts & van de Velde, 2002) busca, por
DP, a combinação ótima de movimentos disjuntos simultâneos em vez de aplicar um de cada
vez. Não foi encontrada na literatura de MLP combinada com as tabelas T/C/Cr. No MLP o
custo é a soma de latências acumuladas, então um 2-opt isolado pode não melhorar pelo
deslocamento de tempo que causa no resto da rota, mas dois 2-opts bem posicionados
poderiam se compensar. No TSP clássico isso não acontece: o custo é aditivo entre
movimentos disjuntos.

## O que foi testado

A formulação ingênua (um valor ótimo por posição) não vale para o MLP: o custo depende
do tempo `t` acumulado, que depende das reversões escolhidas antes, então o estado da DP
teria de ser uma fronteira de Pareto em (t, custo) por posição. Antes de construir isso,
a premissa foi testada com um diagnóstico em
[`src/diag_dynasearch.cpp`](../../src/diag_dynasearch.cpp) (fora do `Makefile`),
`--pool 150 --trials 8`:

1. A partir de um ótimo local do RVND, calcula o delta exato dos O(n²) 2-opts em O(1)
   via T/C/Cr.
2. Seleciona os 150 mais perto de empatar ("near-miss").
3. Para cada par disjunto, aplica as duas reversões numa cópia e recalcula o custo exato
   em O(n).
4. Compara o custo combinado com o custo base e com `delta_A + delta_B`; a diferença
   mede a não-aditividade.

Como cada par é aplicado e recalculado, não há o erro de borda de footprint do
[H4](h4-multi-improvement.md).

## Resultados

8 ótimos locais por instância, `C(150,2)≈11.175` pares por ótimo local:

| instância | pares testados | melhorando | % melhorando | não-aditivos | % não-aditivo | melhor delta combinado |
|---|---:|---:|---:|---:|---:|---:|
| lin318 | 85.791 | 2 | 0,0023% | 1.047 | 1,22% | -7.082 (-0,114%) |
| pr439 | 86.001 | 1 | 0,0012% | 827 | 0,96% | -22.663 (-0,118%) |
| att532 | 86.738 | 0 | 0,0000% | 780 | 0,90% | 0 |

A interação média fica na ordem de poucas unidades, com custos totais na casa dos
milhões. As 3 melhorias caem cada uma em 1 dos 8 ótimos locais da instância.

## Por que não funcionou

O RVND é ótimo local só em relação a movimentos individuais, e a não-aditividade do MLP
de fato abre uma fresta que o TSP não tem. Mas a interação entre movimentos é pequena
demais para virar melhoria: quase nunca é grande ou favorável o bastante. É o mesmo
padrão do [H5](h5-regret-perturbation.md) (sintoma real, pequeno demais para dar ganho),
com causa mais fundamental. Com acerto de ~0,001–0,002% e ganho de ~0,1% quando ocorre,
não compensa resolver a fronteira de Pareto da DP.

## Limitações

- Só pares, dentro de um pool de 150 near-misses; a DP completa buscaria todas as
  combinações, inclusive 3+ reversões, e poderia achar mais.
- Só n entre 318 e 532; `n≳1000` não foi testado.

## Referências

- Potts & van de Velde (1995) — dynasearch.
- Congram, Potts & van de Velde (2002) — dynasearch.
