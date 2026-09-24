# H13 — MDM-GILS-RVND (mineração de segmentos consecutivos)

> Os scripts e dados brutos em `scripts/` citados neste documento foram removidos do
> repositório e estão preservados na tag git `archive/h-scripts`
> (`git show archive/h-scripts:scripts/<arquivo>`).

Status: **ENCERRADA — nula, com a mineração real (FPMax*, hoje via a lib C++
`external/fpmax` — ver seção 2.2 —, antes via `mlxtend`)
corretamente implementada e testada com poder estatístico completo em
`lin318`/`pr439`/`att532` (N=20/15/10). Resultado: nulo, levemente
inclinado pra pior (agregado -0,02%, 12W/12T/21L, p=0,163). Custo de
tempo neutro (a mineração não pesa no total). Ver seção 6 (resultado
final) e seção 7 (o que ficou sem testar: n=1000).**

## 1. Motivação

Pesquisa pelos 3 nomes do problema (MLP/TRP/DMP) achou
[Santana, Plastino & Rosseti — "Improving a State-of-the-Art Heuristic
for the Minimum Latency Problem with Data Mining"](https://arxiv.org/abs/1908.10705)
(arXiv:1908.10705), que faz exatamente o que nosso GRASP-AM/GILS-AM-RVND
tentou (`docs/experiments/grasp-am-large-scale.md`) — só que de um jeito
mais rico, com resultados publicados bem mais fortes.

Diferença central: nosso `construction_am` dá bônus na distância baseado
na **frequência de arestas isoladas** no pool de elite (uma aresta por
vez). O paper minera **itemsets frequentes maximais de arcos**, que
formam **segmentos consecutivos** (sub-caminhos inteiros, não arestas
soltas) via FPMax*, e insere o segmento inteiro de uma vez quando o
primeiro nó dele é escolhido durante a construção. Resultado reportado:
ganho de qualidade **e** velocidade, crescendo com `n` — até 32,78% mais
rápido e 19/20 melhores soluções em n=1000, 32 novos melhores-conhecidos.
Isso é estruturalmente diferente do nosso resultado (empate em qualidade,
só velocidade) — a hipótese é que a mineração de segmentos (não de
arestas isoladas) é o que gera o ganho de qualidade que nossa versão
simplificada nunca alcançou.

## 2. Primeira versão: proxy simplificado (substituído — seção 2.1)

A primeira versão evitava implementar um minerador geral de itemsets
frequentes maximais (FPMax*) — em vez disso, contava frequência de cada
**arco individual** no pool de elite e extraía sequências maximais de
arcos consecutivos **individualmente** frequentes. Questionado se dava
pra usar uma implementação de FPMax* já pronta em vez de inventar um
proxy — resposta: sim, dava, e o proxy tinha uma lacuna de corretude
real, não só "menos sofisticado": suporte de itemset é monotonicamente
não-crescente com o tamanho do itemset (fechamento por baixo/Apriori) —
uma cadeia de arcos cada um individualmente frequente **não garante**
que a combinação inteira apareça, como conjunto, em ≥`sup_min` das
soluções de elite. O proxy assumia essa herança sem verificar.

## 2.1 Correção: FPMax* de verdade (`mlxtend`)

`scripts/fpmax_mine.py` usa `mlxtend.frequent_patterns.fpmax` (instalado
sob demanda via `uv run --with mlxtend --with pandas` — testado e
funcionando). Cada solução de elite vira uma "transação" de arcos
(tokens `"u_v"`); o script roda mineração de itemset frequente maximal de
verdade e escreve os itemsets minerados. `mine_patterns()` em
`src/mdm_gils_rvnd.cpp` escreve as transações num arquivo temporário,
chama o script via `system()`, lê os itemsets minerados de volta, e
**reconstrói as Consecutive Arc Lists** encontrando, dentro de cada rota
de elite, as sequências maximais de arcos consecutivos que são todos
membros de um itemset minerado (agora com suporte conjunto verificado de
verdade, não assumido).

Mineração acontece só algumas vezes por execução (toda vez que o elite
set muda, na fase 2) — overhead do subprocesso (~0,7s por chamada, com
dependências em cache) é desprezível frente ao tempo total de execução
(100+ segundos). Verificado: os segmentos encontrados pela versão real
têm magnitude parecida à do proxy anterior (6-22 nós em `lin318`) — bom
sinal de que o proxy não estava catastroficamente errado na prática,
mas agora o mecanismo é fiel ao paper.

## 2.2 Mineração em C++ (FPmax-LIB) — substitui o subprocesso Python

A mineração agora roda **em memória**, via a
[FPmax-LIB](https://github.com/marcelorhmaia/FPmax-LIB) (MIT), que empacota
a implementação original do FPmax* de Grahne & Zhu (a mesma do
[FIMI](http://fimi.uantwerpen.be/src) que o paper usa) como biblioteca
chamável. Fontes vendorizados sem modificação em `external/fpmax/`,
compilados pelo nosso `Makefile` com `-DMFI`; o acesso passa por
`src/fpmax_mining.cpp` / `include/fpmax_mining.h` (shim necessário porque
`fp_tree.h` declara uma `class stack` global *e* faz `using namespace std`,
o que torna o nome ambíguo em qualquer arquivo que já tenha incluído
`<stack>`).

Convenções copiadas da integração de referência do mesmo autor,
[MDM-HGS-CVRP](https://github.com/marcelorhmaia/MDM-HGS-CVRP)
(`Program/Population.cpp::mineElite`): arco `(u,v)` é o item `u*n + v`;
`minsup` é **absoluto**, `max(2, supMin × |elite|)`; o número de padrões é o
`nlargest` da própria lib; e as Consecutive Arc Lists são remontadas
**encadeando os arcos do itemset entre si** (em vez de varrer uma rota de
elite procurando corridas de arcos, como a versão anterior fazia).

**Equivalência verificada** com o exemplo de ground truth do próprio paper
(Seção 4.1: `D={{1,2,3,4,5},{1,2,3,5},{2,3,4,5},{1,2,5},{2,3,4}}`,
`supmin=80%`): a lib C++ retorna exatamente `{2,3}` e `{2,5}`, idêntico ao
`mlxtend` e ao que o paper afirma.

**Ganho de velocidade** (mesma seed, mesmos custos de solução):

| instância | antes (subprocesso Python) | agora (C++ em memória) |
|---|---:|---:|
| Salehipour n=10 | ~2,1s | **4,3ms** |
| Salehipour n=50 | ~2,9s | **0,36s** |
| `eil51` | ~1,9s | **0,49s** |
| `lin105` | ~3,1s | 2,41s |
| `att532`, orçamento de 15s | **69,6s** (estourou 4,6x) | **15,0s** (respeita) |

O último caso era o problema prático: o subprocesso não era interrompível,
então o `mdm` estourava o orçamento no protocolo de tempo fixo (ver
[[fixed-time-protocol]]). Em `n=1000` a mineração roda com ~244MB de pico
(os ids de item chegam a ~10⁶ com o mapeamento `u*n+v`, e a lib aloca
arrays proporcionais ao maior id).

`scripts/fpmax_mine.py` deixou de ser chamado em runtime — fica no repo só
como registro da versão anterior e para reproduzir a checagem de
equivalência.

**Ressalva para os resultados já publicados**: todos os lotes de H13 e das
comparações Salehipour (`n≤500`, `n=1000`) foram gerados com a versão
Python. Os padrões minerados são equivalentes, mas a remontagem das
Consecutive Arc Lists mudou (encadeamento do itemset vs. varredura de rota
de elite), então os números antigos não são bit-a-bit reprodutíveis com o
código atual.

## 3. Implementação

Novo binário [`src/mdm_gils_rvnd.cpp`](../../src/mdm_gils_rvnd.cpp)
(não uma flag em cima de `gils_rvnd`/`gils_am_rvnd` — nomes/identidade
algorítmica distintos, convenção do projeto):

- `mine_patterns(elite, supMin, maxPatterns)`: conta frequência de arco,
  extrai sequências maximais de arcos consecutivos frequentes por
  solução de elite, deduplica por sequência de nós, mantém as
  `maxPatterns` mais longas.
- `construction_mdm(...)`: mesmo RCL/alpha semi-guloso de `construction()`,
  mas quando o candidato escolhido é o primeiro nó de um segmento minerado
  **ainda totalmente não-visitado**, insere o segmento inteiro de uma vez
  em vez de só aquele nó (Algorithm 5 do paper).
- `mdm_gils_rvnd(...)`: laço de duas fases — primeira metade das
  iterações de `I_max` roda `GILS-RVND` padrão (constrói o elite set);
  da segunda metade em diante, re-minera **toda vez que o elite set muda**
  (a parte "multi-mining"/adaptativa, MDM vs. DM de fase única) e usa
  `construction_mdm` em vez de `construction()`.
- CLI: `--imax 10 --iils 100 --pool 10 --sup-min 0.70 --max-patterns 5 --seed N`
  — defaults batem com os parâmetros do paper (elite=10, suporte
  mínimo=70%, 5 padrões máximos).

## 4. Corretude

- Determinístico com `--seed`; rota sempre permutação válida (checado em
  `eil51`: 51 nós, sem duplicados).
- **Mineração confirmada funcionando de verdade** (build instrumentado,
  descartado depois): em `lin318`, a partir da iteração 6 (metade de
  `--imax 12`), a cada atualização do elite set a mineração encontra 5
  segmentos reais, de tamanho 6 a 22 nós — não fica vazia
  silenciosamente, o mecanismo central está de fato funcionando.

## 5. Calibração inicial — inconclusiva

3 seeds em `lin318` (`--imax 10 --iils 100`): 2 empates, 1 derrota pro
baseline. 3 seeds em `att532` (`--imax 3 --iils 100`, rodado
**concorrentemente** com o lote de H12b, tempos não confiáveis): 1
vitória, 1 derrota, 1 empate para o `mdm`.

Amostra pequena demais pra concluir qualquer coisa — mas isso também é
consistente com o próprio paper: a tabela de resultados deles mostra
efeito modesto em instâncias médias (120-262 nós: 49/89 melhores
soluções, ~55%) e só fica forte a partir de instâncias grandes (500+) e
muito forte em n=1000. `lin318`/`att532` (318/532 nós) ficam bem na
fronteira "médio/grande" da tabela do paper — não é surpresa que o
sinal ainda não apareça claramente numa amostra pequena aqui.

## 6. Lote pareado com o proxy simplificado (seção 2, substituído)

**Obtido com a versão proxy (seção 2), antes da correção para FPMax*
real (seção 2.1) — mantido por registro histórico, não é mais o estado
atual do código.** Resultado (interrompido por decisão do usuário):

`scripts/h13_mdm_test.py`, mesma escala de instância/imax/iils do teste
original de H12a. Interrompido depois de `lin318` completo (N=20),
`pr439` completo (N=15) e `att532` com só 1 seed (insuficiente — excluído
da leitura abaixo):

```
instance      n  mean_rel%      w/t/l   sign_p   time+%
lin318       20     0,0026 5/8/7          0,774     -4,0
pr439        15     0,0530 6/3/6          1,000      8,2
```

**Nulo — ruído puro.** `pr439` é uma moeda exata (6W/3T/6L, p=1,000);
`lin318` não chega perto de significância (p=0,774). Tempo: sem
diferença real (-4% a +8%, dentro do ruído de medição). Um outlier de
tempo (`pr439` seed 10: `mdm` registrou ~3h16 num único run, custo idêntico
ao baseline) foi excluído da média de tempo — mesmo padrão de artefato de
relógio do WSL2 já visto antes nesta sessão, não uma lentidão real do
algoritmo.

Isso é consistente com a própria tabela do paper: nas escalas "média"
(120-262 nós) o placar de melhores soluções deles já era só 49/89 (~55%,
mal acima de moeda) — `lin318`/`pr439` (318/439 nós) ficam bem na mesma
faixa onde o efeito relatado no próprio paper já é fraco. Não é evidência
de que a reimplementação esteja errada (a mineração funciona de verdade,
seção 4) — é mais provável que estejamos simplesmente na faixa de `n`
onde nem o paper original mostra vantagem clara.

## 7. Resultado final (mineração real, FPMax*/`mlxtend`)

Depois de corrigir a mineração para o FPMax* de verdade (seção 2.1),
verificado antes em instâncias pequenas da lista de `run_experiments.py`
(`st70`/`rat99`/`kroD100`/`lin105`/`pr107`/`pr226`: empate exato em todos
os seeds, mesmo padrão de "n≲226 é fácil demais pra diferenciar" já
estabelecido na sessão; só `rat195` mostrou alguma variação, 2W/1L pro
mdm), lote pareado completo (`scripts/h13_mdm_test.py`, dados brutos:
`scripts/h13_mdm_results.json`) em `lin318`/`pr439`/`att532` (N=20/15/10,
mesma escala de H12a):

```
instance      n  mean_rel%      w/t/l   sign_p   time+%
lin318       20    -0,0215 4/7/9          0,267      1,4
pr439        15     0,0039 5/3/7          0,774      8,9
att532       10    -0,0673 3/2/5          0,727     -1,9
AGREGADO     45    -0,0232 12/12/21       0,163    (neutro)
```

**Nulo, levemente inclinado pra pior** (não significativo — todo p≥0,163,
`mean_rel%` negativo em 2 das 3 instâncias). Custo de tempo neutro (a
mineração via subprocesso não pesa no total, como esperado — poucas
chamadas por execução). Um outlier de tempo (`lin318` seed 2: ~7,6M ms
num único run) foi excluído da média de tempo — mesmo artefato de
relógio do WSL2 já visto várias vezes nesta sessão, custo idêntico ao
baseline confirma que não é lentidão real.

## 8. Recomendação

**Encerrada.** Mesmo com a mineração corrigida para o algoritmo real do
paper (não mais o proxy), o resultado em `n=318-532` continua nulo — e
isso é consistente com a própria tabela do paper, que já mostra efeito
fraco (~55% de vitórias) nessa faixa "média/grande" antes de virar forte
em n≥1000. Não recomendado adotar `mdm_gils_rvnd`. Único teste que ainda
poderia reabrir a questão — não feito, prioridade baixa dado o padrão já
bem estabelecido de nulos nesta sessão — é `rand1000` (n=1000, gerada
para H8), onde o paper reporta o efeito mais forte (19/20 melhores
soluções, 32,78% mais rápido).
