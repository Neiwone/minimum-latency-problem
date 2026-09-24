# H16 — vizinhanças podadas por lista de candidatos: batendo o MDM-GILS-RVND a tempo fixo

**Veredito: confirmada.** `gils_am_rvnd --rvnd-mode candidate --cand-k 12` bate o
`mdm_gils_rvnd` a 100 s/execução nas três maiores instâncias TSPLIB do projeto:
**−0,649% agregado, 27 vitórias / 0 empates / 3 derrotas em 30 pares, p < 0,0001**,
vencendo nas três instâncias individualmente. O efeito cresce com `n` (−0,19% em
`lin318`, −1,20% em `att532`). Adotado; é a base do [H19](h19-dlb-fast-regime.md).

## Hipótese

Em [fixed-time-100s-tsplib](../benchmarks/fixed-time-100s-tsplib.md), o melhor achado anterior
(`--rvnd-mode extended-oropt`, [H12](h12-extended-oropt.md)) ficava em −0,185% contra
o MDM a 100 s (14/0/6, p = 0,115), não significativo. Em `att532` o MDM completava só
53 restarts no orçamento, e o `extended-oropt` ainda menos: o gargalo não é a qualidade
do ótimo local, é quantos ótimos locais cabem no tempo. A tempo fixo, velocidade é
qualidade; uma busca local muito mais barata deveria ganhar do MDM com folga.

## O que foi testado

Quatro mudanças em [`src/gils_am_rvnd.cpp`](../../src/gils_am_rvnd.cpp) e na
`Solution`, três de custo e uma de vizinhança:

1. **Dados de subsequência em O(n).** A `Solution` reconstruía as matrizes n×n `T`,
   `C` e `Cr` a cada movimento aplicado. Todas as entradas são expressões O(1) sobre
   dois prefix sums das arestas do tour (`P[j]` e `SP[j] = P[0] + ... + P[j]`):
   `T(i,j) = P[j] − P[i]`, `C(i,j) = (SP[j]−SP[i]) − (j−i)·P[i]`,
   `Cr(i,j) = (j−i+1)·P[j] − (SP[j]−SP[i]+P[i])`. A reconstrução cai de O(n²) para
   O(n) e o footprint de 3n² inteiros para 2n int64 (em `att532`, 3,4 MB que
   estouravam o cache viram 8 KB). Custos bit-idênticos aos da implementação anterior
   nos três binários; a trajetória não muda, só o relógio: **2,4–2,9× mais rápido**.
   Beneficia `gils_rvnd` e `mdm_gils_rvnd` igualmente.
2. **Poda por lista de candidatos** (`--cand-k`, K vizinhos mais próximos). O
   movimento tem que criar uma aresta para um dos K vizinhos mais próximos do extremo
   que ganha vizinho novo: no or-opt, o bloco cai ao lado de um vizinho próximo de
   `tour[i]` ou `tour[j]`; no 2-opt, `tour[j]` tem que ser vizinho próximo de
   `tour[i-1]`; no swap, a mesma regra. Cada varredura passa de O(n²) para O(n·K). É
   uma restrição heurística: troca profundidade do ótimo local por número de
   iterações.
3. **Or-opt com o segmento invertido.** As cinco vizinhanças de Silva et al. (2012)
   só reinserem o segmento na orientação original. Sob latência, inverter o bloco
   realocado muda o tempo de chegada de todos os clientes dentro dele, então não é
   alcançável por composição das cinco. O modo `candidate` roda or-opt direto nos
   comprimentos 1–6 e invertido nos 2–6.
4. **Varredura contínua.** Em vez de reiniciar o scan na primeira posição a cada
   movimento aplicado, as varreduras podadas seguem de onde estavam e se repetem até
   uma passar limpa: continua terminando em ótimo local da vizinhança podada, mas custa
   O(n·K) por varredura, não por movimento.

Efeito combinado em `att532`, 20 iterações de ILS (3 seeds):

| modo | tempo | ganho |
|---|---:|---:|
| `extended-oropt` (incumbente) | 18,48 s | — |
| `extended-oropt-rev` | 31,25 s | 0,6× |
| `candidate` (K=12) | 2,27 s | **8,1×** |

Protocolo de [tempo fixo](../benchmarks/fixed-time-protocol.md): 100 s de wall-clock por execução
para todos, execuções sequenciais, pareadas por seed (1–10), `--iils 10`, baseline
`mdm_gils_rvnd`. Só `lin318`/`pr439`/`att532`, onde há poder estatístico (as sete
menores saturam e empatam 0/10/0). O baseline foi remedido do zero, porque a mudança 1
também acelera o MDM; os dados de 100 s anteriores
(`results/fixed-time/fixed_time_100s_prespeedup.json`) não são comparáveis.

## Resultados

**Triagem a 30 s** (N=18, 6 seeds por instância, todos contra `mdm_gils_rvnd`):

