# Proposta × literatura: os valores publicados, instância a instância

**Veredito.** Contra os valores **publicados** do GILS-RVND e do MDM-GILS-RVND, em todas
as instâncias públicas que os dois papers usam (faltam só duas, sem arquivo no projeto:
`pr76r` e a `dsj1000` `EUC_2D`):

| conjunto | resultado | tempo da proposta |
|---|---|---|
| circuito, Abeledo et al., n de 42 a 107 (22 inst.) | acha o ótimo nas 22, mas em 207 das 220 execuções, contra 220/220 do GILS-RVND; média +0,035% (0/17/5) | igual ao do GILS-RVND (0,2 a 13 s) |
| circuito, n < 200 (16 inst.) | empate: iguala a melhor solução publicada nas 16 | igual ao do MDM |
| circuito, 200 ≤ n < 500 (18 inst.) | **média melhor que a do MDM em 12, igual em 4, pior em 2 (p = 0,013)** | 54% do tempo do MDM |
| circuito, n ≥ 500 (21 inst.), 100 s | média 0,52% pior que a do MDM (4/0/17) | 1,5% do tempo do MDM |
| circuito, n ≥ 500 (21 inst.), 1 000 s | **média 0,11% melhor que a do MDM (16/0/5, p = 0,027)** e 0,19% melhor que a do GILS-RVND (17/0/4, p = 0,007) | **13,9% do tempo do MDM** |
| caminho, as 10 TSPLIB do Silva (2012) | iguala o BKS em 9 de 10; média 0,04% melhor que a do GILS-RVND (4/6/0) | 17% do tempo do GILS-RVND |
| novas melhores soluções (circuito) | **12**, de 262 a 1 291 nós | — |

A partir de 120 nós, a proposta empata com os métodos publicados ou os supera, gastando
uma fração do tempo deles. Há duas exceções:

- **n ≥ 500 com 100 s por execução**, que é 1,5% do tempo do MDM. O empate com o MDM
  chega por volta de 300 s (4,5% do tempo dele), e a vitória com 1 000 s (13,9%).
- **As instâncias de Abeledo (n ≤ 107)**, com os tempos de 0,2 a 13 s do GILS-RVND. A
  proposta acha todos os ótimos, mas é um pouco menos confiável que o GILS-RVND
  publicado, que acerta em todas as execuções.

---

## Pergunta

Os outros estudos do projeto comparam a proposta com o GILS-RVND e o MDM
**reimplementados**, rodando na mesma máquina. Esta comparação usa os **números
publicados**: o que se espera de uma tabela de dissertação ao lado da literatura.

## Protocolo

**Instâncias e valores de referência.** Três tabelas, cada uma na variante e no
arredondamento do seu paper:

| suíte | fonte | instâncias | variante | referência publicada |
|---|---|---|---|---|
| `abeledo` | Silva et al. (2012), Tabela 1 | 22 TSPLIB de Abeledo et al. (2010), n de 42 a 107 | circuito, `nint` | ótimo provado (20) ou limitante (`rat99`, `eil101`); GILS-RVND: melhor, média de 10, tempo |
| `circuit` | Santana, Plastino & Rosseti (2019), Tabela 1 | 55 TSPLIB, n de 120 a 1 379 | circuito, `nint` | GILS-RVND e MDM: melhor, média de 10, tempo |
| `path` | Silva et al. (2012), Tabela 2 | 10 TSPLIB de Salehipour et al. (2011), n de 70 a 532 | caminho, truncamento | GILS-RVND: melhor, média de 10, tempo; BKS de `att532` da Tabela 4 de Santana et al. |

A Tabela 1 do Silva tem 23 linhas; o `pr76r` (o `pr76` reescalado) não tem arquivo no
projeto. O Santana et al. também rodaram esse conjunto, mas só relatam que os dois
métodos acham todos os ótimos, sem tabela. A Tabela 1 do Santana tem 56 linhas; a
`dsj1000` `EUC_2D` fica de fora porque o arquivo do projeto é `CEIL_2D`, que corresponde
à linha `dsj1000ceil`. As instâncias aleatórias de
Salehipour (Tabelas 4–7 do Silva, 2–3 do Santana) não são públicas e não entram.

