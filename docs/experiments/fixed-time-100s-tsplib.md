# Comparação com tempo fixo (100 s/execução) — GILS-RVND vs AM+extended-oropt vs MDM-GILS-RVND

Status: **lote completo, 300 execuções (10 instâncias x 3 algoritmos x 10 seeds), nenhuma falha.**
Protocolo de [[fixed-time-protocol]]; mesma comparação de "running time as stopping criterion"
do paper do MDM-GILS-RVND (arXiv:1908.10705, Seção 5.3.3). Complementa
[[mdm-vs-am-extended-tsplib-comparison]], que compara os mesmos três algoritmos a
**iterações fixas** nas mesmas 10 instâncias.

## 1. Protocolo

```bash
python3 run_experiments.py --mode fixed-time --time-limit 100 --runs 10 \
    --solvers gils_rvnd gils_am_rvnd_extended_oropt mdm_gils_rvnd
```

- **Orçamento**: 100 s de wall-clock por execução, idêntico para os três algoritmos
  (`--max-time 100`). `I_max` fica efetivamente ilimitado — o tempo é a única
  restrição de parada.
- **Execuções sequenciais** (uma por vez): comparação de tempo não sobrevive a
  contenção de CPU.
- **Pareado por seed**: seeds 1..10, as mesmas para os três algoritmos em cada
  instância. Baseline = `gils_rvnd`.
- 10 instâncias TSPLIB na variante *Hamiltonian Path* (n = 70..532).
- Dados brutos: `scripts/fixed_time_100s_prespeedup.json` (300 execuções). O nome
  carrega o `prespeedup` porque estes números são de binários anteriores a
  [[h16-candidate-neighborhoods]] seção 2.1 (prefix sums), que acelerou os tres
  binarios em 2,4-2,9x. Eles nao sao comparaveis com lotes de 100 s posteriores.

> O checkpoint não registra o `--iils` usado; os números de restarts abaixo são
> compatíveis com o default do modo (`--iils 10`).

## 2. Sanidade do protocolo (mecanismos que só agem na fronteira de restart)

O ponto crítico do tempo fixo: se o orçamento não couber vários restarts, a mineração
(`mdm`) e a memória adaptativa (`gils_am_rvnd`) degeneram para GILS-RVND puro e um
resultado nulo vira artefato do protocolo, não do algoritmo.

| Algoritmo | restarts médio | restarts mín | mining_calls médio | mining_calls mín | execuções sem mineração |
|---|---:|---:|---:|---:|---:|
| `gils_rvnd` | 2179.7 | 16 | n/a | n/a | 0/100 |
| `gils_am_rvnd_extended_oropt` | 2732.8 | 15 | n/a | n/a | 0/100 |
| `mdm_gils_rvnd` | 1903.3 | 15 | 955.8 | 7 | 0/100 |

Restarts mínimos (sobre as 10 seeds) por instância — as instâncias grandes são as
que apertam o orçamento:

| Instância | GILS-RVND | AM+extended-oropt | MDM-GILS-RVND |
|---|---:|---:|---:|
| st70 | 9722 | 11215 | 8836 |
| rat99 | 2965 | 3622 | 2397 |
| kroD100 | 2609 | 3925 | 2254 |
| lin105 | 3248 | 3459 | 2664 |
| pr107 | 2177 | 2951 | 1583 |
| rat195 | 360 | 558 | 329 |
| pr226 | 229 | 291 | 210 |
| lin318 | 40 | 50 | 69 |
| pr439 | 34 | 15 | 31 |
| att532 | 16 | 16 | 15 |

## 3. Resultados por instância

Custo mínimo (`Best`) e médio (`Avg`) das 10 seeds, e gap médio em relação ao BKS
registrado em `instances/solutions/best_solutions.json`.

