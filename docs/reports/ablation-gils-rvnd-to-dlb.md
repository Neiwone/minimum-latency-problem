# Ablação: do GILS-RVND ao `gils_am_rvnd_dlb`, um componente por vez

**Resumo.** Partindo do GILS-RVND como publicado (`./bin/gils_rvnd`, `I_ILS = 100`) e
acrescentando um componente por vez até a configuração proposta (`gils_am_rvnd_dlb`), o
custo cai **2,168%** a 100 s por execução, nas seis instâncias TSPLIB com n ≥ 500
(**30 vitórias / 0 empates / 0 derrotas**, p < 10⁻⁸). Quatro componentes contribuem
com significância, e a retirada de cada um deles do método final também piora com
significância:

| componente | ganho ao acrescentar | perda ao retirar do método final |
|---|---:|---:|
| lista de candidatos (K = 12) | −1,042% (27/0/3) | +2,184% (0/0/30) |
| 8 vizinhanças extras (or-opt 4–6 e invertido 2–6) | −0,642% (30/0/0) | +0,405% (6/0/24) |
| `I_ILS = 300` | −0,392% (29/0/1) | +0,338% (6/0/24) |
| *don't-look bits* | −0,113% (19/0/11, n.s.) | +0,250% (7/0/23) |
| construção por limiar + memória adaptativa | +0,007% (n.s.) | −0,005% (15/0/15) |

A memória adaptativa não contribui: o método final empata exatamente com o mesmo
algoritmo sem ela, rodando no `gils_rvnd`. Dentro da busca local, uma triagem a 30 s
com as 13 vizinhanças retiradas uma a uma mostra que só **2-opt** e **reinserção**
(or-opt de 1 cliente) são indispensáveis individualmente. As outras são redundantes
entre si: retirar uma de cada vez não muda nada, mas retirar as oito extras juntas
custa 0,405%.

---

## 1. Pergunta

O [`proposal-vs-gils-rvnd`](../concepts/proposal-vs-gils-rvnd.md) lista oito diferenças
entre o GILS-RVND e a proposta. Cada uma foi testada em algum momento do projeto, mas em
lotes diferentes, contra baselines diferentes e em regimes diferentes: o H16 com
`--iils 10`, o H19 sobre o vencedor do H16. Faltava uma medida **única e pareada** que
respondesse duas perguntas:

1. Partindo do algoritmo publicado, **quanto cada componente acrescenta**?
2. **Quanto cada peça vale dentro do método proposto**, inclusive cada estrutura de
   vizinhança?

## 2. Desenho

São dois lotes. O **lote principal** (100 s, sequencial) responde às duas perguntas no
nível dos componentes. A **triagem** (30 s, 3 processos concorrentes) veio antes e é
usada aqui só para o que o lote principal não cobre: a retirada de cada vizinhança
individualmente (seção 4).

### 2.1 Lote principal: cadeia cumulativa

Cada braço é o anterior mais **um** componente. Cada passo é comparado com o passo
anterior (ganho marginal) e com `k0` (ganho acumulado). Até `k4`, todos os braços rodam
no mesmo binário (`gils_rvnd`), então a construção não muda no meio da cadeia.

| passo | componente acrescentado | comando |
|---|---|---|
| `k0` | GILS-RVND: swap, 2-opt, or-opt 1–3; varredura `O(n²)`; `I_ILS = 100` | `gils_rvnd --iils 100` |
| `k1` | + lista de candidatos K = 12 e varredura contínua, ainda com as 5 vizinhanças do artigo ([H16](../hypotheses/h16-candidate-neighborhoods.md)) | `--rvnd-mode candidate --cand-k 12 --cand-drop <as 8 extras>` |
| `k2` | + or-opt 4–6 ([H12](../hypotheses/h12-extended-oropt.md)) e or-opt invertido 2–6 (13 vizinhanças) | `--rvnd-mode candidate --cand-k 12` |
| `k3` | + *don't-look bits* e aplicação de movimento em `O(span)` ([H19](../hypotheses/h19-dlb-fast-regime.md)) | `--rvnd-mode candidate-dlb --cand-k 12` |
| `k4` | + `I_ILS = 300` | `... --iils 300` |
| `k5` | + construção com RCL por limiar, sem memória (`gils_am_rvnd`, λ = 0) | `gils_am_rvnd ... --lambda 0` |
| `k6` | + memória adaptativa (λ = 0,5) = **`gils_am_rvnd_dlb`** | `gils_am_rvnd --rvnd-mode candidate-dlb --cand-k 12 --iils 300` |

