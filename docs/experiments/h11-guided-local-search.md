# H11 — Guided Local Search (GLS) sobre RVND

Status: **encerrada. Implementado (`src/gls_rvnd.cpp`), tunado (sweep de λ,
correção MLP-aware, híbrido com kick de double-bridge) — em nenhuma das
~12 configurações testadas em `lin318` o GLS bateu o `gils_rvnd`. Platô
robusto a λ (idêntico bit-a-bit entre 3k e 13k iterações no melhor λ),
não resolvido por nenhuma das duas ideias de correção testadas (seções 5 e
8, ambas pioraram). Sem teste estatístico formal — a calibração já foi
suficientemente clara e consistente pra não justificar o investimento.**

## 1. Motivação

Depois de H1-H10 mostrarem que qualquer mecanismo que muda *onde* a busca
reinicia (perturbação, recombinação, LNS, combinação de movimentos) sob a
mesma função de custo acaba sendo absorvido pelo RVND, pesquisamos um
mecanismo que muda *o que* a busca está otimizando: **Guided Local Search**
(Voudouris & Tsang, 1997) — é o componente de intensificação usado pelo
GQPSO (Jmal, Haddar & Chabchoub 2025, já citado na pesquisa de H8) para
justamente este problema (MLP/TRP).

## 2. Mecanismo

Depois que o RVND converge, penaliza-se a aresta de maior "utilidade" da
rota atual (`utilidade = distância_real(u,v) / (1 + penalidade(u,v))` —
formulação clássica de GLS), incrementando sua penalidade. A busca local
seguinte roda sobre uma matriz de distância "guia" (`guideDist = distância
real + λ·penalidade`), nunca sobre a distância real — o RVND, sem nenhuma
modificação, simplesmente passa a evitar aquela aresta. A qualidade real é
sempre calculada separadamente (soma cumulativa de latência direta em O(n)
sobre a distância verdadeira), nunca contaminada pela penalidade.

Implementação em [`src/gls_rvnd.cpp`](../../src/gls_rvnd.cpp) (binário
novo, não mexe em `solution.cpp`/`neighborhoods.cpp`/`rvnd.cpp`): como
`T`/`C`/`Cr` são inteiramente derivados de `Solution::fDist`, bastou trocar
o ponteiro `fDist` entre a matriz real e uma cópia penalizada e chamar
`calculateStructures()` de novo — reaproveita `RVND()` sem nenhuma mudança.
`λ` é calibrado uma vez (`λ = lambda_alpha · custo_do_primeiro_ótimo /
(n-1)`, convenção clássica de GLS), CLI: `--iterations`, `--lambda-alpha`,
`--construction-alpha`, `--seed`.

## 3. Corretude

Determinístico com `--seed`. Rota sempre permutação válida (checado em
`eil51`: 51 nós, sem duplicados).

## 4. Calibração em `lin318` (sem poder estatístico ainda — 1 seed)

| configuração | resultado |
|---|---|
| RVND puro (1 construção + RVND, sem GLS) | 6.252.079 |
| `gils_rvnd --imax 10 --iils 100` (baseline, 108s) | **5.562.365** |
| `gls_rvnd --iterations 3000` (λ_alpha=0,3, ~24s) | 5.694.082 |
| `gls_rvnd --iterations 13000` (mesmo λ, ~120s) | 5.694.082 (idêntico — platô) |
| `gls_rvnd` com λ_alpha=0,05 (penalidade mais fraca), 5000 iters (~44s) | 5.724.571 (ainda caindo, não platô claro) |

GLS melhora bastante sobre RVND puro sem nenhum mecanismo de escape
(6,25M → ~5,69M, ~9% de ganho — confirma que o mecanismo básico funciona),
mas **não fecha a distância pro baseline `gils_rvnd`** (~2,4% pior com
λ=0,3, ~2,9% pior com λ=0,05) dentro de um orçamento de tempo comparável, e
com λ=0,3 trava num platô idêntico entre 3.000 e 13.000 iterações (zero
ganho em 10.000 iterações extras) — mesmo padrão do platô de convergência
encontrado em H8/DBMEA-lite.

## 5. Tentativa de correção MLP-específica — piorou

Hipótese: a utilidade clássica de GLS (`distância/(1+penalidade)`) ignora
que, no MLP, uma aresta no início da rota pesa muito mais no custo total
(multiplicada por quantos clientes vêm depois dela) do que uma perto do
fim — a mesma lógica de T/C/W explorada em H10. Testamos
`utilidade = distância · (clientes_restantes_depois) / (1+penalidade)`.

