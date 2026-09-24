# GRASP+VND / GRASP+VNS (Salehipour et al. 2011)

**Resumo: não concluído.** O algoritmo de Salehipour et al. (2011) está implementado e
verificado em [`src/grasp_vnd.cpp`](../../src/grasp_vnd.cpp), com calibração inicial
coerente com o paper, mas ainda sem lote pareado contra o `gils_rvnd`. O que já tem
poder estatístico é a extensão do or-opt (`--or-opt-max-len 6`): nas 140 instâncias do
benchmark de Salehipour, melhora o GRASP+VND em **0,3351% agregado, 71/45/24,
p < 0,001**, com `n=500` isolado em 18/0/2 (p < 0,001), ao custo de até +165% de tempo
em `n=1000`. Isso reproduz o efeito do [H12](h12-extended-oropt.md) num algoritmo e
num benchmark diferentes.

## Motivação

É o primeiro trabalho metaheurístico publicado para o TRP/MLP e precursor direto do
GILS-RVND (Silva et al. 2012), o baseline do projeto. Além do protocolo de instâncias
(`instances/salehipour/`), reimplementar o próprio algoritmo permite comparação direta.

Ao ler o paper, a geração das instâncias foi corrigida: a versão inicial de
`scripts/generate_salehipour_benchmark.py` usava grid `[0,1000]` para todos os
tamanhos, mas a Tabela 1 do paper especifica `[0,100]` para `n∈{10,20,50,100,200}` e
`[0,500]` para `n∈{500,1000}`. As 140 instâncias foram regeneradas. As distâncias do
paper são arredondadas para baixo, o que a truncação `EUC_2D` de
`src/evaluator.cpp` já faz.

## O que foi testado

Diferenças estruturais em relação ao GILS-RVND:

| | GILS-RVND (Silva et al. 2012, este projeto) | GRASP+VND/VNS (Salehipour et al. 2011) |
|---|---|---|
| RCL | `α%` do intervalo guloso (fração) | `α` candidatos mais próximos (contagem fixa, `α=2` ótimo no paper) |
| Vizinhanças | swap, 2-opt, reinsertion, or-opt2, or-opt3 | swap, **swap-adjacent**, 2-opt, or-opt (comprimentos 1-3, uma vizinhança só), **remove-insert** |
| Perturbação | double-bridge (ILS) | shake: remove 20% dos clientes ao acaso, reinsere em posições aleatórias (VNS) |
| Reinício | `I_max` construções × `I_ILS` perturbações cada | `restarts` construções, sem laço de ILS interno — cada reinício só roda 1 VND/VNS até convergir |

A vizinhança **remove-insert** é própria deste paper: para cada vértice `x_i`, move o
vértice geometricamente mais distante de `x_i` para o final da rota (um candidato fixo
por `i`, sem buscar a melhor posição). Faz sentido no MLP porque a última posição tem
o menor multiplicador na função objetivo, então empurrar outliers para o final reduz o
quanto eles penalizam o resto da rota.

O binário reaproveita `Solution`/`Evaluator` (a função objetivo
`f(x) = Σ(n-i+1)·w(x_{i-1},x_i)` é a mesma latência acumulada do GILS-RVND), mas o
VND/VNS usa o **melhor** movimento de cada vizinhança, não o primeiro que melhora.
Implementa a configuração 1 (NoFix-Full) do paper: vizinhanças completas, sem os
esquemas de redução da Seção 2.3.2, que eram otimizações de velocidade para o hardware
de 2011. CLI: `--alpha 2 --restarts 10 --local-search vnd|vns --shake-pct 0.20
--seed N`, e `--or-opt-max-len N` (padrão 3, como no paper) para estender o or-opt.

