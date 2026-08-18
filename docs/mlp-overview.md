# O Problema da Latência Mínima (Minimum Latency Problem)

Resumo do problema, do artigo de referência do projeto e de como o código em
`src/`/`include/` implementa cada peça do método. Baseado em:

- `docs/A simple and effective metaheuristic for the Minimum Latency Problem.pdf`
  (Silva, Subramanian, Vidal & Ochi, *European Journal of Operational Research* 221 (2012) 513–520)
- `README.md`
- `algorithms/grasp_am.md`
- Código-fonte em `src/` e `include/`

---

## 1. Definição do problema

O **Minimum Latency Problem (MLP)** — também conhecido na literatura como
*Traveling Repairman Problem*, *Delivery Man Problem*, *Cumulative TSP* ou
*School Bus Driver Problem* — é uma variante do TSP.

Dado um grafo completo direcionado `G = (V, A)`, com `V = {0, ..., n}` vértices
e tempos de viagem `t_ij` associados a cada arco, o vértice `0` é o **depósito**.
Uma solução é um circuito Hamiltoniano que começa e termina em `0`. Para cada
vértice `i`, sua **latência** `l(i)` é o tempo total de viagem até alcançá-lo
(o depósito tem `l(0) = 0`).

O objetivo é minimizar a **soma das latências de todos os vértices**:

```
minimizar  Σ l(i),  i = 0..n
```

Diferença essencial em relação ao TSP clássico:

- **TSP**: minimiza o tempo total para visitar todos os clientes (orientado ao
  *servidor* — quem executa a rota).
- **MLP**: minimiza o tempo médio de espera de cada cliente (orientado ao
  *cliente* — quem é visitado). Um arco inserido no início do circuito afeta a
  latência de **todos** os vértices seguintes, o que torna a função objetivo
  não local: pequenas mudanças na configuração podem gerar mudanças bem não
  locais na estrutura da solução ótima.

O MLP é **NP-difícil** em espaços métricos gerais e mesmo em árvores com pesos
nas arestas. Métodos exatos atuais não resolvem de forma consistente
instâncias com mais de ~100 clientes; poucas metaheurísticas eficientes
existiam na literatura até a publicação deste artigo (2012).

Aplicações práticas: entrega domiciliar, logística de ajuda humanitária,
recuperação de dados em redes de computadores — cenários em que a satisfação
do cliente (tempo de espera) importa mais do que o tempo total de operação.

---

## 2. O artigo: GILS-RVND

O artigo propõe uma metaheurística simples chamada **GILS-RVND**, que combina:

- **GRASP** (Greedy Randomized Adaptive Search Procedure) — construção gulosa
  randomizada de soluções iniciais;
- **ILS** (Iterated Local Search) — busca local iterada com perturbação e
  critério de aceitação;
- **RVND** (Variable Neighborhood Descent with Random neighborhood ordering) —
  busca local em múltiplas vizinhanças, exploradas em ordem aleatória.

A segunda contribuição do artigo é um **procedimento de avaliação de
movimentos em O(1) amortizado**, aplicável a qualquer estrutura de vizinhança
baseada em um número limitado de trocas de arcos (o que evita o custo O(n) por
avaliação e O(n³) por vizinhança completa que uma avaliação direta exigiria).

### 2.1 Algoritmo principal — GILS-RVND

```
Procedimento GILS-RVND(IMax, IILS, R)
  f* ← ∞
  para i = 1 .. IMax:
    α ← valor aleatório em R
    s ← Construction(α)
    s' ← s
    iterILS ← 0
    enquanto iterILS < IILS:
      s ← RVND(s)
      se f(s) < f(s'):
        s' ← s
        iterILS ← 0
      s ← Perturb(s')      # sempre perturba a melhor solução corrente
      iterILS ← iterILS + 1
    se f(s') < f*:
      s* ← s'
      f* ← f(s')
  retornar s*
```

Pontos-chave:

- `IMax` iterações de multi-start (nova construção randomizada a cada vez).
- Em cada iteração, RVND melhora a solução até `IILS` perturbações
  consecutivas sem melhoria.
- A perturbação é **sempre aplicada sobre a melhor solução corrente `s'`**
  (critério de aceitação "melhor encontrado", não a última solução visitada).
- Parâmetros usados no artigo (bom compromisso qualidade/tempo):
  `IMax = 10`, `IILS = min(100, n)`, `R = {0.00, 0.01, ..., 0.25}`.

### 2.2 Construção gulosa randomizada (GRASP)

