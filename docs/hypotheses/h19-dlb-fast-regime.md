# H19 — Don't-look bits + I_ILS retunado: batendo o MDM-GILS-RVND a 100 s com folga

**Veredito: confirmada, com uma ressalva decisiva.** `gils_am_rvnd --rvnd-mode
candidate-dlb --cand-k 12 --iils 300` bate o `mdm_gils_rvnd` a 100 s/execução em
`lin318`/`pr439`/`att532`: -1,250% agregado, 30/0/0 em 30 pares, p < 0,0001. Nas 7
instâncias com n >= 200 (70 pares): -1,249%, 60/10/0, p < 1e-6 (os empates são todos
de `pr226`, que satura). Contra o MDM na melhor calibração dele (`--iils 300`, onde a
mineração já não dispara): -0,358%, 46/19/5, p < 1e-6. O gap médio de BKS nas três
instâncias cai de 1,26% (MDM) para 0,0%; em `att532` fica negativo (-0,120%). Mas o
ganho é **da busca local, não da estratégia**: portada a mesma busca local para o
`mdm_gils_rvnd` e para o `gils_rvnd` puro, os três empatam (N=30 por par, todo
p > 0,5). Adotado como algoritmo proposto (`gils_am_rvnd_dlb`).

## Hipótese

[H16](h16-candidate-neighborhoods.md) fechou com "a tempo fixo, velocidade é
qualidade". Com a busca local 8x mais rápida, o `--iils 10` imposto pelo protocolo de
tempo fixo (escolhido para a mineração do `mdm` disparar) faz os reinícios subirem uma
ordem de grandeza, e cada reinício joga fora a incumbente. Tornar a busca local ainda
mais barata e retunar `I_ILS` deveria converter essa velocidade em qualidade.

## O que foi testado

Duas mudanças de código e uma de parametrização sobre o vencedor do H16, em
[`src/neighborhoods_cand.cpp`](../../src/neighborhoods_cand.cpp) e
[`src/solution.cpp`](../../src/solution.cpp):

1. **Don't-look bits** (`--rvnd-mode candidate-dlb`) sobre as vizinhanças podadas. O
   RVND podado revarria toda posição do tour a cada varredura; dentro do ILS isso é
   quase todo trabalho perdido, porque o double bridge perturba um span limitado. A
   técnica clássica do TSP (Bentley, 1992) põe um bit por cidade, limpo só quando algo
   perto dela muda. Sob latência a regra precisa ser mais larga, mas não tanto quanto
   parece: reordenar um span não muda o delta de um movimento inteiramente antes ou
   inteiramente depois dele, porque a duração do prefixo entra no delta multiplicada
   pelo número de clientes posteriores, que a reordenação não altera — e cancela. A
   regra é "desperte toda cidade cuja **posição** mudou, mais as junções": exata para
   movimentos de um lado do span, heurística para os que o atravessam. O bit só é
   limpo depois que todas as vizinhanças varreram a cidade sem achar movimento, e o
   estado persiste entre chamadas do RVND, de modo que após uma perturbação só o span
   tocado pelo double bridge é re-armado.
2. **Aplicação de movimento em O(span)**: um or-opt é uma rotação do intervalo
   afetado, e os prefix sums só mudam a partir da primeira posição perturbada; as
   estruturas passam a ser re-derivadas só dali em diante, em vez de O(n) por
   movimento.
3. **`I_ILS` retunado** (`--iils 300`): sem mudança de código; o runner passou a
   respeitar um `--iils` fixado por solver, porque `I_ILS` é parâmetro do algoritmo e
   forçar um único valor compara cada um na calibração de outro.

As triagens rodam as variantes de cada (instância, seed) em 3 processos concorrentes,
só para ordená-las; o veredito sai de execuções sequenciais no protocolo de
[tempo fixo](../benchmarks/fixed-time-protocol.md), 100 s, pareadas por seed (1-10).

