# H16 — vizinhanças podadas por lista de candidatos: batendo o MDM-GILS-RVND a tempo fixo

Status: **ENCERRADA COM SUCESSO.** `gils_am_rvnd --rvnd-mode candidate --cand-k 12`
bate o `mdm_gils_rvnd` a 100 s/execução nas três maiores instâncias TSPLIB deste
projeto: **−0,649% agregado, 27 vitórias / 0 empates / 3 derrotas em 30 pares,
p < 0,0001**, vencendo nas três instâncias individualmente. O efeito cresce com `n`
(−0,19% em `lin318`, −1,20% em `att532`).

Complementa [[fixed-time-100s-tsplib]], que mediu os três algoritmos de referência
nesse mesmo protocolo e achou o MDM nulo e o `extended-oropt` sem significância.

## 1. Ponto de partida

Em [[fixed-time-100s-tsplib]] o melhor achado anterior do projeto
(`gils_am_rvnd --rvnd-mode extended-oropt`, [[h12-extended-oropt]]) batia o
`gils_rvnd`, mas contra o `mdm_gils_rvnd` a 100 s ficava em −0,185% (14/0/6,
p = 0,115) — não significativo. A pergunta desta hipótese era o que faltava para
ganhar do MDM com folga estatística no mesmo orçamento de tempo.

Diagnóstico: a 100 s em `att532` o MDM completava 53 restarts e o `extended-oropt`
ainda menos. Com tão poucos reinícios, **nenhum** dos dois chega perto de esgotar o
que a busca teria a oferecer — o gargalo não era a qualidade do ótimo local, era
quantos ótimos locais cabem no orçamento. A tempo fixo, velocidade **é** qualidade.

## 2. O que foi mudado

Quatro mudanças, três delas puramente de custo computacional e uma de vizinhança.

### 2.1 Dados de subsequência em O(n) no lugar de três matrizes O(n²)

`Solution` reconstruía `T`, `C` e `Cr` (três matrizes n×n) do zero a **cada movimento
aplicado**. Todas as entradas das três são expressões O(1) sobre dois prefix sums
das arestas do tour:

```
P[j]  = soma das arestas até a posição j        SP[j] = P[0] + ... + P[j]
T(i,j)  = P[j] - P[i]
C(i,j)  = (SP[j]-SP[i]) - (j-i)*P[i]
Cr(i,j) = (j-i+1)*P[j] - (SP[j]-SP[i]+P[i])
```

Isso reproduz as matrizes antigas exatamente (mesmas recorrências
`C(i,j)=C(i,j-1)+T(i,j)` e `Cr(i,j)=Cr(i+1,j)+T(i,j)`), leva
`calculateStructures()` de O(n²) para O(n) e o footprint por `Solution` de 3n²
inteiros para 2n int64 — em `att532`, 3,4 MB de tabelas que estouravam o cache
viram 8 KB.

**Verificação**: custos bit-idênticos aos da implementação anterior em
`gils_am_rvnd`/`gils_rvnd`/`mdm_gils_rvnd` sobre `lin318`/`pr439`/`att532`. A
trajetória de busca não muda; só o relógio. **2,4–2,9× mais rápido.**

### 2.2 Poda por lista de candidatos (k-vizinhos mais próximos)

Todas as vizinhanças varriam o espaço de posições O(n²) inteiro. O `Evaluator` já
construía a lista dos K vizinhos mais próximos de cada cidade (`fNearCity`), mas até
aqui só o experimento de Lin-Kernighan ([[h14-lk-escape]]) a usava. A regra de poda,
em cada caso "o movimento tem que criar uma aresta para um dos K vizinhos mais
próximos do extremo que ganha vizinho novo":

- **or-opt** (direto e invertido, qualquer comprimento): o bloco realocado tem que
  cair ao lado de um vizinho próximo de `tour[i]` ou de `tour[j]`.
- **2-opt**: inverter `[i..j]` cria a aresta `(tour[i-1], tour[j])`, então `tour[j]`
  tem que ser vizinho próximo de `tour[i-1]`.
- **swap**: `tour[j]` passa a ficar entre `tour[i-1]` e `tour[i+1]`, mesma regra.

Cada varredura passa de O(n²) para O(n·K). É uma restrição heurística — movimentos
de melhora cujas arestas novas sejam todas longas deixam de ser vistos —, ou seja,
troca profundidade do ótimo local por número de iterações. É exatamente a troca que
um orçamento de tempo fixo premia.

