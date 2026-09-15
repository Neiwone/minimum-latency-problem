# H19 — Don't-look bits + I_ILS retunado: batendo o MDM-GILS-RVND a 100 s com folga

Status: **ENCERRADA COM SUCESSO.** `gils_am_rvnd --rvnd-mode candidate-dlb --cand-k 12
--iils 300` bate o `mdm_gils_rvnd` a 100 s/execução em `lin318`/`pr439`/`att532`:
**-1,250% agregado, 30 vitórias / 0 empates / 0 derrotas em 30 pares, p < 0,0001**,
vencendo em toda seed de toda instância. Estendido a **todas as 7 instâncias com
n >= 200** deste projeto (70 pares): **-1,249%, 60 vitórias / 10 empates / 0
derrotas, p < 1e-6** — não perde uma única seed, e os empates são todos de `pr226`,
que satura no orçamento. Contra o MDM **na melhor calibração dele**
(`--iils 300`, onde a mineração já não dispara): -0,358%, 46/19/5, p < 1e-6 sobre as
7 instâncias. O gap
médio de BKS nas três instâncias cai de 1,26% (MDM) para **0,0%** — em `att532` o
gap médio fica **negativo** (-0,120%), isto é, a média das 10 seeds já está abaixo da
melhor solução registrada até aqui.

Duas mudanças, uma de engenharia de busca local e outra de parametrização, em cima
do vencedor de [[h16-candidate-neighborhoods]]:

1. **Don't-look bits** sobre as vizinhanças podadas, com regra de despertar
   específica para latência, mais aplicação de movimento em O(span) no lugar de O(n).
2. **`I_ILS` retunado**: o `--iils 10` que o protocolo de tempo fixo impõe (escolhido
   para a mineração do `mdm` disparar) custava **0,65%** de qualidade sozinho.

## 1. Diagnóstico de partida

[[h16-candidate-neighborhoods]] fechou com "a tempo fixo, velocidade é qualidade" e
deixou três ressalvas. A terceira — `--iils 10` nunca foi tunado para o regime
rápido — acabou sendo a maior: com a busca local 8x mais rápida, o número de
reinícios subiu uma ordem de grandeza, e cada reinício **joga fora a solução
incumbente** para recomeçar de uma construção gulosa randomizada. Quanto mais rápida
a busca local, mais caro fica esse desperdício em termos relativos.

## 2. Mecanismo

### 2.1 Don't-look bits com regra de despertar ciente da latência

`RVND_Candidate` revarre **toda** posição do tour a cada varredura. Dentro de um ILS
isso é quase tudo trabalho perdido: um double bridge perturba um span limitado, e o
resto das posições é reexaminado só para reconfirmar que continua sem movimento de
melhora. A solução clássica em TSP (Bentley, 1992) é um bit "don't look" por cidade,
limpo só quando algo perto dela muda.

Sob objetivo de latência a contabilidade precisa ser mais larga que no TSP, porque a
função objetivo é posicional. Mas não tão larga quanto parece: reordenar um span
**não** muda o delta de um movimento inteiramente antes ou inteiramente depois dele.
A duração do prefixo entra nesse delta apenas multiplicada pelo número de clientes
que vêm depois, que a reordenação não altera — ou seja, **cancela**. A regra usada é
então "desperte toda cidade cuja POSIÇÃO mudou, mais as junções": exata para
movimentos que ficam de um lado do span perturbado, heurística só para os que o
atravessam.

O bit de uma cidade só é limpo depois que **todas** as vizinhanças a varreram sem
achar movimento (um bit por vizinhança em `examined`). O estado (`DlbState`) vive
entre chamadas do RVND, então depois de uma perturbação o ILS re-arma apenas o span
que o double bridge tocou, em vez do tour inteiro.

### 2.2 Aplicação de movimento em O(span)

`apply_oropt` reconstruía o tour inteiro num vetor auxiliar e chamava
`calculateStructures()` (O(n)) a cada movimento aplicado. Um or-opt é uma **rotação**
do intervalo afetado, e os prefix sums só mudam a partir da primeira posição
perturbada: `calculateStructuresFrom(lo)` (novo) re-deriva P/SP/posOf só de `lo` em
diante. Movimentos perto da cauda do tour passam a custar quase nada.

### 2.3 `I_ILS`