## Resultados

**Triagens a 30 s** (N=18, `lin318`/`pr439`/`att532`). `I_ILS` é o maior fator
isolado: sobre `--rvnd-mode candidate --cand-k 12 --iils 10`, `--iils 100` dá -0.653,
18/0/0, p 0.0000 (`--iils 30` -0.387, p 0.096; `--iils 3` +0.193). Sobre
`candidate --iils 100`, o `candidate-dlb --iils 300` foi o melhor (-0.167, 11/0/7;
-0.377 em `att532`). `lin318` e `pr439` já saturam a 30 s, então a discriminação vem
de `att532`, onde o gap médio cai para 0.088% com 1/3 do orçamento do lote do H16
(0.837% a 100 s). O DLB entrega 2-10x mais reinícios no mesmo tempo.

**Calibração de `I_ILS` dos dois algoritmos** (60 s, N=12, `att532` +
`salehipour_n0500_i01`, baseline = proposta com `--iils 300`):

| variante | mean_rel% | W/T/L | p | reinícios | minerações |
|---|---:|---:|---:|---:|---:|
| proposta `--iils 1000` | +0.314 | 1/1/10 | **0.012** | 2 | n/a |
| proposta `--iils 3000` | +0.332 | 1/1/10 | **0.012** | 1 | n/a |
| `mdm_gils_rvnd --iils 10` (default do protocolo) | +2.374 | 0/0/12 | **0.0005** | 23 | 10.8 |
| `mdm_gils_rvnd --iils 100` | +1.027 | 0/0/12 | **0.0005** | 2 | 1.2 |
| `mdm_gils_rvnd --iils 300` | +0.832 | 0/0/12 | **0.0005** | 1 | **0.0** |

`I_ILS = 300` é o ótimo da proposta. O MDM também sofria com `--iils 10`, mas o
`I_ILS` que maximiza sua qualidade é exatamente aquele em que a mineração dispara 0
vezes em 12 execuções — ali ele é GILS-RVND puro.

**Oficial, 100 s, contra `mdm_gils_rvnd` no protocolo padrão (`--iils 10`):**

| instância | n | mean_rel% | W/T/L | p (sinais) |
|---|---:|---:|---:|---:|
| `lin318` | 318 | **-0.420** | 10/0/0 | **0.002** |
| `pr439` | 439 | **-1.196** | 10/0/0 | **0.002** |
| `att532` | 532 | **-2.133** | 10/0/0 | **0.002** |
| **AGREGADO** | | **-1.250** | **30/0/0** | **0.00000** |

O vencedor anterior (H16, `gils_am_rvnd_cand12`) fazia -0,649%, 27/0/3 no mesmo lote.
Contra `mdm_gils_rvnd --iils 300`: `lin318` +0.015 (2/4/4, p 0.688, satura),
`pr439` -0.309 (9/1/0, p 0.004), `att532` -0.716 (9/0/1, p 0.022), agregado -0.337
(20/5/5, p 0.004).

**Custos e gaps de BKS** (10 seeds, 100 s):