A poda entra **antes** das vizinhanças extras de propósito. Com varredura completa,
cada vizinhança nova é mais uma varredura `O(n²)`, e a triagem mostrou que nessa ordem
as vizinhanças pagam em profundidade o que custam em iterações e saem com ganho zero
(seção 5). O valor delas só pode ser medido com a varredura já barata. O `k5` separa
duas coisas que o `gils_am_rvnd` muda de uma vez: a regra da RCL (por limiar em vez de
por cardinalidade) e a memória de arestas.

### 2.2 Lote principal: leave-one-out dos componentes

Uma cadeia mede cada componente **dado tudo o que veio antes**, e por isso depende da
ordem escolhida. O leave-one-out mede o contrário: parte do método final (`k6`), retira
**uma** peça e compara com o método completo. O resultado não depende de ordem.

| braço | o que sai do método final |
|---|---|
| `x_cand` | a lista de candidatos (volta à varredura completa com as 13 vizinhanças; o DLB sai junto, porque depende dela) |
| `x_dlb` | os *don't-look bits* (`--rvnd-mode candidate`) |
| `x_iils` | `I_ILS = 300` (volta a 100) |
| `x_ext` | as 8 vizinhanças extras (fica com as 5 do artigo) |
| `k5` | a memória adaptativa (λ = 0); o mesmo braço da cadeia |
| `k4` | memória e construção por limiar juntas (volta ao `gils_rvnd`); o mesmo braço da cadeia |

### 2.3 Critério de seleção das instâncias

As instâncias saem da lista TSPLIB do projeto
([`scripts/registry.py`](../../scripts/registry.py)) pelos critérios abaixo, aplicados
nesta ordem:

1. **n ≥ 500.** Abaixo disso, o método final chega à melhor solução conhecida ou muito
   perto dela dentro do orçamento (`pr226` satura em todas as seeds; `lin318` e `pr439`
   atingem o BKS a 100 s, [H19](../hypotheses/h19-dlb-fast-regime.md)). Pares empatados
   não carregam informação para o teste dos sinais, e a triagem confirmou o efeito:
   `kroA200` e `a280` só produziram empates nos passos finais.
2. **n ≤ ~1 400.** Os braços com varredura completa (`k0`, `x_cand`) precisam completar
   ao menos algumas descidas dentro de 100 s para a comparação ter sentido. Em `nrw1379`
   o `x_cand` já gasta ~50 s só na primeira descida e completa 19 iterações de ILS no
   orçamento inteiro. Acima disso (`fnl4461`, `pr2392`, `pla7397`), esses braços
   degenerariam em "uma descida parcial".
3. **Um representante por tipo de estrutura**, espalhando n pela faixa:

| instância | n | estrutura |
|---|---:|---|
| `att532` | 532 | 532 cidades dos EUA, distância ATT; referência do projeto |
| `rat783` | 783 | grade perturbada (*rattled grid*) |
| `pr1002` | 1002 | agrupada |
| `pcb1173` | 1173 | furação de placa de circuito, em grade |
| `d1291` | 1291 | furação, irregular |
| `nrw1379` | 1379 | cidades da Renânia do Norte-Vestfália, irregular |

A triagem usou um critério mais largo, com 10 instâncias de n = 200 a 1002 (`kroA200`,
`a280`, `lin318`, `rd400`, `pr439`, `pcb442`, `att532`, `rat575`, `rat783`, `pr1002`),
para ver o efeito crescer com n. Foi ela que motivou o critério 1.

### 2.4 Protocolo

