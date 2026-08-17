# H1 — Diversificação adaptativa

Status: **ENCERRADA — sintoma confirmado, mecanismo testado não melhora o
GILS-RVND.** A escalada ingênua por tempo de estagnação (seção 5) foi
refutada logo (perde sistematicamente na instância com folga real). O
controle homeostático por distância de arestas (seção 10, inspirado em
Máximo & Nascimento / AILS-PR) corrigiu esse defeito específico, mas o lote
noturno com poder estatístico real (seção 11: N=20/15/10 em
`lin318`/`pr439`/`att532`) fecha o veredito: efeito indistinguível de ruído
em toda instância (p ≥ 0,30 em todas, a maioria ≥ 0,80; magnitude média
sempre < 0,1%). **Não adotar.** O sintoma que motivou a hipótese é real
(seção 2), mas nenhum dos dois mecanismos testados aqui o converte em ganho
de qualidade.

## 1. Hipótese

Se a perturbação double-bridge do GILS-RVND tem intensidade fixa (sempre 3
cortes / 4 segmentos, independente do estado da busca), então controlar essa
intensidade em função da estagnação (aumentar quando a busca trava, reduzir
quando progride) reduziria o gap médio sem custo de tempo relevante.

Sintoma que a justifica: a curva de custo cai rápido no início do ILS e
depois estagna cedo — muito do orçamento de iterações é gasto sem gerar
nenhuma melhoria adicional.

## 2. Diagnóstico do sintoma (antes de implementar qualquer coisa)

Antes de construir o mecanismo adaptativo, validamos se o sintoma realmente
ocorre nesta base de código. Instrumentamos `gils_rvnd` com uma flag `-v`
(já citada no README, mas até então ignorada pelo parser) que imprime, a
cada melhoria aceita dentro do ILS, uma linha
`TRACE OUTER=<i> STEP=<passo> COST=<custo> ROUTE=<rota>`.

Rodamos `--imax 1` com orçamentos (`--iils`) muito maiores que o padrão do
artigo (100) — até 3000 — para ver até onde a busca consegue ir "deixada
rodando" com a mesma intensidade de perturbação.

| instância | n | nº melhorias | passo da última melhoria (L_last) | orçamento testado | ganho% total |
|---|---|---|---|---|---|
| eil51 | 51 | 9 | 97 | 3000 | 7.82 |
| st70 | 70 | 10 | 40 | 3000 | 5.44 |
| pr76 | 76 | 4 | 24 | 3000 | 4.02 |
| kroA100 | 100 | 7 | 142 | 3000 | 3.00 |
| lin105 | 105 | 3 | 5 | 3000 | 6.59 |
| pr226 | 226 | 7 | 182 | 3000 | 2.12 |
| lin318 | 318 | 17 | 605 | 3000 | 5.80 |
| pr439 | 439 | 22 | 270 | 400 | 6.77 |
| att532 | 532 | 33 | 733 | 150 | 6.29 |

**Achado**: `L_last` (passo da última melhoria) é uma fração pequena de
qualquer orçamento generoso. Em `lin105`, a última melhoria acontece no
passo 5 de 3000 — 99,8% de um orçamento 30x maior que o padrão do artigo não
produz ganho algum. O padrão se repete em quase toda instância testada.

**Conclusão do diagnóstico**: o sintoma é real e forte — a curva cai rápido e
estagna muito antes de esgotar um orçamento generoso, sob perturbação de
intensidade fixa. Isso valida a premissa de H1 e justifica testar o remédio
proposto.

## 3. Implementação

Mudança em [`src/gils_rvnd.cpp`](../../src/gils_rvnd.cpp), aditiva e
retrocompatível (comportamento padrão idêntico ao anterior quando as novas
flags não são usadas):

- `double_bridge_once`: a aplicação original de double-bridge (renomeada; a
  lógica não mudou).
- `perturb(sol, gen, strength)`: aplica `double_bridge_once` `strength`
  vezes em sequência. `strength = 1` reproduz o comportamento original
  exato.
- `perturbation_strength(adaptive, iterILS, stagnationStep, maxStrength)`:
  o agendamento adaptativo. Reaproveita o contador de estagnação que já
  existia no algoritmo (`iterILS`, que já reseta a 0 a cada melhoria) — não
  foi necessário nenhum estado novo:

  ```cpp
  strength = min(1 + iterILS / stagnationStep, maxStrength)
  ```

  Ou seja: começa em 1 (idêntico ao fixo), sobe 1 nível a cada
  `stagnationStep` iterações consecutivas sem melhoria, até o teto
  `maxStrength`. Como `iterILS` reseta a 0 assim que há uma melhoria, a força
  também cai de volta para 1 automaticamente — "reduz quando progride,
  aumenta quando trava" sai de graça do mecanismo de estagnação que o próprio
  ILS já mantinha.