| instância | solver | melhor | médio | gap médio | gap do melhor | reinícios |
|---|---|---:|---:|---:|---:|---:|
| `lin318` | `mdm_gils_rvnd` | 5 565 187 | 5 586 455.7 | 0.464% | 0.081% | 168 |
| `lin318` | `gils_am_rvnd_cand12` (H16) | 5 562 148 | 5 575 913.4 | 0.274% | 0.026% | 781 |
| `lin318` | `mdm_gils_rvnd --iils 300` | 5 560 679 | 5 562 166.9 | 0.027% | 0.000% | 7 |
| `lin318` | **proposta** | **5 560 679** | **5 562 974.9** | **0.041%** | **0.000%** | 27 |
| `pr439` | `mdm_gils_rvnd` | 17 856 623 | 17 912 677.4 | 1.267% | 0.950% | 92 |
| `pr439` | `gils_am_rvnd_cand12` (H16) | 17 757 765 | 17 811 886.4 | 0.697% | 0.391% | 318 |
| `pr439` | `mdm_gils_rvnd --iils 300` | 17 688 561 | 17 753 299.6 | 0.366% | 0.000% | 3 |
| `pr439` | **proposta** | **17 688 561** | **17 698 372.9** | **0.055%** | **0.000%** | 15 |
| `att532` | `mdm_gils_rvnd` | 5 687 070 | 5 704 564.1 | 2.057% | 1.744% | 53 |
| `att532` | `gils_am_rvnd_cand12` (H16) | 5 623 523 | 5 636 343.4 | 0.837% | 0.607% | 224 |
| `att532` | `mdm_gils_rvnd --iils 300` | 5 586 045 | 5 623 229.5 | 0.602% | -0.063% | 1 |
| `att532` | **proposta** | **5 573 783** | **5 582 883.0** | **-0.120%** | **-0.282%** | 8 |

A proposta acha o BKS de `lin318` e `pr439` em 100 s; em `att532` a média das 10
seeds fica abaixo do BKS anterior (5 589 568), e a melhor (5 573 783, -0,2824%)
virou a nova melhor solução registrada (também registrado `a280`: 340 998). A coluna
de reinícios mostra a inversão em relação ao H16: 8 reinícios em `att532` contra 224.

**Demais instâncias com n >= 200** (100 s, 10 seeds; vs `mdm_gils_rvnd` e vs
`mdm --iils 300`): `pr226` +0.000 (0/10/0 nos dois, satura em 7 100 308), `a280`
-0.524 (10/0/0) e -0.022 (6/4/0, 340 998 nas 10 seeds), Salehipour n=500 i01 -2.029 e
-0.626, i02 -2.439 e -0.848 (todos 10/0/0). Agregado das 7 instâncias (N=70): -1.249,
60/10/0, p < 1e-6 contra o protocolo padrão; -0.358, 46/19/5, p < 1e-6 contra
`--iils 300`. O efeito cresce monotonicamente com `n`.

**Controle de justiça: a mesma busca local nos três algoritmos** (100 s, N=30 por
par, 90 execuções refeitas do zero). `candidate-dlb --cand-k 12`, `I_ILS = 300` foi
portado para os outros dois binários; o que resta entre eles é só o mecanismo de
memória — nenhum (`gils_rvnd_dlb`), mineração FPMax* (`mdm_gils_rvnd_dlb`) ou
frequência de arestas do elite (`gils_am_rvnd_dlb`):

| par | mean_rel% | W/T/L | p (sinais) |
|---|---:|---:|---:|
| memória adaptativa vs **sem memória** | -0.017 | 14/6/10 | 0.54 |
| mineração de padrões vs **sem memória** | +0.003 | 10/13/7 | 0.63 |
| memória adaptativa vs mineração de padrões | -0.020 | 10/9/11 | 1.00 |

Nenhuma instância isolada é significativa; os três acham o BKS de `lin318` e `pr439`
e terminam abaixo do valor antigo de `att532`.

**Triagens sem adoção** (todas sobre `candidate-dlb --cand-k 12 --iils 300`):
vizinhança mais funda piora (`--cand-k 20` +0.315, `--cand-k 30` +0.245,
`--cand-front 5` +0.337, `--cand-2opt-both` +0.123); o teto 6 do or-opt de
[H12](h12-extended-oropt.md) se mantém (`--cand-maxlen` 3/4/8/10 pioram de +0.045 a
+0.113) e tirar o or-opt invertido custa +0.243 (`--cand-no-rev`); mecanismos de
estratégia pioram (`--polish-on-best` +0.128, `--accept-eps 0.002`/`0.01`
+0.165/+0.175, crossover ABX `--abx-rate 0.5` +0.255, `--restart-kick 3` +0.257 com
0/0/8, p 0.008); a perturbação fica como está (`--db-maxseg-div` 5/10/20 neutro, e o
viés de início do tour, testado no ramo em que dispara, piora de forma monotônica:
`--db-front-bias 2` +0.123, `4` +0.326). O DLB estrito (`--cand-dlb-strict`, pula o
par cidade-vizinhança já marcado) dá 1,6x mais reinícios mas empata (+0.003, 11/0/7,
p 0.481); não adotado.