**Lote principal.** O [protocolo de tempo fixo](../benchmarks/fixed-time-protocol.md)
oficial:
- 100 s de relógio por execução, **sequencial** (um processo por vez);
- seeds 1–5, pareadas entre os braços: 6 instâncias × 5 seeds = 30 pares por comparação,
  e 11 braços × 30 = **330 execuções**;
- os braços de uma mesma (instância, seed) rodam em sequência e em ordem embaralhada
  pela seed, para que uma deriva lenta da máquina (temperatura, carga) não favoreça
  sistematicamente nenhum braço.

**Triagem.** 30 s por execução, 5 seeds, 10 instâncias, 24 braços: 1 200 execuções. Os
braços de cada (instância, seed) rodam em grupos de exatamente 3 processos concorrentes,
como no [`screen_parallel`](../../scripts/screen_parallel.py). Toda execução vê a mesma
carga, então o pareamento vale, mas cada uma recebe o equivalente a ~22 s de uma
execução sequencial.

**Nos dois lotes:**
- cada tour é **verificado** antes de ser salvo: permutação de 0..n−1 começando no
  depósito, com a latência recalculada das coordenadas e igual à reportada. As 1 530
  passaram;
- teste dos sinais bilateral exato sobre os pares. Como cada família faz várias
  comparações, a coluna **p Holm** traz o p ajustado pela correção de Holm dentro da
  família, e é ela que decide o que é significativo;
- `rel%` = (custo do braço − custo da referência) / custo da referência; negativo é
  melhor;
- o *gap* é medido contra a melhor solução conhecida do projeto
  (`instances/solutions/best_solutions.json`) ou, quando não há registro, contra o
  melhor custo achado por qualquer braço do mesmo lote;
- "iter. ILS" é a média de perturbações aplicadas no orçamento, uma medida direta de
  velocidade.

Reproduzir (os dois comandos retomam o checkpoint se ele existir):

```bash
python3 scripts/ablation.py --suite official100 --out results/ablation/ablation_100s.json
python3 scripts/ablation.py --suite screen30    --out results/ablation/ablation_30s.json
# só o relatório:
python3 scripts/ablation.py --suite official100 --out results/ablation/ablation_100s.json --report-only
```

## 3. Resultados do lote principal (100 s)

### 3.1 Cadeia cumulativa

| passo | N | gap médio% | iter. ILS | reinícios | rel% vs anterior | V/E/D | p | p Holm | rel% vs `k0` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `k0` GILS-RVND | 30 | 2,729 | 300 | 1,2 | — | — | — | — | — |
| `k1` + lista de candidatos | 30 | 1,653 | 5 404 | 9,1 | **−1,042** | **27/0/3** | **< 0,0001** | **< 0,0001** | −1,042 |
| `k2` + 8 vizinhanças | 30 | 1,000 | 2 277 | 4,2 | **−0,642** | **30/0/0** | **< 0,0001** | **< 0,0001** | −1,678 |
| `k3` + *don't-look bits* | 30 | 0,884 | 3 883 | 6,5 | −0,113 | 19/0/11 | 0,201 | 0,602 | −1,790 |
| `k4` + `I_ILS = 300` | 30 | 0,488 | 3 827 | 2,5 | **−0,392** | **29/0/1** | **< 0,0001** | **< 0,0001** | −2,174 |
| `k5` + RCL por limiar | 30 | 0,518 | 3 806 | 2,3 | +0,031 | 13/0/17 | 0,585 | 0,602 | −2,144 |
| `k6` + memória adaptativa | 30 | 0,494 | 3 767 | 2,6 | −0,024 | 15/7/8 | 0,210 | 0,602 | **−2,168** |

`k6` contra `k0`: **−2,168%, 30/0/0, p < 10⁻⁸**.

**Ganho marginal por instância** (rel% vs passo anterior):