- Novas flags de CLI em `gils_rvnd`: `--adaptive` (liga o agendamento;
  padrão desligado = comportamento antigo), `--stagnation-step` (padrão 5),
  `--max-strength` (padrão 5), `--seed N` (RNG determinístico — necessário
  para o teste pareado abaixo; sem ela, comportamento aleatório como antes).
  A saída agora também imprime `PERT_MODE fixed|adaptive`.

## 4. Metodologia do teste A/B

Comparação **pareada**: para cada instância e cada seed, roda-se o mesmo
binário duas vezes com o **mesmo** `--seed` — uma sem `--adaptive`
(baseline) e uma com `--adaptive`. Como o RNG é determinístico e a mesma
seed governa a construção e o RVND em ambos os modos, a única fonte de
diferença entre os dois runs é a política de perturbação — isolando o efeito
que queremos medir em vez de comparar duas amostras aleatórias
independentes.

Parâmetros: `I_max`/`I_ILS` = padrão do artigo (10/100) nas instâncias até
`pr226`; reduzidos em `lin318` (`I_max=5`) por custo computacional dentro do
orçamento desta sessão. `stagnation-step=5`, `max-strength=5` (defaults,
não foram ajustados/tunados). Script:
[`scripts/h1_ab_test.py`](../../scripts/h1_ab_test.py), análise:
[`scripts/h1_ab_analysis.py`](../../scripts/h1_ab_analysis.py), dados brutos:
`scripts/h1_ab_results.json`.

## 5. Resultado

| instância | n pares | custo médio (fixo) | custo médio (adaptativo) | diff média | win/tie/loss | p (teste de sinal) | tempo médio fixo (ms) | tempo médio adaptativo (ms) | overhead de tempo |
|---|---|---|---|---|---|---|---|---|---|
| eil51 | 20 | 9319.0 | 9319.0 | 0.000% | 0/20/0 | 1.000 | 480.9 | 821.0 | +70.7% |
| st70 | 20 | 19215.0 | 19215.0 | 0.000% | 0/20/0 | 1.000 | 944.3 | 1672.9 | +77.2% |
| pr76 | 20 | 3,322,660.0 | 3,322,660.0 | 0.000% | 0/20/0 | 1.000 | 1198.7 | 2322.8 | +93.8% |
| kroA100 | 15 | 958,013.0 | 958,013.0 | 0.000% | 0/15/0 | 1.000 | 3042.2 | 5753.4 | +89.1% |
| lin105 | 15 | 585,823.0 | 585,823.0 | 0.000% | 0/15/0 | 1.000 | 2472.6 | 4682.3 | +89.4% |
| pr226 | 8 | 7,100,308.0 | 7,100,308.0 | 0.000% | 0/8/0 | 1.000 | 37345.2 | 69639.4 | +86.5% |
| lin318 | 4 | 5,569,115.2 | 5,599,276.8 | **−0.541%** | 0/0/4 | 0.125 | 66101.9 | 69123.6 | +4.6% |

("win" = adaptativo estritamente melhor; "loss" = adaptativo estritamente
pior; diff média em % é relativa ao custo fixo.)

Dois achados, ambos desfavoráveis ao mecanismo testado:

1. **Em toda instância até n=226, fixo e adaptativo empatam exatamente em
   custo em 100% dos 98 pares testados** (0 wins, 0 losses em todas). O
   GILS-RVND já encontra a mesma solução (aparentemente ótima, consistente
   com o que o artigo original reporta para instâncias desse porte)
   independente da política de perturbação — não há gap para o mecanismo
   adaptativo recuperar. E como cada nível de força extra faz o RVND
   reconvergir de um estado mais perturbado, o adaptativo é sistematicamente
   **70–94% mais lento**, sem nenhum ganho de qualidade em troca.
2. **Em `lin318` — a única instância com folga real de otimização testada —
   o adaptativo perde em 4 de 4 seeds**, com gap médio de −0,54% (pior, não
   melhor). O teste de sinal não é conclusivo com apenas 4 pares
   (p=0,125), mas a direção é consistente nas 4 execuções e alinhada com o
   padrão de "nunca ajuda" das outras instâncias.

## 6. Interpretação