### 2.3 Or-opt com o segmento invertido

As cinco vizinhanças de Silva et al. (2012) — e todo paper de MLP que este projeto
reproduz — só reinserem um segmento na orientação original. Realocar **e inverter** é
padrão na literatura de roteamento de veículos e nunca tinha sido testado aqui. Sob
objetivo de latência os dois movimentos são genuinamente diferentes: inverter um
bloco realocado muda o tempo de chegada de **todos** os clientes dentro dele, não só
das duas junções, então não é alcançável por composição das cinco existentes.
`RVND_Candidate` roda or-opt direto nos comprimentos 1–6 e invertido nos 2–6.

### 2.4 Varredura contínua no lugar de reinício por movimento

As vizinhanças reiniciavam o scan na primeira posição depois de cada movimento
aplicado, pagando uma varredura inteira por melhora — caro no começo de uma descida,
quando quase toda posição ainda rende movimento. As varreduras podadas seguem de onde
estavam e são repetidas até uma passar limpa: a descida ainda termina em ótimo local
da vizinhança podada, mas custa O(n·K) por varredura em vez de por movimento.

### 2.5 Efeito combinado

Em `att532`, 20 iterações de ILS (3 seeds):

| modo | tempo | ganho |
|---|---:|---:|
| `extended-oropt` (incumbente) | 18,48 s | — |
| `extended-oropt-rev` | 31,25 s | 0,6× |
| `candidate` (K=12) | 2,27 s | **8,1×** |

E isso já contando as vizinhanças invertidas, que o `extended-oropt` nem tem.

## 3. Protocolo

```bash
python3 run_experiments.py --mode fixed-time --time-limit 100 --runs 10 --iils 10 \
    --instances lin318 pr439 att532 \
    --solvers mdm_gils_rvnd gils_am_rvnd_cand12 gils_am_rvnd_cand12_db10 \
              gils_am_rvnd_extended_oropt
```

Protocolo de [[fixed-time-protocol]]: 100 s de wall-clock por execução idênticos para
todos, execuções sequenciais, pareadas por seed (1–10), baseline `mdm_gils_rvnd`.
Só as três instâncias com n > 200, que é onde [[fixed-time-100s-tsplib]] mostrou que
existe poder estatístico (as sete menores saturam e empatam 0/10/0).

**Checkpoint refeito**: os dados de 100 s anteriores (hoje em
`scripts/fixed_time_100s_prespeedup.json`) são de binários pré-otimização e não são
comparáveis — a mudança da seção 2.1 acelera `mdm_gils_rvnd` e `gils_rvnd` também,
então o baseline teve que ser remedido do zero. `scripts/fixed_time_100s.json` passou
a conter só as medições novas.

## 4. Resultado principal — 100 s, N=30 pareado

`gils_am_rvnd --rvnd-mode candidate --cand-k 12` vs `mdm_gils_rvnd`:

| instância | n | mean_rel% | W/T/L | p (sinais) |
|---|---:|---:|---:|---:|
| `lin318` | 318 | **-0.188** | 9/0/1 | **0.021** |
| `pr439` | 439 | **-0.562** | 8/0/2 | 0.109 |
| `att532` | 532 | **-1.196** | 10/0/0 | **0.002** |
| **AGREGADO** | | **-0.649** | **27/0/3** | **0.00001** |

Negativo = melhor que o MDM. Vence nas três instâncias, e a magnitude cresce
monotonicamente com `n`.

### 4.1 Custos e reinícios por instância

| instância | solver | restarts médios | custo médio | melhor custo | gap BKS |
|---|---|---:|---:|---:|---:|
| `lin318` | `mdm_gils_rvnd` | 168 | 5 586 455.7 | 5 565 187 | 0.464% |
| `lin318` | `gils_am_rvnd_cand12` | 781 | 5 575 913.4 | 5 562 148 | 0.274% |
| `pr439` | `mdm_gils_rvnd` | 92 | 17 912 677.4 | 17 856 623 | 1.267% |
| `pr439` | `gils_am_rvnd_cand12` | 318 | 17 811 886.4 | 17 757 765 | 0.697% |
| `att532` | `mdm_gils_rvnd` | 53 | 5 704 564.1 | 5 687 070 | 2.057% |
| `att532` | `gils_am_rvnd_cand12` | 224 | 5 636 343.4 | 5 623 523 | 0.837% |

