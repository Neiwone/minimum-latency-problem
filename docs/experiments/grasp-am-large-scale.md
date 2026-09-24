# GRASP-AM em escala — achado, correção e veredito final

> Os scripts e dados brutos em `scripts/` citados neste documento foram removidos do
> repositório e estão preservados na tag git `archive/h-scripts`
> (`git show archive/h-scripts:scripts/<arquivo>`).

Status: **ENCERRADA — GILS-AM-RVND empata em qualidade com o baseline
(mesmo padrão de ruído de H1/H2), mas chega lá gastando significativamente
menos tempo em 2 das 3 instâncias.** O `GRASP-AM` original perdia 1-2% por
não ter laço de ILS (seção 1-2); a correção `GILS-AM-RVND` (seção 3) elimina
essa perda de qualidade, e a seção 5 (lote noturno) mostra um efeito
colateral real que não estava previsto: a construção enviesada por memória
não acha soluções melhores, mas com poder estatístico real (N=20/15/10)
chega no mesmo resultado ~20-26% mais rápido em `lin318` e `att532`
(`pr439` foge do padrão, quase sem diferença de tempo).

## 1. O que foi testado

Antes do lote em escala, um teste rápido em instâncias pequenas
(`eil51`/`st70`/`pr76`/`kroA100`/`lin105`, pareado por seed, 15 seeds)
comparou o baseline contra `grasp_am --parent-mode pool` e `--parent-mode
pair`: **empate exato em 100% dos 75 trios** (225 execuções) — mesmo
padrão do resto da sessão nessas escalas pequenas (nenhum gap de
qualidade pra diferenciar métodos). Único sinal: GRASP-AM mais rápido nas
2 maiores instâncias do conjunto (`kroA100`: ~1,5s vs ~2,6s; `lin105`:
~1,9s vs ~2,1s) — plausível, já que cada iteração do GRASP-AM é só
construção+RVND, sem o laço de ILS por cima. Não evidencia qualidade
melhor, só custo computacional menor pra achar a mesma qualidade nessas
instâncias pequenas.

`scripts/night_batch.py` (mesmo lote noturno de H1/H2, seção final de
[h1-adaptive-diversification.md](h1-adaptive-diversification.md) e
[h2-elite-path-relinking.md](h2-elite-path-relinking.md)) comparou, pareado
por seed, o GILS-RVND baseline contra `grasp_am --parent-mode pool` e
`grasp_am --parent-mode pair`, agora em escala.

| instância | n | `grasp_iter`/`pool` | pool: diff média | pool w/t/l | pair: diff média | pair w/t/l |
|---|---|---|---|---|---|---|
| lin318 | 20 | 800/20 | **−1,12%** | 0/0/20 | **−0,44%** | 0/0/20 |
| pr439 | 15 | 500/20 | **−1,68%** | 0/0/15 | **−1,43%** | 0/0/15 |
| att532 | 10 | 300/20 | **−1,33%** | 0/0/10 | **−2,04%** | 0/0/10 |

Todos os `p` do teste de sinal ≤ 0,002 — estatisticamente muito sólido, mas
na direção contrária à esperada: **GRASP-AM (os dois modos) perde para o
GILS-RVND baseline em 100% das 90 execuções**, com gaps de 1,1% a 2,0%.
Tempos de execução do GRASP-AM, para contexto: também menores que os do
GILS-RVND nesse experimento (ex. `lin318`: ~70-84s vs ~159-179s) — não é
só perda de qualidade, é também menos tempo de computação total.

## 2. Por que isso não é (necessariamente) evidência contra a ideia de memória adaptativa

Reler `src/grasp_am.cpp` mostra a causa provável: **o laço principal de
`grasp_am` não tem refinamento por ILS.** Cada iteração é só

```cpp
construction_am(s, eval, alpha, freq, lambda, gen);
RVND(s, gen);
memory.add(s);
```

— uma construção seguida de **uma única convergência de RVND**. Não há
double-bridge, não há tentativa de escapar daquele ótimo local e refinar
mais. Compare com o laço de `gils_rvnd`: cada uma das `I_max` construções é
seguida de até `I_ILS` (100, neste experimento) ciclos de
perturbação+RVND, refinando bem mais profundamente aquele mesmo ponto de
partida antes de desistir dele.