```
Procedimento Construction(α)
  s ← {0}                      # começa no depósito
  CL ← V \ {0}                 # candidate list
  r ← 0
  enquanto CL ≠ ∅:
    ordenar CL por distância crescente a r
    RCL ← os α% melhores candidatos de CL
    c ← escolha aleatória em RCL
    s ← s ∪ {c}; r ← c
    CL ← CL \ {r}
  retornar s
```

Quando o conjunto dos `α%` melhores tem tamanho menor que 1, ou quando
`α = 0`, o algoritmo escolhe sempre o melhor candidato (equivalente ao
vizinho mais próximo puro).

### 2.3 Busca local — RVND com 5 vizinhanças

```
Procedimento RVND(s)
  NL ← todas as vizinhanças
  enquanto NL ≠ ∅:
    escolher N(g) ∈ NL aleatoriamente
    s' ← melhor vizinho de s em N(g)
    se f(s') < f(s):
      s ← s'; atualizar NL (repopula todas as vizinhanças)
    senão:
      remover N(g) de NL
  retornar s
```

As 5 estruturas de vizinhança (clássicas do TSP, adaptadas ao MLP), todas
exploradas de forma exaustiva com estratégia *best improvement*:

| Vizinhança  | Descrição |
|---|---|
| Swap (N¹)        | troca dois clientes de posição |
| 2-opt (N²)       | remove dois arcos não adjacentes e reinsere outros dois |
| Reinsertion (N³) | realoca um cliente para outra posição da rota |
| Or-opt2 (N⁴)     | realoca um par de clientes adjacentes |
| Or-opt3 (N⁵)     | realoca um trio de clientes adjacentes |

RVND escolhe a próxima vizinhança **aleatoriamente** entre as que ainda não
falharam (em vez de ordem determinística) — testes preliminares dos autores
mostraram que isso encontra soluções melhores.

### 2.4 Avaliação de movimentos em O(1) — reotimização por concatenação

Como qualquer movimento no MLP afeta a latência de muitos vértices
subsequentes, uma avaliação ingênua custa O(n) por movimento (O(n³) por
vizinhança). O artigo propõe um framework de reotimização "por concatenação"
que reduz isso para **O(1) amortizado**, após um pré-processamento O(n²).

Cada subsequência `σ = (σ_u, ..., σ_v)` guarda três valores:

- **T(σ)** — duração (tempo de viagem) para percorrer a subsequência;
- **C(σ)** — custo (soma de latências) da subsequência, partindo do tempo 0;
- **W(σ)** — "custo de atraso": quanto o custo aumenta por unidade de atraso
  no instante de início (equivale ao número de clientes na subsequência).

Concatenação de duas subsequências `σ ⊕ σ'` (Proposição 1 do artigo):

```
T(σ ⊕ σ') = T(σ) + t(σ_v, σ'_w) + T(σ')
C(σ ⊕ σ') = C(σ) + W(σ') · (T(σ) + t(σ_v, σ'_w)) + C(σ')
W(σ ⊕ σ') = W(σ) + W(σ')
```

Qualquer movimento (swap, 2-opt, reinsertion, or-opt) é visto como uma
concatenação de no máximo 4-5 subsequências (incluindo suas versões
revertidas, para 2-opt), então sua avaliação vira uma sequência de poucas
aplicações da fórmula acima — O(1) por movimento.

### 2.5 Perturbação — Double-bridge

Quando a busca local (RVND) não melhora mais a solução, aplica-se o
**double-bridge** (Martin, Otto & Felten, 1991): remove 4 arcos e reinsere
outros 4 de forma que a rota permaneça viável — equivalente a permutar dois
segmentos disjuntos da rota. É uma perturbação clássica de ILS por ser difícil
de desfazer com movimentos locais simples (evita ficar preso no mesmo ótimo
local).

### 2.6 Resultados computacionais (resumo)

- Testado em **9 conjuntos de instâncias benchmark**, totalizando 173
  instâncias, de 10 a 1000 clientes (TSPLIB + instâncias geradas por
  Salehipour et al., 2011).
- Para instâncias com solução ótima conhecida (até 107 clientes), o
  GILS-RVND **encontra o ótimo sistematicamente**, em frações de segundo a
  poucos segundos — inclusive resolvendo 2 instâncias antes em aberto
  (`rat99`, `eil101`).
- Comparado a Salehipour et al. (2011) e Ngueveu et al. (2010), o GILS-RVND
  obteve gap médio menor (ou igualou/melhorou) o estado da arte, com menor
  tempo computacional escalado, apesar de ser conceitualmente mais simples e
  ter poucos parâmetros.
- Gaps médios em relação ao *nearest neighbor* (heurística construtiva com
  α=0), para instâncias maiores geradas por Salehipour et al.: -13,00% (100
  clientes), -14,35% (200), -15,16% (500), -15,47% (1000).

