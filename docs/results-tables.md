# Tabelas de resultados

Gerado por `scripts/make_result_tables.py` a partir dos checkpoints brutos.
Todos os lotes: 100 s de relógio por execução, execuções sequenciais.

## Como ler as colunas

Cada instância foi resolvida várias vezes, com uma semente aleatória diferente
por execução (10 nas TSPLIB, 4 em n=500, 3 em n=1000). O algoritmo é
estocástico, então cada semente devolve uma solução diferente.

| coluna | o que é |
|---|---|
| **média** | custo médio das execuções daquela instância -- o que se espera rodando **uma vez** |
| **melhor** | menor custo entre elas -- o que se obtém rodando várias e ficando com a melhor |
| **dif%** | média, par a par, de (custo − custo da referência) / custo da referência. Negativo = melhor |
| **V/E/D** | vitórias / empates / derrotas, comparando **semente a semente** (semente 1 contra semente 1, e assim por diante) |
| **p** | teste dos sinais bilateral exato sobre esses pares. Pequeno = difícil de explicar por acaso |

A comparação estatística é sempre pareada por semente, nunca entre médias:
as duas execuções comparadas partem do mesmo sorteio, o que elimina a
variação da instância e deixa só a diferença entre os algoritmos.

## 1. Proposta vs MDM-GILS-RVND publicado

| conjunto | instâncias | seeds | pares | dif% | V/E/D | p |
|---|---:|---:|---:|---:|---:|---:|
| TSPLIB n >= 200 | 5 | 10 | 50 | **−0.855** | 40/10/0 | < 1e-6 |
| Salehipour n = 500 | 20 | 4 | 80 | **−1.987** | 80/0/0 | < 1e-6 |
| Salehipour n = 1000 | 20 | 3 | 60 | **−3.372** | 60/0/0 | < 1e-6 |

## 2. TSPLIB, por instância

`melhor conhecido` é o valor hoje registrado em
`instances/solutions/best_solutions.json` -- em `att532` e `a280` ele foi
atualizado por este trabalho, então o gap contra ele é conservador.

| instância | n | melhor conhecido | MDM médio | proposta média | proposta melhor | dif% | V/E/D | p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `pr226` | 226 | 7 100 308 | 7 100 308 | 7 100 308 | 7 100 308 | +0.000 | 0/10/0 | 1.0000 |
| `a280` | 280 | 340 998 | 342 795 | 340 998 | 340 998 | −0.524 | 10/0/0 | 0.0020 |
| `lin318` | 318 | 5 560 679 | 5 586 456 | 5 562 975 | 5 560 679 | −0.420 | 10/0/0 | 0.0020 |
| `pr439` | 439 | 17 688 561 | 17 912 677 | 17 698 373 | 17 688 561 | −1.196 | 10/0/0 | 0.0020 |
| `att532` | 532 | 5 573 783 | 5 704 564 | 5 582 883 | 5 573 783 | −2.133 | 10/0/0 | 0.0020 |

## 3. Salehipour n = 500, por instância