| instância | `k1` | `k2` | `k3` | `k4` | `k5` | `k6` | total vs `k0` |
|---|---:|---:|---:|---:|---:|---:|---:|
| `att532` | −0,287 | −0,393 | −0,016 | −0,203 | +0,208 | −0,210 | −0,900 |
| `rat783` | −1,224 | −0,788 | −0,073 | −0,325 | +0,019 | +0,151 | −2,232 |
| `pr1002` | −1,161 | −0,730 | −0,457 | −0,503 | −0,016 | −0,032 | −2,872 |
| `pcb1173` | −1,112 | −0,470 | +0,017 | −0,506 | −0,197 | −0,068 | −2,318 |
| `d1291` | −1,092 | −0,735 | −0,049 | −0,308 | +0,316 | −0,057 | −1,920 |
| `nrw1379` | −1,377 | −0,734 | −0,101 | −0,504 | −0,146 | +0,074 | −2,765 |

**Gap médio% para a referência:**

| instância | referência | `k0` | `k1` | `k2` | `k3` | `k4` | `k5` | `k6` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `att532` | 5 573 783 | 1,097 | 0,807 | 0,410 | 0,394 | 0,190 | 0,398 | 0,187 |
| `rat783` | 3 190 335 | 2,949 | 1,687 | 0,883 | 0,809 | 0,481 | 0,499 | 0,649 |
| `pr1002` | 115 034 926 | 3,635 | 2,431 | 1,681 | 1,216 | 0,706 | 0,689 | 0,657 |
| `pcb1173` | 30 771 444 | 3,025 | 1,874 | 1,396 | 1,411 | 0,898 | 0,699 | 0,631 |
| `d1291` | 29 297 420 | 2,413 | 1,289 | 0,545 | 0,494 | 0,184 | 0,501 | 0,444 |
| `nrw1379` | 35 098 056 | 3,254 | 1,832 | 1,084 | 0,980 | 0,471 | 0,324 | 0,398 |

Só `att532` tem melhor solução registrada no projeto. As demais referências são o
melhor custo deste lote e não foram gravadas como melhores soluções.

### 3.2 Leave-one-out dos componentes

`rel%` positivo significa que **retirar** a peça piora, ou seja, que ela contribui.

| retirado do método final | N | gap médio% | iter. ILS | rel% | V/E/D | p | p Holm |
|---|---:|---:|---:|---:|---:|---:|---:|
| (nada: `k6`) | 30 | 0,494 | 3 767 | — | — | — | — |
| lista de candidatos (o DLB sai junto) | 30 | 2,688 | 86 | **+2,184** | **0/0/30** | **< 0,0001** | **< 0,0001** |
| as 8 vizinhanças extras | 30 | 0,900 | 10 875 | **+0,405** | **6/0/24** | **0,001** | **0,007** |
| `I_ILS = 300` (volta a 100) | 30 | 0,833 | 3 794 | **+0,338** | **6/0/24** | **0,001** | **0,007** |
| *don't-look bits* | 30 | 0,744 | 2 284 | **+0,250** | **7/0/23** | **0,005** | **0,016** |
| memória adaptativa | 30 | 0,518 | 3 806 | +0,024 | 8/7/15 | 0,210 | 0,420 |
| memória e construção por limiar | 30 | 0,488 | 3 827 | −0,005 | 15/0/15 | 1,000 | 1,000 |

**Por instância** (rel% vs método completo):

| retirado | `att532` | `rat783` | `pr1002` | `pcb1173` | `d1291` | `nrw1379` |
|---|---:|---:|---:|---:|---:|---:|
| lista de candidatos | +0,911 | +1,739 | +2,449 | +2,983 | +2,145 | +2,875 |
| 8 vizinhanças extras | +0,235 | +0,087 | +0,611 | +0,485 | +0,216 | +0,796 |
| `I_ILS = 300` | +0,145 | +0,095 | +0,534 | +0,594 | +0,294 | +0,367 |
| *don't-look bits* | +0,244 | +0,271 | +0,021 | +0,249 | +0,084 | +0,634 |
| memória adaptativa | +0,211 | −0,149 | +0,032 | +0,068 | +0,057 | −0,074 |
| memória e construção por limiar | +0,003 | −0,166 | +0,052 | +0,267 | −0,257 | +0,073 |

### 3.3 Leitura