**Orçamento.** Cada execução recebe `min(teto, tempo publicado)`: o tempo médio do MDM
(circuito) ou do GILS-RVND (caminho). A proposta nunca usa mais tempo que o método com
que é comparada. Dois tetos:

- **100 s**, 10 seeds, nas 22 + 55 + 10 instâncias: o orçamento de todo o projeto;
- **1 000 s**, 5 seeds, nas 21 instâncias com n ≥ 500, onde 100 s é menos de 10% do
  tempo do MDM em quase todas. Cada execução registra o melhor custo ao longo do tempo
  (`--trace`), então uma execução de 1 000 s também dá o resultado a 100 s e a 300 s.

**Método.** O proposto, sem nenhum ajuste:
`gils_am_rvnd --rvnd-mode candidate-dlb --cand-k 12 --iils 300`, com `--closed --nint`
no circuito. Todo tour foi verificado a partir das coordenadas.

**Estatística.** Os papers só publicam a média e a melhor de cada instância, então não há
pareamento por seed. A comparação é **por instância**: a média da proposta contra a
média publicada, com teste dos sinais sobre as instâncias. Diferenças abaixo de 0,05 na
média contam como empate, porque os papers imprimem uma casa decimal.

**Máquina.** Os dois papers usam um núcleo de um Core i7: 2,93 GHz no Silva e 3,40 GHz
no Santana. Aqui: Core Ultra 5 135U, num laptop, com 4 execuções em paralelo (núcleos
fixos). Um núcleo atual é mais rápido que um i7 de 2012–2014, mas o paralelismo num
laptop reduz a frequência. Não há fator de conversão confiável entre as máquinas. O
argumento não depende de um: com 1 000 s, a proposta usa 13,9% do tempo do MDM e o
supera, o que só deixaria de valer se esta máquina fosse mais de 7 vezes mais rápida.

## Resultados

### Circuito, Abeledo et al. (22 instâncias, 10 seeds)

Com o tempo do GILS-RVND publicado em cada instância:

| instância | n | ótimo | tempo (s) | execuções no ótimo | média da proposta | média do GILS-RVND |
|---|---:|---:|---:|---:|---:|---:|
| `eil51` | 51 | 10 178 | 0,49 | 4/10 | 10 226,4 | 10 178,0 |
| `eil76` | 76 | 17 976 | 2,64 | 8/10 | 18 003,4 | 17 976,0 |
| `pr76` | 76 | 3 455 242 | 2,31 | 9/10 | 3 457 387,7 | 3 455 242,0 |
| `gr96` | 96 | 2 097 170 | 6,19 | 7/10 | 2 098 706,9 | 2 097 170,0 |
| `eil101` | 101 | 27 513 ¹ | 12,76 | 9/10 | 27 517,1 | 27 513,0 |
| as outras 17 | 42–107 | — | 0,16–11,27 | 170/170 | = | = |

¹ Limitante, não provado ótimo; é o valor do GILS-RVND.

A proposta acha o ótimo (ou o melhor valor conhecido) nas 22 instâncias. Mas 13 das 220
execuções terminam acima dele, enquanto o GILS-RVND publicado acerta nas 220. Com 3× o
tempo publicado, as mesmas 5 instâncias acertam em 48 de 50 execuções: a maior parte é
falta de tempo, mas não toda (`eil76` e `gr96` ainda erram uma vez cada). A causa
provável é a poda da lista de candidatos (K = 12), que ignora movimentos que a RVND
completa do GILS-RVND avalia. Com n ≤ 107, a varredura completa já é barata, e a poda
custa um pouco de confiabilidade sem trazer velocidade. A proposta foi calibrada para
n ≥ 500 (ver [irace](irace-dlb-tuning.md)); em instâncias deste tamanho, o GILS-RVND
original é a escolha mais segura.