---

## 3. Este projeto: mapeamento artigo → código

O projeto implementa o GILS-RVND do artigo (e o estende com uma segunda
metaheurística híbrida usando Tabu Search e memória adaptativa). Depósito
fixo no vértice `0`, objetivo é minimizar a soma das latências ao longo de um
**caminho** Hamiltoniano (não circuito — ver `README.md`, que fala em
"Hamiltonian path").

### 3.1 Estruturas de dados de reotimização

`include/solution.h` implementa exatamente os data-structures da Seção 3.2 do
artigo:

- `T[i][j]` → duração `T(σ)` da subsequência `[i..j]`
- `C[i][j]` → custo/latência `C(σ)` da subsequência `[i..j]`
- `Cr[i][j]` → custo da subsequência **revertida** (necessário para avaliar
  2-opt em O(1), já que inverte a ordem de visita de um trecho)
- `getW(i, j)` → equivalente ao `W(σ)` do artigo (número de clientes na
  subsequência)

Os métodos `evaluateSwap`, `evaluate2Opt`, `evaluateReinsertion` e
`evaluateOrOpt` em `src/solution.cpp` usam essas estruturas pré-computadas
para avaliar movimentos sem recalcular a rota inteira — a mesma ideia de
concatenação de subsequências da Proposição 1.

### 3.2 Vizinhanças

`include/neighborhoods.h` / `src/neighborhoods.cpp` implementam exatamente as
5 vizinhanças do artigo:

- `neighborhood_swap` → N¹ (Swap)
- `neighborhood_2opt` → N² (2-opt)
- `neighborhood_reinsertion` → N³ (Reinsertion)
- `neighborhood_oropt2` → N⁴ (Or-opt2)
- `neighborhood_oropt3` → N⁵ (Or-opt3)

### 3.3 RVND

`src/rvnd.cpp` (`include/rvnd.h`) implementa o Algoritmo 3 do artigo: lista de
vizinhanças embaralhada, aplica cada uma até esgotar melhorias, repopula a
lista a cada melhoria, remove a vizinhança da lista quando ela falha, termina
quando a lista esvazia.

### 3.4 Construção GRASP

`src/construction.cpp` (`include/construction.h`) implementa o Algoritmo 2:
lista de candidatos ordenada por proximidade ao último vértice inserido, RCL
com os `α%` melhores, escolha aleatória dentro da RCL.

### 3.5 GILS-RVND

`src/gils_rvnd.cpp` implementa o Algoritmo 1 quase literalmente:

- `I_max` (`--imax`, padrão 10) e `I_ILS` (`--iils`, padrão 100, limitado a
  100) correspondem a `IMax` e `IILS` do artigo.
- `R` é construído como `{0.00, 0.01, ..., 0.25}` — o mesmo conjunto usado no
  artigo.
- `perturb()` implementa o double-bridge (3 cortes aleatórios, reordena os
  4 segmentos como `seg1 + seg3 + seg2 + seg4`), igual à Fig. 1 do artigo.
- O laço principal reproduz fielmente o pseudocódigo: constrói, aplica RVND,
  atualiza `s'` (melhor da iteração) quando há melhoria, perturba sempre a
  partir de `s'`, conta iterações sem melhoria em `iterILS`.

### 3.6 Extensões do projeto além do artigo

O projeto vai além do artigo original com:

- **`tabu_search`** — Tabu Search com varredura completa da vizinhança e
  critério de aspiração (não está no artigo original).
- **`gils_rvnd_tabu`** — híbrido que intercala GILS-RVND com intensificação
  via Tabu Search em caso de estagnação (`--tabu-iter`, `--tabu-every`,
  `--tenure`).
- **`grasp_am`** (GRASP com Memória Adaptativa) — descrito em
  `algorithms/grasp_am.md`, não faz parte do artigo. Introduz:
  - Um **Elite Set** de soluções (Algoritmo 1 do doc): mantém as `maxSize`
    melhores soluções encontradas, com recontagem de frequência de uso de
    cada aresta nas soluções elite.
  - Uma **construção com memória adaptativa** (Algoritmo 2 do doc): o custo
    `dist(u,v)` de cada candidato é penalizado por um **bônus** proporcional
    à frequência da aresta `(u,v)` no Elite Set (`freqNorm`) e à escala do
    problema (`avgDist`), controlado por um parâmetro `λ`. Isso viesa a
    construção gulosa a favorecer arestas que aparecem com frequência em boas
    soluções anteriores — uma forma de aprendizado entre iterações do GRASP,
    ausente na construção puramente gulosa-aleatória do artigo original.
  - O laço GRASP-AM (Algoritmo 3 do doc) é análogo ao GILS-RVND, mas troca a
    construção padrão por `Construction-AM(α, λ, EliteSet)` e atualiza o
    Elite Set a cada iteração.