Ou seja, o experimento comparou:

- GILS-RVND: ~10 pontos de partida, cada um refinado por até ~100 ciclos de
  perturbação+RVND.
- GRASP-AM: ~800/500/300 pontos de partida, cada um com **exatamente 1**
  convergência de RVND, sem refino.

Isso não testa "construção enviesada por memória vs. construção gulosa
normal" — testa "busca sem intensificação vs. busca com intensificação".
Dado o quanto ILS+double-bridge importa no GILS-RVND (é a peça central do
método do artigo-base), é plausível que a perda de 1-2% seja inteiramente
explicada pela ausência desse refino, mascarando qualquer efeito (positivo
ou negativo) da memória adaptativa em si.

## 3. `GILS-AM-RVND` — implementado

Para isolar o efeito da construção enviesada por memória, a construção
precisa competir em pé de igualdade — mesma profundidade de refino por
ponto de partida. Implementado em
[`src/gils_am_rvnd.cpp`](../../src/gils_am_rvnd.cpp) (binário novo, não uma
flag no `grasp_am.cpp` — nomes/identidade algorítmica distintos, seguindo a
convenção do projeto de um arquivo por variante):

1. O laço segue o mesmo formato do `gils_rvnd`:

   ```
   para cada reinício i = 1..I_max:
       s <- Construction_AM(alpha, freq, lambda)   # em vez de Construction(alpha)
       s' <- s
       iterILS <- 0
       enquanto iterILS < I_ILS:
           s <- RVND(s)
           se f(s) < f(s'): s' <- s; iterILS <- 0
           s <- s'; perturb(s)              # double-bridge, igual ao gils_rvnd
           iterILS++
       memory.add(s')
       atualizar melhor global
   ```

   Ou seja: literalmente o laço de `gils_rvnd`, só troca `construction(...)`
   por `construction_am(..., freq, lambda)` e recalcula `freq` (pool ou par
   de pais) a cada reinício, exatamente como `grasp_am` já fazia.

2. Reaproveita quase tudo que já existia: `EliteSet`, `EdgeFreq`,
   `pool_frequency`, `two_parent_frequency`, `construction_am` (copiados de
   `grasp_am.cpp`, com `EliteSet` simplificado — a matriz `freq[i][j]`
   interna dele nunca era usada por essas funções, só duplicava trabalho) e
   `perturb`/`double_bridge_once` (copiados de `gils_rvnd.cpp`, sem os
   modos adaptativos de H1 — só o double-bridge de intensidade fixa, para
   isolar exclusivamente o efeito da construção). Novas flags de CLI:
   `--imax`, `--iils`, `--pool`, `--lambda`, `--parent-mode pool|pair`,
   `--seed` (mesmas convenções de `gils_rvnd`/`grasp_am`).

3. Alvo `gils_am_rvnd` adicionado ao `Makefile`; compila limpo. Smoke test:
   determinístico com `--seed`, roda os dois `--parent-mode`, e em `eil51`/
   `lin105` converge para o mesmo custo que o baseline (esperado — essas
   instâncias já são resolvidas por qualquer método, ver o padrão em todo
   este conjunto de experimentos).

4. Integrado a `run_experiments.py` (`gils_am_rvnd_pool`,
   `gils_am_rvnd_pair` em `SOLVERS`) e a `scripts/night_batch.py`, que agora
   roda `fixed` vs `gils_am_rvnd --parent-mode pool` vs `--parent-mode pair`
   pareado por seed em `lin318`/`pr439`/`att532` (config default: mesmos
   `I_max`/`I_ILS` usados no lote de H1/H2 que já fechou, `--pool 20`).
   Script de análise: `scripts/night_batch_analysis.py`.

5. Rodado em escala — ver seção 5.

## 4. Interpretação (antes do resultado — mantido por registro)

