# H6 — Construção com lookahead cumulativo

Status: **ENCERRADA — o sinal forte da construção pura (seção 3) não
sobrevive ao pipeline completo.** Com poder estatístico real (N=45, lote
noturno, seção 7), o resultado final é um empate estatístico quase
perfeito (23 vitórias/22 derrotas, p=1,000). **Não adotar.**

## 1. Hipótese

A construção gulosa atual (`construction_impl.cpp`) escolhe o próximo
cliente só pela distância até ele (`dist(r,c)`) — um critério de 1 passo de
lookahead. Como o custo do MLP é cumulativo (a latência de todo mundo
depois de `r` depende do caminho inteiro), um candidato levemente mais caro
agora pode habilitar uma sequência bem mais barata nos próximos passos. Se
pontuarmos cada candidato pelo custo cumulativo de um rollout guloso de `k`
passos (não só o primeiro salto), a construção deveria entregar pontos de
partida melhores — mesmo antes de qualquer RVND.

Fonte: inspirado nos resultados teóricos de estrutura matroidal cumulativa
de Fischetti, Laporte & Martello (1993), *"The Delivery Man Problem and
Cumulative Matroids"* — aqui usados só como motivação para um critério
guloso mais informado, não implementando a teoria de matroides em si.

## 2. Metodologia

Réplica em Python de `construction_impl.cpp` (validada: bate exatamente com
o binário C++ em alpha=0, caso determinístico). Variante com lookahead:
pontua cada candidato `c` (partindo de `r`) pelo custo cumulativo do
segmento hipotético `r → c → (k-1 saltos gulosos adicionais)`, em vez de só
`dist(r,c)`; mesma mecânica de RCL/alpha por cima. Comparação **sem RVND
nenhum** — só o custo bruto logo após a construção, pareado por seed, 30
trials × 7 instâncias (`eil51` a `lin318`). Script:
[`scripts/h6_lookahead_construction_test.py`](../../scripts/h6_lookahead_construction_test.py),
dados brutos: `scripts/h6_lookahead_results.json` (k=2) e
`scripts/h6_lookahead_results_k3.json` (k=3).

## 3. Resultado

**k=2** (1 salto real + 1 salto de sondagem): sem sinal — 105 vitórias/105
derrotas no total agregado, `p=1.000`. Ruído puro.

**k=3** (1 salto real + 2 saltos de sondagem):

| instância | n | win/tie/loss | p (sinal) | ganho médio |
|---|---|---|---|---|
| eil51 | 51 | 17/0/13 | 0,585 | +0,86% |
| st70 | 70 | 23/0/7 | **0,005** | +2,09% |
| pr76 | 76 | 18/0/12 | 0,362 | +1,04% |
| kroA100 | 100 | 18/0/12 | 0,362 | +0,59% |
| lin105 | 105 | 15/0/15 | 1,000 | +0,21% |
| pr226 | 226 | 18/0/12 | 0,362 | +1,02% |
| lin318 | 318 | 18/0/12 | 0,362 | +0,02% |
| **agregado (todas)** | | **127/0/83** | **0,0029** | **+0,83%** |

Direção **consistentemente favorável ao lookahead em todas as 7
instâncias** (nunca perde em média), significativo isoladamente em `st70`
e significativo no agregado de 210 tentativas (`p=0,003`). Bem diferente do
padrão de ruído-em-torno-de-zero que H1/H2/H4/H5 mostraram.

Custo computacional: réplica em Python, ainda rápida mesmo nas maiores
instâncias (`pr439`: 0,75s, `att532`: 1,14s para uma construção completa
com k=3) — uma implementação em C++ seria uma fração disso.

## 4. Interpretação e limitações

Isso mede só o **custo bruto da construção**, antes de qualquer RVND. Não
sabemos ainda se essa vantagem sobrevive depois que o RVND (que já é muito
eficaz, como toda a sessão mostrou) refina os dois pontos de partida — é
possível que o RVND "apague" a diferença convergindo os dois para
qualidade parecida, ou que o ponto de partida melhor leve a uma bacia de
atração diferente que o RVND não alcançaria do ponto de partida míope
(esse é o argumento original da hipótese). Só dá para saber testando o
pipeline completo.

`k=2` não mostrou nada; só `k=3` mostrou sinal — sugere que o efeito
precisa de uma sondagem mínima de profundidade para aparecer (faz sentido:
com só 1 salto de sondagem, a diferença de informação em relação ao
critério original é pequena).

## 5. Implementação em C++

Aditiva: `construction_lookahead(sol, eval, alpha, k, gen)` nova em
[`src/construction_impl.cpp`](../../src/construction_impl.cpp) — a
`construction()` original não foi tocada. Réplica exata da lógica Python
validada (mesmo `lookahead_score`: custo cumulativo do rollout guloso de
`k` passos). Flags novas `--construction-mode greedy|lookahead
--lookahead-k N` em `gils_rvnd` (default `greedy` = comportamento antigo)
e em `construction` (para testes isolados). Corretude: com `alpha=0`
(determinístico), C++ e Python dão **exatamente o mesmo custo** em
`lin318` (6.588.331) — validado bit-a-bit antes de qualquer teste com
RVND.

