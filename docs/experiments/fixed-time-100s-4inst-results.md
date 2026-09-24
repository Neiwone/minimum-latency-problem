# Resultados — comparação a tempo fixo de 100 s (4 instâncias, n = 226..532)

Lote completo: **120 execuções** (4 instâncias × 3 algoritmos × 10 seeds), 100 s de
wall-clock por execução, sequenciais, pareadas por seed. Dados brutos em
`results/fixed-time/fixed_time_100s.json`.

```bash
python3 scripts/run_experiments.py --mode fixed-time --time-limit 100 --runs 10 \
    --solvers gils_rvnd mdm_gils_rvnd gils_am_rvnd_cand
```

`gils_am_rvnd_cand` = `./bin/gils_am_rvnd --rvnd-mode candidate --cand-k 12`, o
algoritmo de [[h16-candidate-neighborhoods]]: GILS-AM-RVND com vizinhanças podadas por
lista de candidatos (swap, 2-opt, or-opt direto 1–6 e or-opt **invertido** 2–6, cada
varredura restrita aos 12 vizinhos mais próximos), sobre dados de subsequência em O(n).

## 1. Custos por instância

Melhor e médio sobre as 10 seeds; gap em relação ao BKS de
`instances/solutions/best_solutions.json`.

| instância | n | BKS | algoritmo | melhor | médio | gap médio |
|---|---:|---:|---|---:|---:|---:|
| `pr226` | 226 | 7 100 308 | GILS-RVND | **7 100 308** | 7 100 308.0 | 0.000% |
| `pr226` | 226 | 7 100 308 | MDM-GILS-RVND | **7 100 308** | 7 100 308.0 | 0.000% |
| `pr226` | 226 | 7 100 308 | GILS-AM-RVND-cand | **7 100 308** | 7 100 308.0 | 0.000% |
| `lin318` | 318 | 5 560 679 | GILS-RVND | 5 565 187 | 5 592 625.9 | 0.575% |
| `lin318` | 318 | 5 560 679 | MDM-GILS-RVND | 5 562 365 | 5 580 863.1 | 0.363% |
| `lin318` | 318 | 5 560 679 | GILS-AM-RVND-cand | **5 560 897** | 5 575 565.0 | 0.268% |
| `pr439` | 439 | 17 688 561 | GILS-RVND | 17 849 900 | 17 913 031.3 | 1.269% |
| `pr439` | 439 | 17 688 561 | MDM-GILS-RVND | 17 860 270 | 17 922 577.6 | 1.323% |
| `pr439` | 439 | 17 688 561 | GILS-AM-RVND-cand | **17 757 765** | 17 825 822.5 | 0.776% |
| `att532` | 532 | 5 589 568 | GILS-RVND | 5 679 255 | 5 698 737.1 | 1.953% |
| `att532` | 532 | 5 589 568 | MDM-GILS-RVND | 5 672 681 | 5 693 884.6 | 1.866% |
| `att532` | 532 | 5 589 568 | GILS-AM-RVND-cand | **5 626 624** | 5 637 685.4 | 0.861% |

Gap médio de BKS por algoritmo, resumido:

| instância | GILS-RVND | MDM-GILS-RVND | GILS-AM-RVND-cand |
|---|---:|---:|---:|
| `pr226` | **0.000%** | **0.000%** | **0.000%** |
| `lin318` | 0.575% | 0.363% | **0.268%** |
| `pr439` | 1.269% | 1.323% | **0.776%** |
| `att532` | 1.953% | 1.866% | **0.861%** |
| **média** | 0.949% | 0.888% | **0.476%** |

## 2. Comparação pareada

`mean_rel%` = média, sobre as 10 seeds, de `(custo_A - custo_B)/custo_B`; negativo
significa que A é melhor. `W/T/L` = vitórias/empates/derrotas por seed; `p` = teste
dos sinais bilateral exato.

