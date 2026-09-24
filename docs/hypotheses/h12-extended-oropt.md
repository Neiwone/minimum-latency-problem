# H12a — Or-opt estendido a segmentos maiores (4, 5, 6)

> Os scripts e dados brutos em `scripts/` citados neste documento foram removidos do
> repositório e estão preservados na tag git `archive/h-scripts`
> (`git show archive/h-scripts:scripts/<arquivo>`).

**Veredito: confirmada, com efeito que cresce com `n`.** `--rvnd-mode extended-oropt`
é nulo em `lin318` (p=0,359), significativo em `pr439` (+0,33%, p=0,007) e `att532`
(+0,39%, 10/0/0, p=0,002), e forte em `rand1000` (+1,17%, 10/0/0, p=0,002, mas +87,3%
de tempo). Combinado com `GILS-AM-RVND`, ganha no agregado (30/4/11, p=0,004) e em
`rand2000` é melhor e mais rápido ao mesmo tempo (+1,11%, 10/0/0, p=0,002, 18,4% mais
rápido). No benchmark de Salehipour, n=1000 isolado dá +0,99%, 17/3, p=0,003. Adotado
como opção (`single` continua default); `gils_am_rvnd --rvnd-mode extended-oropt` é
recomendado para `n≳1000`. Com `grasp_am` não se sustenta.

## Hipótese

As 5 vizinhanças do artigo-base (swap, 2-opt, reinsertion, or-opt2, or-opt3) só
realocam segmentos de tamanho 1-3. Depois de H9/H10/H11 mostrarem que escapar melhor do
mesmo RVND não paga, fortalecer a própria vizinhança com or-opt de 4, 5 e 6 deveria
alcançar ótimos que o RVND original não alcança. (LK adaptado ao MLP exigiria um
critério de ganho reconstruído sobre T/C/Cr; foi deixado para depois.)

## O que foi testado

- **Diagnóstico** (sem aplicar movimentos): em 12 de 15 ótimos locais do RVND padrão
  (`lin318`/`pr439`/`att532`, 5 cada) havia pelo menos um or-opt de comprimento ≥4
  melhorando — às vezes muitos (26 movimentos de or-opt6 num único ótimo de `lin318`),
  ao contrário do quase-zero de [H9](h9-ruin-recreate.md) e
  [H10](h10-dynasearch.md).
- **Mecanismo**: um or-opt genérico por comprimento de segmento em
  [`src/neighborhoods.cpp`](../../src/neighborhoods.cpp) (idêntico a or-opt2/3 para
  `segLen=2,3`), e um RVND com 8 vizinhanças (as 5 originais + or-opt 4/5/6) em
  [`src/rvnd.cpp`](../../src/rvnd.cpp). Flag `--rvnd-mode single|extended-oropt` em
  `gils_rvnd`, `local_search`, `grasp_am` e `gils_am_rvnd`; `extended-oropt-wide`
  acrescenta or-opt 8 e 10. Por ser superconjunto estrito das vizinhanças, nunca
  termina pior que `single` na convergência (verificado em `eil51`, `kroA100`,
  `lin318`).

## Resultados

Mean_rel% positivo = `extended-oropt` melhor. Uma calibração de 1 seed em `lin318`
(`--imax 5 --iils 50`) já mostrava melhor custo e menor tempo (5.581.880 em 26,1s
contra 5.590.653 em 28,6s).

**`gils_rvnd`, `single` vs `extended-oropt`** (pareado por seed, mesmas
`--imax`/`--iils` de H1/H2/H6):

```
instance      n  mean_rel%      w/t/l   sign_p   time+%
lin318       20     0,0027 12/1/7         0,359     11,3
pr439        15     0,3311 13/0/2         0,007     42,9
att532       10     0,3878 10/0/0         0,002     23,3
AGREGADO     45     0,1977 35/1/9         0,000     26,0
```

**n=1000** (`rand1000`, N=10, `--imax 1 --iils 100`; a calibração de 1 seed dava
-1,26% de custo com tempo 2,57x maior):

```
instance      n  mean_rel%      w/t/l   sign_p   time+%
rand1000     10     1,1709 10/0/0         0,002     87,3
```

p=0,002 é o menor valor possível para N=10 no teste de sinal.

**`grasp_am` com `extended-oropt`** (N=15-20, `--parent-mode pool`, `lin318`
iter=800, `pr439` iter=500, `att532` iter=300). A calibração de 5 seeds dava 3W/2L com
vitórias de ~1-1,8%, mas com poder estatístico:

```
instance      n  mean_rel%      w/t/l   sign_p   time+%
lin318       20     0,2453 12/0/8         0,503     13,9
pr439        15     0,4696 9/0/6         0,607      7,6
att532       10     0,1658 5/0/5         1,000     17,3
AGREGADO     45     0,3024 26/0/19        0,371     12,6
```

Nenhum p perto de significância: não adotado.

**`gils_am_rvnd` com `extended-oropt`** (`--parent-mode pool`, `lin318` imax=10/N=20,
`pr439` imax=5/N=15, `att532` imax=3/N=10):

```
instance      n  mean_rel%      w/t/l   sign_p   time+%
lin318       20     0,1019 12/4/4         0,077     16,0
pr439        15     0,1232 10/0/5         0,302     14,7
att532       10     0,4580 8/0/2          0,109     50,0
AGREGADO     45     0,1881 30/4/11        0,004     25,8
```

Só o agregado é significativo; nenhuma instância isolada chega a p<0,05.

**n=2000** (`rand2000`, gerada com `instance_generator.py --n 2000 --grid 1000
--seed 42`; N=10, `--imax 1 --iils 10`, `gils_rvnd` single vs `gils_am_rvnd
--rvnd-mode extended-oropt`):

```
instance      n  mean_rel%      w/t/l   sign_p   time+%
rand2000     10     1,1141 10/0/0         0,002    -18,4
```

Um tempo (seed 4, ~4,7M ms) é artefato de relógio de uma interrupção da máquina durante
o lote e foi excluído da média de tempo; o resultado da execução não foi afetado.

**Benchmark de Salehipour** (140 instâncias, `instances/salehipour/`, ver
[h-salehipour-grasp-vnd](h-salehipour-grasp-vnd.md); `gils_rvnd_imax1` vs
`gils_am_rvnd_extended_oropt_imax1`, `--imax 1`):

```
     n  instances  mean_rel%      w/t/l   sign_p  time_b_vs_a%
    10-200  100     ~0,00              1,000     (nulo, esperado — n pequeno)
   500       20     0,4124     12/0/8    0,503         +32,8
  1000       20     0,9852    17/0/3     0,003         +40,7
------------------------------------------------------------------------------------------
   ALL(500+1000) 40  0,6988   29/0/11    0,006
```

É a terceira confirmação independente do efeito crescente com `n`, junto com
`rand1000`/`rand2000` e com o `grasp_vnd` no mesmo benchmark (p<0,001 agregado).

## Por que funcionou

Diferente de H1/H2/H4/H6 (o mecanismo ajuda isolado, mas o RVND absorve a vantagem no
pipeline completo) e de H9/H10/H11 (mecanismo sólido, oportunidade rara ou platô),
aqui a vantagem sobrevive ao ILS porque não é uma vantagem de entrada nem de escape: é
uma vizinhança mais forte, que acha ótimos que as 5 vizinhanças nunca alcançariam, não
importa quantas vezes a busca reinicie. O efeito cresce com `n`, como a literatura de
DBMEA/GQPSO já sugeria ([H8](h8-dbmea-population.md)).

O custo é um fator constante: 3 vizinhanças O(n²) a mais por varredura, sem o overhead
de [H4](h4-multi-improvement.md) (~18x mais varreduras completas). Em n≤532 isso dá
~11-43% a mais de tempo; em n=1000 cresce para +87,3%. Combinado com `GILS-AM-RVND`, a
construção enviesada por memória (20-26% mais rápida, ver
[grasp-am-large-scale](grasp-am-large-scale.md)) compensa esse custo, e em n=2000 a
combinação fica mais rápida que o baseline. No `grasp_am`, que faz uma única
convergência de RVND por construção, sem ILS, a vizinhança maior não preserva a
vantagem.

## Limitações

- Em `lin318` (n=318) não há ganho que justifique o tempo extra; por isso `single`
  continua default.
- `rand1000` e `rand2000` são instâncias geradas pelo projeto, com N=10 e `--imax 1`.
- `extended-oropt-wide` (or-opt 8 e 10) está **não concluído**: só há calibração de 1
  seed, com sinal misto (em `lin318` pior que `extended-oropt`, 5.647.282 contra
  5.630.429; em `att532` melhor, 5.588.190 contra 5.605.750). Um orçamento fixo de
  `iils` pode penalizar um superconjunto de movimentos, então a comparação não é limpa.
- As calibrações de N pequeno enganaram no `grasp_am` (N=5 parecia forte).

## Referências

- Salehipour, A., Sörensen, K., Goos, P., Bräysy, O. (2011). Efficient GRASP+VND and
  GRASP+VNS metaheuristics for the traveling repairman problem. *4OR*, 9(2), 189–209.
