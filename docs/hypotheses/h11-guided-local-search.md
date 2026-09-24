# H11 — Guided Local Search (GLS) sobre RVND

**Veredito: refutada, sem teste estatístico formal.** Em nenhuma das ~12 configurações
testadas em `lin318` (1 seed) o GLS bateu o `gils_rvnd`: o melhor resultado, com
λ_alpha=0,10, foi 5.649.164 contra 5.562.365 (~1,6% pior), e é um platô idêntico bit a
bit entre 3.000 e 13.000 iterações. A utilidade ponderada por posição e o híbrido com
kick de double-bridge pioraram. A calibração foi clara o bastante para não justificar um
lote pareado. Não adotado.

## Hipótese

[H1](h1-adaptive-diversification.md)–[H10](h10-dynasearch.md) mostraram que mudar
*onde* a busca reinicia, sob a mesma função de custo, acaba absorvido pelo RVND. O GLS
(Voudouris & Tsang, 1997) muda *o que* a busca otimiza, penalizando arestas; é o
componente de intensificação do GQPSO (Jmal, Haddar & Chabchoub, 2025), já aplicado ao
MLP/TRP.

## O que foi testado

Depois que o RVND converge, a aresta de maior utilidade da rota
(`distância_real(u,v) / (1 + penalidade(u,v))`, formulação clássica) tem a penalidade
incrementada. A busca seguinte roda sobre a matriz guia
`guideDist = distância real + λ·penalidade`, e o RVND, sem modificação, passa a evitar
aquela aresta. O custo real é sempre recalculado à parte sobre a distância verdadeira.
Como `T`/`C`/`Cr` derivam inteiramente de `fDist`, basta trocar o ponteiro da matriz e
recalcular as estruturas. `λ = lambda_alpha · custo_do_primeiro_ótimo / (n-1)`.

Binário novo [`src/gls_rvnd.cpp`](../../src/gls_rvnd.cpp): `--iterations`,
`--lambda-alpha`, `--construction-alpha`, `--seed`, e `--kick-every N` para o híbrido.

## Resultados

Tudo em `lin318`, 1 seed.

| configuração | resultado |
|---|---|
| RVND puro (1 construção + RVND, sem GLS) | 6.252.079 |
| `gils_rvnd --imax 10 --iils 100` (baseline, 108s) | **5.562.365** |
| `gls_rvnd --iterations 3000` (λ_alpha=0,3, ~24s) | 5.694.082 |
| `gls_rvnd --iterations 13000` (mesmo λ, ~120s) | 5.694.082 (idêntico — platô) |
| `gls_rvnd` com λ_alpha=0,05 (penalidade mais fraca), 5000 iters (~44s) | 5.724.571 (ainda caindo, não platô claro) |

O GLS ganha ~9% sobre o RVND puro (o mecanismo básico funciona), mas fica ~2,4% (λ=0,3)
e ~2,9% (λ=0,05) acima do baseline.

**Sweep de λ** (3000 iterações cada):

| λ_alpha | λ efetivo | custo final | iters melhorando |
|---|---|---|---|
| 0,30 | 5916,79 | 5.694.082 | 45 |
| 0,15 | 2958,40 | 5.715.317 | 49 |
| **0,10** | **1972,26** | **5.649.164** | 48 |
| 0,05 | 986,13 | 5.824.601 | 21 |
| 0,02 | 394,45 | 5.827.217 | 57 |
| 0,01 | 197,23 | 5.725.016 | 66 |

Não é monotônico. Com λ=0,1 e 13.000 iterações (~117s) o custo final é idêntico bit a
bit ao de 3000 (5.649.164, `IMPROVING_ITERS=48` nos dois).

**Utilidade ponderada por posição**
(`distância · clientes_restantes_depois / (1+penalidade)`): o melhor estagnou em
5.752.634, e o custo real oscilou muito mais (picos de até 6,65M, contra ~6,26M na versão
clássica).

**Híbrido com kick** (λ=0,1, 3000 iterações):

| kick-every | custo final |
|---|---|
| (nenhum, GLS puro) | **5.649.164** |
| 50 | 5.681.060 |
| 100 | 5.738.637 |
| 200 | 5.735.503 |
| 500 | 5.817.719 |

## Por que não funcionou

- **Platô estrutural:** penalizar uma aresta por iteração, com passo fixo, para de
  encontrar território novo depois de certo ponto, qualquer que seja λ. λ menor só adia o
  platô. É o mesmo tipo de limite de [H8](h8-dbmea-population.md): uma diversificação
  fraca demais para competir com o double-bridge + ILS depois que o ótimo mais fácil já
  foi encontrado.
- **Peso por posição:** no MLP uma aresta no início da rota pesa mais (multiplicada pelos
  clientes que vêm depois, a lógica de T/C/W de H10). Mas pesar a utilidade por posição
  faz a penalidade recair quase sempre no início da rota, provocando reestruturações
  disruptivas em vez de ajustes finos. A formulação clássica, cega à posição, se sai
  melhor.
- **Kick:** o `gls_rvnd` não tem critério de aceitação nem retorno ao melhor (o
  `gils_rvnd` descarta um double-bridge que piora). Aqui a busca sempre continua de onde
  parou, e um kick ruim só soma ruído ao processo guiado.

Continuam sem teste as mudanças estruturais: aceitação/retorno ao melhor antes do kick,
ou penalizar várias arestas por iteração.

## Limitações

- Uma instância (`lin318`) e uma seed; nenhum teste pareado.

## Referências

- Voudouris & Tsang (1997).
- Jmal, Haddar, Chabchoub (2025). GQPSO (Guided Quantum PSO) para o MLP/TRP.