O **sintoma de H1 é real** (seção 2: a curva estagna cedo mesmo com
orçamento generoso). Mas o **remédio testado — escalar a força do
double-bridge em função da estagnação, com o agendamento `stagnationStep=5,
maxStrength=5` — não funciona**: é neutro-para-pior em qualidade e sempre
mais caro em tempo.

Hipótese de por que o agendamento específico falha:

- Nas instâncias pequenas/médias (≤226), GILS-RVND já bate no teto (ótimo
  ou muito próximo) com a perturbação fixa — não existe "estagnação
  recuperável" para o mecanismo explorar, só overhead computacional.
- Em `lin318`, onde existe folga (o custo final varia entre seeds, sinal de
  que nem toda execução acha o ótimo), a estratégia de escalar rápido demais
  (atinge o teto de 5 kicks simultâneos já em ~20 iterações de estagnação)
  parece destruir estrutura boa da rota mais rápido do que o RVND consegue
  reconstruir dentro do orçamento `I_ILS` restante — um double-bridge
  quíntuplo é uma perturbação muito mais violenta que o double-bridge
  simples do artigo, e a hipótese original não previa esse efeito colateral.

Isso **não refuta a ideia geral de perturbação adaptativa** — só refuta
*este* agendamento específico, não tunado. Um agendamento mais brando (ex.:
`max-strength=2` ou `stagnation-step` maior, ou uma métrica de força mais
fina que "kicks inteiros extras", como cortes mais próximos entre si em vez
de kicks completos empilhados) poderia se comportar diferente — mas isso é
especulação sem novo teste, não uma conclusão deste experimento.

## 7. Limitações

- Agendamento (`stagnationStep=5`, `maxStrength=5`) foi escolhido por
  plausibilidade, não por busca de hiperparâmetro — o resultado negativo
  pode refletir uma escolha ruim desses dois números, não uma falha
  estrutural da ideia de adaptar a intensidade.
- `lin318` — a única instância com sinal de melhoria possível — teve apenas
  4 pares e `I_max` reduzido (5 em vez de 10) por custo computacional; não
  testamos `pr439`/`att532` (instâncias ainda maiores, onde o artigo mostra
  gaps maiores e portanto mais folga) por o custo de tempo desta sessão não
  comportar múltiplas seeds pareadas nesse porte.
- Não testamos formas alternativas de "adaptar" a perturbação (variar o
  tamanho dos segmentos trocados em vez do número de kicks, por exemplo).

## 8. Recomendação (antes da pesquisa de literatura)

**Não adotar o mecanismo testado como está.** Se ainda houver interesse em
perturbação adaptativa como contribuição, os próximos passos que teriam
mais chance de mudar essa conclusão, em ordem de custo crescente:

1. Reduzir a agressividade do agendamento (`max-strength` menor, ex. 2–3;
   `stagnation-step` maior) e repetir o mesmo teste pareado em `lin318` —
   ver se um mecanismo mais brando deixa de piorar antes de decidir se ele
   também melhora.
2. Rodar o mesmo teste A/B em instâncias maiores (`pr439`, `att532`, e as de
   500–1000 clientes do artigo), onde há mais folga de otimização e
   qualquer efeito real do mecanismo teria mais chance de aparecer — fora de
   uma sessão interativa, em lote.
3. Se nada disso mudar o quadro, considerar H1 encerrada nesta forma e focar
   em H2 (path relinking), que teve evidência de sintoma mais específica em
   instâncias grandes.

## 9. Pesquisa de literatura — por que o mecanismo testado falhou e o que a literatura recomenda no lugar

Depois do resultado negativo, pesquisamos a literatura de ILS/VNS/GRASP
sobre controle de intensidade de perturbação, para diagnosticar *por que*
nosso agendamento falhou e o que a literatura já validou como alternativa.
Achado central: **o diagnóstico causal da seção 6 tem respaldo direto na
literatura** — o defeito não é "adaptar é ruim", é "adaptar com base em
quantas iterações se passaram, sem checar o efeito real da perturbação, é a
forma ingênua e não validada de fazer isso."

### 9.1 O que já existia (e o que faltava no nosso agendamento)

- **VNS clássico** (Mladenović & Hansen, 1997) já usa a ideia de "aumenta a
  vizinhança/força do shaking ao falhar, reseta ao melhorar" — a mesma lógica
  que implementamos. Mas na formulação padrão de VNS a escalada é limitada e
  cíclica (volta a k=1 ao atingir k_max, não fica "grudado" no teto), e mais
  importante: variantes mais robustas (ex. *Skewed VNS*) só aceitam o novo
  ponto se a vizinhança realmente trouxe uma solução distinta o bastante
  para justificar a perda de qualidade — ou seja, já constroem um *feedback
  de distância*, não só um contador de tempo. Nosso agendamento usava só o
  contador (`iterILS`), sem olhar se o kick estava de fato produzindo
  diversidade útil.
