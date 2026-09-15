# A proposta vs. o GILS-RVND: o que exatamente mudou

Comparação componente a componente entre o **GILS-RVND** de Silva, Subramanian, Vidal
& Ochi (*EJOR* 221, 2012) — implementado em [`src/gils_rvnd.cpp`](../src/gils_rvnd.cpp)
— e a configuração vencedora deste projeto:

```bash
./bin/gils_am_rvnd <instancia.tsp> --rvnd-mode candidate-dlb --cand-k 12 --iils 300 \
    --max-time 100
```

(registrada como `gils_am_rvnd_dlb` em [`run_experiments.py`](../run_experiments.py);
código em [`src/gils_am_rvnd.cpp`](../src/gils_am_rvnd.cpp) e
[`src/neighborhoods_cand.cpp`](../src/neighborhoods_cand.cpp)).

O esqueleto é o mesmo — GRASP + ILS + RVND, com double bridge como perturbação. O que
muda é **a busca local e a calibração do ILS**. Todas as mudanças abaixo foram testadas
isoladamente com seeds pareadas e teste de sinal; as que não sobreviveram estão na
seção 6.

---

## 1. Resumo em uma tabela

| # | Componente | GILS-RVND | Proposta | Ganho medido |
|---|---|---|---|---|
| 1 | Dados de subsequência | 3 matrizes `n x n` (`T`, `C`, `Cr`) refeitas a cada movimento | 2 prefix sums `O(n)` (`P`, `SP`) | **2,4-2,9x** mais rápido |
| 2 | Nº de vizinhanças | 5 | 13 (or-opt 1-6 + or-opt **invertido** 2-6) | or-opt invertido: **-0,24%** se retirado |
| 3 | Varredura | `O(n²)` completa | podada por lista dos **12 vizinhos mais próximos**, `O(n·K)` | componente dominante do H16 |
| 4 | Ordem de varredura | reinicia a cada movimento aplicado | contínua + **don't-look bits** | 2-10x mais iterações de ILS/s |
| 5 | Aplicação de movimento | `O(n)` (shift + rebuild completo) | `O(span)` (`rotate` + rebuild parcial) | incluído no item 4 |
| 6 | Construção | GRASP puro, RCL por cardinalidade, com `sort` | GRASP + **memória adaptativa** de arestas, RCL por limiar, sem `sort` | — |
| 7 | `I_ILS` | 100 (paper: `min(n, 100)`) | **300** | **-0,65%** vs o `--iils 10` do protocolo |
| 8 | Critério de parada | `I_max x I_ILS` iterações | `--max-time` (wall-clock) | permite comparação a tempo igual |

**Resultado**, 100 s/execução, 7 instâncias com n ≥ 200, 70 pares por seed:
**-1,249% vs `mdm_gils_rvnd`, 60 vitórias / 10 empates / 0 derrotas, p < 1e-6**
(detalhes em [`experiments/h19-dlb-fast-regime.md`](experiments/h19-dlb-fast-regime.md)).

---

## 2. Busca local: as quatro mudanças que carregam o resultado

### 2.1 Vizinhanças: 5 → 13

