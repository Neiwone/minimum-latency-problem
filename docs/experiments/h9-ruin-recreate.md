# H9 — Large Neighborhood Search / ruin-and-recreate

> Os scripts e dados brutos em `scripts/` citados neste documento foram removidos do
> repositório e estão preservados na tag git `archive/h-scripts`
> (`git show archive/h-scripts:scripts/<arquivo>`).

Status: **encerrada só no diagnóstico barato (nada implementado em C++). O
mecanismo testado tem poder de escape ~zero — não é "empata com
double-bridge", é "quase sempre reconstrói exatamente o mesmo ótimo local
de onde partiu".**

## 1. Motivação

H5 mostrou que enviesar *onde* o double-bridge corta (por regret de aresta)
não ajuda, com uma explicação provável: o double-bridge controla onde
cortar mas não com o que reconectar — a reconexão é determinada pela ordem
dos segmentos, não por proximidade. A hipótese de H9 era que
ruin-and-recreate (Ropke & Pisinger 2006) resolve isso ao controlar as
duas pontas: remove k clientes e reinsere cada um na posição de menor
custo via heurística de inserção regret-2, ao invés de reconectar
segmentos por ordem fixa.

## 2. Diagnóstico

Metodologia (mesmo padrão de H5): a partir de um ótimo local já convergido
por RVND, perturbar com `double_bridge` (baseline) ou `ruin_recreate`
(`k=8` clientes removidos, reinserção regret-2 gulosa por custo total de
rota), reconvergir ambos via `./bin/local_search` (RVND), e comparar o
custo final contra o custo antes da perturbação. 3 instâncias × 5 ótimos
locais × 2 modos × 20 trials = 600 trials (`scripts/h9_ruin_recreate_test.py`,
resultados em `scripts/h9_ruin_recreate_results.json`).

Corretude verificada antes do lote completo: em `eil51` (instância pequena,
quase ótima), a reinserção regret-2 reconstrói exatamente a rota original —
a princípio interpretado como comportamento esperado nessa escala pequena,
não bug.

## 3. Resultado

```
instance   mode                n    hit%  mean_delta  mean_rel%
att532     double_bridge     100    68.0    39912.68     0.6577
att532     ruin_recreate     100     0.0      -51.56    -0.0008
lin318     double_bridge     100    67.0    59953.17     0.9551
lin318     ruin_recreate     100     0.0        0.00     0.0000
pr439      double_bridge     100    58.0    95478.83     0.4680
pr439      ruin_recreate     100     0.0        0.00     0.0000
```

`double_bridge` escapa e melhora em 58-68% dos trials, com ganho médio
relativo de 0,47-0,96% — comportamento esperado de uma perturbação real.

`ruin_recreate` tem **hit% = 0,0 nas 3 instâncias** e `mean_delta` ≈ 0
(exatamente 0,0000 em `lin318`/`pr439`). Inspecionando o JSON bruto: **299
dos 300 trials de `ruin_recreate` retornam um custo idêntico bit-a-bit ao
custo antes da perturbação** (o único caso diferente, em `att532`, é
*pior* por uma margem pequena — ruído, não melhora). Ou seja: não é que
`ruin_recreate` explora e converge para algo parecido — ele **quase nunca
sai do ótimo local de onde partiu**.

## 4. Interpretação

Não é o mesmo padrão nulo de H1/H2/H4/H6 (onde o mecanismo funciona mas o
RVND absorve a vantagem). Aqui o mecanismo em si **não perturba de
verdade**: a reinserção regret-2 gulosa, ao escolher a posição de menor
custo de rota completa para cada cliente removido, tende a colocar cada
cliente de volta exatamente na posição de onde saiu — porque, partindo de
um ótimo local já refinado por RVND (que inclui a vizinhança de
reinserção/or-opt), essa já *é* a posição de custo mínimo para aquele
cliente sozinho. Repetir "remove k clientes, reinsira cada um gulosamente
na melhor posição" sobre uma rota já localmente ótima para reinserção
simplesmente desfaz a remoção.

Isso explica por que o teste em `eil51` "reconstruiu a rota original" —
não era uma peculiaridade de instância pequena, era o comportamento real
do mecanismo, e o lote grande confirma que persiste em `n≳300`.

Double-bridge funciona como perturbação justamente porque força uma
reconexão topológica que a busca local (e um repair guloso single-move)
não desfaz trivialmente — regret-2 puro, sem nenhuma fonte de
aleatoriedade na reinserção, não tem essa propriedade.

## 5. Recomendação

Não vale implementar `ruin_recreate` em C++ como está — ele não é uma
perturbação, é um no-op na maior parte das vezes. Ver seção 6 (H9b) para o
teste da correção óbvia.

## 6. H9b — reinserção com aleatoriedade real (`scripts/h9b_randomized_repair_test.py`)