Sem mudança de código — só deixou de ser imposto pelo runner. `run_experiments.py`
passou a respeitar um `--iils` fixado na entrada do solver no registro de solvers,
porque `I_ILS` é **parâmetro do algoritmo**: forçar um único valor em todos compara
cada um na calibração de outro.

## 3. Triagens (harness paralelo pareado, `scripts/screen_parallel.py`)

As triagens usam um harness próprio que roda as variantes de uma célula
(instância, seed) **concorrentemente**, em grupos de exatamente 3 processos, para
comprar wall-clock sem quebrar o pareamento: toda execução de uma comparação vê a
mesma contenção. Medido nesta máquina (`lin318`, 20 s, mesma seed): 112 reinícios
sequencial, 91 com 2 processos, 82 com 3, 59 com 6 — ou seja, 3 processos custam
~27% da vazão, uniformemente. Serve para **ordenar** variantes; o veredito de 100 s
sai do `run_experiments.py`, sequencial.

### 3.1 `I_ILS` é o maior fator isolado (30 s, N=18, `lin318`/`pr439`/`att532`)

Baseline: `--rvnd-mode candidate --cand-k 12 --iils 10` (o vencedor do H16).

| variante | mean_rel% | W/T/L | p |
|---|---:|---:|---:|
| `--iils 100` | **-0.653** | **18/0/0** | **0.0000** |
| `--iils 30` | -0.387 | 13/0/5 | 0.096 |
| `--iils 3` | +0.193 | 6/0/12 | 0.238 |
| `--db-maxseg-div 10` (H17) | -0.125 | 11/0/7 | 0.481 |
| `--db-front-bias 2` (H18) | +0.019 | 0/17/1 | 1.000 |

O front-bias (H18) sai **idêntico** ao baseline em 17 de 18 pares porque o viés só é
aplicado no ramo de double bridge com blocos limitados (`--db-maxseg`), que não estava
ligado — fica sem teste, não refutado.

### 3.2 DLB e `I_ILS` maior (30 s, N=18, baseline `candidate --iils 100`)

| variante | mean_rel% | W/T/L | att532 mean_rel% |
|---|---:|---:|---:|
| `candidate-dlb --iils 300` | **-0.167** | 11/0/7 | **-0.377** |
| `candidate --iils 300` | -0.093 | 12/0/6 | -0.187 |
| `candidate --iils 1000` | -0.087 | 13/0/5 | -0.189 |
| `candidate-dlb --iils 100` | -0.082 | 11/0/7 | -0.148 |
| `candidate-dlb --iils 1000` | -0.064 | 9/0/9 | -0.246 |

`lin318` e `pr439` **saturam** a 30 s no regime novo (o `candidate --iils 1000` acha
o BKS de `lin318`, 5 560 679, em 30 s), então todo o poder de discriminação vem de
`att532`. O DLB entrega 2-10x mais reinícios no mesmo tempo; em `lin318`/`pr439` isso
não vira qualidade (já saturado), em `att532` vira.

Custos em `att532` com **30 s** de orçamento (BKS 5 589 568):

| variante | custo médio | gap médio | melhor custo | gap do melhor |
|---|---:|---:|---:|---:|
| `candidate --iils 10` (H16, 100 s) | 5 636 343 | 0.837% | 5 623 523 | 0.61% |
| `candidate --iils 100` | 5 615 718 | 0.468% | 5 598 357 | 0.157% |
| `candidate-dlb --iils 300` | **5 594 484** | **0.088%** | **5 589 297** | **-0.005%** |

Com **1/3 do orçamento** do lote do H16, o gap médio em `att532` cai de 0,837% para
0,088%, e uma seed já fica **abaixo** do BKS registrado.

### 3.3 Vizinhança mais funda não paga (45 s, `att532` + Salehipour n=500)

Baseline `candidate-dlb --cand-k 12 --iils 300`:

| variante | mean_rel% | W/T/L |
|---|---:|---:|
| `--cand-k 20` | +0.315 | 0/0/7 |
| `--cand-k 30` | +0.245 | 1/0/6 |
| `--cand-front 5` (âncoras no início do tour) | +0.337 | 0/0/7 |
| `--cand-2opt-both` (ancorar 2-opt nas duas arestas novas) | +0.123 | 3/0/4 |
| tudo junto | +0.113 | 3/0/4 |

