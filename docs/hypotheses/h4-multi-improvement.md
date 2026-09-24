# H4 — Busca local multi-improvement

**Veredito: refutada.** A oportunidade existe (em estado perturbado há ~1,8 a ~3,3 movimentos de
melhora simultâneos sem conflito por vizinhança), mas `--rvnd-mode multi` foi mais lento
em 100% das execuções testadas, entre ~1,3x e ~2,3x, com qualidade mista. Não adotado
como padrão; fica disponível como opção (padrão `single`, comportamento anterior intocado).

## Hipótese

Inspirada em Araujo, Coelho & Marzulo (2020): em vez de aplicar o primeiro movimento de
melhora e recalcular `T`/`C`/`Cr` (O(n²)) na hora, varrer a vizinhança inteira, coletar
todos os movimentos de melhora com footprints de posição disjuntos e aplicá-los de uma
vez, com um único recálculo por lote. Isso reduziria o número de recálculos O(n²) por
convergência.

## O que foi testado

**Diagnóstico** read-only em
[`src/diag_multi_improvement.cpp`](../../src/diag_multi_improvement.cpp): número máximo de
movimentos de melhora aplicáveis ao mesmo tempo, por vizinhança, em estado "fresh" (logo
após a construção) e "perturbed" (double-bridge sobre um ótimo local do RVND, o cenário
real do ILS).

**Corretude teórica:** pela concatenação `C(σ⊕σ') = C(σ) + W(σ')·(T(σ)+e) + C(σ')`,
movimentos em footprints disjuntos alteram cada um só o `C` (e talvez o `T`) do próprio
segmento, e essas alterações entram de forma aditiva pelos termos `W(·)·T(·)`, sem termo
cruzado. Aplicá-los juntos equivale a aplicá-los em sequência.

**Implementação**, aditiva: versões `_multi` de cada vizinhança em
[`src/neighborhoods.cpp`](../../src/neighborhoods.cpp) e `RVND_Multi` em
[`src/rvnd.cpp`](../../src/rvnd.cpp), com `--rvnd-mode single|multi` em `gils_rvnd` e
`local_search`. O lote é escolhido por activity selection gulosa pelo fim do footprint
(maximiza a contagem de movimentos, não o ganho). Dois bugs foram corrigidos no caminho:

- A avaliação de cada movimento lê a posição imediatamente fora do footprint (a aresta de
  fronteira). Footprints adjacentes eram tratados como compatíveis e o lote piorava o
  custo (`cost_before=13621 → cost_after=13961`). Correção: exigir 1 posição de folga
  entre footprints.
- Com essa folga, um footprint começando na posição 0 era rejeitado; com o lote vazio o
  código ainda marcava progresso, gerando laço infinito. Corrigido, e nenhuma vizinhança
  marca progresso sem ter aplicado algo.

Depois da correção: `single` sobre a saída do `multi` nunca acha melhoria adicional
(`eil51`/`lin318`/`pr439`/`att532`), o stress test (reaplicar cada vizinhança duas vezes)
e o de perturbações repetidas tiveram 0 falhas, e o `gils_rvnd` completo roda sem travar.

## Resultados

Diagnóstico (valores já com a correção da folga):

| instância | estado | swap | 2opt | reinsertion | oropt2 | oropt3 |
|---|---|---|---|---|---|---|
| lin318 | fresh | ~61 | ~62 | ~61 | ~45 | ~36 |
| lin318 | perturbed | ~2,0 | ~2,9 | ~2,8 | ~2,3 | ~2,2 |
| pr439 | perturbed | ~1,8 | ~2,5 | ~2,8 | ~2,1 | ~2,1 |
| att532 | perturbed | ~2,4 | ~3,3 | ~3,3 | ~2,6 | ~2,4 |

Na comparação direta (mesma seed, mesmos `--imax`/`--iils`, `lin318`/`pr439`/`att532`),
o `multi` foi mais lento em todas as execuções, entre ~1,3x e ~2,3x, e a qualidade não
teve padrão. Instrumentação do motivo (2-opt, `lin318`, mesma seed):

| modo | passadas completas O(n²) | recomputes | custo final |
|---|---|---|---|
| single | 8 | 795 | 7.840.491 |
| multi | **144** | 143 | 8.563.550 (pior) |

## Por que não funcionou

O `multi` precisou de 18x mais varreduras completas para convergir. O `single` não
reinicia a varredura depois de aplicar um movimento: continua o mesmo laço `i,j` sobre as
estruturas já atualizadas, então uma passada aplica e encadeia dezenas de melhorias (795
recomputes em 8 passadas). O `multi` aplica um lote pequeno por passada (2–4 movimentos,
por causa da folga) e precisa recomeçar a varredura inteira para achar o próximo. Como
varredura e recálculo são da mesma ordem (ambos O(n²)), trocar poucos recálculos caros por
muitas varreduras caras é desfavorável. O `single` já captura o benefício do encadeamento
dentro de uma única varredura.

O caminho mais promissor era reduzir o custo do recálculo sem aumentar o número de
varreduras, um problema de estrutura de dados e não de estratégia de busca. Foi o que
[H16](h16-candidate-neighborhoods.md) fez depois (dados de subsequência), com `T`/`C`/`Cr` em O(n).

## Limitações

- A comparação de tempo e qualidade é de execuções pareadas avulsas, sem teste
  estatístico formal.
- O lote maximiza a contagem de movimentos, não o ganho total.

## Referências

- Araujo, Coelho & Marzulo (2020). A multi-improvement local search using dataflow and
  GPU to solve the minimum latency problem.
