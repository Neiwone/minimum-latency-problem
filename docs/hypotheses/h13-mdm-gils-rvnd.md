# H13 — MDM-GILS-RVND (mineração de segmentos consecutivos)

> Os scripts e dados brutos em `scripts/` citados neste documento foram removidos do
> repositório e estão preservados na tag git `archive/h-scripts`
> (`git show archive/h-scripts:scripts/<arquivo>`).

**Veredito: refutada (nula).** Com a mineração real (FPMax*) corretamente implementada
e poder estatístico completo em `lin318`/`pr439`/`att532` (N=20/15/10), o resultado é
nulo, levemente inclinado para pior: agregado −0,02%, 12W/12T/21L, p=0,163. Custo de
tempo neutro. Não adotado. Em `n=1000`, onde o paper relata o efeito mais forte, o
braço MDM continua **não concluído**.

## Hipótese

Santana, Plastino & Rosseti fazem o que o GRASP-AM/GILS-AM-RVND do projeto tentou
([grasp-am-large-scale](grasp-am-large-scale.md)), com resultados publicados bem mais
fortes: ganho de qualidade **e** velocidade crescendo com `n` (até 32,78% mais rápido e
19/20 melhores soluções em n=1000, 32 novos melhores-conhecidos). A diferença central:
o `construction_am` do projeto dá bônus por frequência de **arestas isoladas** no pool
elite; o paper minera **itemsets frequentes maximais de arcos**, que formam segmentos
consecutivos, e insere o segmento inteiro na construção. A hipótese é que minerar
segmentos, e não arestas soltas, é o que gera o ganho de qualidade.

## O que foi testado

Binário próprio, [`src/mdm_gils_rvnd.cpp`](../../src/mdm_gils_rvnd.cpp):

- **Duas fases:** a primeira metade das `I_max` iterações é GILS-RVND padrão (constrói
  o elite set); da segunda metade em diante, re-minera **toda vez que o elite set
  muda** (o "multi-mining", MDM vs. DM de fase única) e usa a construção guiada.
- **Construção guiada:** mesmo RCL semi-guloso da construção padrão, mas quando o
  candidato escolhido é o primeiro nó de um segmento minerado ainda totalmente não
  visitado, insere o segmento inteiro (Algorithm 5 do paper).
- **Mineração:** cada solução elite vira uma transação de arcos; FPMax* extrai os
  itemsets frequentes maximais e deles saem as Consecutive Arc Lists. A mineração foi
  verificada funcionando: em `lin318` encontra 5 segmentos reais de 6 a 22 nós a cada
  atualização do elite set.
- CLI: `--imax 10 --iils 100 --pool 10 --sup-min 0.70 --max-patterns 5 --seed N`,
  defaults iguais ao paper (elite=10, suporte mínimo 70%, 5 padrões).

A mineração passou por três versões:

1. **Proxy (substituído):** contava cada arco isoladamente e extraía cadeias de arcos
   individualmente frequentes. Tinha uma lacuna de corretude: o suporte de um itemset
   é não crescente com seu tamanho (Apriori), então uma cadeia de arcos cada um
   frequente não garante que o conjunto inteiro apareça em ≥`sup_min` das elites.
2. **FPMax* via `mlxtend`:** subprocesso Python (`scripts/fpmax_mine.py`), com suporte
   conjunto verificado de verdade. Os segmentos têm magnitude parecida à do proxy (6–22
   nós em `lin318`). **Todos os resultados deste documento são desta versão.**