| variante | mean_rel% | W/T/L | p |
|---|---:|---:|---:|
| `gils_am_rvnd_cand12_db10` | -0.673 | 16/0/2 | **0.0013** |
| `gils_am_rvnd_cand20` | -0.631 | 16/0/2 | **0.0013** |
| `gils_am_rvnd_cand12` | -0.626 | 17/0/1 | **0.0001** |
| `gils_am_rvnd_ext_db10` | -0.558 | 15/0/3 | **0.0075** |
| `gils_am_rvnd_oropt_rev` | -0.451 | 15/0/3 | **0.0075** |
| `gils_am_rvnd_rev_db10` | -0.449 | 16/0/2 | **0.0013** |
| `gils_am_rvnd_extended_oropt` | -0.169 | 9/1/8 | 1.0000 |

Todos os mecanismos novos batem o MDM com significância; o incumbente não. A poda é o
componente dominante (as três `cand*` lideram), mas o or-opt invertido sozinho, sem
poda (`oropt_rev`), já vale −0,451% (p = 0,0075): a vizinhança nova tem valor próprio,
não é só velocidade. K = 12 e K = 20 empatam na prática; ficou K = 12, mais barato e
com a melhor taxa de vitórias (17/0/1). O double-bridge com blocos limitados (`db10`,
H17) melhora a média mas piora a taxa de vitórias, e a 100 s ficou atrás do `cand12`
puro: não adotado.

**Resultado principal — 100 s, N=30 pareado**, `cand12` vs `mdm_gils_rvnd` (negativo =
melhor que o MDM):

| instância | n | mean_rel% | W/T/L | p (sinais) |
|---|---:|---:|---:|---:|
| `lin318` | 318 | **-0.188** | 9/0/1 | **0.021** |
| `pr439` | 439 | **-0.562** | 8/0/2 | 0.109 |
| `att532` | 532 | **-1.196** | 10/0/0 | **0.002** |
| **AGREGADO** | | **-0.649** | **27/0/3** | **0.00001** |

| instância | solver | restarts médios | custo médio | melhor custo | gap BKS |
|---|---|---:|---:|---:|---:|
| `lin318` | `mdm_gils_rvnd` | 168 | 5 586 455.7 | 5 565 187 | 0.464% |
| `lin318` | `gils_am_rvnd_cand12` | 781 | 5 575 913.4 | 5 562 148 | 0.274% |
| `pr439` | `mdm_gils_rvnd` | 92 | 17 912 677.4 | 17 856 623 | 1.267% |
| `pr439` | `gils_am_rvnd_cand12` | 318 | 17 811 886.4 | 17 757 765 | 0.697% |
| `att532` | `mdm_gils_rvnd` | 53 | 5 704 564.1 | 5 687 070 | 2.057% |
| `att532` | `gils_am_rvnd_cand12` | 224 | 5 636 343.4 | 5 623 523 | 0.837% |

**Contra o incumbente anterior** (`cand12` vs `extended-oropt`): −0,457% a 30 s
(N=18, 16/0/2) e −0,190% a 100 s (N=20, 15/0/5; a 100 s só `lin318` e `pr439`, pois
`att532` foi cortado do lote por tempo de máquina).

Todos os tours das vizinhanças novas foram verificados independentemente (permutação
completa começando no depósito, custo recomputado das coordenadas com a mesma
convenção de arredondamento do `Evaluator`) em `lin318`/`pr439`/`att532`.

## Por que funcionou

O ganho vem de visitar muito mais ótimos locais no mesmo orçamento: em `att532` o
`cand12` completa 224 restarts no tempo em que o MDM completa 53 (**4,2×**), e o gap
médio de BKS cai para menos da metade (2,057% → 0,837%). A poda troca profundidade do
ótimo local por número de iterações, e é exatamente essa troca que um orçamento de
tempo fixo premia; como o custo O(n²) por varredura pesa mais quanto maior o `n`, o
ganho cresce monotonicamente com `n`. O or-opt invertido soma uma vizinhança
genuinamente nova sob o objetivo de latência, com valor próprio medido na triagem.

## Limitações

- **A poda poderia ser portada para o MDM.** A comparação é entre os algoritmos como
  estão implementados; parte da vantagem é engenharia de vizinhança, não estratégia de
  busca. Os prefix sums, esses sim, já beneficiam os três binários. O
  [H19](h19-dlb-fast-regime.md) fez esse porte: com a mesma busca local, MDM,
  `gils_rvnd` e `gils_am_rvnd` empatam.
- **Só n > 200.** As sete instâncias menores saturam a 100 s
  ([fixed-time-100s-tsplib](../benchmarks/fixed-time-100s-tsplib.md)); nada aqui se aplica a elas.
- **`--iils 10` não foi tunado** para o novo regime (retunado no H19).
- **`--db-front-bias`** (perturbação enviesada para o início do tour) não foi testado
  aqui; o H19 o testou e ele piora.

## Referências

- Silva, M.M., Subramanian, A., Vidal, T., Ochi, L.S. (2012). A simple and effective
  metaheuristic for the Minimum Latency Problem. *European Journal of Operational
  Research*, 221(3), 513–520.