## 6. Teste do pipeline completo (com RVND) — resultado parcial

Pareado por seed, `gils_rvnd --imax 5 --iils 100`, `lin318`, comparando
`--construction-mode greedy` (baseline) vs. `--construction-mode
lookahead --lookahead-k 3`. Só 6 seeds rodadas até agora (teste rápido,
não é o lote noturno com poder estatístico pleno):

| seed | greedy | lookahead | resultado |
|---|---|---|---|
| 1 | 5.562.365 | 5.573.335 | lookahead pior |
| 2 | 5.560.679 | 5.578.308 | lookahead pior |
| 3 | 5.574.033 | 5.583.238 | lookahead pior |
| 4 | 5.579.384 | 5.562.365 | lookahead melhor |
| 5 | 5.578.947 | 5.578.308 | lookahead melhor (marginal) |
| 6 | 5.562.365 | 5.560.679 | lookahead melhor (marginal) |

**3 vitórias / 3 derrotas, ganho médio −0,06%** — empate estatístico,
mesmo perfil de ruído-em-torno-de-zero que H1/H2/H4 e a qualidade do
GILS-AM-RVND mostraram. Bem diferente do sinal forte da seção 3 (+0,83%,
p=0,003, sem RVND).

**Leitura honesta**: com N=6 não dá pra afirmar nada com confiança — mas a
suspeita levantada na seção 4 (o RVND pode estar apagando a vantagem do
ponto de partida) parece estar se confirmando. Precisa de N≥15-20 pareado
nas 3 instâncias grandes (`lin318`/`pr439`/`att532`) para fechar o
veredito de verdade — isso é trabalho de lote noturno (cada rodada leva
40-80s), não de teste rápido de sessão.

## 7. Lote noturno — veredito final com poder estatístico real

`python3 scripts/night_batch.py` (config: `lin318` N=20, `pr439` N=15,
`att532` N=10; `--lookahead-k 3`), analisado com
`scripts/night_batch_analysis.py`:

| instância | n | diff média | win/tie/loss | p (sinal) | overhead de tempo |
|---|---|---|---|---|---|
| lin318 | 20 | −0,056% | 10/0/10 | 1,000 | −1,6% |
| pr439 | 15 | +0,199% | 8/0/7 | 1,000 | +17,8% |
| att532 | 10 | −0,037% | 5/0/5 | 1,000 | −3,4% |
| **agregado** | **45** | **+0,033%** | **23/0/22** | **1,000** | +4,3% |

`lin318` e `att532` empatam exatamente no número de vitórias/derrotas
(10/10 e 5/5). O agregado de 45 pares é essencialmente cara-ou-coroa
(23/22, `p=1,000`) — o **sinal de +0,83% da construção pura (seção 3)
desaparece por completo** assim que o RVND entra em cena. Tempo também não
mostra padrão (overhead vai de −3,4% a +17,8% sem direção consistente —
provavelmente só o custo extra de `O(n²·k)` da construção, uma fração
pequena e variável do tempo total dominado pelo ILS).

**Veredito final**: H6 encerrada. O diagnóstico da seção 3 era real (a
construção com lookahead de fato entrega pontos de partida
sistematicamente melhores), mas essa vantagem é **inteiramente absorvida
pelo RVND** — o mesmo RVND que já mostrou, ao longo de toda esta sessão
(H1, H2, H3, H4), ser bom o suficiente para apagar a diferença entre
quase qualquer mecanismo de entrada e o baseline. Isso é consistente com
uma leitura mais ampla desta sessão: o gargalo do GILS-RVND nestas
instâncias não parece estar em nenhum dos pontos de entrada testados
(perturbação, recombinação, construção, busca local em lote) — o método
já é notavelmente robusto a variações nesses eixos.

## 8. Se quiser retomar

- Testar `k=4`/`k=5` (mais profundidade) — improvável que ajude, dado que
  o problema não é a qualidade da construção em si, mas o fato do RVND já
  absorver qualquer vantagem de ponto de partida.
- Combinar lookahead com a memória adaptativa do GRASP-AM (os dois
  critérios de construção juntos) — mesma ressalva.
- Mais produtivo: investigar *por que* o RVND é tão bom em apagar
  diferenças de ponto de partida — isso explicaria o padrão comum a H1,
  H2, H4 e H6, e poderia apontar para onde o gargalo real está (talvez a
  própria capacidade de exploração do RVND dentro de uma única bacia de
  atração, não os pontos de entrada/perturbação/recombinação testados até
  aqui).