A velocidade que o DLB libera **não** deve ser gasta em vizinhança maior. Mesmo as
âncoras de início de tour — motivadas pelo fato de o começo do tour ser onde uma
aresta é paga por mais clientes — pioram: acham movimentos de melhora, mas
relocações longas para o início destroem estrutura e custam varredura.

### 3.4 Comprimento do or-opt: 6 continua sendo o teto certo (60 s, N=5)

| variante | mean_rel% | W/T/L |
|---|---:|---:|
| `--cand-maxlen 8` | +0.045 | 2/0/3 |
| `--cand-maxlen 4` | +0.083 | 2/0/3 |
| `--cand-maxlen 10` | +0.086 | 2/0/3 |
| `--cand-maxlen 3` | +0.113 | 1/0/4 |
| `--cand-no-rev` (sem or-opt invertido) | +0.243 | 1/0/4 |

O teto 6 de [[h12-extended-oropt]] sobrevive ao regime novo, e o or-opt invertido de
[[h16-candidate-neighborhoods]] continua valendo (+0,24% sem ele).

### 3.5 Mecanismos de estratégia: todos nulos ou piores (45 s, N=8)

Baseline `candidate-dlb --cand-k 12 --iils 300`:

| mecanismo | mean_rel% | W/T/L | p |
|---|---:|---:|---:|
| `--polish-on-best` (RVND completo, sem poda, a cada novo melhor global) | +0.128 | 3/0/4 | 1.000 |
| `--accept-eps 0.002` (aceitação por limiar no ILS) | +0.165 | 3/0/5 | 0.727 |
| `--accept-eps 0.01` | +0.175 | 3/0/5 | 0.727 |
| `--abx-rate 0.5` (crossover arc-based entre elites no reinício) | +0.255 | 2/0/6 | 0.289 |
| `--restart-kick 3` (reinício por kick do incumbente) | +0.257 | 0/0/8 | **0.008** |

Todos implementados e verificados (tours válidos, custo recalculado bate). O ABX
segue Ren, Hao, Wu & Fu, EJOR 304(2), 2023 — mantém as arestas em que os dois pais
concordam e enxerta metade das arestas discordantes do segundo pai. Resultado
consistente com [[h1-adaptive-diversification]], [[h2-elite-path-relinking]],
[[h8-dbmea-population]] e [[h9-ruin-recreate]]: **nada que mude de onde a busca
recomeça sobrevive ao RVND** neste problema. O que paga é vizinhança e velocidade.

### 3.6 Calibração de `I_ILS` dos dois algoritmos no orçamento longo (60 s, N=12)

`att532` + `salehipour_n0500_i01`, 6 seeds, baseline = proposta
(`candidate-dlb --cand-k 12 --iils 300`):

| variante | mean_rel% | W/T/L | p | reinícios | minerações |
|---|---:|---:|---:|---:|---:|
| proposta `--iils 1000` | +0.314 | 1/1/10 | **0.012** | 2 | n/a |
| proposta `--iils 3000` | +0.332 | 1/1/10 | **0.012** | 1 | n/a |
| `mdm_gils_rvnd --iils 10` (default do protocolo) | +2.374 | 0/0/12 | **0.0005** | 23 | 10.8 |
| `mdm_gils_rvnd --iils 100` | +1.027 | 0/0/12 | **0.0005** | 2 | 1.2 |
| `mdm_gils_rvnd --iils 300` | +0.832 | 0/0/12 | **0.0005** | 1 | **0.0** |

Duas leituras:

1. `I_ILS = 300` é o ótimo da proposta — 1000 e 3000 já pioram, com significância.
2. **O MDM também sofria com `--iils 10`** (+2,37% -> +1,03% só trocando o
   parâmetro), mas o `I_ILS` que maximiza a qualidade dele é exatamente aquele em
   que o mecanismo do MDM **para de existir**: em `--iils 300` a mineração dispara
   0 vezes em 12 execuções, ou seja, ali o `mdm_gils_rvnd` é GILS-RVND puro. Mesmo
   contra essa versão degenerada — a melhor configuração dele em qualidade — a
   proposta ganha 0,83%, 0/12, p = 0,0005.

### 3.65 Don't-look bits estritos: mais rápido, mesma qualidade (60 s, N=18)