- **Benlic & Hao (2013)**, *"A Study of Adaptive Perturbation Strategy for
  Iterated Local Search"* (EvoCOP 2013, usado antes em Breakout Local
  Search): perturbação adaptativa que escolhe, dependendo do estado da
  busca, entre um kick **dirigido** (usa informação da busca, ex. elementos
  "críticos") e um kick **aleatório**, cada um em intensidades diferentes —
  reforça que "intensidade" sozinha (nosso caso) é só metade do design
  space; o *tipo* de perturbação importa tanto quanto a força.
- **XKICK** (kick "inteligente" para o TSP): em vez de cortes aleatórios do
  double-bridge, usa informação de comparação entre tours já visitados para
  decidir *onde* aplicar o kick — mostrou desempenho muito melhor que
  double-bridge aleatório. Sugere que, mesmo sem mexer na "força", só mudar
  *onde* os cortes acontecem (não uniformemente ao acaso) já é uma alavanca
  de melhoria separada da que testamos.
- **Reactive GRASP** (Prais & Ribeiro, 2000): não é sobre perturbação, é
  sobre o parâmetro α da construção GRASP, mas o princípio é o mecanismo
  mais citado de "auto-ajuste por histórico" em GRASP/ILS: mantém um
  conjunto discreto de valores candidatos, cada um com uma probabilidade de
  escolha proporcional à qualidade média das soluções que produziu no
  passado (não a um contador de estagnação). Esse princípio — escolher a
  força da perturbação por *recompensa histórica observada*, não por tempo
  decorrido — é diretamente portável para "força do double-bridge".
- **ALNS** (Ropke & Pisinger, 2006): generaliza a mesma ideia para um
  portfólio de operadores destroy/repair, com pesos atualizados por
  segmento de iterações a partir de um *score* de desempenho (achou novo
  melhor global, melhorou a solução corrente, ou nada) — roleta pondera a
  escolha do próximo operador pelos pesos. De novo: sinal de recompensa
  observada, não contagem de estagnação.
- **Máximo & Nascimento (2021)**, *"A hybrid adaptive Iterated Local Search
  with diversification control to the Capacitated Vehicle Routing Problem"*
  (AILS-PR, European Journal of Operational Research 294:1108–1119 — mesmo
  periódico do artigo-base deste projeto) — **a referência mais diretamente
  aplicável ao nosso caso**. O mecanismo de controle de diversificação:
  - Mede a distância estrutural `d(s, s_ref) = |E^s Δ E^s_ref|` entre a
    solução obtida após a busca local e uma solução de referência —
    exatamente a métrica de sobreposição de arestas que já usamos no
    diagnóstico de H2 (Jaccard/diferença simétrica de arestas).
  - Ajusta o **grau de perturbação** (no caso deles, número de vértices
    removidos num destroy-and-repair) para manter essa distância dentro de
    uma faixa-alvo de diversidade — não "aumenta sempre que estagna", mas
    "aumenta só se a diversidade realizada ficou abaixo do alvo, diminui se
    ficou acima". É um controle homeostático (malha fechada), não uma régua
    de escalonamento cega.
  - Adapta **também o critério de aceitação** em conjunto (baseado no fluxo
    de soluções aceitas ao longo da busca), não só a força da perturbação.
  - Combina isso com **Path Relinking** entre soluções — ligando diretamente
    à nossa H2. Em instâncias muito grandes o path relinking se mostrou
    lento demais, o que motivou a extensão **AILS-II** (Máximo, Cordeau &
    Nascimento, *INFORMS Journal on Computing* 36(4), 2024) para CVRP em
    larga escala — relevante porque nosso próprio teste também degradou em
    performance nas instâncias maiores.
- **Salehipour et al. (2011)** — já citado no artigo-base como o
  método concorrente ao GILS-RVND — usa *shaking* de VNS restrito a
  realocações entre clientes espacialmente próximos, uma restrição
  específica de domínio (localidade geográfica) que poderia se combinar com
  qualquer um dos mecanismos acima.

### 9.2 Por que isso explica o nosso resultado negativo