| instância | MDM médio | MDM melhor | proposta média | proposta melhor | dif% | V/E/D |
|---|---:|---:|---:|---:|---:|---:|
| `n0500_i01` | 1 854 009 | 1 846 038 | 1 815 393 | 1 809 990 | −2.081 | 4/0/0 |
| `n0500_i02` | 1 779 524 | 1 765 705 | 1 739 487 | 1 736 787 | −2.248 | 4/0/0 |
| `n0500_i03` | 1 813 528 | 1 808 851 | 1 773 972 | 1 768 593 | −2.180 | 4/0/0 |
| `n0500_i04` | 1 832 382 | 1 829 470 | 1 793 127 | 1 783 457 | −2.142 | 4/0/0 |
| `n0500_i05` | 1 823 201 | 1 817 656 | 1 791 124 | 1 784 015 | −1.759 | 4/0/0 |
| `n0500_i06` | 1 859 349 | 1 851 769 | 1 814 508 | 1 810 582 | −2.411 | 4/0/0 |
| `n0500_i07` | 1 870 395 | 1 863 649 | 1 836 503 | 1 833 267 | −1.812 | 4/0/0 |
| `n0500_i08` | 1 815 665 | 1 806 388 | 1 780 462 | 1 779 463 | −1.938 | 4/0/0 |
| `n0500_i09` | 1 862 431 | 1 858 866 | 1 827 914 | 1 818 159 | −1.853 | 4/0/0 |
| `n0500_i10` | 1 883 474 | 1 873 817 | 1 847 980 | 1 846 528 | −1.883 | 4/0/0 |
| `n0500_i11` | 1 847 106 | 1 838 271 | 1 812 700 | 1 808 292 | −1.861 | 4/0/0 |
| `n0500_i12` | 1 832 582 | 1 827 347 | 1 800 996 | 1 794 177 | −1.723 | 4/0/0 |
| `n0500_i13` | 1 833 837 | 1 826 666 | 1 798 521 | 1 793 355 | −1.925 | 4/0/0 |
| `n0500_i14` | 1 888 879 | 1 884 801 | 1 855 503 | 1 853 418 | −1.767 | 4/0/0 |
| `n0500_i15` | 1 869 944 | 1 866 789 | 1 834 244 | 1 826 956 | −1.908 | 4/0/0 |
| `n0500_i16` | 1 856 360 | 1 846 895 | 1 817 041 | 1 811 794 | −2.116 | 4/0/0 |
| `n0500_i17` | 1 853 604 | 1 851 970 | 1 815 319 | 1 808 978 | −2.065 | 4/0/0 |
| `n0500_i18` | 1 848 660 | 1 842 341 | 1 807 364 | 1 803 824 | −2.233 | 4/0/0 |
| `n0500_i19` | 1 867 774 | 1 856 497 | 1 831 556 | 1 827 633 | −1.938 | 4/0/0 |
| `n0500_i20` | 1 837 162 | 1 831 397 | 1 802 328 | 1 798 886 | −1.896 | 4/0/0 |
| **agregado** | | | | | **−1.987** | **80/0/0** |

## 3. Salehipour n = 1000, por instância

| instância | MDM médio | MDM melhor | proposta média | proposta melhor | dif% | V/E/D |
|---|---:|---:|---:|---:|---:|---:|
| `n1000_i01` | 5 264 073 | 5 249 355 | 5 109 201 | 5 086 728 | −2.941 | 3/0/0 |
| `n1000_i02` | 5 312 981 | 5 300 276 | 5 137 974 | 5 119 712 | −3.294 | 3/0/0 |
| `n1000_i03` | 5 346 541 | 5 311 578 | 5 166 740 | 5 118 781 | −3.354 | 3/0/0 |
| `n1000_i04` | 5 303 510 | 5 293 925 | 5 123 638 | 5 099 654 | −3.391 | 3/0/0 |
| `n1000_i05` | 5 229 161 | 5 196 593 | 5 052 352 | 5 044 628 | −3.378 | 3/0/0 |
| `n1000_i06` | 5 289 382 | 5 277 443 | 5 096 055 | 5 048 571 | −3.653 | 3/0/0 |
| `n1000_i07` | 5 268 316 | 5 251 498 | 5 088 407 | 5 067 389 | −3.414 | 3/0/0 |
| `n1000_i08` | 5 369 277 | 5 351 674 | 5 188 609 | 5 182 266 | −3.365 | 3/0/0 |
| `n1000_i09` | 5 224 762 | 5 204 410 | 5 058 534 | 5 043 838 | −3.180 | 3/0/0 |
| `n1000_i10` | 5 253 248 | 5 249 612 | 5 057 862 | 5 034 149 | −3.720 | 3/0/0 |
| `n1000_i11` | 5 379 289 | 5 363 791 | 5 195 174 | 5 186 987 | −3.422 | 3/0/0 |
| `n1000_i12` | 5 209 728 | 5 186 969 | 5 053 240 | 5 038 777 | −3.004 | 3/0/0 |
| `n1000_i13` | 5 321 628 | 5 288 372 | 5 137 457 | 5 107 575 | −3.461 | 3/0/0 |
| `n1000_i14` | 5 292 499 | 5 287 133 | 5 092 333 | 5 077 119 | −3.782 | 3/0/0 |
| `n1000_i15` | 5 264 228 | 5 230 066 | 5 063 255 | 5 012 025 | −3.814 | 3/0/0 |
| `n1000_i16` | 5 215 406 | 5 214 266 | 5 061 069 | 5 052 003 | −2.959 | 3/0/0 |
| `n1000_i17` | 5 302 997 | 5 294 314 | 5 122 948 | 5 102 851 | −3.395 | 3/0/0 |
| `n1000_i18` | 5 286 883 | 5 273 737 | 5 114 772 | 5 109 022 | −3.255 | 3/0/0 |
| `n1000_i19` | 5 208 698 | 5 191 103 | 5 041 538 | 5 034 422 | −3.209 | 3/0/0 |
| `n1000_i20` | 5 245 520 | 5 226 054 | 5 064 935 | 5 053 486 | −3.442 | 3/0/0 |
| **agregado** | | | | | **−3.372** | **60/0/0** |

