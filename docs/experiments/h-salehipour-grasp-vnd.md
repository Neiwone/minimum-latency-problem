# GRASP+VND / GRASP+VNS (Salehipour et al. 2011)

Status: **implementado e verificado (`src/grasp_vnd.cpp`), calibração
inicial coerente com o paper. Sem lote estatístico completo ainda.**

## 1. Motivação

Além de usar o protocolo de instâncias de
[Salehipour, Sörensen, Goos & Bräysy — "Efficient GRASP+VND and
GRASP+VNS metaheuristics for the traveling repairman problem"](https://doi.org/10.1007/s10288-011-0153-0)
(4OR 9:189–209, 2011) — já feito em `instances/salehipour/` —
implementamos o próprio algoritmo do paper, pra comparação direta:
é o primeiro trabalho metaheurístico publicado pro TRP/MLP, precursor
direto do GILS-RVND (Silva et al. 2012) que este projeto inteiro usa
como baseline.

## 2. Correção da geração de instâncias (achado ao ler o paper original)

A versão inicial de `scripts/generate_salehipour_benchmark.py` usava
grid `[0,1000]` uniforme pra todos os 7 tamanhos — **errado**. A Seção 4
do paper (Tabela 1) especifica: grid `[0,100]` para
`n∈{10,20,50,100,200}` e `[0,500]` para `n∈{500,1000}`. Corrigido e as
140 instâncias foram regeneradas.

Também conferido: as distâncias do paper são "arredondadas para baixo ao
inteiro mais próximo". A truncação `(int)(d)` em
`src/evaluator.cpp` (tipo `EUC_2D`) já é floor pra distâncias positivas
— **nenhuma mudança necessária no motor C++**, só no gerador de
instâncias.

## 3. Diferenças estruturais em relação ao GILS-RVND já implementado

| | GILS-RVND (Silva et al. 2012, este projeto) | GRASP+VND/VNS (Salehipour et al. 2011) |
|---|---|---|
| RCL | `α%` do intervalo guloso (fração) | `α` candidatos mais próximos (contagem fixa, `α=2` ótimo no paper) |
| Vizinhanças | swap, 2-opt, reinsertion, or-opt2, or-opt3 | swap, **swap-adjacent**, 2-opt, or-opt (comprimentos 1-3, uma vizinhança só), **remove-insert** |
| Perturbação | double-bridge (ILS) | shake: remove 20% dos clientes ao acaso, reinsere em posições aleatórias (VNS) |
| Reinício | `I_max` construções × `I_ILS` perturbações cada | `restarts` construções, sem laço de ILS interno — cada reinício só roda 1 VND/VNS até convergir |

A vizinhança **remove-insert** é única deste paper: para cada vértice
`x_i` do tour, move o vértice geometricamente **mais distante** de
`x_i` para o **final** da rota (não busca a melhor posição — é um
candidato fixo por `i`). Faz sentido para o MLP: a última posição tem
peso 1 na função objetivo (menor multiplicador), então empurrar outliers
geometricamente distantes pro final reduz o quanto eles penalizam o
resto da rota. Implementado com um pré-cálculo `farthest[v]` (propriedade
estática da matriz de distância, O(n²) uma vez só).

## 4. Implementação

Novo binário [`src/grasp_vnd.cpp`](../../src/grasp_vnd.cpp), reaproveitando
`Solution`/`Evaluator` (mesma função objetivo, mesmas tabelas T/C/Cr —
`f(x) = Σ(n-i+1)·w(x_{i-1},x_i)` é idêntica à latência acumulada do
GILS-RVND). Funções `delta_swap`/`delta_2opt`/`delta_reinsertion`/
`delta_oropt` espelham a lógica exata de
`Solution::evaluate{Swap,2Opt,Reinsertion,OrOpt}` mas retornam o delta
assinado em vez de booleano (VND/VNS precisam do **melhor** movimento de
toda a vizinhança — "arg min Nk" — não só do primeiro que melhora).

Implementa a "configuração 1 (NoFix-Full)" do paper — vizinhanças
completas, sem os esquemas de redução (Seção 2.3.2, otimizações de
velocidade pra hardware de 2011, documentadas como não implementadas por
não serem necessárias pra uma comparação de qualidade em hardware
atual). CLI: `--alpha 2 --restarts 10 --local-search vnd|vns
--shake-pct 0.20 --seed N`.

## 5. Bugs encontrados e corrigidos durante a implementação

1. **Placeholder esquecido no rascunho**: uma chamada
   `apply_reinsertion(tour, 0, 0)` sobrou dentro da função de *busca* do
   melhor movimento (deveria só calcular, a aplicação acontece depois,
   em outro lugar) — teria movido o depósito (vértice 0, sempre fixo na
   posição 0) pra posição 1 sempre que `swap-adjacent` encontrasse
   melhoria. Pego antes de qualquer teste rodar, por revisão do código.
2. **`compute_farthest` podia escolher o depósito como alvo**: a função
   que pré-calcula "o vértice mais distante de v" não excluía o vértice
   0 (depósito) da busca — se o depósito fosse geometricamente o mais
   distante de algum `v`, o `remove-insert` tentaria realocar o
   depósito pra o final da rota, quebrando a invariante de que ele fica
   sempre na posição 0. Corrigido excluindo o vértice 0 da busca.
3. **Interpretação errada de "local search" no Algoritmo 3/4**: a
   primeira versão tratava `x' <- arg min Nk(x)` como **um único
   movimento** (o melhor de toda a vizinhança, aplicado uma vez). Isso
   deixa o VND correto por acidente (o laço externo já revisita a mesma
   vizinhança repetidamente), mas **quebra o VNS completamente**: depois
   de perturbar 20% da rota, um único movimento nunca é forte o
   suficiente pra recuperar e superar o custo pré-perturbação — o VNS
   terminava quase instantaneamente (1-2ms) sem nunca aceitar nada,
   ficando pior que o VND. Corrigido: "local search" agora é uma
   **convergência completa** dentro da vizinhança (repete o melhor
   movimento até não haver mais melhoria), pra ambos VND e VNS —
   consistente com a convenção usual de VNS na literatura e com o
   próprio `RVND()` já existente neste projeto (que também converge
   cada vizinhança antes de trocar).

## 6. Corretude

- Determinístico com `--seed`; rota sempre permutação válida, depósito
  sempre na posição 0 (checado em `eil51`, 51 nós, sem duplicados).

## 7. Calibração inicial (coerente com o paper)

| instância | VND | VNS |
|---|---|---|
| `eil51` (10 restarts) | 9.574 / 8ms | **9.395** / 54ms |
| `lin318` (10 restarts) | **5.751.022** / 2,1s | 5.837.279 / 19,1s |

Em `eil51`, VNS vence (perturbação ajuda) — em `lin318`, VND vence. Isso
bate com a própria conclusão do paper: *"The perturbations in the
GRASP+VNS algorithm seem to help marginally... this may indicate that
the GRASP multi-start is not able to provide enough diversification"* —
ou seja, o ganho do VNS sobre o VND é pequeno e inconsistente entre
instâncias, exatamente o que vemos aqui. Ambos ficam atrás do
`gils_rvnd` baseline nessa escala (~5,56M em `lin318`) — esperado, já
que o GILS-RVND (2012) é posterior e tem refino de ILS completo
(`I_ILS` perturbações double-bridge por reinício) que este método (só
`restarts` reinícios simples, sem ILS interno) não tem.

## 8. Or-opt estendido (`--or-opt-max-len`) — mesmo eixo do H12a, também funciona aqui

O achado central desta sessão (H12a,
`docs/experiments/h12-extended-oropt.md`) é que estender o or-opt a
segmentos maiores (4-6, além dos 1-3 clássicos) é uma vizinhança
genuinamente mais forte, que rende ganho real de qualidade no
GILS-RVND. Testamos a mesma extensão aqui: `--or-opt-max-len N`
(default 3, igual ao paper original) controla até que comprimento de
segmento o `OR_OPT` escaneia — aditivo, `local_search_in_neighborhood`/
`run_vnd`/`run_vns` recebem o parâmetro e repassam pro loop
`for (segLen = 1; segLen <= orOptMaxLen; segLen++)`.

Corretude: `--or-opt-max-len 6` nunca piora `eil51` (empate, 9.574 nos
dois — superconjunto estrito de movimentos). Calibração de 1 seed em
`lin318` (VND, 10 restarts): **melhora de verdade**, 5.751.022 → 5.670.191
(**-1,4%**), ao custo de ~1,8x mais tempo (1,7s → 3,1s) — mesmo padrão
qualitativo do H12a (vizinhança mais forte paga seu custo computacional
com ganho real de qualidade, não é grátis mas compensa). Ainda é 1 seed,
não é teste estatístico — mas é um sinal forte de que o eixo "fortalecer
or-opt" generaliza além do GILS-RVND especificamente, valendo a pena
incluir no lote pareado completo do capítulo de resultados.

## 8.1 Confirmação com poder estatístico completo — o achado mais forte do TCC

Lote completo (`run_experiments.py --mode salehipour-benchmark --solvers
grasp_vnd grasp_vnd_extended_oropt`), as 140 instâncias do benchmark
oficial (não instâncias nossas — Seção 2), pareado por instância:

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

**Confirmação cruzada forte do achado central desta sessão (H12a).** O
mesmo efeito ("or-opt com segmentos maiores melhora a qualidade, mais
forte conforme `n` cresce") aparece de novo, agora: (a) num algoritmo
**diferente** (GRASP+VND de Salehipour et al., não GILS-RVND), e (b) no
**benchmark oficial da literatura** (140 instâncias reproduzindo o
protocolo do próprio paper, não instâncias geradas por nós ad-hoc). Isso
não é mais coincidência de um único algoritmo/conjunto de instâncias —
`n=500` isolado já é p<0,001 (18W/0T/2L), e o agregado das 140 instâncias
é p<0,001. Custo de tempo cresce forte com `n` (+165% em n=1000), mas o
ganho de qualidade compensa.

Pro TCC: esta é provavelmente a evidência mais forte disponível pra
sustentar a tese de que estender o or-opt é uma melhoria genuína e
generalizável da vizinhança de busca local para o MLP/TRP, não um
artefato de uma implementação específica.

## 8.2 Robustez de lotes longos: checkpoint/resume no `run_experiments.py`

Rodando `gils_rvnd_imax1` vs `gils_am_rvnd_extended_oropt_imax1` em
n=500/1000 (várias horas de execução esperada), a sessão foi
interrompida (reinício de ambiente) e o processo em background foi
morto **sem nenhum resultado parcial salvo** — o modo
`salehipour-benchmark` só imprimia o resumo no final, então horas de
trabalho foram perdidas.

Corrigido: `run_salehipour_benchmark_mode` (modo `--solvers`, o caso que
importa pra corridas longas) agora salva cada par instância+resultado
incrementalmente em `--checkpoint <arquivo.json>` (default
`results/salehipour_<a>_vs_<b>.json`) e **retoma automaticamente** do
checkpoint se ele já existir, pulando pares já computados. Testado:
rodar 2x com o mesmo checkpoint na segunda vez não recomputa nada e
reproduz o mesmo resultado. O lote de n=500/1000 foi relançado com
`nohup ... & disown` (sobrevive a reinício de sessão do agente, não só
a interrupções do processo) e com `-u` (saída não-bufferizada).

## 9. Próximos passos (não feitos ainda)

- Lote pareado com poder estatístico (N≥15-20) comparando
  `grasp_vnd`/`vns` contra `gils_rvnd` nas instâncias TSPLIB e no
  benchmark Salehipour completo — pro capítulo de resultados do TCC.
- Tabelas 3-9 do paper original (comparação com CPLEX em `n=10,20` e com
  bounds UB/LB) dão números de referência diretos pra validar a
  reimplementação — ainda não comparado ponto a ponto.
- Esquemas de redução de vizinhança (Fix/NoFix, Full/Half) não
  implementados — só a configuração 1 (mais completa, mais lenta).
