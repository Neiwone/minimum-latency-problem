# H3 — Vizinhança específica de MLP no prefixo

## Hipótese

Se o custo de latência é dominado pelas primeiras posições da rota
(propriedade estrutural do MLP, não do TSP — um arco no início do circuito
afeta a latência de todos os vértices seguintes), então as vizinhanças
herdadas do TSP (swap, 2-opt, reinsertion, or-opt2, or-opt3), aplicadas por
RVND, deveriam deixar escapar melhorias no prefixo da rota com mais
frequência do que no meio ou no fim. Sintoma esperado: gap residual
concentrado no início da rota, crescendo com `n`.

## Operacionalização testada

Não temos otimalidade provada para a maioria das instâncias, então não dá
para medir "gap vs. ótimo" diretamente. Em vez disso, testamos a forma mais
direta e barata de expor um "ponto cego" de vizinhança: dado um ótimo local
de RVND, existe uma **permutação conjunta de uma janela de `k` clientes
consecutivos** que ainda melhora o custo? Uma janela reordenada é um
movimento fora do alcance de swap/2-opt/reinsertion isolados (que mexem em
1–3 elementos de cada vez) quando a melhoria só aparece com os `k` elementos
reordenados simultaneamente.

Para cada instância e trial:

1. `./bin/construction --alpha 0.15` (randômico) + `./bin/local_search
   --route <rota>` → ótimo local de RVND (as 5 vizinhanças do artigo).
2. Busca exaustiva por permutação (`k!` permutações) em 3 janelas de
   controle:
   - **prefix**: posições `[1, 1+k)` (logo após o depósito) — onde H3 prevê o
     maior potencial de melhoria;
   - **middle**: janela no centro da rota — controle;
   - **suffix**: últimas `k` posições — controle (deveria ser a região com
     *menos* potencial, já que afeta poucas latências futuras).
3. Registra se a permutação encontrou melhoria (`delta = custo_base -
   custo_melhor`), e a magnitude relativa.

Script: [`scripts/h3_prefix_test.py`](../../scripts/h3_prefix_test.py).
Resultados brutos (k=4,6): `scripts/h3_prefix_results.json`.

Instâncias: `eil51` (51), `st70` (70), `pr76` (76), `kroA100` (100),
`lin105` (105), `pr226` (226), `lin318` (318), `pr439` (439), `att532` (532)
— mesma faixa de tamanho usada no artigo. 10 trials por instância, k ∈
{4, 6}; extensão com k=8 rodada à parte em `eil51`/`pr226`/`att532` (5 trials).

## Resultado

| n range | k | prefix hit% | middle hit% | suffix hit% |
|---|---|---|---|---|
| 51–532 | 4 | 0% (0/90) | 0% (0/90) | 0% (0/90) |
| 51–532 | 6 | ~1% (1/90, pr76, Δ=0.02%) | 0% (0/90) | 0% (0/90) |
| 51/226/532 | 8 | 0% (0/15) | 0% (0/15) | 0% (0/15) |

Nenhuma tendência de crescimento com `n`. Nenhuma diferença sistemática entre
prefixo, meio e fim — a única melhoria encontrada em ~200 janelas testadas
foi uma única ocorrência isolada (0,02% de ganho relativo), estatisticamente
indistinguível de ruído.

## Interpretação

**H3, na forma testada, não é sustentada.** Os ótimos locais de RVND já são
efetivamente "ótimos de janela" (k até 8) tanto no prefixo quanto no meio e
no fim da rota — não há evidência de que swap/2-opt/reinsertion/or-opt deixem
buracos exploráveis especificamente no início da rota.

Faz sentido mecanicamente: a busca *best improvement* do RVND escolhe a cada
passo o movimento de maior ganho absoluto entre todas as vizinhanças: como um
arco de dado tamanho no início da rota tem impacto amplificado em muito mais
latências futuras do que o mesmo arco perto do fim (propriedade estrutural do
MLP mencionada no próprio artigo), esse mecanismo de seleção já é enviesado a
corrigir defeitos no prefixo *primeiro e com prioridade* — o oposto do
"ponto cego" que a hipótese previa. O prefixo tende a ser a região *mais*
escrutinada pela busca, não a menos.

## Limitações do teste (o que isso NÃO descarta)

- Só testamos reordenar os `k` clientes que **já estão** na janela — não
  testamos se clientes de fora deveriam entrar no prefixo (isso já é coberto,
  ainda que não exaustivamente, por reinsertion/or-opt durante o RVND).
- Usamos um único RVND por trial, não o GILS-RVND completo (múltiplos
  restarts + double-bridge). Se o objetivo fosse avaliar o algoritmo completo
  em vez do conjunto de vizinhanças, o teste seria outro.
- Não medimos diretamente "gap vs. ótimo conhecido" por posição — para isso
  seria necessário comparar, posição a posição, o ótimo local contra uma
  solução de referência mais forte (ótimo exato ou melhor solução conhecida),
  o que é um teste diferente e mais direto do "sintoma" (gap cresce com n /
  erro concentrado no início) caso se queira reabrir a hipótese por esse
  ângulo.

## Recomendação

Descartar H3 nesta forma como candidata a contribuição. Se ainda houver
interesse em uma vizinhança MLP-específica, o próximo teste que isolaria o
"sintoma" de forma mais direta seria comparar, instância a instância onde o
ótimo é conhecido (ex.: conjunto de Abeledo et al. até 107 clientes),
a posição das divergências entre a solução do GILS-RVND e o ótimo — não a
permutabilidade local de uma janela.