## 4. Controle: mesma busca local, só muda o mecanismo de memória

Referência de cada linha: o braço **sem mecanismo de memória**.

| conjunto | braço | dif% | V/E/D | p |
|---|---|---:|---:|---:|
| Salehipour n = 500 | proposta | −0.023 | 43/0/37 | 0.5764 |
| Salehipour n = 500 | MDM + busca local nova | −0.026 | 28/31/21 | 0.3916 |
| Salehipour n = 500 | MDM + busca local, mineração com folga | +0.089 | 28/1/51 | 0.0128 |
| Salehipour n = 1000 | proposta | +0.005 | 33/0/27 | 0.5190 |
| Salehipour n = 1000 | MDM + busca local nova | +0.012 | 6/45/9 | 0.6072 |
| Salehipour n = 1000 | MDM + busca local, mineração com folga | +0.490 | 8/1/51 | < 1e-6 |

## 5. Custo médio agregado por braço

Média sobre as instâncias do conjunto. Só entram os braços que rodaram em
**todas** elas -- médias sobre subconjuntos diferentes não são comparáveis.

| conjunto | braço | custo médio | vs MDM publicado |
|---|---|---:|---:|
| TSPLIB n >= 200 | MDM publicado | 7 329 360 | +0.000 |
| TSPLIB n >= 200 | MDM na melhor calibração dele | 7 276 016 | −0.728 |
| TSPLIB n >= 200 | proposta | 7 257 107 | −0.986 |
| Salehipour n = 500 | MDM publicado | 1 846 493 | +0.000 |
| Salehipour n = 500 | MDM + busca local, mineração com folga | 1 811 841 | −1.877 |
| Salehipour n = 500 | sem memória | 1 810 232 | −1.964 |
| Salehipour n = 500 | proposta | 1 809 802 | −1.987 |
| Salehipour n = 500 | MDM + busca local nova | 1 809 755 | −1.990 |
| Salehipour n = 1000 | MDM publicado | 5 279 406 | +0.000 |
| Salehipour n = 1000 | MDM + busca local, mineração com folga | 5 126 077 | −2.904 |
| Salehipour n = 1000 | MDM + busca local nova | 5 101 719 | −3.366 |
| Salehipour n = 1000 | proposta | 5 101 305 | −3.374 |
| Salehipour n = 1000 | sem memória | 5 101 105 | −3.377 |

## 6. Sanidade do protocolo

Mecanismos que só agem na fronteira de reinício precisam de reinícios para
existir. `minerações` é n/a para os braços que não mineram.

| conjunto | braço | reinícios médios | minerações médias | execuções sem minerar |
|---|---|---:|---:|---:|
| TSPLIB n >= 200 | vencedor anterior (H16) | 441.2 | n/a | n/a |
| TSPLIB n >= 200 | proposta | 39.3 | n/a | n/a |
| TSPLIB n >= 200 | MDM publicado | 207.1 | 104.0 | 0/50 |
| TSPLIB n >= 200 | MDM na melhor calibração dele | 8.6 | 4.0 | 11/50 |
| Salehipour n = 500 | proposta | 10.1 | n/a | n/a |
| Salehipour n = 500 | sem memória | 7.8 | n/a | n/a |
| Salehipour n = 500 | MDM publicado | 56.9 | 27.8 | 0/80 |
| Salehipour n = 500 | MDM + busca local nova | 7.7 | 3.6 | 0/80 |
| Salehipour n = 500 | MDM + busca local, mineração com folga | 19.7 | 9.5 | 0/80 |
| Salehipour n = 1000 | proposta | 2.9 | n/a | n/a |
| Salehipour n = 1000 | sem memória | 2.1 | n/a | n/a |
| Salehipour n = 1000 | MDM publicado | 9.0 | 4.2 | 0/60 |
| Salehipour n = 1000 | MDM + busca local nova | 2.1 | 0.8 | 14/60 |
| Salehipour n = 1000 | MDM + busca local, mineração com folga | 5.5 | 2.4 | 0/60 |