### GILS-AM-RVND-cand vs MDM-GILS-RVND

| instância | n | mean_rel% | W/T/L | p |
|---|---:|---:|---:|---:|
| `pr226` | 226 | +0.000 | 0/10/0 | 1.000 |
| `lin318` | 318 | -0.095 | 8/0/2 | 0.109 |
| `pr439` | 439 | -0.539 | 8/0/2 | 0.109 |
| `att532` | 532 | -0.986 | 10/0/0 | **0.002** |
| **AGREGADO** | | **-0.405** | **26/10/4** | **0.00006** |

### GILS-AM-RVND-cand vs GILS-RVND

| instância | n | mean_rel% | W/T/L | p |
|---|---:|---:|---:|---:|
| `pr226` | 226 | +0.000 | 0/10/0 | 1.000 |
| `lin318` | 318 | -0.305 | 9/0/1 | **0.021** |
| `pr439` | 439 | -0.486 | 7/0/3 | 0.344 |
| `att532` | 532 | -1.071 | 10/0/0 | **0.002** |
| **AGREGADO** | | **-0.465** | **26/10/4** | **0.00006** |

### MDM-GILS-RVND vs GILS-RVND

| instância | n | mean_rel% | W/T/L | p |
|---|---:|---:|---:|---:|
| `pr226` | 226 | +0.000 | 0/10/0 | 1.000 |
| `lin318` | 318 | -0.210 | 7/3/0 | **0.016** |
| `pr439` | 439 | +0.053 | 2/4/4 | 0.688 |
| `att532` | 532 | -0.085 | 4/2/4 | 1.000 |
| **AGREGADO** | | **-0.060** | **13/19/8** | 0.38331 |

## 3. Reinícios completados no mesmo orçamento

É o mecanismo do ganho: a tempo fixo, quantos ótimos locais cabem em 100 s.

| instância | GILS-RVND | MDM-GILS-RVND | GILS-AM-RVND-cand | fator vs MDM |
|---|---:|---:|---:|---:|
| `pr226` | 622 | 633 | 1946 | 3.1× |
| `lin318` | 189 | 184 | 869 | 4.7× |
| `pr439` | 97 | 94 | 304 | 3.2× |
| `att532` | 51 | 50 | 217 | 4.4× |

## 4. Tempo efetivamente gasto

`--max-time` é checado entre iterações de ILS e entre reinícios, nunca no meio de uma
convergência do RVND, então o orçamento pode estourar por até uma convergência.

| algoritmo | t médio | t máximo | estouro médio |
|---|---:|---:|---:|
| GILS-RVND | 100.0 s | 100.1 s | +0.0 s |
| MDM-GILS-RVND | 100.0 s | 100.1 s | +0.0 s |
| GILS-AM-RVND-cand | 100.0 s | 100.0 s | +0.0 s |

## 5. Leitura

1. **GILS-AM-RVND-cand bate o MDM-GILS-RVND**: -0.405% agregado,
   26/10/4 em 40 pares, p = 0.00006.
2. **O efeito cresce com `n`** e é o oposto de uniforme: `pr226` (n=226) está saturada a
   100 s — os três algoritmos empatam —, e a vantagem só aparece de `lin318` em diante,
   chegando ao máximo em `att532`.
3. **O MDM continua nulo contra o GILS-RVND** neste orçamento, consistente com
   [[h13-mdm-gils-rvnd]] e com o próprio paper do MDM, que também não achou diferença
   estatística no conjunto de 10 instâncias TSPLIB.
4. **O mecanismo é vazão de reinícios**, não profundidade do ótimo local (seção 3).

## 6. Ressalva

A poda por lista de candidatos poderia ser portada para o `mdm_gils_rvnd`, que aqui
ainda varre O(n²) completo — parte da vantagem medida é engenharia de vizinhança, não
estratégia de busca. Os dados de subsequência em O(n), esses, já beneficiam os três
binários igualmente neste lote.