**A lista de candidatos é o componente dominante.** Acrescentada ao GILS-RVND, vale
−1,04%. Retirada do método final, custa +2,18% e perde nas 30 seeds. O mecanismo é
velocidade: em `nrw1379` o GILS-RVND faz 98 iterações de ILS em 100 s, e o `k1` faz
3 333 (**34×**). A tempo fixo, esse número de iterações vira qualidade diretamente. O
efeito cresce com n: retirá-la custa +0,9% em `att532` e +2,9% a +3,0% em `pcb1173` e
`nrw1379`.

**As vizinhanças extras pagam, mas só depois da poda.** Acrescentadas sobre a varredura
podada, as 8 vizinhanças valem −0,64% e vencem nos 30 pares, **apesar** de reduzirem as
iterações a menos da metade (5 404 → 2 277). Ou seja, elas compram profundidade do ótimo local
que mais que compensa a velocidade perdida. Na triagem, acrescentadas **antes** da poda,
elas davam zero (seção 5): com a varredura `O(n²)`, o custo em iterações era alto demais.

***Don't-look bits* contribuem, mas o efeito é menor que o dos outros três.** Na cadeia,
o passo `k3` não é significativo (−0,11%, 19/0/11). No leave-one-out, retirá-los custa
+0,25% (7/0/23, p Holm = 0,016). A diferença entre as duas medidas é ela mesma um
resultado: o DLB vale mais **combinado com `I_ILS = 300`** do que sozinho. Com
`I_ILS = 100` (o `k3`), a busca reinicia mais, e cada reinício arma todas as cidades de
novo, anulando a economia do DLB. Com `I_ILS = 300`, a maior parte do tempo é gasta em
descidas pós-perturbação, exatamente onde o DLB evita revarrer a rota inteira. Medidos
juntos (`k2` → `k4`), DLB e `I_ILS = 300` valem −0,50% (28/0/2, p < 10⁻⁶).

**`I_ILS = 300` vale −0,39% contra o `I_ILS = 100` publicado.** É menos que o 0,65% do
H19, que media contra o `--iils 10` do protocolo, mas é consistente (29/0/1). O
mecanismo aparece na coluna de reinícios, que cai de 6,5 para 2,5: o orçamento passa a
aprofundar poucas trajetórias em vez de recomeçar de construções novas.

**Construção por limiar e memória adaptativa não contribuem.** Os dois passos juntos
somam +0,007%, e o método final empata com o mesmo algoritmo rodando no `gils_rvnd`
(−0,005%, **15/0/15**). Isso reproduz o controle de justiça do
[H19](../hypotheses/h19-dlb-fast-regime.md) por outro caminho. A ressalva é que, com
`I_ILS = 300`, as instâncias fazem de **1,0** (`nrw1379`) a **5,2** (`att532`)
reinícios por execução, e a memória só age a partir do segundo. Ela tem pouca
oportunidade de agir, mas não nenhuma, e onde age mais (`att532`, 5,2 reinícios) o
efeito é inconsistente: retirar só a memória custa +0,21%, mas retirar memória e
construção juntas custa +0,003%.

**Robustez.** Seis das 330 execuções atravessaram uma suspensão da máquina (tempo de
parede de 125 s a 12 h). O orçamento do solver é medido em `steady_clock`, que não
avança durante a suspensão, e o número de iterações de ILS dessas execuções está dentro
da faixa das outras seeds do mesmo braço: nenhuma recebeu tempo de CPU a mais ou a menos.
Mesmo assim, refiz as comparações sem os 6 pares (instância, seed) afetados (24 pares
por comparação). Nenhuma conclusão muda: os quatro componentes continuam significativos
no leave-one-out (p entre 10⁻⁵ e 0,015), e construção e memória continuam nulas.

## 4. Cada estrutura de vizinhança (triagem, 30 s)

O lote principal mede as 8 vizinhanças extras como um bloco. A contribuição de **cada**
vizinhança vem da triagem: o método final com uma vizinhança retirada por vez
(`--cand-drop`), em 10 instâncias de n = 200 a 1002, 50 pares por comparação. Os valores
absolutos não são comparáveis com o lote principal (orçamento ~22 s equivalente), só os
pares entre si.