O GILS-RVND usa `swap`, `2-opt`, `reinsertion` (= or-opt de 1), `or-opt-2` e `or-opt-3`
([`src/rvnd.cpp:8`](../src/rvnd.cpp#L8)). A proposta usa:

- **or-opt direto, comprimentos 1 a 6** — o teto 6 é o achado de
  [`h12-extended-oropt`](experiments/h12-extended-oropt.md), reconfirmado no regime novo
  (3, 4, 8 e 10 são todos piores);
- **or-opt invertido, comprimentos 2 a 6** — realocar **e inverter** o bloco. Sob
  objetivo de latência esse movimento não é alcançável por composição dos cinco
  originais: inverter um bloco realocado muda o tempo de chegada de **todos** os
  clientes dentro dele, não só das duas junções. Vale **0,24%** sozinho.

### 2.2 Poda por lista de candidatos (K = 12)

Toda vizinhança do GILS-RVND varre o espaço de posições `O(n²)` inteiro. A proposta só
considera movimentos que **criam uma aresta para um dos 12 vizinhos mais próximos** do
extremo que ganha vizinho novo — a "vizinhança granular" padrão na literatura de
roteamento, que nenhum paper de MLP que este projeto reproduz usa. Cada varredura vira
`O(n·K)`.

É uma restrição heurística: movimentos de melhora cujas arestas novas sejam todas longas
deixam de ser vistos. Troca profundidade do ótimo local por número de iterações — a troca
que um orçamento de tempo fixo premia. K = 20 e K = 30 foram testados e são **piores**.

### 2.3 Don't-look bits com regra de despertar ciente da latência

A mudança nova desta rodada ([`src/neighborhoods_cand.cpp`](../src/neighborhoods_cand.cpp)).
Dentro de um ILS, revarrer todas as posições é quase tudo trabalho perdido: um double
bridge perturba um span limitado, e o resto é reexaminado só pra reconfirmar que continua
sem movimento.

A dificuldade no MLP é que a função objetivo é **posicional** — reordenar um trecho muda o
tempo de chegada de tudo que vem depois. Mas o efeito **cancela** no delta de um movimento
que fica inteiramente de um lado do trecho perturbado: a duração do prefixo entra nesse
delta só multiplicada pelo número de clientes depois dele, que a reordenação não altera.
Daí a regra usada:

> desperte toda cidade cuja **posição** mudou, mais as junções.

Exata para movimentos que ficam de um lado do span, heurística só para os que o
atravessam. O bit de uma cidade só é limpo depois que **todas** as 13 vizinhanças a
varreram sem achar movimento (um bit por vizinhança em `DlbState::examined`), e o estado
vive **entre** chamadas do RVND — então, depois de uma perturbação, o ILS re-arma apenas o
span que o double bridge tocou, em vez do tour inteiro.

### 2.4 Aplicação de movimento em `O(span)`

No GILS-RVND cada movimento aplicado custa `O(n)`: a reinserção desloca elemento a
elemento ([`src/neighborhoods.cpp:24`](../src/neighborhoods.cpp#L24)) e em seguida chama
`calculateStructures()` sobre o tour inteiro. Na proposta:

- um or-opt é uma **rotação** do intervalo afetado (`std::rotate`), não uma reconstrução;
- `Solution::calculateStructuresFrom(lo)` (novo) re-deriva `P`/`SP`/`posOf` só a partir da
  primeira posição perturbada — posições antes de `lo` não mudaram.

Movimentos perto da cauda do tour passam a custar quase nada.

---

## 3. Fora da busca local

### 3.1 Estruturas de subsequência (já compartilhada com o `gils_rvnd` do projeto)

O GILS-RVND original materializa três matrizes `n x n` (`T`, `C`, `Cr`) e as reconstrói do
zero a cada movimento. Todas as entradas das três são expressões `O(1)` sobre dois prefix
sums das arestas do tour:

```
P[j]  = soma das arestas ate a posicao j        SP[j] = P[0] + ... + P[j]
T(i,j)  = P[j] - P[i]
C(i,j)  = (SP[j]-SP[i]) - (j-i)*P[i]
Cr(i,j) = (j-i+1)*P[j] - (SP[j]-SP[i]+P[i])
```

`calculateStructures()` vai de `O(n²)` para `O(n)` e o footprint por solução de `3n²`
inteiros para `2n` int64 — em `att532`, 3,4 MB de tabelas que estouravam o cache viram
8 KB. Custos bit-idênticos aos da implementação anterior.

**Esta mudança já está no `./bin/gils_rvnd` deste projeto** (feita em
[`h16`](experiments/h16-candidate-neighborhoods.md)); está listada aqui porque é uma
diferença em relação ao GILS-RVND como publicado, e porque o baseline contra o qual a
proposta foi medida **já se beneficia dela**.

### 3.2 Construção

| | GILS-RVND | Proposta |
|---|---|---|
| RCL | por cardinalidade: os `alpha·\|CL\|` mais próximos, com `sort` a cada passo | por limiar: `custo <= min + alpha·(max-min)`, sem `sort` |
| Custo do candidato | `dist(r, c)` | `dist(r, c) - lambda·freq(r,c)·dist_media` |
| `alpha` | sorteado de `R = {0.00, 0.01, ..., 0.25}` a cada reinício | idem |

`freq(r,c)` é a frequência normalizada da aresta `(r,c)` no pool de soluções elite — a
**memória adaptativa**: arestas que aparecem muito nas boas soluções ficam mais baratas na
construção seguinte. O `sort` do GILS-RVND era `O(n log n)` dentro de um laço `O(n)` e não
mudava quais nós passam pelo limiar; sair dele deixa a construção `O(n²)`, o que passou a
importar quando a busca local ficou rápida o bastante pra construção virar fatia visível
de um reinício.

### 3.3 `I_ILS` e o papel do multi-start

O achado mais barato e maior desta rodada. O protocolo de tempo fixo do projeto impunha
`--iils 10` a todos os solvers (escolhido pra mineração do `mdm_gils_rvnd` disparar); isso
sozinho custava **0,65%** de qualidade (18 vitórias em 18 pares ao trocar para 100).

A razão é estrutural: **cada reinício joga fora a solução incumbente** para recomeçar de
uma construção gulosa randomizada, e a descida a partir de uma construção é a mais cara do
run. Quanto mais rápida a busca local, mais caro fica esse desperdício em termos
relativos. Com `I_ILS = 300`, em `att532` a proposta faz **8 reinícios** em 100 s, onde a
configuração do H16 fazia 224 — o orçamento passa a ser gasto aprofundando **uma**
trajetória de ILS, não visitando mais ótimos locais rasos.

`I_ILS = 1000` e `3000` já pioram (p = 0,012), então 300 é um ótimo real, não uma monotonia.

### 3.4 Critério de parada

`--max-time` verificado entre iterações de ILS e entre reinícios, nunca no meio de uma
convergência do RVND (o orçamento pode estourar por no máximo uma convergência). Sem isso
não existe comparação a tempo igual — comparar a `I_max x I_ILS` fixo compara orçamentos
computacionais diferentes, já que o custo por iteração difere muito entre os algoritmos.

---

## 4. Complexidade, lado a lado

| Operação | GILS-RVND | Proposta |
|---|---|---|
| `calculateStructures()` | `O(n²)` | `O(n)` — parcial, `O(n - lo)` |
| Uma varredura de vizinhança | `O(n²)` avaliações | `O(n·K)`, e só sobre cidades armadas |
| Aplicar um movimento | `O(n)` + rebuild `O(n²)` | `O(span)` + rebuild `O(n - lo)` |
| Avaliar um movimento | `O(1)` | `O(1)` (inalterado) |
| Descida pós-perturbação | varredura completa de todas as vizinhanças | proporcional ao span perturbado |
| Memória por solução | `3n²` ints | `2n` int64 + `2n` ints |

---

## 5. O que **não** mudou

- O esqueleto GRASP + ILS + RVND e a estrutura do laço.
- O **double bridge** como perturbação, uniforme e com `strength = 1`.
- A **aceitação estrita**: o ILS sempre volta para a melhor solução do reinício antes de
  perturbar de novo.
- A avaliação `O(1)` de movimento por concatenação de subsequências — a contribuição
  central do paper de 2012, usada sem alteração.
- O conjunto `R` de valores de `alpha`.

---

## 6. Mudanças testadas e **rejeitadas**

Todas implementadas, verificadas (tour válido + custo recalculado das coordenadas) e
testadas com seeds pareadas. Nenhuma entrou:

| Mudança | Resultado |
|---|---|
| `--cand-k` 20 / 30 | +0,32% / +0,25% |
| `--cand-maxlen` 3 / 4 / 8 / 10 | +0,11% / +0,08% / +0,05% / +0,09% |
| Âncoras de or-opt no início do tour (`--cand-front 5`) | +0,34% |
| 2-opt ancorado nas duas arestas novas (`--cand-2opt-both`) | +0,12% |
| Aceitação por limiar no ILS (`--accept-eps`) | +0,17% |
| Polimento com RVND completo no novo melhor global (`--polish-on-best`) | +0,13% |
| **Crossover arc-based (ABX)** entre elites, Ren/Hao/Wu/Fu EJOR 2023 (`--abx-rate`) | +0,26% |
| Reinício por kick do incumbente (`--restart-kick 3`) | +0,26%, p = 0,008 |
| Double bridge com blocos limitados (`--db-maxseg-div`) | nulo |
| Perturbação enviesada para o início do tour (`--db-front-bias`) | +0,12% a +0,33% |

Isso fecha o padrão que as 19 hipóteses deste projeto desenharam: **no MLP, mudar *de onde*
a busca recomeça não sobrevive ao RVND — o que paga é vizinhança e velocidade.**