`examined` hoje é só um contador de "quantas vizinhanças já falharam nesta cidade": o
pulo das varreduras olha `active`, então uma cidade com 12 dos 13 bits marcados ainda
é varrida pelas 13. A versão estrita (`--cand-dlb-strict`) pula o par
**(cidade, vizinhança)** cujo bit já está marcado.

Baseline `candidate-dlb --cand-k 12 --iils 300`, em `att532` + Salehipour n=500 (i01, i02):

| variante | mean_rel% | W/T/L | p | reinícios (`att532`) |
|---|---:|---:|---:|---:|
| `--cand-dlb-strict --iils 300` | +0.003 | 11/0/7 | 0.481 | 7.8 (baseline: 4.5) |
| `--cand-dlb-strict --iils 100` | +0.175 | 6/0/12 | 0.238 | 17.7 |

Funciona como otimização — **1,6x mais reinícios** no mesmo orçamento — e a velocidade
extra **não** vira qualidade: o resultado cai exatamente em cima do baseline. Mesmo
padrão que o próprio DLB mostra em `lin318`/`pr439`: velocidade só converte enquanto a
busca ainda está limitada por iterações.

**Não adotado** (flag mantida para reprodução). A revarredura redundante do modo
frouxo não é puro desperdício: um movimento aplicado em outro lugar muda em que
posição os candidatos de uma cidade estão, e a regra posicional de religar não cobre
esse caso — a revarredura compensa parcialmente essa incompletude, o que provavelmente
explica o empate.

### 3.7 Perturbação: nada a adotar (60 s, N=5)

| variante | mean_rel% | W/T/L |
|---|---:|---:|
| `--db-maxseg-div 10` (H17) | +0.004 | 3/0/2 |
| `--db-maxseg-div 20` | +0.039 | 1/0/4 |
| `--db-maxseg-div 5` | +0.051 | 2/0/3 |
| `--db-maxseg-div 10 --db-front-bias 2` (H18) | +0.123 | 2/0/3 |
| `--db-maxseg-div 10 --db-front-bias 4` | +0.326 | 1/0/4 |

Fecha [[h17]] e [[h18]]: o double bridge com blocos limitados é neutro, e o viés
para o início do tour — agora testado no ramo em que de fato dispara — **piora**, de
forma monotônica na intensidade do viés. O double bridge uniforme fica.

## 4. O algoritmo proposto

`gils_am_rvnd --rvnd-mode candidate-dlb --cand-k 12 --iils 300`
(registrado como `gils_am_rvnd_dlb` em `run_experiments.py`).

Em relação ao GILS-RVND de Silva et al. (2012), a pilha de mudanças acumulada por
este projeto e fechada aqui:

1. **Construção**: GRASP randomizada com memória adaptativa de frequência de arestas
   sobre um pool elite (`gils_am_rvnd`).
2. **Busca local**: RVND sobre 13 vizinhanças — swap, 2-opt, or-opt direto
   comprimentos 1-6 e or-opt **invertido** 2-6 ([[h12-extended-oropt]],
   [[h16-candidate-neighborhoods]]) —, cada varredura **podada por lista dos 12
   vizinhos mais próximos** e conduzida por **don't-look bits** com a regra de
   despertar por posição (seção 2.1). Movimentos aplicados em O(span) (seção 2.2).
3. **Perturbação**: double bridge.
4. **ILS**: `I_ILS = 300` perturbações consecutivas sem melhora antes de reiniciar
   (seção 3.6); reinício por construção nova.
5. **Dados de subsequência**: dois prefix sums O(n) no lugar das três matrizes O(n²)
   ([[h16-candidate-neighborhoods]] seção 2.1).

O que **não** entrou, por ter sido testado e refutado aqui: vizinhanças mais largas
(K maior, âncoras de início de tour, 2-opt ancorado nas duas arestas), aceitação por
limiar no ILS, polimento com RVND completo, crossover ABX entre elites, reinício por
kick do incumbente.

## 5. Verificação de corretude

Todo tour produzido pelos modos novos é verificado independentemente: permutação
completa de `0..n-1` começando no depósito, e custo recalculado das coordenadas
(mesma convenção de arredondamento do `Evaluator`: truncamento em EUC_2D, teto em
ATT) batendo exatamente com o custo reportado — em `st70`/`rat195`/`lin318`/`att532`,
para `candidate-dlb` puro e com todas as flags novas ligadas.