O mecanismo do ganho fica explícito na coluna de reinícios: em `att532` o `cand12`
completa 224 restarts no mesmo orçamento em que o MDM completa 53 — **4,2× mais**
ótimos locais visitados. O gap médio de BKS cai em todas as três, e em `att532` cai
para menos da metade (2,057% -> 0,837%).

## 5. Contra o incumbente anterior do projeto

| comparação | orçamento | N | mean_rel% | W/T/L |
|---|---|---:|---:|---:|
| `cand12` vs `extended-oropt` | 30 s | 18 | -0.457 | 16/0/2 |
| `cand12` vs `extended-oropt` | 100 s | 20 | -0.190 | 15/0/5 |

(A 100 s o `extended-oropt` só tem `lin318` e `pr439` no lote — `att532` foi cortado
do batch por tempo de máquina.)

## 6. Triagem que selecionou a configuração (30 s, N=18)

Antes do lote de 100 s, os mecanismos foram triados isoladamente a 30 s nas mesmas
três instâncias, 6 seeds, todos contra o `mdm_gils_rvnd`:

| variante | mean_rel% | W/T/L | p |
|---|---:|---:|---:|
| `gils_am_rvnd_cand12_db10` | -0.673 | 16/0/2 | **0.0013** |
| `gils_am_rvnd_cand20` | -0.631 | 16/0/2 | **0.0013** |
| `gils_am_rvnd_cand12` | -0.626 | 17/0/1 | **0.0001** |
| `gils_am_rvnd_ext_db10` | -0.558 | 15/0/3 | **0.0075** |
| `gils_am_rvnd_oropt_rev` | -0.451 | 15/0/3 | **0.0075** |
| `gils_am_rvnd_rev_db10` | -0.449 | 16/0/2 | **0.0013** |
| `gils_am_rvnd_extended_oropt` | -0.169 | 9/1/8 | 1.0000 |

Leitura:

1. **Todos** os mecanismos novos batem o MDM com significância; o incumbente
   `extended-oropt` (última linha) não bate.
2. A poda por lista de candidatos é o componente dominante — as três variantes
   `cand*` lideram.
3. O or-opt invertido sozinho (`oropt_rev`, sem poda) já vale −0,451% (p = 0,0075),
   confirmando que a vizinhança nova tem valor próprio e não é só efeito de
   velocidade.
4. K = 12 e K = 20 empatam na prática; ficou K = 12, por ser mais barato e ter a
   melhor taxa de vitórias (17/0/1).
5. O double-bridge com blocos limitados (`db10`, [[h17]]) melhora a média mas piora a
   taxa de vitórias, e a 100 s ficou atrás do `cand12` puro. **Não adotado.**

## 7. Verificação de corretude

Toda vizinhança nova produz tours verificados independentemente: permutação completa
de `0..n-1` começando no depósito, e custo recomputado a partir das coordenadas
batendo exatamente com o custo reportado, em `lin318`/`pr439`/`att532`. O script de
verificação recomputa as distâncias com a mesma convenção de arredondamento do
`Evaluator` (truncamento em EUC_2D, arredondamento para cima em ATT).

A mudança de prefix sums foi validada mais forte ainda: **igualdade bit-a-bit** dos
custos com a implementação anterior, nos três binários.

## 8. Ressalvas

1. **A poda poderia ser portada para o MDM.** A comparação é entre os algoritmos como
   estão implementados, e o `mdm_gils_rvnd` continua com varredura O(n²) completa.
   Parte da vantagem medida é de engenharia de vizinhança, não de estratégia de
   busca; um MDM com as mesmas listas de candidatos seria um baseline mais duro. As
   melhorias da seção 2.1 (prefix sums), essas sim, **já** beneficiam os três
   binários igualmente, e mesmo assim o MDM perde.
2. **Só n > 200.** As sete instâncias menores saturam a 100 s
   ([[fixed-time-100s-tsplib]] seção 7); nada aqui diz respeito a elas.
3. **`--iils 10` não foi tunado** para o novo regime. Com a busca 8× mais rápida, o
   número de reinícios subiu uma ordem de grandeza e o valor ideal de `I_ILS`
   provavelmente mudou — é o próximo experimento natural.
4. **A perturbação enviesada para o início do tour** (`--db-front-bias`, motivada por
   o fato de uma aresta na posição p ser paga por todos os n-p clientes seguintes)
   está implementada mas ainda não foi testada.
