# H4 — Busca local multi-improvement

Status: **ENCERRADA — implementada corretamente (com um bug real encontrado
e corrigido no caminho), mas consistentemente mais lenta que o
first-improvement atual, com mecanismo bem explicado. Não adotar.** Mantida
disponível como opção (`--rvnd-mode multi`), padrão continua `single`
(comportamento atual, intocado).

## 1. Hipótese

Inspirada em Araujo, Coelho & Marzulo (2020), *"A multi-improvement local
search using dataflow and GPU to solve the minimum latency problem"*: em vez
de aplicar o primeiro movimento de melhora encontrado numa varredura e
recalcular `T`/`C`/`Cr` (O(n²)) imediatamente, escanear a vizinhança
inteira, coletar todos os movimentos de melhora **mutuamente não-
conflitantes** (footprints de posição disjuntos) e aplicá-los todos de uma
vez, recalculando uma única vez por lote. Se houver rotineiramente vários
movimentos simultâneos disponíveis, isso reduziria o número de recomputes
O(n²) por convergência.

## 2. Diagnóstico (antes de implementar)

Ferramenta read-only [`src/diag_multi_improvement.cpp`](../../src/diag_multi_improvement.cpp)
(nunca aplica movimentos, só chama os `evaluate*()` já existentes): mede,
em estados "FRESH" (logo após construção) e "PERTURBED" (um double-bridge
aplicado sobre um ótimo local de RVND — o cenário real do laço de ILS), o
número máximo de movimentos de melhora simultaneamente aplicáveis sem
conflito de posição, por vizinhança.

| instância | estado | swap | 2opt | reinsertion | oropt2 | oropt3 |
|---|---|---|---|---|---|---|
| lin318 | fresh | ~61 | ~62 | ~61 | ~45 | ~36 |
| lin318 | perturbed | ~2,0 | ~2,9 | ~2,8 | ~2,3 | ~2,2 |
| pr439 | perturbed | ~1,8 | ~2,5 | ~2,8 | ~2,1 | ~2,1 |
| att532 | perturbed | ~2,4 | ~3,3 | ~3,3 | ~2,6 | ~2,4 |

(Valores finais, já com a correção de buffer da seção 4 — os números
originais antes da correção eram parecidos, um pouco mais altos.)

Sinal consistente e bem acima de 1 em todos os casos — diagnóstico
favorável, motivou a implementação.

## 3. Prova de corretude teórica (antes de codificar)

Pela fórmula de concatenação do artigo-base, `C(σ⊕σ') = C(σ) +
W(σ')·(T(σ)+e) + C(σ')`: se dois movimentos reordenam customers dentro de
footprints de posição disjuntos, cada um só altera o `C` intrínseco (e
possivelmente `T`) do seu próprio segmento, e essas alterações entram na
fórmula de forma **aditiva/linear** através dos termos `W(·)·T(·)` — não há
termo cruzado multiplicativo entre os dois movimentos. Ou seja, aplicar
dois movimentos de footprint disjunto juntos deveria ser matematicamente
equivalente a aplicá-los sequencialmente com recálculo entre eles.

## 4. Implementação e um bug real encontrado no caminho

Aditivo, nada existente foi alterado: `neighborhood_*_multi` em
[`src/neighborhoods.cpp`](../../src/neighborhoods.cpp) (uma por vizinhança),
`RVND_Multi` em [`src/rvnd.cpp`](../../src/rvnd.cpp), flag `--rvnd-mode
single|multi` em `gils_rvnd` (default `single`, sem mudança de
comportamento) e em `local_search` (para testes). Seleção do lote:
*activity selection* guloso por fim de footprint (maximiza contagem, não
ganho total — não precisou expor o delta de `evaluate*()`, que continua
retornando só bool).

**Bug encontrado**: a prova da seção 3 assume que o footprint de um
movimento captura *tudo* que ele lê e escreve. Na prática,
`evaluate2Opt(i,j)` (e os demais) computam a aresta de fronteira via
`fDist[last][firstNode]` usando o conteúdo da posição **imediatamente
fora** do footprint (`i-1` e `j+1`) — uma leitura, não escrita, que meu
footprint original não protegia. Resultado: dois movimentos com footprints
adjacentes (ex. `[21,23]` e `[24,33]`) eram tratados como compatíveis,
aplicados juntos, e o resultado **piorava o custo** (confirmado
empiricamente: round com `cost_before=13621 → cost_after=13961`) — porque a
avaliação de um deles ficava inválida assim que o outro reescrevia a
posição de fronteira que a primeira avaliação assumia inalterada.
Correção: exigir 1 posição de folga entre footprints escolhidos (`fp.lo >
lastEnd + 1`, não `fp.lo > lastEnd`).