## Por que funcionou

A vantagem é inteiramente da busca local e da calibração de `I_ILS`, não da estratégia
de memória. Com a busca local barata, o ganho não vem mais de visitar mais ótimos
locais (o H16 reiniciava centenas de vezes), e sim de gastar o orçamento aprofundando
uma única trajetória de ILS: com `--iils 10` o algoritmo descartava incumbentes boas
cedo demais, e esse desperdício cresce justamente quando cada iteração fica barata.

O controle de justiça dá o resultado mais forte: sob uma busca local suficientemente
rápida, os dois mecanismos de memória publicados para o MLP — mineração de padrões
(MDM-GILS-RVND) e memória adaptativa por frequência de arestas — são indistinguíveis de
não ter mecanismo nenhum. É a conclusão que [H1](h1-adaptive-diversification.md),
[H2](h2-elite-path-relinking.md), [H8](h8-dbmea-population.md) e
[H9](h9-ruin-recreate.md) desenhavam por dentro do projeto, e que as triagens
repetem: nada que mude de onde a busca recomeça sobrevive ao RVND; o que paga é
vizinhança e velocidade. A velocidade extra também não deve ser gasta em vizinhança
maior: âncoras de início de tour acham movimentos, mas relocações longas destroem
estrutura e custam varredura. E velocidade só converte enquanto a busca é limitada por
iterações (DLB estrito, `lin318`/`pr439` saturados). Com a busca local nova, o MDM em
`I_ILS = 300` completa 25 reinícios em `lin318` e a mineração volta a disparar — e
mesmo assim não muda o resultado.

## Limitações

- O resultado oficial compara **implementações**; o controle de justiça, **estratégias**.
  A afirmação defensável é "a busca local e a calibração explicam o ganho", não "a
  estratégia é melhor".
- `I_ILS = 300` foi calibrado a 45-60 s em `att532`/Salehipour n=500; em instâncias
  menores a busca satura antes, e em n=1000 o valor provavelmente muda.
- A lista do `Evaluator` guarda a própria cidade na posição 0 (`cl.near[c][0] == c`),
  então `--cand-k 12` usa 11 vizinhos reais (~8% do custo do scan desperdiçado). Não
  corrigido, para não mudar o `K` efetivo das triagens.
- Os don't-look bits são heurísticos para movimentos que atravessam o span perturbado;
  não há garantia de terminar no mesmo ótimo local da varredura completa. A revarredura
  do modo frouxo compensa em parte, porque um movimento em outro lugar muda a posição
  dos candidatos de uma cidade e a regra posicional não cobre esse caso.
- Os pares com `mdm_gils_rvnd` e `gils_am_rvnd_cand12` do lote oficial foram
  reaproveitados do lote do H16 (mesmo checkpoint, máquina e binários; as mudanças
  deste H são desligadas por default).

## Referências

- Bentley, J.L. (1992). Fast algorithms for geometric traveling salesman problems.
  *ORSA Journal on Computing*, 4(4), 387–411.
- Ren, Hao, Wu & Fu (2023). *European Journal of Operational Research*, 304(2)
  (origem do crossover ABX).
- Silva, M.M., Subramanian, A., Vidal, T., Ochi, L.S. (2012). *A simple and effective
  metaheuristic for the Minimum Latency Problem*. European Journal of Operational
  Research, 221, 513–520. DOI: 10.1016/j.ejor.2012.03.044
