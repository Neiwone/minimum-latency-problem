# GILS-RVND vs GILS-AM-RVND (extended-oropt) vs MDM-GILS-RVND — comparação nas 10 instâncias TSPLIB

**Resumo:** nas 10 instâncias TSPLIB do artigo-base, com o protocolo do MDM-GILS-RVND
(Santana, Plastino & Rosseti), `gils_am_rvnd --rvnd-mode extended-oropt` bate o
`gils_rvnd` com significância agregada em todas as janelas de `n` (27/61/12, p=0,024
nas 10 instâncias; p entre 0,020 e 0,041 nas demais), confirmando
[H12](../hypotheses/h12-extended-oropt.md). O `mdm_gils_rvnd` é nulo nesta faixa (12/72/16, p=0,572;
p≥0,44 em todas as janelas), como em [H13](../hypotheses/h13-mdm-gils-rvnd.md), e não reproduz a
redução de tempo de −14,47% do artigo.

## Questão

Comparar três algoritmos nas 10 TSPLIB que o projeto usa por padrão (`st70`, `rat99`,
`kroD100`, `lin105`, `pr107`, `rat195`, `pr226`, `lin318`, `pr439`, `att532`; variante
*Hamiltonian Path*, 70 a 532 clientes): o baseline `gils_rvnd` (Silva et al., 2012),
`gils_am_rvnd --rvnd-mode extended-oropt` (memória adaptativa na construção + or-opt
estendido a segmentos 4–6, [H12](../hypotheses/h12-extended-oropt.md)) e `mdm_gils_rvnd`
(reimplementação do MDM-GILS-RVND com mineração de itemsets maximais via
FPMax*/`mlxtend`, [H13](../hypotheses/h13-mdm-gils-rvnd.md)).

O artigo do MDM-GILS-RVND não publica tabela por instância para este conjunto; na
Seção 5.2 reporta só o agregado: mesmas melhores soluções (nove delas BKS), gap médio
de BKS de 0,08% (MDM-GILS-RVND) e 0,09% (GILS-RVND), nenhuma diferença significativa,
e redução de tempo de 14,47% para o MDM-GILS-RVND. A tabela abaixo é a execução deste
projeto, não números da literatura.

## O que foi testado

Protocolo do artigo (Seção 5): `I_max = 10`, `I_ILS = min(100, n)`,
`R = {0.00, 0.01, ..., 0.25}` (defaults dos três binários); `mdm_gils_rvnd` com
`sup_min = 0.70`, elite pool `d = 10`, `max_patterns = 5` (defaults, iguais ao
artigo). 10 execuções por instância e algoritmo, seeds 1 a 10, pareadas entre os três.
W/T/L e p (teste de sinal exato) são contra o `gils_rvnd`.

## Resultados

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

*(BKS = melhor custo registrado em `instances/solutions/best_solutions.json` para a
variante Hamiltonian Path; Gap% é sobre a solução média.)*

Agregados pareados por janela de `n` (teste de sinal exato):

| Subconjunto | GILS-AM-RVND+extended-oropt W/T/L | GILS-AM-RVND+extended-oropt p | MDM-GILS-RVND W/T/L | MDM-GILS-RVND p |
|---|---:|---:|---:|---:|
| Todas as 10 instâncias (N=100 pares) | 27/61/12 | **0,024** | 12/72/16 | 0,572 |
| n≥195 (`rat195`...`att532`, N=60) | 26/13/11 | **0,020** | 11/23/16 | 0,442 |
| n≥318 (`lin318`...`att532`, N=30) | 20/2/8 | **0,036** | 8/10/12 | 0,503 |
| n≥439 (`pr439`, `att532`, N=20) | 15/0/5 | **0,041** | 7/6/7 | 1,000 |

- **AM+extended-oropt:** o efeito fica concentrado (não necessariamente maior em %) nas
  instâncias maiores: em `pr439`/`att532` o gap médio de BKS cai de 0,39%/0,43% para
  0,25%/0,15%. É a 4ª confirmação independente de [H12](../hypotheses/h12-extended-oropt.md), depois
  de `rand1000`, `rand2000` e do benchmark de Salehipour. Nenhuma instância isolada
  chega a p<0,05 com N=10; só o agregado tem poder estatístico.
- **MDM-GILS-RVND:** nulo em todas as janelas, consistente com
  [H13](../hypotheses/h13-mdm-gils-rvnd.md) e com o próprio artigo, que reporta efeito fraco em
  instâncias médias e forte só em `n≥1000` (fora deste teste, que para em n=532).
- **Tempo:** o `mdm_gils_rvnd` não é mais rápido que o baseline (de +1% a +260%, pior
  nas pequenas, quase neutro nas maiores), plausivelmente porque a mineração nesta
  implementação rodava como subprocesso Python (`fpmax_mine.py` via `mlxtend`) e não
  como código nativo integrado. O AM+extended-oropt empata ou é mais rápido que o
  baseline até `lin318` (a aceleração da memória adaptativa compensa o or-opt
  estendido) e fica ligeiramente mais lento só em `pr439`/`att532` (+5,2%/+0,8%).

## Limitações

- N=10 seeds por instância: nenhuma instância isolada tem poder estatístico.
- Seis das dez instâncias (até `pr226`, exceto `rat195`) empatam em quase todos os
  pares; o sinal vem de quatro instâncias.
- O teste para em n=532, abaixo da faixa em que o artigo reporta ganho do MDM.

## Referências

- Santana, I., Plastino, A., Rosseti, I. Improving a State-of-the-Art Heuristic for the
  Minimum Latency Problem with Data Mining. arXiv:1908.10705.
  https://arxiv.org/abs/1908.10705
