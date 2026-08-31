# GILS-RVND vs GILS-AM-RVND (extended-oropt) vs MDM-GILS-RVND — comparação nas 10 instâncias TSPLIB

Status: **Comparação nova, protocolo replicado do paper de referência do MDM-GILS-RVND**
(Santana, Plastino & Rosseti, ["Improving a State-of-the-Art Heuristic for the Minimum
Latency Problem with Data Mining"](https://arxiv.org/abs/1908.10705), arXiv:1908.10705).
Resultado consistente com [[h12-extended-oropt]] (positivo, cresce com `n`) e
[[h13-mdm-gils-rvnd]] (nulo nesta faixa de `n`).

## 1. Objetivo

Comparar, nas mesmas 10 instâncias TSPLIB que este projeto já usa por padrão
(`st70`, `rat99`, `kroD100`, `lin105`, `pr107`, `rat195`, `pr226`, `lin318`, `pr439`,
`att532` — a variante *Hamiltonian Path*, 70 a 532 clientes), três algoritmos:

- `gils_rvnd` — baseline (Silva et al., 2012).
- `gils_am_rvnd --rvnd-mode extended-oropt` — melhor achado deste projeto até agora
  (memória adaptativa na construção + or-opt estendido a segmentos 4-6, ver
  [[h12-extended-oropt]]).
- `mdm_gils_rvnd` — reimplementação deste projeto do MDM-GILS-RVND (mineração real de
  itemsets maximais via FPMax*/`mlxtend`, ver [[h13-mdm-gils-rvnd]]).

## 2. Ressalva importante sobre a fonte dos números do MDM-GILS-RVND

**O paper original não publica uma tabela por instância para este conjunto exato de 10
TSPLIB.** Na Seção 5.2, ele descreve esse "10-instances set... introduced in Salehipour
et al. (2011)" e só reporta o **agregado**, porque os dois heurísticos tiveram
desempenho muito parecido:

> "In experiments for the 10-instances set, both heuristics reached the same best
> solutions, where nine of them are, indeed, BKSs. For average solutions, these
> heuristics presented very similar results, reflected by average BKS gap values of
> 0.08% and 0.09%, respectively, for MDM-GILS-RVND and GILS-RVND. No difference between
> the heuristics' results was statistically significant. In contrast to solution quality
> results, a computational time reduction of 14.47% was obtained by MDM-GILS-RVND."

| Fonte | Gap médio de BKS (Avg. Solution) | Significância estatística | Tempo (MDM vs GILS-RVND) |
|---|---:|---|---:|
| **Paper (Seção 5.2, agregado, 10 instâncias, 10 seeds)** | MDM-GILS-RVND: 0,08% / GILS-RVND: 0,09% | nenhuma diferença significativa | MDM-GILS-RVND **-14,47%** |

Não existe, portanto, uma tabela "oficial" por instância para citar diretamente. A
tabela da Seção 3 abaixo é a nossa própria execução do `mdm_gils_rvnd` (implementação
já existente neste repositório, ver [[h13-mdm-gils-rvnd]]) rodada com os
**hiperparâmetros exatos do paper**, não números da literatura.

## 3. Protocolo

Replicado exatamente como descrito no paper (Seção 5, "Computational Results"):

- `I_max = 10`, `I_ILS = min(100, n)`, `R = {0.00, 0.01, ..., 0.25}` (já é o default do
  código deste projeto para os 3 binários, nenhuma mudança necessária).
- `mdm_gils_rvnd`: `sup_min = 0.70`, elite pool `d = 10`, `max_patterns = 5` (defaults
  do binário, iguais ao paper).
- 10 execuções por instância/algoritmo, seeds 1 a 10 (mesma seed usada nos 3
  algoritmos por instância — comparação pareada).
- `gils_am_rvnd_extended_oropt` roda com os mesmos `--imax`/`--iils` acima, mais
  `--rvnd-mode extended-oropt`.

## 4. Resultados por instância

Estilo `run_experiments.py --mode compare-best`: BKS, Melhor Solução, Solução Média,
Gap médio de BKS, Tempo médio. Para `gils_am_rvnd_extended_oropt` e `mdm_gils_rvnd`,
adicionalmente W/T/L (vitórias/empates/derrotas pareadas por seed contra o baseline
`gils_rvnd`) e p-valor do teste de sinal exato.

| Instance | n | BKS | GILS-RVND Best | GILS-RVND Avg | GILS-RVND Gap% | GILS-RVND Time(s) | AM+extended-oropt Best | AM+extended-oropt Avg | AM+extended-oropt Gap% | AM+extended-oropt Time(s) | AM+extended-oropt W/T/L | AM+extended-oropt p | MDM-GILS-RVND Best | MDM-GILS-RVND Avg | MDM-GILS-RVND Gap% | MDM-GILS-RVND Time(s) | MDM-GILS-RVND W/T/L | MDM-GILS-RVND p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| st70 | 70 | 19,215 | 19,215 | 19,215.0 | 0.000% | 0.50 | 19,215 | 19,215.0 | 0.000% | 0.56 | 0/10/0 | 1.000 | 19,215 | 19,215.0 | 0.000% | 1.82 | 0/10/0 | 1.000 |
| rat99 | 99 | 54,984 | 54,984 | 54,984.0 | 0.000% | 3.35 | 54,984 | 54,984.0 | 0.000% | 2.87 | 0/10/0 | 1.000 | 54,984 | 54,984.0 | 0.000% | 5.36 | 0/10/0 | 1.000 |
| kroD100 | 100 | 949,594 | 949,594 | 949,594.0 | 0.000% | 2.78 | 949,594 | 949,594.0 | 0.000% | 2.53 | 0/10/0 | 1.000 | 949,594 | 949,594.0 | 0.000% | 3.83 | 0/10/0 | 1.000 |
| lin105 | 105 | 585,823 | 585,823 | 585,823.0 | 0.000% | 2.42 | 585,823 | 585,823.0 | 0.000% | 2.41 | 0/10/0 | 1.000 | 585,823 | 585,823.0 | 0.000% | 3.09 | 0/10/0 | 1.000 |
| pr107 | 107 | 1,980,767 | 1,980,767 | 1,980,771.6 | 0.000% | 3.36 | 1,980,767 | 1,980,771.6 | 0.000% | 3.04 | 1/8/1 | 1.000 | 1,980,767 | 1,980,767.0 | 0.000% | 4.44 | 1/9/0 | 1.000 |
| rat195 | 195 | 210,191 | 210,191 | 210,435.9 | 0.117% | 30.46 | 210,191 | 210,279.6 | 0.042% | 23.09 | 6/1/3 | 0.508 | 210,191 | 210,366.5 | 0.083% | 32.39 | 3/3/4 | 1.000 |
| pr226 | 226 | 7,100,308 | 7,100,308 | 7,100,308.0 | 0.000% | 32.36 | 7,100,308 | 7,100,308.0 | 0.000% | 25.22 | 0/10/0 | 1.000 | 7,100,308 | 7,100,308.0 | 0.000% | 32.69 | 0/10/0 | 1.000 |
| lin318 | 318 | 5,560,679 | 5,560,679 | 5,567,300.8 | 0.119% | 109.50 | 5,560,679 | 5,563,591.9 | 0.052% | 102.88 | 5/2/3 | 0.727 | 5,560,679 | 5,570,040.2 | 0.168% | 112.85 | 1/4/5 | 0.219 |
| pr439 | 439 | 17,688,561 | 17,712,833 | 17,756,929.0 | 0.387% | 289.00 | 17,703,277 | 17,732,401.4 | 0.248% | 303.88 | 7/0/3 | 0.344 | 17,712,833 | 17,760,000.4 | 0.404% | 301.67 | 3/4/3 | 1.000 |
| att532 | 532 | 5,589,568 | 5,596,981 | 5,613,479.8 | 0.428% | 701.88 | 5,585,316 | 5,598,053.2 | 0.152% | 707.39 | 8/0/2 | 0.109 | 5,584,926 | 5,610,285.1 | 0.371% | 691.86 | 4/2/4 | 1.000 |

*(BKS = melhor custo já registrado neste projeto em `instances/solutions/best_solutions.json`
para a variante Hamiltonian Path; Gap% é sobre a Solução Média.)*

## 5. Agregados pareados (janela de `n`, teste de sinal exato)

| Subconjunto | GILS-AM-RVND+extended-oropt W/T/L | GILS-AM-RVND+extended-oropt p | MDM-GILS-RVND W/T/L | MDM-GILS-RVND p |
|---|---:|---:|---:|---:|
| Todas as 10 instâncias (N=100 pares) | 27/61/12 | **0,024** | 12/72/16 | 0,572 |
| n≥195 (`rat195`...`att532`, N=60) | 26/13/11 | **0,020** | 11/23/16 | 0,442 |
| n≥318 (`lin318`...`att532`, N=30) | 20/2/8 | **0,036** | 8/10/12 | 0,503 |
| n≥439 (`pr439`, `att532`, N=20) | 15/0/5 | **0,041** | 7/6/7 | 1,000 |

## 6. Leitura

- **`gils_am_rvnd_extended_oropt` bate o baseline com significância estatística
  agregada em todas as janelas testadas** (p entre 0,020 e 0,041), e o efeito de
  qualidade fica mais concentrado — não necessariamente mais forte em `%` — nas
  instâncias maiores (`pr439`/`att532`: gap médio de BKS cai de 0,39%/0,43%
  no baseline para 0,25%/0,15%). É a 4ª confirmação independente do achado de
  [[h12-extended-oropt]] (depois de `rand1000`, `rand2000`, e o benchmark oficial de
  Salehipour), agora também nas 10 TSPLIB "clássicas" do paper-base. Nenhuma instância
  individual isolada chega a p<0,05 com N=10 — é o mesmo padrão já visto antes: só o
  agregado tem poder estatístico nessa escala de amostra.
- **`mdm_gils_rvnd` continua nulo nesta faixa de `n`** (p≥0,44 em todas as janelas,
  incluindo 0/0/1,000 no subconjunto mais restrito) — consistente com
  [[h13-mdm-gils-rvnd]] e com o próprio paper, que já reporta efeito fraco em
  instâncias "médias" antes de crescer forte em `n≥1000` (fora do alcance deste teste,
  que para em `att532`/n=532).
- **Tempo**: diferente do -14,47% relatado no paper para este mesmo conjunto de 10
  instâncias, nossa reimplementação do `mdm_gils_rvnd` **não é mais rápida** que o
  baseline aqui (fica de +1% a +260% mais lenta, pior em instâncias pequenas, quase
  neutra nas maiores) — plausivelmente porque a mineração de padrões nesta
  implementação roda como subprocesso Python (`scripts/fpmax_mine.py` via `mlxtend`)
  em vez de código nativo integrado como no paper original. `gils_am_rvnd_extended_oropt`,
  por outro lado, fica no mesmo patamar de tempo do baseline ou mais rápido até
  `lin318` (a vantagem de velocidade da memória adaptativa registrada em
  [[mlp-research-status]] compensa o custo do or-opt estendido), ficando
  ligeiramente mais lento só em `pr439`/`att532` (+5,2%/+0,8%).

## 7. Reprodução

```bash
make gils_rvnd gils_am_rvnd mdm_gils_rvnd
# por instância/algoritmo, 10 seeds (1..10), --iils min(100, n):
./bin/gils_rvnd instances/<inst>.tsp --iils <min(100,n)> --seed <1..10>
./bin/gils_am_rvnd instances/<inst>.tsp --iils <min(100,n)> --seed <1..10> --rvnd-mode extended-oropt
./bin/mdm_gils_rvnd instances/<inst>.tsp --iils <min(100,n)> --seed <1..10>
```