### Circuito, 100 s (55 instâncias, 10 seeds)

| faixa | inst. | média vs GILS-RVND | V/E/D | p | média vs MDM | V/E/D | p | tempo / MDM |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| n < 200 | 16 | −0,005% | 5/9/2 | 0,45 | −0,003% | 5/9/2 | 0,45 | 100% |
| 200 ≤ n < 500 | 18 | **−0,059%** | **14/3/1** | **0,001** | **−0,037%** | **12/4/2** | **0,013** | 54% |
| n ≥ 500 | 21 | +0,434% | 5/0/16 | 0,027 | +0,518% | 4/0/17 | 0,007 | 1,5% |

Melhor solução contra a melhor publicada (o menor entre GILS-RVND e MDM):

| faixa | igual | proposta melhor | proposta pior |
|---|---:|---:|---:|
| n < 200 | 16 | 0 | 0 |
| 200 ≤ n < 500 | 13 | 2 | 3 |
| n ≥ 500 | 2 | 4 | 15 |

Até 500 nós, com no máximo o tempo do MDM, a proposta iguala ou supera a literatura. Perde
na média só em `rd400` e `pcb442`, e na melhor solução em `rd400`, `gr431` e `pcb442`, sempre
por menos de 0,25%.

### Circuito, n ≥ 500, até 1 000 s (21 instâncias, 5 seeds)

| marca | tempo / MDM | média vs GILS-RVND | V/E/D | p | média vs MDM | V/E/D | p |
|---|---:|---:|---:|---:|---:|---:|---:|
| 100 s | 1,5% | +0,424% | 6/0/15 | 0,078 | +0,507% | 4/0/17 | 0,007 |
| 300 s | 4,5% | +0,040% | 11/0/10 | 1,0 | +0,123% | 9/0/12 | 0,66 |
| **1 000 s** | **13,9%** | **−0,193%** | **17/0/4** | **0,007** | **−0,110%** | **16/0/5** | **0,027** |

Por instância (média da proposta vs média do MDM, %):

| instância | n | tempo do MDM (s) | 100 s | 300 s | 1 000 s |
|---|---:|---:|---:|---:|---:|
| `att532` | 532 | 760 | −0,058 | −0,243 | **−0,300** |
| `ali535` | 535 | 571 | +0,284 | +0,039 | −0,008 |
| `si535` | 535 | 319 | +0,036 | +0,003 | +0,003 |
| `pa561` | 561 | 873 | −0,114 | −0,296 | **−0,543** |
| `u574` | 574 | 855 | +0,246 | −0,037 | −0,188 |
| `rat575` | 575 | 1 234 | +0,107 | −0,151 | −0,315 |
| `p654` | 654 | 1 239 | −0,007 | −0,007 | −0,008 |
| `d657` | 657 | 1 779 | +0,646 | −0,118 | −0,337 |
| `gr666` | 666 | 1 609 | +0,181 | +0,087 | −0,013 |
| `u724` | 724 | 3 133 | +0,685 | +0,144 | −0,142 |
| `rat783` | 783 | 4 476 | +0,429 | +0,171 | −0,217 |
| `dsj1000` | 1 000 | 11 930 | +1,547 | +0,685 | +0,236 |
| `pr1002` | 1 002 | 8 030 | +0,454 | +0,180 | +0,020 |
| `si1032` | 1 032 | 1 927 | −0,001 | −0,001 | −0,001 |
| `u1060` | 1 060 | 9 910 | +0,833 | +0,216 | −0,118 |
| `vm1084` | 1 084 | 9 469 | +0,489 | +0,188 | −0,143 |
| `pcb1173` | 1 173 | 14 038 | +1,424 | +0,517 | −0,037 |
| `d1291` | 1 291 | 8 073 | +0,446 | −0,002 | **−0,364** |
| `rl1304` | 1 304 | 12 407 | +0,413 | −0,029 | −0,075 |
| `rl1323` | 1 323 | 15 116 | +1,272 | +0,553 | +0,085 |
| `nrw1379` | 1 379 | 32 039 | +1,345 | +0,686 | +0,162 |