Correção testada: em vez de sempre escolher a posição de custo mínimo pra
cada cliente removido, sortear uniformemente entre as `TOP_M=3` posições
mais baratas (técnica clássica de ALNS — "randomized/noised best
insertion"). Testado em instâncias **pequenas** (`eil51`/`kroA100`/`rat195`,
n=51/100/195) a pedido do usuário, mesmo método de antes (5 ótimos locais
× 20 trials × 2 modos). Dados brutos: `scripts/h9b_randomized_repair_results.json`.

```
instance   mode                  n    hit%  mean_delta  mean_rel%  identical%
eil51      double_bridge       100    48.0      131.98     1.2469        27.0
eil51      ruin_recreate_v2    100    46.0      111.93     1.0795        38.0
kroA100    double_bridge       100    56.0     8906.44     0.8614        13.0
kroA100    ruin_recreate_v2    100    23.0     1725.71     0.1707        68.0
rat195     double_bridge       100    65.0     1206.47     0.5259         4.0
rat195     ruin_recreate_v2    100    36.0      662.08     0.2876        54.0
```

A correção funciona no sentido de destravar o mecanismo: `identical%` caiu
de ~99,7% (H9 original) para 27-68% — a randomização de fato reduz (mas
não elimina) o colapso pra rota de origem. Mas mesmo destravado,
`ruin_recreate_v2` **perde consistentemente pra `double_bridge` nas 3
instâncias** em hit% (23-46% vs 48-65%) e em ganho médio (0,17-1,08% vs
0,53-1,25%) — sinal consistente, não misto entre instâncias como em H5.
Em `kroA100` a diferença é grande (68% dos trials ainda idênticos, hit%
menos da metade do double-bridge).

Interpretação: mesmo com aleatoriedade, a reinserção regret-2 continua
gulosa (top-3 ainda tende a incluir a posição de origem ou vizinhas
equivalentes) — o mecanismo de repair em si puxa de volta pro mesmo
vale com mais força que o corte "cego" do double-bridge. Aumentar `k`,
`TOP_M`, ou trocar a métrica de seleção de cliente/posição poderiam mudar
esse quadro, mas não foram testados.

## 7. H9c — remoção correlacionada geograficamente (Shaw removal)

Hipótese: a remoção uniforme aleatória do H9b tende a espalhar os k
clientes removidos por lugares distantes da rota, então cada "buraco" é
isolado e fácil de tapar quase na mesma posição (mesmo com aleatoriedade
no repair). Trocamos por **Shaw removal** (Shaw 1998, clássico de
ALNS): sorteia um cliente semente e remove ele + os k-1 clientes mais
próximos dele no espaço — os removidos ficam mutuamente substituíveis,
criando ambiguidade genuína pro repair escolher entre eles. Mesmo repair
de H9b (regret-2, sorteio entre top-3), mesmas 3 instâncias pequenas
(`scripts/h9c_shaw_removal_test.py`). Dados brutos:
`scripts/h9c_shaw_removal_results.json`.

```
instance   mode              n    hit%  mean_delta  mean_rel%  identical%
eil51      double_bridge   100    37.0       10.54     0.0945        26.0
eil51      shaw_removal    100    36.0        5.08     0.0397        30.0
kroA100    double_bridge   100    41.0     1200.37     0.1080        33.0
kroA100    shaw_removal    100    25.0     1373.38     0.1319        63.0
rat195     double_bridge   100    49.0      174.53     0.0717         5.0
rat195     shaw_removal    100    27.0      112.01     0.0486        39.0
```

Mesmo padrão de novo: `shaw_removal` perde pro `double_bridge` em hit% nas
3 instâncias (empatado em `eil51`, claramente pior em `kroA100` e
`rat195`), e `identical%` continua alto (30-63%). Correlacionar a remoção
geograficamente não resolveu o problema de fundo — o repair guloso (com
ou sem aleatoriedade no topo) continua puxando de volta pro mesmo vale
com mais força do que o corte cego do double-bridge escapa dele.

## 8. Recomendação final

Três variantes testadas (H9 gulosa pura, H9b com randomização top-3, H9c
com remoção correlacionada + randomização) — **todas perdem
consistentemente pro double-bridge**, em instâncias pequenas e grandes.
O padrão não é mais "só faltou consertar o colapso" — é que, para este
problema/conjunto de instâncias, o double-bridge (uma perturbação
"burra" que ignora custo) supera de forma robusta uma família de
perturbações "inteligentes" baseadas em regret-insertion. Encerrado; não
implementar em C++. Se algo nessa linha for retomado no futuro, precisaria
de um mecanismo de repair qualitativamente diferente (não apenas mais
aleatoriedade em cima de regret-2) — por exemplo repair via 2-opt/or-opt
completo em vez de só inserção, o que efetivamente reinventaria parte do
RVND já existente.