| retirada | N | gap médio% | iter. ILS | rel% | V/E/D | p | p Holm |
|---|---:|---:|---:|---:|---:|---:|---:|
| (nenhuma) | 50 | 0,590 | 2 725 | — | — | — | — |
| **2-opt** | 50 | 1,532 | 2 870 | **+0,933** | **7/3/40** | **< 0,0001** | **< 0,0001** |
| **or-opt 1** (reinserção) | 50 | 1,119 | 2 830 | **+0,525** | **7/4/39** | **< 0,0001** | **< 0,0001** |
| swap | 50 | 0,553 | 2 856 | −0,036 | 22/9/19 | 0,755 | 1,000 |
| or-opt 2 | 50 | 0,522 | 3 041 | −0,066 | 22/7/21 | 1,000 | 1,000 |
| or-opt 3 | 50 | 0,540 | 3 044 | −0,049 | 22/10/18 | 0,636 | 1,000 |
| or-opt 4 | 50 | 0,511 | 2 976 | −0,077 | 22/10/18 | 0,636 | 1,000 |
| or-opt 5 | 50 | 0,527 | 2 941 | −0,061 | 21/9/20 | 1,000 | 1,000 |
| or-opt 6 | 50 | 0,586 | 3 008 | −0,004 | 24/10/16 | 0,268 | 1,000 |
| invertido 2 | 50 | 0,491 | 3 139 | −0,098 | 25/9/16 | 0,211 | 1,000 |
| invertido 3 | 50 | 0,483 | 2 943 | −0,106 | 26/9/15 | 0,117 | 1,000 |
| invertido 4 | 50 | 0,551 | 3 092 | −0,038 | 20/9/21 | 1,000 | 1,000 |
| invertido 5 | 50 | 0,550 | 2 887 | −0,040 | 21/9/20 | 1,000 | 1,000 |
| invertido 6 | 50 | 0,595 | 2 971 | +0,005 | 20/9/21 | 1,000 | 1,000 |
| grupo or-opt 4–6 | 50 | 0,495 | 3 414 | −0,094 | 25/8/17 | 0,280 | 1,000 |
| grupo invertido 2–6 | 50 | 0,618 | 4 738 | +0,028 | 16/9/25 | 0,211 | 1,000 |
| os dois grupos | 50 | 0,613 | 7 224 | +0,023 | 19/8/23 | 0,644 | 1,000 |

**Por instância** (rel% vs método completo; instâncias em ordem de n):

| retirada | `kroA200` | `a280` | `lin318` | `rd400` | `pr439` | `pcb442` | `att532` | `rat575` | `rat783` | `pr1002` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2-opt | +0,046 | +0,256 | +0,153 | +1,253 | +0,594 | +0,729 | +0,746 | +0,726 | +2,101 | +2,729 |
| or-opt 1 | +0,036 | +0,165 | +0,259 | +0,454 | +0,059 | +0,290 | +0,276 | +1,180 | +1,147 | +1,381 |
| swap | +0,000 | +0,048 | −0,104 | −0,366 | −0,077 | +0,067 | −0,061 | +0,334 | −0,186 | −0,012 |
| or-opt 2 | +0,000 | +0,062 | −0,015 | −0,012 | +0,038 | +0,080 | −0,016 | −0,239 | −0,154 | −0,407 |
| or-opt 3 | +0,000 | +0,000 | −0,148 | −0,242 | +0,059 | +0,075 | −0,230 | +0,102 | +0,082 | −0,184 |
| or-opt 4 | +0,000 | +0,000 | −0,053 | −0,079 | −0,116 | −0,111 | −0,167 | −0,158 | +0,034 | −0,123 |
| or-opt 5 | +0,000 | +0,025 | −0,018 | −0,180 | −0,094 | +0,003 | +0,069 | −0,311 | −0,068 | −0,038 |
| or-opt 6 | +0,000 | +0,000 | −0,128 | −0,146 | −0,099 | −0,040 | −0,027 | −0,104 | +0,246 | +0,258 |
| invertido 2 | +0,000 | +0,025 | −0,145 | −0,172 | −0,072 | −0,051 | −0,029 | −0,204 | +0,041 | −0,370 |
| invertido 3 | +0,000 | +0,025 | −0,138 | −0,030 | +0,017 | −0,043 | −0,128 | −0,293 | −0,280 | −0,189 |
| invertido 4 | +0,000 | +0,021 | −0,070 | +0,119 | −0,057 | +0,109 | −0,000 | −0,254 | −0,218 | −0,029 |
| invertido 5 | +0,000 | +0,025 | −0,105 | −0,131 | −0,056 | +0,002 | +0,109 | −0,160 | +0,011 | −0,091 |
| invertido 6 | +0,000 | +0,006 | +0,063 | −0,245 | −0,094 | −0,115 | +0,169 | −0,051 | +0,617 | −0,295 |