A melhor solução é outra história: com 1 000 s, a melhor das 5 execuções da proposta
iguala a melhor publicada em 2 instâncias, a supera em 9 e fica abaixo em 10. A média da
proposta já é melhor que a do MDM, mas o melhor de 10 execuções de horas do MDM ainda
vence o melhor de 5 execuções de 1 000 s em metade das instâncias grandes.

As 4 instâncias de `att532` a `u574` têm tempo do MDM abaixo de 1 000 s; nelas, a coluna
de 1 000 s usa exatamente o tempo do MDM. As derrotas restantes a 1 000 s (`dsj1000`,
`rl1323`, `nrw1379`, `pr1002`, `si535`) estão entre as instâncias em que a proposta teve
a menor fração do tempo do MDM: 8%, 7%, 3% e 12%. A exceção é `si535`, empatada em
+0,003%.

### Caminho, Silva (2012), Tabela 2 (10 instâncias, 10 seeds)

| instância | n | BKS | GILS-RVND média | tempo GILS (s) | proposta melhor | proposta média | tempo (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| `st70` | 70 | 19 215 | 19 215,0 | 1,5 | 19 215 | 19 215,0 | 1,5 |
| `rat99` | 99 | 54 984 | 54 984,0 | 9,5 | 54 984 | 54 984,0 | 9,5 |
| `kroD100` | 100 | 949 594 | 949 594,0 | 6,9 | 949 594 | 949 594,0 | 6,9 |
| `lin105` | 105 | 585 823 | 585 823,0 | 6,2 | 585 823 | 585 823,0 | 6,2 |
| `pr107` | 107 | 1 980 767 | 1 980 767,0 | 8,1 | 1 980 767 | 1 980 767,0 | 8,1 |
| `rat195` | 195 | 210 191 | 210 335,9 | 75,6 | 210 191 | **210 191,0** | 75,6 |
| `pr226` | 226 | 7 100 308 | 7 100 308,0 | 59,0 | 7 100 308 | 7 100 308,0 | 59,1 |
| `lin318` | 318 | 5 560 679 | 5 569 819,5 | 220,6 | 5 560 679 | **5 565 101,8** | 100,0 |
| `pr439` | 439 | 17 688 561 | 17 734 922,0 | 553,7 | 17 688 561 | **17 722 718,6** | 100,0 |
| `att532` | 532 | 5 572 131 | 5 597 866,8 | 1 792,6 | 5 575 445 | **5 587 450,3** | 100,0 |

Iguala o BKS em 9 de 10. A média é igual à publicada nas 6 instâncias em que o GILS-RVND
já acerta sempre, e melhor nas outras 4 (−0,04% no conjunto). Isso com 17% do tempo
publicado. Em `att532`, o BKS (5 572 131) é do MDM, na Tabela 4 de Santana et al.; o
melhor do projeto continua sendo 5 573 783 ([best_solutions.json](../../instances/solutions/best_solutions.json)).

### Novas melhores soluções para o circuito

Contra a melhor solução publicada na Tabela 1 de Santana et al. (o menor entre GILS-RVND e
MDM). Os tours estão em [instances/solutions/closed/](../../instances/solutions/closed/),
junto com a melhor solução de circuito da proposta para cada uma das 77 instâncias
(`--save-best`); todos foram verificados a partir das coordenadas.

| instância | melhor publicada | proposta | dif.% | checkpoint |
|---|---:|---:|---:|---|
| `gil262` | 285 060 | 284 948 | −0,039 | `circuit.json`, `gil262\|6` |
| `d493` | 6 677 458 | 6 671 887 | −0,083 | `circuit.json`, `d493\|7` |
| `att532` | 5 613 010 | 5 607 098 | −0,105 | `circuit_long.json`, `att532\|3` |
| `si535` | 12 247 211 | 12 247 182 | −0,000 | `circuit.json`, `si535\|7` |
| `pa561` | 658 870 | 656 380 | −0,378 | `circuit_long.json`, `pa561\|2` |
| `u574` | 9 308 820 | 9 292 704 | −0,173 | `circuit_long.json`, `u574\|4` |
| `rat575` | 1 847 272 | 1 845 287 | −0,107 | `circuit_long.json`, `rat575\|3` |
| `u724` | 13 504 408 | 13 491 893 | −0,093 | `circuit_long.json`, `u724\|3` |
| `u1060` | 102 508 056 | 102 386 362 | −0,119 | `circuit_long.json`, `u1060\|4` |
| `vm1084` | 94 670 122 | 94 645 899 | −0,026 | `circuit_long.json`, `vm1084\|3` |
| `pcb1173` | 30 890 385 | 30 820 331 | −0,227 | `circuit_long.json`, `pcb1173\|4` |
| `d1291` | 29 383 346 | 29 378 545 | −0,016 | `circuit_long.json`, `d1291\|5` |

## Conclusão

1. **Até ~107 nós (Abeledo), a proposta acha todos os ótimos, mas com 94% de acerto por
   execução, contra 100% do GILS-RVND.** É o único conjunto em que ela não empata nem
   supera o publicado, e o motivo é a poda calibrada para instâncias grandes.
2. **De 120 a ~500 nós, a proposta supera a literatura com menos tempo.** Ela iguala a melhor
   solução publicada em todas as instâncias com n < 200. Entre 200 e 500 nós, sua média
   é melhor que a do MDM em 12 de 18 instâncias (p = 0,013), com 54% do tempo dele.
3. **Acima de 500 nós, ela precisa de cerca de 5% do tempo do MDM para empatar e de 14%
   para superá-lo.** Com 1 000 s, a média é melhor que a do MDM em 16 de 21 instâncias
   (p = 0,027) e melhor que a do GILS-RVND em 17 de 21 (p = 0,007). A melhor solução
   ainda perde para a melhor publicada em 10 das 21.
4. **12 novas melhores soluções** para o circuito, dez delas com n ≥ 532.
5. **No caminho**, a proposta reproduz todos os BKS do Silva menos o de `att532`, que é
   do MDM, e melhora a média publicada onde o GILS-RVND não era exato.

## Limitações

1. **Máquinas diferentes.** Os tempos publicados são de outro hardware, sem fator de
   conversão confiável. A margem de tempo é grande (7× a 1 000 s), mas a comparação não
   é a mesma coisa que rodar os dois métodos lado a lado; isso foi feito nos outros
   estudos do projeto, com os métodos reimplementados.
2. **5 seeds na rodada de 1 000 s**, contra 10 nos papers. A média por instância é mais
   ruidosa; a conclusão se apoia no conjunto das 21 instâncias.
3. **Sem pareamento por seed.** Os papers não publicam execuções individuais, então os
   testes são sobre instâncias, e não sobre execuções.
4. **A referência é o Santana et al. (2019).** Trabalhos posteriores podem ter melhorado
   alguns valores do circuito; os "novos" BKS valem contra essa tabela.
5. **Instâncias de Salehipour fora.** As aleatórias não são públicas; as do projeto
   foram regeneradas e não são as mesmas do Silva e do Santana.

## Reproduzir

```bash
python3 scripts/literature_compare.py --suite circuit      --out results/literature/circuit.json --jobs 4 --cores 2 4 6 8
python3 scripts/literature_compare.py --suite path         --out results/literature/path.json
python3 scripts/literature_compare.py --suite abeledo      --out results/literature/abeledo.json --jobs 4 --cores 2 4 6 8
python3 scripts/literature_compare.py --suite circuit-long --out results/literature/circuit_long.json --jobs 4 --cores 2 4 6 8
```

Com `--report-only`, cada comando só regenera as tabelas a partir do checkpoint; com
`--save-best` (suítes de circuito), grava o melhor tour de cada instância em
`instances/solutions/closed/`. Os agregados também estão na seção 7 de
[results-tables.md](../results-tables.md).