Se `GILS-AM-RVND` também perder ou empatar (mesmo perfil de ruído que H1/H2
mostraram na seção 11/10 dos respectivos documentos), é evidência real
contra a ideia de memória adaptativa nesta forma (ou contra os
hiperparâmetros `lambda=0.5`/`pool=20` usados, não testados/ajustados). Se
ganhar de forma consistente e estatisticamente significativa, é a primeira
hipótese desta sessão com sinal positivo de verdade — e a primeira coisa a
verificar, antes de comemorar, é se o ganho aparece nas duas variantes
(`pool` e `pair`) ou só numa (o que apontaria para a fonte específica do
efeito). Resultado real: nem uma coisa nem outra — ver seção 5.

## 5. Lote noturno — resultado final

`python3 scripts/night_batch.py` (config default: `lin318` imax=10/20
seeds, `pr439` imax=5/15 seeds, `att532` imax=3/10 seeds; `--pool 20
--lambda 0.5`), analisado com `scripts/night_batch_analysis.py`.

### 5.1 Qualidade — nulo, mesmo padrão de H1/H2

| instância | n | pool: diff média | pool w/t/l | pool p | pair: diff média | pair w/t/l | pair p |
|---|---|---|---|---|---|---|---|
| lin318 | 20 | −0,081% | 8/3/9 | 1,000 | −0,068% | 8/2/10 | 0,815 |
| pr439 | 15 | +0,039% | 6/0/9 | 0,607 | +0,091% | 8/0/7 | 1,000 |
| att532 | 10 | +0,054% | 6/0/4 | 0,754 | +0,069% | 5/0/5 | 1,000 |

Nenhum `p` significativo, sinais trocando de direção entre instâncias,
magnitude sempre abaixo de 0,1% — o mesmo perfil de ruído em torno de zero
de H1 e H2. **A construção enviesada por memória não acha soluções
melhores que a construção gulosa normal**, quando ambas competem com a
mesma profundidade de refino por ILS.

### 5.2 Tempo — sinal real, não previsto, parcialmente significativo

Como o achado em qualidade era nulo, fomos conferir tempo com o mesmo rigor
(teste de sinal pareado por seed, não só a média agregada):

| instância | n | pool: mais rápido/empate/mais lento | pool p | pool tempo médio | pair: mais rápido/empate/mais lento | pair p | pair tempo médio |
|---|---|---|---|---|---|---|---|
| lin318 | 20 | 18/0/2 | **0,0004** | **−21,9%** | 16/0/4 | **0,012** | **−19,9%** |
| pr439 | 15 | 8/0/7 | 1,000 | −2,6% | 8/0/7 | 1,000 | −3,0% |
| att532 | 10 | 9/0/1 | **0,022** | **−26,4%** | 7/0/3 | 0,344 | −19,9% |

Em `lin318`, os dois modos são significativamente mais rápidos (p=0,0004 e
p=0,012). Em `att532`, `pool` é significativo (p=0,022, apesar da amostra
pequena) e `pair` não (p=0,344, mas mesma direção e magnitude parecida —
provavelmente só falta de poder estatístico com n=10). Em `pr439` não há
efeito de tempo nenhum (~3%, p=1,0 nos dois) — foge do padrão sem
explicação óbvia identificada até agora.

### 5.3 Veredito final

**GILS-AM-RVND não melhora a qualidade da solução, mas em 2 das 3
instâncias grandes testadas chega no mesmo resultado gastando 20-26% menos
tempo de computação, com significância estatística real.** Hipótese
mecânica (não verificada diretamente): a construção enviesada por
frequência de arestas do pool de elite já produz tours mais coerentes com
padrões de boas soluções anteriores, então o RVND tem menos trabalho de
convergência a cada reinício — não é que a busca explore mais espaço ou
ache ótimos melhores, é que ela gasta menos ciclos para chegar no mesmo
ótimo.

Isso não confirma a hipótese original (memória adaptativa → melhor
qualidade) mas encontra um benefício prático real e não previsto (mesma
qualidade, menos tempo) — útil se o gargalo do projeto for tempo de
computação e não qualidade da solução (ex. rodar em instâncias maiores
ainda, ou testar mais seeds no mesmo orçamento de tempo). `pr439` sendo a
exceção sem explicação sugere que vale investigar o que a diferencia de
`lin318`/`att532` antes de generalizar a alegação de velocidade.
