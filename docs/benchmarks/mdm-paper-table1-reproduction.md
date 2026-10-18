# MDM-GILS-RVND: o do paper contra o deste projeto (Tabela 1)

**Resumo.** As implementações deste projeto do GILS-RVND e do MDM-GILS-RVND,
rodadas no protocolo de Santana, Plastino & Rosseti (arXiv:1908.10705), reproduzem a
**qualidade** que o paper publica nas 28 instâncias da Tabela 1 com n de 120 a 318:

| | diferença média das médias | nossa média melhor / igual / pior | p (sinais) | melhor solução igual à do paper |
|---|---:|---:|---:|---:|
| GILS-RVND | **−0,0007%** | 7/12/9 | 0,80 | 26 de 28 |
| MDM-GILS-RVND | **+0,0072%** | 5/12/11 | 0,21 | 24 de 28 (+1 melhor) |

As diferenças estão na quarta casa decimal e não têm direção. Nenhuma instância passa
de 0,11% em módulo. A relação **de qualidade** entre os dois algoritmos também se
reproduz: no paper e aqui, o MDM empata com o GILS-RVND nessa faixa de tamanho
(−0,004% no paper, +0,004% aqui).

O que **não** se reproduz é a **redução de tempo**: no paper, o MDM roda 15,2% mais
rápido que o GILS-RVND nessas instâncias; aqui, 1,1%. A seção 5 discute a causa
provável, que está na implementação do GILS-RVND de referência, não na mineração.

---

## 1. Por que só a Tabela 1

O paper publica três tabelas por instância:

| tabela | instâncias | comparável aqui? |
|---|---|---|
| 1 | 56 TSPLIB, n de 120 a 1 379, variante **circuito** | **sim**: os arquivos TSPLIB são públicos e idênticos |
| 2 | Salehipour, n = 500 | **não** |
| 3 | Salehipour, n = 1 000 | **não** |