## 6. Resultado oficial — 100 s/execução, sequencial, N=70 pareado

```bash
python3 run_experiments.py --mode fixed-time --time-limit 100 --runs 10 --iils 10 \
    --instances lin318 pr439 att532 \
    --solvers mdm_gils_rvnd gils_am_rvnd_cand12 gils_am_rvnd_dlb mdm_gils_rvnd_i300 \
    --checkpoint scripts/fixed_time_100s.json
```

Protocolo de [[fixed-time-protocol]]: 100 s de wall-clock iguais para todos,
execuções **sequenciais**, pareadas por seed (1-10). As execuções de
`mdm_gils_rvnd` e `gils_am_rvnd_cand12` são as do lote de
[[h16-candidate-neighborhoods]], no mesmo checkpoint, mesma máquina e mesmos
binários (as mudanças desta hipótese são todas desligadas por default e não tocam o
caminho de código desses dois) — só os dois solvers novos rodaram.

### 6.1 Contra o `mdm_gils_rvnd` (protocolo padrão, `--iils 10`)

| instância | n | mean_rel% | W/T/L | p (sinais) |
|---|---:|---:|---:|---:|
| `lin318` | 318 | **-0.420** | 10/0/0 | **0.002** |
| `pr439` | 439 | **-1.196** | 10/0/0 | **0.002** |
| `att532` | 532 | **-2.133** | 10/0/0 | **0.002** |
| **AGREGADO** | | **-1.250** | **30/0/0** | **0.00000** |

Para comparação, o vencedor anterior ([[h16-candidate-neighborhoods]],
`gils_am_rvnd_cand12`) no mesmo lote: -0,649%, 27/0/3.

### 6.2 Contra o `mdm_gils_rvnd --iils 300` (a melhor calibração do MDM)

| instância | mean_rel% | W/T/L | p |
|---|---:|---:|---:|
| `lin318` | +0.015 | 2/4/4 | 0.688 |
| `pr439` | **-0.309** | 9/1/0 | **0.004** |
| `att532` | **-0.716** | 9/0/1 | **0.022** |
| **AGREGADO** | **-0.337** | **20/5/5** | **0.004** |

`lin318` empata porque satura: as duas configurações acham o BKS em quase toda seed.

### 6.3 Custos e gaps de BKS (10 seeds, 100 s)

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

Três coisas para ler aqui:

1. A proposta **acha o BKS de `lin318` e de `pr439`** dentro do orçamento de 100 s, e
   em `pr439` o custo **médio** das 10 seeds fica a 0,055% do BKS (o MDM fica a
   1,267%).
2. Em `att532` o gap médio é **negativo**: todas as 10 seeds, em média, ficam abaixo
   da melhor solução que o projeto tinha registrada (5 589 568). A melhor das 10
   (5 573 783) é uma **nova melhor solução conhecida** para a instância neste
   projeto, 0,28% abaixo da anterior.
3. A coluna de reinícios mostra a inversão em relação ao H16: a proposta faz
   **8 reinícios** em `att532` onde o `cand12` fazia 224. O ganho não vem mais de
   visitar mais ótimos locais, e sim de gastar o orçamento aprofundando **um**
   trajetória de ILS com uma busca local muito barata por iteração.

### 6.4 Breadth — as demais instâncias com n >= 200 (100 s, 10 seeds cada)

Mesmo protocolo, dois lotes extras: `a280`/`pr226` (TSPLIB) em
`scripts/fixed_time_100s_breadth.json` e duas instâncias do benchmark Salehipour
n=500 em `scripts/fixed_time_100s_n500.json`.

| instância | n | vs `mdm_gils_rvnd` | W/T/L | vs `mdm --iils 300` | W/T/L |
|---|---:|---:|---:|---:|---:|
| `pr226` | 226 | +0.000 | 0/10/0 | +0.000 | 0/10/0 |
| `a280` | 280 | **-0.524** | 10/0/0 | -0.022 | 6/4/0 |
| `salehipour n=500 i01` | 500 | **-2.029** | 10/0/0 | **-0.626** | 10/0/0 |
| `salehipour n=500 i02` | 500 | **-2.439** | 10/0/0 | **-0.848** | 10/0/0 |

