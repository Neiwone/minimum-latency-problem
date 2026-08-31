# H14 — Escape sequencial estilo Lin-Kernighan

## Motivação

Depois de H12a (or-opt estendido) se confirmar como o único achado de
qualidade real da sessão, e com o projeto virando TCC, a pergunta natural
foi: existe um ganho categoricamente maior disponível, ou ~1% é o teto do
que RVND com vizinhanças simples consegue capturar? O candidato óbvio é
Lin-Kernighan — a família de busca local mais forte conhecida para TSP,
nunca adaptada a um objetivo posicional como o MLP.

**Por que o critério clássico de LK não serve aqui**: LK decide estender
ou fechar a cadeia comparando o comprimento da aresta removida com o da
aresta adicionada — um critério aditivo, válido só porque o custo do TSP é
soma de arestas. No MLP o custo é `Σ(n-i+1)·w(...)`: uma aresta cara no
início da rota penaliza todo cliente depois dela. O critério aditivo do
LK está simplesmente errado aqui.

**Por que isso ainda é viável**: a infraestrutura T/C/Cr do projeto
(`solution.cpp`) já dá o custo exato de qualquer concatenação de
segmentos (retos ou revertidos) em O(1) dado que as tabelas estão
atualizadas. Diferente do H10 (dynasearch), que precisava buscar a
melhor combinação de reversões *simultâneas* e caiu numa fronteira de
Pareto (T e C não decompõem em DP escalar), uma cadeia LK é
*sequencial* — cada passo compromete uma escolha antes do próximo, então
basta um estado corrente `(t, custo)`, sem a complicação combinatória.

## Etapa 1 — diagnóstico (`src/diag_lk.cpp`)

Pergunta testada primeiro, barata: a partir de uma solução já convergida
por `RVND_ExtendedOrOpt` (nenhuma vizinhança simples melhora), uma cadeia
de reversões 2-opt sequenciais, guiada por listas de candidatos
(`Evaluator::fNearCity`, k-vizinhos mais próximos), profundidade limitada,
aplicada de fato a cada passo (`reverse` + `calculateStructures`,
O(n²) por passo, mas poucos passos), consegue achar uma solução
estritamente melhor que RVND não alcança?

Mecânica da cadeia (posições, não IDs de cidade; depósito nunca é ponta
livre nem faz parte de um intervalo revertido): dado `freeEnd` (posição
com a cidade c1) e candidato c2 na posição `posC2`:
- `posC2 > freeEnd`: reverte `[freeEnd+1, posC2]`
- `posC2 < freeEnd`: reverte `[posC2, freeEnd-1]`

Em ambos os casos a nova aresta `(c1,c2)` aparece (verificado contra a
derivação do próprio `evaluate2Opt`: reverter `[i,j]` cria as arestas
`(tour[i-1],tour[j])` e `(tour[i],tour[j+1])`), e a nova ponta livre é
sempre `posC2` — o antigo vizinho de c1 fica lá, pendente para o próximo
passo, sem bookkeeping extra.

**Bug real encontrado e corrigido**: o candidato mais próximo de c1 é
frequentemente o próprio vizinho de tour atual (natural — busca local já
conectou coisas próximas), o que gera `i==j` (reversão de 1 elemento,
no-op). Sem excluir esse caso, a cadeia ficava presa oscilando entre dois
não-movimentos para sempre (visto em `LK_VERBOSE=1`: `reverse[281,281]`,
`reverse[282,282]`, repetindo, delta sempre 0). Corrigido excluindo
candidatos com `i>=j`.

### Resultado do diagnóstico

Escapes (cadeias que bateram o ótimo local do RVND estendido) são
**raros mas reais**, e crescem com profundidade/largura de candidatos —
não é o zero absoluto que apareceria se RVND já cobrisse tudo que uma
busca sequencial limitada alcança:

```
depth=8  cand-k=12  (5 trials × 40 starts cada, lin318/pr439/att532/rand1000/rand2000)
  lin318   0.5% escapes   best_delta_seen=-10436 (-0.18%)
  pr439    1.0% escapes   best_delta_seen=-34732 (-0.18%)
  att532   1.5% escapes   best_delta_seen=  -904 (-0.02%)
  rand1000 1.5% escapes   best_delta_seen=-51263 (-0.46%)
  rand2000 1.0% escapes   best_delta_seen= -5006 (-0.02%)

depth=15 cand-k=20  (lin318/pr439/att532)
  lin318   1.5% escapes   best_delta_seen=-11262 (-0.19%)
  pr439    2.5% escapes   best_delta_seen=-44555 (-0.23%)
  att532   1.5% escapes   best_delta_seen= -2679 (-0.05%)
```