O nosso agendamento (`strength = min(1 + iterILS/5, 5)`) nunca olha para o
*efeito* da perturbação — só para quanto tempo já se passou sem melhoria.
Em `lin318`, isso significa: ao atingir o teto de 5 kicks empilhados
(~20 iterações de estagnação), o algoritmo aplica um double-bridge
quíntuplo *de qualquer forma*, mesmo que essa intensidade já esteja
destruindo mais estrutura do que o RVND consegue reconstruir no orçamento
restante — não há nenhum mecanismo para "perceber" isso e recuar. É
exatamente o problema que o controle por distância do AILS-PR foi desenhado
para evitar.

### 9.3 Caminho recomendado

Em ordem de esforço de implementação:

1. **Mais simples — reactive/histórico (Prais & Ribeiro adaptado)**: manter
   um conjunto discreto de forças `{1,2,3,4,5}`, cada uma com um peso
   atualizado pela qualidade média (ou taxa de melhoria) que produziu nas
   últimas N vezes que foi usada; escolher a força por roleta ponderada em
   vez de por `iterILS/5`. Reaproveita a mesma infraestrutura de `perturb`
   que já implementamos — só troca a regra de escolha de `strength`.
2. **Mais fiel à literatura mais próxima do nosso caso — controle por
   distância (Máximo & Nascimento / AILS-PR)**: calcular
   `d(s, s_ref) = |E^s Δ E^s_ref|` (arestas dirigidas, já implementado no
   script de H2) entre a solução pré-perturbação e a solução pós-RVND;
   manter uma faixa-alvo de diversidade (ex. em % de arestas trocadas);
   subir a força só se `d` ficou abaixo do alvo, descer se ficou acima. Mais
   trabalho, mas ataca exatamente a causa-raiz identificada na seção 9.2.
3. **Combinar com H2**: como o próprio AILS-PR já une controle de
   diversificação com path relinking no mesmo laço, esta é a leitura mais
   natural de continuidade: em vez de tratar H1 e H2 como iniciativas
   separadas, a literatura sugere um único mecanismo (AILS-PR-like) que
   endereça as duas hipóteses ao mesmo tempo — vale considerar essa fusão em
   vez de retestar H1 isoladamente com um agendamento só um pouco melhor.

## 10. Segunda iteração — controle por distância de arestas (estilo AILS-PR)

Implementamos e testamos a opção 2 da seção 9.3: em vez de escalar a força
da perturbação por tempo decorrido, medir a diversidade *realmente
alcançada* após cada ciclo de perturbação+RVND e usar isso para corrigir a
força para cima ou para baixo — um controle de malha fechada, não uma régua
cega.

### 10.1 Implementação

Mudança em [`src/gils_rvnd.cpp`](../../src/gils_rvnd.cpp):

- `edge_distance(tourA, tourB, n)`: conta quantos nós têm sucessor diferente
  entre duas rotas — proxy O(n) para `|E^s Δ E^s_ref|` (cada nó contribui no
  máximo uma aresta de saída num caminho Hamiltoniano, então essa contagem é
  proporcional à diferença simétrica de arestas usada no AILS-PR). Reaproveita
  a mesma ideia de comparação de arestas já usada no diagnóstico de H2.
- `PertMode` agora é um enum de 3 valores: `Fixed` (original), `Stagnation`
  (a escalada ingênua da seção 3, mantida para comparação), `Distance` (novo).
  CLI: `--pert-mode fixed|stagnation|distance` substitui a flag booleana
  `--adaptive` (o antigo `--adaptive` virou `--pert-mode stagnation`).
- Mecanismo `Distance`: a cada iteração do ILS, depois que `RVND` converge,
  mede-se `d = edge_distance(s, referenceTour)` — a distância entre a
  solução obtida e a rota que foi perturbada para chegar nela. Um alvo de
  diversidade `[targetMin, targetMax]` é definido como fração de `n`
  (`--target-min-pct 0.05`, `--target-max-pct 0.15` por padrão — 5%–15% dos
  nós com sucessor trocado). Regra de controle:

  ```cpp
  if (d < targetMin) strength = min(strength + 1, maxStrength);
  else if (d > targetMax) strength = max(strength - 1, 1);
  // caso contrário, mantém a força atual
  ```

  Diferente do mecanismo antigo, `strength` agora é uma variável de estado
  que persiste e é ajustada incrementalmente ao longo do ILS (não recalculada
  do zero por uma fórmula de `iterILS`) — sobe só quando o RVND está
  "desfazendo" a perturbação além do esperado (diversidade abaixo do alvo),
  desce quando a perturbação está sendo disruptiva demais (acima do alvo).