**Leitura.**

- **2-opt e reinserção são indispensáveis.** São as únicas vizinhanças cuja retirada
  isolada piora com significância, e ambas pioram mais quanto maior o n (2-opt: +0,05%
  em `kroA200`, +2,7% em `pr1002`). Nenhuma outra faz o papel delas: o 2-opt é a única
  que inverte trechos de comprimento arbitrário (o or-opt invertido só inverte blocos de
  até 6), e a reinserção é a única que move um cliente isolado (todo outro or-opt move
  blocos de 2 ou mais).
- **As outras onze são redundantes entre si.** Retirar qualquer uma delas sozinha não
  muda nada mensurável, e o sinal médio é até levemente negativo: cada vizinhança a menos
  deixa a descida ~5–15% mais barata. O lote principal mostra que essa redundância é
  **individual, não coletiva**: as 8 extras retiradas juntas custam +0,405% a 100 s.
  O mais provável é que os movimentos que uma delas acha sejam achados, em boa parte,
  pelas vizinhanças de comprimento próximo, já que as varreduras podadas usam as mesmas
  âncoras geométricas. Essa redundância é inferida do resultado, não foi medida
  diretamente.
- **A triagem subestima o bloco de vizinhanças.** A 30 s, retirar as 8 extras juntas
  custava só +0,023% (n.s.); a 100 s, custa +0,405% (6/0/24). As vizinhanças extras
  compram profundidade, e profundidade só vira qualidade quando o orçamento permite
  aproveitá-la.

## 5. O que a triagem a 30 s errou, e por quê

A triagem também rodou uma cadeia, na ordem histórica (vizinhanças antes da poda). A
comparação com o lote principal é útil como lição de protocolo:

| componente | triagem, 30 s concorrente (50 pares, n = 200–1002) | lote principal, 100 s sequencial (30 pares, n ≥ 500) |
|---|---|---|
| lista de candidatos | −0,912% (45/5/0), dominante | −1,042% (27/0/3), dominante |
| 8 vizinhanças extras | +0,017% antes da poda; retirá-las depois dela: +0,023% (n.s.) | −0,642% (30/0/0); retirá-las: +0,405% |
| *don't-look bits* | −0,072% (n.s.) | −0,113% (n.s.); retirá-los: +0,250% |
| `I_ILS = 300` | −0,076% (n.s.) | −0,392% (29/0/1) |
| construção + memória | +0,009% (n.s.) | +0,007% (n.s.) |
| total | −1,037% (45/3/2) | −2,168% (30/0/0) |

A triagem acertou o que é robusto (a poda domina, e construção e memória não contam),
mas **errou os três componentes que pagam no longo prazo**. Duas razões, que se somam:

1. **Orçamento curto.** Com ~22 s equivalentes, DLB e `I_ILS = 300` não têm tempo de
   acumular vantagem, e as vizinhanças extras não têm tempo de converter profundidade em
   qualidade.
2. **Instâncias pequenas.** Seis das dez tinham n ≤ 442, onde o método final já está
   perto do teto. Restritos às quatro instâncias com n ≥ 500, os números da triagem já
   apontavam na direção certa: `I_ILS = 300` com −0,145% (15/2/3, p = 0,008) e DLB com
   −0,254% (13/0/7).