| Instância | n | BKS | GILS-RVND Best | GILS-RVND Avg | GILS-RVND Gap% | AM+extended-oropt Best | AM+extended-oropt Avg | AM+extended-oropt Gap% | MDM-GILS-RVND Best | MDM-GILS-RVND Avg | MDM-GILS-RVND Gap% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| st70 | 70 | 19 215 | 19 215 | 19 215.0 | 0.000 | 19 215 | 19 215.0 | 0.000 | 19 215 | 19 215.0 | 0.000 |
| rat99 | 99 | 54 984 | 54 984 | 54 984.0 | 0.000 | 54 984 | 54 984.0 | 0.000 | 54 984 | 54 984.0 | 0.000 |
| kroD100 | 100 | 949 594 | 949 594 | 949 594.0 | 0.000 | 949 594 | 949 594.0 | 0.000 | 949 594 | 949 594.0 | 0.000 |
| lin105 | 105 | 585 823 | 585 823 | 585 823.0 | 0.000 | 585 823 | 585 823.0 | 0.000 | 585 823 | 585 823.0 | 0.000 |
| pr107 | 107 | 1 980 767 | 1 980 767 | 1 980 767.0 | 0.000 | 1 980 767 | 1 980 767.0 | 0.000 | 1 980 767 | 1 980 767.0 | 0.000 |
| rat195 | 195 | 210 191 | 210 305 | 211 005.0 | 0.387 | 210 191 | 210 271.3 | 0.038 | 210 305 | 210 918.8 | 0.346 |
| pr226 | 226 | 7 100 308 | 7 100 308 | 7 100 308.0 | 0.000 | 7 100 308 | 7 100 308.0 | 0.000 | 7 100 308 | 7 100 335.3 | 0.000 |
| lin318 | 318 | 5 560 679 | 5 565 187 | 5 601 310.1 | 0.731 | 5 562 365 | 5 578 865.6 | 0.327 | 5 565 187 | 5 598 699.6 | 0.684 |
| pr439 | 439 | 17 688 561 | 17 886 301 | 17 955 310.8 | 1.508 | 17 876 876 | 17 953 476.8 | 1.498 | 17 886 301 | 17 960 847.8 | 1.539 |
| att532 | 532 | 5 589 568 | 5 688 768 | 5 707 473.3 | 2.109 | 5 666 399 | 5 683 097.2 | 1.673 | 5 688 768 | 5 709 905.9 | 2.153 |
| **Média** | | | | | **0.474** | | | **0.354** | | | **0.472** |

## 4. Comparação pareada vs GILS-RVND

`mean_rel%` = média, sobre as 10 seeds, de `(custo_solver - custo_baseline)/custo_baseline`
(negativo = melhor que o baseline). `W/T/L` = vitórias/empates/derrotas por seed;
`p` = teste dos sinais bilateral exato.

### 4.1 AM+extended-oropt vs GILS-RVND