### 10.2 Metodologia

Mesmo teste pareado da seção 4, reaproveitando as **mesmas seeds e mesmas
instâncias** já usadas no experimento fixo-vs-estagnação (não foi necessário
re-rodar fixed/stagnation, já que o comportamento deles não mudou — só a
interface de CLI). Rodamos apenas o modo `distance` nessas seeds e
comparamos os três lado a lado. Script:
[`scripts/h1_distance_test.py`](../../scripts/h1_distance_test.py), análise:
[`scripts/h1_3way_analysis.py`](../../scripts/h1_3way_analysis.py), dados
brutos: `scripts/h1_3way_results.json`. Parâmetros de banda-alvo não foram
ajustados (usamos os defaults 5%–15%).

### 10.3 Resultado

| instância | n pares | estagnação: diff média | win/tie/loss | overhead tempo | distância: diff média | win/tie/loss | overhead tempo |
|---|---|---|---|---|---|---|---|
| eil51 | 20 | 0.000% | 0/20/0 | +70.7% | 0.000% | 0/20/0 | **+23.8%** |
| st70 | 20 | 0.000% | 0/20/0 | +77.2% | 0.000% | 0/20/0 | **+28.0%** |
| pr76 | 20 | 0.000% | 0/20/0 | +93.8% | 0.000% | 0/20/0 | **+30.6%** |
| kroA100 | 15 | 0.000% | 0/15/0 | +89.1% | 0.000% | 0/15/0 | **+38.3%** |
| lin105 | 15 | 0.000% | 0/15/0 | +89.4% | 0.000% | 0/15/0 | **+47.2%** |
| pr226 | 8 | 0.000% | 0/8/0 | +86.5% | 0.000% | 0/8/0 | **+41.3%** |
| lin318 | 4 | **−0.541%** | 0/0/4 | +4.6% | **−0.022%** | 1/1/2 | +31.0% |

("diff média" é `(custo_fixo − custo_variante)/custo_fixo`; positivo =
variante melhor que o fixo.)

Detalhe seed a seed em `lin318` (a instância que expôs o problema original):

| seed | fixo | estagnação | distância |
|---|---|---|---|
| 1 | 5,562,365 | 5,602,386 (pior) | 5,562,365 (**empate exato**) |
| 2 | 5,560,679 | 5,571,896 (pior) | 5,562,365 (pior, −0,03%) |
| 3 | 5,574,033 | 5,610,626 (pior) | 5,570,278 (**melhor, +0,07%**) |
| 4 | 5,579,384 | 5,612,199 (pior) | 5,586,386 (pior, −0,13%) |

Dois achados:

1. **Nas instâncias até n=226, o controle por distância empata em qualidade
   com o fixo em 100% dos pares (igual à estagnação) mas com bem menos
   overhead de tempo** — tipicamente metade do custo extra da estagnação
   (ex. `pr76`: +30,6% vs +93,8%; `lin105`: +47,2% vs +89,4%). Isso é
   consistente com a mecânica esperada: o controlador só aumenta a força
   quando a diversidade medida fica abaixo do alvo, então não fica escalando
   às cegas quando um único double-bridge já entrega diversidade suficiente.
2. **Em `lin318`, o defeito grave da estagnação desaparece**: em vez de
   perder em 4 de 4 seeds com −0,54% de gap médio, a distância empata
   exatamente em 1 seed, melhora o fixo em 1 (a primeira vez que qualquer
   variante testada supera o fixo neste experimento) e perde por margem
   pequena nas outras 2 — gap médio de −0,022%, 25x menor que o da
   estagnação. O overhead de tempo aqui (+31%) é maior que o da estagnação
   (+4,6%) nesta instância especificamente, então não é um "almoço grátis"
   completo, mas a troca qualidade/tempo é muito mais defensável que a da
   primeira tentativa.

### 10.4 Interpretação

O diagnóstico da seção 9.2 — "o mecanismo antigo nunca checava se a
perturbação estava produzindo diversidade útil" — se confirma diretamente:
trocar o gatilho de "tempo decorrido" para "diversidade medida" (a mesma
mudança que a literatura de AILS-PR já validou para CVRP) elimina a
degradação sistemática vista antes, com uma amostra pequena mas favorável
(4 pares em `lin318`) mostrando inclusive um caso de melhoria real.