- **`backtracking`** — solver exato (branch-and-bound), útil só como baseline
  para instâncias pequenas.

### 3.7 Como o projeto valida contra o artigo

`run_experiments.py` (`--mode compare-best`, `--mode exact`,
`--mode compare-solvers`) permite comparar os solvers do projeto contra
soluções conhecidas (`instances/solutions/best_solutions.json`), contra o
backtracking exato, ou uns contra os outros — o mesmo tipo de validação
(gap médio, tempo médio, melhor solução) que o artigo reporta nas Tabelas
1–8, embora aqui usando o conjunto próprio de instâncias em `instances/`
(subconjunto de TSPLIB: `eil51`, `berlin52`, `st70`, `pr76`, `kroA100`,
`kroD100`, `lin105`, `pr107`, `pr226`, `lin318`, `att532`, etc.).

---

## 4. Pesquisa de melhorias (sessões posteriores)

Depois da leitura inicial do artigo (seções 1-3 acima), o projeto passou
por uma rodada extensa de pesquisa testando hipóteses de melhoria sobre
o GILS-RVND — 13 linhas de investigação (H1-H13), documentadas
individualmente em `docs/experiments/*.md`. Resumo:

- **A esmagadora maioria (H1-H11, H12b, H13) deu nula em qualidade**
  (perturbação adaptativa, path relinking, vizinhança de prefixo,
  multi-improvement, perturbação por regret, dynasearch, guided local
  search, LNS/ruin-and-recreate em 3 variantes, 3-opt genuíno, mineração
  de padrões via FPMax*) — em quase todos os casos o RVND absorve
  qualquer vantagem de ponto de entrada ou mecanismo de escape testado.
  Duas exceções renderam só **velocidade**, não qualidade:
  `grasp_am`/`gils_am_rvnd` (construção enviesada por memória, 20-26%
  mais rápido) e `dbmea` (populacional, mais rápido em `n` grande).
- **H12a é a exceção real — or-opt estendido a segmentos maiores (4, 5,
  6)** (`neighborhood_oropt4/5/6`, `RVND_ExtendedOrOpt`,
  `--rvnd-mode extended-oropt` em `gils_rvnd`/`gils_am_rvnd`): as 5
  vizinhanças do artigo original só realocam segmentos de tamanho 1-3;
  estendendo pra 4-6 abre uma vizinhança genuinamente mais forte, que o
  RVND original nunca alcançaria por mais que reinicie. O efeito **cresce
  fortemente com `n`**: nulo em `lin318` (n=318), modesto mas
  significativo em `pr439`/`att532` (n=439/532, +0,3-0,4%), e **forte e
  estatisticamente perfeito a partir de n=1000** (10 vitórias em 10 seeds,
  p=0,002, +1,1-1,2% em `rand1000` e `rand2000`). Combinado com
  `gils_am_rvnd` em `n≳1000`, a vantagem deixa de ser trade-off — fica
  **melhor em qualidade E mais rápido** que o baseline ao mesmo tempo.
  Ver `docs/experiments/h12-extended-oropt.md` para a história completa.

Novos binários desta fase: `gils_am_rvnd`, `dbmea`, `mdm_gils_rvnd`
(mineração de padrões, H13 — nulo, mas implementação e infra ficam no
projeto). Novos modos de `--rvnd-mode` em `gils_rvnd`/`gils_am_rvnd`:
`multi` (H4), `extended-oropt`/`extended-oropt-wide`/`extended-oropt-3opt`
(H12a/H12b) — `single` continua o default em todos os binários.

**Recomendação prática**: para instâncias com `n≳1000` onde qualidade
importa mais que reproduzir exatamente o artigo original, usar
`gils_am_rvnd --rvnd-mode extended-oropt` em vez do `gils_rvnd` puro.

## 5. Referências rápidas

- Artigo: Silva, M.M., Subramanian, A., Vidal, T., Ochi, L.S. (2012). *A simple
  and effective metaheuristic for the Minimum Latency Problem*. European
  Journal of Operational Research, 221, 513–520.
  DOI: 10.1016/j.ejor.2012.03.044
- `algorithms/grasp_am.md` — extensão do projeto (GRASP com Memória Adaptativa),
  não presente no artigo original.
- `README.md` — instruções de build, uso dos binários e do
  `run_experiments.py`.