| Instância | mean_rel% | W/T/L | p | custo médio base | custo médio solver | t base (s) | t solver (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| st70 | +0.000 | 0/10/0 | 1.000 | 19 215.0 | 19 215.0 | 102.7 | 107.8 |
| rat99 | +0.000 | 0/10/0 | 1.000 | 54 984.0 | 54 984.0 | 108.8 | 106.5 |
| kroD100 | +0.000 | 0/10/0 | 1.000 | 949 594.0 | 949 594.0 | 104.2 | 103.9 |
| lin105 | +0.000 | 0/10/0 | 1.000 | 585 823.0 | 585 823.0 | 107.7 | 107.1 |
| pr107 | +0.000 | 0/10/0 | 1.000 | 1 980 767.0 | 1 980 767.0 | 100.0 | 102.2 |
| rat195 | -0.348 | 10/0/0 | **0.002** | 211 005.0 | 210 271.3 | 101.8 | 101.3 |
| pr226 | +0.000 | 0/10/0 | 1.000 | 7 100 308.0 | 7 100 308.0 | 102.1 | 103.2 |
| lin318 | -0.400 | 8/1/1 | **0.039** | 5 601 310.1 | 5 578 865.6 | 104.3 | 104.7 |
| pr439 | -0.009 | 5/0/5 | 1.000 | 17 955 310.8 | 17 953 476.8 | 102.3 | 100.7 |
| att532 | -0.427 | 10/0/0 | **0.002** | 5 707 473.3 | 5 683 097.2 | 101.4 | 102.1 |
| **AGREGADO** | **-0.118** | **33/61/6** | **0.0000** | | | | |

### 4.2 MDM-GILS-RVND vs GILS-RVND

| Instância | mean_rel% | W/T/L | p | custo médio base | custo médio solver | t base (s) | t solver (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| st70 | +0.000 | 0/10/0 | 1.000 | 19 215.0 | 19 215.0 | 102.7 | 109.0 |
| rat99 | +0.000 | 0/10/0 | 1.000 | 54 984.0 | 54 984.0 | 108.8 | 106.6 |
| kroD100 | +0.000 | 0/10/0 | 1.000 | 949 594.0 | 949 594.0 | 104.2 | 106.7 |
| lin105 | +0.000 | 0/10/0 | 1.000 | 585 823.0 | 585 823.0 | 107.7 | 103.9 |
| pr107 | +0.000 | 0/10/0 | 1.000 | 1 980 767.0 | 1 980 767.0 | 100.0 | 101.1 |
| rat195 | -0.041 | 4/2/4 | 1.000 | 211 005.0 | 210 918.8 | 101.8 | 101.8 |
| pr226 | +0.000 | 0/9/1 | 1.000 | 7 100 308.0 | 7 100 335.3 | 102.1 | 104.0 |
| lin318 | -0.047 | 4/4/2 | 0.688 | 5 601 310.1 | 5 598 699.6 | 104.3 | 102.7 |
| pr439 | +0.031 | 0/8/2 | 0.500 | 17 955 310.8 | 17 960 847.8 | 102.3 | 102.8 |
| att532 | +0.043 | 4/2/4 | 1.000 | 5 707 473.3 | 5 709 905.9 | 101.4 | 102.0 |
| **AGREGADO** | **-0.001** | **12/75/13** | 1.0000 | | | | |

## 5. Agregados por faixa de n

| Faixa | AM+extended-oropt W/T/L | AM+extended-oropt p | MDM-GILS-RVND W/T/L | MDM-GILS-RVND p |
|---|---:|---:|---:|---:|
| todas (N=100) | 33/61/6 | **0.000** | 12/75/13 | 1.000 |
| n<195 (`st70`..`pr107`, N=50) | 0/50/0 | 1.000 | 0/50/0 | 1.000 |
| n>=195 (`rat195`..`att532`, N=50) | 33/11/6 | **0.000** | 12/25/13 | 1.000 |
| n>=318 (`lin318`..`att532`, N=30) | 23/1/6 | **0.002** | 8/14/8 | 1.000 |
| n>=439 (`pr439`,`att532`, N=20) | 15/0/5 | **0.041** | 4/10/6 | 0.754 |

## 6. Tempo efetivamente gasto

O `--max-time` é verificado entre iterações do ILS e entre restarts, nunca no meio de
uma convergência do RVND, então o orçamento pode estourar por até uma convergência
(mais uma mineração, no `mdm`).

| Algoritmo | t médio (s) | t máx (s) | estouro médio sobre 100 s |
|---|---:|---:|---:|
| `gils_rvnd` | 103.5 | 109.8 | +3.5 s |
| `gils_am_rvnd_extended_oropt` | 103.9 | 111.5 | +3.9 s |
| `mdm_gils_rvnd` | 104.0 | 112.2 | +4.0 s |

O estouro é de ~3,5 a 4 s (3,5-4% do orçamento) e é praticamente igual nos três
algoritmos, então não enviesa a comparação. O `mdm` não paga um pedágio de tempo
perceptível pela mineração neste orçamento.

## 7. Conclusões

1. **O protocolo é válido**: mesmo em `att532`, a instância mais apertada, o pior caso
   é de 15-16 restarts por execução, e a mineração do `mdm` disparou em 100/100
   execuções (mínimo de 7 chamadas). Nenhum resultado nulo aqui é artefato de
   orçamento curto.
2. **Com 100 s, as 7 instâncias até `pr226` estão saturadas**: os três algoritmos
   acham o mesmo custo em todas as 10 seeds (`0/10/0` empate). O poder estatístico
   vem só de `rat195`, `lin318`, `pr439` e `att532`.
3. **`gils_am_rvnd --rvnd-mode extended-oropt` vence a tempo igual**: -0,118% agregado,
   33/61/6, p < 0,0001; gap médio de BKS cai de 0,474% para 0,354%. O ganho é
   concentrado em `n >= 195` (33/11/6, p < 0,001) e individualmente significativo em
   `rat195` (-0,348%), `lin318` (-0,400%) e `att532` (-0,427%). Isso **confirma a
   tempo fixo** o que [[h12-extended-oropt]] e
   [[mdm-vs-am-extended-tsplib-comparison]] tinham achado a iterações fixas: a
   vantagem não era só um orçamento computacional maior por iteração.
4. **`mdm_gils_rvnd` continua nulo nesta faixa**: -0,001% agregado, 12/75/13, p = 1,0;
   nenhuma instância individual significativa, nenhuma faixa de `n` significativa.
   Consistente com [[h13-mdm-gils-rvnd]] e com o próprio paper, que também não achou
   diferença estatística neste conjunto de 10 instâncias — mas aqui **também não** se
   observa a redução de tempo de 14,47% relatada no paper, porque a tempo fixo essa
   vantagem, se existir, teria que aparecer como qualidade melhor, e não aparece.
5. **`pr439` é a exceção do AM**: 5/0/5, mean_rel% -0,009%. É também a instância onde o
   AM teve o menor número de restarts (15, contra 34 do baseline) — o custo por restart
   do `extended-oropt` aqui corta a quantidade de reinícios pela metade sem devolver
   qualidade. Vale investigar se o orçamento de 100 s é curto demais especificamente
   para essa instância.