As instâncias de Salehipour et al. (2011) não são públicas ("available from the
authors upon request"). O projeto as **regerou** pelo protocolo documentado
([`generate_salehipour_benchmark.py`](../../scripts/generate_salehipour_benchmark.py)),
então `salehipour_n0500_i01` não é o `TRP-S500-R1` do paper: são outros pontos
sorteados com a mesma distribuição. Os custos das Tabelas 2 e 3 não se aplicam a elas.

Dentro da Tabela 1, ficaram as **28 instâncias com n ≤ 318** (de `gr120` a `lin318`).
As 27 restantes custariam, no tempo do paper, de 6 min a 14 h **por execução**
(`nrw1379`: 49 625 s), e somariam mais de 11 h só até `att532`. `dsj1000ceil` não está
em `instances/`.

## 2. A definição do problema: circuito e `nint`

A primeira tentativa deu custos **abaixo do ótimo provado** publicado no paper (por
exemplo, 3 153 710 em `pr124`, contra o ótimo de 3 154 346 de Bulhões et al., 2018).
Isso é impossível com a mesma função objetivo, e a causa é o arredondamento:

- o paper usa a distância TSPLIB padrão para `EUC_2D`, `nint(√(dx² + dy²))`;
- este projeto **trunca** desde o início ([distance-types](../concepts/distance-types.md)).

Truncar dá distâncias menores ou iguais, logo latências menores. Para esta comparação,
os três solvers ganharam a flag **`--nint`**. Depois deste estudo, o arredondamento
passou a acompanhar a variante, como na literatura: `--closed` usa `nint` por padrão, e
o caminho continua truncando, bit a bit idêntico ao de antes
([distance-types](../concepts/distance-types.md)). A variante circuito do paper é exatamente o
`--closed` do projeto ([return-to-depot](../concepts/return-to-depot.md)).

Com `--closed --nint`, o GILS-RVND do projeto atinge o **ótimo provado** em todas as 18
instâncias da tabela que o têm, e o MDM em 17. Atingir valores provadamente ótimos
publicados confirma que a função objetivo agora é a mesma.

## 3. Protocolo

O do paper (Seção 5), com os mesmos parâmetros:

- `I_max = 10`, `I_ILS = min(100, n)`, `R = {0,00; 0,01; …; 0,25}`;
- MDM com `sup_min = 0,70`, `d = 10`, `MaxP = 5` (os defaults do binário);
- 10 execuções por instância e algoritmo, seeds 1 a 10;
- `--closed --nint`, execução sequencial;
- cada tour verificado: permutação de 0..n−1 a partir do depósito, com a latência do
  circuito recalculada das coordenadas com `nint` e igual à reportada. As 560
  passaram.

Comando:

```bash
python3 scripts/mdm_paper_compare.py --out results/mdm-paper/table1.json --max-n 318
python3 scripts/mdm_paper_compare.py --out results/mdm-paper/table1.json --report-only
```

Dados brutos: [`results/mdm-paper/table1.json`](../../results/mdm-paper/table1.json).

**O que dá para testar.** O paper publica só a melhor solução e a média de cada
instância, sem as 10 execuções individuais nem o desvio. A comparação estatística
possível é, portanto, **entre instâncias**: para cada uma, se a nossa média ficou
acima ou abaixo da média do paper, com teste dos sinais sobre as 28 instâncias. "Igual"
é diferença menor que 0,05 (o paper imprime uma casa decimal).

## 4. Resultados

### 4.1 Por instância

"dif.%" = (nossa média − média do paper) / média do paper; negativo é melhor para nós.
O BKS só aparece onde o paper o cita de Bulhões et al. (2018), todos ótimos provados.

| instância | n | BKS | GILS melhor paper | GILS melhor nosso | GILS média paper | GILS média nossa | dif.% | MDM melhor paper | MDM melhor nosso | MDM média paper | MDM média nossa | dif.% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gr120 | 120 | 363 454 | 363 454 | 363 454 | 363 569,5 | 363 512,4 | −0,016 | 363 454 | 363 454 | 363 454,0 | 363 532,9 | +0,022 |
| pr124 | 124 | 3 154 346 | 3 154 346 | 3 154 346 | 3 154 346,0 | 3 154 346,0 | +0,000 | 3 154 346 | 3 154 346 | 3 154 346,0 | 3 154 346,0 | +0,000 |
| bier127 | 127 | 4 545 005 | 4 545 005 | 4 545 005 | 4 546 378,8 | 4 545 005,0 | −0,030 | 4 545 005 | 4 545 005 | 4 545 691,9 | 4 545 005,0 | −0,015 |
| ch130 | 130 | 349 874 | 349 874 | 349 874 | 349 891,7 | 349 891,7 | +0,000 | 349 874 | 349 874 | 349 903,5 | 349 885,8 | −0,005 |
| pr136 | 136 | 6 199 268 | 6 199 268 | 6 199 268 | 6 199 805,4 | 6 201 074,6 | +0,020 | 6 199 268 | 6 199 268 | 6 200 041,6 | 6 200 357,1 | +0,005 |
| gr137 | 137 | 4 061 498 | 4 061 498 | 4 061 498 | 4 061 498,0 | 4 061 498,0 | +0,000 | 4 061 498 | 4 061 498 | 4 061 498,0 | 4 061 498,0 | +0,000 |
| pr144 | 144 | 3 846 137 | 3 846 137 | 3 846 137 | 3 846 137,0 | 3 846 137,0 | +0,000 | 3 846 137 | 3 846 137 | 3 846 137,0 | 3 846 137,0 | +0,000 |
| ch150 | 150 | 444 424 | 444 424 | 444 424 | 444 424,0 | 444 424,0 | +0,000 | 444 424 | 444 424 | 444 424,0 | 444 424,0 | +0,000 |
| kroA150 | 150 | 1 825 769 | 1 825 769 | 1 825 769 | 1 825 769,0 | 1 825 858,4 | +0,005 | 1 825 769 | 1 825 769 | 1 825 769,0 | 1 825 813,7 | +0,002 |
| kroB150 | 150 | 1 786 546 | 1 786 546 | 1 786 546 | 1 786 546,0 | 1 786 546,0 | +0,000 | 1 786 546 | 1 786 546 | 1 786 546,0 | 1 786 546,0 | +0,000 |
| pr152 | 152 | 5 064 566 | 5 064 566 | 5 064 566 | 5 064 566,0 | 5 064 566,0 | +0,000 | 5 064 566 | 5 064 566 | 5 064 566,0 | 5 064 566,0 | +0,000 |
| u159 | 159 | 2 972 030 | 2 972 030 | 2 972 030 | 2 972 204,2 | 2 972 030,0 | −0,006 | 2 972 030 | 2 972 030 | 2 972 204,2 | 2 972 204,2 | +0,000 |
| si175 | 175 | 1 808 532 | 1 808 532 | 1 808 532 | 1 808 532,0 | 1 808 532,0 | +0,000 | 1 808 532 | 1 808 532 | 1 808 532,0 | 1 808 532,0 | +0,000 |
| brg180 | 180 | 174 750 | 174 750 | 174 750 | 174 750,0 | 174 750,0 | +0,000 | 174 750 | 174 750 | 174 750,0 | 174 750,0 | +0,000 |
| rat195 | 195 | 218 632 | 218 632 | 218 632 | 218 763,2 | 218 862,1 | +0,045 | 218 632 | 218 676 | 218 736,6 | 218 866,2 | +0,059 |
| d198 | 198 | 1 186 049 | 1 186 049 | 1 186 049 | 1 186 098,6 | 1 186 077,0 | −0,002 | 1 186 049 | 1 186 049 | 1 186 273,3 | 1 186 162,8 | −0,009 |
| kroA200 | 200 | 2 672 437 | 2 672 437 | 2 672 437 | 2 672 444,2 | 2 672 510,5 | +0,002 | 2 672 437 | 2 672 437 | 2 672 444,2 | 2 672 559,4 | +0,004 |
| kroB200 | 200 | 2 669 515 | 2 669 515 | 2 669 515 | 2 674 486,0 | 2 672 716,6 | −0,066 | 2 669 515 | 2 669 515 | 2 675 993,6 | 2 675 270,9 | −0,027 |
| gr202 | 202 | — | 2 909 247 | 2 909 247 | 2 914 644,2 | 2 912 268,0 | −0,082 | 2 909 247 | 2 911 364 | 2 913 368,4 | 2 913 640,9 | +0,009 |
| ts225 | 225 | — | 13 240 046 | 13 240 046 | 13 240 046,0 | 13 240 046,0 | +0,000 | 13 240 046 | 13 240 046 | 13 240 046,0 | 13 240 046,0 | +0,000 |
| tsp225 | 225 | — | 402 783 | 402 783 | 403 080,2 | 403 226,3 | +0,036 | 402 783 | 402 783 | 402 933,3 | 403 185,9 | +0,063 |
| pr226 | 226 | — | 7 196 869 | 7 196 869 | 7 196 869,0 | 7 196 869,0 | +0,000 | 7 196 869 | 7 196 869 | 7 196 869,0 | 7 196 869,0 | +0,000 |
| gr229 | 229 | — | 10 725 914 | 10 730 297 | 10 729 883,8 | 10 739 782,8 | +0,092 | 10 725 914 | 10 728 681 | 10 731 249,9 | 10 734 777,8 | +0,033 |
| gil262 | 262 | — | 285 060 | 285 076 | 285 527,1 | 285 527,2 | +0,000 | 285 060 | **284 863** | 285 312,6 | 285 413,1 | +0,035 |
| pr264 | 264 | — | 5 471 615 | 5 471 615 | 5 471 615,0 | 5 471 615,0 | +0,000 | 5 471 615 | 5 471 615 | 5 471 615,0 | 5 471 615,0 | +0,000 |
| a280 | 280 | — | 346 989 | 346 989 | 347 125,9 | 347 200,5 | +0,021 | 346 989 | 346 989 | 347 106,9 | 347 417,9 | +0,090 |
| pr299 | 299 | — | 6 556 628 | 6 556 628 | 6 557 983,4 | 6 561 153,3 | +0,048 | 6 556 628 | 6 556 628 | 6 559 030,8 | 6 561 486,5 | +0,037 |
| lin318 | 318 | — | 5 619 810 | 5 619 810 | 5 629 995,9 | 5 625 010,9 | −0,089 | 5 619 810 | 5 619 810 | 5 630 590,5 | 5 624 891,6 | −0,101 |

### 4.2 Agregado

| algoritmo | dif. média% | nossa média melhor / igual / pior | p (sinais) | melhor solução: igual / nossa melhor / nossa pior |
|---|---:|---:|---:|---:|
| GILS-RVND | −0,0007 | 7/12/9 | 0,804 | 26/0/2 |
| MDM-GILS-RVND | +0,0072 | 5/12/11 | 0,210 | 24/1/3 |

- **Médias.** Nenhuma direção sistemática em nenhum dos dois algoritmos. As diferenças
  por instância ficam entre −0,10% e +0,09%. Para comparação, o desvio-padrão entre
  seeds nas nossas execuções é de 0,05% a 0,15% nas instâncias maiores (`pr299` a
  `lin318`), o que dá um erro-padrão de 0,02% a 0,05% para uma média de 10 execuções e
  de ~0,03% a 0,07% para a diferença entre duas médias. As maiores diferenças estão a
  cerca de dois erros-padrão, o esperado entre 28 instâncias por puro acaso.
- **Melhores soluções.** O GILS-RVND acha a mesma melhor solução do paper em 26 de 28
  instâncias; o MDM, em 24, e em `gil262` acha uma **melhor** (284 863 contra 285 060,
  −0,07%, tour verificado). As cinco diferenças restantes (`gr229`, `gil262` no GILS,
  `rat195`, `gr202` e `gr229` no MDM) são de no máximo 0,07% e dependem de uma única
  seed entre dez.
- **Ótimos provados.** Das 18 instâncias com ótimo provado, o nosso GILS-RVND atinge o
  ótimo em todas, e o nosso MDM em 17 (em `rat195` fica em 218 676, +0,02%). No paper,
  os dois atingem as 18.

### 4.3 O efeito do MDM, no paper e aqui

| | paper | este projeto |
|---|---:|---:|
| média: MDM vs GILS-RVND, dif.% | −0,0037 | +0,0042 |
| média: MDM melhor / igual / pior | 7/14/7 | 7/12/9 |
| **tempo: MDM vs GILS-RVND, dif.%** | **−15,21** | **−1,07** |
| tempo médio do GILS-RVND por execução | 36,55 s | 20,27 s |

Em qualidade, o paper e este projeto contam a mesma história: na faixa n ≤ 318, o MDM
empata com o GILS-RVND. No tempo, não: a redução de 15% do paper vira 1% aqui.
Instância a instância, a redução do paper vai de −27,6% (`pr299`) a +1,9% (`ts225`);
a nossa, de −9,6% (`d198`) a +7,9% (`ch150`), sem relação com a do paper.

**Tempo por instância** (s):

| instância | GILS paper | GILS nosso | MDM paper | MDM nosso | dif. tempo paper% | dif. tempo nosso% |
|---|---:|---:|---:|---:|---:|---:|
| gr120 | 9,54 | 5,44 | 8,10 | 5,56 | −15,09 | +2,24 |
| pr124 | 5,39 | 3,19 | 5,15 | 3,24 | −4,45 | +1,43 |
| bier127 | 9,25 | 5,97 | 7,73 | 5,56 | −16,43 | −6,93 |
| ch130 | 9,23 | 5,77 | 8,88 | 5,41 | −3,79 | −6,33 |
| pr136 | 17,30 | 10,11 | 14,82 | 9,68 | −14,34 | −4,32 |
| gr137 | 8,11 | 5,09 | 7,16 | 5,05 | −11,71 | −0,78 |
| pr144 | 9,11 | 6,94 | 8,80 | 6,54 | −3,40 | −5,65 |
| ch150 | 13,06 | 7,10 | 10,67 | 7,66 | −18,30 | +7,89 |
| kroA150 | 19,84 | 11,72 | 15,68 | 11,53 | −20,97 | −1,60 |
| kroB150 | 16,27 | 10,47 | 14,49 | 10,08 | −10,94 | −3,75 |
| pr152 | 11,23 | 6,93 | 10,20 | 6,80 | −9,17 | −1,93 |
| u159 | 14,21 | 8,24 | 12,92 | 7,81 | −9,08 | −5,20 |
| si175 | 19,14 | 11,33 | 14,85 | 11,71 | −22,41 | +3,39 |
| brg180 | 16,79 | 13,67 | 16,18 | 14,19 | −3,63 | +3,76 |
| rat195 | 44,69 | 20,02 | 35,57 | 20,83 | −20,41 | +4,03 |
| d198 | 38,28 | 21,35 | 31,95 | 19,30 | −16,54 | −9,63 |
| kroA200 | 42,23 | 20,58 | 33,73 | 20,05 | −20,13 | −2,57 |
| kroB200 | 42,00 | 21,52 | 36,17 | 20,91 | −13,88 | −2,83 |
| gr202 | 35,95 | 20,25 | 29,68 | 19,61 | −17,44 | −3,17 |
| ts225 | 26,60 | 12,49 | 27,10 | 13,28 | +1,88 | +6,25 |
| tsp225 | 53,89 | 26,84 | 43,43 | 27,83 | −19,41 | +3,69 |
| pr226 | 34,29 | 17,15 | 28,85 | 18,00 | −15,86 | +4,97 |
| gr229 | 53,66 | 28,09 | 41,12 | 28,16 | −23,37 | +0,28 |
| gil262 | 96,12 | 48,80 | 74,72 | 46,99 | −22,26 | −3,71 |
| pr264 | 47,02 | 25,35 | 38,68 | 25,31 | −17,74 | −0,15 |
| a280 | 107,18 | 58,68 | 79,05 | 57,16 | −26,25 | −2,60 |
| pr299 | 104,92 | 62,94 | 75,93 | 61,30 | −27,63 | −2,60 |
| lin318 | 117,98 | 71,56 | 90,74 | 68,66 | −23,09 | −4,04 |

## 5. Por que a redução de tempo não se reproduz

A explicação mais provável está no **GILS-RVND de referência**, não na mineração.

O paper usa o código-fonte original de Silva et al. (2012), cedido pelos autores, e
nele cada movimento aplicado reconstrói três matrizes n × n (`T`, `C`, `Cr`), ao custo de
`O(n²)` ([proposal-vs-gils-rvnd](../concepts/proposal-vs-gils-rvnd.md), seção 3.1).
Nessa implementação, o tempo de uma descida é dominado pelo **número de movimentos
aplicados**. As soluções construídas a partir de padrões minerados já contêm centenas
de arcos de soluções elite (o paper relata 480 arcos frequentes por padrão em n = 500),
então partem muito mais perto de um ótimo local e aplicam muito menos movimentos até
convergir. Daí os 15–33% de tempo a menos.

Neste projeto, as duas implementações usam somas de prefixo: a reconstrução custa
`O(n)` por movimento, e o tempo da descida passa a ser dominado pelas **varreduras**
(`O(n²)` por vizinhança), cujo número é parecido para uma construção comum e para uma
construção a partir de padrões. Aplicar menos movimentos quase não economiza tempo, e a
vantagem do MDM desaparece.

Dois fatos são consistentes com essa explicação:

1. **Os tempos absolutos.** Nosso GILS-RVND roda a ~55% do tempo do paper (20,3 s
   contra 36,6 s em média), apesar de um processador de notebook. A diferença de
   implementação é grande o bastante para mudar onde o tempo é gasto.
2. **A redução do paper cresce com n:** −11,5% em média nas 12 instâncias com n < 160,
   e de −23% a −28% de `a280` a `lin318`. É o esperado se o custo `O(n²)` por movimento
   for o termo que a mineração economiza.

**Isto é hipótese, não medida.** Confirmá-la exigiria contar movimentos aplicados por
descida nos dois algoritmos, ou rodar com a reconstrução `O(n²)` original. Nenhuma das
duas coisas foi feita.

**Consequência para o resto do projeto.** As comparações a tempo fixo contra o MDM
([H16](../hypotheses/h16-candidate-neighborhoods.md),
[H19](../hypotheses/h19-dlb-fast-regime.md)) usam esta implementação, que é mais
rápida que a original mas **não tem** a vantagem de tempo do MDM sobre o GILS-RVND que
o paper relata. Um leitor pode objetar que, com a vantagem de tempo, o MDM teria mais
iterações dentro do mesmo orçamento. A objeção não muda o resultado do H19: lá, dar ao
MDM a mesma busca local rápida não o fez ganhar, e forçar a mineração a agir mais o
fez **piorar**.

## 6. Conclusão

Com a mesma função objetivo (circuito, `nint`) e o mesmo protocolo, as implementações
do projeto são **compatíveis em qualidade** com as do paper: médias e melhores soluções
iguais dentro da variação entre seeds, todos os ótimos provados atingidos, e a mesma
relação de qualidade entre MDM e GILS-RVND. A redução de tempo de 15% do MDM **não se
reproduz**, e a causa mais provável é a diferença de implementação do GILS-RVND
subjacente.

## 7. Limitações

1. **Só n ≤ 318.** O paper relata que o MDM só ganha em qualidade a partir de ~500
   clientes, e essa faixa ficou de fora por custo. A comparação aqui confirma
   compatibilidade, mas não testa o regime em que o MDM supostamente faz diferença.
2. **Médias contra médias.** Sem as execuções individuais do paper, o teste é entre
   instâncias, sobre médias; não há como testar instância a instância.
3. **Máquinas e compiladores diferentes** (paper: i7 3,4 GHz, g++ 4.4.3; aqui: Intel Core
   Ultra 5 135U sob WSL2). Os tempos absolutos não são comparáveis; só a razão MDM/GILS
   dentro de cada máquina.
4. **Implementações diferentes.** O GILS-RVND do paper é o código original; o deste
   projeto é uma reimplementação com somas de prefixo. As seeds têm o mesmo número, mas
   não geram as mesmas trajetórias.

## 8. Onde está cada coisa

| o quê | onde |
|---|---|
| driver e relatório | [`scripts/mdm_paper_compare.py`](../../scripts/mdm_paper_compare.py) (contém a Tabela 1 do paper inteira, as 56 instâncias) |
| dados brutos (560 execuções) | [`results/mdm-paper/table1.json`](../../results/mdm-paper/table1.json) |
| flag `--nint` | [`src/evaluator.cpp`](../../src/evaluator.cpp), em `gils_rvnd`, `gils_am_rvnd` e `mdm_gils_rvnd` |
| o paper | [`docs/papers/santana-2019-mdm-gils-rvnd.pdf`](../papers/santana-2019-mdm-gils-rvnd.pdf) |