3. **FPMax* em C++ (atual):** via a FPmax-LIB, que empacota a implementação original
   de Grahne & Zhu (a mesma do FIMI usada pelo paper), vendorizada em `external/fpmax/`
   e acessada por [`src/fpmax_mining.cpp`](../../src/fpmax_mining.cpp), com as
   convenções do MDM-HGS-CVRP do mesmo autor (arco `(u,v)` = item `u*n + v`, `minsup`
   absoluto `max(2, supMin × |elite|)`, Consecutive Arc Lists remontadas encadeando os
   arcos do itemset). Reproduz o ground truth da Seção 4.1 do paper (`{2,3}` e
   `{2,5}`), elimina o overhead do subprocesso (Salehipour n=10: ~2,1s → 4,3ms) e faz
   o `mdm` respeitar o [protocolo de tempo fixo](../benchmarks/fixed-time-protocol.md) (`att532`,
   orçamento 15s: 69,6s antes, 15,0s agora).

## Resultados

Calibração inicial (3 seeds em `lin318` e `att532`) e um lote parcial com o proxy
(`lin318` 0,0026%, 5/8/7, p=0,774; `pr439` 0,0530%, 6/3/6, p=1,000) já davam nulo. Nas
instâncias pequenas (`st70`/`rat99`/`kroD100`/`lin105`/`pr107`/`pr226`) o empate foi
exato em todas as seeds; só `rat195` variou (2W/1L para o `mdm`).

**Lote final, mineração real** (`mean_rel%` negativo = `mdm` pior; w/t/l do ponto de
vista do `mdm`):

```
instance      n  mean_rel%      w/t/l   sign_p   time+%
lin318       20    -0,0215 4/7/9          0,267      1,4
pr439        15     0,0039 5/3/7          0,774      8,9
att532       10    -0,0673 3/2/5          0,727     -1,9
AGREGADO     45    -0,0232 12/12/21       0,163    (neutro)
```

Nenhum p significativo, `mean_rel%` negativo em 2 das 3 instâncias. A mineração, com
poucas chamadas por execução, não pesa no tempo total.

## Por que não funcionou

Não há sinal de que a reimplementação esteja errada — a mineração encontra segmentos
reais. O mais provável é que `n=318–532` esteja na faixa em que nem o paper mostra
vantagem clara: na tabela de resultados deles, nas instâncias médias (120–262 nós) o
placar de melhores soluções é só 49/89 (~55%, mal acima de moeda); o efeito só fica
forte a partir de 500+ nós e muito forte em n=1000. No benchmark Salehipour até n=500
o MDM também ficou nulo, sem reproduzir o ganho que o paper relata nessa escala
([salehipour-tsplib-mdm-vs-am-extended](../benchmarks/salehipour-tsplib-mdm-vs-am-extended.md)).

## Limitações

- Os números foram gerados com a versão Python; os padrões minerados são equivalentes
  aos da versão C++, mas a remontagem das Consecutive Arc Lists mudou, então não são
  bit-a-bit reprodutíveis com o código atual.
- `n=1000` não foi testado neste lote (`rand1000`, gerada para H8, não foi rodada); no
  benchmark Salehipour o braço MDM de `n=1000` está não concluído
  ([salehipour-n1000-mdm-vs-am-extended](../benchmarks/salehipour-n1000-mdm-vs-am-extended.md)).
- Um tempo medido (`lin318` seed 2: ~7,6M ms, custo idêntico ao baseline) é artefato de
  relógio do WSL2 e foi excluído da média de tempo.
- Em `n=1000` a mineração C++ usa ~244MB de pico, porque os ids de item chegam a ~10⁶
  com o mapeamento `u*n+v` e a lib aloca arrays proporcionais ao maior id.

## Referências

- Santana, Í., Plastino, A., Rosseti, I. Improving a State-of-the-Art Heuristic for
  the Minimum Latency Problem with Data Mining. arXiv:1908.10705.
  https://arxiv.org/abs/1908.10705
- FPmax-LIB (MIT), implementação do FPmax* de Grahne & Zhu como biblioteca.
  https://github.com/marcelorhmaia/FPmax-LIB
- FIMI, repositório de implementações de mineração de itemsets frequentes.
  http://fimi.uantwerpen.be/src
- MDM-HGS-CVRP (`Program/Population.cpp::mineElite`), integração de referência.
  https://github.com/marcelorhmaia/MDM-HGS-CVRP