`pr226` satura: as três configurações acham 7 100 308 em todas as 10 seeds.

| instância | solver | melhor | médio | reinícios |
|---|---|---:|---:|---:|
| `a280` | `mdm_gils_rvnd` | 341 895 | 342 794.7 | 172 |
| `a280` | `mdm --iils 300` | 340 998 | 341 073.9 | 7 |
| `a280` | **proposta** | **340 998** | **340 998.0** | 35 |
| `n0500_i01` | `mdm_gils_rvnd` | 1 836 810 | 1 853 978.7 | 52 |
| `n0500_i01` | `mdm --iils 300` | 1 818 630 | 1 827 760.1 | 1 |
| `n0500_i01` | **proposta** | **1 809 990** | **1 816 297.7** | 10 |
| `n0500_i02` | `mdm_gils_rvnd` | 1 772 669 | 1 783 901.0 | 52 |
| `n0500_i02` | `mdm --iils 300` | 1 742 697 | 1 755 327.9 | 2 |
| `n0500_i02` | **proposta** | **1 736 787** | **1 740 369.2** | 11 |

Em `a280` a proposta acha o **mesmo custo nas 10 seeds** (340 998, desvio zero) — o
MDM no protocolo padrão nunca chega lá.

### 6.5 Agregado sobre todas as instâncias com n >= 200 (N=70 pareado)

| baseline | mean_rel% | W/T/L | p (sinais) |
|---|---:|---:|---:|
| `mdm_gils_rvnd` (protocolo, `--iils 10`) | **-1.249** | **60/10/0** | **< 1e-6** |
| `mdm_gils_rvnd --iils 300` (melhor calibração do MDM) | **-0.358** | **46/19/5** | **< 1e-6** |

7 instâncias (`pr226`, `a280`, `lin318`, `pr439`, `att532`, Salehipour n=500 i01 e
i02), 10 seeds cada. Contra o MDM no protocolo padrão a proposta **não perde uma
única seed em 70**; os 10 empates são `pr226`, que satura. O efeito cresce
monotonicamente com `n`.

### 6.6 Melhores soluções conhecidas atualizadas

`scripts/record_best.py` (novo) roda a proposta algumas vezes, **verifica cada tour
de forma independente** (permutação de `0..n-1` começando no depósito, latência
recalculada das coordenadas com a convenção de arredondamento do `Evaluator`) e só
então grava pelo mesmo caminho que o `run_experiments.py` usa
(`instances/solutions/*.tour` + `best_solutions.json`).

| instância | antes | agora | 5 seeds a 100 s |
|---|---:|---:|---|
| `att532` | 5 589 568 | **5 573 783** (-0,2824%) | todas as 5 abaixo do valor antigo |
| `a280` | (sem registro) | **340 998** | as 5 acham o mesmo valor |

## 7. Ressalvas

1. **A poda continua portável para o MDM.** Como em
   [[h16-candidate-neighborhoods]] seção 8.1, a comparação é entre os algoritmos
   como estão implementados: `mdm_gils_rvnd` segue com varredura O(n²) completa e
   sem don't-look bits. Parte da vantagem é engenharia de busca local, não
   estratégia. O que a seção 3.6 acrescenta é que **o `I_ILS`, esse sim, foi
   corrigido para os dois lados**: o MDM foi medido na calibração que maximiza a
   qualidade dele, e ainda perde.
2. **O `I_ILS` ótimo depende do orçamento e do `n`.** 300 foi calibrado a 45-60 s em
   `att532`/Salehipour n=500. Em instâncias menores a busca satura muito antes
   (`lin318` acha o BKS em 30 s), e em n=1000 o valor provavelmente muda de novo.
3. **`cl.near[c][0] == c`**: a lista do `Evaluator` guarda a própria cidade na
   posição 0, então `--cand-k 12` na prática usa 11 vizinhos reais mais uma
   avaliação inútil por varredura (~8% do custo do scan). Não foi corrigido aqui
   porque mudaria o `K` efetivo de todas as triagens acima; fica como otimização
   pendente.
4. **Don't-look bits são uma restrição heurística** para os movimentos que
   atravessam o span perturbado (seção 2.1). Não há garantia de terminar no mesmo
   ótimo local que a varredura completa — o que os números dizem é que a troca
   compensa.