**Segundo bug, mais sério (laço infinito)**: a inicialização `lastEnd = -1`
fazia o *primeiro* candidato de uma varredura ser incorretamente rejeitado
sempre que seu footprint começasse na posição 0 (possível em or-opt2/3, já
que `k` varre de 0 a n-1) — `0 > -1+1=0` é falso. Quando isso deixava
`chosen` vazio mesmo com `candidates` não-vazio, o código antigo ainda
marcava `improved=true` incondicionalmente e chamava
`calculateStructures()` (um no-op), causando um **laço infinito** que
nunca muda o estado. Reproduzido de forma determinística (seed fixo,
`neighborhood_oropt2_multi` em `eil51`) e corrigido com duas mudanças:
`lastEnd` inicializado em `-2` (aceita corretamente footprint em posição
0) e, defensivamente, `if (chosen.empty()) continue;` em todas as 5
funções antes de aplicar/recomputar (nunca marcar progresso sem ter
aplicado algo).

## 5. Verificação de corretude (pós-correção)

- **Ótimo local genuíno**: rodar `single` em cima da saída do `multi`
  nunca encontra melhoria adicional, em `eil51`/`lin318`/`pr439`/`att532`.
- **Stress test** (300 tentativas em `eil51`, 20 em cada instância grande,
  reaplicando cada `neighborhood_*_multi` duas vezes seguidas e exigindo
  que o custo não mude na segunda): 0 falhas.
- **Estado de perturbação repetida** (30 tentativas × 5 perturbações por
  instância, o cenário real do laço de ILS): 0 falhas.
- **`gils_rvnd` completo com `--rvnd-mode multi`**: roda do início ao fim
  sem travar em `eil51`/`lin318`/`pr439`.

## 6. Resultado final — por que não vale a pena

Comparações diretas (mesma seed, `--imax`/`--iils` iguais,
`single` vs `multi`) em `lin318`/`pr439`/`att532`: **`multi` foi mais lento
em 100% das execuções testadas**, entre ~1,3x e ~2,3x mais devagar, com
qualidade mista (às vezes um pouco melhor, às vezes pior, sem padrão
consistente).

Instrumentei o motivo diretamente (2-opt, `lin318`, mesma semente):

| modo | passadas completas O(n²) | recomputes | custo final |
|---|---|---|---|
| single | 8 | 795 | 7.840.491 |
| multi | **144** | 143 | 8.563.550 (pior) |

O `multi` precisou de **18x mais varreduras completas** para convergir. O
motivo: `single` não reinicia a varredura após aplicar um movimento —
continua o mesmo laço `i,j` usando as estruturas já atualizadas, então uma
única passagem já aplica e encadeia dezenas de melhorias (795 recomputes
em só 8 passadas). O `multi` só aplica um lote pequeno (2-4 movimentos, pela
restrição de buffer) por passada e precisa recomeçar a varredura inteira
para achar o próximo lote — e como a varredura em si é O(n²) (não é grátis),
o custo de escanear 144 vezes supera a economia de fazer só 143 recomputes
em vez de 795.

**A hipótese original (existe oportunidade de aplicar vários movimentos
simultâneos) estava certa — o diagnóstico não mentiu.** O que faltou
prever é que o desenho "colete tudo, aplique o lote, recalcule uma vez"
troca poucos recomputes caros por muitas varreduras caras, e essa troca é
desfavorável neste código porque a varredura e o recompute são da mesma
ordem de custo (ambos O(n²)), e o `single` já captura boa parte do benefício
do "encadeamento" *dentro* de uma única varredura, sem precisar de nenhum
mecanismo de lote.

## 7. Recomendação

Não adotar `--rvnd-mode multi` como padrão — mantido como opção documentada
(`single` continua default, comportamento idêntico ao de antes desta
hipótese). Se algum dia quiser retomar a ideia, o caminho mais promissor
não é "colete tudo antes de aplicar" — é reduzir o número de recomputes
*sem* aumentar o número de varreduras, por exemplo atualizando `T`/`C`/`Cr`
incrementalmente só na região afetada por um movimento (não com um
`calculateStructures()` O(n²) completo a cada aplicação) — um problema de
estrutura de dados, não de estratégia de busca.