Isso **não é ainda uma vitória decisiva de H1** — a amostra em `lin318` é
pequena demais para um veredito estatístico forte (1 win / 1 tie / 2 losses
não é significativo), e nas instâncias fáceis o mecanismo continua sem
motivo para existir (empata com o fixo, apenas com menos overhead que a
primeira tentativa, mas ainda overhead). O resultado honesto é: **o
mecanismo de controle por distância corrige o defeito identificado na
literatura, é seguro (nunca degrada de forma sistemática) e mostra sinal
inicial de benefício em instâncias com folga real — mas precisa de mais
dados (mais seeds, instâncias maiores como `pr439`/`att532`, e talvez ajuste
fino da banda-alvo 5%–15%) antes de declarar ganho consistente.**

### 10.5 Próximos passos

1. Rodar mais seeds em `lin318` (e subir para `pr439`/`att532` em lote, fora
   de sessão interativa) para ter poder estatístico real no teste de sinal.
2. Testar sensibilidade à banda-alvo (`--target-min-pct`/`--target-max-pct`)
   — os defaults (5%–15%) não foram ajustados, só herdados de bom senso.
3. Investigar se o overhead de tempo em instâncias fáceis pode cair ainda
   mais controlando a banda-alvo por instância (ex. banda mais estreita ou
   `maxStrength` menor quando `n` é pequeno).
4. Seguir a sugestão da seção 9.3.3: como o próprio AILS-PR já une esse
   controle com path relinking, considerar testar H2 sobre esta mesma base
   de código (o `edge_distance` já implementado aqui é reutilizável para
   medir similaridade entre soluções elite).

### 10.6 Amostra ampliada — `lin318` (12 seeds), `pr439` e `att532` (novos)

Seguindo o passo 1 da seção 10.5, ampliamos `lin318` de 4 para 12 seeds
pareadas e rodamos pares novos (fixed vs distance, não existiam antes) em
`pr439` (5 seeds) e `att532` (3 seeds) — `I_max` reduzido (1) nessas duas
por custo computacional. Script:
[`scripts/h1_large_instances_test.py`](../../scripts/h1_large_instances_test.py),
dados brutos: `scripts/h1_large_results.json`.

Nota sobre qualidade do dado: uma medição de tempo (`lin318` seed=11,
modo distância: `7 956 882 ms`) é um artefato de ambiente (a duração total
do lote inteiro, incluindo várias rodadas depois dessa, foi de ~25 min —
incompatível com uma pausa real de ~2h nessa única execução; consistente
com um glitch de relógio do WSL2, provavelmente uma suspensão breve do
host). O custo (`5574033`) não é afetado, só a medição de tempo dessa
execução foi descartada do agregado de tempo.

| instância | n pares | diff média (fixo→distância) | win/tie/loss | p (sinal) | overhead médio de tempo |
|---|---|---|---|---|---|
| lin318 | 12 | **+0.065%** | 6/1/5 | 1.000 | +15.0% |
| pr439 | 5 | −0.085% | 4/0/1 | 0.375 | +12.3% |
| att532 | 3 | −0.844% | 1/0/2 | 1.000 | −26.4% |

Nenhum dos três é estatisticamente significativo (todo `p` ≥ 0.375, amostras
pequenas). Olhando seed a seed:

- **`lin318`** deixa de ser um resultado negativo: com 4 seeds era 0 wins/4
  losses (−0,54%); com 12 seeds é 6 wins/5 losses/1 tie (+0,065%) — a
  degradação sistemática desaparece, sobra ruído em torno de zero.
- **`pr439`**: 4 das 5 seeds têm ganho pequeno e consistente (+0,18% a
  +0,41%), mas 1 seed tem uma perda grande (−1,54%) que sozinha inverte a
  média. Sem essa seed, o resultado seria um ganho claro; com ela, é
  inconclusivo — evidência de que o mecanismo ainda tem uma cauda de casos
  ruins, não eliminada pelo ajuste de gatilho.
- **`att532`** (n=3, a amostra mais fraca do conjunto): 1 ganho
  (+0,50%), 2 perdas (−1,61%, −1,42%) — inconclusivo, precisa de mais seeds
  antes de significar qualquer coisa.
- Overhead de tempo ficou moderado nas três (+15%, +12%, e até negativo em
  `att532`), bem diferente do +70–94% da escalada por estagnação nas
  instâncias pequenas — mesmo quando a qualidade não melhora, o mecanismo
  não é caro.