**Resultado: piorou**, não melhorou — `best` estagnou em 5.752.634 (pior que
5.694.082 da versão clássica) e o custo real oscilou de forma muito mais
violenta entre iterações (picos de até 6,65M, contra no máximo ~6,26M na
versão clássica). Efeito provável: pesar por posição faz a penalização
recair quase sempre em arestas do início da rota, causando reestruturações
muito mais disruptivas a cada iteração em vez de ajustes finos — o oposto
do que se queria. **Achado honesto e um pouco contraintuitivo**: a
formulação clássica (cega à posição) generaliza melhor pro MLP do que a
versão "consciente da posição" que parecia mais natural.

## 6. Interpretação

GLS funciona parcialmente (bate RVND puro por uma margem real) mas ainda
não bate o `gils_rvnd` com o rigor de perturbação double-bridge + ILS que já
existe. O platô com λ maior sugere que penalizar 1 aresta por iteração com
passo fixo perde força de diversificação depois de certo ponto — mesmo
tipo de problema do H8 (mecanismo de diversificação fraco demais pra
competir com o que já existe, uma vez que o "ótimo mais fácil" já foi
encontrado). λ menor adia o platô mas ainda não fechou a distância na janela
de tempo testada.

## 7. Sweep de λ e platô confirmado com orçamento maior

Sweep de `--lambda-alpha` em `lin318`, 3000 iterações cada (mesma seed):

| λ_alpha | λ efetivo | custo final | iters melhorando |
|---|---|---|---|
| 0,30 | 5916,79 | 5.694.082 | 45 |
| 0,15 | 2958,40 | 5.715.317 | 49 |
| **0,10** | **1972,26** | **5.649.164** | 48 |
| 0,05 | 986,13 | 5.824.601 | 21 |
| 0,02 | 394,45 | 5.827.217 | 57 |
| 0,01 | 197,23 | 5.725.016 | 66 |

Não é monotônico — λ=0,1 é o melhor ponto encontrado (não os extremos).
Rodando λ=0,1 com **13.000 iterações** (~117s, orçamento comparável ao
`gils_rvnd`): custo final **idêntico bit-a-bit** a 3000 iterações
(5.649.164, `IMPROVING_ITERS=48` nos dois) — confirma que o platô não é
sensível a λ dentro da faixa testada, é estrutural: penalizar 1 aresta por
iteração para de encontrar território útil novo depois de um certo ponto,
qualquer que seja o passo de penalidade.

## 8. Híbrido GLS + kick de double-bridge — piorou

Tentativa de quebrar o platô combinando os dois mecanismos: a cada `N`
iterações de GLS, aplicar um double-bridge na solução atual antes de
continuar (implementado via `--kick-every N` em `gls_rvnd.cpp`). Testado
com λ=0,1 (o melhor ponto do sweep), `N` ∈ {50, 100, 200, 500}, 3000
iterações:

| kick-every | custo final |
|---|---|
| (nenhum, GLS puro) | **5.649.164** |
| 50 | 5.681.060 |
| 100 | 5.738.637 |
| 200 | 5.735.503 |
| 500 | 5.817.719 |

**Piorou em todos os intervalos testados** — o kick aleatório atrapalha em
vez de ajudar. Explicação provável: este `gls_rvnd` não tem critério de
aceitação/retorno-ao-melhor (diferente do `gils_rvnd`, que só aceita um
double-bridge se a reconvergência subsequente não piorar, voltando pro
melhor conhecido caso contrário) — aqui a busca sempre continua a partir de
onde parou, então um kick ruim nunca é descartado, só soma ruído ao
processo guiado.

## 9. Recomendação

Depois de tunar λ (6 valores), confirmar que o platô persiste com 4x mais
iterações no melhor λ, testar a correção MLP-aware (piorou, seção 5), e
testar o híbrido com kick (piorou em todos os intervalos, seção 8) — **4
tentativas de tuning barato, nenhuma fechou a distância pro `gils_rvnd`**
(melhor resultado: 5.649.164 vs 5.562.365, ~1,6% pior, em `lin318`, 1
seed). O padrão já não é mais "ainda pode estar melhorando" (como parecia
antes do sweep) — é um platô robusto a λ, a peso por posição, e a kicks.

Não recomendo mais tuning barato nesta forma. Próximas opções, se algum dia
retomado, exigiriam mudança estrutural (não paramétrica): adicionar
critério de aceitação/retorno-ao-melhor antes do kick (em vez de só somar
mais um parâmetro), ou penalizar várias arestas por iteração em vez de uma.
Dado o padrão da sessão (H9/H9b/H9c e H10 também pararam em platôs
parecidos), a linha de "diversificar melhor em cima do RVND fixo" já foi
testada de várias formas distintas (perturbação, LNS, combinação de
movimentos, penalidade de aresta) sem sucesso — encerrar H11 e considerar
se vale mudar de eixo por completo (ex.: vizinhança de busca local mais
forte, não só melhor forma de escapar da mesma).