Três bugs foram corrigidos na implementação: uma chamada de aplicação de movimento
esquecida dentro da função de busca (teria movido o depósito); o pré-cálculo do
vértice mais distante podia escolher o depósito como alvo do remove-insert; e a
"busca local" do Algoritmo 3/4 era interpretada como um único movimento, o que
deixava o VND correto por acidente mas quebrava o VNS (depois de perturbar 20% da
rota, um movimento nunca recupera o custo; o VNS terminava em 1–2 ms sem aceitar
nada). Agora a busca local converge dentro da vizinhança, como na convenção usual de
VNS e no `RVND()` do projeto. O resultado é determinístico com `--seed`, e a rota é
sempre uma permutação válida com o depósito na posição 0 (checado em `eil51`).

## Resultados

**Calibração inicial** (1 seed, 10 restarts):

| instância | VND | VNS |
|---|---|---|
| `eil51` (10 restarts) | 9.574 / 8ms | **9.395** / 54ms |
| `lin318` (10 restarts) | **5.751.022** / 2,1s | 5.837.279 / 19,1s |

Em `eil51` o VNS vence; em `lin318`, o VND. Isso bate com a conclusão do próprio
paper: *"The perturbations in the GRASP+VNS algorithm seem to help marginally... this
may indicate that the GRASP multi-start is not able to provide enough
diversification"*. Os dois ficam atrás do `gils_rvnd` nessa escala (~5,56M em
`lin318`), o esperado para um método sem laço de ILS interno.

**Or-opt estendido.** Com `--or-opt-max-len 6`, `eil51` empata (9.574 nos dois; é um
superconjunto estrito de movimentos), e 1 seed em `lin318` (VND, 10 restarts) já
melhora de 5.751.022 para 5.670.191 (−1,4%), com ~1,8× mais tempo (1,7s → 3,1s). O
lote completo, `grasp_vnd` vs `grasp_vnd_extended_oropt` nas 140 instâncias do
benchmark, pareado por instância:

```
     n  instances  mean_rel%      w/t/l   sign_p  time_b_vs_a%
    10         20     0.0000     0/20/0    1.000          +6.5
    20         20     0.0000     0/20/0    1.000         +28.8
    50         20     0.2844     11/5/4    0.118         +48.0
   100         20     0.2876     14/0/6    0.115         +62.5
   200         20     0.3997     13/0/7    0.263         +69.1
   500         20     1.0123     18/0/2    0.000         +80.2
  1000         20     0.3617     15/0/5    0.041        +165.0
------------------------------------------------------------------------------------------
   ALL        140     0.3351   71/45/24    0.000
```

## Por que funcionou

O mesmo efeito do H12 ("or-opt com segmentos maiores melhora a qualidade, mais forte
conforme `n` cresce") aparece num algoritmo **diferente** (GRASP+VND, não GILS-RVND) e
no **benchmark oficial da literatura** (140 instâncias no protocolo do próprio paper,
não instâncias geradas ad hoc). Isso sustenta que estender o or-opt é uma melhoria
genuína da vizinhança de busca local para o MLP/TRP, não um artefato de uma
implementação. O custo de tempo cresce forte com `n` (+165% em `n=1000`), mas o ganho
de qualidade compensa.

## Limitações

- Falta o lote pareado com poder estatístico (N≥15-20) de `grasp_vnd`/`vns` contra
  `gils_rvnd`, nas instâncias TSPLIB e no benchmark de Salehipour.
- A reimplementação ainda não foi comparada ponto a ponto com as Tabelas 3-9 do paper
  (CPLEX em `n=10,20` e bounds UB/LB).
- Só a configuração 1 (mais completa, mais lenta); os esquemas de redução (Fix/NoFix,
  Full/Half) não foram implementados.

## Referências

- Salehipour, A., Sörensen, K., Goos, P., Bräysy, O. (2011). Efficient GRASP+VND and
  GRASP+VNS metaheuristics for the traveling repairman problem. *4OR*, 9(2), 189–209.
  https://doi.org/10.1007/s10288-011-0153-0
- Silva, M.M., Subramanian, A., Vidal, T., Ochi, L.S. (2012). A simple and effective
  metaheuristic for the Minimum Latency Problem. *European Journal of Operational
  Research*, 221(3), 513–520.