Conclusão da etapa 1: vale integrar de verdade (não é nulo total).

## Etapa 2 — integração (`RVND_LKEscape`, `src/rvnd_lk.cpp`)

Converge com `RVND_ExtendedOrOpt`, depois dispara lotes de cadeias LK a
partir de posições aleatórias; se alguma cadeia acha um ponto
estritamente melhor, adota e reconverge (`RVND_ExtendedOrOpt` de novo,
já que novos movimentos podem ter se aberto); repete até um lote inteiro
falhar. Ligado a `gils_am_rvnd` via `--rvnd-mode lk-escape`.

**Achado de calibração — custo do lote domina o raro ganho**: com
`numProbes=40/depth=15/candK=20` (parâmetros do diagnóstico), uma
chamada de `RVND_LKEscape` em `lin318` ficou **2,6x mais lenta** que
`RVND_ExtendedOrOpt` sozinho e pior em qualidade (o orçamento de ILS
fixo em iterações, não em tempo, absorve o custo extra como menos
iterações reais). Reduzindo para `numProbes=10/depth=10/candK=12`
melhorou a lentidão mas não zerou (1,6x). Isso é esperado: a taxa de
escape medida na etapa 1 é de ~1-2,5% dos starts, então a maioria dos
lotes de sondas paga o custo O(n²) inteiro sem achar nada, a cada
convergência do RVND — não só na convergência final.

## Teste estatístico — `gils_am_rvnd --rvnd-mode lk-escape` vs `extended-oropt`

`rand1000.tsp`, `--imax 1 --iils 5`, 20 seeds pareadas, `numProbes=10
depth=10 candK=12`:

```
N=20  W/T/L = 10/0/10   sign_p = 1,0000
mean_rel% (lk melhor) = +0,29%   (desvio = 0,94% — dentro do ruído)
mean_time_rel% (lk mais lento) = +30,5%
```

**Nulo limpo, e pior em tempo.** Empate estatístico perfeito (10/10) na
qualidade, com variância grande o suficiente (de -0,66% a +2,23% por
seed) pra engolir qualquer efeito real que exista, e ainda ~30% mais
lento em média (com variância também enorme: -47% a +263%, um sinal de
que quando escapa de verdade o custo da reconvergência completa varia
muito).

## Interpretação

O mecanismo *existe* (etapa 1 provou isso: cadeias sequenciais alcançam
pontos que nenhuma vizinhança simples alcança, taxa crescente com
profundidade). Mas capturá-lo de forma que compense o custo — pagar
O(n²) por passo, por sonda, a cada convergência de RVND, pela cauda rara
de 1-2,5% que escapa — não funcionou com esta integração. Hipóteses do
porquê, não testadas:

1. **Frequência errada**: disparar sondas em TODA convergência do RVND
   (dentro do laço de ILS) é caro demais pra uma taxa de acerto tão
   baixa. Talvez funcionasse como diversificação ocasional (ex.: só
   quando o ILS está perto de estagnar) em vez de rotina.
2. **Profundidade/candidatos mal calibrados para o trade-off de tempo**:
   o diagnóstico usou parâmetros generosos (depth=15, candK=20) pra medir
   a taxa de escape "verdadeira"; a integração precisaria de parâmetros
   muito mais baratos (depth baixo, candK pequeno) pra não dominar o
   tempo, o que reduziria ainda mais a taxa de escape já rara.
3. **O ganho de cada escape pode não compor**: mesmo quando uma cadeia
   escapa, reconvergir com `RVND_ExtendedOrOpt` pode devolver a um ótimo
   local só marginalmente diferente do original em qualidade final —
   i.e., o "escape" é real mas não necessariamente leva a uma bacia de
   atração melhor no espaço de soluções.

Combinado com H1-H11/H12b/H13 (todos nulos) e H12a (o único achado real,
~1%), este é mais um dado honesto para o capítulo de discussão do TCC:
mesmo o candidato teoricamente mais promissor para escapar de ótimos
locais do RVND — Lin-Kernighan adaptado corretamente ao objetivo
posicional do MLP — não superou o RVND estendido em teste estatístico
completo, ao menos nesta integração. Ver [[mlp-research-status]].