A conclusão que essa triagem chegou a sustentar ("o algoritmo final poderia ser só
GILS-RVND com 5 vizinhanças podadas") está **errada** e foi descartada. Ela também
punha em dúvida o valor do or-opt invertido citado no
[proposal-vs-gils-rvnd](../concepts/proposal-vs-gils-rvnd.md). O lote principal não
mede o invertido isoladamente, mas confirma que o bloco de vizinhanças extras, do qual
ele faz parte, vale 0,4%.

## 6. Conclusões

Em ordem de força:

1. **Do GILS-RVND publicado ao método proposto, o custo cai 2,17% a 100 s em n ≥ 500**,
   vencendo nas 30 seeds, e o ganho cresce com n (−0,9% em `att532`, −2,9% em
   `pr1002`).
2. **Quatro componentes carregam o resultado**, todos de busca local ou de calibração, e
   cada um é significativo quando retirado do método final: lista de candidatos
   (+2,18%), vizinhanças extras (+0,41%), `I_ILS = 300` (+0,34%) e *don't-look bits*
   (+0,25%).
3. **Velocidade e profundidade se complementam.** A poda e o DLB compram iterações, e as
   vizinhanças extras gastam parte delas em profundidade. A poda vem primeiro: sem ela,
   as vizinhanças extras não pagam o que custam.
4. **2-opt e reinserção são as duas vizinhanças indispensáveis.** As outras são
   individualmente substituíveis, mas não coletivamente.
5. **Construção por limiar e memória adaptativa não contribuem**, o que é consistente com
   o controle de justiça do H19: o método final empata com o mesmo algoritmo sem memória
   (15/0/15).

## 7. Limitações

1. **Cinco seeds por instância.** Suficiente para o agregado (30 pares), mas nenhuma
   instância isolada atinge significância sozinha.
2. **A memória adaptativa age pouco.** Com `I_ILS = 300`, as instâncias fazem de 1 a 5
   reinícios em 100 s, e a memória só age a partir do segundo. O "zero" vale para este
   orçamento; com orçamentos maiores ela teria mais oportunidades.
3. **Componentes agrupados.** Três pares de mudanças não podem ser separados com as flags
   atuais: lista de candidatos + varredura contínua, DLB + aplicação em `O(span)`, e as
   somas de prefixo em `O(n)`, que já estão no `gils_rvnd` usado como `k0`. Logo, **o
   `k0` já é 2,4–2,9× mais rápido que o código original do artigo**
   ([H16](../hypotheses/h16-candidate-neighborhoods.md)), e os ganhos medidos aqui são
   sobre essa base mais rápida.
4. **Vizinhanças individuais só na triagem.** A contribuição de cada vizinhança isolada
   (seção 4) vem do lote de 30 s, que comprovadamente subestima o bloco de vizinhanças.
   2-opt e reinserção indispensáveis é um resultado robusto; "as outras são
   individualmente nulas" deveria ser rechecado a 100 s.
5. **Referências sem BKS da literatura.** O *gap* é contra o melhor valor deste projeto,
   não contra valores publicados; serve para comparar braços, não para comparar com
   outros trabalhos.
6. **Uma só máquina**: um notebook com núcleos heterogêneos (Intel Core Ultra 5 135U, sob
   WSL2). Seis execuções atravessaram suspensões; verificado que isso não afetou o tempo
   de CPU recebido nem as conclusões (seção 3.3).

## 8. Onde está cada coisa

| o quê | onde |
|---|---|
| driver dos dois lotes e relatório | [`scripts/ablation.py`](../../scripts/ablation.py) (`--suite official100` / `screen30`) |
| dados do lote principal (330 execuções) | [`results/ablation/ablation_100s.json`](../../results/ablation/ablation_100s.json) |
| dados da triagem (1 200 execuções) | [`results/ablation/ablation_30s.json`](../../results/ablation/ablation_30s.json) |
| `--cand-drop` (retirar vizinhanças) | [`src/neighborhoods_cand.cpp`](../../src/neighborhoods_cand.cpp), flag em `gils_rvnd` e `gils_am_rvnd` |
| modos `extended-oropt-rev` e `candidate` no `gils_rvnd` | [`src/gils_rvnd.cpp`](../../src/gils_rvnd.cpp) |
| contador `ILS_ITERS` na saída | `gils_rvnd`, `gils_am_rvnd` |