**Veredito final revisado para H1**: o controle por distância de arestas
resolve o defeito identificado na literatura (nunca mais perde de forma
sistemática, ao contrário da escalada por estagnação) e é computacionalmente
barato, mas **não há evidência estatisticamente sólida, com os dados
coletados até aqui, de que ele reduza o gap médio** nas instâncias com folga
real — o resultado é ruído em torno de zero, com uma cauda ocasional de
perdas maiores (`pr439` seed=1: −1,54%; `att532` seeds 2–3: −1,4% a −1,6%)
que ainda merece investigação (possivelmente a banda-alvo 5%–15% não é bem
calibrada para todo tamanho de instância, ou `maxStrength=5` ainda é alto
demais nessas perdas específicas). H1 não pode ser declarada confirmada nem
refutada com confiança neste ponto — precisaria de mais seeds (dezenas, não
unidades) nessas instâncias grandes, ou uma varredura da banda-alvo, para um
veredito estatístico.

## 11. Lote noturno — veredito final com poder estatístico real

Rodado fora de sessão interativa (`scripts/night_batch.py`), pareado por
seed, `I_max`/`I_ILS` mais altos que nas seções anteriores:

| instância | n | `I_max`/`I_ILS` | diff média | win/tie/loss | p (sinal) |
|---|---|---|---|---|---|
| lin318 | 20 | 10/100 | +0,007% | 8/2/10 | 0,815 |
| pr439 | 15 | 5/100 | −0,082% | 5/0/10 | 0,302 |
| att532 | 10 | 3/100 | −0,038% | 5/0/5 | 1,000 |

Nenhum `p` chega perto de significância, os sinais trocam de direção entre
instâncias, e a magnitude média é sempre menor que 0,1% — o perfil clássico
de ruído estatístico em torno de zero, não de um efeito real mascarado por
amostra pequena.

**Veredito final**: com N grande o suficiente para confiar no teste de
sinal, o controle por distância de arestas **não melhora o GILS-RVND** nestas
instâncias. O sintoma diagnosticado na seção 2 continua válido (a curva do
ILS puro realmente estagna cedo), mas nenhum dos dois mecanismos testados
nesta hipótese (escalada por estagnação, controle por distância) o
transforma em ganho de qualidade. H1 está encerrada nesta forma.

Isso não fecha a porta para diversificação adaptativa em geral — só para as
duas implementações testadas aqui. Se houver interesse em retomar, os
candidatos não testados da seção 9 (reactive/histórico à la Prais & Ribeiro,
ou adaptar o guia de perturbação por informação local como no XKICK) partem
de um ponto diferente e não foram descartados por este resultado.

### Fontes

- Mladenović, N., Hansen, P. (1997). Variable neighborhood search.
  *Computers & Operations Research*, 24(11), 1097–1100.
- Martin, O., Otto, S.W., Felten, E.W. (1991). Large-step Markov chains for
  the TSP. *Complex Systems*, 5(3), 299–326.
- Benlic, U., Hao, J.K. (2013). A Study of Adaptive Perturbation Strategy
  for Iterated Local Search. *EvoCOP 2013*, LNCS 7832.
  https://link.springer.com/chapter/10.1007/978-3-642-37198-1_6
- XKICK, an intelligent kick perturbation for the traveling salesman
  problem. https://www.researchgate.net/publication/317370678
- Prais, M., Ribeiro, C.C. (2000). Reactive GRASP: An application to a
  matrix decomposition problem in TDMA traffic assignment. *INFORMS Journal
  on Computing*, 12(3).
  https://www.semanticscholar.org/paper/989a3b09ce28d7463ebcbe4e15dc57d0290d4f27
- Ropke, S., Pisinger, D. (2006). An adaptive large neighborhood search
  heuristic for the pickup and delivery problem with time windows.
  https://www.researchgate.net/publication/220413334
- Máximo, V.R., Nascimento, M.C.V. (2021). A hybrid adaptive Iterated Local
  Search with diversification control to the Capacitated Vehicle Routing
  Problem. *European Journal of Operational Research*, 294, 1108–1119.
  https://arxiv.org/abs/2012.11021 ·
  https://www.sciencedirect.com/science/article/abs/pii/S037722172100117X
- Máximo, V.R., Cordeau, J.-F., Nascimento, M.C.V. (2024). AILS-II: An
  Adaptive Iterated Local Search Heuristic for the Large-Scale Capacitated
  Vehicle Routing Problem. *INFORMS Journal on Computing*, 36(4), 974–986.
  https://arxiv.org/abs/2205.12082
- Salehipour, A., Sörensen, K., Goos, P., Bräysy, O. (2011). Efficient
  GRASP+VND and GRASP+VNS metaheuristics for the traveling repairman
  problem. *4OR*, 9(2), 189–209 (já referenciado no artigo-base do
  projeto).
